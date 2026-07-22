#!/usr/bin/env python3
"""
Master neighborhood summary: one ranked table (most -> least expensive) with every
normalized metric up front AND the suggested repricing for each neighborhood's live
inventory. Synthesizes the MLS, repricing, high-ticket, time and Redfin layers.

Output: data/processed/master_neighborhoods.csv + master_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")


def _load(name):
    with open(os.path.join(PROC, name)) as f:
        return json.load(f)


def main():
    mls = _load("mls_bundle.json")
    reprice = {r["neighborhood"]: r for r in _load("reprice_bundle.json")["by_nbhd"]}
    shifts = {r["neighborhood"]: r for r in _load("time_bundle.json")["shifts"]}
    try:
        dom = {r["neighborhood"]: r for r in _load("analysis_bundle.json")["headline"]}
    except FileNotFoundError:
        dom = {}

    # high-ticket per neighborhood (>= $1M live): counts, $10M+ count, list vs suggested
    ht = pd.read_csv(os.path.join(PROC, "high_ticket_underwriting.csv"))
    live = ht[ht["status"].isin(["Active", "Pending"])]
    ht_n = live.groupby("neighborhood").size()
    ht_10 = live[live["band"] == "$10M+"].groupby("neighborhood").size()
    ht_list = live.groupby("neighborhood")["list_price"].sum()

    rows = []
    for nb in mls["neighborhoods"]:
        name = nb["neighborhood"]
        rp = reprice.get(name, {})
        sh = shifts.get(name, {})
        dm = dom.get(name, {})
        list_total = float(ht_list.get(name, np.nan))
        # suggested repricing from the ROBUST benchmark: asking vs recent sold comps
        # (reprice layer, gated to >=8 comps). Negative = reprice down toward comps.
        ask, should = rp.get("ask_ppsf"), rp.get("sold_ppsf")
        adj = round((should / ask - 1) * 100, 1) if ask and should else None
        sug_total = (int(list_total * (1 + adj / 100)) if adj is not None
                     and list_total and not np.isnan(list_total) else None)
        rows.append({
            "neighborhood": name,
            "geo_type": nb.get("geo_type"),
            "norm_ppsf": nb["norm_ppsf"],
            "vs_city_pct": nb.get("vs_city_pct"),
            "waterfront_ppsf": nb.get("waterfront_ppsf"),
            "dry_ppsf": nb.get("dry_ppsf"),
            "new_premium_pct": nb.get("new_premium_pct"),
            "median_sale_price": nb.get("median_sale_price"),
            "median_discount_pct": nb.get("median_discount_pct"),
            "dom": round(dm["norm_dom"]) if dm.get("norm_dom") is not None
                and not pd.isna(dm.get("norm_dom")) else None,
            "appreciation_since_2020": sh.get("pct_2020_now"),
            "failure_rate": nb.get("failure_rate"),
            "n_high_ticket": int(ht_n.get(name, 0)),
            "n_over_10m": int(ht_10.get(name, 0)),
            "n_live_repriced": rp.get("n_live"),
            "asking_ppsf": rp.get("ask_ppsf"),
            "should_be_ppsf": rp.get("sold_ppsf"),
            "ask_vs_sold_pct": rp.get("gap_pct"),
            "ht_listed_total": int(list_total) if list_total and not np.isnan(list_total) else None,
            "ht_suggested_total": sug_total,
            "suggested_adjust_pct": adj,
            "sold_n": nb.get("sold_n"),
        })
    df = pd.DataFrame(rows).sort_values("norm_ppsf", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", range(1, len(df) + 1))
    df.to_csv(os.path.join(PROC, "master_neighborhoods.csv"), index=False)

    bundle = {
        "meta": {
            "n_neighborhoods": int(len(df)),
            "n_high_ticket_total": int(df["n_high_ticket"].sum()),
            "n_over_10m_total": int(df["n_over_10m"].sum()),
        },
        "neighborhoods": json.loads(df.to_json(orient="records")),
    }
    with open(os.path.join(PROC, "master_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    print(f"Master: {len(df)} neighborhoods ranked | {bundle['meta']['n_high_ticket_total']} "
          f"live >=$1M ({bundle['meta']['n_over_10m_total']} over $10M)")
    top = df.head(6)
    for _, r in top.iterrows():
        adj = f"{r['suggested_adjust_pct']:+.0f}%" if pd.notna(r["suggested_adjust_pct"]) else "  n/a"
        print(f"  {r['rank']:>2d}. {r['neighborhood']:22s} ${r['norm_ppsf']:>6,.0f}/sqft | "
              f">=1M:{r['n_high_ticket']:>2d} (>{'':0}$10M:{r['n_over_10m']}) | reprice {adj}")


if __name__ == "__main__":
    main()
