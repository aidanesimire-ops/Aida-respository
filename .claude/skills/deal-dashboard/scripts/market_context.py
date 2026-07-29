#!/usr/bin/env python3
"""
Market context — the costs & realities behind the price, per neighborhood.

Ultra-luxury sellers and buyers think in REPLACEMENT COST: what would it take to
reproduce this home — land + construction + soft costs — versus what finished product
trades for? This module fuses the user's own comps (resale $/sqft, land $/sqft, lot &
home size) with sourced construction / rehab / waterfront / insurance benchmarks (from
config.costs; see docs/MARKET_REALITIES.md) to compute a build-vs-buy read for every
neighborhood, and packages the market facts an agent should be able to speak to.

Inputs : mls_bundle.json, land_bundle.json, master_bundle.json, config.costs
Output : context_bundle.json  (dashboard "Costs & realities" card + Excel tab + marketing)

NOTE: the cost figures are external market ESTIMATES, not from the MLS data. They are
configurable and sourced; treat build-vs-buy as directional, not a bid.
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
C = CFG.costs
SOFT = 1 + C["soft_cost_pct"] / 100.0


def _load(name):
    try:
        with open(os.path.join(PROC, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _usd(v):
    return f"${v:,.0f}" if v is not None else "—"


def _actual_land():
    lb = _load("land_bundle.json")
    if not lb:
        return {}
    return {r["neighborhood"]: r["land_ppsf"] for r in lb.get("by_neighborhood", [])
            if r.get("in_improved") and (r.get("n_sold") or 0) >= 3 and r.get("land_ppsf")}


def build_vs_buy(r, land_actual):
    """Replacement-cost economics for one neighborhood."""
    sqft = r.get("median_sqft")
    if not sqft or sqft <= 0:
        return None
    # replacement cost is a land/house concept — skip condo-dominant neighborhoods
    if (r.get("n_condo") or 0) > (r.get("n_house") or 0):
        return None
    wf_heavy = (r.get("waterfront_share") or 0) >= 0.4
    # compare build cost to FINISHED-NEW resale where we have it (apples-to-apples),
    # else waterfront resale for waterfront areas, else the overall median
    if r.get("new_ppsf") and (r.get("new_n") or 0) >= 3:
        resale_psf, resale_basis = r["new_ppsf"], "new construction"
    elif wf_heavy and r.get("waterfront_ppsf"):
        resale_psf, resale_basis = r["waterfront_ppsf"], "waterfront"
    else:
        resale_psf, resale_basis = r.get("sold_ppsf_median"), "overall"
    if not resale_psf:
        return None
    nb = r["neighborhood"]
    land_ppsf = land_actual.get(nb) or r.get("implied_land_ppsf")
    land_basis = "comp" if nb in land_actual else "implied"
    lot = r.get("median_lot_sqft") or 0
    land_val = (land_ppsf or 0) * lot
    land_per_home_psf = land_val / sqft if sqft else 0

    cp = C["construction_psf"]
    tiers = {k: v * SOFT + land_per_home_psf for k, v in cp.items()}  # all-in $/sqft to reproduce
    lo, typ, hi = tiers["luxury"], tiers["high_end"], tiers["ultra_waterfront"]
    # pick the tier a home HERE would most likely be built to
    point = hi if wf_heavy and resale_psf >= 800 else typ if resale_psf >= 450 else lo
    prem = (resale_psf / point - 1) * 100 if point else None

    if prem is not None and prem >= 10:
        verdict = "Above replacement — new construction is highly profitable (spec-builder territory)"
    elif prem is not None and prem <= -15:
        verdict = "Below replacement — often cheaper to buy finished than to build"
    else:
        verdict = "Near replacement cost — build-vs-buy is roughly a wash"

    build_total_lo = (cp["luxury"] * SOFT * sqft) + land_val
    build_total_hi = (cp["ultra_waterfront"] * SOFT * sqft) + land_val

    tps = []
    tps.append(
        f"Reproducing a typical ~{sqft:,.0f} sqft home here runs about "
        f"{_usd(cp['luxury'])}–{_usd(cp['ultra_waterfront'])}/sqft to build "
        f"(+~{C['soft_cost_pct']}% soft costs), plus land at ~{_usd(land_ppsf)}/sqft of lot "
        f"(~{_usd(land_val)} on a {lot:,.0f} sqft lot) — roughly {_usd(build_total_lo)}–"
        f"{_usd(build_total_hi)} all-in.")
    tps.append(
        f"That's about {_usd(point)}/sqft to replace vs {_usd(resale_psf)}/sqft resale, so "
        f"finished product trades ~{abs(prem):.0f}% {'above' if prem >= 0 else 'below'} "
        f"replacement cost. {verdict.split('—')[1].strip().capitalize()}.")
    if wf_heavy:
        tps.append(
            "Waterfront is priced per linear foot of frontage off same-waterbody comps — "
            "depth, no-fixed-bridges ocean access and dockage move it more than interior sqft. "
            f"A new seawall runs {_usd(C['seawall_psf_lf'][0])}–{_usd(C['seawall_psf_lf'][1])}/"
            "linear foot and a dock " + f"{_usd(C['dock_build'][0])}–{_usd(C['dock_build'][1])}.")

    return {"neighborhood": nb, "median_sqft": int(sqft),
            "resale_psf": round(resale_psf), "resale_basis": resale_basis,
            "land_ppsf": round(land_ppsf) if land_ppsf else None, "land_basis": land_basis,
            "land_val": int(round(land_val, -3)) if land_val else None,
            "replacement_psf_lo": round(lo), "replacement_psf_typ": round(point),
            "replacement_psf_hi": round(hi),
            "build_total_lo": int(round(build_total_lo, -3)),
            "build_total_hi": int(round(build_total_hi, -3)),
            "premium_to_replacement_pct": round(prem) if prem is not None else None,
            "verdict": verdict, "talking_points": tps}


SOURCES = [
    {"label": "Sabal Luxury Builder — Miami luxury cost/sqft (2026)",
     "url": "https://sabalbuilder.com/en/journal/luxury-home-construction-cost-per-square-foot-miami"},
    {"label": "Tri-Town Construction — Fort Lauderdale build & renovation costs (2025)",
     "url": "https://www.tri-townconstruction.com/blog/cost-to-build-home-fort-lauderdale-2025/"},
    {"label": "Seanote Construction — Cost to build a house in Florida (2026)",
     "url": "https://seanotefl.com/cost-to-build-a-house-in-florida/"},
    {"label": "Ginger Luxe Real Estate — Fort Lauderdale waterfront pricing guide",
     "url": "https://gingerluxereal.com/blog/pricing-waterfront-homes-in-fort-lauderdale"},
    {"label": "Souffront / Sea Me Dive — South Florida seawall cost (2025)",
     "url": "https://seamedive.net/how-much-does-a-seawall-cost-in-south-florida/"},
    {"label": "Crocker Marine — dock construction cost guide (2025)",
     "url": "https://crockermarine.com/blog/complete-dock-construction-cost-guide-for-southwest-florida/"},
    {"label": "Josh Dotoli Group — Fort Lauderdale waterfront insurance costs",
     "url": "https://joshdotoligroup.com/blog/insurance-costs-for-waterfront-homes-in-fort-lauderdale/"},
    {"label": "MillionLuxury — South Florida ultra-luxury market (2025)",
     "url": "https://www.millionluxury.com/news/south-florida-luxury-real-estate-market-september-2025-report"},
    {"label": "The Real Deal — Fort Lauderdale luxury market (2025-26)",
     "url": "https://therealdeal.com/miami/2026/05/13/fort-lauderdales-luxury-market-regains-momentum/"},
]


def main():
    mls = _load("mls_bundle.json")
    master = _load("master_bundle.json")
    if not mls or not master:
        raise SystemExit("Run the pipeline first (needs mls + master bundles).")
    land_actual = _actual_land()
    by_nb = {n["neighborhood"]: n for n in mls["neighborhoods"]}

    ctx = []
    for m in master["neighborhoods"]:
        r = by_nb.get(m["neighborhood"])
        if not r:
            continue
        bvb = build_vs_buy(r, land_actual)
        if bvb:
            bvb["rank"] = m.get("rank")
            ctx.append(bvb)

    cp, rp = C["construction_psf"], C["rehab_psf"]
    benchmarks = {
        "construction": [
            {"tier": "Luxury custom", "psf": cp["luxury"]},
            {"tier": "High-end custom", "psf": cp["high_end"]},
            {"tier": "Ultra-premium waterfront", "psf": cp["ultra_waterfront"]},
        ],
        "construction_range": C["construction_range_psf"],
        "rehab": [{"tier": "High-end gut reno", "psf": rp["high_end"]},
                  {"tier": "Ultra-luxury reno", "psf": rp["ultra"]}],
        "soft_cost_pct": C["soft_cost_pct"],
        "seawall_psf_lf": C["seawall_psf_lf"], "dock_build": C["dock_build"],
        "boatlift_per_1000lb": C["boatlift_per_1000lb"],
        "insurance_annual": C["insurance_annual"],
    }
    market_facts = [
        {"fact": f"New luxury custom construction runs about ${cp['luxury']:,}–${cp['high_end']:,}/sqft "
                 f"in South Florida; ultra-premium waterfront exceeds ${cp['ultra_waterfront']:,}–$2,000/sqft "
                 f"(hard cost; add ~{C['soft_cost_pct']}% soft costs).", "src": "Sabal / Seanote"},
        {"fact": f"High-end gut renovation runs about ${rp['high_end']:,}–${rp['ultra']:,}+/sqft.",
         "src": "Tri-Town / Sweeten"},
        {"fact": "Waterfront is priced per linear foot of frontage from same-waterbody comps — "
                 "depth, bridge clearance (no fixed bridges = ocean access) and exposure drive it "
                 "more than interior square footage.", "src": "Ginger Luxe"},
        {"fact": f"Seawall replacement runs ${C['seawall_psf_lf'][0]:,}–${C['seawall_psf_lf'][1]:,}/"
                 f"linear foot; a new dock ${C['dock_build'][0]:,}–${C['dock_build'][1]:,}; a boat lift "
                 f"about $1/lb (a 24,000-lb lift ≈ $38k).", "src": "Sea Me Dive / Crocker Marine"},
        {"fact": f"Insurance/carrying on luxury waterfront: canal ${C['insurance_annual']['canal'][0]:,}–"
                 f"${C['insurance_annual']['canal'][1]:,}/yr, Intracoastal ${C['insurance_annual']['intracoastal'][0]:,}–"
                 f"${C['insurance_annual']['intracoastal'][1]:,}, oceanfront ${C['insurance_annual']['oceanfront'][0]:,}–"
                 f"${C['insurance_annual']['oceanfront'][1]:,}+.", "src": "Josh Dotoli Group"},
        {"fact": "Ultra-luxury is deep: 361 South Florida homes sold above $10M in 2025 — the 2nd-highest "
                 "year ever (2021 = 444) — Broward logged its first $70M sale, and the market now trades "
                 "$20M–$50M+.", "src": "MillionLuxury / The Real Deal"},
        {"fact": "Broadly Fort Lauderdale ran a buyer's market in 2025 (~9.8 months of inventory); "
                 "the top end still moves on scarcity of finished waterfront product and cash / "
                 "international demand.", "src": "The Real Deal"},
    ]

    bundle = {
        "meta": {"market": CFG.market["name"], "n_neighborhoods": len(ctx),
                 "soft_cost_pct": C["soft_cost_pct"],
                 "note": "Build-vs-buy fuses your comps with sourced construction/land/waterfront "
                         "cost benchmarks (config.costs). Costs are external market estimates — "
                         "directional, not a bid. Sources in docs/MARKET_REALITIES.md."},
        "benchmarks": benchmarks,
        "market_facts": market_facts,
        "sources": SOURCES,
        "neighborhoods": ctx,
    }
    with open(os.path.join(PROC, "context_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"Market context: build-vs-buy for {len(ctx)} neighborhoods, "
          f"{len(market_facts)} market facts, {len(SOURCES)} sources.")
    for b in sorted(ctx, key=lambda x: (x["rank"] or 999))[:5]:
        print(f"   {b['neighborhood']:20s} resale ${b['resale_psf']:>4}/sqft vs replace "
              f"${b['replacement_psf_typ']:>4}/sqft → {b['premium_to_replacement_pct']:+d}% "
              f"({b['verdict'].split('—')[0].strip()})")


if __name__ == "__main__":
    main()
