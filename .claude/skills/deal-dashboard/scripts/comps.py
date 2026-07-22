#!/usr/bin/env python3
"""
Comps drill-down: the actual comparable sales behind each live valuation, so a number
can be defended in the room -- not just "the model says $X".

For every live listing >=$1M, pulls up to 5 recent SOLD comps, preferring the same
street, then the same neighborhood + price band, ranked by square-footage similarity.

Reads mls_all_valued.csv.
Output: comps_flat.csv (one row per target-comp pair) + comps_bundle.json (keyed by target)
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
MIN_TICKET = 1_000_000
N_COMPS = 5
EDGES = [0, 1e6, 2e6, 3e6, 5e6, 10e6, np.inf]
LABELS = ["<$1M", "$1M–$2M", "$2M–$3M", "$3M–$5M", "$5M–$10M", "$10M+"]


def main():
    df = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    df["band"] = pd.cut(df["price"], EDGES, labels=LABELS, right=False)
    sold = df[(df["status"] == "Sold") & df["price"].gt(0)].copy()
    live = df[df["status"].isin(["Active", "Pending"]) & (df["price"] >= MIN_TICKET)].copy()

    sold_by_street = {k: g for k, g in sold.groupby("street")}
    sold_by_nb_band = {k: g for k, g in sold.groupby(["neighborhood", "band"], observed=True)}

    flat, bundle = [], {}
    for _, r in live.iterrows():
        pool = sold_by_street.get(r["street"])
        basis = "same street"
        if pool is None or len(pool) < 2:
            pool = sold_by_nb_band.get((r["neighborhood"], r["band"]))
            basis = "neighborhood + band"
        if pool is None or not len(pool):
            continue
        c = pool.assign(_d=(pool["sqft"] - r["sqft"]).abs()).nsmallest(N_COMPS, "_d")
        comps = []
        for _, s in c.iterrows():
            comps.append({
                "address": s["address"], "sold_price": int(s["price"]),
                "ppsf": round(s["actual_ppsf"], 0), "sqft": int(s["sqft"]),
                "beds": int(s["beds"]) if pd.notna(s.get("beds")) else None,
            })
            flat.append({"target": r["address"], "target_neighborhood": r["neighborhood"],
                         "target_list": int(r["price"]), "basis": basis,
                         "comp_address": s["address"], "comp_sold_price": int(s["price"]),
                         "comp_ppsf": round(s["actual_ppsf"], 0), "comp_sqft": int(s["sqft"])})
        bundle[r["address"]] = {
            "neighborhood": r["neighborhood"], "list_price": int(r["price"]),
            "ask_ppsf": round(r["actual_ppsf"], 0), "basis": basis,
            "comp_median_ppsf": round(float(c["actual_ppsf"].median()), 0),
            "comps": comps,
        }

    pd.DataFrame(flat).to_csv(os.path.join(PROC, "comps_flat.csv"), index=False)
    with open(os.path.join(PROC, "comps_bundle.json"), "w") as f:
        json.dump({"meta": {"n_targets": len(bundle), "n_comps": N_COMPS},
                   "targets": bundle}, f, separators=(",", ":"))
    print(f"Comps: {len(bundle)} live >=$1M listings matched to up to {N_COMPS} sold comps each "
          f"({len(flat)} comp rows)")


if __name__ == "__main__":
    main()
