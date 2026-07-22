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
    para("Institutional acquisition underwriting for a five-asset covered-land-play assemblage on the E Sunrise Blvd hard corner at the Galleria.")
    para("Two valuations of the same block are presented: (1) an INCOME basis — what the combined cash flows support — and (2) a HIGHEST-AND-")
    para("BEST-USE / covered-land basis — land value plus an assemblage premium to control every parcel. Only blue cells are inputs; change any")
    para("blue cell and the entire workbook recalculates (full recalc on open). The ASSUMPTIONS tab is the single control surface — global drivers")
    para("plus a block per asset (price · rents · occupancy · operating expenses · caps · debt). Standard modeling params (rent/expense growth,")
    para("TI/LC, reserves, closing detail) stay blue on each asset tab. Order: Exec · Assumptions · Income · Scenarios · Assemblage · Highest & Best Use · assets · Notes.")
    para("Each component is priced independently (asset tabs) and combined (Assemblage / Income / HBU). The HBU tab prices the land as regular fragmented parcels vs. an assembled superblock (plottage premium), and carries the office condo full buy-out.")
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

    head("KEY MARKET ASSUMPTIONS  (mid-2026, MODELED)")
    for k, v in [
        ("Retail rents", "in-line $32–55/SF NNN (Sunrise corridor $45–60); restaurant/end-cap $40–50/SF"),
        ("Publix / Starbucks", "grocery ~$13/SF NNN, cap 6.0–6.75%; Starbucks pad ~$60/SF, cap 4.75–5.5%"),
        ("Office", "small Class B/C ~$20–30/SF gross (~$15–24 NNN); cap 7.5–9.0%"),
        ("Retail caps", "stabilized strip 6.25–6.75%; value-add 7.25–8.0%; exit = going-in +25 bps"),
        ("Land", "Fort Lauderdale infill ~$248/SF (subject comps $228–255); Galleria bulk ~$53/SF"),
        ("Senior debt", "stabilized 5.75–7.0%, 60–75% LTV, DSCR 1.25–1.40x, debt yield 7–10%"),
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
