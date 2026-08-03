"""Stage orchestration: fetch -> classify -> waterfront -> flags -> enrich -> workbooks."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd

from . import classify, condos, spatial
from .arcgis import ArcGISClient, code_where, order_field
from .columns import condo_layout, ownership_layout, to_sheet
from .config import MarketConfig
from .excel import PROVENANCE_NOTES, summary_table, write_workbook
from .flags import add_flags, callable_entities
from .sunbiz import EntityResolver, apply_enrichment

log = logging.getLogger(__name__)

STAGES = ("fetch", "classify", "waterfront", "flags", "enrich", "workbooks")

PARCELS_FILE = "parcels_all"
WATER_FILE = "water"
CONDO_FILE = "beach_condos"

# Candidate source names when a configured field is missing, for verify_fields().
FIELD_HINTS = {
    "f_folio": ("FOLIO", "PARCEL", "PIN", "APN", "STRAP", "PARCELNO", "PARCELID"),
    "f_owner1": ("OWNER", "OWNERNME", "NAME"),
    "f_owner2": ("OWNER2", "OWNERNME2"),
    "f_owners": ("OWNERS", "OWNERNAME"),
    "f_mail": ("MAIL", "PSTL", "POSTAL", "ADDR"),
    "f_mailcity": ("CITY",),
    "f_situs": ("SITE", "SITUS", "PHYSICAL", "LOCATION"),
    "f_use": ("USE", "DOR", "CLASS"),
    "f_usedesc": ("USEDSCRP", "DESC"),
    "f_usedetail": ("DETAIL",),
    "f_value": ("VAL", "JUST", "MARKET", "ASSD"),
    "f_sqft": ("SQFT", "SQFEET", "AREA"),
    "f_bldgs": ("BLDG", "BUILDING"),
    "f_saledate": ("SALEDATE", "SALE_DT", "DATE"),
    "f_saleprice": ("SALEPRICE", "SALE_AMT", "PRICE"),
}


# -- helpers -------------------------------------------------------------
def _save(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if gdf.empty:
        path.unlink(missing_ok=True)
        log.info("  %s: 0 rows (no file written)", path.name)
        return
    out = gdf.copy()
    for col in out.columns:
        if col != "geometry" and out[col].dtype == "object":
            out[col] = out[col].astype("string")
    out.to_file(path, driver="GPKG")


def _load(path: Path) -> gpd.GeoDataFrame:
    if not path.exists():
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    return gpd.read_file(path)


def _load_stage(cfg: MarketConfig, key: str, stages: Iterable[str]) -> gpd.GeoDataFrame:
    """Load the latest available stage file for an asset class."""
    for stage in stages:
        path = cfg.stage_path(stage, key)
        if path.exists():
            return gpd.read_file(path)
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")


# -- stages --------------------------------------------------------------
def verify_fields(cfg: MarketConfig, client: ArcGISClient | None = None) -> dict[str, object]:
    """Check the configured field map against the live layer schema.

    Run this first on any new market: it is the difference between a clean run
    and a workbook full of empty owner columns.
    """
    client = client or ArcGISClient(timeout=cfg.market.request_timeout)
    types = client.field_types(cfg.market.parcel_layer_url)
    available = list(types)
    upper = {name.upper(): name for name in available}

    ok: dict[str, str] = {}
    missing: dict[str, list[str]] = {}
    for key, name in cfg.market.fields.items():
        if name in types or name.upper() in upper:
            ok[key] = name
            continue
        hints = FIELD_HINTS.get(key, ())
        suggestions = [f for f in available if any(h in f.upper() for h in hints)]
        missing[key] = suggestions[:8]

    report: dict[str, object] = {
        "layer": cfg.market.parcel_layer_url,
        "field_count": len(available),
        "mapped_ok": ok,
        "missing": missing,
        "available_fields": available,
    }
    try:
        report["feature_count"] = client.count(cfg.market.parcel_query_url)
        report["sample_record"] = client.sample_record(cfg.market.parcel_layer_url)
    except Exception as exc:  # count/sample are diagnostics, never fatal
        report["feature_count_error"] = str(exc)

    if missing:
        log.warning("field map has %d unmapped keys: %s", len(missing), list(missing))
    else:
        log.info("field map verified against %s", cfg.market.parcel_layer_url)
    return report


def fetch(cfg: MarketConfig, client: ArcGISClient | None = None) -> gpd.GeoDataFrame:
    """Pull every parcel in scope (all asset classes + condos) plus hydrography."""
    market = cfg.market
    client = client or ArcGISClient(timeout=market.request_timeout)

    types = client.field_types(market.parcel_layer_url)
    where = code_where(
        market.f("use"),
        cfg.all_source_codes,
        field_type=types.get(market.f("use")),
        match=market.code_match,
    )
    log.info("parcel WHERE: %s", where)

    features = client.query_geojson(
        market.parcel_query_url,
        where=where,
        page_size=market.page_size,
        order_by=order_field(types),
    )
    if not features:
        raise RuntimeError(
            "parcel query returned 0 features — check the use-code field mapping and "
            "code values with `verify-fields`"
        )
    parcels = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")
    _save(parcels, cfg.stage_path(PARCELS_FILE))
    log.info("pulled %d parcels across %d use codes", len(parcels), len(cfg.all_source_codes))

    fetch_water(cfg, client)
    return parcels


def fetch_water(cfg: MarketConfig, client: ArcGISClient | None = None) -> gpd.GeoDataFrame:
    """Pull the hydrography layer (or read the configured local file)."""
    market = cfg.market
    path = cfg.stage_path(WATER_FILE)

    if market.water_path:
        water = gpd.read_file(market.water_path).to_crs(4326)
    else:
        client = client or ArcGISClient(timeout=market.request_timeout)
        fields = [f for f in (market.water_name_field, market.water_type_field) if f]
        features = client.query_geojson(
            market.water_query_url,
            out_fields=",".join(fields) if fields else "*",
            page_size=market.page_size,
        )
        if not features:
            raise RuntimeError("water layer returned 0 features — check water_layer id")
        water = gpd.GeoDataFrame.from_features(features, crs="EPSG:4326")

    _save(water, path)
    log.info("water features: %d", len(water))
    return water


def classify_stage(cfg: MarketConfig) -> dict[str, gpd.GeoDataFrame]:
    parcels = _load(cfg.stage_path(PARCELS_FILE))
    if parcels.empty:
        raise RuntimeError("no parcels on disk — run the fetch stage first")

    buckets = classify.split_asset_classes(parcels, cfg.asset_classes, cfg.market)
    for key, frame in buckets.items():
        _save(gpd.GeoDataFrame(frame, crs=parcels.crs), cfg.stage_path("class", key))
    return {k: gpd.GeoDataFrame(v, crs=parcels.crs) for k, v in buckets.items()}


def waterfront_stage(cfg: MarketConfig) -> dict[str, gpd.GeoDataFrame]:
    water = _load(cfg.stage_path(WATER_FILE))
    if water.empty:
        raise RuntimeError("no water layer on disk — run the fetch stage first")
    buffered = spatial.buffer_water(water, cfg.market)

    out: dict[str, gpd.GeoDataFrame] = {}
    for key in cfg.asset_classes:
        parcels = _load(cfg.stage_path("class", key))
        kept = spatial.waterfront(parcels, buffered, cfg.market)
        _save(kept, cfg.stage_path("waterfront", key))
        log.info("%-18s %6d waterfront of %6d", key, len(kept), len(parcels))
        out[key] = kept
    return out


def flags_stage(cfg: MarketConfig) -> dict[str, gpd.GeoDataFrame]:
    out: dict[str, gpd.GeoDataFrame] = {}
    for key in cfg.asset_classes:
        parcels = _load(cfg.stage_path("waterfront", key))
        if parcels.empty:
            out[key] = parcels
            continue
        flagged = gpd.GeoDataFrame(add_flags(parcels, cfg.market), crs=parcels.crs)
        _save(flagged, cfg.stage_path("flagged", key))
        out[key] = flagged

    if cfg.condo:
        condo_frame = build_condos(cfg)
        out["_condos"] = condo_frame
    return out


def build_condos(cfg: MarketConfig) -> gpd.GeoDataFrame:
    """Workbook 2 dataset: condo-coded parcels on the barrier island, flagged."""
    if not cfg.condo:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

    parcels = _load(cfg.stage_path(PARCELS_FILE))
    if parcels.empty:
        raise RuntimeError("no parcels on disk — run the fetch stage first")

    mask = classify.match_codes(parcels[cfg.market.f("use")], cfg.condo.codes, cfg.market.code_match)
    condo_parcels = parcels[mask].copy()
    log.info("condo-coded parcels: %d", len(condo_parcels))

    if cfg.condo.beach_only:
        condo_parcels = spatial.beach_filter(condo_parcels, cfg.market, cfg.condo.boundary_path)

    if condo_parcels.empty:
        log.warning("no beach condos after filtering — check beach_lon_threshold / codes")
        return condo_parcels

    flagged = add_flags(condo_parcels, cfg.market)
    with_units = condos.add_unit_columns(flagged, cfg.market)
    result = gpd.GeoDataFrame(with_units, crs=parcels.crs)
    _save(result, cfg.stage_path(CONDO_FILE))
    return result


def enrich_stage(
    cfg: MarketConfig,
    resolver: EntityResolver,
    *,
    include_condos: bool = True,
) -> dict[str, gpd.GeoDataFrame]:
    """Second pass: resolve entity-owned rows to managers / registered agent."""
    owner_field = cfg.market.f("owner1")
    out: dict[str, gpd.GeoDataFrame] = {}

    for key in cfg.asset_classes:
        parcels = _load(cfg.stage_path("flagged", key))
        if parcels.empty:
            out[key] = parcels
            continue
        mask = callable_entities(parcels)
        log.info("%-18s enriching %d entity-owned rows", key, int(mask.sum()))
        enriched = apply_enrichment(parcels, resolver, mask=mask, owner_field=owner_field)
        gdf = gpd.GeoDataFrame(enriched, crs=parcels.crs)
        _save(gdf, cfg.stage_path("enriched", key))
        out[key] = gdf

    if include_condos and cfg.condo:
        condo_frame = _load(cfg.stage_path(CONDO_FILE))
        if not condo_frame.empty:
            mask = callable_entities(condo_frame)
            log.info("beach condos: enriching %d entity-owned units", int(mask.sum()))
            enriched = apply_enrichment(condo_frame, resolver, mask=mask, owner_field=owner_field)
            gdf = gpd.GeoDataFrame(enriched, crs=condo_frame.crs)
            _save(gdf, cfg.stage_path(CONDO_FILE))
            out["_condos"] = gdf
    return out


# -- workbooks -----------------------------------------------------------
def ownership_sheets(cfg: MarketConfig) -> dict[str, pd.DataFrame]:
    layout = ownership_layout(cfg.market)
    sheets: dict[str, pd.DataFrame] = {}
    for key, asset in cfg.asset_classes.items():
        frame = _load_stage(cfg, key, ("enriched", "flagged", "waterfront"))
        sheets[asset.label] = to_sheet(frame, layout)
    return sheets


def build_ownership_workbook(cfg: MarketConfig, extra_notes: tuple[str, ...] = ()) -> Path:
    sheets = ownership_sheets(cfg)
    groups = {asset.label: asset.group for asset in cfg.asset_classes.values()}
    summary = summary_table(sheets, groups)

    qa: dict[str, pd.DataFrame] = {}
    dupes = classify.overlap_report(
        {k: _load_stage(cfg, k, ("flagged", "waterfront", "class")) for k in cfg.asset_classes},
        cfg.asset_classes,
        cfg.market,
    )
    if not dupes.empty:
        qa["QA — Multi-Class Folios"] = dupes

    parcels = _load(cfg.stage_path(PARCELS_FILE))
    if not parcels.empty:
        qa["QA — Use Code Census"] = classify.use_code_census(parcels, cfg.market)

    ordered = {"Summary": summary, **sheets, **qa}
    path = cfg.out_dir / f"Waterfront_Ownership_Lists_{cfg.market.slug()}.xlsx"
    return write_workbook(
        path,
        ordered,
        title=f"{cfg.market.name} — Waterfront Ownership",
        notes=tuple(extra_notes) + PROVENANCE_NOTES,
    )


def build_condo_workbook(cfg: MarketConfig, extra_notes: tuple[str, ...] = ()) -> Path | None:
    if not cfg.condo:
        return None
    frame = _load(cfg.stage_path(CONDO_FILE))
    units = to_sheet(frame, condo_layout(cfg.market))
    index = condos.building_index(units)

    path = cfg.out_dir / f"Beach_Condo_Owners_{cfg.market.slug()}.xlsx"
    return write_workbook(
        path,
        {"By Building": index, "Units": units},
        title=f"{cfg.market.name} — {cfg.condo.label}",
        notes=tuple(extra_notes) + PROVENANCE_NOTES,
    )


def write_run_report(cfg: MarketConfig, extra: dict[str, object] | None = None) -> Path:
    """Row counts per stage — the thing to read before dialing."""
    report: dict[str, object] = {
        "market": cfg.market.name,
        "config": str(cfg.source_path) if cfg.source_path else None,
        "use_codes": cfg.all_source_codes,
        "classes": {},
    }
    for key, asset in cfg.asset_classes.items():
        report["classes"][asset.label] = {  # type: ignore[index]
            "classified": len(_load(cfg.stage_path("class", key))),
            "waterfront": len(_load(cfg.stage_path("waterfront", key))),
            "enriched": len(_load(cfg.stage_path("enriched", key))),
        }
    if cfg.condo:
        report["beach_condo_units"] = len(_load(cfg.stage_path(CONDO_FILE)))
    if extra:
        report.update(extra)

    path = cfg.out_dir / f"run_report_{cfg.market.slug()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, default=str))
    log.info("wrote %s", path)
    return path
