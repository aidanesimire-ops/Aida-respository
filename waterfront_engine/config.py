"""Market configuration objects.

A market config is a plain Python file exposing three module-level dicts —
``MARKET``, ``ASSET_CLASSES`` and ``CONDO_DELIVERABLE`` — so a new market is a
new file, never a code change. See ``configs/fort_lauderdale.py``.
"""

from __future__ import annotations

import importlib.util
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

log = logging.getLogger(__name__)

# Field-map keys every market must supply. The values are the *source layer's*
# attribute names, which differ county to county.
REQUIRED_FIELD_KEYS = (
    "f_folio",
    "f_owner1",
    "f_mail",
    "f_mailcity",
    "f_situs",
    "f_use",
    "f_usedesc",
    "f_value",
)

OPTIONAL_FIELD_KEYS = (
    "f_owner2",
    "f_owners",
    "f_usedetail",
    "f_sqft",
    "f_bldgs",
    "f_saledate",
    "f_saleprice",
)

FIELD_KEYS = REQUIRED_FIELD_KEYS + OPTIONAL_FIELD_KEYS


class ConfigError(ValueError):
    """Raised when a market config is missing or internally inconsistent."""


@dataclass(frozen=True)
class AssetClass:
    """One output tab of Workbook 1."""

    key: str
    label: str
    group: str
    codes: tuple[str, ...]
    include_kw_from: tuple[str, ...] = ()
    include_kw: str | None = None
    exclude_kw: str | None = None

    @property
    def source_codes(self) -> tuple[str, ...]:
        """Every use code that must be pulled to build this class."""
        return tuple(dict.fromkeys(self.codes + self.include_kw_from))

    @classmethod
    def from_dict(cls, key: str, raw: dict[str, Any]) -> "AssetClass":
        missing = {"label", "group", "codes"} - raw.keys()
        if missing:
            raise ConfigError(f"asset class {key!r} missing {sorted(missing)}")
        include_kw_from = tuple(str(c) for c in raw.get("include_kw_from", ()))
        include_kw = raw.get("include_kw")
        if include_kw_from and not include_kw:
            raise ConfigError(
                f"asset class {key!r} sets include_kw_from but no include_kw pattern"
            )
        for pattern in (include_kw, raw.get("exclude_kw")):
            if pattern is not None:
                _validate_regex(pattern, key)
        return cls(
            key=key,
            label=str(raw["label"]),
            group=str(raw["group"]),
            codes=tuple(str(c) for c in raw["codes"]),
            include_kw_from=include_kw_from,
            include_kw=include_kw,
            exclude_kw=raw.get("exclude_kw"),
        )


@dataclass(frozen=True)
class CondoDeliverable:
    """Workbook 2 — unit-level beach condo owners."""

    label: str
    codes: tuple[str, ...]
    beach_only: bool = True
    boundary_path: str | None = None  # optional barrier-island polygon (any OGR format)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "CondoDeliverable":
        if "codes" not in raw:
            raise ConfigError("CONDO_DELIVERABLE missing 'codes'")
        return cls(
            label=str(raw.get("label", "Beach Condo Owners")),
            codes=tuple(str(c) for c in raw["codes"]),
            beach_only=bool(raw.get("beach_only", True)),
            boundary_path=raw.get("boundary_path"),
        )


@dataclass(frozen=True)
class Market:
    """Everything that varies between markets."""

    name: str
    parcel_service: str
    parcel_layer: int
    water_layer: int | None
    proj_crs: int
    fields: dict[str, str]
    home_city: str
    home_city_aliases: tuple[str, ...] = ()
    beach_lon_threshold: float | None = None
    beach_side: str = "east"  # which side of the threshold is the barrier island
    water_buffer_ft: float = 30.0
    min_frontage_ft: float = 15.0
    water_type_field: str | None = "TYPE"
    water_name_field: str | None = "NAME"
    water_type_exclude: str | None = None  # regex, e.g. r"Ditch|Retention"
    water_service: str | None = None  # defaults to parcel_service
    water_path: str | None = None  # local hydrography file instead of a REST layer
    code_match: str = "exact"  # "exact" or "prefix" (for 4-digit detail codes)
    request_timeout: int = 120
    page_size: int = 1000

    def __post_init__(self) -> None:
        missing = [k for k in REQUIRED_FIELD_KEYS if not self.fields.get(k)]
        if missing:
            raise ConfigError(f"MARKET missing required field mappings: {missing}")
        if self.code_match not in ("exact", "prefix"):
            raise ConfigError("MARKET['code_match'] must be 'exact' or 'prefix'")
        if self.beach_side not in ("east", "west"):
            raise ConfigError("MARKET['beach_side'] must be 'east' or 'west'")
        if self.water_layer is None and not self.water_path:
            raise ConfigError("MARKET needs either 'water_layer' or 'water_path'")
        if self.water_type_exclude:
            _validate_regex(self.water_type_exclude, "water_type_exclude")
        if self.min_frontage_ft <= 2 * self.water_buffer_ft:
            log.warning(
                "min_frontage_ft (%.0f) is not above 2 x water_buffer_ft (%.0f): a parcel "
                "touching water at a single corner picks up roughly one buffer width on each "
                "of its two edges, so corner clips will pass the frontage test",
                self.min_frontage_ft,
                self.water_buffer_ft,
            )

    # -- convenience -----------------------------------------------------
    def f(self, key: str) -> str:
        """Source attribute name for a field key (``'f_folio'`` or ``'folio'``)."""
        key = key if key.startswith("f_") else f"f_{key}"
        name = self.fields.get(key)
        if not name:
            raise ConfigError(f"MARKET has no mapping for {key!r}")
        return name

    def opt(self, key: str) -> str | None:
        """Like :meth:`f` but returns ``None`` for unmapped optional fields."""
        key = key if key.startswith("f_") else f"f_{key}"
        return self.fields.get(key) or None

    @property
    def parcel_query_url(self) -> str:
        return f"{self.parcel_service.rstrip('/')}/{self.parcel_layer}/query"

    @property
    def parcel_layer_url(self) -> str:
        return f"{self.parcel_service.rstrip('/')}/{self.parcel_layer}"

    @property
    def water_query_url(self) -> str | None:
        if self.water_layer is None:
            return None
        base = (self.water_service or self.parcel_service).rstrip("/")
        return f"{base}/{self.water_layer}/query"

    @property
    def local_cities(self) -> tuple[str, ...]:
        """Mailing cities that count as *not* absentee."""
        cities = (self.home_city,) + tuple(self.home_city_aliases)
        return tuple(dict.fromkeys(c.upper().strip() for c in cities if c))

    def slug(self) -> str:
        return re.sub(r"[^a-z0-9]+", "_", self.name.lower()).strip("_")

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Market":
        fields_map = {k: raw[k] for k in FIELD_KEYS if raw.get(k)}
        known = {
            "name",
            "parcel_service",
            "parcel_layer",
            "water_layer",
            "proj_crs",
            "home_city",
            "home_city_aliases",
            "beach_lon_threshold",
            "beach_side",
            "water_buffer_ft",
            "min_frontage_ft",
            "water_type_field",
            "water_name_field",
            "water_type_exclude",
            "water_service",
            "water_path",
            "code_match",
            "request_timeout",
            "page_size",
        }
        kwargs = {k: raw[k] for k in known if k in raw}
        kwargs["home_city_aliases"] = tuple(raw.get("home_city_aliases", ()))
        return cls(fields=fields_map, **kwargs)


@dataclass
class MarketConfig:
    """A loaded market config: market + asset classes + condo deliverable."""

    market: Market
    asset_classes: dict[str, AssetClass]
    condo: CondoDeliverable | None = None
    source_path: Path | None = None
    data_dir: Path = field(default_factory=lambda: Path("data"))
    out_dir: Path = field(default_factory=lambda: Path("."))

    @property
    def all_source_codes(self) -> list[str]:
        """Every use code the pipeline must pull, across all deliverables."""
        codes: list[str] = []
        for ac in self.asset_classes.values():
            codes.extend(ac.source_codes)
        if self.condo:
            codes.extend(self.condo.codes)
        return sorted(dict.fromkeys(codes))

    def stage_path(self, stage: str, key: str = "") -> Path:
        name = f"{stage}_{key}.gpkg" if key else f"{stage}.gpkg"
        return self.data_dir / name


def _validate_regex(pattern: str, where: str) -> None:
    try:
        re.compile(pattern)
    except re.error as exc:  # pragma: no cover - config typo path
        raise ConfigError(f"invalid regex in {where}: {exc}") from exc


def load_config(
    path: str | Path,
    *,
    data_dir: str | Path = "data",
    out_dir: str | Path = ".",
) -> MarketConfig:
    """Import a market config file and build a :class:`MarketConfig`."""
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"market config not found: {path}")

    spec = importlib.util.spec_from_file_location(f"market_{path.stem}", path)
    if spec is None or spec.loader is None:  # pragma: no cover - import machinery
        raise ConfigError(f"could not import market config: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "MARKET"):
        raise ConfigError(f"{path} does not define MARKET")
    if not hasattr(module, "ASSET_CLASSES"):
        raise ConfigError(f"{path} does not define ASSET_CLASSES")

    market = Market.from_dict(module.MARKET)
    classes = {
        key: AssetClass.from_dict(key, raw)
        for key, raw in module.ASSET_CLASSES.items()
    }
    if not classes:
        raise ConfigError(f"{path} defines no asset classes")
    condo_raw = getattr(module, "CONDO_DELIVERABLE", None)
    condo = CondoDeliverable.from_dict(condo_raw) if condo_raw else None

    return MarketConfig(
        market=market,
        asset_classes=classes,
        condo=condo,
        source_path=path,
        data_dir=Path(data_dir),
        out_dir=Path(out_dir),
    )


def normalize_codes(codes: Iterable[str]) -> list[str]:
    """Trim and upper-case use codes, dropping blanks and duplicates."""
    out = (str(c).strip().upper() for c in codes)
    return list(dict.fromkeys(c for c in out if c))
