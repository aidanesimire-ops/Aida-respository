#!/usr/bin/env python3
"""
Leasing & yield — the rent side of every neighborhood, and the sell-vs-hold read.

Owners always ask "what would it rent for, and should I sell or hold?" This module
answers it per neighborhood: rent $/sqft, an estimated monthly rent for a typical home,
gross yield (annual rent ÷ price), GRM, and a sell-vs-hold verdict.

If you drop MLS **lease** exports in data/raw/lease/ (List Price = asking rent, Sale Price
= leased rent) it uses those REAL lease comps. With none present it falls back to sourced
Fort Lauderdale rent benchmarks (config.lease_benchmarks) so there's a defensible estimate
today — clearly flagged as an estimate.

Inputs : mls_bundle.json, master_bundle.json, config.lease_benchmarks, optional data/raw/lease
Output : lease_bundle.json
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
import mls_normalize as M
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
LB = CFG.lease_benchmarks
LEASE_DIR = CFG.folder("lease")


def _load(name):
    try:
        with open(os.path.join(PROC, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _real_lease_comps():
    """Per-neighborhood rent $/sqft-yr + median monthly rent from actual leased comps,
    if MLS lease exports are present. Returns {} when there are none."""
    files = glob.glob(os.path.join(LEASE_DIR, "*.csv"))
    if not files:
        return {}, 0
    C = CFG.cols("lease")
    sm = CFG.asset("lease")["status_map"]
    stcol = CFG.asset("lease")["status_column"]
    frames = []
    for f in files:
        try:
            frames.append(pd.read_csv(f))
        except Exception:  # noqa: BLE001
            pass
    if not frames:
        return {}, 0
    raw = pd.concat(frames, ignore_index=True)
    if stcol not in raw.columns:
        return {}, 0
    d = pd.DataFrame({
        "status": raw[stcol].map(sm),
        "neighborhood": raw[C["subdivision"]].map(M._canon_neigh),
        "rent": raw[C["sale_price"]].map(M._num),          # closed monthly rent
        "ask_rent": raw[C["list_price"]].map(M._num),
        "sqft": raw[C["sqft"]].map(M._num),
    })
    leased = d[(d["status"] == "Leased") & d["rent"].gt(0) & d["sqft"].gt(200)].copy()
    leased["rent_psf_yr"] = leased["rent"] * 12 / leased["sqft"]
    leased = leased[leased["rent_psf_yr"].between(5, 400)]   # drop errors
    out = {}
    for nb, g in leased.groupby("neighborhood"):
        if nb and len(g) >= 3:
            out[nb] = {"rent_psf_yr": float(g["rent_psf_yr"].median()),
                       "median_rent": float(g["rent"].median()), "n": int(len(g))}
    return out, int(len(leased))


def _tier_rent_psf(r):
    """Benchmark annual rent $/sqft when we have no lease comps for the neighborhood."""
    t = LB["rent_psf_yr"]
    sold = r.get("sold_ppsf_median") or 0
    wf = (r.get("waterfront_share") or 0) >= 0.4
    if wf and sold >= 1000:
        return t["ultra_waterfront"], "estimate (ultra)"
    if sold >= 500:
        return t["luxury"], "estimate (luxury)"
    return t["standard"], "estimate"


def _verdict(y):
    if y is None:
        return None
    if y >= LB["yield_hold"]:
        return "Rental-supported — holding/renting cash-flows"
    if y < LB["yield_low"]:
        return "Yield-compressed — a sale/appreciation market, not cash-flow (typical of luxury)"
    return "Moderate yield — sell or hold both viable"


def main():
    mls = _load("mls_bundle.json")
    master = _load("master_bundle.json")
    if not mls or not master:
        raise SystemExit("Run the pipeline first (needs mls + master bundles).")
    comps, n_comps = _real_lease_comps()
    by_nb = {n["neighborhood"]: n for n in mls["neighborhoods"]}

    rows = []
    for m in master["neighborhoods"]:
        nb = m["neighborhood"]
        r = by_nb.get(nb)
        if not r:
            continue
        sold_psf = r.get("sold_ppsf_median")
        sqft = r.get("median_sqft")
        if not sold_psf or not sqft:
            continue
        if nb in comps:
            rent_psf, basis = comps[nb]["rent_psf_yr"], f"comp (n={comps[nb]['n']})"
            monthly = comps[nb]["median_rent"]
        else:
            rent_psf, basis = _tier_rent_psf(r)
            monthly = rent_psf * sqft / 12
        gross_yield = 100 * rent_psf / sold_psf if sold_psf else None
        grm = sold_psf / rent_psf if rent_psf else None
        rows.append({
            "neighborhood": nb, "rank": m.get("rank"),
            "median_sqft": int(sqft), "sale_ppsf": round(sold_psf),
            "rent_psf_yr": round(rent_psf, 1), "rent_basis": basis,
            "est_monthly_rent": int(round(monthly, -2)),
            "gross_yield_pct": round(gross_yield, 1) if gross_yield else None,
            "grm": round(grm, 1) if grm else None,
            "verdict": _verdict(gross_yield),
        })
    rows.sort(key=lambda x: (x["rank"] or 999))

    bundle = {
        "meta": {
            "market": CFG.market["name"],
            "has_lease_comps": bool(comps), "n_lease_comps": n_comps,
            "n_neighborhoods": len(rows),
            "city_median_rent": LB["city_median_rent"],
            "house_median_rent": LB["house_median_rent"],
            "city_rent_psf_yr": LB["city_rent_psf_yr"],
            "gross_yield_city_pct": LB["gross_yield_city_pct"],
            "luxury_sf_lease_range": LB["luxury_sf_lease_range"],
            "note": ("Rent figures are REAL lease comps where available (rent_basis = comp); "
                     "otherwise sourced market estimates by tier — directional. Drop MLS lease "
                     "exports in data/raw/lease/ to make every neighborhood comp-backed. "
                     "Luxury yields compress: at the top you sell on lifestyle/appreciation, "
                     "not cash flow."),
        },
        "facts": [
            f"Citywide rent averages about ${LB['city_median_rent']:,}/mo (~${LB['city_rent_psf_yr']}/"
            f"sqft/yr); single-family houses ~${LB['house_median_rent']:,}/mo — a ~{LB['gross_yield_city_pct']}% "
            "gross yield at the median home price.",
            f"Luxury single-family leases run about ${LB['luxury_sf_lease_range'][0]:,}–"
            f"${LB['luxury_sf_lease_range'][1]:,}/mo (4-bed to trophy, often seasonal).",
            "Gross yield compresses sharply in luxury — a $5M+ waterfront home rarely clears "
            "3–4%, so the top end trades on lifestyle, scarcity and appreciation, not cash flow.",
        ],
        "neighborhoods": rows,
    }
    with open(os.path.join(PROC, "lease_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    src = f"{n_comps} lease comps" if comps else "sourced benchmarks (no lease comps yet)"
    print(f"Leasing & yield: {len(rows)} neighborhoods from {src}.")
    for r in rows[:6]:
        print(f"   {r['neighborhood']:20s} ~${r['est_monthly_rent']:>7,}/mo  "
              f"${r['rent_psf_yr']:>4}/sqft/yr  yield {r['gross_yield_pct']}%  "
              f"[{r['rent_basis']}]")


if __name__ == "__main__":
    main()
