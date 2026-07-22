"""
tab_review.py — REVIEW BOARD (interactive sensitivity war-room).
A single high-level page for the investment committee: live headline KPIs, the
key levers (current values, linked from the Assumptions control tab), one-way
sensitivity ladders, a two-way levered-return grid, a driver tornado, and the
scenario band. Every sensitivity is CLOSED-FORM (no Excel data tables) so it
recalculates live and validates headless. Blue axis/­band cells are yours to
flex — change them here, or change the driver on Assumptions, and the board moves.

Reversion is anchored to the ACTUAL consolidated reversion (REV_BASE) so every
grid reproduces the headline levered multiple at base — critical here because
two of five parcels (Publix, Land) exit at LAND VALUE, not an income cap, so an
income-cap reversion would badly understate the exit. The exit-cap axis scales
that anchored reversion by SCAP/xc (a board simplification: it also flexes the
land-exit parcels with cap; footnoted on the tab).
"""
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR

L = 2
def CL(c): return get_column_letter(c)
HEAT = ColorScaleRule(start_type="min", start_color="F8696B",
                      mid_type="percentile", mid_value=50, mid_color="FFEB84",
                      end_type="max", end_color="63BE7B")


def build(s, regs):
    IV, A, SC, AS = "Income Valuation", "Assemblage", "Scenarios", "Assumptions"

    def cell(sheet, name):
        return f"'{sheet}'!{regs[sheet][name]}"
    def x(sheet, name):
        return f"={cell(sheet, name)}"

    # base-case links (Income Valuation engine) used throughout the closed-form grids
    ASIS = cell(IV, "ASIS_NOI"); PRICE = cell(IV, "PRICE")
    SUMOP = cell(IV, "SUMOP5"); REVB = cell(IV, "REV_BASE")
    COS = cell(IV, "COS"); CLOSE = cell(IV, "CLOSE")
    MCONST = cell(IV, "MCONST"); MRATE = cell(IV, "MRATE"); H = cell(IV, "HOLD")
    LTV = cell(IV, "LTV"); LDSCR = cell(IV, "L_DSCR"); LDY = cell(IV, "L_DY")
    LOAN = cell(IV, "LOAN"); DS = cell(IV, "DS"); LBAL5 = cell(IV, "LBAL5")
    EQ = cell(IV, "EQ_I"); SCAP = cell(IV, "SCAP")
    AMORT = cell(IV, "AMORT"); RAW = cell(A, "RAW_COST"); EMBASE = cell(IV, "EML_I")

    # closed-form levered equity-multiple pieces, anchored to REV_BASE so base ties to headline
    def loanP(P):         return f"MIN({P}*{LTV},{LDSCR},{LDY})"
    def balf(ln, ds, mr): return f"({ln}*(1+{mr})^(12*{H})-({ds}/12)*((1+{mr})^(12*{H})-1)/{mr})"
    def revcap(xc):       return f"({REVB}*{SCAP}/{xc})"          # exit-cap-anchored reversion
    def emf(op, ds, rev, bal, eq): return f"=({op}-{H}*{ds}+{rev}-{bal})/{eq}"

    s.colw({"A": 2, "B": 30, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "REVIEW BOARD  —  KEY SENSITIVITIES  &  WHAT-IF", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "DAWN RE · E Sunrise Blvd Assemblage · flex a blue lever here (or on the Assumptions tab) and every number on this page recomputes live",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 16); r += 2

    # ---------------- live KPI strip ----------------
    s.section(r, L, 13, "HEADLINE  (live)"); r += 1
    kpis = [
        ("Income price", x(IV, "PX_INCOME"), F_ACCT_TOP),
        ("Covered-land price", x(A, "ACQ"), F_ACCT_TOP),
        ("Premium (dirt)", x(IV, "PREMIUM"), F_ACCT_TOP),
        ("Levered IRR (income)", x(IV, "IRRL_I"), F_PCT1),
        ("Unlevered IRR", x(IV, "IRRU_I"), F_PCT1),
        ("Levered EM", x(IV, "EML_I"), F_MULT),
        ("Yr-1 DSCR", x(IV, "DSCR_I"), F_MULT),
        ("Break-even exit cap", x(IV, "BE_EXITCAP"), F_PCT2),
    ]
    c = L
    for lab, f, fmt in kpis:
        endc = c + 2 if lab == "Break-even exit cap" else c + 1
        s.put(r, c, lab, style="kpi_lab", align="center", merge=(r, endc))
        s.put(r + 1, c, f, style="kpi_val", fmt=fmt, align="center", merge=(r + 1, endc))
        c = endc + 1
    s.rowh(r, 13); s.rowh(r + 1, 22); r += 3

    # ---------------- key levers (current values, linked) ----------------
    s.section(r, L, 13, "KEY LEVERS  —  current value linked from Assumptions  (change there → whole model moves)"); r += 1
    s.put(r, L, "Lever", style="subhead", align="left")
    s.put(r, 4, "Now", style="subhead", align="center")
    s.put(r, 5, "Drives", style="subhead", align="left", merge=(r, 13)); r += 1
    levers = [
        ("Blended going-in cap (as-is)", AS, "CAP", F_PCT2, "income price = as-is NOI ÷ this"),
        ("Stabilized / exit cap", AS, "SCAP", F_PCT2, "reversion & exit value"),
        ("NOI growth", AS, "GROW", F_PCT1, "forward NOI, reversion"),
        ("Senior rate", AS, "RATE", F_PCT2, "debt service, levered return"),
        ("Max senior LTV", AS, "LTV", F_PCT1, "leverage / equity check"),
        ("Hold (yrs)", AS, "HOLD", F_YR, "exit year"),
        ("Assemblage premium (base)", AS, "PREM_BASE", F_PCT1, "covered-land price over sum-of-parts"),
        ("Target unlevered yield (DCF)", AS, "TYLD", F_PCT1, "DCF cross-check value"),
    ]
    for lab, sh, nm, fmt, drv in levers:
        s.put(r, L, lab, style="label", align="left")
        s.put(r, 4, x(sh, nm), style="calc", color="008000", fmt=fmt, align="center")
        s.put(r, 5, drv, style="note", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---------------- one-way ladders (live, closed-form) ----------------
    s.section(r, L, 13, "ONE-WAY SENSITIVITY  —  🔵 blue axis points are editable"); r += 1

    # (a) income price vs blended going-in cap
    s.put(r, L, "① Income price ($M)  vs. blended going-in cap", style="subhead", align="left", merge=(r, 13)); r += 1
    caps = [0.055, 0.060, 0.065, 0.070, 0.075]
    for j, cp in enumerate(caps):
        s.put(r, 4 + j, cp, style="input", fmt=F_PCT2, align="center")
    axis_cap = r; r += 1
    for j in range(len(caps)):
        s.put(r, 4 + j, f"={ASIS}/{CL(4+j)}{axis_cap}/1000000", style="calc", fmt="#,##0.0", align="center")
    s.put(r, L, "  price", style="note", align="left")
    s.ws.conditional_formatting.add(f"{CL(4)}{r}:{CL(8)}{r}", HEAT); r += 2

    # (b) covered-land price vs assemblage premium
    s.put(r, L, "② Covered-land price ($M)  vs. assemblage premium", style="subhead", align="left", merge=(r, 13)); r += 1
    prems = [0.10, 0.15, 0.20, 0.25, 0.30]
    for j, pm in enumerate(prems):
        s.put(r, 4 + j, pm, style="input", fmt=F_PCT1, align="center")
    axis_prem = r; r += 1
    for j in range(len(prems)):
        s.put(r, 4 + j, f"={RAW}*(1+{CL(4+j)}{axis_prem})/1000000", style="calc", fmt="#,##0.0", align="center")
    s.put(r, L, "  price", style="note", align="left")
    s.ws.conditional_formatting.add(f"{CL(4)}{r}:{CL(8)}{r}", HEAT); r += 2

    # (c) levered equity multiple vs exit cap  (at base income price; reversion anchored to REV_BASE)
    s.put(r, L, "③ Levered equity multiple  vs. exit cap  (at income price)", style="subhead", align="left", merge=(r, 13)); r += 1
    xcaps = [0.060, 0.065, 0.070, 0.075, 0.080]
    for j, xc in enumerate(xcaps):
        s.put(r, 4 + j, xc, style="input", fmt=F_PCT2, align="center")
    axis_xc = r; r += 1
    for j in range(len(xcaps)):
        s.put(r, 4 + j, emf(SUMOP, DS, revcap(f"{CL(4+j)}{axis_xc}"), LBAL5, EQ), style="calc", fmt=F_MULT, align="center")
    s.put(r, L, "  EM", style="note", align="left")
    s.ws.conditional_formatting.add(f"{CL(4)}{r}:{CL(8)}{r}", HEAT); r += 2

    # ---------------- two-way grid (live, closed-form) ----------------
    s.section(r, L, 13, "TWO-WAY  —  levered equity multiple  ·  purchase price (rows) × exit cap (cols)  🔵 editable axes"); r += 1
    s.put(r, L, "Price ╲ exit cap", style="subhead", align="center")
    xcaps2 = [0.060, 0.065, 0.070, 0.075, 0.080]
    for j, xc in enumerate(xcaps2):
        s.put(r, 4 + j, xc, style="input", fmt=F_PCT2, align="center")
    hx = r; r += 1
    prices = [60000000, 70000000, 85000000, 100000000, 122000000]
    top2 = r
    for p in prices:
        s.put(r, L, p, style="input", fmt=F_ACCT, align="center")
        for j in range(len(xcaps2)):
            xc = f"{CL(4+j)}{hx}"
            P = f"{CL(L)}{r}"
            ln = loanP(P)
            ds = f"({ln}*{MCONST})"
            bal = balf(ln, ds, MRATE)
            eq = f"({P}*(1+{CLOSE})-{ln})"
            s.put(r, 4 + j, emf(SUMOP, ds, revcap(xc), bal, eq), style="calc", fmt=F_MULT, align="center")
        r += 1
    s.ws.conditional_formatting.add(f"{CL(4)}{top2}:{CL(8)}{r-1}", HEAT)
    s.put(r, L, "income price ≈ row 2 · covered-land price ≈ row 5 · reversion anchored to actual (incl. land-value exits)",
          style="note", align="left", merge=(r, 13)); r += 2

    # ---------------- driver tornado (levered EM, one driver flexed at a time) ----------------
    s.section(r, L, 13, "DRIVER TORNADO  —  swing in levered equity multiple, one lever flexed low↔high (others at base)  🔵 bands editable"); r += 1
    s.put(r, L, "Lever", style="subhead", align="left")
    s.put(r, 4, "Low", style="subhead", align="center")
    s.put(r, 5, "EM@Low", style="subhead", align="center")
    s.put(r, 6, "EM@Base", style="subhead", align="center")
    s.put(r, 7, "High", style="subhead", align="center")
    s.put(r, 8, "EM@High", style="subhead", align="center")
    s.put(r, 9, "Swing", style="subhead", align="center")
    s.put(r, 10, "note", style="subhead", align="left", merge=(r, 13)); r += 1

    def em_exitcap(xc):     # reversion scales with cap (anchored)
        return emf(SUMOP, DS, revcap(xc), LBAL5, EQ)
    def em_price(P):        # price → loan, ds, bal, eq (reversion at base)
        ln = loanP(P); ds = f"({ln}*{MCONST})"; bal = balf(ln, ds, MRATE); eq = f"({P}*(1+{CLOSE})-{ln})"
        return emf(SUMOP, ds, REVB, bal, eq)
    def em_ltv(lv):         # loan → ds, bal, eq (price at base)
        ln = f"MIN({PRICE}*{lv},{LDSCR},{LDY})"; ds = f"({ln}*{MCONST})"; bal = balf(ln, ds, MRATE); eq = f"({PRICE}*(1+{CLOSE})-{ln})"
        return emf(SUMOP, ds, REVB, bal, eq)
    def em_rate(rt):        # mortgage constant + monthly rate (LTV binding → loan at base)
        mr = f"({rt}/12)"; mc = f"({mr}/(1-(1+{mr})^(-{AMORT}*12))*12)"
        ds = f"({LOAN}*{mc})"; bal = balf(LOAN, ds, mr)
        return emf(SUMOP, ds, REVB, bal, EQ)
    def em_op(ph):          # operating cash-flow ±% (scales Σ op CF)
        return emf(f"({ph}*{SUMOP})", DS, REVB, LBAL5, EQ)

    # (label, low, high, fmt, em(cellref)) — low/high are blue inputs
    trows = [
        ("Exit cap", 0.060, 0.080, F_PCT2, em_exitcap, "softer exit → reversion falls (incl. land)"),
        ("Purchase price", 60000000, 85000000, F_ACCT, em_price, "pay less → higher multiple"),
        ("Senior rate", 0.055, 0.080, F_PCT2, em_rate, "cost of debt"),
        ("Senior LTV", 0.50, 0.70, F_PCT1, em_ltv, "more debt → more levered"),
        ("Op cash flow (×)", 0.90, 1.10, F_MULT, em_op, "NOI / carry achievement ±10%"),
    ]
    tor_first = r
    for lab, lo, hi, fmt, emfn, note in trows:
        s.put(r, L, lab, style="label", align="left")
        s.put(r, 4, lo, style="input", fmt=fmt, align="center")
        s.put(r, 5, emfn(f"{CL(4)}{r}"), style="calc", fmt=F_MULT, align="center")
        s.put(r, 6, f"={EMBASE}", style="calc", color="008000", fmt=F_MULT, align="center")
        s.put(r, 7, hi, style="input", fmt=fmt, align="center")
        s.put(r, 8, emfn(f"{CL(7)}{r}"), style="calc", fmt=F_MULT, align="center")
        s.put(r, 9, f"=ABS({CL(8)}{r}-{CL(5)}{r})", style="calc", fmt=F_MULT, align="center")
        s.put(r, 10, note, style="note", align="left", merge=(r, 13)); r += 1
    s.ws.conditional_formatting.add(f"{CL(9)}{tor_first}:{CL(9)}{r-1}", HEAT); r += 1

    # ---------------- scenario band (linked) ----------------
    s.section(r, L, 13, "SCENARIO BAND  —  Downside / Base / Upside levered IRR  (full consolidated cash flows on the Scenarios tab)"); r += 1
    s.put(r, L, "Levered IRR (income price)", style="label_b", align="left")
    s.put(r, 5, "Downside", style="subhead", align="center")
    s.put(r, 6, "Base", style="subhead", align="center")
    s.put(r, 7, "Upside", style="subhead", align="center", merge=(r, 8)); r += 1
    s.put(r, L, "  IRR", style="note", align="left")
    s.put(r, 5, x(SC, "IRRL_DOWN"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 6, x(IV, "IRRL_I"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 7, x(SC, "IRRL_UP"), style="calc", color="008000", fmt=F_PCT1, align="center", merge=(r, 8)); r += 1
    s.put(r, L, "At the COVERED-LAND price", style="warn", align="left")
    s.put(r, 4, x(IV, "IRRL_H"), style="warn", fmt=F_PCT1, align="center")
    s.put(r, 5, f'=IF({cell(IV,"IRRL_H")}<0,"income case loses money at this price — the return is land appreciation / redevelopment only","thin income return — land optionality drives it")',
          style="warn", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Land CAGR needed to justify the premium", style="label", align="left")
    s.put(r, 4, x(IV, "BE_APPREC"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 5, "annual land-value growth over the hold to break even on the dirt premium", style="note", align="left", merge=(r, 13)); r += 2

    s.put(r, L, "How to read", style="note", align="left")
    s.put(r, 4, "Every grid is closed-form and live, anchored so the base case reproduces the headline multiple. Edit a 🔵 blue axis/band "
                "cell to reshape a table, or change the underlying lever on the Assumptions tab to move the whole board (and the model) at once.",
          style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
