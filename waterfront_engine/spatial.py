"""Waterfront frontage join and barrier-island (beach) filtering."""

from __future__ import annotations

import logging

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

from .config import Market

log = logging.getLogger(__name__)

WATERFRONT_COLS = ["Waterfront_Type", "Water_Body", "Frontage_Ft"]
_POLY = {"Polygon", "MultiPolygon"}


def buffer_water(water: gpd.GeoDataFrame, market: Market) -> gpd.GeoDataFrame:
    """Project hydrography to the market CRS and buffer it by ``water_buffer_ft``.

    The buffer absorbs the small gap between a parcel edge and the mapped water
    edge; the frontage test downstream is what actually decides waterfront.
    """
    if water.empty:
        raise ValueError("water layer is empty — check the water layer id / filter")

    projected = water.to_crs(market.proj_crs)
    if market.water_type_exclude and market.water_type_field in projected.columns:
        before = len(projected)
        keep = ~projected[market.water_type_field].astype("string").fillna("").str.contains(
            market.water_type_exclude, case=False, regex=True, na=False
        )
        projected = projected[keep]
        log.info(
            "water_type_exclude dropped %d of %d water features", before - len(projected), before
        )
    if projected.empty:
        raise ValueError("water_type_exclude filtered out every water feature")

    buffered = projected.copy()
    buffered["geometry"] = projected.geometry.buffer(market.water_buffer_ft)
    return buffered


def _attr(row: pd.Series, field: str | None) -> str:
    if not field:
        return ""
    value = row.get(field)
    return "" if value is None or pd.isna(value) else str(value)


def waterfront(
    parcels: gpd.GeoDataFrame,
    water_buffered: gpd.GeoDataFrame,
    market: Market,
) -> gpd.GeoDataFrame:
    """Keep parcels with real water frontage, tagged with type/body/length.

    A parcel qualifies when the length of its boundary lying inside the buffered
    water is at least ``min_frontage_ft`` — that threshold is what rejects a
    parcel that merely clips a canal at one corner. The attributed water body is
    the one contributing the most frontage, not an arbitrary first match.

    ``Frontage_Ft`` is that measured length, so it reads long by up to about two
    buffer widths: the buffer wraps a lot's corners and picks up a little of each
    side lot line. Treat it as "water-facing width, plus slop" — good for sorting
    a call list, not a survey number. Non-polygon parcels (a layer that serves
    centroids) cannot be measured and are kept on intersection alone.
    """
    empty = _empty_like(parcels)
    if parcels.empty:
        return empty

    projected = parcels.to_crs(market.proj_crs)
    water_cols = [
        c for c in (market.water_name_field, market.water_type_field) if c and c in water_buffered.columns
    ]
    right = water_buffered[water_cols + ["geometry"]]

    pairs = gpd.sjoin(projected, right, how="inner", predicate="intersects")
    if pairs.empty:
        log.info("no parcels intersect water")
        return empty

    non_poly = ~projected.geometry.geom_type.isin(_POLY)
    if non_poly.any():
        log.warning(
            "%d parcels are not polygons (points/lines) — frontage length cannot be "
            "measured for them; they are kept on an intersects-only basis",
            int(non_poly.sum()),
        )

    records: list[dict[str, object]] = []
    for parcel_idx, matches in pairs.groupby(level=0):
        geom = projected.geometry.loc[parcel_idx]
        if geom is None or geom.is_empty:
            continue

        is_polygon = geom.geom_type in _POLY
        boundary = geom.boundary if is_polygon else geom

        best_len, best_row = -1.0, matches.iloc[0]
        lengths: list[float] = []
        for _, match in matches.iterrows():
            water_geom = water_buffered.geometry.loc[match["index_right"]]
            piece = boundary.intersection(water_geom)
            length = float(getattr(piece, "length", 0.0))
            lengths.append(length)
            if length > best_len:
                best_len, best_row = length, match

        if len(matches) == 1:
            total = lengths[0]
        else:
            merged = unary_union(
                [water_buffered.geometry.loc[i] for i in matches["index_right"]]
            )
            total = float(boundary.intersection(merged).length)

        if is_polygon and total < market.min_frontage_ft:
            continue

        records.append(
            {
                "_idx": parcel_idx,
                "Waterfront_Type": _attr(best_row, market.water_type_field),
                "Water_Body": _attr(best_row, market.water_name_field),
                "Frontage_Ft": round(total, 1) if is_polygon else None,
            }
        )

    if not records:
        return empty

    tags = pd.DataFrame(records).set_index("_idx")
    kept = parcels.loc[tags.index].copy()
    for col in WATERFRONT_COLS:
        kept[col] = tags[col]
    log.info("waterfront: %d of %d parcels", len(kept), len(parcels))
    return kept


def _empty_like(parcels: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    empty = parcels.iloc[0:0].copy()
    for col in WATERFRONT_COLS:
        empty[col] = pd.Series(dtype="object")
    return empty


def beach_filter(
    parcels: gpd.GeoDataFrame,
    market: Market,
    boundary_path: str | None = None,
) -> gpd.GeoDataFrame:
    """Restrict to the barrier island.

    Prefers a drawn barrier-island polygon when the config supplies one; falls
    back to the longitude threshold, which is the quick approximation and the
    thing to eyeball on satellite before dialing.
    """
    if parcels.empty:
        return parcels

    if boundary_path:
        island = gpd.read_file(boundary_path).to_crs(parcels.crs)
        joined = gpd.sjoin(
            parcels, island[["geometry"]], how="inner", predicate="intersects"
        )
        kept = parcels.loc[joined.index.unique()].copy()
        log.info("beach filter (polygon %s): %d of %d", boundary_path, len(kept), len(parcels))
        return kept

    if market.beach_lon_threshold is None:
        log.warning("no beach polygon and no beach_lon_threshold — keeping all parcels")
        return parcels

    lon = centroid_lon(parcels, market)
    keep = lon > market.beach_lon_threshold if market.beach_side == "east" else lon < market.beach_lon_threshold
    kept = parcels[keep].copy()
    kept["Centroid_Lon"] = lon[keep].round(6)
    log.info(
        "beach filter (lon %s %s): %d of %d",
        ">" if market.beach_side == "east" else "<",
        market.beach_lon_threshold,
        len(kept),
        len(parcels),
    )
    return kept


def centroid_lon(parcels: gpd.GeoDataFrame, market: Market) -> pd.Series:
    """Centroid longitude in WGS84, computed in the projected CRS to stay honest."""
    centroids = parcels.to_crs(market.proj_crs).geometry.centroid.to_crs(4326)
    return pd.Series(centroids.x, index=parcels.index)
