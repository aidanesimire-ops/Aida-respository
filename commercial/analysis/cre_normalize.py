#!/usr/bin/env python3
"""
Core commercial normalization on the one hard metric the export contains: PRICE PER SQFT.

  log($/sqft) ~ log(sqft) + age + sold + C(asset_type) + C(submarket)

The submarket / asset-type fixed effects, evaluated for a standardized building, are the
normalized $/sqft — apples-to-apples across areas and property types. Then, because the
export has no income, every listing is ALSO given an assumption-derived income view (NOI,
implied cap, value) from cre_assumptions, which the dashboard recomputes live.

OUTPUT: data/processed/cre_all_valued.csv, cre_submarkets.csv, cre_types.csv, cre_bundle.json
"""
from __future__ import annotations
import json
import os
import warnings

import numpy as np
import pandas as pd

import cre_common as CRE
import cre_assumptions as A

warnings.filterwarnings("ignore")

MIN_GEO = 5          # non-failed sale rows a submarket needs for its own model level
MIN_ASSET = 6        # rows an asset type needs before folding into Commercial (other)


def _conf(n_sold):
    """Confidence tier from closed-comp depth — keeps thin cells honest."""
    return "High" if n_sold >= 8 else ("Med" if n_sold >= 4 else "Indicative")


def _prep(d):
    d = d.copy()
    d["lsqft"] = np.log(d["sqft"].clip(lower=1))
    d["age_i"] = d["age"].fillna(d["age"].median() if d["age"].notna().any() else 45)
    d["sold"] = d["status"].eq(CRE.SOLD).astype(int)
    return d


def assign_groups(s):
    s = s.copy()
    nonfailed = s[~s["status"].isin(CRE.FAILED)]
    geo_big = set(nonfailed["submarket"].value_counts()[lambda x: x >= MIN_GEO].index)
    asset_big = set(s["asset_type"].value_counts()[lambda x: x >= MIN_ASSET].index)
    s["geo"] = np.where(s["submarket"].isin(geo_big), s["submarket"], "OTHER")
    s["asset_grp"] = np.where(s["asset_type"].isin(asset_big), s["asset_type"], "Commercial (other)")
    return s


def fit(s):
    import statsmodels.formula.api as smf
    d = _prep(s[~s["status"].isin(CRE.FAILED)])       # fit on sold + live (not failed)
    d["y"] = np.log(d["ppsf"])
    d["asset_grp"] = d["asset_grp"].astype("category")
    d["geo"] = d["geo"].astype("category")
    mod = smf.ols("y ~ lsqft + age_i + sold + C(asset_grp) + C(geo)", data=d).fit()
    smear = float(np.mean(np.exp(mod.resid)))
    return mod, d, smear


def predict(mod, smear, rows, frame):
    r = rows.copy()
    r["asset_grp"] = pd.Categorical(r["asset_grp"], categories=frame["asset_grp"].cat.categories)
    r["geo"] = pd.Categorical(r["geo"], categories=frame["geo"].cat.categories)
    return np.exp(mod.predict(r)) * smear


def submarket_table(s, mod, frame, smear, med):
    modal_asset = s["asset_grp"].mode().iat[0]
    model_geos = [g for g in frame["geo"].cat.categories if g != "OTHER"]
    rows = []
    for sub in model_geos:
        g = s[s["submarket"] == sub]
        gsold = g[g["status"] == CRE.SOLD]
        std = pd.DataFrame([{"lsqft": np.log(med["sqft"]), "age_i": med["age"], "sold": 1,
                             "asset_grp": modal_asset, "geo": sub}])
        norm = float(predict(mod, smear, std, frame)[0])
        rows.append({
            "submarket": sub,
            "norm_ppsf": round(norm, 0),
            "sold_ppsf_median": round(float(gsold["ppsf"].median()), 0) if len(gsold) else np.nan,
            "ask_ppsf_median": round(float(g[g["status"].isin(CRE.LIVE)]["ppsf"].median()), 0)
                if g["status"].isin(CRE.LIVE).any() else np.nan,
            "median_price": int(g["price"].median()),
            "median_sqft": int(g["sqft"].median()),
            "n": int(len(g)), "n_sold": int(len(gsold)),
            "n_live": int(g["status"].isin(CRE.LIVE).sum()),
            "top_asset": g["asset_type"].mode().iat[0] if len(g) else None,
            "waterfront_share": round(float(g["waterfront"].mean()), 2),
            "confidence": _conf(len(gsold)),
            "corridors": CRE.corridor_hint(g["address"]),
        })
    t = pd.DataFrame(rows).set_index("submarket")
    city = float(np.average(t["norm_ppsf"], weights=t["n"]))
    t["vs_city_pct"] = ((t["norm_ppsf"] / city - 1) * 100).round(1)
    return t.sort_values("norm_ppsf", ascending=False), city


def type_table(s, mkt_rents):
    """Median $/sqft by asset type (factual) + the default income assumptions and the
    income they imply on the type's typical deal. Medians, not per-type model predictions,
    which are unstable where an asset type has only a handful of closed sales."""
    rows = []
    for at in [a for a in CRE.ASSET_ORDER if a in set(s["asset_type"])]:
        g = s[s["asset_type"] == at]
        gsold = g[g["status"] == CRE.SOLD]
        asm = A.for_type(at)
        d = A.derive(g["price"].median(), g["sqft"].median(), at)
        rows.append({
            "asset_type": at,
            "median_ppsf": round(float(g["ppsf"].median()), 0),
            "sold_ppsf_median": round(float(gsold["ppsf"].median()), 0) if len(gsold) else np.nan,
            "median_price": int(g["price"].median()),
            "median_sqft": int(g["sqft"].median()),
            "n": int(len(g)), "n_sold": int(len(gsold)),
            "n_live": int(g["status"].isin(CRE.LIVE).sum()),
            "confidence": _conf(len(gsold)),
            "assume_rent_psf": asm["rent_psf"], "assume_vacancy": asm["vacancy"],
            "assume_opex_ratio": asm["opex_ratio"], "assume_cap_rate": asm["cap_rate"],
            "market_rent_psf": mkt_rents.get(at, {}).get("rate"),
            "market_rent_n": mkt_rents.get(at, {}).get("n"),
            "typical_noi_psf": round(d["noi_psf"], 2),
            "typical_implied_cap": round(d["implied_cap"], 4),
        })
    return pd.DataFrame(rows).set_index("asset_type")


def value_all(s, mod, frame, smear):
    d = _prep(s)
    d["asset_grp"] = np.where(d["asset_type"].isin(set(frame["asset_grp"].cat.categories)),
                              d["asset_type"], "Commercial (other)")
    d["geo"] = np.where(d["submarket"].isin(set(frame["geo"].cat.categories)),
                        d["submarket"], "OTHER")
    d["pred_ppsf"] = predict(mod, smear, d, frame)
    d["ppsf_gap_pct"] = (d["ppsf"] / d["pred_ppsf"] - 1) * 100
    # assumption-derived income view (default assumptions; dashboard recomputes live)
    inc = d.apply(lambda r: A.derive(r["price"], r["sqft"], r["asset_type"]), axis=1)
    d["noi"] = [x["noi"] for x in inc]
    d["implied_cap"] = [x["implied_cap"] for x in inc]
    d["market_cap"] = [x["market_cap"] for x in inc]
    d["assumed_value"] = [x["value"] for x in inc]
    d["income_gap_pct"] = [x["value_gap"] * 100 for x in inc]
    keep = ["mls", "address", "submarket", "asset_type", "status", "deal_kind", "price",
            "sqft", "units", "price_per_unit", "ppsf", "pred_ppsf", "ppsf_gap_pct", "age",
            "year_built", "waterfront", "bays", "zoning", "noi", "implied_cap", "market_cap",
            "assumed_value", "income_gap_pct"]
    out = d[keep].copy()
    out["price_band"] = out["price"].map(CRE.price_band)
    out["price_per_unit"] = out["price_per_unit"].round(-2)
    for c in ("ppsf", "pred_ppsf", "assumed_value", "noi"):
        out[c] = out[c].round(0)
    for c in ("ppsf_gap_pct", "income_gap_pct"):
        out[c] = out[c].round(1)
    for c in ("implied_cap", "market_cap"):
        out[c] = out[c].round(4)
    return out


def main():
    df = CRE.load_clean()
    s = CRE.sales(df)
    s = assign_groups(s)
    print(f"{len(df):,} listings | {len(s):,} valid SALE comps "
          f"({int(s['status'].eq(CRE.SOLD).sum())} closed)")

    mod, frame, smear = fit(s)
    print(f"$/sqft hedonic: R^2={mod.rsquared:.3f} adjR^2={mod.rsquared_adj:.3f} n={int(mod.nobs)}")
    sold_gap = (np.exp(mod.params.get("sold", 0)) - 1) * 100
    print(f"  closed-vs-listed effect: {sold_gap:+.1f}% | size elasticity "
          f"{mod.params.get('lsqft', float('nan')):.3f}")

    mkt_rents, n_lease_rated = CRE.market_rents(df)
    mf = s[(s["asset_type"] == "Multifamily")]
    mf_units = int(mf["units"].notna().sum())
    print(f"  market rents from {n_lease_rated} lease comps ({len(mkt_rents)} types); "
          f"parsed unit counts for {mf_units}/{len(mf)} multifamily comps")

    med = {"sqft": float(s["sqft"].median()), "age": float(s["age"].median())}
    subt, city = submarket_table(s, mod, frame, smear, med)
    typt = type_table(s, mkt_rents)
    valued = value_all(s, mod, frame, smear)

    subt.to_csv(os.path.join(CRE.PROC, "cre_submarkets.csv"))
    typt.to_csv(os.path.join(CRE.PROC, "cre_types.csv"))
    valued.to_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"), index=False)
    print(f"  {len(subt)} submarkets ranked | city normalized ${city:,.0f}/sqft")

    # per-asset premiums vs the reference asset (Commercial other)
    asset_prem = {}
    for at in frame["asset_grp"].cat.categories:
        p = f"C(asset_grp)[T.{at}]"
        if p in mod.params:
            asset_prem[at] = round((np.exp(mod.params[p]) - 1) * 100, 1)

    bundle = {
        "meta": {
            "asset_class": "Commercial (all types)",
            "sources": sorted(df["source_file"].unique().tolist()),
            "n_listings": int(len(df)),
            "n_sale_comps": int(len(s)),
            "n_closed": int(s["status"].eq(CRE.SOLD).sum()),
            "n_lease": int(df["deal_kind"].eq("Lease").sum()),
            "hedonic_r2": round(float(mod.rsquared), 3),
            "hedonic_n": int(mod.nobs),
            "city_norm_ppsf": round(city, 0),
            "closed_vs_listed_pct": round(sold_gap, 1),
            "standardized_building": {"sqft": int(med["sqft"]), "age": int(med["age"])},
            "asset_premium_pct": asset_prem,
            "status_counts": {k: int(v) for k, v in df["status"].value_counts().items()},
            "no_income_note": ("MLS export carries no NOI / rent / cap / units — income "
                               "metrics are derived from assumptions, with rents anchored to "
                               "lease comps where available and unit counts parsed from addresses."),
            "market_rent_lease_comps": n_lease_rated,
            "mf_unit_coverage": {"parsed": mf_units, "total": int(len(mf))},
        },
        "submarkets": json.loads(subt.reset_index().to_json(orient="records")),
        "types": json.loads(typt.reset_index().to_json(orient="records")),
        "assumptions": {"by_type": A.DEFAULTS, "finance": A.FINANCE},
        "market_rents": mkt_rents,
    }
    with open(os.path.join(CRE.PROC, "cre_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print("Done. Wrote data/processed/cre_*.{csv,json}")


if __name__ == "__main__":
    main()
