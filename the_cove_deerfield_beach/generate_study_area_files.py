#!/usr/bin/env python3
"""
generate_study_area_files.py
----------------------------
Generate clean deliverables from the OFFICIAL / PROVIDED boundary
"Cove Waterfront District Study Area" (extracted verbatim from the supplied
KMZ: 01__Cove_Waterfront_District_Study_Area.kmz). No network required.

Unlike the earlier interpretive polygon, this geometry is authoritative and is
preserved exactly (no simplification) - only closure is enforced.

Outputs (in this folder):
  - the_cove_waterfront_district_study_area.kml       (Google My Maps)
  - the_cove_waterfront_district_study_area.geojson
  - the_cove_waterfront_district_study_area_points.csv
"""
import csv, json, math
from shapely.geometry import Polygon

CREATED_DATE = "2026-07-03"

# 32 vertices [lon, lat], verbatim from the provided KMZ study-area polygon.
COORDS = [
 [-80.09064, 26.325227], [-80.0926031, 26.3262462], [-80.0947219, 26.3247556],
 [-80.0956311, 26.3238564], [-80.0959394, 26.3224188], [-80.0982705, 26.322438],
 [-80.0996788, 26.3204569], [-80.0996841, 26.3050311], [-80.0956179, 26.3050315],
 [-80.0954999, 26.3010012], [-80.0937161, 26.30096], [-80.0924811, 26.3007673],
 [-80.0923447, 26.3014301], [-80.0914369, 26.3015552], [-80.0914229, 26.3023822],
 [-80.0914389, 26.3039211], [-80.0890954, 26.3038581], [-80.0853067, 26.3026077],
 [-80.0830918, 26.3015397], [-80.0800612, 26.3014342], [-80.0792668, 26.3053238],
 [-80.0800612, 26.3090992], [-80.0808984, 26.3128745], [-80.0813063, 26.3169184],
 [-80.0805762, 26.3201882], [-80.0804044, 26.3208026], [-80.0876574, 26.3208026],
 [-80.0883874, 26.3209959], [-80.0893305, 26.3228421], [-80.0892445, 26.3240338],
 [-80.0894596, 26.3245916], [-80.09064, 26.325227],
]

COMMERCIAL_CORE = {
    "name": "The Cove Shopping Center / Commercial Core",
    "lon": -80.08765, "lat": 26.31515,
    "note": "The Cove Shopping Center, ~1574-1584 SE 3rd Ct, Deerfield Beach, FL 33441.",
}

PROPS = {
    "name": "Cove Waterfront District - Study Area",
    "neighborhood": "The Cove",
    "district": "Cove Waterfront District",
    "city": "Deerfield Beach", "county": "Broward", "state": "Florida",
    "boundary_type": "provided study-area boundary (waterfront district)",
    "official_status": "provided/official study area (from supplied KMZ) - supersedes the earlier interpretive polygon",
    "sources": "Supplied KMZ: 01__Cove_Waterfront_District_Study_Area.kmz",
    "notes": "Geometry preserved verbatim from the KMZ (32 vertices). North extends past Hillsboro Blvd to the north waterfront.",
    "created_date": CREATED_DATE,
}

KML_DESC = (
    "Cove Waterfront District - Study Area.\n\n"
    "STATUS: Provided/official study-area boundary (extracted verbatim from the supplied KMZ "
    "'01__Cove_Waterfront_District_Study_Area.kmz'). This supersedes the earlier interpretive polygon.\n\n"
    "EXTENT: ~1,040 acres / 1.63 sq mi. Bounded by US-1/Federal Highway (W) and the Intracoastal/"
    "canal waterfront (E), extending from a southern edge near the Lighthouse Point transition north "
    "past Hillsboro Blvd to the north waterfront.\n\n"
    "For planning / discussion use. Geometry is authoritative as supplied; verify against the city's "
    "official GIS if used for regulatory purposes."
)


def ring():
    r = [tuple(p) for p in COORDS]
    if r[0] != r[-1]:
        r.append(r[0])
    return r


def area_acres(r):
    lat0 = sum(p[1] for p in r) / len(r)
    k = math.cos(math.radians(lat0))
    xy = [(lo * k * 111320.0, la * 110540.0) for lo, la in r]
    s = sum(xy[i][0] * xy[i+1][1] - xy[i+1][0] * xy[i][1] for i in range(len(xy)-1))
    m2 = abs(s) / 2.0
    return m2 / 4046.8564224, m2 / 2_589_988.11


def write_kml(path, r):
    coord_str = " ".join(f"{lo:.6f},{la:.6f},0" for lo, la in r)
    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
  <name>Cove Waterfront District - Study Area (Deerfield Beach)</name>
  <description><![CDATA[{KML_DESC}]]></description>
  <Style id="cove"><LineStyle><color>ff0000ff</color><width>3</width></LineStyle>
    <PolyStyle><color>4d0000ff</color><fill>1</fill><outline>1</outline></PolyStyle></Style>
  <Style id="core"><IconStyle><color>ff0000ff</color><scale>1.1</scale>
    <Icon><href>http://maps.google.com/mapfiles/kml/shapes/shopping.png</href></Icon></IconStyle></Style>
  <Placemark><name>Cove Waterfront District - Study Area</name>
    <description><![CDATA[{KML_DESC}]]></description>
    <styleUrl>#cove</styleUrl>
    <Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>
      <coordinates>{coord_str}</coordinates>
    </LinearRing></outerBoundaryIs></Polygon></Placemark>
  <Placemark><name>{COMMERCIAL_CORE['name']}</name>
    <description><![CDATA[{COMMERCIAL_CORE['note']}]]></description>
    <styleUrl>#core</styleUrl>
    <Point><coordinates>{COMMERCIAL_CORE['lon']:.6f},{COMMERCIAL_CORE['lat']:.6f},0</coordinates></Point></Placemark>
</Document></kml>
"""
    open(path, "w").write(kml)


def write_geojson(path, r):
    fc = {"type": "FeatureCollection", "name": "cove_waterfront_district_study_area",
          "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
          "features": [
              {"type": "Feature", "properties": PROPS,
               "geometry": {"type": "Polygon", "coordinates": [[list(p) for p in r]]}},
              {"type": "Feature",
               "properties": {"name": COMMERCIAL_CORE["name"], "type": "commercial_core",
                              "note": COMMERCIAL_CORE["note"]},
               "geometry": {"type": "Point", "coordinates": [COMMERCIAL_CORE["lon"], COMMERCIAL_CORE["lat"]]}},
          ]}
    json.dump(fc, open(path, "w"), indent=2)


def write_csv(path, r):
    with open(path, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["vertex", "longitude", "latitude"])
        for i, (lo, la) in enumerate(r):
            w.writerow([i, lo, la])


def main():
    r = ring()
    poly = Polygon(r)
    write_kml("the_cove_waterfront_district_study_area.kml", r)
    write_geojson("the_cove_waterfront_district_study_area.geojson", r)
    write_csv("the_cove_waterfront_district_study_area_points.csv", r)
    ac, sqmi = area_acres(r)
    print("=== Cove Waterfront District - Study Area (from KMZ) ===")
    print(f"vertices: {len(r)} (incl. close) | valid: {poly.is_valid} | simple: {poly.is_simple}")
    print(f"area: {ac:,.1f} acres | {sqmi:.3f} sq mi")
    print("wrote KML, GeoJSON, CSV")


if __name__ == "__main__":
    main()
