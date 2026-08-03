"""
tab_notes.py — Notes, Sources & Methodology. Institutional documentation tab:
data provenance + confidence flags, valuation methodology, financing conventions,
color legend, and limitations/disclaimers.
"""
L = 2


def build(s):
    s.colw({"A": 2.5, "B": 30, "C": 13, "D": 13, "E": 13, "F": 13, "G": 13,
            "H": 13, "I": 13, "J": 13, "K": 13, "L": 13, "M": 13})
    r = 1
    s.put(r, L, "NOTES, SOURCES  &  METHODOLOGY", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "DAWN RE Enterprises Corp.  ·  E Sunrise Blvd Assemblage  ·  Fort Lauderdale, FL  ·  prepared 2026-07-21  ·  CONFIDENTIAL",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    def head(t):
        nonlocal r
        s.section(r, L, 13, t); r += 1
    def para(t, style="calc"):
        nonlocal r
        s.put(r, L, t, style=style, align="left", merge=(r, 13)); r += 1
    def kv(k, v):
        nonlocal r
        s.put(r, L, k, style="label_b", align="left")
        s.put(r, 4, v, style="calc", align="left", merge=(r, 13)); r += 1

    head("PURPOSE  &  HOW TO USE THIS MODEL")
    para("Institutional underwriting for a four-parcel covered-land / redevelopment assemblage on the E Sunrise Blvd hard corner at the Galleria (a 5th parcel, 1040 Bayview, sold to Willow Bridge ~Aug 2026 and is modeled as a JV upside).")
    para("Two valuations of the same block are presented: (1) an INCOME basis — what the combined cash flows support — and (2) a HIGHEST-AND-")
    para("BEST-USE / covered-land basis — land value plus an assemblage premium to control every parcel. Only blue cells are inputs; change any")
    para("blue cell and the entire workbook recalculates (full recalc on open). The ASSUMPTIONS tab is the single control surface — global drivers")
    para("plus a block per asset (price · rents · occupancy · operating expenses · caps · debt). Standard modeling params (rent/expense growth,")
    para("TI/LC, reserves, closing detail) stay blue on each asset tab. Order: Exec · Assumptions · Income · Scenarios · Assemblage · Highest & Best Use · assets · Notes.")
    para("Each component is priced independently (asset tabs) and combined (Assemblage / Income / HBU). The HBU tab prices the land as regular fragmented parcels vs. an assembled superblock (plottage premium), and carries the office condo full buy-out.")
    r += 1

    head("REUSE FOR A NEW ASSEMBLAGE  (this is a template)")
    para("The workbook is a system: the same engine repriced for any covered-land / assemblage play. To repoint it at a new deal, change only the blue")
    para("inputs — no formulas move. The recipe:")
    kv("1. Prior-sale basis", "On ASSUMPTIONS → 'PRIOR SALE / SELLER BASIS', set each component's last price + year. Drives the HBU acquisition history and the Exec scorecard's 'they paid' column (one source, both places).")
    kv("2. Per-asset blocks", "On ASSUMPTIONS → 'PER-ASSET INPUTS', reset each asset's price · rents · occupancy · operating expenses · caps · debt. Retail/office/land blocks already differ by type; copy the closest one for a new asset.")
    kv("3. Global drivers", "Reset caps, hold, financing, closing costs, assemblage premium, and the land/redevelopment ladder up top. These flow to Income, Scenarios, Assemblage, and HBU automatically.")
    kv("4. Rosters & rent rolls", "Replace the office owner roster (Office Condo tab) and each asset's tenant rows with the real ones — all blue/editable. Sizes and $/SF recompute value, buy-out, and plottage.")
    kv("5. Component list", "Add/drop an asset by editing the component list in the builder (one tuple per asset in tab_hbu / tab_exec / tab_assemblage); the scorecard, ladder, and sum-of-parts pick it up.")
    kv("6. Verify & re-flag", "Confirm ⚠️ REPORTED figures at the county, move them to ✅ VERIFIED, and re-run. The data-gap register on Assumptions lists exactly what to confirm.")
    r += 1

    head("VALUATION METHODOLOGY")
    kv("As-is vs. stabilized", "Direct cap on AS-IS in-place NOI (current occupancy) gives the going-in value; stabilized NOI ÷ exit cap gives post-lease-up value. The spread is value creation.")
    kv("Income-based price", "Concluded on as-is direct cap; stabilized direct cap and a DCF (PV of unlevered cash flows at the target unlevered yield) are shown as cross-checks.")
    kv("Portfolio returns", "Computed by CONSOLIDATING each asset's actual cash flows into one stream and running a single IRR — never by averaging asset IRRs (mathematically invalid).")
    kv("Sources & Uses", "Uses = price + doc-stamp/transfer tax + title + legal/DD + loan origination; Sources = sized senior debt + equity (plug). Equity is the S&U plug, not a shortcut.")
    kv("Return attribution", "Unlevered profit is decomposed into operating cash flow, NOI growth / lease-up, cap-rate movement, cost of sale, and closing — and ties exactly to the consolidated cash flow.")
    kv("Scenario analysis", "Downside / Base / Upside bundle NOI achievement, exit cap, and financing rate; each is a full consolidated cash flow with its own IRR / multiple / DSCR / cash-on-cash.")
    kv("Break-even", "The break-even exit cap is the softest exit that still returns 1.0x of equity; the cushion vs. the underwritten exit cap is a downside guardrail.")
    kv("Covered-land (HBU) price", "Summed control cost (each parcel at the greater of income or land value; Publix via sale-leaseback at its fee price) plus a 15/20/25% assemblage premium.")
    kv("Publix sale-leaseback", "Acquire the Publix fee; Publix leases back and pays NNN rent for the entitlement term (rent covers carry), then vacates. The leaseback income CLIFFS at term-end and the parcel EXITS AT LAND VALUE (covered-land), not an income cap. A solver on the Publix tab back-solves the leaseback rent for a target DSCR or cap. Rent, SF, price, term, and leverage are on the Assumptions tab.")
    kv("Reversion", "Each asset sells in the hold year at its forward NOI ÷ exit cap, net of cost of sale; the consolidated reversion sums the asset-level reversions.")
    kv("Redevelopment", "The Live Local residual runs negative in the AE flood zone at current coastal hard costs; the model does NOT force it positive — the conclusion is HOLD.")
    r += 1

    head("SENIOR DEBT  —  SIZING CONVENTION")
    para("Debt is sized to the LESSER OF three lender constraints, sized on as-is in-place NOI:")
    kv("Constraint 1 — LTV", "Loan ≤ max LTV × purchase price (default 60%).")
    kv("Constraint 2 — DSCR", "Loan ≤ NOI ÷ (min DSCR × mortgage constant); default min DSCR 1.30x.")
    kv("Constraint 3 — Debt yield", "Loan ≤ NOI ÷ min debt yield (default 8.5%).")
    para("The sized loan is the minimum of the three; the binding constraint is flagged on the Income Valuation tab.")
    r += 1

    head("DATA SOURCES  &  CONFIDENCE FLAGS")
    s.put(r, L, "Flag", style="subhead", align="center")
    s.put(r, 3, "Meaning", style="subhead", align="left", merge=(r, 13)); r += 1
    for f, m in [("✅ VERIFIED", "public record — BCPA property appraiser / FL Sunbiz / recorded deed"),
                 ("⚠️ REPORTED", "counterparty, broker listing (LoopNet/Crexi), or press — unconfirmed at the county"),
                 ("🔶 MODELED", "assumption from mid-2026 market research; moves with the blue inputs")]:
        s.put(r, L, f, style="calc", align="center")
        s.put(r, 3, m, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1
    hdr = ["Asset", "Verified", "Sources"]
    s.put(r, L, hdr[0], style="subhead", align="left")
    s.put(r, 4, hdr[1], style="subhead", align="center")
    s.put(r, 5, hdr[2], style="subhead", align="left", merge=(r, 13)); r += 1
    rows = [
        ("Shahidi Retail (Galleria Plaza)", "✅ BCPA/Sunbiz", "Folio 49-42-36-12-0070; tenants via LoopNet/Southeast Centers, Yelp, official locators; rents from corridor comps"),
        ("Publix + Starbucks", "✅ BCPA/deed", "Folio -0060; $25M Trustee's Deed 03/2025 (The Real Deal); rents/caps from net-lease research (Boulder Group, Matthews)"),
        ("Sunrise Plaza (Kar Luen)", "⚠️ reported", "Folio -0011; LoopNet/Sunbiz/Cortera; tenants via Yelp; value & sale unconfirmed — VERIFY AT BCPA"),
        ("Galleria Corporate Centre", "⚠️ reported", "2455 E Sunrise; owners via Daily Business Review 10/2019 (Main Street Fund 57.4%); per-unit folios not enumerated"),
        ("1040 Bayview (land)", "⚠️ reported", "Folio -0040; Florida YIMBY/Traded/BBX/Procacci; entitlement 259 units; BCPA market value reported not confirmed"),
    ]
    for a, v, src in rows:
        s.put(r, L, a, style="label", align="left")
        s.put(r, 4, v, style="calc", align="center")
        s.put(r, 5, src, style="calc", align="left", merge=(r, 13)); r += 1
    para("BCPA (bcpa.net) was blocked from the build environment; ⚠️ items were sourced from web mirrors of the tax roll and must be confirmed at the county before close.", style="warn")
    r += 1

    head("KEY MARKET ASSUMPTIONS  (mid-2026 — sourced from the research sweep below)")
    for k, v in [
        ("Retail rents", "Fort Lauderdale avg $34–36/SF NNN (Matthews Q3'25); Sunrise arterial strip ~$25–50/SF, premium space to $60; Las Olas $50–100+"),
        ("Retail caps", "unanchored strip stabilized 6.25–7.5%, value-add 6.5–8.5% (Matthews); Broward retail vacancy ~3.7–3.9% (pricing power)"),
        ("Publix / net lease", "Publix NNN 5.25–6.25% (anchored centers 5.5–5.8%); grocery base rent $8–14/SF NNN — our $22 leaseback is a bridge rate above market (Boulder Group, investmentgrade.com)"),
        ("Starbucks pad", "~$60/SF NNN, 10% bumps/5yr, ~$2.0–2.5M/pad; cap ~5.2% (as low as 4.1–5.0% for drive-thru) — Boulder Group"),
        ("Office", "Broward avg $40–42/SF gross (Class A $46; Class B ~$28); vacancy 12.3%; cap 8%+ (Class B/C double-digit 'commonplace') — Colliers 4Q25, CBRE"),
        ("Land", "FL infill closed $129/SF & ~$38k/unit (Affiliated 2/24); asking to $316/SF & $61k/unit — subject $125/SF ≈ the closed comp"),
        ("Multifamily rent (new A)", "Downtown FTL ~$3.44/SF/mo · 1BR ~$3,150 · 2BR ~$4,700 (RentCafe/Yardi 6/26); SOFT — ~9% Class-A vacancy, ~2mo concessions, 8,760-unit pipeline"),
        ("Multifamily value / cap", "new Class A ~$550–640k/unit (Veneto Las Olas $637k, Q2'25); stabilized cap ~4.75–5.6% (CBRE/Matthews); OER ~40% (FL insurance-heavy)"),
        ("For-sale condo (new)", "FTL $700–1,200+/SF; oceanfront $1,100+ (Selene, Andare); non-oceanfront near-Galleria ~$800–1,000/SF (CondoBlackBook) — the corridor's newest towers skew condo"),
        ("Density (redev)", "codified base 60 du/net ac (RMH-60/RAC-High); Bayview did 108/ac (city affordable bonus); Galleria next door ≈140/ac (Live Local, 4,417 units/31.5 ac) → 7 ac ≈ 756–980 units"),
        ("Height / FAR (redev)", "DRAC FAR 4.0 codified (Live Local floor ~6.0); Live Local height = tallest within 1 mi ≈ Selene 300 ft / Galleria 342 ft ≈ 30 stories"),
        ("Impact fees (redev)", "Broward road/rec/transportation fees SUSPENDED ($0) since 10/2024; material per-unit fee ≈ Broward school $461/unit (high-rise) + city park/water — light"),
        ("Entitled-land comp", "★ 1040 Bayview (259 units, entitled) SOLD to Willow Bridge $24.7M ≈ $95k/entitled unit, ~Aug 2026 (The Real Deal) — the block's best entitled comp"),
        ("Construction (redev)", "AE-coastal concrete mid/high-rise $300–450/SF defensible; HVHZ premium 8–12% (RSMeans, RLB E-Q2'25, Multifamily.loans)"),
        ("Insurance", "coastal Broward commercial 1.2–4.5% of value; within ~1 mi of water 2–3×; South FL premiums now rolling back −11% to −17% in 2026 (Bridgeway, Artemis)"),
        ("Senior debt", "single-tenant net-lease STNL avg 6.55–6.80% (Boulder Q1'26); stabilized 5.75–7.0%, 60–75% LTV, DSCR 1.25–1.40×, debt yield 7–10%"),
        ("Covered-land cap", "in-place income cap ~3–5% — income covers carry, not a yield play"),
    ]:
        kv(k, v)
    r += 1

    head("COLOR  &  FONT LEGEND")
    for c, m in [("Blue on yellow", "hardcoded input — the only cells to change"),
                 ("Black on white", "formula / calculation"),
                 ("Green", "public-record verified fact or cross-sheet link"),
                 ("Gold on navy / dark", "section header, total, KPI box, banner"),
                 ("Orange / dark red", "warning, flag, or excluded-from note")]:
        s.put(r, L, c, style="label_b", align="left")
        s.put(r, 4, m, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    head("LIMITATIONS  &  DISCLAIMERS")
    for t in [
        "• Space-level rent rolls are estimated; no tenant-by-tenant lease abstracts (expirations, options, recovery type) were available. Replace with real leases in diligence.",
        "• Publix and the office-condo units are not listed for sale; they are modeled as acquisition cases. Publix is a fee owner, so its 'rent' is a mark-to-market, not contract income.",
        "• Property-tax reassessment is modeled to each asset's own price (FL rule); an assemblage purchase would reallocate basis and taxes across parcels.",
        "• Returns exclude any LP/GP promote/waterfall, transfer taxes, and portfolio-level G&A. This is a screening model, not a closing model.",
        "• All figures are estimates for internal evaluation only and are not an appraisal, an offer, or investment advice. Confirm all ⚠️ REPORTED data at the county before relying on it.",
    ]:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1

    s.freeze("C3")
    return s
