#!/usr/bin/env python3
"""
Loader + shared helpers for the commercial (all-asset-class) deal dashboard.

Reads the BeachesMLS / RAPB "Agent Single Line — COM" exports (one row per listing) that
live in data/raw/*.csv, cleans them, classifies asset type and status, and computes the one
hard pricing metric the export actually contains: PRICE PER SQUARE FOOT.

Important: these exports carry NO income data (no NOI, cap rate, rents, occupancy, units).
Everything income-based downstream is therefore built from EDITABLE INDUSTRY-NORM ASSUMPTIONS
(see cre_assumptions.py), so the user can dial rents / vacancy / expense ratios / cap rates and
watch value, implied cap and returns move in real time. The $/sqft layer here is the factual
backbone those assumptions sit on.
"""
from __future__ import annotations
import glob
import os
import re

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAWDIR = os.path.join(ROOT, "data", "raw")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)

THIS_YEAR = 2026
MIN_SQFT = 300
PPSF_LO, PPSF_HI = 20, 2500          # plausible commercial sale $/sqft (drop data errors)
MIN_SEG_SOLD = 5                     # closed sales a segment needs to earn its own model level

# raw MLS status code -> bucket
STATUS_MAP = {
    "CS": "Sold", "PS": "Pending", "AC": "UnderContract", "A": "Active",
    "C": "Cancelled", "X": "Expired", "W": "Withdrawn", "T": "TempOff", "R": "Rented",
}
SOLD = "Sold"
LIVE = ("Active", "Pending", "UnderContract")
FAILED = ("Cancelled", "Expired", "Withdrawn", "TempOff")

# deal-size bands (commercial)
PRICE_BANDS = [
    ("< $1M", 0, 1_000_000),
    ("$1–2.5M", 1_000_000, 2_500_000),
    ("$2.5–5M", 2_500_000, 5_000_000),
    ("$5–10M", 5_000_000, 10_000_000),
    ("$10M+", 10_000_000, float("inf")),
]

ASSET_ORDER = ["Multifamily", "Office", "Retail", "Industrial", "Mixed Use",
               "Hotel", "Restaurant", "Flex", "Special Purpose", "Commercial (other)"]


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


def _asset(type_of_property, style, subtype):
    """Classify from the MLS 'Type of Property' field (the actual asset class). The
    'Style of Property' field only refines the generic 'Commercial' bucket; the noisy
    'Prop Type/Type of Building' list of allowed-uses is deliberately ignored."""
    t = str(type_of_property).lower()
    if "multifamily" in t or "multi-family" in t or "apartment" in t:
        return "Multifamily"
    if "hotel" in t or "motel" in t:
        return "Hotel"
    if "restaurant" in t or "entertainment" in t:
        return "Restaurant"
    if "flex" in t:
        return "Flex"
    if "industrial" in t:
        return "Industrial"
    if "office" in t:
        return "Office"
    if "retail" in t:
        return "Retail"
    if "mixed" in t:
        return "Mixed Use"
    if "special purpose" in t:
        return "Special Purpose"
    # generic "Commercial" or blank -> refine from the cleaner Style field only
    s = str(style).lower()
    if "retail" in s:
        return "Retail"
    if "office" in s:
        return "Office"
    if "industrial" in s:
        return "Industrial"
    if "hotel" in s:
        return "Hotel"
    if "mixed" in s:
        return "Mixed Use"
    return "Commercial (other)"


def _submarket(area):
    if pd.isna(area):
        return "Unknown"
    a = re.sub(r"\.0$", "", str(area)).strip()
    if not a:
        return "Unknown"
    return f"Area {a}"


def _is_lease(prop_type):
    return "lease" in str(prop_type).lower()


def _units_from_address(addr):
    """Recover a whole-building unit count from a 'Unit#1-28' style range in the address."""
    if pd.isna(addr):
        return np.nan
    m = re.search(r"unit\s*#?\s*(\d+)\s*[-–]\s*(\d+)", str(addr), re.I)
    if m:
        lo, hi = int(m.group(1)), int(m.group(2))
        if hi > lo and (hi - lo + 1) <= 400:
            return float(hi - lo + 1)
    return np.nan


def _lease_rate_psf(price, sqft):
    """Normalize a messy lease 'price' to an annual $/SqFt rate, inferring the rate basis."""
    if pd.isna(price) or pd.isna(sqft) or sqft < MIN_SQFT or price <= 0:
        return np.nan
    if price <= 100:                       # already quoted as $/SqFt/yr
        r = price
    else:
        annual_total = price / sqft        # price is a full annual rent
        monthly_total = price * 12 / sqft  # price is a monthly rent
        if 4 <= annual_total <= 120:
            r = annual_total
        elif 4 <= monthly_total <= 120:
            r = monthly_total
        else:
            return np.nan
    return r if 3 <= r <= 200 else np.nan


def market_rents(df: pd.DataFrame, min_n: int = 4):
    """Median asking lease rate ($/SqFt/yr) by asset type (and type×submarket) from the
    lease listings — turns assumed rents into data-derived market rents where we have comps."""
    lease = df[df["deal_kind"].eq("Lease") & df["lease_rate_psf"].notna()]
    by_type = {}
    for at, g in lease.groupby("asset_type"):
        if len(g) >= min_n:
            by_type[at] = {"rate": round(float(g["lease_rate_psf"].median()), 1), "n": int(len(g))}
    return by_type, int(len(lease))


def load_clean() -> pd.DataFrame:
    files = sorted(glob.glob(os.path.join(RAWDIR, "*.csv")))
    frames = []
    for p in files:
        d = pd.read_csv(p, dtype=str)
        if "St" not in d.columns or "Type of Property" not in d.columns:
            continue
        d["__src"] = os.path.basename(p)
        frames.append(d)
    if not frames:
        raise FileNotFoundError(f"No commercial MLS CSVs found in {RAWDIR}")
    raw = pd.concat(frames, ignore_index=True)

    df = pd.DataFrame({
        "mls": raw["MLS # Link"].astype(str).str.strip(),
        "status": raw["St"].astype(str).str.strip().str.upper().map(STATUS_MAP),
        "deal_kind": np.where(raw["Prop Type"].map(_is_lease), "Lease", "Sale"),
        "submarket": raw["Area"].map(_submarket),
        "area_code": raw["Area"].astype(str).str.replace(r"\.0$", "", regex=True).str.strip(),
        "address": raw["Address"].astype(str).str.strip(),
        "asset_type": [_asset(a, b, c) for a, b, c in zip(
            raw["Type of Property"], raw.get("Style of Property", pd.Series(index=raw.index)),
            raw.get("Prop Type/Type of Building", pd.Series(index=raw.index)))],
        "zoning": raw["ZN"].astype(str).str.replace("¤", "", regex=False).str.strip(),
        "year_built": raw["Year Built"].map(_num),
        "current_price": raw["Current Price"].map(_num),
        "sale_price": raw["Sale Price"].map(_num),
        "sqft": raw["Property SqFt"].map(_num),
        "waterfront": raw["Waterfront Property (Y/N)"].astype(str).str.strip().str.lower().eq("yes"),
        "bays": raw["#Bays"].map(_num),
        "source_file": raw["__src"],
    })
    df["status"] = df["status"].fillna("Active")
    # deal price: final sale for closed, else current/asking
    df["price"] = np.where(df["status"].eq(SOLD) & df["sale_price"].notna(),
                           df["sale_price"], df["current_price"])
    df["price"] = df["price"].fillna(df["sale_price"]).fillna(df["current_price"])
    yb = df["year_built"].where(df["year_built"].between(1850, THIS_YEAR))
    df["year_built"] = yb
    df["age"] = THIS_YEAR - yb
    df["ppsf"] = df["price"] / df["sqft"]
    df["units"] = raw["Address"].map(_units_from_address)
    df["price_per_unit"] = np.where(df["units"].gt(0), df["price"] / df["units"], np.nan)
    df["lease_rate_psf"] = [_lease_rate_psf(p, s) if k == "Lease" else np.nan
                            for p, s, k in zip(df["current_price"], df["sqft"], df["deal_kind"])]

    # dedupe exact MLS duplicates (same listing across pulls), keep the most-progressed status
    prio = {"Sold": 0, "UnderContract": 1, "Pending": 2, "Active": 3, "Rented": 4,
            "Cancelled": 5, "Expired": 6, "Withdrawn": 7, "TempOff": 8}
    df["_prio"] = df["status"].map(prio).fillna(9)
    df = df.sort_values("_prio").drop_duplicates(subset=["mls"], keep="first").drop(columns="_prio")

    df.attrs["n_raw"] = int(len(raw))
    return df.reset_index(drop=True)


def sales(df: pd.DataFrame) -> pd.DataFrame:
    """Clean SALE rows valid for $/sqft analysis."""
    s = df[df["deal_kind"].eq("Sale") & df["sqft"].gt(MIN_SQFT) & df["price"].gt(0)].copy()
    s = s[s["ppsf"].between(PPSF_LO, PPSF_HI)]
    return s.reset_index(drop=True)


def big_segments(s: pd.DataFrame, col: str, min_n: int = MIN_SEG_SOLD) -> set:
    sold = s[s["status"].eq(SOLD)]
    vc = sold[col].value_counts()
    return set(vc[vc >= min_n].index)


def price_band(p):
    if pd.isna(p):
        return None
    for label, lo, hi in PRICE_BANDS:
        if lo <= p < hi:
            return label
    return PRICE_BANDS[-1][0]


# major Fort Lauderdale corridors -> canonical label (keyword matched against addresses)
CORRIDORS = {
    "federal": "Federal Hwy", "andrews": "Andrews Ave", "oakland park": "Oakland Park Blvd",
    "las olas": "Las Olas Blvd", "sunrise": "Sunrise Blvd", "broward": "Broward Blvd",
    "commercial blvd": "Commercial Blvd", "dixie": "Dixie Hwy", "state road 84": "SR-84",
    "powerline": "Powerline Rd", "davie": "Davie Blvd", "17th": "SE 17th St",
    "sistrunk": "Sistrunk Blvd", "wilton": "Wilton Dr", "ocean": "Ocean Blvd",
    "miami road": "Miami Rd", "bayview": "Bayview Dr", "cordova": "Cordova Rd",
}


def corridor_hint(addresses, top=2):
    """The dominant street corridors in a set of addresses — turns an MLS area code into a
    place a broker recognizes."""
    import collections
    c = collections.Counter()
    for a in addresses:
        s = str(a).lower()
        for kw, lab in CORRIDORS.items():
            if kw in s:
                c[lab] += 1
    return " · ".join(lab for lab, _ in c.most_common(top))


def usd(x):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if pd.isna(x):
        return "—"
    a = abs(x)
    if a >= 1e9:
        return f"${x/1e9:.2f}B"
    if a >= 1e6:
        return f"${x/1e6:.2f}M"
    if a >= 1e3:
        return f"${x/1e3:.0f}K"
    return f"${x:,.0f}"


if __name__ == "__main__":
    df = load_clean()
    s = sales(df)
    print(f"{len(df):,} listings ({df.attrs['n_raw']} raw rows) | "
          f"Sale={int(df['deal_kind'].eq('Sale').sum())} Lease={int(df['deal_kind'].eq('Lease').sum())}")
    print("status:", ", ".join(f"{k}={v}" for k, v in df["status"].value_counts().items()))
    print("asset types:", ", ".join(f"{k}={v}" for k, v in df["asset_type"].value_counts().items()))
    print(f"\nvalid SALE comps: {len(s)} | closed: {int(s['status'].eq(SOLD).sum())}")
    print("median $/sqft by asset type (sales):")
    print(s.groupby("asset_type")["ppsf"].median().round(0).sort_values(ascending=False))
