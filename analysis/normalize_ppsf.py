#!/usr/bin/env python3
"""
Fort Lauderdale neighborhood price-per-square-foot (PPSF) normalization.

WHAT THIS DOES
--------------
Raw $/sqft is a confounded number. A neighborhood can look cheap or expensive
purely because of *when* its homes sold (2021 vs 2024), *what type* they were
(condos vs single-family), and how much sample it has. This pipeline strips
those confounders out with a weighted hedonic index and reports a clean,
apples-to-apples normalized PPSF for every Fort Lauderdale neighborhood, plus
normalized days-on-market and list-to-sale discount.

METHOD (weighted hedonic fixed-effects index)
---------------------------------------------
On the cell-level monthly data (one row = neighborhood x property-type x month),
weighted by the number of homes sold in each cell, we fit three regressions:

    log(PPSF)          ~ C(neighborhood) + C(property_type) + C(month)
    log(1 + DOM)       ~ C(neighborhood) + C(property_type) + C(month)
    sale_to_list       ~ C(neighborhood) + C(property_type) + C(month)

  * The C(month) effects capture market-wide appreciation -> this removes the
    "years" confounder (the market index).
  * The C(property_type) effects separate single-family, condo and townhouse.
  * The C(neighborhood) effects are the thing we actually want: each
    neighborhood's contribution holding time and property type constant.

We then PREDICT each metric for every neighborhood at a fixed reference point
(a chosen property type, averaged over the most recent 12 months) to get an
absolute, normalized number in real units. Log models use a Duan smearing
correction on retransformation.

DATA SOURCE
-----------
Redfin Data Center, neighborhood market tracker (public, free, legal to use):
https://www.redfin.com/news/data-center/ -- filtered to Fort Lauderdale, FL.
This is aggregate (neighborhood medians), so the normalization controls for
time, property type and sample size, but cannot control for within-neighborhood
differences (waterfront, age, lot, bed count). See README for the honest limits.

USAGE
-----
    python analysis/normalize_ppsf.py

Outputs land in data/processed/ (CSVs + JSON) and outputs/ (charts). The Excel
workbook and dashboard are built by build_excel.py and build_dashboard.py.
"""
from __future__ import annotations

import json
import os
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "raw", "redfin_fll_neighborhoods.tsv")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)

# Property types we model as comparable "homes" (exclude the "All Residential"
# super-aggregate to avoid double-counting, and Multi-Family whose per-sqft
# semantics differ). These are the clean, disaggregated for-living types.
MODEL_TYPES = ["Single Family Residential", "Condo/Co-op", "Townhouse"]
HEADLINE_TYPE = "Single Family Residential"  # the "home" ranking most people mean

REF_MONTHS = 12       # reference window = most recent N months (stabilises the "now")
MIN_SAMPLE = 20       # min approx. transactions over the span to enter main ranking
CONF_HIGH = 120       # sample thresholds for the confidence tier label
CONF_MED = 40


# --------------------------------------------------------------------------- #
# 1. Load & clean
# --------------------------------------------------------------------------- #
def load_and_clean() -> pd.DataFrame:
    df = pd.read_csv(RAW, sep="\t", na_values=["NA", ""], low_memory=False)
    df["period"] = pd.to_datetime(df["PERIOD_BEGIN"])
    df["neighborhood"] = (
        df["REGION"].str.replace(r"^Fort Lauderdale, FL - ", "", regex=True).str.strip()
    )
    df = df.rename(
        columns={
            "PROPERTY_TYPE": "ptype",
            "MEDIAN_PPSF": "ppsf",
            "MEDIAN_LIST_PPSF": "list_ppsf",
            "MEDIAN_SALE_PRICE": "sale_price",
            "HOMES_SOLD": "homes_sold",
            "MEDIAN_DOM": "dom",
            "AVG_SALE_TO_LIST": "sale_to_list",
            "SOLD_ABOVE_LIST": "sold_above",
            "PRICE_DROPS": "price_drops",
            "MONTHS_OF_SUPPLY": "months_supply",
            "NEW_LISTINGS": "new_listings",
            "INVENTORY": "inventory",
        }
    )
    keep = [
        "period", "neighborhood", "ptype", "ppsf", "list_ppsf", "sale_price",
        "homes_sold", "dom", "sale_to_list", "sold_above", "price_drops",
        "months_supply", "new_listings", "inventory",
    ]
    df = df[keep].copy()
    for c in ["ppsf", "list_ppsf", "sale_price", "homes_sold", "dom",
              "sale_to_list", "sold_above", "price_drops", "months_supply",
              "new_listings", "inventory"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df["homes_sold"].fillna(0) > 0]
    df["month_key"] = df["period"].dt.strftime("%Y-%m")
    # Non-overlapping quarter flag: the data are 90-day rolling windows stamped
    # monthly, so consecutive months overlap. Sampling Jan/Apr/Jul/Oct gives
    # roughly independent windows for honest transaction counts.
    df["quarter_anchor"] = df["period"].dt.month.isin([1, 4, 7, 10])
    return df


# --------------------------------------------------------------------------- #
# 2. Weighted hedonic fixed-effects models
# --------------------------------------------------------------------------- #
def fit_wls(model_df: pd.DataFrame, y: np.ndarray):
    """Weighted least squares: y ~ C(neighborhood)+C(ptype)+C(month), w=homes_sold."""
    import statsmodels.formula.api as smf

    d = model_df.copy()
    d["_y"] = y
    d["neighborhood"] = d["neighborhood"].astype("category")
    d["ptype"] = pd.Categorical(d["ptype"], categories=MODEL_TYPES)
    d["month_key"] = d["month_key"].astype("category")
    mod = smf.wls(
        "_y ~ C(neighborhood) + C(ptype) + C(month_key)",
        data=d,
        weights=d["homes_sold"].values,
    ).fit()
    return mod, d


def predict_reference(mod, template_df: pd.DataFrame, ref_months, ptype: str,
                      neighborhoods, smearing: float = 1.0, log: bool = True,
                      log1p: bool = False) -> pd.Series:
    """Predict a metric for every neighborhood at (ptype, avg over ref_months)."""
    rows = []
    for nb in neighborhoods:
        for mk in ref_months:
            rows.append({"neighborhood": nb, "ptype": ptype, "month_key": mk})
    pred_df = pd.DataFrame(rows)
    pred_df["neighborhood"] = pd.Categorical(
        pred_df["neighborhood"], categories=template_df["neighborhood"].cat.categories
    )
    pred_df["ptype"] = pd.Categorical(pred_df["ptype"], categories=MODEL_TYPES)
    pred_df["month_key"] = pd.Categorical(
        pred_df["month_key"], categories=template_df["month_key"].cat.categories
    )
    pred = mod.predict(pred_df)
    pred_df["pred"] = pred.values
    agg = pred_df.groupby("neighborhood", observed=True)["pred"].mean()
    if log:
        agg = np.expm1(agg) if log1p else np.exp(agg) * smearing
    return agg


def build_models(df: pd.DataFrame):
    mdf = df[df["ptype"].isin(MODEL_TYPES)].copy()
    ref_months = sorted(mdf["month_key"].unique())[-REF_MONTHS:]
    neighborhoods = sorted(mdf["neighborhood"].unique())

    out = {}

    # --- PPSF (log) ---
    ppdf = mdf[mdf["ppsf"] > 0].copy()
    mod_pp, tmpl_pp = fit_wls(ppdf, np.log(ppdf["ppsf"].values))
    smear_pp = float(np.mean(np.exp(mod_pp.resid)))
    for pt in MODEL_TYPES:
        out[f"norm_ppsf_{pt}"] = predict_reference(
            mod_pp, tmpl_pp, ref_months, pt, neighborhoods, smear_pp, log=True
        )
    # market index = month fixed effects, re-based to 100 at first month
    out["_month_index"] = _month_index(mod_pp, tmpl_pp, smear_pp)

    # --- DOM (log1p) ---
    ddf = mdf[mdf["dom"].notna()].copy()
    if len(ddf) > 100:
        mod_d, tmpl_d = fit_wls(ddf, np.log1p(ddf["dom"].values))
        out["norm_dom"] = predict_reference(
            mod_d, tmpl_d, ref_months, HEADLINE_TYPE, neighborhoods, log=True, log1p=True
        )
    else:
        out["norm_dom"] = pd.Series(dtype=float)

    # --- sale-to-list (level) ---
    sdf = mdf[mdf["sale_to_list"].notna()].copy()
    if len(sdf) > 100:
        mod_s, tmpl_s = fit_wls(sdf, sdf["sale_to_list"].values)
        out["norm_s2l"] = predict_reference(
            mod_s, tmpl_s, ref_months, HEADLINE_TYPE, neighborhoods, log=False
        )
    else:
        out["norm_s2l"] = pd.Series(dtype=float)

    out["_ref_months"] = ref_months
    out["_r2_ppsf"] = float(mod_pp.rsquared)
    out["_n_obs_ppsf"] = int(mod_pp.nobs)
    return out


def _month_index(mod, tmpl, smear) -> pd.DataFrame:
    """Quality-adjusted market PPSF index from the month fixed effects."""
    months = list(tmpl["month_key"].cat.categories)
    base_nb = tmpl["neighborhood"].cat.categories[0]
    rows = [{"neighborhood": base_nb, "ptype": HEADLINE_TYPE, "month_key": m} for m in months]
    pred_df = pd.DataFrame(rows)
    pred_df["neighborhood"] = pd.Categorical(pred_df["neighborhood"],
                                             categories=tmpl["neighborhood"].cat.categories)
    pred_df["ptype"] = pd.Categorical(pred_df["ptype"], categories=MODEL_TYPES)
    pred_df["month_key"] = pd.Categorical(pred_df["month_key"],
                                          categories=tmpl["month_key"].cat.categories)
    vals = np.exp(mod.predict(pred_df).values) * smear
    idx = pd.DataFrame({"month_key": months, "level": vals})
    idx["index_100"] = 100.0 * idx["level"] / idx["level"].iloc[0]
    return idx


# --------------------------------------------------------------------------- #
# 3. Descriptive per-neighborhood stats (cross-check + raw tables)
# --------------------------------------------------------------------------- #
def _wmean(v, w):
    v = pd.to_numeric(v, errors="coerce")
    w = pd.to_numeric(w, errors="coerce")
    m = v.notna() & w.notna() & (w > 0)
    if m.sum() == 0:
        return np.nan
    return float(np.average(v[m], weights=w[m]))


def descriptive_stats(df: pd.DataFrame, ptype: str) -> pd.DataFrame:
    d = df[df["ptype"] == ptype].copy()
    recent_cut = d["period"].max() - pd.DateOffset(months=REF_MONTHS)
    rows = []
    for nb, g in d.groupby("neighborhood"):
        recent = g[g["period"] > recent_cut]
        sample = int(g.loc[g["quarter_anchor"], "homes_sold"].sum())
        rows.append({
            "neighborhood": nb,
            "sample_txns": sample,
            "avg_homes_sold_90d": round(g["homes_sold"].mean(), 1),
            "raw_ppsf_recent": round(_wmean(recent["ppsf"], recent["homes_sold"]), 1)
                if len(recent) else np.nan,
            "raw_dom_recent": round(_wmean(recent["dom"], recent["homes_sold"]), 1)
                if len(recent) else np.nan,
            "raw_s2l_recent": _wmean(recent["sale_to_list"], recent["homes_sold"]),
            "price_drop_rate": _wmean(g["price_drops"], g["homes_sold"]),
            "sold_above_rate": _wmean(g["sold_above"], g["homes_sold"]),
            "months_supply": _wmean(g["months_supply"], g["homes_sold"]),
            "list_ppsf_recent": round(_wmean(recent["list_ppsf"], recent["homes_sold"]), 1)
                if len(recent) else np.nan,
            "first_year": int(g["period"].dt.year.min()),
            "last_period": g["period"].max().strftime("%Y-%m"),
        })
    return pd.DataFrame(rows).set_index("neighborhood")


def appreciation(df: pd.DataFrame, ptype: str) -> pd.Series:
    """Annualised PPSF growth (CAGR) from first to last reliable year, per nbhd."""
    d = df[df["ptype"] == ptype].copy()
    out = {}
    for nb, g in d.groupby("neighborhood"):
        yearly = (
            g.assign(year=g["period"].dt.year)
            .groupby("year")
            .apply(lambda x: _wmean(x["ppsf"], x["homes_sold"]))
            .dropna()
        )
        if len(yearly) >= 3:
            y0, y1 = yearly.index.min(), yearly.index.max()
            p0, p1 = yearly.loc[y0], yearly.loc[y1]
            n = y1 - y0
            if p0 and p0 > 0 and n > 0:
                out[nb] = (p1 / p0) ** (1 / n) - 1
    return pd.Series(out, name="ppsf_cagr")


# --------------------------------------------------------------------------- #
# 4. Assemble the master normalized table + scores
# --------------------------------------------------------------------------- #
def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if s.std(ddof=0) == 0 or s.notna().sum() < 2:
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / s.std(ddof=0)


def _conf(n):
    return "High" if n >= CONF_HIGH else ("Medium" if n >= CONF_MED else "Low")


def assemble(df: pd.DataFrame, models: dict) -> dict:
    tables = {}
    for pt in MODEL_TYPES:
        desc = descriptive_stats(df, pt)
        cagr = appreciation(df, pt)
        t = desc.copy()
        t["norm_ppsf"] = models[f"norm_ppsf_{pt}"].round(1)
        t["ppsf_cagr"] = cagr
        if pt == HEADLINE_TYPE:
            t["norm_dom"] = models["norm_dom"].round(0)
            t["norm_s2l"] = models["norm_s2l"]
        # discount %: how far below list homes sell (positive = buyer discount)
        s2l = t["norm_s2l"] if "norm_s2l" in t else t["raw_s2l_recent"]
        t["discount_pct"] = ((1 - s2l) * 100).round(2)
        t["raw_discount_pct"] = ((1 - t["raw_s2l_recent"]) * 100).round(2)
        # per-type premium/discount vs that type's citywide norm + confidence tier
        city_pt = _wmean(t.loc[t["sample_txns"] >= MIN_SAMPLE, "norm_ppsf"],
                         t.loc[t["sample_txns"] >= MIN_SAMPLE, "sample_txns"])
        t["vs_city_pct"] = ((t["norm_ppsf"] / city_pt - 1) * 100).round(1)
        t["confidence"] = t["sample_txns"].apply(_conf)
        tables[pt] = t

    # Headline table (single-family) with rankings + buyer-leverage score
    h = tables[HEADLINE_TYPE].copy()
    h = h[h["sample_txns"] >= MIN_SAMPLE].copy()
    city_norm = _wmean(h["norm_ppsf"], h["sample_txns"])
    h["vs_city_pct"] = ((h["norm_ppsf"] / city_norm - 1) * 100).round(1)
    h["value_rank"] = h["norm_ppsf"].rank(method="min", ascending=False).astype("Int64")
    h["appreciation_rank"] = h["ppsf_cagr"].rank(method="min", ascending=False).astype("Int64")

    # Buyer-leverage: longer DOM + bigger discount + more price drops + more supply.
    # Missing components are treated as neutral (z=0) rather than poisoning the score.
    lev = (
        zscore(h.get("norm_dom", pd.Series(index=h.index))).fillna(0.0)
        + zscore(h.get("discount_pct", pd.Series(index=h.index))).fillna(0.0)
        + zscore(h["price_drop_rate"]).fillna(0.0)
        + zscore(h["months_supply"]).fillna(0.0)
    ) / 4.0
    h["buyer_leverage"] = lev.round(3)
    h["leverage_rank"] = h["buyer_leverage"].rank(method="min", ascending=False).astype("Int64")

    tables["_headline"] = h.sort_values("norm_ppsf", ascending=False)
    tables["_city_norm_ppsf"] = city_norm
    return tables


# --------------------------------------------------------------------------- #
# 5. Write processed outputs (CSV + JSON bundle for dashboard/excel)
# --------------------------------------------------------------------------- #
def write_outputs(df: pd.DataFrame, models: dict, tables: dict):
    idx = models["_month_index"]
    idx.to_csv(os.path.join(PROC, "market_index.csv"), index=False)

    for pt in MODEL_TYPES:
        safe = pt.split("/")[0].replace(" ", "_").lower()
        tables[pt].to_csv(os.path.join(PROC, f"normalized_{safe}.csv"))
    tables["_headline"].to_csv(os.path.join(PROC, "headline_single_family.csv"))

    # Monthly time series per neighborhood (headline type) for charts/dashboard
    ts = (
        df[df["ptype"] == HEADLINE_TYPE]
        .assign(month=df["period"].dt.strftime("%Y-%m"))
        .pivot_table(index="month", columns="neighborhood", values="ppsf", aggfunc="mean")
        .round(1)
    )
    ts.to_csv(os.path.join(PROC, "ppsf_timeseries_sfr.csv"))

    # JSON bundle
    h = tables["_headline"].reset_index()
    bundle = {
        "meta": {
            "source": "Redfin Data Center - neighborhood market tracker (Fort Lauderdale, FL)",
            "generated_span": [df["period"].min().strftime("%Y-%m"),
                               df["period"].max().strftime("%Y-%m")],
            "ref_months": models["_ref_months"],
            "n_neighborhoods_ranked": int(len(h)),
            "city_norm_ppsf_sfr": round(tables["_city_norm_ppsf"], 1),
            "hedonic_r2": round(models["_r2_ppsf"], 3),
            "hedonic_n_obs": models["_n_obs_ppsf"],
            "min_sample": MIN_SAMPLE,
        },
        "market_index": idx.to_dict(orient="records"),
        "headline": json.loads(h.to_json(orient="records")),
        "condo": json.loads(
            tables["Condo/Co-op"].reset_index().to_json(orient="records")
        ),
        "townhouse": json.loads(
            tables["Townhouse"].reset_index().to_json(orient="records")
        ),
        "timeseries": {
            "months": list(ts.index),
            "series": {c: [None if pd.isna(v) else v for v in ts[c].tolist()]
                       for c in ts.columns},
        },
    }
    with open(os.path.join(PROC, "analysis_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    return bundle


# --------------------------------------------------------------------------- #
def main():
    print("Loading & cleaning Redfin Fort Lauderdale neighborhood data ...")
    df = load_and_clean()
    print(f"  {len(df):,} cell-rows | {df['neighborhood'].nunique()} neighborhoods "
          f"| {df['period'].min():%Y-%m}..{df['period'].max():%Y-%m}")

    print("Fitting weighted hedonic fixed-effects models (PPSF, DOM, sale-to-list) ...")
    models = build_models(df)
    print(f"  PPSF model: R^2={models['_r2_ppsf']:.3f} on {models['_n_obs_ppsf']:,} obs")

    print("Assembling normalized neighborhood tables & scores ...")
    tables = assemble(df, models)
    print(f"  {len(tables['_headline'])} single-family neighborhoods pass the "
          f"{MIN_SAMPLE}-txn sample gate")

    print("Writing processed CSVs + JSON bundle ...")
    write_outputs(df, models, tables)
    print("Done. See data/processed/.")


if __name__ == "__main__":
    main()
