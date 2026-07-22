"""
configs.py — per-asset config dicts for the generic income-asset builder.
"""

# =============================================================== PUBLIX + STARBUCKS
PUBLIX_CFG = dict(
    title="PUBLIX + STARBUCKS  ·  SALE-LEASEBACK  (acquire fee, lease back during entitlement)",
    subtitle="2501–2519 E Sunrise Blvd   |   Folio 49-42-36-12-0060   |   REAL SUB LLC (Publix) "
             "· 36,822 SF · built 2011 · acquire the fee → Publix leases back → rent covers carry while you entitle the land",
    facts_header="PROPERTY FACTS  —  ✅ BCPA / 🔶 SALE-LEASEBACK STRUCTURE (leaseback terms on the Assumptions tab)",
    facts=[
        ("Record owner (today)", "REAL SUB LLC (Publix Super Markets real-estate entity, Lakeland FL) — fee owner", True),
        ("Deal structure", "Sale-leaseback: DAWN RE acquires the fee; Publix leases back and pays rent during the entitlement period, then vacates for redevelopment", False),
        ("Building", "36,822 SF (Publix ~34,622 SF leaseback + Starbucks drive-thru pad ~2,200 SF)", True),
        ("Land", "109,791 SF  (2.520 ac)", True),
        ("Year built", "2011 (eff. 2012)", True),
        ("Last sale", "03/14/2025  —  $25,000,000  (Trustee's Deed)  =  $679/SF bldg · $228/SF land", True),
        ("2025 real-estate taxes", "$208,467   (2024: $217,404) — NNN, reimbursed by Publix during leaseback", True),
        ("Leaseback economics", "Publix leaseback ~$22/SF NNN (bridge rate) + Starbucks pad ~$60/SF NNN; ~4-yr term (adjustable on Assumptions tab)", False),
        ("Covered-land logic", "The leaseback rent covers the operating carry (Publix pays taxes/ins NNN) while the land is entitled; the play is the dirt, not the current yield", False),
        ("Standalone return (below)", "NEGATIVE on a pure income basis by design — you pay land value ($25M) for income supporting only ~$13M. The return is the LAND, realized via the assemblage / redevelopment; the leaseback (DSCR ≈ 1.0x) simply covers the entitlement carry", False),
    ],
    lease_header="RENT ROLL  —  🔶 sale-leaseback terms (set on the Assumptions tab · Publix block)",
    leases=[
        ("Publix (sale-leaseback)", "Grocery anchor (credit) — leases back during entitlement", 34622, 22.00, "leaseback NNN; terms on Assumptions tab"),
        ("Starbucks (drive-thru pad)", "QSR pad (credit)", 2200, 60.00, "pad NNN; terms on Assumptions tab"),
    ],
    vacant_sf=0,
    lease_note="100% occ · credit tenants · sale-leaseback",
    land_psf=227.75,   # Publix's actual land basis -> land value ties to $25M
    mrent_from_slb=True,   # blended rent computed from Publix leaseback + Starbucks pad (Assumptions tab)
    slb_term=True,         # leaseback income cliffs at the entitlement term
    exit_land=True,        # covered-land exit: reversion at land value, not income cap
    slb_solver=True,       # add the leaseback-rent solver (target DSCR / cap)
    src=dict(
        gla="✅ BCPA (36,822 SF)", occ0="✅ fully occupied", stab_occ="🔶",
        rent="🔶 leaseback + pad", mill="✅ 2025",
        price="🔶 SLB acquisition price (fee) — negotiated ≈ $25M basis",
        cap="🔶 grocery-anchored 6.0% (reference)", exit="🔶 6.25%",
    ),
    inp=dict(
        gla=36822, occ0=1.00, stab_occ=1.00,
        market_rent=24.27,               # fallback blended (leaseback+pad); real value computed on tab
        rent_growth=0.02, credit_loss=0.01, millage=0.0191,
        insurance=45000, cam=35000, rm=25000, mgmt_pct=0.02, exp_growth=0.03,
        ti_psf=0.00, lc_psf=0.00, reserve_psf=0.15, rollover_psf=0.15,
        price=25000000,                  # SLB acquisition price (fee, ≈ Publix basis)
        closing_pct=0.02, ltv=0.45, loan_rate=0.0625, amort=30,
        goingin_cap=0.060, exit_cap=0.0625, cost_sale=0.02, hold=5, disc=0.07,
        land_sf=109791,
        # sale-leaseback terms (hypothetical — Publix is a fee owner, not a seller)
        slb_rent=22.00, slb_sf=34622, sbux_rent=60.00, sbux_sf=2200, term=4,
    ),
)

# =============================================================== SUNRISE PLAZA (Kar Luen)
KARLUEN_CFG = dict(
    title="SUNRISE PLAZA  ·  ADJACENT RETAIL CENTER  (2465–2485, incl. 2473)",
    subtitle="2465–2485 E Sunrise Blvd   |   Folio 49-42-36-12-0011   |   Kar Luen Inc "
             "· 25,105 SF · built 1962 (remod. 1987) · SEPARATE parcel from the 2455 office condo · restaurant/jeweler value-add",
    facts_header="PROPERTY FACTS  —  ⚠️ REPORTED (BCPA blocked in build env; LoopNet/Sunbiz sourced)",
    facts=[
        ("Record owner", "Kar Luen Inc  (FL corp est. 1994; registered at 2465 E Sunrise)", False),
        ("Parcel scope", "2465 / 2473 / 2485 E Sunrise — one folio (-0011); DISTINCT from the 2455 office condo (its own tab)", False),
        ("Building", "25,105 SF, 2-story retail/commercial", False),
        ("Land", "0.71 ac  ≈  30,928 SF", False),
        ("Year built", "1962 (remodeled 1987)", False),
        ("Zoning", "Community Business (CB) / B-1 corridor", False),
        ("Anchor tenant", "Daoud's Fine Jewelry — 100+ yr family jeweler at 2473 (~6,000 SF)", False),
        ("Reported value", "≈ $8.5M  (UNVERIFIED — no recent arm's-length sale)", False),
        ("Last recorded sale", "Oct 2000 — $128,000 (stale/partial; not a value indicator)", False),
    ],
    lease_header="RENT ROLL (2465–2485 E Sunrise, incl. 2473)  —  🔶 tenants REPORTED (Yelp/LoopNet); suite SF & rents estimated",
    leases=[
        ("2473 · Daoud's Fine Jewelry", "Retail – jeweler (anchor)", 6000, 34.00, "100+ yr family business"),
        ("2465 · Sunness Supper Club", "Restaurant", 4000, 36.00, "corner restaurant"),
        ("2475 · BurgerFi", "Fast-casual restaurant", 3000, 40.00, "national franchise"),
        ("2485 · In-line shops", "Various local retail/service", 6005, 30.00, "balance of occupied"),
        ("2481 · SFL Maven", "Retail / resale", 1100, 32.00, "small-shop"),
    ],
    vacant_sf=5000,   # ~5,000 SF ground-floor restaurant space vacant (prior tenant 26 yrs)
    lease_note="Daoud's = anchor; ~20% vacant",
    land_psf=248.00,
    src=dict(
        gla="⚠️ LoopNet (25,105 SF)", occ0="🔶 ~20% vacant", stab_occ="🔶",
        rent="🔶 corridor $32–45 NNN", mill="✅ 2025 area millage",
        price="⚠️ reported ~$8.5M", cap="🔶 value-add strip 7.5%", exit="🔶 7.75%",
    ),
    inp=dict(
        gla=25105, occ0=0.801, stab_occ=0.95,
        market_rent=34.00, rent_growth=0.03, credit_loss=0.03, millage=0.0191,
        insurance=40000, cam=40000, rm=30000, mgmt_pct=0.04, exp_growth=0.03,
        ti_psf=30.00, lc_psf=20.00, reserve_psf=0.15, rollover_psf=0.75,
        price=8500000, closing_pct=0.025, ltv=0.60, loan_rate=0.0750, amort=30,
        goingin_cap=0.075, exit_cap=0.0775, cost_sale=0.02, hold=5, disc=0.09,
        land_sf=30928,
    ),
)
