#!/usr/bin/env python3
"""
Residential-income (small multifamily) comps for Fort Lauderdale.

A third asset class alongside improved-residential and land. Duplex / triplex /
quad and small apartment buildings trade on **price per unit** and **price per
square foot** — this module builds both, normalized by neighborhood and by unit
tier, plus a live repricing view (active $/unit vs recent closed $/unit).

INPUT  : data/raw/income/*.csv  (RIN "Residential Income" single-line exports)
         status is carried in the "St" column:
           CS=closed sale, PS=pending, A=active, X/C/W/T=expired/cancelled/withdrawn/temp
OUTPUT : data/processed/income_all.csv + data/processed/income_bundle.json

CAVEATS
-------
- The export has NO rent roll / NOI, so cap rate and GRM cannot be computed here —
  they need income figures. This is a *price-comp* layer ($/unit, $/sqft), which is
  how these buildings are screened before you underwrite the rent roll.
- No close dates, so supply is a coarse active:sold ratio, not months-of-supply.
- Small buildings are heterogeneous (condition/renovation unobserved); trust the
  neighborhood + unit-tier medians over any single sale.
"""
from __future__ import annotations
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mls_normalize as M  # reuse _num + neighborhood canonicalization

ROOT = os.path.dirname(HERE)
RAWDIR = os.path.join(ROOT, "data", "raw", "income")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)

ST_GROUP = {"CS": "Sold", "PS": "Pending", "A": "Active", "AC": "Active",
            "X": "Expired", "C": "Cancelled", "W": "Withdrawn", "T": "TempOff"}
FAILED = {"Expired", "Withdrawn", "Cancelled", "TempOff"}
MIN_NBHD_SOLD = 5
THIS_YEAR = 2026
PPU_LO, PPU_HI = 40_000, 3_000_000     # plausible $/unit band
PPSF_LO, PPSF_HI = 60, 2000            # plausible $/sqft band


def _unit_tier(u):
    if pd.isna(u) or u <= 0:
        return None
    u = int(u)
    if u == 2:
        return "Duplex (2)"
    if u == 3:
        return "Triplex (3)"
    if u == 4:
        return "Quadplex (4)"
    return "5+ units"


TIER_ORDER = ["Duplex (2)", "Triplex (3)", "Quadplex (4)", "5+ units"]


def load_clean():
    frames = []
    for path in sorted(glob.glob(os.path.join(RAWDIR, "*.csv"))):
        frames.append(pd.read_csv(path))
    raw = pd.concat(frames, ignore_index=True)
    df = pd.DataFrame({
        "status": raw["St"].map(ST_GROUP),
        "mls": raw["MLS # Link"].astype(str),
        "area": raw["Area"].map(lambda x: str(x).replace(".0", "") if pd.notna(x) else None),
        "address": raw["Address"].astype(str).str.strip(),
        "neighborhood": raw["Subdivision Name"].map(M._canon_neigh),
        "list_price": raw["Current Price"].map(M._num),
        "sale_price": raw["Sale Price"].map(M._num),
        "units": raw["Total Units"].map(M._num),
        "style": raw["Style "].astype(str).str.strip(),
        "sqft": raw["SqFt LA"].map(M._num),
        "year_built": raw["Year Built"].map(M._num),
        "parking": raw["#Parking Spaces"].map(M._num),
        "pool": raw["Pool YN"].astype(str).str.strip().str.lower().eq("yes"),
        "waterfront": raw["Waterfront Property (Y/N)"].astype(str).str.strip().str.lower().eq("yes"),
    })
    df = df[df["status"].notna()].copy()
    # recover missing unit counts from the income style code (I02=2, I03=3, I04=4 ...)
    style_units = df["style"].str.extract(r"I0?(\d+)")[0].astype("float")
    df["units"] = df["units"].where(df["units"].gt(0), style_units)
    df["value"] = np.where(df["status"] == "Sold", df["sale_price"], df["list_price"])
    df["ppu"] = df["value"] / df["units"]
    df["ppsf"] = df["value"] / df["sqft"]
    # $/unit is the primary gate; $/sqft is a secondary metric that's often missing a
    # sqft value, so bound it separately instead of dropping the whole comp.
    df["ppsf_v"] = df["ppsf"].where(df["ppsf"].between(PPSF_LO, PPSF_HI))
    df["tier"] = df["units"].map(_unit_tier)
    yr = df["year_built"].where((df["year_built"] >= 1900) & (df["year_built"] <= THIS_YEAR))
    df["age"] = THIS_YEAR - yr
    return df.reset_index(drop=True)


def _sanitize(o):
    """Recursively replace NaN/inf with None so the bundle is valid JSON."""
    if isinstance(o, float):
        return None if (o != o or o in (float("inf"), float("-inf"))) else o
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o


def _med(s):
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return float(s.median()) if len(s) else None


def _fll_set():
    try:
        with open(os.path.join(PROC, "mls_bundle.json")) as f:
            return {n["neighborhood"] for n in json.load(f)["neighborhoods"]}
    except FileNotFoundError:
        return set()


def main():
    df = load_clean()
    df.to_csv(os.path.join(PROC, "income_all.csv"), index=False)
    fll = _fll_set()

    sold = df[(df["status"] == "Sold") & df["ppu"].between(PPU_LO, PPU_HI)].copy()
    active = df[(df["status"] == "Active") & df["ppu"].between(PPU_LO, PPU_HI)].copy()
    failed = df[df["status"].isin(FAILED)].copy()

    # ---- $/unit + $/sqft by neighborhood ----
    by_nbhd = []
    for nb, g in sold.groupby("neighborhood"):
        if nb is None or len(g) < MIN_NBHD_SOLD:
            continue
        a = active[active["neighborhood"] == nb]
        fa = failed[failed["neighborhood"] == nb]
        ns, na = len(g), len(a)
        sold_ppu, ask_ppu = _med(g["ppu"]), (_med(a["ppu"]) if na else None)
        gap = round(100 * (ask_ppu / sold_ppu - 1)) if (ask_ppu and sold_ppu) else None
        verdict = None
        if gap is not None:
            verdict = "Overpriced" if gap > 8 else "Underpriced" if gap < -8 else "Fairly priced"
        by_nbhd.append({
            "neighborhood": nb, "n_sold": int(ns),
            "ppu": round(sold_ppu) if sold_ppu else None,
            "ppsf": round(_med(g["ppsf_v"])) if _med(g["ppsf_v"]) else None,
            "median_price": _med(g["value"]),
            "median_units": int(_med(g["units"])) if _med(g["units"]) else None,
            "waterfront_share": round(float(g["waterfront"].mean()), 2),
            "n_active": int(na), "active_ppu": round(ask_ppu) if ask_ppu else None,
            "gap_pct": gap, "verdict": verdict,
            "n_failed": int(len(fa)), "in_improved": nb in fll,
        })
    by_nbhd.sort(key=lambda r: -(r["ppu"] or 0))

    # ---- by unit tier ----
    by_tier = []
    for tier, g in sold.groupby("tier"):
        if tier is None or len(g) < 4:
            continue
        by_tier.append({"tier": tier, "n": int(len(g)), "ppu": round(_med(g["ppu"])),
                        "ppsf": round(_med(g["ppsf_v"])), "median_price": _med(g["value"])})
    by_tier.sort(key=lambda r: TIER_ORDER.index(r["tier"]) if r["tier"] in TIER_ORDER else 99)

    # ---- active inventory, repriced vs neighborhood sold $/unit ----
    sold_ppu_by_nb = {nb: _med(g["ppu"]) for nb, g in sold.groupby("neighborhood")
                      if len(g) >= MIN_NBHD_SOLD}
    act = active.copy()
    act["_fll"] = act["neighborhood"].isin(fll)
    act = act.sort_values(["_fll", "value"], ascending=[False, False])
    actives = []
    for _, r in act.head(200).iterrows():
        comp = sold_ppu_by_nb.get(r["neighborhood"])
        supported = comp * r["units"] if (comp and pd.notna(r["units"])) else None
        actives.append({
            "address": r["address"], "neighborhood": r["neighborhood"], "area": r["area"],
            "price": int(r["value"]) if pd.notna(r["value"]) else None,
            "units": int(r["units"]) if pd.notna(r["units"]) else None,
            "sqft": int(r["sqft"]) if pd.notna(r["sqft"]) else None,
            "ppu": round(float(r["ppu"])) if pd.notna(r["ppu"]) else None,
            "ppsf": round(float(r["ppsf"])) if pd.notna(r["ppsf"]) else None,
            "year_built": int(r["year_built"]) if pd.notna(r["year_built"]) else None,
            "waterfront": bool(r["waterfront"]),
            "supported_price": round(supported) if supported else None,
            "gap_pct": round(100 * (r["value"] / supported - 1)) if supported else None,
        })

    n_over = sum(1 for n in by_nbhd if n["verdict"] == "Overpriced")
    n_under = sum(1 for n in by_nbhd if n["verdict"] == "Underpriced")
    bundle = {
        "meta": {
            "n_sold": int(len(sold)), "n_active": int(len(active)),
            "n_failed": int(len(failed)),
            "n_pending": int((df["status"] == "Pending").sum()),
            "n_fll_sold": int(sold["neighborhood"].isin(fll).sum()),
            "median_ppu": round(_med(sold["ppu"])), "median_ppsf": round(_med(sold["ppsf_v"])),
            "waterfront_ppu": round(_med(sold[sold["waterfront"]]["ppu"])) if sold["waterfront"].any() else None,
            "dry_ppu": round(_med(sold[~sold["waterfront"]]["ppu"])) if (~sold["waterfront"]).any() else None,
            "n_neighborhoods": len(by_nbhd),
            "n_over": n_over, "n_under": n_under,
            "note": "Price-comp layer for small multifamily ($/unit, $/sqft). No rent roll "
                    "in the export, so cap rate / GRM need income figures. Mostly Fort "
                    "Lauderdale. No close dates, so supply is a coarse active:sold ratio.",
        },
        "by_neighborhood": by_nbhd,
        "by_tier": by_tier,
        "actives": actives,
    }
    with open(os.path.join(PROC, "income_bundle.json"), "w") as f:
        json.dump(_sanitize(bundle), f, separators=(",", ":"))

    m = bundle["meta"]
    print(f"Income (multifamily): {m['n_sold']} sold ({m['n_fll_sold']} FLL), {m['n_active']} active, "
          f"{m['n_failed']} failed")
    print(f"  Median ${m['median_ppu']:,}/unit · ${m['median_ppsf']}/sqft · "
          f"{m['n_neighborhoods']} neighborhoods ({m['n_over']} over / {m['n_under']} under on ask)")
    for r in by_nbhd[:6]:
        print(f"   {r['neighborhood']:22s} ${r['ppu']:>9,}/unit  ${r['ppsf']:>4}/sqft  "
              f"n={r['n_sold']:<3d}" + (f"  ask {r['gap_pct']:+d}%" if r['gap_pct'] is not None else ""))
    for t in by_tier:
        print(f"   {t['tier']:14s} ${t['ppu']:>9,}/unit  ${t['ppsf']:>4}/sqft  n={t['n']}")


if __name__ == "__main__":
    main()
