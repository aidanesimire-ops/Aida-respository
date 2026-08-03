"""
tab_comps.py — COMPS & PRICING (the quotable factual basis).
For each asset: the subject facts, the comparable sales / lease / cap-rate evidence
with a NAMED SOURCE and date, and the concluded value — priced individually — then
the assemblage roll-up. Confidence-flagged so you know exactly what you can quote:
  ✅ public record (BCPA / recorded deed / Sunbiz)   ·   📰 press-reported transaction
  📊 broker / market report (range)                  ·   ⚠️ asking / unverified
County portals (BCPA / Clerk / Sunbiz) were egress-blocked when this was compiled, so
📰/📊/⚠️ items come from press and broker research and MUST be confirmed at the county
before close. Concluded prices are live links to the model.
"""
from mblib import F_ACCT, F_ACCT_TOP, F_PCT2, F_NUM, F_PSF

L = 2

# per asset: subject facts (label, value, flag) ; concluded price cell ; income-value cell ;
#            comps as (kind, description, figure, source · date, flag)
ASSETS = [
    dict(
        key="Shahidi Retail", title="① SHAHIDI RETAIL  ·  “Galleria Plaza”  —  the anchor",
        sub=[("Address / folio", "2541–2595 E Sunrise Blvd · folio 49-42-36-12-0070", "✅"),
             ("Owner", "Shawnick Galleria LLC (Esmail Shahidi) · Sunbiz L21000389291", "✅"),
             ("Size", "26,272 SF building (24,807 SF GLA) · 67,080 SF land (1.54 ac)", "✅"),
             ("Last sale", "$17,100,000 · Nov 2021 · from Stiles/Sunrise Investment Props · CBRE-brokered", "📰"),
             ("Occupancy", "~83% leased — value-add lease-up upside", "⚠️")],
        price=("Shahidi Retail", "PRICE"), income=("Shahidi Retail", "INPLACE_NOI"),
        comps=[
            ("SALE", "Shahidi itself — $651/SF bldg · $255/SF land", "$17.1M", "Shopping Center Business / Traded · 11/2021", "📰"),
            ("SALE", "The Galleria mall, 2414 E Sunrise (800k SF, redevelopment)", "$73M · $91/SF", "The Real Deal · 9/2025", "📰"),
            ("SALE", "200 E Sunrise land (Holy Cross ER site)", "$13M", "Traded.co · 2024", "📰"),
            ("RENT", "Fort Lauderdale avg retail asking, NNN", "$34–36/SF", "Matthews Retail Report · Q3'25", "📊"),
            ("RENT", "E Sunrise arterial strip (premium space to $60)", "$25–50/SF NNN", "Native Realty / Justin Crow CRE · 2025-26", "📊"),
            ("CAP", "Unanchored strip — stabilized / value-add", "6.25–7.5% / 6.5–8.5%", "Matthews · 2025", "📊"),
            ("CAP", "Broward retail vacancy (pricing power)", "3.7–3.9%", "Broker One / market · 2025-26", "📊"),
        ],
        concl="Concluded at the Nov-2021 arm's-length basis ($17.1M); the model's income value at $55/SF blended "
              "rent and a 6.0% going-in cap ties to ~$16.7M. Value-add lease-up to 95% is the upside.",
    ),
    dict(
        key="Publix & Starbucks", title="② PUBLIX + STARBUCKS",
        sub=[("Address / folio", "2501–2519 E Sunrise Blvd · folio -0060", "✅"),
             ("Owner", "REAL SUB LLC (Publix Super Markets, Lakeland)", "✅"),
             ("Size", "36,822 SF (Publix ~34,622 + Starbucks pad ~2,200) · 2.5 ac", "✅"),
             ("Last sale", "$25,000,000 · $678/SF · Mar 2025 (seller held since 1977)", "📰")],
        price=("Publix & Starbucks", "PRICE"), income=("Publix & Starbucks", "AS_IS_NOI"),
        comps=[
            ("CAP", "Publix single-tenant NNN (anchored centers 5.5–5.8%)", "5.25–6.25%", "Boulder Group / investmentgrade.com · 2025-26", "📊"),
            ("RENT", "Grocery-anchor base rent, NNN", "$8–14/SF", "apers.app / net-lease research · 2026", "📊"),
            ("SALE", "Starbucks drive-thru pad — rent / cap", "~$60/SF · ~5.2% cap", "The Boulder Group · 2025", "📊"),
            ("RENT", "Starbucks pad — 10% bumps/5yr · ~$2.0–2.5M/pad", "~$60/SF NNN", "Boulder Group / LoopNet · 2025", "📊"),
        ],
        concl="Fee acquisition at the verified $25M basis. NOTE: the model's $22/SF leaseback is a bridge rate above "
              "the $8–14/SF market grocery rent — a structuring assumption, not a market comp. Confirm any leaseback with Publix.",
    ),
    dict(
        key="Sunrise Plaza", title="③ SUNRISE PLAZA  (Kar Luen)  —  incl. 2473 Daoud's Jewelry",
        sub=[("Address / folio", "2465–2485 E Sunrise Blvd · folio -0011", "✅"),
             ("Owner", "Kar Luen Inc · Sunbiz P94000029444", "✅"),
             ("Size", "25,105 SF · 0.71 ac (~30,928 SF land) · built 1962 (remod. 1987)", "⚠️"),
             ("Last sale", "Oct 2000 · $128,000 — implausibly low; likely nominal, NOT a value", "⚠️")],
        price=("Sunrise Plaza", "PRICE"), income=("Sunrise Plaza", "AS_IS_NOI"),
        comps=[
            ("VALUE", "Reported value — no recent arm's-length sale", "~$8.5M", "LoopNet / broker · unverified", "⚠️"),
            ("RENT", "Corridor in-line / restaurant NNN (see Shahidi comps)", "$25–50/SF", "Native Realty / Matthews · 2025", "📊"),
            ("CAP", "Value-add strip (below-market rents, ~20% vacant)", "7.25–8.5%", "Matthews · 2025", "📊"),
        ],
        concl="Priced at the reported ~$8.5M pending confirmation — the $128k/2000 record is not a value indicator. "
              "The most data-dependent asset: verify SF, rents, occupancy and any recent basis at BCPA before an offer.",
    ),
    dict(
        key="Office Condo", title="④ GALLERIA CORPORATE CENTRE  (office condominium)",
        sub=[("Address", "2455 E Sunrise Blvd · 13-story Class B office condo · 168,807 SF", "✅"),
             ("Control", "Grove Gate / Main Street Fund (Brad Weiss) — 57.4% (96,930 SF)", "✅"),
             ("Bulk basis", "$10,000,000 · ~$103/SF · Sept 2019 (from Intl Sunrise Partners)", "✅"),
             ("Balance", "42.6% held by ~40 individual owners (needs a per-unit BCPA pull)", "⚠️")],
        price=("Office Condo", "BUYOUT_TOTAL"), income=("Office Condo", "AS_IS_NOI"),
        comps=[
            ("SALE", "Unit #401 — closed", "$381/SF", "MLS A11438689 · 6/2024", "📰"),
            ("SALE", "Suite 805 — closed", "$238/SF", "Berger Commercial · 11/2019", "📰"),
            ("SALE", "Grove Gate unit asking range (building-wide)", "$367–475/SF", "LoopNet / CommercialSearch · 2025", "⚠️"),
            ("RENT", "Office units — Modified Gross asking", "$25–26/SF MG", "LoopNet listing · 2024-26", "📰"),
            ("CAP", "Fort Lauderdale Class B/C office", "8%+ (double-digit common)", "Colliers 4Q25 / CBRE", "📊"),
        ],
        concl="Full buy-out priced at $250/SF (a bulk discount to the $238–381/SF closed comps and $367–475/SF asks) "
              "= $42.2M. The income value at an 8% cap is ~$22M — the ~$20M gap is the fragmentation premium to re-assemble the condo.",
    ),
    dict(
        key="Land", title="⑤ 1040 BAYVIEW  —  JV UPSIDE  (sold to Willow Bridge; NOT in the 4-parcel core)",
        sub=[("Address / folio", "1040 Bayview Dr · folio -0040 · 2.39 ac (103,982 SF)", "✅"),
             ("⚠️ JUST SOLD", "Procacci → WILLOW BRIDGE for $24.7M (~Aug 2026) — parcel has traded; verify & re-approach", "📰"),
             ("Prior sale", "$7.9–8.0M · 2014 (Procacci/BBX JV)", "✅"),
             ("Entitlement", "259 units (247 mkt + 12 aff), 8 stories · case UDP-Z25002", "📰")],
        price=("Land", "CONCLUDED"), income=("Land", "INCVAL"),
        comps=[
            ("SALE", "★ 1040 Bayview itself — 259-unit ENTITLED site, SOLD to Willow Bridge", "$24.7M · $236/SF · $95k/unit", "The Real Deal · ~8/2026", "📰"),
            ("SALE", "2125 S Andrews (Affiliated) — 400-unit approved site, CLOSED", "$15.2M · $129/SF · $38k/unit", "The Real Deal · 2/2024", "📰"),
            ("SALE", "707 SE Third (Benjamin Cos) — 542-unit site, ASKING", "$33M · $316/SF · $61k/unit", "The Real Deal · 2/2025", "⚠️"),
        ],
        concl="THE PARCEL JUST TRADED: Procacci sold the entitled site to Willow Bridge for $24.7M (~$95k/entitled unit) in ~Aug 2026 — "
              "so the model's $13M basis is stale, and the counterparty has changed. That $95k/unit is now your best entitled-land comp for the "
              "whole assemblage. Re-approach as a JV with Willow Bridge, or underwrite the block as four parcels.",
    ),
]


def build(s, regs):
    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"
    A, HB, IV = "Assemblage", "Highest & Best Use", "Income Valuation"

    s.colw({"A": 2, "B": 30, "C": 13, "D": 13, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "COMPS & PRICING  —  individual + assemblage, with sources you can quote", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "The factual basis for each asset's value and the assemblage price. ✅ public record · 📰 press-reported deal · 📊 broker/market "
                "report · ⚠️ asking/unverified. County portals were blocked when compiled — confirm ⚠️/📰/📊 items at BCPA before close.",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    KIND = {"SALE": "Sale comp", "RENT": "Lease comp", "CAP": "Cap rate", "VALUE": "Value indicator"}
    for a in ASSETS:
        s.section(r, L, 13, a["title"]); r += 1
        # subject facts
        s.put(r, L, "Subject", style="subhead", align="left", merge=(r, 3))
        s.put(r, 4, "", style="subhead"); s.put(r, 5, "flag", style="subhead", align="center"); r += 1
        for lab, val, flag in a["sub"]:
            s.put(r, L, "  " + lab, style="label", align="left", merge=(r, 3))
            s.put(r, 4, val, style=("verified" if flag == "✅" else "calc"), align="left", merge=(r, 12))
            s.put(r, 13, flag, style="calc", align="center"); r += 1
        # concluded pricing (live links)
        s.put(r, L, "  CONCLUDED PRICE (individual)", style="subtotal", align="left", merge=(r, 3))
        s.put(r, 4, f"={cell(a['key'], a['price'][1])}", style="calc", color="008000", fmt=F_ACCT_TOP, align="right")
        if a["income"]:
            iv = a["income"]
            # income assets: value = NOI/cap; land/office already carry an income value cell
            if iv[1] in ("INCVAL",):
                s.put(r, 6, f"={cell(iv[0], iv[1])}", style="calc", color="008000", fmt=F_ACCT, align="right")
            else:
                s.put(r, 6, f"={cell(iv[0], iv[1])}/{cell(a['key'],'GICAP')}", style="calc", color="008000", fmt=F_ACCT, align="right")
            s.put(r, 7, "← income value (cross-check)", style="note", align="left", merge=(r, 13))
        r += 1
        # comps table
        s.put(r, L, "  Type", style="subhead", align="left", merge=(r, 3))
        s.put(r, 4, "Comparable", style="subhead", align="left", merge=(r, 7))
        s.put(r, 8, "Figure", style="subhead", align="center", merge=(r, 9))
        s.put(r, 10, "Source · date", style="subhead", align="left", merge=(r, 13)); r += 1
        for kind, desc, fig, src, flag in a["comps"]:
            s.put(r, L, "  " + KIND.get(kind, kind), style="label_b", align="left", merge=(r, 3))
            s.put(r, 4, desc, style="calc", align="left", merge=(r, 7))
            s.put(r, 8, fig, style="calc", align="center", merge=(r, 9))
            s.put(r, 10, f"{flag} {src}", style="note", align="left", merge=(r, 13)); r += 1
        # conclusion
        s.put(r, L, "  Read", style="warn", align="left", merge=(r, 3))
        s.put(r, 4, a["concl"], style="calc", align="left", merge=(r, 13)); r += 2

    # ---------------- assemblage pricing ----------------
    s.section(r, L, 13, "⑥  ASSEMBLAGE PRICING  —  individual prices, summed, then assembled"); r += 1
    def price_row(label, formula, fmt, note, style="label", link=True):
        nonlocal r
        s.put(r, L, label, style=("grand" if style == "grand" else ("subtotal" if style == "sub" else "label")), align="left", merge=(r, 4))
        s.put(r, 5, formula, style=("grand" if style == "grand" else "calc"),
              color=(None if style == "grand" else ("008000" if link else None)), fmt=fmt, align="right", merge=(r, 6))
        s.put(r, 7, note, style="note", align="left", merge=(r, 13)); r += 1
    for a in ASSETS:
        if a["key"] == "Land":
            continue  # Bayview is a JV upside, not part of the 4-parcel core
        price_row("  " + a["key"], f"={cell(a['key'], a['price'][1])}", F_ACCT, "concluded individual price")
    price_row("SUM OF THE PARTS — 4 parcels, priced independently", f"={cell(A,'RAW_COST')}", F_ACCT_TOP, "what you pay buying each owner out", style="sub")
    price_row("＋ Assemblage premium (to control the block)", f"={cell(A,'ACQ')}-{cell(A,'RAW_COST')}", F_ACCT, "hard-to-assemble · holdout risk (20% base)")
    price_row("COVERED-LAND PRICE — controlled as one block", f"={cell(A,'ACQ')}", F_ACCT_TOP, "the ceiling — highest & best use", style="grand")
    price_row("Income basis (what the rent supports)", f"={cell(IV,'PX_INCOME')}", F_ACCT_TOP, "valuation floor — direct-cap on the combined rent")
    price_row("＋ Bayview JV (Willow Bridge) — upside", f"={cell('Land','CONCLUDED')}", F_ACCT, "adds ~2.39 ac & 259 entitled units IF a JV is struck — not in the core")
    price_row("Post-approval entitled land (4-parcel core)", f"={cell(HB,'LAND_ENTITLED')}", F_ACCT, "once density is approved")
    r += 1
    s.put(r, L, "How to quote this", style="warn", align="left", merge=(r, 3))
    s.put(r, 4, "Quote ✅ items freely (public record). Attribute 📰/📊 to the named source and date, and say “reported / market” — "
                "they are research, not the county roll. Confirm every ⚠️ before it goes in an LOI or an offering memo.",
          style="warn", align="left", merge=(r, 13)); r += 1

    s.freeze("C3")
    return s
