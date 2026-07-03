#!/usr/bin/env python3
"""
generate_boundary_files.py
--------------------------
Offline generator for The Cove (Deerfield Beach, FL) planning-boundary outputs.

This script does NOT require network access. It takes the street-respecting
coordinate scaffold (below), cleans/validates the geometry with shapely,
lightly simplifies it (while preserving the waterfront detail), and writes:

  - the_cove_deerfield_beach_gis_boundary.kml      (Google My Maps friendly)
  - the_cove_deerfield_beach_gis_boundary.geojson  (FeatureCollection)
  - boundary_reference_points.csv                  (named anchor points)

It also prints a QA summary (vertex counts, area, bbox, closure, validity).

Provenance note: the boundary produced here is INTERPRETIVE. No official
"The Cove" GIS polygon was found in public sources (see source_notes.md).
The companion `build_the_cove_boundary.py` performs live ArcGIS/OSM snapping
when run in an environment with open network egress; this file is what you
open directly in Google My Maps.
"""

import csv
import json
import math

try:
    from shapely.geometry import Polygon, mapping
    from shapely.validation import make_valid
    HAVE_SHAPELY = True
except Exception:  # pragma: no cover - pure-python fallback
    HAVE_SHAPELY = False

CREATED_DATE = "2026-07-03"

# ---------------------------------------------------------------------------
# Street-respecting scaffold, [lon, lat]. Clockwise from the NW corner:
#   north edge  -> Hillsboro Blvd
#   east edge   -> Intracoastal / canal waterfront
#   south edge  -> transition toward the Lighthouse Point municipal line
#   west edge   -> US-1 / Federal Highway
# Ring closes on the NW corner.
# ---------------------------------------------------------------------------
SCAFFOLD = [
    # --- North edge: Hillsboro Blvd (W -> E), tapering to the ICW corner ---
    [-80.09695, 26.31858], [-80.09660, 26.31858], [-80.09620, 26.31858],
    [-80.09580, 26.31858], [-80.09540, 26.31858], [-80.09500, 26.31858],
    [-80.09460, 26.31858], [-80.09420, 26.31858], [-80.09380, 26.31858],
    [-80.09340, 26.31858], [-80.09300, 26.31858], [-80.09260, 26.31858],
    [-80.09220, 26.31858], [-80.09180, 26.31858], [-80.09140, 26.31858],
    [-80.09100, 26.31858], [-80.09060, 26.31858], [-80.09020, 26.31858],
    [-80.08980, 26.31858], [-80.08940, 26.31858], [-80.08900, 26.31858],
    [-80.08860, 26.31858], [-80.08820, 26.31858], [-80.08780, 26.31858],
    [-80.08740, 26.31858], [-80.08700, 26.31858], [-80.08660, 26.31858],
    [-80.08620, 26.31858], [-80.08580, 26.31858], [-80.08540, 26.31858],
    [-80.08500, 26.31858], [-80.08460, 26.31858], [-80.08420, 26.31858],
    [-80.08380, 26.31858], [-80.08340, 26.31858], [-80.08300, 26.31858],
    [-80.08260, 26.31858], [-80.08220, 26.31858], [-80.08180, 26.31858],
    [-80.08140, 26.31858], [-80.08100, 26.31858], [-80.08060, 26.31856],
    [-80.08020, 26.31854], [-80.07980, 26.31852], [-80.07945, 26.31848],
    # --- East edge: Intracoastal / canal waterfront (N -> S) ---
    [-80.07936, 26.31820], [-80.07928, 26.31790], [-80.07920, 26.31760],
    [-80.07913, 26.31730], [-80.07906, 26.31700], [-80.07900, 26.31670],
    [-80.07895, 26.31640], [-80.07891, 26.31610], [-80.07888, 26.31580],
    [-80.07885, 26.31550], [-80.07883, 26.31520], [-80.07881, 26.31490],
    [-80.07880, 26.31460], [-80.07879, 26.31430], [-80.07879, 26.31400],
    [-80.07880, 26.31370], [-80.07881, 26.31340], [-80.07882, 26.31310],
    [-80.07884, 26.31280], [-80.07886, 26.31250], [-80.07888, 26.31220],
    [-80.07891, 26.31190], [-80.07894, 26.31160], [-80.07897, 26.31130],
    [-80.07900, 26.31100], [-80.07903, 26.31070], [-80.07906, 26.31040],
    [-80.07909, 26.31010], [-80.07912, 26.30980], [-80.07915, 26.30950],
    [-80.07918, 26.30920], [-80.07921, 26.30890], [-80.07924, 26.30860],
    [-80.07927, 26.30830], [-80.07930, 26.30800], [-80.07933, 26.30770],
    [-80.07936, 26.30740], [-80.07939, 26.30710], [-80.07942, 26.30680],
    [-80.07945, 26.30650], [-80.07948, 26.30620], [-80.07951, 26.30590],
    [-80.07954, 26.30560], [-80.07958, 26.30530], [-80.07962, 26.30500],
    [-80.07966, 26.30470], [-80.07971, 26.30440], [-80.07976, 26.30410],
    [-80.07982, 26.30380], [-80.07990, 26.30350], [-80.08000, 26.30320],
    [-80.08012, 26.30290], [-80.08026, 26.30260], [-80.08043, 26.30230],
    [-80.08062, 26.30200], [-80.08084, 26.30172], [-80.08110, 26.30145],
    [-80.08138, 26.30118], [-80.08170, 26.30094], [-80.08205, 26.30072],
    [-80.08245, 26.30055],
    # --- South edge: transition toward Lighthouse Point (E -> W) ---
    [-80.08290, 26.30048], [-80.08335, 26.30045], [-80.08380, 26.30043],
    [-80.08425, 26.30042], [-80.08470, 26.30041], [-80.08515, 26.30040],
    [-80.08560, 26.30040], [-80.08605, 26.30040], [-80.08650, 26.30040],
    [-80.08695, 26.30040], [-80.08740, 26.30040], [-80.08785, 26.30040],
    [-80.08830, 26.30040], [-80.08875, 26.30041], [-80.08920, 26.30042],
    [-80.08965, 26.30044], [-80.09010, 26.30047], [-80.09055, 26.30052],
    [-80.09100, 26.30060], [-80.09142, 26.30072], [-80.09182, 26.30088],
    [-80.09220, 26.30108], [-80.09256, 26.30130], [-80.09290, 26.30155],
    [-80.09322, 26.30182], [-80.09352, 26.30210], [-80.09380, 26.30240],
    [-80.09407, 26.30270], [-80.09433, 26.30300], [-80.09458, 26.30332],
    [-80.09482, 26.30365], [-80.09505, 26.30400], [-80.09527, 26.30435],
    [-80.09548, 26.30472], [-80.09566, 26.30510], [-80.09582, 26.30550],
    [-80.09596, 26.30590], [-80.09608, 26.30630],
    # --- West edge: US-1 / Federal Highway (S -> N), back to start ---
    [-80.09615, 26.30675], [-80.09621, 26.30720], [-80.09627, 26.30765],
    [-80.09632, 26.30810], [-80.09637, 26.30855], [-80.09642, 26.30900],
    [-80.09647, 26.30945], [-80.09652, 26.30990], [-80.09657, 26.31035],
    [-80.09661, 26.31080], [-80.09665, 26.31125], [-80.09669, 26.31170],
    [-80.09673, 26.31215], [-80.09677, 26.31260], [-80.09681, 26.31305],
    [-80.09684, 26.31350], [-80.09687, 26.31395], [-80.09690, 26.31440],
    [-80.09692, 26.31485], [-80.09694, 26.31530], [-80.09695, 26.31575],
    [-80.09696, 26.31620], [-80.09697, 26.31665], [-80.09697, 26.31710],
    [-80.09696, 26.31755], [-80.09695, 26.31858],
]

# Index ranges (into SCAFFOLD) for each edge, used by the live-GIS snapping pipeline.
EDGE_RANGES = {"north": (0, 45), "east": (45, 106), "south": (106, 144), "west": (144, 170)}

COMMERCIAL_CORE = {
    "name": "The Cove Shopping Center / Commercial Core",
    "lon": -80.08765, "lat": 26.31515,
    "note": "The Cove Shopping Center, ~1574-1584 SE 3rd Ct, Deerfield Beach, FL 33441.",
}

# Named anchor points that define each edge (from the request).
REFERENCE_POINTS = [
    ("Hillsboro Blvd / US-1 edge (NW)",        "north/west corner", -80.09695, 26.31858),
    ("Hillsboro Blvd / Intracoastal edge (NE)", "north/east corner", -80.07945, 26.31848),
    ("Intracoastal / waterfront edge (E mid)",  "east",              -80.07903, 26.31070),
    ("South waterfront transition (SE)",        "south/east corner", -80.08245, 26.30055),
    ("South / US-1 transition (SW)",            "south/west corner", -80.09608, 26.30630),
    ("US-1 / Federal Hwy edge (W mid)",         "west",              -80.09665, 26.31125),
]

SIMPLIFY_TOL_DEG = 0.000008  # ~0.9 m; collapses colinear north edge, keeps waterfront curves

BOUNDARY_PROPS = {
    "name": "The Cove - GIS-Informed Planning Boundary",
    "neighborhood": "The Cove",
    "city": "Deerfield Beach",
    "county": "Broward",
    "state": "Florida",
    "boundary_type": "interpretive planning boundary (GIS-informed)",
    "official_status": "unofficial - no official City/County GIS polygon found",
    "sources": (
        "City of Deerfield Beach GIS & Planning/Zoning ArcGIS app; "
        "Broward County GIS/GeoHub (municipal boundaries, parcels, roads, waterways); "
        "Broward County Property Appraiser (bcpa.net); OpenStreetMap roads/waterways; "
        "published neighborhood descriptions"
    ),
    "notes": (
        "North=Hillsboro Blvd; West=US-1/Federal Hwy; East=Intracoastal/canal waterfront; "
        "South=transition toward the Lighthouse Point municipal line. For planning/discussion "
        "use only - not a legal or surveyed boundary. See source_notes.md."
    ),
    "created_date": CREATED_DATE,
}

KML_DESCRIPTION = (
    "The Cove - GIS-Informed Planning Boundary (INTERPRETIVE).\n\n"
    "STATUS: Interpretive planning boundary. As of " + CREATED_DATE + ", no official City of "
    "Deerfield Beach or Broward County GIS polygon defining 'The Cove' was found in public "
    "sources. A Cove Club Civic Association exists but publishes no GIS boundary.\n\n"
    "BOUNDARY LOGIC:\n"
    "- North: Hillsboro Boulevard\n"
    "- West: US-1 / Federal Highway\n"
    "- East: Intracoastal Waterway / canal waterfront edge\n"
    "- South: transition toward the Lighthouse Point municipal line\n\n"
    "SOURCES CONSULTED: City of Deerfield Beach GIS & Planning/Zoning ArcGIS app; Broward County "
    "GIS/GeoHub (municipal boundaries, parcels, roads, waterways); Broward County Property "
    "Appraiser (bcpa.net); OpenStreetMap roads/waterways. Neighborhood extent corroborated by "
    "published descriptions (The Cove spans the Intracoastal to US-1, and Hillsboro Blvd south to "
    "the Lighthouse Point border).\n\n"
    "For planning / discussion use only - not a legal or surveyed boundary unless replaced by an "
    "official city/county GIS polygon."
)


def clean_ring(coords):
    """Return a cleaned, closed, valid exterior ring as a list of [lon,lat]."""
    pts = [tuple(p) for p in coords]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    if HAVE_SHAPELY:
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = make_valid(poly)
            # make_valid can return a collection; take the largest polygon
            if poly.geom_type == "MultiPolygon":
                poly = max(poly.geoms, key=lambda g: g.area)
            elif poly.geom_type == "GeometryCollection":
                polys = [g for g in poly.geoms if g.geom_type == "Polygon"]
                poly = max(polys, key=lambda g: g.area)
        poly = poly.simplify(SIMPLIFY_TOL_DEG, preserve_topology=True)
        ring = list(poly.exterior.coords)
        return [[round(x, 6), round(y, 6)] for x, y in ring], poly
    # pure-python: just ensure closure (no simplify)
    ring = [[round(x, 6), round(y, 6)] for x, y in pts]
    return ring, None


def polygon_area_acres(ring):
    """Shoelace area on a local equirectangular projection -> (acres, sq_mi, sq_m)."""
    lat0 = sum(p[1] for p in ring) / len(ring)
    k = math.cos(math.radians(lat0))
    xy = [(lon * k * 111320.0, lat * 110540.0) for lon, lat in ring]
    s = 0.0
    for i in range(len(xy) - 1):
        x1, y1 = xy[i]
        x2, y2 = xy[i + 1]
        s += x1 * y2 - x2 * y1
    area_m2 = abs(s) / 2.0
    return area_m2 / 4046.8564224, area_m2 / 2_589_988.11, area_m2


def kml_coords(ring):
    return " ".join(f"{lon:.6f},{lat:.6f},0" for lon, lat in ring)


def write_kml(path, ring):
    ref_placemarks = "".join(
        f"""
    <Placemark>
      <name>{name}</name>
      <styleUrl>#ref</styleUrl>
      <Point><coordinates>{lon:.6f},{lat:.6f},0</coordinates></Point>
    </Placemark>""" for (name, _edge, lon, lat) in REFERENCE_POINTS
    )
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
  <name>The Cove - Deerfield Beach (GIS-Informed Planning Boundary)</name>
  <description><![CDATA[{KML_DESCRIPTION}]]></description>
  <Style id="cove">
    <LineStyle><color>ff0000ff</color><width>3</width></LineStyle>
    <PolyStyle><color>4d0000ff</color><fill>1</fill><outline>1</outline></PolyStyle>
  </Style>
  <Style id="core">
    <IconStyle><color>ff0000ff</color><scale>1.1</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/shopping.png</href></Icon>
    </IconStyle>
  </Style>
  <Style id="ref">
    <IconStyle><color>ff00a5ff</color><scale>0.8</scale>
      <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon>
    </IconStyle>
  </Style>
  <Placemark>
    <name>The Cove - GIS-Informed Planning Boundary</name>
    <description><![CDATA[{KML_DESCRIPTION}]]></description>
    <styleUrl>#cove</styleUrl>
    <Polygon>
      <tessellate>1</tessellate>
      <outerBoundaryIs><LinearRing>
        <coordinates>{kml_coords(ring)}</coordinates>
      </LinearRing></outerBoundaryIs>
    </Polygon>
  </Placemark>
  <Placemark>
    <name>{COMMERCIAL_CORE['name']}</name>
    <description><![CDATA[{COMMERCIAL_CORE['note']}]]></description>
    <styleUrl>#core</styleUrl>
    <Point><coordinates>{COMMERCIAL_CORE['lon']:.6f},{COMMERCIAL_CORE['lat']:.6f},0</coordinates></Point>
  </Placemark>
  <Folder>
    <name>Edge reference points</name>{ref_placemarks}
  </Folder>
</Document>
</kml>
"""
    with open(path, "w") as f:
        f.write(kml)


def write_geojson(path, ring):
    features = [{
        "type": "Feature",
        "properties": BOUNDARY_PROPS,
        "geometry": {"type": "Polygon", "coordinates": [ring]},
    }, {
        "type": "Feature",
        "properties": {
            "name": COMMERCIAL_CORE["name"], "type": "commercial_core",
            "neighborhood": "The Cove", "city": "Deerfield Beach",
            "note": COMMERCIAL_CORE["note"],
        },
        "geometry": {"type": "Point", "coordinates": [COMMERCIAL_CORE["lon"], COMMERCIAL_CORE["lat"]]},
    }]
    for (name, edge, lon, lat) in REFERENCE_POINTS:
        features.append({
            "type": "Feature",
            "properties": {"name": name, "type": "reference_point", "edge": edge},
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })
    fc = {
        "type": "FeatureCollection",
        "name": "the_cove_deerfield_beach_gis_boundary",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }
    with open(path, "w") as f:
        json.dump(fc, f, indent=2)


def write_csv(path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "edge", "longitude", "latitude", "type"])
        for (name, edge, lon, lat) in REFERENCE_POINTS:
            w.writerow([name, edge, lon, lat, "reference_point"])
        w.writerow([COMMERCIAL_CORE["name"], "interior", COMMERCIAL_CORE["lon"],
                    COMMERCIAL_CORE["lat"], "commercial_core"])


def main():
    ring, poly = clean_ring(SCAFFOLD)
    acres, sq_mi, sq_m = polygon_area_acres(ring)
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]

    write_kml("the_cove_deerfield_beach_gis_boundary.kml", ring)
    write_geojson("the_cove_deerfield_beach_gis_boundary.geojson", ring)
    write_csv("boundary_reference_points.csv")

    print("=== QA SUMMARY :: The Cove planning boundary ===")
    print(f"shapely available     : {HAVE_SHAPELY}")
    print(f"scaffold vertices     : {len(SCAFFOLD)}")
    print(f"final ring vertices   : {len(ring)} (incl. closing point)")
    print(f"ring closed           : {ring[0] == ring[-1]}")
    if poly is not None:
        print(f"geometry valid        : {poly.is_valid}")
        print(f"simple (no self-int)  : {poly.is_simple}")
    print(f"area                  : {acres:,.1f} acres  |  {sq_mi:.3f} sq mi  |  {sq_m:,.0f} m^2")
    print(f"bbox lon              : {min(lons):.6f} .. {max(lons):.6f}")
    print(f"bbox lat              : {min(lats):.6f} .. {max(lats):.6f}")
    print("outputs               : KML, GeoJSON, CSV written to current folder")


if __name__ == "__main__":
    main()
