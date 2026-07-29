#!/usr/bin/env python3
"""
Model accuracy backtest — how close does the normalization actually get?

Runs a 5-fold cross-validation of the per-home hedonic: repeatedly fit on 80% of the
closed sales and predict the held-out 20% the model has never seen, then compare the
predicted price to the real sale price. The result is an out-of-sample accuracy the
model can't fake — the credibility line behind "data-backed pricing."

Reports median absolute error in % and $, the share of homes priced within ±10% and
±20%, and the same broken out by price band and property type.

Reads the cleaned MLS sales (via mls_normalize). Output: backtest_bundle.json.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mls_normalize as M  # reuse load_clean + assign_geo
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
N_FOLDS = 5
NEW_MAX_AGE = CFG.thr("new_max_age")
EDGES, LABELS = CFG.full_bands()


def _prep(sold):
    d = sold.copy()
    d = d[d["sale_ppsf"].notna() & d["sqft"].gt(0) & d["sale_price"].gt(0)]
    d["ltsqft"] = np.log(d["sqft"])
    d["beds_i"] = d["beds"].fillna(d["beds"].median())
    d["baths_i"] = d["baths"].fillna(d["baths"].median())
    d["age_i"] = d["age"].fillna(d["age"].median())
    d["wf"] = d["waterfront"].astype(int)
    d["pl"] = d["pool"].astype(int)
    d["new"] = (d["age_i"] <= NEW_MAX_AGE).astype(int)
    d["y"] = np.log(d["sale_ppsf"])
    d["ptype"] = d["ptype"].astype("category")
    d["geo"] = d["geo"].astype("category")
    return d.reset_index(drop=True)


def _fit(train):
    import statsmodels.formula.api as smf
    mod = smf.ols("y ~ ltsqft + beds_i + baths_i + wf + pl + age_i + new + C(ptype) + C(geo)",
                  data=train).fit()
    smear = float(np.mean(np.exp(mod.resid)))
    return mod, smear


def _metrics(ape):
    ape = np.asarray(ape, dtype=float)
    ape = ape[np.isfinite(ape)]
    if not len(ape):
        return None
    return {
        "n": int(len(ape)),
        "mdape": round(float(np.median(ape)) * 100, 1),       # median abs % error
        "mape": round(float(np.mean(ape)) * 100, 1),
        "within10": round(float((ape <= 0.10).mean()) * 100, 0),
        "within20": round(float((ape <= 0.20).mean()) * 100, 0),
    }


def main():
    df = M.assign_geo(M.load_clean())
    sold = _prep(df[df["status"] == "Sold"])
    n = len(sold)
    rng = np.random.RandomState(42)          # fixed seed -> reproducible bundle
    folds = rng.permutation(n) % N_FOLDS

    recs = []
    for k in range(N_FOLDS):
        tr, te = sold[folds != k], sold[folds == k]
        mod, smear = _fit(tr)
        # only score test rows whose categories the training fold actually saw
        seen_geo, seen_pt = set(tr["geo"]), set(tr["ptype"])
        te = te[te["geo"].isin(seen_geo) & te["ptype"].isin(seen_pt)].copy()
        if not len(te):
            continue
        yhat = mod.predict(te)
        te["pred_ppsf"] = np.exp(yhat) * smear
        te["pred_price"] = te["pred_ppsf"] * te["sqft"]
        te["ape"] = (te["pred_price"] - te["sale_price"]).abs() / te["sale_price"]
        recs.append(te[["sale_price", "ptype", "ape"]])

    scored = pd.concat(recs, ignore_index=True)
    scored["band"] = pd.cut(scored["sale_price"], EDGES, labels=LABELS, right=False)

    scored = scored[np.isfinite(scored["ape"])].copy()
    overall = _metrics(scored["ape"])
    overall["median_dollar_err"] = int(round(
        float((scored["ape"] * scored["sale_price"]).median()), -3))
    by_band = []
    for b in LABELS:
        g = scored[scored["band"] == b]
        m = _metrics(g["ape"])
        if m and m["n"] >= 15:
            by_band.append({"band": b, **m})
    by_ptype = []
    for pt, g in scored.groupby("ptype", observed=True):
        m = _metrics(g["ape"])
        if m and m["n"] >= 15:
            by_ptype.append({"ptype": str(pt), **m})
    by_ptype.sort(key=lambda r: -r["n"])

    bundle = {
        "meta": {
            "n_sold": int(n), "n_scored": int(len(scored)),
            "coverage_pct": round(100 * len(scored) / n, 1),
            "n_folds": N_FOLDS,
            "headline": (f"On {len(scored):,} closed sales the model priced the typical home "
                         f"within ±{overall['mdape']:.0f}% out-of-sample "
                         f"({overall['within10']:.0f}% within ±10%, "
                         f"{overall['within20']:.0f}% within ±20%)."),
        },
        "overall": overall,
        "by_band": by_band,
        "by_ptype": by_ptype,
    }
    with open(os.path.join(PROC, "backtest_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    o = overall
    print(f"Backtest ({N_FOLDS}-fold CV on {len(scored):,}/{n:,} sales, "
          f"{bundle['meta']['coverage_pct']}% coverage):")
    print(f"  median abs error {o['mdape']}% (±${o['median_dollar_err']:,}) · "
          f"{o['within10']:.0f}% within ±10% · {o['within20']:.0f}% within ±20%")
    for b in by_band:
        print(f"   {b['band']:9s} n={b['n']:<4d} median err {b['mdape']:>4.1f}% · "
              f"{b['within10']:.0f}% within 10%")


if __name__ == "__main__":
    main()
