#!/usr/bin/env python3
"""
Segmentation analytics — slice the market by asset type × price bracket × size class ×
neighborhood, with MARKET-SHARE percentages (what % each category makes up of its parent).

"Floor plan" note: the commercial MLS export has no unit-mix / bed-bath data, so the size
analog is a SqFt bracket (size class); for the multifamily we could parse unit counts, a
unit-count bracket is added too.

OUTPUT: data/processed/segments_matrix_*.csv, segmentation_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE

SIZE_BANDS = [("< 2.5K", 0, 2500), ("2.5–5K", 2500, 5000), ("5–10K", 5000, 10000),
              ("10–25K", 10000, 25000), ("25–50K", 25000, 50000), ("50K+", 50000, float("inf"))]
PPSF_BANDS = [("< $100", 0, 100), ("$100–200", 100, 200), ("$200–300", 200, 300),
              ("$300–500", 300, 500), ("$500+", 500, float("inf"))]
UNIT_BANDS = [("< 10", 0, 10), ("10–25", 10, 25), ("25–50", 25, 50),
              ("50–100", 50, 100), ("100+", 100, float("inf"))]
PRICE_ORDER = [b[0] for b in CRE.PRICE_BANDS]
SIZE_ORDER = [b[0] for b in SIZE_BANDS]
PPSF_ORDER = [b[0] for b in PPSF_BANDS]
UNIT_ORDER = [b[0] for b in UNIT_BANDS]


def _band(x, bands):
    if pd.isna(x):
        return None
    for label, lo, hi in bands:
        if lo <= x < hi:
            return label
    return bands[-1][0]


def _share(df, group_cols, within):
    g = df.groupby(group_cols, observed=True).agg(
        n=("ppsf", "size"), median_ppsf=("ppsf", "median"),
        median_price=("price", "median"), median_sqft=("sqft", "median")).reset_index()
    tot = df.groupby(within, observed=True).size().rename("within_total").reset_index()
    g = g.merge(tot, on=within)
    g["share_pct"] = (g["n"] / g["within_total"] * 100).round(1)
    g["median_ppsf"] = g["median_ppsf"].round(0)
    g["median_price"] = g["median_price"].round(-3)
    g["median_sqft"] = g["median_sqft"].round(0)
    return g.drop(columns="within_total")


def _matrix(df, row, col, order_col, order_row=None):
    """count matrix rows×cols + a % share (within row) matrix, as records."""
    piv = df.pivot_table(index=row, columns=col, values="ppsf", aggfunc="size", fill_value=0)
    piv = piv.reindex(columns=[c for c in order_col if c in piv.columns])
    if order_row:
        piv = piv.reindex(index=[r for r in order_row if r in piv.index])
    counts = piv.reset_index().to_dict(orient="records")
    share = piv.div(piv.sum(axis=1).replace(0, np.nan), axis=0) * 100
    share = share.round(1).reset_index().to_dict(orient="records")
    return {"cols": list(piv.columns), "counts": counts, "share": share}


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    v = v[v["ppsf"].notna() & v["price"].gt(0)].copy()
    v["price_band"] = pd.Categorical(v["price_band"], categories=PRICE_ORDER, ordered=True)
    v["size_band"] = pd.Categorical(v["sqft"].map(lambda x: _band(x, SIZE_BANDS)),
                                    categories=SIZE_ORDER, ordered=True)
    v["ppsf_band"] = pd.Categorical(v["ppsf"].map(lambda x: _band(x, PPSF_BANDS)),
                                    categories=PPSF_ORDER, ordered=True)
    v["unit_band"] = v["units"].map(lambda x: _band(x, UNIT_BANDS)) if "units" in v.columns else None

    asset_order = [a for a in CRE.ASSET_ORDER if a in set(v["asset_type"])]
    subs = sorted(v["submarket"].value_counts()[lambda x: x >= 4].index)
    vv = v[v["submarket"].isin(subs)]

    bundle = {
        "meta": {"n": int(len(v)), "note": ("Shares are within the stated parent. 'Size class' is a "
                 "SqFt bracket (no floor-plan/unit-mix data in the export); unit brackets cover only "
                 "multifamily with a parsed unit count."),
                 "price_bands": PRICE_ORDER, "size_bands": SIZE_ORDER, "ppsf_bands": PPSF_ORDER},
        # long-format share tables
        "type_by_price": json.loads(_share(v, ["asset_type", "price_band"], ["asset_type"]).to_json(orient="records")),
        "price_by_type": json.loads(_share(v, ["price_band", "asset_type"], ["price_band"]).to_json(orient="records")),
        "type_by_size": json.loads(_share(v, ["asset_type", "size_band"], ["asset_type"]).to_json(orient="records")),
        "type_by_ppsf": json.loads(_share(v, ["asset_type", "ppsf_band"], ["asset_type"]).to_json(orient="records")),
        "nbhd_by_type": json.loads(_share(vv, ["submarket", "asset_type"], ["submarket"]).to_json(orient="records")),
        "nbhd_by_price": json.loads(_share(vv, ["submarket", "price_band"], ["submarket"]).to_json(orient="records")),
        "nbhd_by_size": json.loads(_share(vv, ["submarket", "size_band"], ["submarket"]).to_json(orient="records")),
        # pivot matrices (for the Excel)
        "matrix_type_price": _matrix(v, "asset_type", "price_band", PRICE_ORDER, asset_order),
        "matrix_type_size": _matrix(v, "asset_type", "size_band", SIZE_ORDER, asset_order),
        "matrix_price_size": _matrix(v, "price_band", "size_band", SIZE_ORDER, PRICE_ORDER),
        "matrix_nbhd_type": _matrix(vv, "submarket", "asset_type", asset_order),
        "matrix_nbhd_price": _matrix(vv, "submarket", "price_band", PRICE_ORDER),
        "matrix_nbhd_size": _matrix(vv, "submarket", "size_band", SIZE_ORDER),
        # overall market composition
        "market": {
            "by_type": _comp(v, "asset_type"),
            "by_price": _comp(v, "price_band"),
            "by_size": _comp(v, "size_band"),
        },
    }
    # multifamily unit-mix (where parsed)
    mfu = v[(v["asset_type"] == "Multifamily") & v["units"].notna()].copy()
    if len(mfu):
        mfu["unit_band"] = pd.Categorical(mfu["units"].map(lambda x: _band(x, UNIT_BANDS)),
                                          categories=UNIT_ORDER, ordered=True)
        bundle["mf_unit_mix"] = _comp(mfu, "unit_band")
        bundle["meta"]["mf_units_parsed"] = int(len(mfu))

    with open(os.path.join(CRE.PROC, "segmentation_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)

    # a flat, pivot-ready detail table (submarket × type × price bracket)
    detail = _share(v, ["submarket", "asset_type", "price_band"], ["submarket"])
    detail.to_csv(os.path.join(CRE.PROC, "segments_detail.csv"), index=False)
    print(f"Segmentation: {len(v)} priced sale listings | "
          f"{len(asset_order)} asset types × {len(PRICE_ORDER)} price × {len(SIZE_ORDER)} size "
          f"brackets × {len(subs)} neighborhoods")
    top = bundle["market"]["by_type"][0]
    print(f"    biggest slice of market: {top['asset_type']} ({top['share_pct']}%)")


def _comp(df, col):
    g = df.groupby(col, observed=True).agg(n=("ppsf", "size"), median_ppsf=("ppsf", "median")).reset_index()
    g["share_pct"] = (g["n"] / g["n"].sum() * 100).round(1)
    g["median_ppsf"] = g["median_ppsf"].round(0)
    g = g.rename(columns={col: g.columns[0]}).sort_values("n", ascending=False)
    return json.loads(g.to_json(orient="records"))


if __name__ == "__main__":
    main()
