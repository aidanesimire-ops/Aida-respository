#!/usr/bin/env python3
"""
Enrich the MLS data with PUBLIC datasets: geocoding, Census ACS demographics,
FEMA flood zones, and Broward County Property Appraiser assessed values.

    python analysis/enrich_public.py

WHY THIS IS A SEPARATE SCRIPT
-----------------------------
The environment this project was built in blocks the required hosts at the network
layer (geocoding.geo.census.gov, api.census.gov, hazards.fema.gov, and the Broward
GIS / BCPA endpoints all return 403 at the egress proxy). This script is written and
ready — run it anywhere with open outbound HTTPS (a laptop, a CI runner) and it will
geocode every address and append:

  lat, lon, census_tract, flood_zone,
  tract_median_income, tract_median_home_value, tract_owner_occupied_pct,
  bcpa_land_value, bcpa_building_value      (land-vs-structure split, per parcel)

Outputs: data/processed/mls_enriched.csv  and  data/processed/enrichment_by_neighborhood.csv

Each source is independent and fails soft: if one host is unreachable the others still
run and their columns are filled. Requires `requests` (pip install requests).
"""
from __future__ import annotations
import io
import os
import sys
import time

import pandas as pd

try:
    import requests
except ImportError:
    sys.exit("This script needs `requests`:  pip install requests")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
CLEAN = os.path.join(PROC, "mls_clean_all.csv")

CITY, STATE = "Fort Lauderdale", "FL"
ACS_YEAR = 2022
BROWARD = {"state": "12", "county": "011"}
# Broward parcels feature service (public). Adjust the layer URL if the county
# republishes it; it must expose LANDVAL / BLDGVAL (or equivalent) fields.
BCPA_LAYER = ("https://gis.broward.org/arcgis/rest/services/CADASTRAL/"
              "MapServer/0/query")
FEMA_LAYER = ("https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/"
              "MapServer/28/query")


# --------------------------------------------------------------------------- #
def geocode_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Census batch geocoder -> lat, lon, census_tract. Up to 10k rows/request."""
    url = "https://geocoding.geo.census.gov/geocoder/geographies/addressbatch"
    out = {}
    rows = df[["_id", "address"]].dropna()
    for start in range(0, len(rows), 9000):
        chunk = rows.iloc[start:start + 9000]
        buf = io.StringIO()
        for _, r in chunk.iterrows():
            buf.write(f'{r["_id"]},"{r["address"]}","{CITY}","{STATE}",\n')
        files = {"addressFile": ("addrs.csv", buf.getvalue())}
        data = {"benchmark": "Public_AR_Current", "vintage": "Current_Current"}
        try:
            resp = requests.post(url, files=files, data=data, timeout=300)
            resp.raise_for_status()
        except Exception as e:  # noqa: BLE001
            print(f"  geocode chunk @{start} failed: {e}")
            continue
        cols = ["id", "in_addr", "match", "matchtype", "out_addr", "lonlat",
                "tigerid", "side", "state", "county", "tract", "block"]
        g = pd.read_csv(io.StringIO(resp.text), header=None, names=cols, dtype=str)
        for _, r in g.iterrows():
            if str(r["match"]).lower() == "match" and pd.notna(r["lonlat"]):
                lon, lat = r["lonlat"].split(",")
                out[r["id"]] = {
                    "lat": float(lat), "lon": float(lon),
                    "census_tract": f'{r["state"]}{r["county"]}{r["tract"]}',
                }
        print(f"  geocoded {start+len(chunk)}/{len(rows)} "
              f"({len(out)} matched so far)")
        time.sleep(1)
    return pd.DataFrame.from_dict(out, orient="index")


def acs_by_tract() -> pd.DataFrame:
    """Census ACS 5-year: income, home value, owner-occupancy per Broward tract."""
    vars_ = {"B19013_001E": "tract_median_income",
             "B25077_001E": "tract_median_home_value",
             "B25003_001E": "_occ_total", "B25003_002E": "_occ_owner"}
    url = (f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5?get=NAME,"
           + ",".join(vars_) + f"&for=tract:*&in=state:{BROWARD['state']}"
           + f"&in=county:{BROWARD['county']}")
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    rows = resp.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    for v in vars_:
        df[v] = pd.to_numeric(df[v], errors="coerce")
    df["census_tract"] = df["state"] + df["county"] + df["tract"]
    df["tract_owner_occupied_pct"] = (df["B25003_002E"] / df["B25003_001E"] * 100).round(1)
    df = df.rename(columns=vars_)
    return df[["census_tract", "tract_median_income", "tract_median_home_value",
               "tract_owner_occupied_pct"]]


def flood_zone(lat, lon):
    params = {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
              "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
              "outFields": "FLD_ZONE", "returnGeometry": "false", "f": "json"}
    try:
        r = requests.get(FEMA_LAYER, params=params, timeout=30).json()
        feats = r.get("features", [])
        return feats[0]["attributes"]["FLD_ZONE"] if feats else None
    except Exception:  # noqa: BLE001
        return None


def bcpa_values(lat, lon):
    """Land & building assessed value at a point from Broward parcels."""
    params = {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint",
              "inSR": "4326", "spatialRel": "esriSpatialRelIntersects",
              "outFields": "*", "returnGeometry": "false", "f": "json"}
    try:
        r = requests.get(BCPA_LAYER, params=params, timeout=30).json()
        a = r["features"][0]["attributes"]
        def pick(*names):
            for n in names:
                for k in a:
                    if k.upper() == n:
                        return a[k]
            return None
        return {"bcpa_land_value": pick("LANDVAL", "LND_VAL", "LAND_VALUE"),
                "bcpa_building_value": pick("BLDGVAL", "BLD_VAL", "IMPR_VALUE",
                                            "BUILDING_VALUE")}
    except Exception:  # noqa: BLE001
        return {"bcpa_land_value": None, "bcpa_building_value": None}


# --------------------------------------------------------------------------- #
def main():
    if not os.path.exists(CLEAN):
        sys.exit("Run mls_normalize.py first (needs data/processed/mls_clean_all.csv).")
    df = pd.read_csv(CLEAN)
    # rebuild a full address (the clean file dropped the raw street; re-read raw if needed)
    if "address" not in df.columns:
        import glob
        raws = pd.concat([pd.read_csv(f) for f in glob.glob(
            os.path.join(ROOT, "data", "raw", "mls", "*.csv"))], ignore_index=True)
        df["address"] = raws["Address"].values[:len(df)]
    df["_id"] = range(len(df))

    print("1) Geocoding addresses (Census batch) ...")
    geo = geocode_batch(df)
    df = df.merge(geo, left_on="_id", right_index=True, how="left")

    print("2) Census ACS demographics by tract ...")
    try:
        df = df.merge(acs_by_tract(), on="census_tract", how="left")
    except Exception as e:  # noqa: BLE001
        print(f"  ACS failed: {e}")

    print("3) FEMA flood zone + 4) BCPA land/building value (per matched point) ...")
    fz, lv, bv = [], [], []
    for _, r in df.iterrows():
        if pd.notna(r.get("lat")):
            fz.append(flood_zone(r["lat"], r["lon"]))
            b = bcpa_values(r["lat"], r["lon"])
            lv.append(b["bcpa_land_value"]); bv.append(b["bcpa_building_value"])
        else:
            fz.append(None); lv.append(None); bv.append(None)
    df["flood_zone"], df["bcpa_land_value"], df["bcpa_building_value"] = fz, lv, bv

    df.drop(columns=["_id"]).to_csv(os.path.join(PROC, "mls_enriched.csv"), index=False)

    # per-neighborhood rollup
    agg = df.groupby("neighborhood").agg(
        flood_zone_mode=("flood_zone", lambda x: x.mode().iat[0] if len(x.mode()) else None),
        tract_median_income=("tract_median_income", "median"),
        tract_owner_occupied_pct=("tract_owner_occupied_pct", "median"),
        bcpa_land_value=("bcpa_land_value", "median"),
        bcpa_building_value=("bcpa_building_value", "median"),
    )
    agg["land_share_pct"] = (agg["bcpa_land_value"] /
                             (agg["bcpa_land_value"] + agg["bcpa_building_value"]) * 100).round(1)
    agg.to_csv(os.path.join(PROC, "enrichment_by_neighborhood.csv"))
    print("Done. Wrote mls_enriched.csv + enrichment_by_neighborhood.csv")


if __name__ == "__main__":
    main()
