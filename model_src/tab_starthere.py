"""
tab_starthere.py — START HERE (the reading map).
The front door: the deal in three lines, the four numbers that matter, a plain-
English guide to what each tab answers and the order to read them, and how to
change an input. Its whole job is to make a 16-tab workbook clear to follow.
"""
from mblib import F_ACCT_TOP, F_PCT1, F_MULT

L = 2


def build(s, regs):
    IV, A, PR = "Income Valuation", "Assemblage", "Partner Returns"

    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"

    s.colw({"A": 2, "B": 22, "C": 15, "D": 15, "E": 15, "F": 15, "G": 13,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "START HERE  —  how to read this model", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "DAWN RE Enterprises · E Sunrise Blvd Assemblage · Fort Lauderdale, FL · a covered-land play at the Galleria hard corner",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # ---------------- the deal in three lines ----------------
    s.section(r, L, 13, "THE DEAL IN THREE LINES"); r += 1
    for lab, txt in [
        ("What", "Acquire 4 contiguous parcels on E Sunrise Blvd and control the corner — buy the income, control the dirt. (Bayview, a 5th parcel, just sold to Willow Bridge — now a JV upside.)"),
        ("Price", "The rent supports about $65M (income basis); controlling the whole block costs about $127M (covered-land) — the gap is the land + density option."),
        ("Return", "At the income basis the LP earns ~20% IRR / 2.4×; the real upside is the entitled land you hold for redevelopment."),
    ]:
        s.put(r, L, lab, style="label_b", align="left")
        s.put(r, 3, txt, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---------------- the four numbers ----------------
    s.section(r, L, 13, "THE FOUR NUMBERS THAT MATTER  (live)"); r += 1
    kpis = [
        ("INCOME BASIS", f"={cell(IV,'PX_INCOME')}", F_ACCT_TOP, "what the rent supports"),
        ("COST TO CONTROL", f"={cell(A,'ACQ')}", F_ACCT_TOP, "covered-land price"),
        ("LP IRR", f"={cell(PR,'LP_IRR')}", F_PCT1, "investor return, 5-yr"),
        ("EQUITY TO CLOSE", f"={cell(IV,'EQ_H')}", F_ACCT_TOP, "the check to raise"),
    ]
    c = 2
    for lab, f, fmt, sub in kpis:
        s.put(r, c, lab, style="kpi_lab", align="center", merge=(r, c + 2))
        s.put(r + 1, c, f, style="kpi_val", fmt=fmt, align="center", merge=(r + 1, c + 2))
        s.put(r + 2, c, sub, style="note", align="center", merge=(r + 2, c + 2))
        c += 3
    s.rowh(r, 14); s.rowh(r + 1, 30); r += 4

    # ---------------- reading map ----------------
    s.section(r, L, 13, "WHERE TO GO  —  each tab answers one question  (read top to bottom)"); r += 1
    s.put(r, L, "Tab", style="subhead", align="left", merge=(r, 4))
    s.put(r, 5, "Answers the question…", style="subhead", align="left", merge=(r, 13)); r += 1
    guide = [
        ("group", "① SEE THE DEAL & THE VISION", None),
        ("tab", "Executive Summary", "What's the whole deal, on one page?"),
        ("tab", "Comps & Pricing", "What's each asset worth and what can I quote? — sourced comps + individual & assemblage pricing"),
        ("tab", "Development Pro Forma", "What can be built here — density, product, cost, value? The redevelopment vision, quantified"),
        ("tab", "Start Here", "How do I read this? (you are here)"),
        ("group", "② MAKE THE DEAL", None),
        ("tab", "Deal Book", "Who do I buy from, at what price, and how? (per-owner strategy, sources & uses, risks, timeline)"),
        ("group", "③ PLAY WITH IT", None),
        ("tab", "Review Board", "How do the returns move if I change the key assumptions? (live sensitivities)"),
        ("tab", "Capital Stack", "How much can I borrow / afford, and how does the stack look? (leverage & equity)"),
        ("group", "④ CHANGE THE INPUTS", None),
        ("tab", "Assumptions", "The ONE place to change numbers. Every blue cell drives the model — change one and everything recalculates."),
        ("group", "⑤ THE MATH (drill-down)", None),
        ("tab", "Income Valuation", "How is the price and the return actually computed? (the engine — consolidated cash flows)"),
        ("tab", "Scenarios", "What do downside / base / upside look like?"),
        ("tab", "Assemblage", "How do the parts add up to the covered-land price?"),
        ("tab", "Highest & Best Use", "What's the land worth alone vs. assembled, and does redevelopment pencil?"),
        ("tab", "Partner Returns", "If you raise LP equity: how the money splits (8% pref, promote)"),
        ("group", "⑥ THE ASSETS (one tab each)", None),
        ("tab", "Shahidi · Publix · Sunrise · Office · Land", "The full underwrite of each property — rent roll, cash flow, P&L."),
        ("group", "⑦ WHERE IT COMES FROM", None),
        ("tab", "Notes & Sources", "Where every number came from, what's verified vs. still to confirm, and the methodology."),
    ]
    for kind, a, q in guide:
        if kind == "group":
            s.put(r, L, a, style="subhead", align="left", merge=(r, 13)); r += 1
        else:
            s.put(r, L, a, style="label_b", align="left", merge=(r, 4))
            s.put(r, 5, q, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---------------- play with it ----------------
    s.section(r, L, 13, "PLAY WITH IT  —  it's a live model: change a BLUE cell and everything recalculates"); r += 1
    s.put(r, L, "Open it in Excel or Google Sheets (a preview is read-only). Blue cells are the only ones you touch — the rest updates on its own.",
          style="warn", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "To change…", style="subhead", align="left", merge=(r, 4))
    s.put(r, 5, "Go here and edit the blue cell", style="subhead", align="left", merge=(r, 9))
    s.put(r, 10, "…and watch this update", style="subhead", align="left", merge=(r, 13)); r += 1
    for what, where, result in [
        ("What you pay for an asset", "Assumptions → that asset's block → 'Purchase price / basis'", "income price, returns, Comps & Pricing"),
        ("A cap rate", "Assumptions → 'Blended going-in cap' (or an asset's going-in / exit cap)", "the value and the price"),
        ("Rents", "Assumptions → an asset's 'Market rent' (or the Publix leaseback rent)", "NOI → value → returns"),
        ("How much you borrow", "Assumptions → 'Max senior LTV' and 'Senior rate'", "debt, equity, DSCR, returns"),
        ("The assemblage premium", "Assumptions → 'Assemblage premium — base'", "the covered-land price"),
        ("The office buy-out price", "Office Condo tab → 'Buy-out $/SF (unit market)'", "office price → covered-land"),
        ("A sensitivity (without touching the model)", "Review Board → the blue axis cells on any grid", "the grid + driver tornado, live"),
        ("What you can afford", "Capital Stack → 'Equity available'", "max price + assemblage capacity"),
    ]:
        s.put(r, L, what, style="label_b", align="left", merge=(r, 4))
        s.put(r, 5, where, style="calc", align="left", merge=(r, 9))
        s.put(r, 10, result, style="note", align="left", merge=(r, 13)); r += 1
    r += 1
    s.put(r, L, "Confirming real data", style="label_b", align="left", merge=(r, 4))
    s.put(r, 5, "As you get real facts (a sale price, a rent, a lender quote), put them in the overrides.json file and rebuild — it lists every gap and where to source it. Or just edit the blue cell directly and keep the file.",
          style="calc", align="left", merge=(r, 13)); r += 1

    # ---------------- colour legend ----------------
    s.section(r, L, 13, "THE COLOR CODE"); r += 1
    for c_txt, m in [
        ("Blue on yellow", "an input — the only cells you change"),
        ("Black", "a formula / calculation (leave it)"),
        ("Green", "a verified fact, or a live link pulling from another tab"),
        ("Gold on navy", "a header, total, or key number"),
        ("Orange", "a warning, a flag, or something to confirm"),
    ]:
        s.put(r, L, c_txt, style="label_b", align="left", merge=(r, 3))
        s.put(r, 4, m, style="calc", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Confidence", style="label_b", align="left", merge=(r, 3))
    s.put(r, 4, "✅ verified (public record)   ·   ⚠️ reported (confirm at the county)   ·   🔶 modeled (a market assumption)",
          style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C3")
    return s
