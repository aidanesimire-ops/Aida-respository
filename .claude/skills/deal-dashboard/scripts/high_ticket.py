#!/usr/bin/env python3
"""
High-ticket underwriting: reprice every LIVE listing >= $1M and give a suggested
list price, organized into luxury price bands. Low-ticket inventory is ignored.

Reads data/processed/street_active_deals.csv (every live listing already underwritten
against its street's comps) and produces:

  high_ticket_underwriting.csv : each >=$1M listing -- current list, supported value,
        SUGGESTED LIST, over/under, verdict, band, comp confidence
  high_ticket_bands.csv        : per-band roll-up (count, $/sqft, list vs supported $)
  high_ticket_bundle.json      : same, for the workbook + dashboard

"Supported value" = street-comp-adjusted model value (median recent sales on the street,
size/age/waterfront-adjusted). Suggested list = supported value rounded to a clean number.
Comp confidence flags how much real sold data backs each figure -- luxury is thin, so a
pre-construction tower with no comps is marked Low, not silently trusted.
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
SRC = os.path.join(PROC, "street_active_deals.csv")
VALUED = os.path.join(PROC, "mls_all_valued.csv")
MIN_CELL = 2   # min sold or live in a (neighborhood, band) cell to report it

MIN_TICKET = 1_000_000
BAND_EDGES = [1e6, 2e6, 3e6, 5e6, 10e6, np.inf]
BAND_LABELS = ["$1M–$2M", "$2M–$3M", "$3M–$5M", "$5M–$10M", "$10M+"]
BAND = 10   # +/- % = fairly priced


def _round_list(v):
    """Round a supported value to a clean suggested-list number."""
    if pd.isna(v):
        return None
    if v < 2e6:
        step = 25_000
    elif v < 5e6:
        step = 50_000
    elif v < 10e6:
        step = 100_000
    else:
        step = 250_000
    return int(round(v / step) * step)


def _confidence(comps):
    return "High" if comps >= 4 else ("Medium" if comps >= 1 else "Low (no comps)")


def _verdict(gap, comps):
    if pd.isna(gap):
        return None
    if comps < 1:
        return "Insufficient comps"
    return "Overpriced" if gap > BAND else ("Underpriced" if gap < -BAND else "Fairly priced")


def _mkt_verdict(gap):
    if gap is None or pd.isna(gap):
        return None
    return "Overpriced" if gap > BAND else ("Underpriced" if gap < -BAND else "Fairly priced")


def band_by_neighborhood():
    """How each price band behaves WITHIN each neighborhood: what sells vs what's asked."""
    v = pd.read_csv(VALUED)
    v = v[v["price"] >= MIN_TICKET].copy()
    v["band"] = pd.cut(v["price"], BAND_EDGES, labels=BAND_LABELS, right=False)
    live_st = {"Active", "Pending"}
    rows = []
    for (nb, band), g in v.groupby(["neighborhood", "band"], observed=True):
        sold = g[g["status"] == "Sold"]
        live = g[g["status"].isin(live_st)]
        if len(sold) < MIN_CELL and len(live) < MIN_CELL:
            continue
        sold_ppsf = float(sold["actual_ppsf"].median()) if len(sold) >= MIN_CELL else None
        ask_ppsf = float(live["actual_ppsf"].median()) if len(live) >= MIN_CELL else None
        gap = ((ask_ppsf / sold_ppsf - 1) * 100) if (sold_ppsf and ask_ppsf) else None
        rows.append({
            "neighborhood": nb, "band": band,
            "n_sold": int(len(sold)), "n_live": int(len(live)),
            "sold_ppsf": round(sold_ppsf, 0) if sold_ppsf else None,
            "ask_ppsf": round(ask_ppsf, 0) if ask_ppsf else None,
            "gap_pct": round(gap, 1) if gap is not None else None,
            "verdict": _mkt_verdict(gap),
            "median_sold_price": int(sold["price"].median()) if len(sold) else None,
        })
    t = pd.DataFrame(rows)
    order = {b: i for i, b in enumerate(BAND_LABELS)}
    if len(t):
        # keep neighborhoods that span >=2 bands -- the point is the trend ACROSS bands
        multi = t.groupby("neighborhood").size()
        t = t[t["neighborhood"].isin(multi[multi >= 2].index)]
        t["_o"] = t["band"].map(order)
        t = t.sort_values(["neighborhood", "_o"]).drop(columns="_o")
    return t


def main():
    if not os.path.exists(SRC):
        raise SystemExit("Run street_underwrite.py first (needs street_active_deals.csv).")
    d = pd.read_csv(SRC)
    d = d[d["list_price"] >= MIN_TICKET].copy()

    d["supported_ppsf"] = d["street_value_ppsf"].round(0)
    d["supported_value"] = (d["street_value_ppsf"] * d["sqft"]).round(-3)
    d["suggested_list"] = d["supported_value"].map(_round_list)
    d["over_under_list"] = (d["list_price"] - d["suggested_list"]).round(-3)
    d["gap_pct"] = d["gap_vs_street"].round(1)
    d["comp_confidence"] = d["street_comps"].map(_confidence)
    d["verdict"] = [_verdict(g, c) for g, c in zip(d["gap_pct"], d["street_comps"])]
    d["band"] = pd.cut(d["list_price"], BAND_EDGES, labels=BAND_LABELS, right=False)

    cols = ["status", "address", "neighborhood", "geo_type", "ptype", "sqft", "waterfront",
            "band", "list_price", "ask_ppsf", "supported_ppsf", "suggested_list",
            "over_under_list", "gap_pct", "street_comps", "comp_confidence", "verdict"]
    out = d[cols].sort_values(["band", "gap_pct"], ascending=[True, False])
    out.to_csv(os.path.join(PROC, "high_ticket_underwriting.csv"), index=False)

    # per-band roll-up
    rows = []
    for band in BAND_LABELS:
        g = d[d["band"] == band]
        if not len(g):
            continue
        cb = g[g["street_comps"] >= 1]   # comp-backed subset for the $ comparison
        rows.append({
            "band": band,
            "n": int(len(g)),
            "median_ask_ppsf": round(float(g["ask_ppsf"].median()), 0),
            "median_supported_ppsf": round(float(g["supported_ppsf"].median()), 0),
            "total_list": int(g["list_price"].sum()),
            "total_suggested": int(cb["suggested_list"].sum()) if len(cb) else 0,
            "overpriced": int((g["verdict"] == "Overpriced").sum()),
            "fairly_priced": int((g["verdict"] == "Fairly priced").sum()),
            "underpriced": int((g["verdict"] == "Underpriced").sum()),
            "no_comps": int((g["verdict"] == "Insufficient comps").sum()),
        })
    bands = pd.DataFrame(rows)
    bands.to_csv(os.path.join(PROC, "high_ticket_bands.csv"), index=False)

    # band x neighborhood: the core view -- each band's behavior within each neighborhood
    bn = band_by_neighborhood()
    bn.to_csv(os.path.join(PROC, "high_ticket_band_neighborhood.csv"), index=False)

    cb = d[d["street_comps"] >= 1]
    over = 100 * (cb["list_price"].sum() / cb["suggested_list"].sum() - 1) if len(cb) else 0
    bundle = {
        "meta": {
            "min_ticket": MIN_TICKET,
            "n_listings": int(len(d)),
            "n_comp_backed": int(len(cb)),
            "total_list": int(cb["list_price"].sum()) if len(cb) else 0,
            "total_suggested": int(cb["suggested_list"].sum()) if len(cb) else 0,
            "list_vs_suggested_pct": round(over, 1),
            "verdict_counts": {k: int(v) for k, v in d["verdict"].value_counts().items()},
        },
        "bands": json.loads(bands.to_json(orient="records")),
        "band_neighborhood": json.loads(
            bn.assign(band=bn["band"].astype(str)).to_json(orient="records")) if len(bn) else [],
        "listings": json.loads(
            out.assign(band=out["band"].astype(str)).to_json(orient="records")),
    }
    with open(os.path.join(PROC, "high_ticket_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    m = bundle["meta"]
    print(f"High-ticket (>= ${MIN_TICKET/1e6:.0f}M): {m['n_listings']} live listings "
          f"({m['n_comp_backed']} comp-backed)")
    print(f"  comp-backed listed at ${m['total_list']/1e9:.2f}B vs suggested "
          f"${m['total_suggested']/1e9:.2f}B ({m['list_vs_suggested_pct']:+.0f}%)")
    print(f"  verdicts: {m['verdict_counts']}")
    for _, r in bands.iterrows():
        print(f"  {r['band']:10s} n={r['n']:>3d} | ask ${r['median_ask_ppsf']:>5,.0f} vs "
              f"supported ${r['median_supported_ppsf']:>5,.0f}/sqft | "
              f"{r['overpriced']}over/{r['fairly_priced']}fair/{r['underpriced']}under")


if __name__ == "__main__":
    main()
