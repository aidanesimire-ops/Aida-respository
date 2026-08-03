"""Thin ArcGIS REST client: layer metadata, paged queries, WHERE building."""

from __future__ import annotations

import logging
import time
from typing import Any, Iterable

import requests

log = logging.getLogger(__name__)

STRING_TYPES = {"esriFieldTypeString", "esriFieldTypeGUID", "esriFieldTypeGlobalID"}
_RETRY_STATUS = (429, 500, 502, 503, 504)


class ArcGISError(RuntimeError):
    """The service returned an error payload or stopped responding."""


class ArcGISClient:
    """Small wrapper around one ArcGIS MapServer/FeatureServer."""

    def __init__(
        self,
        *,
        timeout: int = 120,
        retries: int = 4,
        pause: float = 0.3,
        session: requests.Session | None = None,
    ) -> None:
        self.timeout = timeout
        self.retries = retries
        self.pause = pause
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "DAWNRE-waterfront-engine/1.0")

    # -- low level -------------------------------------------------------
    def get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        params = {"f": "json", **params}
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
                if resp.status_code in _RETRY_STATUS:
                    raise ArcGISError(f"HTTP {resp.status_code} from {url}")
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, dict) and "error" in payload:
                    err = payload["error"]
                    raise ArcGISError(
                        f"{url} -> {err.get('message', err)} "
                        f"{'; '.join(err.get('details', []))}".strip()
                    )
                return payload
            except (requests.RequestException, ArcGISError, ValueError) as exc:
                last = exc
                if attempt == self.retries - 1:
                    break
                backoff = 2**attempt
                log.warning("%s (attempt %d) — retrying in %ds", exc, attempt + 1, backoff)
                time.sleep(backoff)
        raise ArcGISError(f"request failed after {self.retries} attempts: {last}")

    # -- metadata --------------------------------------------------------
    def layer_info(self, layer_url: str) -> dict[str, Any]:
        return self.get_json(layer_url, {})

    def field_types(self, layer_url: str) -> dict[str, str]:
        """``{field_name: esriFieldType}`` for a layer."""
        info = self.layer_info(layer_url)
        return {f["name"]: f.get("type", "") for f in info.get("fields", []) or []}

    def sample_record(self, layer_url: str) -> dict[str, Any]:
        """One feature's attributes, for field-map verification."""
        payload = self.get_json(
            f"{layer_url.rstrip('/')}/query",
            {
                "where": "1=1",
                "outFields": "*",
                "returnGeometry": "false",
                "resultRecordCount": 1,
            },
        )
        features = payload.get("features") or []
        return features[0].get("attributes", {}) if features else {}

    def count(self, query_url: str, where: str = "1=1") -> int:
        payload = self.get_json(query_url, {"where": where, "returnCountOnly": "true"})
        return int(payload.get("count", 0))

    # -- paged feature pull ----------------------------------------------
    def query_geojson(
        self,
        query_url: str,
        *,
        where: str = "1=1",
        out_fields: str = "*",
        page_size: int = 1000,
        out_sr: int = 4326,
        geometry: bool = True,
        order_by: str | None = None,
        progress: bool = True,
    ) -> list[dict[str, Any]]:
        """Page through a layer and return GeoJSON features.

        Uses ``resultOffset``/``resultRecordCount`` and stops on either a short
        page or an explicit ``exceededTransferLimit: false``.
        """
        features: list[dict[str, Any]] = []
        offset = 0
        while True:
            params = {
                "f": "geojson",
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "true" if geometry else "false",
                "outSR": out_sr,
                "resultOffset": offset,
                "resultRecordCount": page_size,
            }
            if order_by:
                params["orderByFields"] = order_by
            payload = self.get_json(query_url, params)
            batch = payload.get("features") or []
            features.extend(batch)
            if progress and batch:
                log.info("  fetched %d (total %d)", len(batch), len(features))
            if not batch or len(batch) < page_size:
                break
            if payload.get("exceededTransferLimit") is False:
                break
            offset += len(batch)
            time.sleep(self.pause)
        return features


def order_field(field_types: dict[str, str]) -> str | None:
    """Pick a stable sort field so paging can't skip or repeat rows."""
    for candidate in ("OBJECTID", "objectid", "FID", "OID"):
        if candidate in field_types:
            return candidate
    return next(
        (n for n, t in field_types.items() if t == "esriFieldTypeOID"),
        None,
    )


def code_where(
    field: str,
    codes: Iterable[str],
    *,
    field_type: str | None = None,
    match: str = "exact",
) -> str:
    """Build a WHERE clause for a set of land-use codes.

    Handles the two things that quietly break a port to a new county:
    numeric use-code columns (which must not be quoted), and codes stored
    unpadded (``1``) versus padded (``01``).
    """
    codes = [str(c).strip().upper() for c in codes if str(c).strip()]
    if not codes:
        raise ValueError("no use codes supplied")

    numeric = field_type is not None and field_type not in STRING_TYPES

    if match == "prefix":
        if numeric:
            raise ValueError(
                f"prefix matching needs a string use-code column; {field} is {field_type}"
            )
        likes = " OR ".join(f"{field} LIKE '{c}%'" for c in sorted(set(codes)))
        return f"({likes})"

    variants: list[str] = []
    for code in codes:
        variants.append(code)
        if code.isdigit():
            variants.append(code.lstrip("0") or "0")  # 01 -> 1
            variants.append(code.zfill(2))  # 1 -> 01
    variants = sorted(dict.fromkeys(variants))

    if numeric:
        nums = sorted({int(v) for v in variants if v.isdigit()})
        if not nums:
            raise ValueError(f"no numeric use codes to query against {field}")
        return f"{field} IN (" + ",".join(str(n) for n in nums) + ")"

    quoted = ",".join(f"'{v}'" for v in variants)
    return f"{field} IN ({quoted})"
