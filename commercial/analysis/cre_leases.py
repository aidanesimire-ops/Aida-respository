#!/usr/bin/env python3
"""
Leasing layer — turns the 521 lease listings into a real rents picture alongside the sale
picture, and derives a market cap rate from actual data (lease ÷ sale) instead of assumptions.

For each asset type and submarket×type where we have both sides:
    gross yield  = annual lease $/SqFt ÷ sale $/SqFt
    implied cap  = gross yield × (1 − vacancy) × (1 − opex)      [vacancy/opex from assumptions]
That implied cap is anchored to observed rents and prices — the number to quote an owner.

OUTPUT: data/processed/lease_rates.csv, lease_comps.csv, implied_yields.csv, leases_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

import cre_common as CRE
import cre_assumptions as A

MIN_N = 3


def _stats(x):
    x = x.dropna()
    return {"n": int(len(x)),
            "median": round(float(x.median()), 1) if len(x) else None,
            "p25": round(float(x.quantile(0.25)), 1) if len(x) else None,
            "p75": round(float(x.quantile(0.75)), 1) if len(x) else None}


def main():
    df = CRE.load_clean()
    lease = df[df["deal_kind"].eq("Lease") & df["lease_rate_psf"].notna()].copy()
    sales = CRE.sales(df)
    sale_psf_type = sales.groupby("asset_type")["ppsf"].median()
    sale_psf_sub = sales.groupby("submarket")["ppsf"].median()

    # ---- lease rate by asset type (+ sale side + data-derived cap) ----
    type_rows = []
    for at in [a for a in CRE.ASSET_ORDER if a in set(lease["asset_type"])]:
        g = lease[lease["asset_type"] == at]
        st = _stats(g["lease_rate_psf"])
        if st["n"] < MIN_N:
            continue
        s_psf = float(sale_psf_type.get(at, np.nan))
        gross = st["median"] / s_psf if s_psf and not np.isnan(s_psf) else np.nan
        asm = A.for_type(at)
        implied_cap = gross * (1 - asm["vacancy"]) * (1 - asm["opex_ratio"]) if gross == gross else np.nan
        type_rows.append({
            "asset_type": at, "lease_psf": st["median"], "lease_p25": st["p25"],
            "lease_p75": st["p75"], "n_lease": st["n"],
            "sale_psf": round(s_psf, 0) if s_psf == s_psf else None,
            "gross_yield": round(gross, 4) if gross == gross else None,
            "implied_cap_data": round(implied_cap, 4) if implied_cap == implied_cap else None,
            "assumed_cap": asm["cap_rate"],
            "n_active": int(g["status"].isin(CRE.LIVE).sum()),
            "n_leased": int(g["status"].eq("Rented").sum()),
        })
    type_tbl = pd.DataFrame(type_rows)

    # ---- lease rate by submarket (blended) ----
    big = set(lease["submarket"].value_counts()[lambda x: x >= MIN_N].index)
    sub_rows = []
    for sub in sorted(big):
        g = lease[lease["submarket"] == sub]
        st = _stats(g["lease_rate_psf"])
        s_psf = float(sale_psf_sub.get(sub, np.nan))
        gross = st["median"] / s_psf if s_psf and not np.isnan(s_psf) else np.nan
        sub_rows.append({
            "submarket": sub, "corridors": CRE.corridor_hint(g["address"]),
            "lease_psf": st["median"], "n_lease": st["n"],
            "n_active": int(g["status"].isin(CRE.LIVE).sum()),
            "n_leased": int(g["status"].eq("Rented").sum()),
            "sale_psf": round(s_psf, 0) if s_psf == s_psf else None,
            "gross_yield": round(gross, 4) if gross == gross else None,
        })
    sub_tbl = pd.DataFrame(sub_rows).sort_values("lease_psf", ascending=False)

    # ---- submarket × type matrix (median lease $/SqFt) ----
    sxt = []
    for (sub, at), g in lease.groupby(["submarket", "asset_type"]):
        if len(g) >= MIN_N:
            sxt.append({"submarket": sub, "asset_type": at,
                        "lease_psf": round(float(g["lease_rate_psf"].median()), 1), "n": int(len(g))})
    sxt_tbl = pd.DataFrame(sxt)

    # ---- lease comps (the actual listings) ----
    comps = lease[["mls", "address", "submarket", "asset_type", "status", "sqft",
                   "lease_rate_psf", "year_built"]].copy()
    comps["annual_rent_est"] = (comps["lease_rate_psf"] * comps["sqft"]).round(-2)
    comps = comps.sort_values("lease_rate_psf", ascending=False)

    type_tbl.to_csv(os.path.join(CRE.PROC, "lease_rates.csv"), index=False)
    sub_tbl.to_csv(os.path.join(CRE.PROC, "lease_rates_by_submarket.csv"), index=False)
    comps.round(2).to_csv(os.path.join(CRE.PROC, "lease_comps.csv"), index=False)
    type_tbl[["asset_type", "sale_psf", "lease_psf", "gross_yield", "implied_cap_data",
              "assumed_cap"]].to_csv(os.path.join(CRE.PROC, "implied_yields.csv"), index=False)

    bundle = {
        "meta": {"n_lease_listings": int(df["deal_kind"].eq("Lease").sum()),
                 "n_lease_rated": int(len(lease)),
                 "n_active_lease": int(lease["status"].isin(CRE.LIVE).sum()),
                 "n_leased": int(lease["status"].eq("Rented").sum()),
                 "min_n": MIN_N,
                 "note": ("Lease $/SqFt/yr from listing rates (basis inferred). Implied cap = "
                          "(lease÷sale gross yield) × (1−vacancy) × (1−opex) — anchored to observed "
                          "rents & prices; market-level proxy, not a per-deal cap.")},
        "by_type": json.loads(type_tbl.to_json(orient="records")),
        "by_submarket": json.loads(sub_tbl.to_json(orient="records")),
        "submarket_x_type": json.loads(sxt_tbl.to_json(orient="records")) if len(sxt_tbl) else [],
        "comps": json.loads(comps.head(60).round(2).to_json(orient="records")),
    }
    with open(os.path.join(CRE.PROC, "leases_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"Leasing: {bundle['meta']['n_lease_rated']} rated lease listings "
          f"({bundle['meta']['n_active_lease']} active, {bundle['meta']['n_leased']} leased) | "
          f"{len(type_tbl)} asset types, {len(sub_tbl)} submarkets, {len(sxt_tbl)} submarket×type cells")
    if len(type_tbl):
        for _, r in type_tbl.iterrows():
            print(f"    {r['asset_type']:20s} lease ${r['lease_psf']}/SqFt · sale ${r['sale_psf']}/SqFt "
                  f"· gross {100*r['gross_yield']:.1f}% · implied cap "
                  f"{100*r['implied_cap_data']:.2f}%" if r['implied_cap_data'] else
                  f"    {r['asset_type']:20s} lease ${r['lease_psf']}/SqFt")


if __name__ == "__main__":
    main()
