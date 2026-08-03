"""Workbook 2 — unit-level beach condo owners and the by-building index."""

from __future__ import annotations

import logging
import re

import geopandas as gpd
import pandas as pd

from .config import Market

log = logging.getLogger(__name__)

# "3000 E SUNRISE BLVD # 12B" / "... UNIT 12B" / "... APT 12B" / "... STE 200"
UNIT_SPLIT = re.compile(r"\s*(?:#|\bUNIT\b|\bAPT\b|\bSTE\b|\bPH\b(?=\s*\d))\s*", flags=re.I)


def split_unit(address: object) -> tuple[str, str]:
    """``('3000 E SUNRISE BLVD', '12B')`` — building, unit number."""
    if address is None or (isinstance(address, float) and pd.isna(address)):
        return "", ""
    text = re.sub(r"\s+", " ", str(address)).strip()
    if not text:
        return "", ""
    parts = UNIT_SPLIT.split(text, maxsplit=1)
    if len(parts) == 2 and parts[1].strip():
        return parts[0].strip(" ,"), parts[1].strip(" ,")
    return text, ""


def add_unit_columns(frame: gpd.GeoDataFrame | pd.DataFrame, market: Market) -> pd.DataFrame:
    """Add Unit_Address / Building / Unit_Number off the situs address."""
    out = frame.copy()
    situs = market.f("situs")
    source = out[situs] if situs in out.columns else pd.Series("", index=out.index)
    out["Unit_Address"] = source.astype("string").fillna("")
    parsed = out["Unit_Address"].map(split_unit)
    out["Building"] = [p[0] for p in parsed]
    out["Unit_Number"] = [p[1] for p in parsed]

    missing = int((out["Unit_Number"] == "").sum())
    if missing:
        log.warning(
            "%d of %d condo rows have no unit number in the situs address — "
            "check the situs field mapping before relying on the Building index",
            missing,
            len(out),
        )
    return out


def building_index(units: pd.DataFrame) -> pd.DataFrame:
    """One row per building: unit count, LLC/absentee share, median value.

    This is the prioritisation tab — which towers are worth working first.
    """
    if units.empty or "Building" not in units.columns:
        return pd.DataFrame(
            columns=["Building", "Units", "LLC Owned", "LLC %", "Absentee", "Absentee %", "Median Value"]
        )

    frame = units.copy()
    key = "Folio" if "Folio" in frame.columns else frame.columns[0]
    frame["_value"] = pd.to_numeric(frame.get("Just/Market Value"), errors="coerce")
    frame["_llc"] = (frame.get("Entity", pd.Series("", index=frame.index)) == "Y").astype(int)
    frame["_abs"] = (frame.get("Absentee", pd.Series("", index=frame.index)) == "Y").astype(int)

    idx = (
        frame.groupby("Building")
        .agg(
            Units=(key, "nunique"),
            **{"LLC Owned": ("_llc", "sum")},
            Absentee=("_abs", "sum"),
            **{"Median Value": ("_value", "median")},
        )
        .reset_index()
    )
    idx["LLC %"] = (100 * idx["LLC Owned"] / idx["Units"]).round(1)
    idx["Absentee %"] = (100 * idx["Absentee"] / idx["Units"]).round(1)
    idx["Median Value"] = idx["Median Value"].round(0)
    return idx[
        ["Building", "Units", "LLC Owned", "LLC %", "Absentee", "Absentee %", "Median Value"]
    ].sort_values(["Units", "Building"], ascending=[False, True]).reset_index(drop=True)
