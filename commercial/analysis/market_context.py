#!/usr/bin/env python3
"""
External market context — researched benchmarks a Fort Lauderdale commercial broker needs to
sound like the room's expert. Cap rates, rents, sale $/SqFt, construction / rehab / land /
waterfront / insurance costs by asset class, and current submarket realities with real 2024–25
deals. Every figure carries a source and date.

IMPORTANT: these are EXTERNAL market benchmarks from published brokerage/industry research
(2024–2025, some Q1 2026), curated on 2026-07-29. They are the market backdrop to compare your
own data against — not live feeds. Refresh periodically. Numbers are ranges/as-reported; verify
before quoting a specific deal.
"""
from __future__ import annotations

AS_OF = "2024–2025 (some Q1 2026); curated 2026-07-29"

# ---- benchmarks by asset class ------------------------------------------------------------
# fields: cap (range), rent, sale_ppsf, vacancy, trend, sources
ASSET_BENCHMARKS = {
    "Multifamily": {
        "cap": "4.7–5.4% (A ~4.74% · B ~4.92% · C ~5.38%); ~5.6% blended, Yardi ~6.3%",
        "rent": "priced per unit; ~$359,437/unit avg (2025 YTD)",
        "sale_ppsf": "~$300–450/SF on value-add product; per-unit is the metric",
        "vacancy": "~7.9% (buildings 50+ units, Q3 2025)",
        "trend": "Ranked #1 of 30 US markets for MF investment profitability; ~$1.8B annual "
                 "volume; A/B cap compression, C softer. Live Local Act driving density.",
        "sources": ["MIAMI REALTORS/Yardi 2025", "CBRE (Weaver) FLL submarket 2025", "Matthews Q3 2025"],
    },
    "Office": {
        "cap": "~6.75–8.0%",
        "rent": "$41.60/SF full-service overall (record high); Class A $46.74/SF; medical ~$34–36/SF",
        "sale_ppsf": "closed $196–442/SF (Plantation Place ~$196; Las Olas Centre trophy $442)",
        "vacancy": "~12.3% (Broward, Q4 2025)",
        "trend": "Flight-to-quality — post-2010 buildings hold occupancy while the market runs "
                 "negative absorption; record asking rents; medical/healthcare growing.",
        "sources": ["Colliers Q4 2025", "CLS Commercial 2025", "Matthews Q2 2025"],
    },
    "Retail": {
        "cap": "~6.0–6.1%",
        "rent": "$27.59/SF NNN Broward; Fort Lauderdale ~$36/SF; prime Las Olas/Downtown $50–75/SF",
        "sale_ppsf": "closed ~$391/SF (RK Centers, Riverbend, Dec 2025); listings avg ~$630/SF",
        "vacancy": "~3.8–3.9% (very tight)",
        "trend": "Sub-4% vacancy, little new supply, grocery-anchored & infill centers in demand; "
                 "absorption limited by scarce space, not weak demand.",
        "sources": ["Colliers Q4 2025", "Matthews Q4 2025", "The Real Deal Dec 2025"],
    },
    "Industrial": {
        "cap": "~6.0–6.3% (South FL)",
        "rent": "~$16/SF NNN (Fort Lauderdale ~$16.22); small-bay/flex $18–30/SF NNN",
        "sale_ppsf": "~$150–300/SF (well-located Broward warehouse)",
        "vacancy": "~4.0–5.5% (rising on new supply)",
        "trend": "Record pipeline concentrated in Pompano; small-bay/flex tight while big-box "
                 "distribution absorbs slowly.",
        "sources": ["CBRE Q1 2025", "JLL Q1 2025", "Matthews Q2 2025", "Colliers Q1 2026"],
    },
    "Hotel": {
        "cap": "~7.8%",
        "rent": "ADR $129 (summer trough) to ~$240 peak; per key ~$273,831",
        "sale_ppsf": "priced per key (~$274K/key), not per SF",
        "vacancy": "occupancy ~55% (summer) to 72–85% (peak/annual, destination-wide)",
        "trend": "801-room Omni + Whitfield/Auberge underway; beachfront commands a clear ADR "
                 "premium; tourism/TDT revenue near record.",
        "sources": ["Matthews Q3 2025", "Visit Lauderdale/STR 2025–26", "CBRE Hotels 2025"],
    },
    "Mixed Use": {
        "cap": "~6.0–6.75% (blends retail/MF)",
        "rent": "ground-floor retail $27–75/SF NNN + residential above",
        "sale_ppsf": "varies with the residential/retail split",
        "vacancy": "tracks its retail (sub-4%) and MF (~8%) components",
        "trend": "The dominant new-development format downtown (Live Local density bonuses).",
        "sources": ["Colliers/Matthews 2025"],
    },
}

# ---- costs (South Florida; national where noted, + Florida adders) ------------------------
CONSTRUCTION_COST = {  # hard cost $/SqFt
    "Multifamily — garden / wood (1–3 story)": "$170–200/SF",
    "Multifamily — mid-rise podium (5-over-1)": "$200–275/SF",
    "Multifamily — high-rise (concrete tower)": "$400–675/SF",
    "Office": "$200–575/SF (Class A $350–575)",
    "Retail / strip center": "$245–415/SF (standalone store ~$180/SF)",
    "Industrial / warehouse (tilt-up)": "$156–234/SF",
    "Hotel": "$150–250 economy · $250–400 midscale · $400–600+/SF luxury",
}
REHAB_COST = {
    "Multifamily — light reno (paint/floors/fixtures)": "$15,000–25,000/unit",
    "Multifamily — moderate (kitchen/bath/appliances)": "$25,000–45,000/unit",
    "Multifamily — heavy / gut (systems)": "$45,000–65,000+/unit",
    "Office tenant improvement (Miami)": "~$122/SF (Class A $135–150 · Class B $90–120)",
    "Retail tenant improvement": "$40–300/SF (restaurant $200–500/SF)",
}
COST_ADDERS = {
    "Soft costs": "15–30% of hard costs",
    "HVHZ hurricane-code premium (Broward/Miami-Dade)": "+10–15% of construction cost",
    "Builders-risk insurance (during build)": "1–5% of value; coastal within ~1 mi 2–3×",
    "Impact fees (Miami-Dade example)": "~$7,500/MF unit · ~$13/SF commercial",
    "Cost escalation (2025)": "~+4–5.5%/yr (Turner index; RLB Miami +4.7–5.5% YoY)",
}

# ---- land, waterfront, insurance, incentives (filled from research) ----------------------
# (populated below; see LAND section)

# ---- submarket profiles (named neighborhoods) --------------------------------------------
SUBMARKET_PROFILES = {
    "Downtown / Flagler Village": {
        "blurb": "The region's most active development submarket — a former warehouse district now "
                 "dense with high-rise multifamily, creative office and ground-floor retail.",
        "deals": "FAT Village — Hines/Urban Street ~$500M, ~600 units + the region's first "
                 "mass-timber office, topping off 2025, delivery mid-2026. Gallery at Flagler "
                 "Village (263 units) queued. Class A office asking low-$40s/SF.",
        "angle": "Development & land assembly; Live Local density bonuses; office repositioning.",
        "conf": "High",
    },
    "Las Olas": {
        "blurb": "Broward's premier office / CBD address — law, finance and wealth-management tenancy.",
        "deals": "2025 delivered the two largest office trades in a decade: Las Olas Centre I & II "
                 "$208M (~$442/SF, Bradford Allen) and Bank of America Plaza at 401 E Las Olas ~$220M "
                 "(Lone Star/Highline/Square2).",
        "angle": "Trophy office, repositioning, ground-floor retail at $50–75/SF.",
        "conf": "High",
    },
    "17th Street Causeway / Harbor Beach / SE": {
        "blurb": "The marine & yachting-services heart of the market — and increasingly a waterfront "
                 "redevelopment target.",
        "deals": "The Quay (1515 SE 17th) — Related/BH/PEBB bought the ~7-acre waterfront marina/retail "
                 "site for $48.5M (2024) and won approval for a 521-unit tower (40% workforce, Live "
                 "Local). F3 Marina automated drystack completed.",
        "angle": "Waterfront/marina redevelopment; dockage value; Live Local density on the water.",
        "conf": "High",
    },
    "Sistrunk / Progresso / Northwest": {
        "blurb": "A CRA-driven, largely opportunity-zone corridor where public subsidy is catalyzing "
                 "affordable/workforce and mixed-use redevelopment.",
        "deals": "The Aldridge & The Laramore — ~$42M, 72-unit mixed-use with retail at 1204 Sistrunk. "
                 "NPF-CRA plan runs to 2035 with construction/façade incentives.",
        "angle": "Low basis vs downtown; land assembly on the OZ + CRA-incentive angle; Flagler Village "
                 "spillover.",
        "conf": "Med",
    },
    "Victoria Park": {
        "blurb": "A close-in, low-density, high-demand enclave next to downtown and Las Olas — single-"
                 "family and small (5–20 unit) legacy multifamily rather than institutional product.",
        "deals": "Median residential ~$1.05–1.1M (2025); new construction >$3.5M sets the ceiling. "
                 "Boutique value-add MF trades on in-place income + upside.",
        "angle": "Scarcity & location; small value-add multifamily.",
        "conf": "Med",
    },
    "Oakland Park": {
        "blurb": "One of Broward's fastest-emerging urban-infill submarkets, led by public placemaking.",
        "deals": "Culinary Arts District (NE 12th Ave) restaurant/distillery corridor; new City Hall "
                 "mixed-use (2025); 6-acre Horizon redevelopment of the old City Hall site.",
        "angle": "Infill mixed-use, older-industrial repositioning; CRA incentives; attractive basis.",
        "conf": "High",
    },
    "Wilton Manors": {
        "blurb": "A walkable, affluent arts-and-entertainment node (Wilton Drive) drawing its first "
                 "mid-rise projects.",
        "deals": "Stiles bought the Shoppes of Wilton Manors (78,600 SF) for $27.6M (Dec 2024), pursuing "
                 "an 82-unit rezoning; Kaplan's Generation proposes ~190 units.",
        "angle": "Retail redevelopment; constrained supply; strong restaurant/retail demand.",
        "conf": "High",
    },
    "Pompano Beach": {
        "blurb": "The county's highest-volume growth submarket on large sites, anchored by The Pomp "
                 "(Cordish/Caesars ~$2B, 223-acre racetrack redevelopment).",
        "deals": "Land trading briskly: $29.1M for 12.8 acres (423-unit 'Indigo', 2024); Lennar land "
                 "bank $50M for ~20 acres (2025).",
        "angle": "Land/development play; favorable pricing vs downtown; casino/pier tourism; active CRA.",
        "conf": "High",
    },
    "Hollywood": {
        "blurb": "High-momentum multifamily between Miami and Fort Lauderdale with a $1B+ pipeline.",
        "deals": "Soleste Hollywood Blvd (324u), Hollywood Bread Building (361u), 21 Hollywood (200u, "
                 "broke ground Dec 2024). Brightline/transit access.",
        "angle": "Transit-oriented multifamily development; walkability; between-two-metros demand.",
        "conf": "High",
    },
    "Plantation": {
        "blurb": "A West Broward suburban office-and-mixed-use market defined by Plantation Walk.",
        "deals": "Plantation Walk — ~$350M, ~32-acre redevelopment of the former Fashion Mall (Class A "
                 "office + retail + 297-unit final phase, $66.6M construction loan 2025).",
        "angle": "Suburban mixed-use placemaking; office repositioning; I-595/University corporate tenancy.",
        "conf": "High",
    },
    "Lauderhill": {
        "blurb": "A workforce/value submarket along State Road 7 (US-441) — garden multifamily, "
                 "neighborhood retail and small industrial/flex at a lower per-foot basis.",
        "deals": "441 Arthouse (245 units + retail) under construction; listings ~$329/SF, ~$19.5/SF "
                 "asking rent; cap rates at the higher end (C ~5.4%+).",
        "angle": "Yield & value-add on aging stock; SR-7 corridor redevelopment.",
        "conf": "Med",
    },
    "Fort Lauderdale Beach": {
        "blurb": "The barrier-island beach market — hospitality, beachfront retail and boutique "
                 "commercial/condo, where waterfront and ocean views drive a clear premium.",
        "deals": "Hotel product trades ~$274K/key with a beachfront ADR premium; retail/mixed commercial "
                 "along the A1A / Ocean Blvd corridor.",
        "angle": "Hospitality & beachfront retail; premium land; tourism demand.",
        "conf": "Med",
    },
}

# map each MLS area code (submarket in the data) -> named profile + a one-line local note
AREA_TO_PROFILE = {
    "Area 3600": ("17th Street Causeway / Harbor Beach / SE", "17th St Causeway / Harbor Beach — marine & waterfront."),
    "Area 3810": ("Sistrunk / Progresso / Northwest", "NW downtown-adjacent — CRA / opportunity-zone corridor."),
    "Area 3380": ("Wilton Manors", "Middle River / Poinsettia Heights, Wilton Manors edge (NE 13th St)."),
    "Area 3370": ("Oakland Park", "Coral Ridge / Oakland Park corridor (Dixie Hwy · Oakland Park Blvd)."),
    "Area 3500": ("Downtown / Flagler Village", "Downtown-south / Tarpon River (S Andrews corridor)."),
    "Area 3800": ("Downtown / Flagler Village", "Downtown / Rio Vista / SE (Andrews · SE 17th)."),
    "Area 3470": ("Las Olas", "West Las Olas / Tarpon River / Riverside — value vs the CBD trophy blocks."),
    "Area 3460": ("Sistrunk / Progresso / Northwest", "Northwest / Sunrise corridor."),
    "Area 3160": ("Fort Lauderdale Beach", "Central Beach / Ocean Blvd — hospitality & beachfront retail."),
}

# ---- land, waterfront, insurance, incentives ---------------------------------------------
LAND = {
    "Commercial land (small infill)": "~$944/SF (avg parcel ~6,700 SF); ~$4.04M/acre",
    "Downtown per-buildable-unit land": "~$82,000/unit (200 W Broward, 381 units, 2024)",
    "Near-downtown per-unit land": "~$38,000/unit (2125 S Andrews 'The Era', 400 units, 2024)",
    "Flagler Village per-unit land": "~$43,650/unit (Advantis assemblage, 252 units)",
    "Waterfront luxury per-unit land": "~$420,000/unit (900 Intracoastal 'Sage', 44 units, 2024)",
    "Flagler Village land $/SF": "$126–267/land SF (2024 comps)",
    "Stabilized MF (residual-land context)": "2025 YTD $359,437/unit @ $268/SF, ~$2,760/unit rent, 91.7% occ",
}
WATERFRONT = {
    "Waterfront premium": "direct/unobstructed water access sells ~30–50% above comparable dry-lot",
    "Waterfront land": "~$4.84M/acre vs ~$4.04M/acre general commercial",
    "Deep-water value driver": "6 ft+ at mean low tide (8–12 ft for large vessels), NO fixed bridges, point lots = top value",
    "Pricing convention": "per linear foot of frontage, adjusted for depth, bridge clearance, seawall/dock",
    "Seawall cost": "~$500–1,000/linear foot",
    "Marina slip rental": "~$25/ft/month",
    "Marina land comp": "Lauderdale Marine Center (~60 ac) $340M in 2021 ≈ $5.67M/acre",
}
INSURANCE = {
    "MF insurance (Fort Lauderdale)": "~$1,430/unit/yr (+53% YoY, 2024)",
    "FL MF trend": "~$800 → ~$2,000/unit over two years (+150%)",
    "Per SqFt": "$0.50–3.00/SF/yr (condo towers ~$0.23–0.26/SF/month)",
    "Effect on value": "insurance ~7% of opex but ~17% of expense growth since 2019 → compresses NOI, expands caps; FL values −6.8%",
    "Flood (NFIP)": "avg ~$938/yr; Zone AE $300–500K property ~$1,500–3,500/yr; VE = coastal high-hazard; Broward maps updated Jul 2024",
}
INCENTIVES = {
    "Opportunity Zones": "Broward 30 tracts / Fort Lauderdale 10 — prime: Flagler Village, 13th St/Progresso, Sistrunk",
    "NPF-CRA": "Northwest–Progresso–Flagler Heights CRA grant/incentive programs; plan amended 2025",
    "Live Local Act (SB 102)": "by-right MF on commercial/industrial if ≥40% units ≤120% AMI; density = highest in jurisdiction, "
                               "height = highest within 1 mi; 75–100% property-tax exemption on affordable units",
}

SOURCES = [
    ("Multifamily — CBRE (Calum Weaver) Fort Lauderdale submarket report 2024–25",
     "https://mediaassets.cbre.com/-/media/project/cbre/shared-site/teams/united-states/ft-lauderdale/calum-weaver/fort-lauderdale-submarket-report--.pdf"),
    ("Fort Lauderdale #1 MF profitability (Yardi Matrix / MIAMI REALTORS, Oct 2025)",
     "https://www.miamirealtors.com/2025/10/20/fort-lauderdale-ranked-no-1-in-multifamily-investment-profitability/"),
    ("Office & Retail — Colliers Broward Q4 2025", "https://www.colliers.com/en/research/ft-lauderdale/4q25-broward-county-office"),
    ("Retail — Colliers Broward Q4 2025", "https://www.colliers.com/en/research/ft-lauderdale/4q25-broward-county-retail"),
    ("Office/Retail — Matthews Fort Lauderdale reports 2025", "https://www.matthews.com/insights/fort-lauderdale-retail"),
    ("Las Olas Centre $442/SF sale (CRE-Sources, Feb 2025)", "https://cre-sources.com/las-olas-centre-trades-for-442-psf/"),
    ("401 E Las Olas / BofA tower ~$220M (The Real Deal, Feb 2025)", "https://therealdeal.com/miami/2025/02/14/lone-star-funds-highline-square2-buy-fort-lauderdale-tower/"),
    ("The Quay waterfront $48.5M (Commercial Observer, 2024)", "https://commercialobserver.com/2024/05/related-bh-pebb-the-quay/"),
    ("Industrial — CBRE Broward Q1 2025", "https://www.cbre.com/insights/figures/broward-industrial-figures-q1-2025"),
    ("Industrial — JLL Broward Q1 2025", "https://www.jll.com/en-us/insights/market-dynamics/broward-industrial"),
    ("Hotel — Matthews Fort Lauderdale Hospitality Q3 2025", "https://www.matthews.com/insights/fort-lauderdale-fl-hospitality-report-q3-2025"),
    ("Construction cost — RSMeans", "https://www.rsmeans.com/resources/how-much-does-it-cost-to-build-an-apartment-complex"),
    ("Construction escalation — Turner Building Cost Index 2025", "https://www.turnerconstruction.com/insights/turner-building-cost-index-shows-growth-in-q4-2025-amid-strong-data-center-and-manufacturing-demand"),
    ("Construction escalation — RLB North America Q3 2025", "https://www.rlb.com/americas/insight/rlb-construction-cost-report-north-america-q3-2025/"),
    ("Office/retail TI & rehab — Terrapin CG / CommercialCafe 2024–26", "https://www.commercialcafe.com/office-market-trends/us/fl/miami/"),
    ("HVHZ & builders-risk — Bridgeway Insurance 2026", "https://bridgewayins.com/2026/05/05/builders-risk-insurance-florida/"),
    ("Land values — LandSearch Fort Lauderdale", "https://www.landsearch.com/commercial/fort-lauderdale-fl"),
    ("Per-unit land — The Real Deal / bldup 2024", "https://www.bldup.com/posts/development-site-in-downtown-fort-lauderdale-acquired-for-31-24-million"),
    ("Waterfront pricing — Gilles Rais Fine Homes 2026", "https://gillesraisfinehomes.com/blog/how-fort-lauderdales-waterfront-micro-markets-shape-pricing"),
    ("MF insurance — Matthews Florida Multifamily 2024–25", "https://www.matthews.com/insights/rising-multifamily-insurance-costs-in-2025"),
    ("Flood insurance — Harbour Insurance / NerdWallet 2026", "https://harbourinsuranceagency.com/blog/florida-flood-zones-ae-vs-x-vs-ve-insurance-requirements-2026/"),
    ("Opportunity Zones — Greater Fort Lauderdale Alliance", "https://www.gflalliance.org/news/2018/04/20/press-releases/gov.-scott-announces-30-low-tax-opportunity-zone-designations-for-fort-lauderdale-area/"),
    ("Live Local Act — Holland & Knight 2023", "https://www.hklaw.com/en/insights/publications/2023/08/floridas-new-live-local-act-offers-land-use-and-tax-benefits"),
    ("Submarkets — Florida YIMBY / The Real Deal / SFBJ 2024–25", "https://floridayimby.com/2025/10/construction-progresses-on-500-million-fat-village-in-fort-lauderdales-flagler-village.html"),
]


def to_dict():
    """JSON-serializable market context for embedding in the dashboard/Excel."""
    return {
        "as_of": AS_OF,
        "assets": ASSET_BENCHMARKS,
        "construction": CONSTRUCTION_COST,
        "rehab": REHAB_COST,
        "adders": COST_ADDERS,
        "land": LAND,
        "waterfront": WATERFRONT,
        "insurance": INSURANCE,
        "incentives": INCENTIVES,
        "submarket_profiles": SUBMARKET_PROFILES,
        "area_to_profile": {k: {"key": v[0], "note": v[1]} for k, v in AREA_TO_PROFILE.items()},
        "sources": [{"name": n, "url": u} for n, u in SOURCES],
    }


def context_for_area(area_submarket):
    prof_key, note = AREA_TO_PROFILE.get(area_submarket, (None, None))
    prof = SUBMARKET_PROFILES.get(prof_key) if prof_key else None
    return {"profile_key": prof_key, "local_note": note, "profile": prof}


if __name__ == "__main__":
    print(f"Benchmarks as of {AS_OF}")
    for a, b in ASSET_BENCHMARKS.items():
        print(f"  {a:14s} cap {b['cap']}")
    print(f"{len(SUBMARKET_PROFILES)} submarket profiles; {len(AREA_TO_PROFILE)} area mappings")
