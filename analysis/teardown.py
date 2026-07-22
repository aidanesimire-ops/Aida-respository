#!/usr/bin/env python3
"""
Teardown / land-play screen: single-family listings where the LAND is most of the
value -- buy for the lot, build new. In waterfront Fort Lauderdale these are the core
development plays.

land_value = neighborhood implied land $/sqft-of-lot x lot size.
Flags a listing when land_value >= 60% of the ask (the structure is a rounding error),
or an old home (>=40 yrs) on a lot whose land is >= 45% of the ask.

Reads mls_all_valued.csv + mls_bundle.json.
Output: teardown_candidates.csv + teardown_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
EDGES = [0, 1e6, 2e6, 3e6, 5e6, 10e6, np.inf]
LABELS = ["<$1M", "$1M–$2M", "$2M–$3M", "$3M–$5M", "$5M–$10M", "$10M+"]


def _actual_land():
    """Neighborhood -> actual sold land $/sqft, from the comp layer, where a Fort
    Lauderdale neighborhood has enough vacant-land sales to trust the median."""
    try:
        with open(os.path.join(PROC, "land_bundle.json")) as f:
            lb = json.load(f)
    except FileNotFoundError:
        return {}
    return {r["neighborhood"]: r["land_ppsf"] for r in lb.get("by_neighborhood", [])
            if r.get("in_improved") and r.get("n_sold", 0) >= 3 and r.get("land_ppsf")}


def main():
    df = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    with open(os.path.join(PROC, "mls_bundle.json")) as f:
        nbh = {n["neighborhood"]: n for n in json.load(f)["neighborhoods"]}
    actual_land = _actual_land()   # comp-backed land $/sqft where available

    d = df[df["status"].isin(["Active", "Pending"]) & (df["ptype"] == "Single Family")
           & df["lot_sqft"].gt(1000) & df["price"].gt(0)].copy()
    rows = []
    for _, r in d.iterrows():
        # prefer actual vacant-land comps; fall back to the hedonic-implied land value
        comp_ppsf = actual_land.get(r["neighborhood"])
        land_ppsf = comp_ppsf or nbh.get(r["neighborhood"], {}).get("implied_land_ppsf")
        basis = "comp" if comp_ppsf else "implied"
        if not land_ppsf:
            continue
        land_val = land_ppsf * r["lot_sqft"]
        share = land_val / r["price"]
        old = pd.notna(r.get("age")) and r["age"] >= 40
        if share >= 0.60 or (old and share >= 0.45):
            rows.append({
                "band": str(pd.cut([r["price"]], EDGES, labels=LABELS, right=False)[0]),
                "address": r["address"], "neighborhood": r["neighborhood"],
                "geo_type": r["geo_type"], "waterfront": bool(r.get("waterfront")),
                "list_price": int(r["price"]), "sqft": int(r["sqft"]),
                "lot_sqft": int(r["lot_sqft"]),
                "year_built": int(r["year_built"]) if pd.notna(r.get("year_built")) else None,
                "land_value": int(round(land_val, -3)),
                "land_share_pct": round(share * 100, 0),
                "land_ppsf": round(land_ppsf, 0),
                "land_basis": basis,
                "note": ("Land alone is ~{:.0f}% of the ask ({} land value{}).".format(
                    share * 100, "comp-backed" if basis == "comp" else "implied",
                    f"; {int(r['year_built'])} structure" if pd.notna(r.get("year_built")) else "")),
            })
    t = pd.DataFrame(rows).sort_values("land_share_pct", ascending=False)
    t.to_csv(os.path.join(PROC, "teardown_candidates.csv"), index=False)

    bundle = {
        "meta": {"n": int(len(t)),
                 "n_waterfront": int(t["waterfront"].sum()) if len(t) else 0,
                 "n_comp_backed": int((t["land_basis"] == "comp").sum()) if len(t) else 0},
        "candidates": json.loads(t.head(200).to_json(orient="records")),
    }
    with open(os.path.join(PROC, "teardown_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"Teardown / land plays: {bundle['meta']['n']} SFR listings "
          f"({bundle['meta']['n_waterfront']} waterfront)")
    for _, r in t.head(4).iterrows():
        print(f"  {r['address'][:30]:30s} {r['neighborhood'][:16]:16s} ${r['list_price']/1e6:.1f}M "
              f"| land ${r['land_value']/1e6:.1f}M ({r['land_share_pct']:.0f}%) | lot {r['lot_sqft']:,}")


if __name__ == "__main__":
    main()
