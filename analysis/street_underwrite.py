#!/usr/bin/env python3
"""
Street-by-street value + deal underwriting.

Reads data/processed/mls_all_valued.csv (every listing valued by the per-home
hedonic, with a normalised street name) and produces:

  - street_underwrite.csv : per-street value (sold $/sqft, model $/sqft, the
        street's premium vs its neighborhood, waterfront share, sold/active counts)
  - street_active_deals.csv : every active/pending listing underwritten -- asking
        $/sqft vs a STREET-AWARE model value, with a deal flag
  - street_bundle.json : the same, for the dashboard

Street value refines the neighborhood model: a street with enough closed sales gets
its own premium/discount (shrunk toward zero by sample size) layered on top of the
model's neighborhood prediction -- so a prime waterfront block isn't valued like the
dry street one block inland.
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
VALUED = os.path.join(PROC, "mls_all_valued.csv")

MIN_STREET_SOLD = 4     # min closed sales to publish a street's own value
SHRINK_K = 5            # street-premium shrinkage strength (toward neighborhood)
LIVE = {"Active", "Pending"}


def street_table(v):
    sold = v[v["status"] == "Sold"]
    nbhd_med = sold.groupby("neighborhood")["actual_ppsf"].median()
    active_ct = v[v["status"].isin(LIVE)].groupby("street").size()
    rows = []
    for st, g in sold.groupby("street"):
        if len(g) < MIN_STREET_SOLD or pd.isna(st):
            continue
        nb = g["neighborhood"].mode().iat[0]
        med = float(g["actual_ppsf"].median())
        base = float(nbhd_med.get(nb, np.nan))
        prem = (med / base - 1) * 100 if base and pd.notna(base) else np.nan
        # shrink the premium toward 0 by sample size
        prem_shrunk = prem * len(g) / (len(g) + SHRINK_K) if pd.notna(prem) else 0.0
        rows.append({
            "street": st, "neighborhood": nb,
            "geo_type": g["geo_type"].mode().iat[0] if len(g["geo_type"].mode()) else None,
            "sold_ppsf": round(med, 0),
            "model_ppsf": round(float(g["pred_ppsf"].median()), 0),
            "premium_vs_nbhd": round(prem, 1) if pd.notna(prem) else None,
            "_prem_shrunk": prem_shrunk,
            "waterfront_share": round(float(g["waterfront"].mean()), 2),
            "median_price": int(g["price"].median()) if g["price"].notna().any() else None,
            "n_sold": int(len(g)),
            "n_active": int(active_ct.get(st, 0)),
        })
    return pd.DataFrame(rows).sort_values("sold_ppsf", ascending=False)


def underwrite_live(v, streets):
    prem = streets.set_index("street")["_prem_shrunk"].to_dict()
    comps = streets.set_index("street")["n_sold"].to_dict()
    d = v[v["status"].isin(LIVE) & v["pred_ppsf"].gt(0)].copy()
    # street-aware value = neighborhood model x (1 + shrunk street premium)
    d["street_prem"] = d["street"].map(prem).fillna(0.0)
    d["street_comps"] = d["street"].map(comps).fillna(0).astype(int)
    d["street_value_ppsf"] = (d["pred_ppsf"] * (1 + d["street_prem"] / 100)).round(0)
    d["gap_vs_street"] = ((d["actual_ppsf"] / d["street_value_ppsf"] - 1) * 100).round(1)

    def flag(g):
        return "Underpriced" if g < -7 else ("Overpriced" if g > 10 else "Fair")
    d["flag"] = d["gap_vs_street"].apply(flag)
    out = d[["status", "address", "street", "neighborhood", "geo_type", "ptype",
             "sqft", "waterfront", "price", "actual_ppsf", "street_value_ppsf",
             "street_comps", "gap_vs_street", "flag"]].rename(columns={
                 "actual_ppsf": "ask_ppsf", "price": "list_price"})
    return out.sort_values("gap_vs_street")


def main():
    if not os.path.exists(VALUED):
        raise SystemExit("Run mls_normalize.py first (needs mls_all_valued.csv).")
    v = pd.read_csv(VALUED)
    streets = street_table(v)
    live = underwrite_live(v, streets)

    streets_out = streets.drop(columns=["_prem_shrunk"])
    streets_out.to_csv(os.path.join(PROC, "street_underwrite.csv"), index=False)
    live.to_csv(os.path.join(PROC, "street_active_deals.csv"), index=False)

    # SFR under-priced shortlist underwritten against >=4 actual street comps
    # (a bounded gap, so distressed/teardown outliers don't masquerade as deals).
    deals = live[(live["flag"] == "Underpriced")
                 & (live["ptype"] == "Single Family")
                 & (live["street_comps"] >= MIN_STREET_SOLD)
                 & (live["gap_vs_street"].between(-35, -8))].head(40)
    bundle = {
        "meta": {
            "n_streets": int(len(streets_out)),
            "min_street_sold": MIN_STREET_SOLD,
            "n_live_underwritten": int(len(live)),
            "flag_counts": {k: int(x) for k, x in live["flag"].value_counts().items()},
        },
        "streets": json.loads(streets_out.to_json(orient="records")),
        "deals": json.loads(deals.to_json(orient="records")),
    }
    with open(os.path.join(PROC, "street_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"Streets valued (>= {MIN_STREET_SOLD} sold): {len(streets_out)} | "
          f"live listings underwritten: {len(live)} "
          f"({bundle['meta']['flag_counts']})")
    top = streets_out.head(5)
    for _, r in top.iterrows():
        print(f"  {r['street']:26s} ({r['neighborhood'][:18]:18s}) ${r['sold_ppsf']:>6,.0f}/sqft "
              f"| {r['premium_vs_nbhd']:+.0f}% vs nbhd | {r['n_sold']} sold")


if __name__ == "__main__":
    main()
