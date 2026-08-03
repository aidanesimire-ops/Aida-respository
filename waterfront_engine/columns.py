"""Output column layout: source attribute -> call-sheet header, in dial order."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .config import Market
from .sunbiz import ENRICHMENT_COLS

SUNBIZ_HEADERS = {
    "Sunbiz_Entity": "Sunbiz Entity",
    "Sunbiz_Status": "Sunbiz Status",
    "Managers_Members": "Managers/Members",
    "Registered_Agent": "Registered Agent",
    "Sunbiz_Principal_Address": "Sunbiz Principal Address",
    "Sunbiz_DocNumber": "Sunbiz Doc #",
    "Sunbiz_URL": "Sunbiz URL",
}


def ownership_layout(market: Market) -> list[tuple[str, str]]:
    """(source column, output header) pairs for a Workbook 1 tab."""
    pairs: list[tuple[str, str]] = [
        (market.f("folio"), "Folio"),
        (market.f("situs"), "Situs Address"),
        ("Asset_Group", "Group"),
        ("Asset_Class", "Asset Class"),
        (market.f("use"), "DOR Use"),
        (market.f("usedesc"), "Use Description"),
        (market.f("owner1"), "Owner 1"),
    ]
    for key, header in (("owner2", "Owner 2"), ("owners", "Owner (full)")):
        name = market.opt(key)
        if name:
            pairs.append((name, header))
    pairs += [
        (market.f("mail"), "Mailing Address"),
        (market.f("mailcity"), "Mailing City"),
        ("Absentee_YN", "Absentee"),
        ("Entity_YN", "Entity"),
        ("Entity_Type", "Entity Type"),
        (market.f("value"), "Just/Market Value"),
    ]
    for key, header in (("sqft", "Bldg SqFt"), ("bldgs", "# Bldgs")):
        name = market.opt(key)
        if name:
            pairs.append((name, header))
    pairs += [
        ("Waterfront_Type", "Waterfront Type"),
        ("Water_Body", "Water Body"),
        ("Frontage_Ft", "Frontage (ft)"),
    ]
    pairs += [(col, SUNBIZ_HEADERS[col]) for col in ENRICHMENT_COLS]
    return pairs


def condo_layout(market: Market) -> list[tuple[str, str]]:
    """(source column, output header) pairs for the Workbook 2 Units tab."""
    pairs: list[tuple[str, str]] = [
        (market.f("folio"), "Folio"),
        ("Unit_Address", "Unit Address"),
        ("Building", "Building"),
        ("Unit_Number", "Unit #"),
        (market.f("owner1"), "Owner 1"),
    ]
    for key, header in (("owner2", "Owner 2"), ("owners", "Owner (full)")):
        name = market.opt(key)
        if name:
            pairs.append((name, header))
    pairs += [
        (market.f("mail"), "Mailing Address"),
        (market.f("mailcity"), "Mailing City"),
        ("Absentee_YN", "Absentee"),
        ("Entity_YN", "Entity"),
        ("Entity_Type", "Entity Type"),
        (market.f("value"), "Just/Market Value"),
    ]
    sqft = market.opt("sqft")
    if sqft:
        pairs.append((sqft, "Bldg SqFt"))
    for key, header in (("saledate", "Last Sale Date"), ("saleprice", "Last Sale Price")):
        name = market.opt(key)
        if name:
            pairs.append((name, header))
    pairs += [(col, SUNBIZ_HEADERS[col]) for col in ENRICHMENT_COLS]
    return pairs


def to_sheet(frame: pd.DataFrame | gpd.GeoDataFrame, layout: list[tuple[str, str]]) -> pd.DataFrame:
    """Project a working frame onto its output layout, dropping geometry.

    Columns absent from the source (an optional field this county doesn't
    publish, Sunbiz columns on an un-enriched run) are simply skipped.
    """
    if isinstance(frame, gpd.GeoDataFrame) or "geometry" in frame.columns:
        frame = pd.DataFrame(frame).drop(columns=["geometry"], errors="ignore")

    present = [(src, out) for src, out in layout if src in frame.columns]
    if not present:
        # An asset class with no rows still gets a full, usable (empty) call sheet.
        return pd.DataFrame(columns=[out for _, out in layout])

    sheet = frame[[src for src, _ in present]].copy()
    sheet.columns = [out for _, out in present]
    return sheet.reset_index(drop=True)
