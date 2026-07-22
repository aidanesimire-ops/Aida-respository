#!/usr/bin/env python3
"""
Reprice the entire live market inventory against the per-home model.

Reads data/processed/mls_all_valued.csv (every listing valued by the hedonic) and,
for all ACTIVE + PENDING listings, compares the current asking price to the model's
"should-be" value -- at the individual-listing level and aggregated by neighborhood
(condos called out specifically). Answers: is each neighborhood priced right, and
which live listings are over / fairly / under-priced.

Outputs:
  reprice_inventory.csv        every live listing repriced (all types)
  reprice_condos_by_nbhd.csv   neighborhood-level condo repricing
  reprice_by_nbhd.csv          neighborhood-level repricing, all types
  reprice_bundle.json          same, for the dashboard

CAVEAT: model value reflects neighborhood, size, age, type, waterfront & pool -- NOT
floor, view or renovation. Individual condo repricing is a starting point; the
neighborhood aggregate (where unit-level noise averages out) is the reliable read.
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

BAND = 10          # +/- % around the model = "fairly priced"
MIN_NBHD_LIVE = 3  # min live listings to score a neighborhood
MIN_COMPS = 5      # min SOLD comps (neighborhood x type) for a reliable verdict
MIN_NBHD_SOLD = 8  # min sold comps to score a neighborhood's market


def verdict(gap, comps=None):
    if gap is None or pd.isna(gap):
        return None
    if comps is not None and comps < MIN_COMPS:
        return "Insufficient comps"       # e.g. pre-construction towers, thin buildings
    return "Overpriced" if gap > BAND else ("Underpriced" if gap < -BAND else "Fairly priced")


def _comp_counts(sold):
    return sold.groupby(["neighborhood", "ptype"]).size()


def listing_level(live, sold):
    comps = _comp_counts(sold)
    d = live.copy()
    d["comps"] = [int(comps.get((nb, pt), 0)) for nb, pt in zip(d["neighborhood"], d["ptype"])]
    d["should_be_ppsf"] = d["pred_ppsf"].round(0)
    d["should_be_price"] = (d["pred_ppsf"] * d["sqft"]).round(-3)   # nearest $1k
    d["diff_price"] = (d["price"] - d["should_be_price"]).round(-3)
    d["gap_pct"] = ((d["actual_ppsf"] / d["pred_ppsf"] - 1) * 100).round(1)
    d["verdict"] = [verdict(g, c) for g, c in zip(d["gap_pct"], d["comps"])]
    cols = ["status", "address", "neighborhood", "geo_type", "ptype", "sqft", "beds",
            "waterfront", "price", "actual_ppsf", "should_be_ppsf", "should_be_price",
            "diff_price", "gap_pct", "comps", "verdict"]
    return d[cols].rename(columns={"price": "list_price", "actual_ppsf": "ask_ppsf"})


def by_neighborhood(live, sold, label_types=None):
    d = live if label_types is None else live[live["ptype"].isin(label_types)]
    sd = sold if label_types is None else sold[sold["ptype"].isin(label_types)]
    sold_med = sd.groupby("neighborhood")["actual_ppsf"].median()
    sold_n = sd.groupby("neighborhood").size()
    rows = []
    for nb, g in d.groupby("neighborhood"):
        ns = int(sold_n.get(nb, 0))
        if len(g) < MIN_NBHD_LIVE or ns < MIN_NBHD_SOLD:   # need real sold comps
            continue
        ask = float(g["actual_ppsf"].median())
        soldv = float(sold_med.get(nb, np.nan))
        model = float(g["pred_ppsf"].median())
        # "what it should be" = recent SOLD comps (the appraisal benchmark); model shown too
        gap = (ask / soldv - 1) * 100
        rows.append({
            "neighborhood": nb,
            "n_live": int(len(g)),
            "n_sold_comps": ns,
            "ask_ppsf": round(ask, 0),
            "sold_ppsf": round(soldv, 0),          # what comparable units actually sell for
            "model_ppsf": round(model, 0),         # normalized model value
            "gap_pct": round(gap, 1),              # asking vs recent sold
            "verdict": verdict(gap),
            "list_total": int(g["price"].sum()),
            "should_be_total": int(round(g["sqft"].mul(soldv).sum(), -3)),
        })
    t = pd.DataFrame(rows)
    return t.sort_values("gap_pct", ascending=False) if len(t) else t


def main():
    if not os.path.exists(VALUED):
        raise SystemExit("Run mls_normalize.py first (needs mls_all_valued.csv).")
    v = pd.read_csv(VALUED)
    live = v[v["status"].isin(["Active", "Pending"]) & v["pred_ppsf"].gt(0)].copy()
    sold = v[v["status"] == "Sold"].copy()

    inv = listing_level(live, sold).sort_values("gap_pct", ascending=False)
    condos = by_neighborhood(live, sold, ["Condo"])
    allt = by_neighborhood(live, sold)

    inv.to_csv(os.path.join(PROC, "reprice_inventory.csv"), index=False)
    condos.to_csv(os.path.join(PROC, "reprice_condos_by_nbhd.csv"), index=False)
    allt.to_csv(os.path.join(PROC, "reprice_by_nbhd.csv"), index=False)

    def counts(df):
        return {k: int(x) for k, x in df["verdict"].value_counts().items()}
    # aggregate $ only over comp-backed (repriceable) listings, so pre-construction
    # towers the model can't value don't distort the citywide number
    rp = inv[inv["verdict"] != "Insufficient comps"]
    bundle = {
        "meta": {
            "n_live": int(len(inv)),
            "n_repriceable": int(len(rp)),
            "band_pct": BAND, "min_comps": MIN_COMPS,
            "list_total": int(rp["list_price"].sum()),
            "should_be_total": int(rp["should_be_price"].sum()),
            "verdict_counts": counts(inv),
            "condo_verdict_counts": counts(inv[inv["ptype"] == "Condo"]),
        },
        "condos_by_nbhd": json.loads(condos.to_json(orient="records")),
        "by_nbhd": json.loads(allt.to_json(orient="records")),
        # cap the per-listing payload for the dashboard; full set is in the CSV
        "inventory": json.loads(inv.head(1200).to_json(orient="records")),
    }
    with open(os.path.join(PROC, "reprice_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    mb = bundle["meta"]
    over = 100 * (mb["list_total"] / mb["should_be_total"] - 1)
    print(f"Repriced {mb['n_live']:,} live listings ({mb['n_repriceable']:,} comp-backed) | "
          f"comp-backed asking ${mb['list_total']/1e9:.2f}B vs model "
          f"${mb['should_be_total']/1e9:.2f}B ({over:+.1f}%)")
    print(f"  all: {mb['verdict_counts']}")
    print(f"  condos: {mb['condo_verdict_counts']}")
    if len(condos):
        print("  most OVERPRICED condo neighborhoods (asking vs recent sold):")
        for _, r in condos.head(4).iterrows():
            print(f"    {r['neighborhood']:24s} ask ${r['ask_ppsf']:>5,.0f} vs sold ${r['sold_ppsf']:>5,.0f} "
                  f"({r['gap_pct']:+.0f}%) [{r['verdict']}]  n={r['n_live']}")


if __name__ == "__main__":
    main()
