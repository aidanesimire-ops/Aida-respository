#!/usr/bin/env python3
"""
Master ranked submarket sheet — joins normalized $/sqft, absorption, failure rate and live
mispricing into one decision table with a suggested stance.

OUTPUT: data/processed/master_submarkets.csv, master_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE


def _load(name, key):
    p = os.path.join(CRE.PROC, name)
    if not os.path.exists(p):
        return {}
    with open(p) as f:
        data = json.load(f)
    rows = data.get(key, [])
    return {r.get("submarket"): r for r in rows}


def stance(vs_city, months_supply, fail_rate):
    score = 0
    if pd.notna(months_supply):
        score += 1 if months_supply < 12 else (-1 if months_supply > 30 else 0)
    if pd.notna(fail_rate):
        score += -1 if fail_rate > 55 else (1 if fail_rate < 30 else 0)
    return "Accumulate" if score >= 2 else ("Caution" if score <= -2 else "Neutral")


def main():
    with open(os.path.join(CRE.PROC, "cre_bundle.json")) as f:
        cre = json.load(f)
    base = pd.DataFrame(cre["submarkets"]).set_index("submarket")

    absb = _load("segments_bundle.json", "absorption_by_submarket")
    reb = _load("reprice_bundle.json", "by_submarket")
    frb = _load("prospects_bundle.json", "failure_rate_submarket")

    rows = []
    for sub, r in base.iterrows():
        ab, rp, fr = absb.get(sub, {}), reb.get(sub, {}), frb.get(sub, {})
        ms, frate = ab.get("months_supply"), fr.get("failure_rate_pct")
        rows.append({
            "submarket": sub, "norm_ppsf": r.get("norm_ppsf"),
            "vs_city_pct": r.get("vs_city_pct"), "median_price": r.get("median_price"),
            "top_asset": r.get("top_asset"), "n": r.get("n"), "n_sold": r.get("n_sold"),
            "months_supply": ms, "failure_rate_pct": frate,
            "live_underpriced": rp.get("underpriced"), "live_overpriced": rp.get("overpriced"),
            "stance": stance(r.get("vs_city_pct"), ms, frate),
        })
    m = pd.DataFrame(rows).sort_values("norm_ppsf", ascending=False)
    m.to_csv(os.path.join(CRE.PROC, "master_submarkets.csv"), index=False)

    bundle = {"meta": {"n_submarkets": int(len(m)),
                       "city_norm_ppsf": cre["meta"]["city_norm_ppsf"]},
              "submarkets": json.loads(m.round(4).to_json(orient="records"))}
    with open(os.path.join(CRE.PROC, "master_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Master: {len(m)} submarkets | "
          f"{int((m['stance']=='Accumulate').sum())} Accumulate")


if __name__ == "__main__":
    main()
