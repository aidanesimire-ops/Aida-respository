#!/usr/bin/env python3
"""
Absorption / months-of-supply: how hard it is to sell at each price band, by
neighborhood. The macro leverage signal -- where the top is oversupplied and where
inventory is tight.

months_of_supply = active listings / (sold in ~24 months / 24).
Output: absorption_by_band.csv, absorption_by_band_neighborhood.csv, absorption_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
MONTHS = 24
EDGES = [0, 1e6, 2e6, 3e6, 5e6, 10e6, np.inf]
LABELS = ["<$1M", "$1M–$2M", "$2M–$3M", "$3M–$5M", "$5M–$10M", "$10M+"]
LIVE = {"Active", "Pending"}


def market(mos):
    if mos is None or pd.isna(mos):
        return None
    if mos < 6:
        return "Seller's market"
    if mos < 12:
        return "Balanced"
    if mos < 24:
        return "Buyer's market"
    return "Deep buyer's market"


def _rows(df, by):
    sold = df[df["status"] == "Sold"]
    live = df[df["status"].isin(LIVE)]
    rows = []
    keys = sorted(set(sold[by].dropna()) | set(live[by].dropna()), key=str) if isinstance(by, str) \
        else None
    for key, g_all in df.groupby(by, observed=True):
        s = int((g_all["status"] == "Sold").sum())
        a = int(g_all["status"].isin(LIVE).sum())
        if s == 0 and a == 0:
            continue
        rate = s / MONTHS
        mos = round(a / rate, 1) if rate else (None if a == 0 else 999.0)
        rec = {"sold_2y": s, "active": a, "months_supply": mos, "market": market(mos)}
        if isinstance(by, list):
            for col, val in zip(by, key):
                rec[col] = val
        else:
            rec[by] = key
        rows.append(rec)
    return pd.DataFrame(rows)


def main():
    df = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    df["band"] = pd.cut(df["price"], EDGES, labels=LABELS, right=False)

    by_band = _rows(df, "band")
    order = {b: i for i, b in enumerate(LABELS)}
    by_band["_o"] = by_band["band"].map(order)
    by_band = by_band.sort_values("_o").drop(columns="_o")[
        ["band", "sold_2y", "active", "months_supply", "market"]]
    by_band.to_csv(os.path.join(PROC, "absorption_by_band.csv"), index=False)

    bn = _rows(df, ["neighborhood", "band"])
    bn = bn[(bn["sold_2y"] >= 3) | (bn["active"] >= 3)]
    bn["_o"] = bn["band"].map(order)
    bn = bn.sort_values(["neighborhood", "_o"]).drop(columns="_o")[
        ["neighborhood", "band", "sold_2y", "active", "months_supply", "market"]]
    bn.to_csv(os.path.join(PROC, "absorption_by_band_neighborhood.csv"), index=False)

    bundle = {
        "meta": {"months_window": MONTHS},
        "by_band": json.loads(by_band.to_json(orient="records")),
        "by_band_neighborhood": json.loads(bn.to_json(orient="records")),
    }
    with open(os.path.join(PROC, "absorption_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    print("Absorption (months of supply) by band:")
    for _, r in by_band.iterrows():
        print(f"  {r['band']:9s} sold {r['sold_2y']:>4d} / active {r['active']:>4d} "
              f"= {r['months_supply']:>5} mo  [{r['market']}]")


if __name__ == "__main__":
    main()
