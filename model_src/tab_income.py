"""
tab_income.py — ASSEMBLAGE INCOME VALUATION (consolidated cash flows).
Combines every asset's cash flow into one pro forma, then derives the purchase
price the COMBINED INCOME supports (direct cap + DCF), and contrasts it with the
highest-and-best-use covered-land acquisition cost. The two prices differ — the
gap is the land / redevelopment-optionality premium.
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR)

L = 2
ACQ = 3
def pc(y): return 3 + y
def CL(c): return get_column_letter(c)

ASSETS = ["Shahidi Retail", "Publix & Starbucks", "Sunrise Plaza", "Office Condo", "Land"]
LABEL = {"Shahidi Retail": "Shahidi Retail (Galleria Plaza)",
         "Publix & Starbucks": "Publix + Starbucks",
         "Sunrise Plaza": "Sunrise Plaza (Kar Luen)",
         "Office Condo": "Galleria Corporate Centre (office)",
         "Land": "1040 Bayview (interim office)"}
HAS_CAP = {"Shahidi Retail": True, "Publix & Starbucks": True, "Sunrise Plaza": True,
           "Office Condo": True, "Land": False}


def _row(coord):
    return int("".join(c for c in coord if c.isdigit()))


def build(s, regs):
    def link(sheet, anchor, y):
        rw = _row(regs[sheet][anchor])
        return f"'{sheet}'!{CL(pc(y))}{rw}"
    s.colw({"A": 2.5, "B": 34, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "ASSEMBLAGE — INCOME VALUATION  (CONSOLIDATED CASH FLOWS)", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "Combine every asset's cash flow → derive the purchase price the COMBINED INCOME supports "
                "(direct cap + DCF) → contrast with the covered-land / highest-and-best-use price",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    s.section(r, L, 13, "HOW THIS DIFFERS FROM THE HBU ASSEMBLAGE"); r += 1
    intro = [
        "The Assemblage tab prices the block on a HIGHEST-AND-BEST-USE / covered-land basis — land value + an assemblage premium to",
        "control every parcel. This tab prices the SAME block purely on the income it produces: consolidate all five cash-flow streams,",
        "then value that income by direct capitalization and by DCF. Income-producing real estate is worth the rent it throws off — which",
        "is LESS than the land-control price. The difference is what a buyer pays for the dirt and the Live Local density option.",
    ]
    for t in intro:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---- consolidated cash flow ----
    s.section(r, L, 13, "CONSOLIDATED CASH FLOW  —  10-year annual  (🟢 green = links to each asset tab)"); r += 1
    s.put(r, L, "Year", style="subhead", align="left")
    for y in range(1, 11): s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1
    s.put(r, L, "Year ending", style="note", align="left")
    for y in range(1, 11): s.put(r, pc(y), f"Dec-{2026+y}", style="note", align="center")
    r += 1

    # NOI by asset
    s.put(r, L, "NET OPERATING INCOME by asset", style="subhead", align="left", merge=(r, 13)); r += 1
    noi_first = r
    for a in ASSETS:
        s.put(r, L, f"  {LABEL[a]}", style="label", align="left")
        for y in range(1, 11):
            s.put(r, pc(y), f"={link(a, 'ROW_NOI', y)}", style="calc", color="008000",
                  fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
        r += 1
    noi_last = r - 1
    noi_tot = r
    s.put(r, L, "Consolidated NOI", style="subtotal", align="left")
    for y in range(1, 11):
        s.put(r, pc(y), f"=SUM({CL(pc(y))}{noi_first}:{CL(pc(y))}{noi_last})",
              style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    # consolidated capital
    cap_row = r
    s.put(r, L, "Less: consolidated capital (reserves + leasing)", style="label", align="left")
    for y in range(1, 11):
        terms = "+".join(link(a, "ROW_CAP", y) for a in ASSETS if HAS_CAP[a])
        s.put(r, pc(y), f"=-({terms})", style="calc", color="008000", fmt=F_ACCT, align="right")
    r += 1
    op_row = r
    s.put(r, L, "Consolidated unlevered operating CF", style="subtotal", align="left")
    for y in range(1, 11):
        s.put(r, pc(y), f"={CL(pc(y))}{noi_tot}+{CL(pc(y))}{cap_row}",
              style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    # consolidated reversion
    rev_row = r
    s.put(r, L, "Consolidated reversion (net sale, exit yr)", style="label", align="left")
    for y in range(1, 11):
        terms = "+".join(link(a, "ROW_REV", y) for a in ASSETS)
        s.put(r, pc(y), f"={terms}", style="calc", color="008000", fmt=F_ACCT, align="right")
    r += 2

    g = s.reg
    def R(n): return g[n]

    # ---- valuation assumptions ----
    s.section(r, L, 13, "INCOME-VALUATION ASSUMPTIONS  —  🔵 blue inputs"); r += 1
    def inp(name, label, val, fmt, note):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="right", name=name)
        s.put(r, 4, note, style="note", align="left", merge=(r, 13)); r += 1
    inp("CAP", "Blended going-in cap (market)", 0.065, F_PCT2, "🔶 NOI-weighted across retail/grocery/office")
    inp("SCAP", "Blended stabilized/exit cap", 0.0675, F_PCT2, "🔶")
    inp("TYLD", "Target unlevered yield (DCF discount)", 0.085, F_PCT1, "🔶 unlevered return hurdle")
    inp("HOLD", "Hold period (yrs)", 5, F_YR, "🔶 all assets exit together")
    inp("CLOSE", "Closing & acq costs (% price)", 0.02, F_PCT1, "🔶")
    inp("LTV", "Blended senior LTV", 0.60, F_PCT1, "🔶")
    inp("RATE", "Blended senior rate", 0.065, F_PCT2, "🔶")
    inp("AMORT", "Amortization (yrs)", 30, F_YR, "🔶")
    r += 1

    # ---- income valuation ----
    s.section(r, L, 13, "PURCHASE PRICE ON THE BASIS OF ASSEMBLAGE CASH FLOWS"); r += 1
    def der(name, label, formula, fmt, style="calc", note=""):
        nonlocal r
        s.put(r, L, label, style=("subtotal" if style == "sub" else ("grand" if style == "grand" else "label")), align="left")
        s.put(r, 3, formula, style=("calc" if style != "grand" else "grand"), fmt=fmt, align="right", name=name, bold=(style in ("sub", "grand")))
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    der("INPLACE_NOI", "Consolidated in-place NOI (Yr 1)", f"={CL(pc(1))}{op_row}+({CL(pc(1))}{cap_row}*-1)", F_ACCT_TOP,
        note="NOI before capital = Yr-1 consolidated NOI")
    # cleaner: in-place NOI = consolidated NOI Yr1
    s.ws[f"C{r-1}"] = f"={CL(pc(1))}{noi_tot}"
    der("STAB_NOI", "Consolidated stabilized NOI (Yr 2)", f"={CL(pc(2))}{noi_tot}", F_ACCT_TOP)
    der("VAL_DC", "① Direct-cap value (in-place NOI ÷ cap)", f"={R('INPLACE_NOI')}/{R('CAP')}", F_ACCT_TOP,
        note="going-in income value")
    der("VAL_DCS", "② Direct-cap value (stabilized ÷ cap)", f"={R('STAB_NOI')}/{R('SCAP')}", F_ACCT_TOP,
        note="stabilized income value")
    # DCF value = PV @ target yield of (op CF through hold + reversion)
    valcf_hdr = r
    s.put(r, L, "Valuation cash flow (op CF ≤ hold + reversion)", style="label", align="left")
    for y in range(1, 11):
        s.put(r, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{op_row},0)+IF({y}={R('HOLD')},{CL(pc(y))}{rev_row},0)",
              style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    valcf_row = r; r += 1
    der("VAL_DCF", "③ DCF value (PV @ target yield)", f"=NPV({R('TYLD')},{CL(pc(1))}{valcf_row}:{CL(pc(10))}{valcf_row})", F_ACCT_TOP,
        note="price at which unlevered IRR = target yield")
    der("PRICE", "CONCLUDED INCOME-BASED PURCHASE PRICE", f"={R('VAL_DC')}", F_ACCT_TOP, style="grand",
        note="🔶 concluded = direct-cap on in-place NOI; ②/③ are cross-checks")
    r += 1

    # ---- returns at income-based price ----
    s.section(r, L, 13, "RETURNS AT THE INCOME-BASED PRICE  —  unlevered & levered"); r += 1
    der("LOAN", "Senior loan", f"={R('PRICE')}*{R('LTV')}", F_ACCT_TOP)
    der("MRATE", "Monthly rate", f"={R('RATE')}/12", F_PCT2)
    der("DS", "Annual debt service", f"={R('LOAN')}*({R('MRATE')}/(1-(1+{R('MRATE')})^(-{R('AMORT')}*12)))*12", F_ACCT_TOP)
    der("EQ", "Equity required", f"={R('PRICE')}*(1+{R('CLOSE')})-{R('LOAN')}", F_ACCT_TOP)
    der("LBAL5", "Loan balance at exit",
        f"={R('LOAN')}*(1+{R('MRATE')})^(12*{R('HOLD')})-({R('DS')}/12)*((1+{R('MRATE')})^(12*{R('HOLD')})-1)/{R('MRATE')}", F_ACCT_TOP)
    r += 1
    # unlevered CF row
    s.put(r, L, "Unlevered project CF (@ income price)", style="label_b", align="left")
    s.put(r, ACQ, f"=-{R('PRICE')}*(1+{R('CLOSE')})", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(r, pc(y), f"={CL(pc(y))}{valcf_row}", style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    un_row = r; r += 1
    # levered CF row
    s.put(r, L, "Levered CF — equity (@ income price)", style="label_b", align="left")
    s.put(r, ACQ, f"=-{R('EQ')}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(r, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{op_row}-{R('DS')},0)"
              f"+IF({y}={R('HOLD')},{CL(pc(y))}{rev_row}-{R('LBAL5')},0)",
              style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    lv_row = r; r += 2

    unr = f"{CL(ACQ)}{un_row}:{CL(pc(10))}{un_row}"
    unr1 = f"{CL(pc(1))}{un_row}:{CL(pc(10))}{un_row}"
    lvr = f"{CL(ACQ)}{lv_row}:{CL(pc(10))}{lv_row}"
    lvr1 = f"{CL(pc(1))}{lv_row}:{CL(pc(10))}{lv_row}"
    def ret(name, label, formula, fmt):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name); r += 1
    ret("IRR_U", "Unlevered IRR", f"=IRR({unr})", F_PCT1)
    ret("EM_U", "Unlevered equity multiple", f"=SUM({unr1})/-{CL(ACQ)}{un_row}", F_MULT)
    ret("NPV_U", "Unlevered NPV @ target yield", f"={CL(ACQ)}{un_row}+NPV({R('TYLD')},{unr1})", F_ACCT_TOP)
    ret("IRR_L", "Levered IRR", f"=IRR({lvr})", F_PCT1)
    ret("EM_L", "Levered equity multiple", f"=SUM({lvr1})/{R('EQ')}", F_MULT)
    ret("GOINGIN", "Going-in cap (in-place NOI ÷ price)", f"={R('INPLACE_NOI')}/{R('PRICE')}", F_PCT2)
    ret("DSCR1", "Year-1 DSCR", f"={R('INPLACE_NOI')}/{R('DS')}", F_MULT)
    ret("DY1", "Year-1 debt yield", f"={R('INPLACE_NOI')}/{R('LOAN')}", F_PCT1)
    r += 1

    # ---- valuation bridge / contrast ----
    s.section(r, L, 13, "VALUATION BRIDGE  —  income basis vs. highest-and-best-use (covered land)"); r += 1
    s.put(r, L, "Income-based purchase price (this tab)", style="label_b", align="left")
    s.put(r, 3, f"={R('PRICE')}", style="calc", fmt=F_ACCT_TOP, align="right", name="PX_INCOME")
    s.put(r, 4, "what the combined cash flows support", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "HBU covered-land acquisition (Assemblage tab)", style="label_b", align="left")
    s.put(r, 3, "='Assemblage'!" + regs["Assemblage"]["ACQ"], style="calc", color="008000", fmt=F_ACCT_TOP, align="right", name="PX_HBU")
    s.put(r, 4, "land value + 20% assemblage premium to control", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "PREMIUM OVER INCOME VALUE (dirt + optionality)", style="grand", align="left")
    s.put(r, 3, f"={R('PX_HBU')}-{R('PX_INCOME')}", style="grand", fmt=F_ACCT_TOP, align="right", name="PREMIUM"); r += 1
    s.put(r, L, "Premium as % of income value", style="label", align="left")
    s.put(r, 3, f"={R('PREMIUM')}/{R('PX_INCOME')}", style="calc", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "Read", style="warn", align="left")
    s.put(r, 4, "The rent supports the income-based price; the covered-land price is the strategic control cost. Pay toward income value "
                "and treat the premium as the option cost on Live Local density — justified only if you intend to redevelop or flip the dirt.",
          style="warn", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
