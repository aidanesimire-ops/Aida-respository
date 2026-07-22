#!/usr/bin/env python3
"""
Comps — the closed sales behind every $/sqft number, auditable by submarket and asset type.

OUTPUT: data/processed/comps_flat.csv, comps_bundle.json
"""
from __future__ import annotations
import json
import os

import pandas as pd

import cre_common as CRE


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    sold = v[v["status"] == CRE.SOLD].copy()
    cols = ["mls", "address", "submarket", "asset_type", "price_band", "sqft", "year_built",
            "price", "ppsf", "pred_ppsf", "ppsf_gap_pct", "waterfront"]
    flat = sold[cols].sort_values(["submarket", "price"], ascending=[True, False])
    flat.round(2).to_csv(os.path.join(CRE.PROC, "comps_flat.csv"), index=False)

    by_sub = {sub: json.loads(g.sort_values("price", ascending=False)[cols].head(12)
                              .round(2).to_json(orient="records"))
              for sub, g in sold.groupby("submarket")}
    by_type = {at: json.loads(g.sort_values("price", ascending=False)[cols].head(12)
                              .round(2).to_json(orient="records"))
               for at, g in sold.groupby("asset_type")}

    bundle = {"meta": {"n_closed": int(len(sold))},
              "by_submarket": by_sub, "by_type": by_type}
    with open(os.path.join(CRE.PROC, "comps_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Comps: {len(sold)} closed sales across {sold['submarket'].nunique()} submarkets")


if __name__ == "__main__":
    main()
