#!/usr/bin/env python3
"""
Per-home hedonic normalization of Fort Lauderdale MLS listings.

INPUT  : data/raw/mls/*.csv  (agent single-line exports, one row per listing)
         statuses: sold, expired, withdrawn, temp_off, cancelled,
                   active_coming_soon, active_pending
OUTPUT : data/processed/mls_*.csv + data/processed/mls_bundle.json

METHOD
------
1. Clean the raw export (prices, sqft, year, booleans, property type,
   canonical neighborhood from the messy Subdivision/Complex field).
2. Fit a per-home hedonic on CLOSED SALES:
       log(sale_ppsf) ~ log(sqft) + beds + baths + waterfront + pool + age
                        + C(property_type) + C(geo)
   where geo = canonical neighborhood (when it has enough closed sales) else a
   fallback MLS-area bucket. The neighborhood fixed effects, converted back to a
   standardized home, are the normalized $/sqft. The waterfront/pool/size/age
   coefficients are reported as interpretable premiums.
3. Discounts: actual (list - sale)/list per closed home, summarized by neighborhood.
4. Overpricing: for every non-sold listing, compare its asking $/sqft to the
   model's predicted market $/sqft for the same home -> an overpricing gap.
   Failed listings quantify what the market rejects; active/pending listings are
   flagged under / fair / over-priced so the user can act on live inventory.

NOTE: the MLS export carries no list/close dates or days-on-market, so the time
dimension (appreciation) and DOM come from the Redfin layer (normalize_ppsf.py).
"""
from __future__ import annotations
import glob
import json
import os
import re
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAWDIR = os.path.join(ROOT, "data", "raw", "mls")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)

THIS_YEAR = 2026
MIN_GEO_SOLD = 10      # min closed sales for a neighborhood to be its own model level
MIN_REPORT_SOLD = 12   # min closed sales to appear in the neighborhood ranking
NEW_MAX_AGE = 6        # <= this many years old counts as "new construction"
PPSF_LO, PPSF_HI = 40, 6000     # plausible $/sqft band (drop data errors)

STATUS_GROUP = {
    "sold": "Sold",
    "expired": "Expired", "withdrawn": "Withdrawn",
    "cancelled": "Cancelled", "temp_off": "TempOff",
    "active_coming_soon": "Active", "active_pending": "Pending",
}
FAILED = {"Expired", "Withdrawn", "Cancelled", "TempOff"}
LIVE = {"Active", "Pending"}

# Canonical display names for the biggest / most important neighborhoods, keyed
# by their cleaned (upper) form. Keeps the headline neighborhoods correct and
# merges obvious export variants.
CANON = {
    "PROGRESSO": "Progresso", "CORAL RIDGE": "Coral Ridge",
    "CORAL RIDGE GALT": "Coral Ridge Galt", "VICTORIA PARK": "Victoria Park",
    "RIO VISTA ISLES": "Rio Vista", "RIO VISTA": "Rio Vista",
    "COLEE HAMMOCK": "Colee Hammock", "POINSETTIA HEIGHTS": "Poinsettia Heights",
    "LAUDERDALE MANORS": "Lauderdale Manors", "WILTON STATION": "Wilton Station",
    "WATERGARDEN": "Watergarden", "MARINA LANDINGS": "Marina Landings",
    "RIVER REACH": "River Reach", "SOUTH NEW RIVER ISLES": "South New River Isles",
    "LAS OLAS": "Las Olas", "LAS OLAS ISLES": "Las Olas Isles",
    "SUNRISE INTRACOASTAL": "Sunrise Intracoastal", "HARBOR BEACH": "Harbor Beach",
    "SEVEN ISLES": "Seven Isles", "NURMI ISLES": "Nurmi Isles",
    "IDLEWYLD": "Idlewyld", "LAUDERDALE HARBOURS": "Lauderdale Harbours",
    "BERMUDA RIVIERA": "Bermuda Riviera", "IMPERIAL POINT": "Imperial Point",
    "CORAL SHORES": "Coral Shores", "LAKE RIDGE": "Lake Ridge",
    "TARPON RIVER": "Tarpon River", "CROISSANT PARK": "Croissant Park",
    "DOLPHIN ISLES": "Dolphin Isles", "LANDINGS": "Landings",
    "RIVERLAND": "Riverland", "MELROSE PARK": "Melrose Park",
    "EDGEWOOD": "Edgewood", "SAILBOAT BEND": "Sailboat Bend",
    "FLAGLER VILLAGE": "Flagler Village", "HARBORDALE": "Harbordale",
}
NOISE = {"RESUB", "SUB", "ADD", "SEC", "PLAT", "BLK", "BLKS", "OF", "PB", "AMD",
         "AMENDED", "REV", "REVISED", "NO", "UNIT", "UNITS", "CONDO", "THE",
         "AT", "A", "REPLAT", "PARCEL", "TR", "PT"}


# --------------------------------------------------------------------------- #
def _num(s):
    if pd.isna(s):
        return np.nan
    v = re.sub(r"[^0-9.]", "", str(s))
    if v in ("", "."):
        return np.nan
    try:
        return float(v)
    except ValueError:
        return np.nan


def _canon_neigh(s):
    if pd.isna(s):
        return None
    s = str(s).upper().strip()
    s = re.sub(r"[0-9]+[-0-9/]*", " ", s)           # drop numbers & plat refs
    s = re.sub(r"[^A-Z& ]", " ", s)
    # drop single-letter plat-block tokens and noise words; normalise isle variants
    toks = [t for t in s.split() if len(t) > 1 and t not in NOISE]
    toks = ["ISLES" if t in ("ISLE", "ISLAND", "ISLANDS") else t for t in toks]
    # collapse a fully-doubled phrase: "VICTORIA PARK VICTORIA PARK" -> "VICTORIA PARK"
    n = len(toks)
    if n >= 2 and n % 2 == 0 and toks[: n // 2] == toks[n // 2:]:
        toks = toks[: n // 2]
    # collapse immediate duplicate tokens
    out = []
    for t in toks:
        if not out or out[-1] != t:
            out.append(t)
    key = " ".join(out).strip()
    if not key:
        return None
    if key in CANON:
        return CANON[key]
    # try progressive prefix match against canon (e.g. "CORAL RIDGE GALT X")
    for k in sorted(CANON, key=len, reverse=True):
        if key.startswith(k + " ") or key == k:
            return CANON[k]
    return key.title()


def _ptype(s):
    if pd.isna(s):
        return None
    s = str(s).strip().lower()
    if s.startswith("single"):
        return "Single Family"
    if s.startswith("condo"):
        return "Condo"
    if s.startswith("co-op") or s.startswith("coop"):
        return "Condo"
    if s.startswith("town"):
        return "Townhouse"
    if s.startswith("villa"):
        return "Villa"
    return None  # hotel/timeshare/lease/etc -> excluded


# --------------------------------------------------------------------------- #
def load_clean() -> pd.DataFrame:
    frames = []
    for path in sorted(glob.glob(os.path.join(RAWDIR, "*.csv"))):
        key = os.path.splitext(os.path.basename(path))[0]
        if key not in STATUS_GROUP:
            continue
        d = pd.read_csv(path)
        d["status"] = STATUS_GROUP[key]
        frames.append(d)
    raw = pd.concat(frames, ignore_index=True)

    df = pd.DataFrame({
        "status": raw["status"],
        "area": raw["Area"].map(lambda x: re.sub(r"\.0$", "", str(x)) if pd.notna(x) else None),
        "neighborhood": raw["Subdivision/Complex"].map(_canon_neigh),
        "list_price": raw["List Price"].map(_num),
        "sale_price": raw["Sale Price"].map(_num),
        "beds": pd.to_numeric(raw["#Beds"], errors="coerce"),
        "fbaths": pd.to_numeric(raw["#FBaths"], errors="coerce"),
        "hbaths": pd.to_numeric(raw["#HBaths"], errors="coerce"),
        "sqft": raw["SqFt LA"].map(_num),
        "ptype": raw["Type of Property"].map(_ptype),
        "year_built": raw["Year Built"].map(_num),
        "garage": pd.to_numeric(raw["#Garage Spaces"], errors="coerce"),
        "pool": raw["Pool YN"].astype(str).str.strip().str.lower().eq("yes"),
        "waterfront": raw["Waterfront Property (Y/N)"].astype(str).str.strip().str.lower().eq("yes"),
        "lot_sqft": raw["Lot SqFt"].map(_num),
    })
    df["baths"] = df["fbaths"].fillna(0) + 0.5 * df["hbaths"].fillna(0)
    yr = df["year_built"].where((df["year_built"] >= 1900) & (df["year_built"] <= THIS_YEAR))
    df["age"] = THIS_YEAR - yr
    df["ask_ppsf"] = df["list_price"] / df["sqft"]
    df["sale_ppsf"] = df["sale_price"] / df["sqft"]
    df["discount"] = np.where(
        (df["status"] == "Sold") & df["list_price"].gt(0),
        (df["list_price"] - df["sale_price"]) / df["list_price"], np.nan)

    # basic validity
    df = df[df["ptype"].notna() & df["sqft"].gt(200) & df["neighborhood"].notna()]
    # drop implausible ppsf (data errors) on whichever price defines the listing
    ppsf = df["sale_ppsf"].where(df["status"] == "Sold", df["ask_ppsf"])
    df = df[ppsf.between(PPSF_LO, PPSF_HI)]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------------- #
def assign_geo(df: pd.DataFrame) -> pd.DataFrame:
    sold_counts = df[df["status"] == "Sold"]["neighborhood"].value_counts()
    big = set(sold_counts[sold_counts >= MIN_GEO_SOLD].index)
    df = df.copy()
    df["geo"] = np.where(df["neighborhood"].isin(big), df["neighborhood"],
                         "AREA_" + df["area"].astype(str))
    return df


def fit_hedonic(sold: pd.DataFrame):
    import statsmodels.formula.api as smf

    d = sold.copy()
    d["ltsqft"] = np.log(d["sqft"])
    d["beds_i"] = d["beds"].fillna(d["beds"].median())
    d["baths_i"] = d["baths"].fillna(d["baths"].median())
    d["age_i"] = d["age"].fillna(d["age"].median())
    d["wf"] = d["waterfront"].astype(int)
    d["pl"] = d["pool"].astype(int)
    d["new"] = (d["age_i"] <= NEW_MAX_AGE).astype(int)   # new construction flag
    d["y"] = np.log(d["sale_ppsf"])
    d["ptype"] = d["ptype"].astype("category")
    d["geo"] = d["geo"].astype("category")
    mod = smf.ols(
        "y ~ ltsqft + beds_i + baths_i + wf + pl + age_i + new + C(ptype) + C(geo)",
        data=d).fit()
    smear = float(np.mean(np.exp(mod.resid)))
    return mod, d, smear


def fit_land(sold: pd.DataFrame):
    """SFR-only structure-vs-land model -> marginal value of lot size.
    log(sale_price) ~ log(living_sqft) + log(lot_sqft) + beds + baths + wf + pool
                      + age + new + C(geo).  The lot elasticity converts to an
    implied land $/sqft (derivative of price wrt lot)."""
    import statsmodels.formula.api as smf
    d = sold[(sold["ptype"] == "Single Family") & sold["lot_sqft"].gt(500)
             & sold["sale_price"].gt(0)].copy()
    d["ltliv"] = np.log(d["sqft"])
    d["ltlot"] = np.log(d["lot_sqft"])
    d["beds_i"] = d["beds"].fillna(d["beds"].median())
    d["baths_i"] = d["baths"].fillna(d["baths"].median())
    d["age_i"] = d["age"].fillna(d["age"].median())
    d["wf"] = d["waterfront"].astype(int)
    d["pl"] = d["pool"].astype(int)
    d["new"] = (d["age_i"] <= NEW_MAX_AGE).astype(int)
    d["y"] = np.log(d["sale_price"])
    d["geo"] = d["geo"].astype("category")
    mod = smf.ols("y ~ ltliv + ltlot + beds_i + baths_i + wf + pl + age_i + new + C(geo)",
                  data=d).fit()
    return mod, float(mod.params["ltlot"]), d


def predict_ppsf(mod, smear, rows: pd.DataFrame) -> np.ndarray:
    """rows must carry ltsqft, beds_i, baths_i, wf, pl, age_i, new, ptype, geo."""
    return np.exp(mod.predict(rows)) * smear


# --------------------------------------------------------------------------- #
def _med_ppsf(g, ptype=None):
    x = g if ptype is None else g[g["ptype"] == ptype]
    return round(float(x["sale_ppsf"].median()), 1) if len(x) else None


def normalized_table(df, sold, mod, dmodel, smear, land_elast):
    """Predict a standardized home per neighborhood -> normalized $/sqft, plus
    new-vs-existing, per-type pricing, and implied land value context."""
    med = {
        "sqft": sold["sqft"].median(),
        "beds": sold["beds"].median(),
        "baths": sold["baths"].median(),
        "age": sold["age"].median(),
    }
    geos = dmodel["geo"].cat.categories
    ptypes = dmodel["ptype"].cat.categories

    sold_named = sold[sold["geo"].isin([g for g in geos if not g.startswith("AREA_")])]
    rows = []
    for nb, g in sold_named.groupby("neighborhood"):
        if len(g) < MIN_REPORT_SOLD:
            continue
        geo = nb if nb in set(geos) else "AREA_" + str(g["area"].mode().iat[0])
        basis = g["ptype"].mode().iat[0]
        pred_std = pd.DataFrame([{
            "ltsqft": np.log(med["sqft"]), "beds_i": med["beds"],
            "baths_i": med["baths"], "age_i": med["age"], "wf": 0, "pl": 0, "new": 0,
            "ptype": pd.Categorical([basis], categories=ptypes)[0],
            "geo": pd.Categorical([geo], categories=geos)[0],
        }])
        norm = float(predict_ppsf(mod, smear, pred_std)[0])

        newg = g[g["age"] <= NEW_MAX_AGE]
        exg = g[g["age"] > NEW_MAX_AGE]
        new_ppsf = _med_ppsf(newg) if len(newg) >= 4 else None
        ex_ppsf = _med_ppsf(exg) if len(exg) >= 4 else None
        new_prem = (round((new_ppsf / ex_ppsf - 1) * 100, 1)
                    if new_ppsf and ex_ppsf else None)

        # waterfront vs dry-lot actual $/sqft in THIS neighborhood
        wfg = g[g["waterfront"]]
        dryg = g[~g["waterfront"]]
        wf_ppsf = _med_ppsf(wfg) if len(wfg) >= 4 else None
        dry_ppsf = _med_ppsf(dryg) if len(dryg) >= 4 else None
        wf_prem_local = (round((wf_ppsf / dry_ppsf - 1) * 100, 1)
                         if wf_ppsf and dry_ppsf else None)

        # implied land value ($/sqft of lot) for SFR in this neighborhood
        sfr = g[(g["ptype"] == "Single Family") & g["lot_sqft"].gt(500)]
        land_ppsf = None
        if len(sfr) >= 6:
            land_ppsf = round(land_elast * sfr["sale_price"].median()
                              / sfr["lot_sqft"].median(), 1)

        rows.append({
            "neighborhood": nb, "basis_type": basis,
            "norm_ppsf": round(norm, 1),
            "sold_ppsf_median": round(float(g["sale_ppsf"].median()), 1),
            "sold_n": int(len(g)),
            "waterfront_share": round(float(g["waterfront"].mean()), 2),
            "waterfront_ppsf": wf_ppsf, "dry_ppsf": dry_ppsf,
            "waterfront_premium_local_pct": wf_prem_local,
            "n_waterfront": int(len(wfg)),
            "median_sale_price": int(g["sale_price"].median()),
            "median_sqft": int(g["sqft"].median()),
            "median_discount_pct": round(float(g["discount"].median()) * 100, 2)
                if g["discount"].notna().any() else np.nan,
            "house_ppsf": _med_ppsf(g, "Single Family"),
            "condo_ppsf": _med_ppsf(g, "Condo"),
            "townhouse_ppsf": _med_ppsf(g, "Townhouse"),
            "n_house": int((g["ptype"] == "Single Family").sum()),
            "n_condo": int((g["ptype"] == "Condo").sum()),
            "n_townhouse": int((g["ptype"] == "Townhouse").sum()),
            "new_ppsf": new_ppsf, "existing_ppsf": ex_ppsf,
            "new_premium_pct": new_prem, "new_n": int(len(newg)),
            "implied_land_ppsf": land_ppsf,
            "median_lot_sqft": int(sfr["lot_sqft"].median()) if len(sfr) >= 6 else None,
            "median_year_built": int(g["year_built"].median())
                if g["year_built"].notna().any() else None,
        })
    t = pd.DataFrame(rows).set_index("neighborhood")
    city = float(np.average(t["norm_ppsf"], weights=t["sold_n"]))
    t["vs_city_pct"] = ((t["norm_ppsf"] / city - 1) * 100).round(1)
    return t.sort_values("norm_ppsf", ascending=False), city, med


def overpricing(df, sold, mod, smear, dmodel):
    """Predict market ppsf for non-sold listings; gap vs asking."""
    geos = set(dmodel["geo"].cat.categories)
    ptypes = dmodel["ptype"].cat.categories
    d = df[df["status"] != "Sold"].copy()
    d = d[d["ask_ppsf"].notna()]
    d["ltsqft"] = np.log(d["sqft"])
    d["beds_i"] = d["beds"].fillna(sold["beds"].median())
    d["baths_i"] = d["baths"].fillna(sold["baths"].median())
    d["age_i"] = d["age"].fillna(sold["age"].median())
    d["wf"] = d["waterfront"].astype(int)
    d["pl"] = d["pool"].astype(int)
    d["new"] = (d["age_i"] <= NEW_MAX_AGE).astype(int)
    d["geo_use"] = np.where(d["geo"].isin(geos), d["geo"], np.nan)
    d = d[d["geo_use"].notna()]
    d["ptype"] = pd.Categorical(d["ptype"], categories=ptypes)
    d["geo"] = pd.Categorical(d["geo_use"], categories=dmodel["geo"].cat.categories)
    d = d[d["ptype"].notna()]
    d["pred_ppsf"] = predict_ppsf(mod, smear, d)
    d["gap_pct"] = (d["ask_ppsf"] / d["pred_ppsf"] - 1) * 100
    # clip absurd gaps from characteristic mismatches
    d = d[d["gap_pct"].between(-80, 300)]
    return d


def load_redfin_context():
    """Pull appreciation (CAGR) and days-on-market per neighborhood from the
    Redfin layer, if it has been generated, to enrich the talking points."""
    path = os.path.join(PROC, "headline_single_family.csv")
    if not os.path.exists(path):
        return {}
    r = pd.read_csv(path).set_index("neighborhood")
    ctx = {}
    for nb, row in r.iterrows():
        ctx[nb] = {"cagr": row.get("ppsf_cagr"), "dom": row.get("norm_dom")}
    return ctx


def build_profiles(ntable, prem, city, city_land, redfin_ctx):
    """One homeowner-ready profile per neighborhood: a headline + data-backed
    talking points an agent can say out loud."""
    profiles = []
    for nb, r in ntable.iterrows():
        tp = []
        vs = r["vs_city_pct"]
        pos = f"{abs(vs):.0f}% {'above' if vs >= 0 else 'below'} the citywide average"
        tp.append(f"A standardized home here normalizes to ${r['norm_ppsf']:,.0f}/sqft — "
                  f"{pos} (city ${city:,.0f}/sqft).")
        tp.append(f"Recent closed sales run a median ${r['median_sale_price']:,.0f} on about "
                  f"{r['median_sqft']:,} sqft (${r['sold_ppsf_median']:,.0f}/sqft actual).")
        # property-type spread
        types = [("houses", r.get("house_ppsf"), r.get("n_house")),
                 ("condos", r.get("condo_ppsf"), r.get("n_condo")),
                 ("townhomes", r.get("townhouse_ppsf"), r.get("n_townhouse"))]
        parts = [f"{lab} ${v:,.0f}/sqft" for lab, v, n in types if v and n and n >= 4]
        if len(parts) >= 2:
            tp.append("By property type: " + ", ".join(parts) + ".")
        # waterfront $/sqft (neighborhood-specific)
        if r.get("waterfront_ppsf") and r.get("dry_ppsf"):
            extra = (f" — about +{r['waterfront_premium_local_pct']:.0f}% for the water here"
                     if r.get("waterfront_premium_local_pct") is not None else "")
            tp.append(f"Waterfront homes sell around ${r['waterfront_ppsf']:,.0f}/sqft vs "
                      f"${r['dry_ppsf']:,.0f}/sqft dry{extra}.")
        elif r.get("waterfront_ppsf"):
            tp.append(f"Waterfront homes sell around ${r['waterfront_ppsf']:,.0f}/sqft here "
                      f"({r['waterfront_share']*100:.0f}% of sales are waterfront).")
        elif r["waterfront_share"] >= 0.12:
            tp.append(f"{r['waterfront_share']*100:.0f}% of sales are waterfront; waterfront is "
                      f"worth about +{prem['waterfront_pct']:.0f}% per foot citywide, all else equal.")
        # new vs existing
        if r.get("new_premium_pct") is not None:
            tp.append(f"New construction sells around ${r['new_ppsf']:,.0f}/sqft vs "
                      f"${r['existing_ppsf']:,.0f} for existing here — a +{r['new_premium_pct']:.0f}% new-build premium.")
        elif prem.get("new_construction_pct"):
            tp.append(f"Citywide, new construction carries roughly +{prem['new_construction_pct']:.0f}% "
                      f"per foot over comparable existing homes.")
        # implied land value
        if r.get("implied_land_ppsf") and r.get("median_lot_sqft"):
            land_total = r["implied_land_ppsf"] * r["median_lot_sqft"]
            tp.append(f"On a typical {r['median_lot_sqft']:,} sqft lot the land alone is worth "
                      f"~${r['implied_land_ppsf']:,.0f}/sqft (~${land_total:,.0f}).")
        # discount / DOM / appreciation
        disc = r.get("median_discount_pct")
        ctx = redfin_ctx.get(nb, {})
        dom = ctx.get("dom")
        cagr = ctx.get("cagr")
        if pd.notna(disc):
            s = f"Homes typically close about {disc:.0f}% under asking"
            if dom and pd.notna(dom):
                s += f", after roughly {dom:.0f} days on market"
            tp.append(s + ".")
        if cagr and pd.notna(cagr):
            tp.append(f"Prices here have compounded about {cagr*100:.0f}%/yr over the last decade.")
        # failure rate
        if r.get("failure_rate") is not None and pd.notna(r["failure_rate"]):
            tp.append(f"{r['failure_rate']:.0f}% of listings here fail to sell — pricing right "
                      f"the first time matters more than in most areas.")
        profiles.append({
            "neighborhood": nb,
            "headline": f"${r['norm_ppsf']:,.0f}/sqft normalized · {pos}",
            "talking_points": tp,
        })
    return profiles


# --------------------------------------------------------------------------- #
def main():
    print("Loading & cleaning MLS listings ...")
    df = load_clean()
    print(f"  {len(df):,} clean listings | statuses: "
          + ", ".join(f"{k}={v}" for k, v in df['status'].value_counts().items()))
    df = assign_geo(df)
    sold = df[df["status"] == "Sold"].copy()
    print(f"  {len(sold):,} closed sales feed the hedonic model")

    print("Fitting per-home hedonic (log sale $/sqft) ...")
    mod, dmodel, smear = fit_hedonic(sold)
    sold = dmodel  # carries engineered cols + geo category
    print(f"  R^2 = {mod.rsquared:.3f} | adj R^2 = {mod.rsquared_adj:.3f} | n = {int(mod.nobs):,}")

    # interpretable premiums
    def coefpct(name):
        return (np.exp(mod.params[name]) - 1) * 100
    prem = {
        "waterfront_pct": round(coefpct("wf"), 1),
        "pool_pct": round(coefpct("pl"), 1),
        "new_construction_pct": round(coefpct("new"), 1),
        "size_elasticity": round(mod.params["ltsqft"], 3),
        "age_per_decade_pct": round((np.exp(mod.params["age_i"] * 10) - 1) * 100, 2),
        "bath_pct": round(coefpct("baths_i"), 1),
    }
    print(f"  premiums: waterfront {prem['waterfront_pct']}% | pool {prem['pool_pct']}% "
          f"| new-construction {prem['new_construction_pct']}% | +decade age {prem['age_per_decade_pct']}%")

    print("Fitting SFR structure-vs-land model ...")
    land_mod, land_elast, land_d = fit_land(sold)
    city_land = float(land_elast * land_d["sale_price"].median() / land_d["lot_sqft"].median())
    print(f"  lot elasticity {land_elast:.3f} | implied citywide land ${city_land:,.0f}/lot-sqft "
          f"(SFR R^2={land_mod.rsquared:.3f})")

    print("Building normalized neighborhood table ...")
    ntable, city, med = normalized_table(df, sold, mod, dmodel, smear, land_elast)
    print(f"  {len(ntable)} neighborhoods ranked | citywide normalized "
          f"${city:,.0f}/sqft (standardized dry-lot home)")

    print("Scoring overpricing on failed + live listings ...")
    op = overpricing(df, sold, mod, smear, dmodel)
    failed = op[op["status"].isin(FAILED)]
    live = op[op["status"].isin(LIVE)].copy()
    # per-neighborhood failure rate + failed overpricing gap
    grp = []
    for nb in ntable.index:
        s_n = int((sold["neighborhood"] == nb).sum())
        f_n = int((failed["neighborhood"] == nb).sum())
        fg = failed.loc[failed["neighborhood"] == nb, "gap_pct"]
        grp.append({
            "neighborhood": nb,
            "failure_rate": round(f_n / (f_n + s_n) * 100, 1) if (f_n + s_n) else np.nan,
            "failed_median_overpricing": round(float(fg.median()), 1) if len(fg) else np.nan,
            "failed_n": f_n,
        })
    ftab = pd.DataFrame(grp).set_index("neighborhood")
    ntable = ntable.join(ftab)

    # flag live listings
    def flag(g):
        return "Underpriced" if g < -7 else ("Overpriced" if g > 10 else "Fair")
    live["flag"] = live["gap_pct"].apply(flag)
    live_out = live[["status", "neighborhood", "ptype", "list_price", "sqft",
                     "ask_ppsf", "pred_ppsf", "gap_pct", "waterfront", "flag"]].copy()
    live_out = live_out.round({"ask_ppsf": 0, "pred_ppsf": 0, "gap_pct": 1})
    # Actionable deal shortlist: single-family only (condo value hinges on
    # floor/view/renovation the model can't see) and bounded gaps -- a -70% gap is
    # almost always a product/data mismatch, not a real bargain.
    deals = live_out[(live_out["flag"] == "Underpriced")
                     & (live_out["ptype"] == "Single Family")
                     & (live_out["gap_pct"].between(-38, -8))
                     ].sort_values("gap_pct").head(30)

    print("Generating per-neighborhood talking-point profiles ...")
    profiles = build_profiles(ntable, prem, city, city_land, load_redfin_context())

    # ---- write outputs ----
    ntable.to_csv(os.path.join(PROC, "mls_normalized_neighborhoods.csv"))
    live_out.sort_values("gap_pct").to_csv(os.path.join(PROC, "mls_live_listings_flagged.csv"), index=False)
    df.to_csv(os.path.join(PROC, "mls_clean_all.csv"), index=False)
    pd.DataFrame([{"neighborhood": p["neighborhood"], "headline": p["headline"],
                   "talking_points": " | ".join(p["talking_points"])} for p in profiles]
                 ).to_csv(os.path.join(PROC, "mls_neighborhood_profiles.csv"), index=False)

    bundle = {
        "meta": {
            "source": "Fort Lauderdale MLS agent single-line export (user-provided)",
            "n_listings": int(len(df)),
            "n_sold": int(len(sold)),
            "hedonic_r2": round(float(mod.rsquared), 3),
            "hedonic_n": int(mod.nobs),
            "city_norm_ppsf": round(city, 1),
            "city_land_ppsf": round(city_land, 1),
            "land_lot_elasticity": round(land_elast, 3),
            "standardized_home": {k: (int(v) if k == "sqft" else round(float(v), 1))
                                  for k, v in med.items()},
            "premiums": prem,
            "new_max_age": NEW_MAX_AGE,
            "status_counts": {k: int(v) for k, v in df["status"].value_counts().items()},
            "min_report_sold": MIN_REPORT_SOLD,
        },
        "neighborhoods": json.loads(ntable.reset_index().to_json(orient="records")),
        "profiles": profiles,
        "live_flag_summary": {
            k: int(v) for k, v in live_out["flag"].value_counts().items()},
        "deals": json.loads(deals.to_json(orient="records")),
    }
    with open(os.path.join(PROC, "mls_bundle.json"), "w") as f:
        json.dump(bundle, f, indent=2)
    print(f"  live listings flagged: "
          + ", ".join(f"{k}={v}" for k, v in bundle['live_flag_summary'].items()))
    print("Done. Wrote data/processed/mls_*.{csv,json}")


if __name__ == "__main__":
    main()
