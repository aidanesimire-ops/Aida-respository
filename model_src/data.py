"""
data.py — all verified facts, assumptions, and market research figures.
Single source of truth for the model build. Edit here, rebuild.

Confidence flags:
  V  = VERIFIED  (BCPA / Sunbiz / recorded deed — public record)
  R  = REPORTED  (counterparty / press, unconfirmed)
  M  = MODELED   (assumption; moves with inputs)
  E  = ESTIMATED (market research triangulation)
"""

# ============================================================ VERIFIED PARCEL FACTS
PARCELS = {
    "shahidi": dict(
        name="Shahidi Retail Center",
        addr="2541–2595 E Sunrise Blvd, Fort Lauderdale, FL 33304",
        folio="49-42-36-12-0070",
        owner="SHAWNICK GALLERIA LLC",
        principal="Esmail Shahidi (mgr) — Sunbiz L21000389291",
        gla=26272, land_sf=67080, land_ac=1.540,
        year_built="1960 (eff. 1980)",
        zoning="B-1 (Boulevard Business) / FEMA AE",
        last_sale_date="11/09/2021", last_sale=17100000,
        tax_2024=152766, tax_2025=162366,
        just_2026=8911690, millage=0.0191,
        basis_land=254.92, basis_bldg=650.88,
        occ=0.8317,
    ),
    "publix": dict(
        name="Publix + Starbucks",
        addr="2501–2519 E Sunrise Blvd, Fort Lauderdale, FL 33304",
        folio="49-42-36-12-0060",
        owner="REAL SUB LLC (Publix real-estate entity, Lakeland FL)",
        principal="Publix Super Markets — fee owner (NOT a seller)",
        gla=36822, land_sf=109791, land_ac=2.520,
        year_built="2011 (eff. 2012)",
        zoning="B-1 (Boulevard Business) / FEMA AE",
        last_sale_date="03/14/2025", last_sale=25000000,
        tax_2024=217404, tax_2025=208467,
        just_2026=None, millage=0.0191,
        basis_land=227.75, basis_bldg=678.94,
        occ=1.00,
    ),
}

# combined block A + B (verified)
COMBINED = dict(land_sf=176871, land_ac=4.060, bldg_sf=63094)

# ============================================================ SHAHIDI ASSUMPTIONS (BuildSpec §6)
SH = dict(
    # property
    gla=26272, occ0=0.8317, land_sf=67080, millage=0.0191,
    # revenue
    base_rent=55.00, market_rent=55.00, rent_growth=0.03,
    stab_occ=0.95, credit_loss=0.02,
    # opex
    reassessed=17100000, insurance=65000, cam=55000, rm=40000,
    mgmt_pct=0.04, exp_growth=0.03,
    # capital
    ti_psf=30.00, lc_psf=20.00, reserve_psf=0.15, rollover_psf=0.75,
    # acq / debt
    price=17100000, closing_pct=0.025, ltv=0.65, loan_rate=0.0675, amort=30,
    # valuation / hold
    goingin_cap=0.060, exit_cap=0.060, cost_sale=0.02, hold=5,
)

# ============================================================ MARKET RESEARCH (agent-verified, mid-2026)
MKT = dict(
    # Publix (fee-owned -> mark-to-market hypothetical)
    publix_rent_psf=13.00,          # E  $12-14/SF NNN newer store
    publix_pct_rent=0.010,          # E  1% over breakpoint
    publix_cap=0.0600,              # V  grocery-anchored 6.0-6.75%; ST Publix 5.5-6.0%
    publix_exit_cap=0.0625,
    # Starbucks pad
    sbux_sf=2200,                   # E  drive-thru pad
    sbux_rent_psf=60.00,            # E  ~$60/SF NNN
    sbux_cap=0.0520,                # V  4.75-5.5%, median ~5.2%
    sbux_exit_cap=0.0550,
    # in-line retail (Fort Lauderdale / Sunrise Blvd)
    retail_inline_rent=36.00,       # V  $32-40/SF NNN
    retail_restaurant_rent=45.00,   # V  $40-50/SF NNN
    strip_cap_stab=0.0650,          # V  6.25-6.75%
    strip_cap_valueadd=0.0750,      # V/E 7.25-8.0%
    # office (small Class B/C)
    office_rent_nnn=20.00,          # V  $15-24/SF NNN base
    office_rent_gross=27.00,        # V  ~$20-30 gross
    office_cap=0.0800,              # E  7.5-9.0%
    office_sale_psf=200.00,         # V  $150-250/SF small B/C condo
    # land / covered land play
    land_psf_infill=248.00,         # V  FTL median ~$248/SF; subject $228-255
    land_psf_bulk=53.00,            # V  Galleria bulk 31.5 ac
    covered_land_cap=0.045,         # E  in-place income cap ~3-5% on covered land plays
    # debt (mid-2026)
    debt_rate_stab=0.0650,          # V  5.75-7.0%
    debt_rate_valueadd=0.0900,      # E  SOFR+275-400
    ltv_stab=0.65, dscr_min=1.30, debt_yield_min=0.08,
)

# ============================================================ ASSEMBLAGE STRUCTURE
ASSEMBLAGE = dict(
    premium_low=0.15, premium_base=0.20, premium_high=0.25,
    hold=5,
)

# LP / GP waterfall defaults (skill standard)
WF = dict(
    lp_equity=0.90, gp_equity=0.10, pref=0.08, above_lp=0.70, above_gp=0.30,
)
