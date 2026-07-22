#!/usr/bin/env python3
"""
Prospecting — owners to call.
  * FAILED listings (expired / cancelled / withdrawn / temp-off): motivated owners, with the
    $/sqft overpricing vs comps that likely stalled the deal.
  * OVERPRICED actives: live listings well above assumption value / comp $/sqft.
Plus a failure rate by submarket and by asset type.

OUTPUT: data/processed/prospects_*.csv, prospects_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE

OVER = 12.0


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))

    failed = v[v["status"].isin(CRE.FAILED)].copy()
    fcols = ["mls", "address", "submarket", "asset_type", "status", "price", "sqft", "ppsf",
             "pred_ppsf", "ppsf_gap_pct", "assumed_value", "income_gap_pct"]
    fail_out = failed[fcols].sort_values("ppsf_gap_pct", ascending=False)
    fail_out.to_csv(os.path.join(CRE.PROC, "prospects_failed.csv"), index=False)

    over = v[v["status"].isin(CRE.LIVE) & v["income_gap_pct"].gt(OVER)].copy()
    over_out = over[fcols].sort_values("income_gap_pct", ascending=False)
    over_out.to_csv(os.path.join(CRE.PROC, "prospects_overpriced_active.csv"), index=False)

    def _rate(df, col):
        rows = []
        for key, g in df.groupby(col):
            nf = int(g["status"].isin(CRE.FAILED).sum())
            ns = int((g["status"] == CRE.SOLD).sum())
            denom = nf + ns
            rows.append({col: key, "n_failed": nf, "n_sold": ns,
                         "failure_rate_pct": round(nf / denom * 100, 1) if denom else np.nan})
        return pd.DataFrame(rows).sort_values("failure_rate_pct", ascending=False)

    fr_sub = _rate(v[v["submarket"].isin(CRE.big_segments(v, "submarket", 4))], "submarket")
    fr_type = _rate(v, "asset_type")
    fr_sub.to_csv(os.path.join(CRE.PROC, "prospects_failure_rate.csv"), index=False)

    bundle = {
        "meta": {"n_failed": int(len(failed)), "n_overpriced_active": int(len(over)),
                 "over_gap_pct": OVER},
        "failed": json.loads(fail_out.head(40).round(4).to_json(orient="records")),
        "overpriced_active": json.loads(over_out.head(40).round(4).to_json(orient="records")),
        "failure_rate_submarket": json.loads(fr_sub.round(2).to_json(orient="records")),
        "failure_rate_type": json.loads(fr_type.round(2).to_json(orient="records")),
    }
    with open(os.path.join(CRE.PROC, "prospects_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Prospects: {len(failed)} failed, {len(over)} overpriced actives")


if __name__ == "__main__":
    main()
