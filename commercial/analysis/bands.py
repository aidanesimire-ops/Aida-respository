#!/usr/bin/env python3
"""
Segment analysis + absorption for the commercial market.

Cuts pricing and supply by ASSET TYPE, DEAL-SIZE BAND and SUBMARKET. Absorption = months of
supply from the active:closed ratio (the export has no dates, so closed sales are assumed to
span a window — set MF_SOLD_MONTHS / CRE_SOLD_MONTHS to your real window).

OUTPUT: data/processed/segments_bundle.json (+ CSVs)
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE

SOLD_WINDOW_MONTHS = float(os.environ.get("CRE_SOLD_MONTHS", 18))


def _agg(g):
    return pd.Series({
        "n": len(g),
        "n_sold": int((g["status"] == CRE.SOLD).sum()),
        "n_live": int(g["status"].isin(CRE.LIVE).sum()),
        "n_failed": int(g["status"].isin(CRE.FAILED).sum()),
        "median_price": float(g["price"].median()),
        "median_ppsf": float(g["ppsf"].median()),
        "sold_ppsf": float(g[g["status"] == CRE.SOLD]["ppsf"].median())
            if (g["status"] == CRE.SOLD).any() else np.nan,
    })


def _absorption(n_live, n_sold):
    if n_sold <= 0:
        return np.nan
    return round(n_live / (n_sold / SOLD_WINDOW_MONTHS), 1)


def _with_absorption(t):
    t["months_supply"] = [_absorption(a, s) for a, s in zip(t["n_live"], t["n_sold"])]
    return t


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    band_order = [b[0] for b in CRE.PRICE_BANDS]
    v["price_band"] = pd.Categorical(v["price_band"], categories=band_order, ordered=True)

    by_type = _with_absorption(v.groupby("asset_type").apply(_agg).reset_index()
                               ).sort_values("n", ascending=False)
    by_band = _with_absorption(v.groupby("price_band", observed=True).apply(_agg).reset_index())
    big = CRE.big_segments(v, "submarket", 4)
    by_sub = _with_absorption(v[v["submarket"].isin(big)].groupby("submarket").apply(_agg)
                              .reset_index()).sort_values("months_supply")

    by_type.round(4).to_csv(os.path.join(CRE.PROC, "segments_by_type.csv"), index=False)
    by_band.round(4).to_csv(os.path.join(CRE.PROC, "segments_by_band.csv"), index=False)
    by_sub.round(4).to_csv(os.path.join(CRE.PROC, "absorption_by_submarket.csv"), index=False)

    bundle = {
        "meta": {"sold_window_months": SOLD_WINDOW_MONTHS,
                 "absorption_note": ("Months of supply = live / (closed per month); closed "
                                     f"assumed to span {SOLD_WINDOW_MONTHS:.0f} months "
                                     "(no dates in export — set CRE_SOLD_MONTHS).")},
        "by_type": json.loads(by_type.round(4).to_json(orient="records")),
        "by_band": json.loads(by_band.round(4).to_json(orient="records")),
        "absorption_by_submarket": json.loads(by_sub.round(4).to_json(orient="records")),
    }
    with open(os.path.join(CRE.PROC, "segments_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Segments: {len(by_type)} asset types, {len(by_band)} bands, {len(by_sub)} submarkets")


if __name__ == "__main__":
    main()
