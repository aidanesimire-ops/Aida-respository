"""KML export — the call list as map layers for Google Earth.

One KML per workbook: each asset class becomes its own folder you can toggle,
each parcel a pin whose balloon carries the dial-sheet fields (owner, mailing
address, absentee/entity flags, value, frontage, managers). Pins are placed at
parcel centroids by default because a few thousand polygons make Google Earth
crawl; pass ``polygons=True`` when you want the lot outlines instead.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping, Sequence
from xml.sax.saxutils import escape

import geopandas as gpd
import pandas as pd

log = logging.getLogger(__name__)

# KML colors are aabbggrr (alpha, blue, green, red) — not rrggbb.
GROUP_COLORS: dict[str, str] = {
    "Residential": "ff4b9fff",  # orange-ish
    "Land": "ff4bd44b",  # green
    "Office": "ffe0a14b",  # blue-grey
    "Commercial": "ff4b4bd4",  # red
    "Hospitality": "ffd44bd4",  # magenta
    "Specialty": "ff00d7ff",  # yellow
    "Condo": "ffff9e4b",  # light blue
}
DEFAULT_COLOR = "ffcccccc"

# Balloon fields, in the order a caller wants to read them.
BALLOON_FIELDS = (
    "Owner 1",
    "Owner 2",
    "Mailing Address",
    "Mailing City",
    "Absentee",
    "Entity",
    "Entity Type",
    "Managers/Members",
    "Registered Agent",
    "Just/Market Value",
    "DOR Use",
    "Use Description",
    "Bldg SqFt",
    "Waterfront Type",
    "Water Body",
    "Frontage (ft)",
    "Unit #",
    "Folio",
)


def _style(group: str) -> str:
    color = GROUP_COLORS.get(group, DEFAULT_COLOR)
    ident = _style_id(group)
    return f"""  <Style id="{ident}">
    <IconStyle><color>{color}</color><scale>0.9</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
    <LineStyle><color>{color}</color><width>2</width></LineStyle>
    <PolyStyle><color>7f{color[2:]}</color></PolyStyle>
    <BalloonStyle><text><![CDATA[$[description]]]></text></BalloonStyle>
  </Style>"""


def _style_id(group: str) -> str:
    return "grp_" + "".join(c if c.isalnum() else "_" for c in str(group).lower())


def _balloon(row: pd.Series) -> str:
    """An HTML table of the populated dial-sheet fields."""
    cells = []
    for field in BALLOON_FIELDS:
        value = row.get(field)
        if value is None or (isinstance(value, float) and pd.isna(value)):
            continue
        text = str(value).strip()
        if not text or text.lower() == "nan":
            continue
        if field == "Just/Market Value":
            try:
                text = f"${float(value):,.0f}"
            except (TypeError, ValueError):
                pass
        cells.append(
            f"<tr><td><b>{escape(field)}</b></td><td>{escape(text)}</td></tr>"
        )
    if not cells:
        return ""
    return "<table>" + "".join(cells) + "</table>"


def _coords(geom) -> str:
    """Outer-ring coordinates for a polygon, in KML lon,lat order."""
    poly = max(geom.geoms, key=lambda g: g.area) if geom.geom_type == "MultiPolygon" else geom
    return " ".join(f"{x:.7f},{y:.7f},0" for x, y in poly.exterior.coords)


def _placemark(row: pd.Series, geom, style: str, *, polygons: bool) -> str | None:
    if geom is None or geom.is_empty:
        return None

    label = str(row.get("Situs Address") or row.get("Unit Address") or row.get("Folio") or "").strip()
    description = _balloon(row)
    body = f"      <description><![CDATA[{description}]]></description>\n" if description else ""

    if polygons and geom.geom_type in ("Polygon", "MultiPolygon"):
        shape = (
            "      <Polygon><outerBoundaryIs><LinearRing>"
            f"<coordinates>{_coords(geom)}</coordinates>"
            "</LinearRing></outerBoundaryIs></Polygon>\n"
        )
    else:
        point = geom.centroid
        shape = f"      <Point><coordinates>{point.x:.7f},{point.y:.7f},0</coordinates></Point>\n"

    return (
        "    <Placemark>\n"
        f"      <name>{escape(label)}</name>\n"
        f"      <styleUrl>#{style}</styleUrl>\n"
        f"{body}{shape}"
        "    </Placemark>"
    )


def write_kml(
    path: str | Path,
    layers: Mapping[str, tuple[gpd.GeoDataFrame, pd.DataFrame, str]],
    *,
    document_name: str,
    polygons: bool = False,
) -> Path:
    """Write one KML with a folder per layer.

    ``layers`` maps a folder name to ``(geometry frame, sheet frame, group)``:
    the geometry frame supplies position, the sheet frame supplies the balloon
    columns already renamed to their call-sheet headers, and the group picks the
    pin color. Both frames must share a row order.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    groups = {group for _, _, group in layers.values()}
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        "<Document>",
        f"  <name>{escape(document_name)}</name>",
        *[_style(group) for group in sorted(groups)],
    ]

    total = 0
    for folder, (geo, sheet, group) in layers.items():
        if geo.empty:
            continue
        geo_wgs = geo.to_crs(4326) if geo.crs and geo.crs.to_epsg() != 4326 else geo
        style = _style_id(group)
        placemarks = []
        for (_, row), geom in zip(sheet.iterrows(), geo_wgs.geometry, strict=False):
            mark = _placemark(row, geom, style, polygons=polygons)
            if mark:
                placemarks.append(mark)
        if not placemarks:
            continue
        total += len(placemarks)
        parts.append(f"  <Folder>\n    <name>{escape(folder)} ({len(placemarks)})</name>")
        parts.extend(placemarks)
        parts.append("  </Folder>")

    parts.extend(["</Document>", "</kml>"])
    path.write_text("\n".join(parts), encoding="utf-8")
    log.info("wrote %s (%d placemarks)", path, total)
    return path
