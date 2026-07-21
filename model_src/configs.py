"""
configs.py — per-asset config dicts for the generic income-asset builder.
"""

# =============================================================== PUBLIX + STARBUCKS
PUBLIX_CFG = dict(
    title="PUBLIX + STARBUCKS  ·  SHADOW-ANCHOR PAD",
    subtitle="2501–2519 E Sunrise Blvd   |   Folio 49-42-36-12-0060   |   REAL SUB LLC (Publix) "
             "— fee owner, NOT a seller · 36,822 SF · built 2011 · valued off the rent it produces",
    facts_header="PROPERTY FACTS  —  ✅ BCPA / ⚠️ REPORTED (Publix is not a seller — modeled as a mark-to-market case)",
    facts=[
        ("Record owner", "REAL SUB LLC (Publix Super Markets real-estate entity, Lakeland FL)", True),
        ("Status", "Publix bought the FEE under its own store 03/2025 — NOT a seller; modeled as assumption case", False),
        ("Building", "36,822 SF (Publix ~34,622 SF + Starbucks drive-thru pad ~2,200 SF)", True),
        ("Land", "109,791 SF  (2.520 ac)", True),
        ("Year built", "2011 (eff. 2012)", True),
        ("Last sale", "03/14/2025  —  $25,000,000  (Trustee's Deed)  =  $679/SF bldg · $228/SF land", True),
        ("2025 real-estate taxes", "$208,467   (2024: $217,404)", True),
        ("Rent economics (market)", "Publix ~$13/SF NNN (newer FL store); Starbucks pad ~$60/SF NNN", False),
        ("Cap rates (market)", "Grocery-anchored 6.0–6.75%; Starbucks pad 4.75–5.5%", False),
        ("Covered-land insight", "Publix paid $25M (land value) vs. ~$9–10M rent-supported income value — the land premium IS the covered-land thesis", False),
    ],
    lease_header="RENT DETAIL  —  🔶 market mark-to-market (Publix is fee-owned; no contract rent flows today)",
    leases=[
        ("Publix Super Market", "Grocery anchor (credit)", 34622, 13.00, "~$13/SF NNN newer store"),
        ("Starbucks (drive-thru pad)", "QSR pad (credit)", 2200, 60.00, "~$60/SF NNN pad"),
    ],
    vacant_sf=0,
    lease_note="100% occ · credit tenants",
    land_psf=227.75,   # Publix's actual land basis -> land value ties to $25M
    src=dict(
        gla="✅ BCPA (36,822 SF)", occ0="✅ fully occupied", stab_occ="🔶",
        rent="🔶 blended $13 grocery + $60 pad", mill="✅ 2025",
        price="🔶 income value (rent ÷ 6% cap); land basis $25M",
        cap="🔶 grocery-anchored 6.0%", exit="🔶 6.25%",
    ),
    inp=dict(
        gla=36822, occ0=1.00, stab_occ=1.00,
        market_rent=15.81,               # (34,622×13 + 2,200×60)/36,822
        rent_growth=0.02, credit_loss=0.01, millage=0.0191,
        insurance=45000, cam=35000, rm=25000, mgmt_pct=0.02, exp_growth=0.03,
        ti_psf=0.00, lc_psf=0.00, reserve_psf=0.15, rollover_psf=0.15,
        price=9700000,                   # rent-supported income value
        closing_pct=0.02, ltv=0.55, loan_rate=0.0625, amort=30,
        goingin_cap=0.060, exit_cap=0.0625, cost_sale=0.02, hold=5, disc=0.07,
        land_sf=109791,
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
