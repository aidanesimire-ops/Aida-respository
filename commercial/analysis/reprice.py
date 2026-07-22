#!/usr/bin/env python3
"""
Reprice live commercial inventory two ways:
  * $/sqft basis  — asking $/sqft vs the hedonic-predicted $/sqft for the same building.
  * income basis  — asking price vs assumption-derived value (NOI ÷ market cap), i.e. the
    yield you'd buy at given the industry-norm rents/vacancy/opex for its asset type.
The income lens is assumption-driven (defaults from cre_assumptions) and recomputes live in
the dashboard; here we snapshot it at the defaults.

OUTPUT: data/processed/reprice_inventory.csv, underpriced_opportunities.csv, reprice_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE

UNDER, OVER = -10.0, 10.0     # income value-gap % thresholds


def flag(gap):
    if pd.isna(gap):
        return "n/a"
    return "Underpriced" if gap < UNDER else ("Overpriced" if gap > OVER else "Fair")


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    live = v[v["status"].isin(CRE.LIVE)].copy()
    live["flag"] = live["income_gap_pct"].map(flag)
    live["ppsf_flag"] = live["ppsf_gap_pct"].map(
        lambda g: "Under" if g < -12 else ("Over" if g > 12 else "Fair") if pd.notna(g) else "n/a")

    cols = ["mls", "address", "submarket", "asset_type", "status", "price_band", "price",
            "sqft", "ppsf", "pred_ppsf", "ppsf_gap_pct", "noi", "implied_cap", "market_cap",
            "assumed_value", "income_gap_pct", "flag"]
    inv = live[cols].sort_values("income_gap_pct")
    inv.to_csv(os.path.join(CRE.PROC, "reprice_inventory.csv"), index=False)

    opp = live[(live["flag"] == "Underpriced")
               & live["implied_cap"].notna()
               & live["income_gap_pct"].between(-60, UNDER)].copy()

    def reason(r):
        bits = [f"implied cap {r['implied_cap']*100:.2f}% vs {r['market_cap']*100:.2f}% market "
                f"(given assumed rents)"]
        if pd.notna(r["ppsf_gap_pct"]) and r["ppsf_gap_pct"] < -8:
            bits.append(f"{abs(r['ppsf_gap_pct']):.0f}% under comp $/sqft")
        bits.append(f"asking ~{abs(r['income_gap_pct']):.0f}% below assumption value "
                    f"({CRE.usd(r['assumed_value'])})")
        return "; ".join(bits)

    opp["reason"] = opp.apply(reason, axis=1)
    opp_out = opp[["mls", "address", "submarket", "asset_type", "price", "assumed_value",
                   "implied_cap", "market_cap", "ppsf", "pred_ppsf", "income_gap_pct",
                   "reason"]].sort_values("income_gap_pct").head(40)
    opp_out.to_csv(os.path.join(CRE.PROC, "underpriced_opportunities.csv"), index=False)

    counts = {k: int(v_) for k, v_ in live["flag"].value_counts().items()}
    bundle = {
        "meta": {"n_live": int(len(live)), "thresholds": {"under": UNDER, "over": OVER},
                 "flag_counts": counts,
                 "note": "Income flags use DEFAULT assumptions; tune them live in the dashboard."},
        "flag_counts": counts,
        "inventory": json.loads(inv.round(4).to_json(orient="records")),
        "opportunities": json.loads(opp_out.round(4).to_json(orient="records")),
        "by_submarket": json.loads(
            live.groupby("submarket").agg(
                n=("price", "size"),
                median_income_gap=("income_gap_pct", "median"),
                underpriced=("flag", lambda x: int((x == "Underpriced").sum())),
                overpriced=("flag", lambda x: int((x == "Overpriced").sum())),
            ).round(1).reset_index().to_json(orient="records")),
    }
    with open(os.path.join(CRE.PROC, "reprice_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Repriced {len(live)} live listings | "
          + ", ".join(f"{k}={v_}" for k, v_ in counts.items())
          + f" | {len(opp_out)} opportunities")


if __name__ == "__main__":
    main()
