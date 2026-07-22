"""
tab_capital.py — CAPITAL STACK & AFFORDABILITY (interactive, user-friendly).
Play with the capital stack — senior LTV/LTC, rate, amortization, DSCR/debt-yield
tests, a mezzanine layer, and equity — and watch two things move:
  (A) the STACK at each deal price (income price and covered-land price): how the
      dollars split into senior / mezz / equity, with DSCR, debt yield, LTC, blended
      cost of capital, and the GP/LP equity split; and
  (B) AFFORDABILITY / CAPACITY: given the equity you have, the biggest purchase price
      and the share of the assemblage you can control.
All inputs on this tab are a 🔵 sandbox (seeded to the Assumptions defaults, shown as a
green reference) so you can explore without touching the committed model. Every number
is closed-form and live; it validates headless.
"""
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import DataBarRule, ColorScaleRule
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR

L = 2
def CL(c): return get_column_letter(c)
HEAT = ColorScaleRule(start_type="min", start_color="F8696B",
                      mid_type="percentile", mid_value=50, mid_color="FFEB84",
                      end_type="max", end_color="63BE7B")


def build(s, regs):
    IV, A, AS = "Income Valuation", "Assemblage", "Assumptions"

    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"
    def x(sheet, name): return f"={cell(sheet, name)}"

    PX_INC = cell(IV, "PX_INCOME"); PX_CL = cell(A, "ACQ")
    ASIS = cell(IV, "ASIS_NOI"); CLOSE = cell(IV, "CLOSE"); RAW = cell(A, "RAW_COST")

    s.colw({"A": 2, "B": 32, "C": 13, "D": 14, "E": 11, "F": 3, "G": 14, "H": 11,
            "I": 11, "J": 11, "K": 11, "L": 11, "M": 11})
    r = 1
    s.put(r, L, "CAPITAL STACK  &  AFFORDABILITY", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "Play with leverage, rates & equity (🔵 blue sandbox) → see the stack at each price and how much you can afford. "
                "Change these to explore; to COMMIT a value, set it on the Assumptions tab.", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # ---------------- sandbox inputs ----------------
    s.section(r, L, 13, "CAPITAL-STACK INPUTS  —  🔵 sandbox (green = current model value for reference)"); r += 1
    s.put(r, L, "Lever", style="subhead", align="left")
    s.put(r, 3, "You", style="subhead", align="center")
    s.put(r, 4, "Model now", style="subhead", align="center")
    s.put(r, 5, "note", style="subhead", align="left", merge=(r, 13)); r += 1

    def sin(name, label, val, fmt, ref=None, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="center", name=name)
        if ref is not None:
            s.put(r, 4, f"={ref}", style="calc", color="008000", fmt=fmt, align="center")
        else:
            s.put(r, 4, "—", style="note", align="center")
        s.put(r, 5, note, style="note", align="left", merge=(r, 13)); r += 1

    s.put(r, L, "Senior debt", style="subhead", align="left", merge=(r, 13)); r += 1
    sin("LTV_S", "Max senior LTV (% of price)", 0.60, F_PCT1, cell(IV, "LTV"), "sizing constraint 1")
    sin("RATE_S", "Senior rate", 0.065, F_PCT2, cell(IV, "RATE"), "annual")
    sin("AMORT_S", "Amortization (yrs)", 30, F_YR, cell(IV, "AMORT"), "0 = interest-only")
    sin("DSCR_MIN", "Min DSCR", 1.30, F_MULT, cell(IV, "DSCRMIN"), "sizing constraint 2")
    sin("DY_MIN", "Min debt yield", 0.085, F_PCT1, cell(IV, "DYMIN"), "sizing constraint 3")
    s.put(r, L, "Mezzanine / preferred (optional)", style="subhead", align="left", merge=(r, 13)); r += 1
    sin("MEZZ_PCT", "Mezzanine (% of total cost)", 0.00, F_PCT1, None, "0 = none; a second debt layer")
    sin("MEZZ_RATE", "Mezzanine rate (interest-only)", 0.12, F_PCT2, None, "typically higher than senior")
    s.put(r, L, "Equity", style="subhead", align="left", merge=(r, 13)); r += 1
    sin("EQ_AVAIL", "Equity available ($)", 30000000, F_ACCT_TOP, cell(IV, "EQ_I"), "your check size — drives affordability")
    sin("GP_PCT", "GP / sponsor co-invest (% of equity)", 0.10, F_PCT1, None, "LP takes the balance")
    sin("PREF", "LP preferred return", 0.08, F_PCT1, None, "hurdle before promote (reference)")
    r += 1

    g = s.reg
    # local input coord refs (registry maps name -> cell coordinate string)
    LTV_S = g["LTV_S"]; RATE_S = g["RATE_S"]; AMORT_S = g["AMORT_S"]
    DSCR_MIN = g["DSCR_MIN"]; DY_MIN = g["DY_MIN"]
    MEZZ_PCT = g["MEZZ_PCT"]; MEZZ_RATE = g["MEZZ_RATE"]
    EQ_AVAIL = g["EQ_AVAIL"]; GP_PCT = g["GP_PCT"]

    # local mortgage constant (interest-only if amort = 0)
    s.section(r, L, 13, "DERIVED"); r += 1
    s.put(r, L, "Senior monthly rate", style="label", align="left")
    s.put(r, 3, f"={RATE_S}/12", style="calc", fmt=F_PCT2, align="center", name="MR_S"); r += 1
    MR_S = g["MR_S"]
    s.put(r, L, "Senior mortgage constant (annual)", style="label", align="left")
    s.put(r, 3, f"=IF({AMORT_S}=0,{RATE_S},({MR_S}/(1-(1+{MR_S})^(-{AMORT_S}*12)))*12)", style="calc", fmt=F_PCT2, align="center", name="MCONST_S")
    s.put(r, 4, "debt service ÷ loan (IO if amort = 0)", style="note", align="left", merge=(r, 13)); r += 1
    MCONST_S = g["MCONST_S"]
    r += 1

    # ---------------- MODE A: stack at each deal price ----------------
    s.section(r, L, 13, "①  THE STACK AT EACH DEAL PRICE  —  how the dollars split  (live)"); r += 1
    s.put(r, L, "", style="subhead", align="left")
    s.put(r, 4, "INCOME PRICE", style="subhead", align="center", merge=(r, 5))
    s.put(r, 7, "COVERED-LAND PRICE", style="subhead", align="center", merge=(r, 8)); r += 1
    s.put(r, L, "Component", style="subhead", align="left")
    s.put(r, 4, "$", style="subhead", align="center")
    s.put(r, 5, "% cost", style="subhead", align="center")
    s.put(r, 7, "$", style="subhead", align="center")
    s.put(r, 8, "% cost", style="subhead", align="center"); r += 1

    # for a price expression P, build the sized pieces
    def SENIOR(P):
        return f"MIN({LTV_S}*{P},{ASIS}/({DSCR_MIN}*{MCONST_S}),{ASIS}/{DY_MIN})"
    def MEZZ(P):  return f"({MEZZ_PCT}*{P})"
    def COST(P):  return f"({P}*(1+{CLOSE}))"
    def EQ(P):    return f"({COST(P)}-{SENIOR(P)}-{MEZZ(P)})"

    Pi, Pc = PX_INC, PX_CL
    # rows: capture the % rows for data-bar formatting
    def stackrow(label, fi, fc, style="calc", pct_i=None, pct_c=None, fmt=F_ACCT, bold=False):
        nonlocal r
        st = "subtotal" if bold else "label"
        s.put(r, L, label, style=st, align="left")
        s.put(r, 4, fi, style=style, fmt=fmt, align="right", bold=bold)
        if pct_i is not None: s.put(r, 5, pct_i, style=style, fmt=F_PCT1, align="center")
        s.put(r, 7, fc, style=style, fmt=fmt, align="right", bold=bold)
        if pct_c is not None: s.put(r, 8, pct_c, style=style, fmt=F_PCT1, align="center")
        rr = r; r += 1
        return rr

    stackrow("Purchase price", f"={Pi}", f"={Pc}", fmt=F_ACCT_TOP)
    stackrow("＋ Closing & acq costs", f"={Pi}*{CLOSE}", f"={Pc}*{CLOSE}")
    row_cost = stackrow("＝ Total uses (cost)", f"={COST(Pi)}", f"={COST(Pc)}", fmt=F_ACCT_TOP, bold=True)
    ci = f"{CL(4)}{row_cost}"; cc = f"{CL(7)}{row_cost}"
    row_sen = stackrow("Senior debt (sized, lesser-of)", f"={SENIOR(Pi)}", f"={SENIOR(Pc)}",
                       pct_i=f"={SENIOR(Pi)}/{ci}", pct_c=f"={SENIOR(Pc)}/{cc}")
    row_mez = stackrow("Mezzanine", f"={MEZZ(Pi)}", f"={MEZZ(Pc)}",
                       pct_i=f"={MEZZ(Pi)}/{ci}", pct_c=f"={MEZZ(Pc)}/{cc}")
    row_eq = stackrow("Equity (plug)", f"={EQ(Pi)}", f"={EQ(Pc)}",
                      pct_i=f"={EQ(Pi)}/{ci}", pct_c=f"={EQ(Pc)}/{cc}", bold=True)
    # data bars on the % columns for a visual stack
    s.ws.conditional_formatting.add(f"E{row_sen}:E{row_eq}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="4F81BD"))
    s.ws.conditional_formatting.add(f"H{row_sen}:H{row_eq}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="C0504D"))
    r += 1

    # metrics under the stack
    s.put(r, L, "Loan-to-cost (senior + mezz)", style="label", align="left")
    s.put(r, 4, f"=({SENIOR(Pi)}+{MEZZ(Pi)})/{ci}", style="calc", fmt=F_PCT1, align="right")
    s.put(r, 7, f"=({SENIOR(Pc)}+{MEZZ(Pc)})/{cc}", style="calc", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "Year-1 DSCR (senior)", style="label", align="left")
    s.put(r, 4, f"={ASIS}/({SENIOR(Pi)}*{MCONST_S})", style="calc", fmt=F_MULT, align="right")
    s.put(r, 7, f"={ASIS}/({SENIOR(Pc)}*{MCONST_S})", style="calc", fmt=F_MULT, align="right"); r += 1
    s.put(r, L, "Debt yield (senior)", style="label", align="left")
    s.put(r, 4, f"={ASIS}/{SENIOR(Pi)}", style="calc", fmt=F_PCT1, align="right")
    s.put(r, 7, f"={ASIS}/{SENIOR(Pc)}", style="calc", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "Blended cost of debt", style="label", align="left")
    s.put(r, 4, f"=IFERROR(({SENIOR(Pi)}*{RATE_S}+{MEZZ(Pi)}*{MEZZ_RATE})/({SENIOR(Pi)}+{MEZZ(Pi)}),{RATE_S})", style="calc", fmt=F_PCT2, align="right")
    s.put(r, 7, f"=IFERROR(({SENIOR(Pc)}*{RATE_S}+{MEZZ(Pc)}*{MEZZ_RATE})/({SENIOR(Pc)}+{MEZZ(Pc)}),{RATE_S})", style="calc", fmt=F_PCT2, align="right"); r += 1
    s.put(r, L, "  GP / sponsor equity", style="note", align="left")
    s.put(r, 4, f"={EQ(Pi)}*{GP_PCT}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 7, f"={EQ(Pc)}*{GP_PCT}", style="calc", fmt=F_ACCT, align="right"); r += 1
    s.put(r, L, "  LP equity", style="note", align="left")
    s.put(r, 4, f"={EQ(Pi)}*(1-{GP_PCT})", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 7, f"={EQ(Pc)}*(1-{GP_PCT})", style="calc", fmt=F_ACCT, align="right"); r += 1
    s.put(r, L, "Levered IRR at this price (from model)", style="label", align="left")
    s.put(r, 4, x(IV, "IRRL_I"), style="calc", color="008000", fmt=F_PCT1, align="right")
    s.put(r, 7, x(IV, "IRRL_H"), style="calc", color="008000", fmt=F_PCT1, align="right"); r += 2

    # ---------------- MODE B: affordability / capacity ----------------
    s.section(r, L, 13, "②  AFFORDABILITY  —  what your equity can buy  (live)"); r += 1
    # equity share of cost = 1 - senior LTC target - mezz%. Use senior LTV as its cost share proxy.
    s.put(r, L, "Total debt as % of cost (senior LTV + mezz)", style="label", align="left")
    s.put(r, 3, f"={LTV_S}+{MEZZ_PCT}", style="calc", fmt=F_PCT1, align="center", name="LTC_TGT"); r += 1
    LTC_TGT = g["LTC_TGT"]
    s.put(r, L, "Equity share of cost", style="label", align="left")
    s.put(r, 3, f"=1-{LTC_TGT}", style="calc", fmt=F_PCT1, align="center", name="EQ_SHARE"); r += 1
    EQ_SHARE = g["EQ_SHARE"]
    s.put(r, L, "Max total cost you can fund", style="label_b", align="left")
    s.put(r, 3, f"={EQ_AVAIL}/{EQ_SHARE}", style="calc", fmt=F_ACCT_TOP, align="center", name="MAX_COST"); r += 1
    MAX_COST = g["MAX_COST"]
    s.put(r, L, "→ MAX PURCHASE PRICE", style="grand", align="left")
    s.put(r, 3, f"={MAX_COST}/(1+{CLOSE})", style="grand", fmt=F_ACCT_TOP, align="center", name="MAX_PRICE")
    s.put(r, 4, "the biggest price your equity + this leverage supports", style="note", align="left", merge=(r, 13)); r += 1
    MAX_PRICE = g["MAX_PRICE"]
    s.put(r, L, "DSCR / debt-yield check at that price", style="label", align="left")
    s.put(r, 3, f'=IF(AND({ASIS}/(({LTV_S}*{MAX_PRICE})*{MCONST_S})>={DSCR_MIN},{ASIS}/({LTV_S}*{MAX_PRICE})>={DY_MIN}),"OK — debt tests pass","⚠ senior would be cut by DSCR/DY (income-limited)")',
          style="calc", align="left", merge=(r, 13)); r += 2

    # capacity vs the three prices
    s.put(r, L, "Assemblage capacity", style="subhead", align="left")
    s.put(r, 3, "Price", style="subhead", align="center")
    s.put(r, 4, "Your max vs it", style="subhead", align="center")
    s.put(r, 6, "Equity to control it", style="subhead", align="center", merge=(r, 7))
    s.put(r, 8, "Equity gap", style="subhead", align="center", merge=(r, 9)); r += 1
    for label, Pexpr in [("Income price", PX_INC), ("Sum-of-parts (raw cost)", RAW), ("Covered-land price", PX_CL)]:
        s.put(r, L, "  " + label, style="label", align="left")
        s.put(r, 3, f"={Pexpr}", style="calc", color="008000", fmt=F_ACCT, align="center")
        s.put(r, 4, f"={MAX_PRICE}/{Pexpr}", style="calc", fmt=F_PCT1, align="center")
        need = f"({Pexpr}*(1+{CLOSE})*{EQ_SHARE})"
        s.put(r, 6, f"={need}", style="calc", fmt=F_ACCT, align="right", merge=(r, 7))
        s.put(r, 8, f"={need}-{EQ_AVAIL}", style="calc", fmt=F_ACCT, align="right", merge=(r, 9)); r += 1
    s.put(r, L, "Read", style="note", align="left")
    s.put(r, 4, "‘Your max vs it’ = what share of that price your equity covers at this leverage. "
                "‘Equity gap’ > 0 = additional equity needed to control it; < 0 = headroom.", style="note", align="left", merge=(r, 13)); r += 2

    # ---------------- capacity sensitivity grid ----------------
    s.section(r, L, 13, "③  PURCHASE CAPACITY ($M)  —  equity available (rows) × total leverage (cols)  🔵 editable axes"); r += 1
    s.put(r, L, "Equity ╲ leverage", style="subhead", align="center")
    levs = [0.45, 0.55, 0.60, 0.65, 0.70]
    for j, lv in enumerate(levs):
        s.put(r, 4 + j, lv, style="input", fmt=F_PCT1, align="center")
    hlev = r; r += 1
    eqs = [15000000, 25000000, 35000000, 50000000, 75000000]
    top = r
    for e in eqs:
        s.put(r, L, e, style="input", fmt=F_ACCT, align="center")
        for j in range(len(levs)):
            lv = f"{CL(4+j)}{hlev}"; E = f"{CL(L)}{r}"
            s.put(r, 4 + j, f"={E}/(1-{lv})/(1+{CLOSE})/1000000", style="calc", fmt="#,##0.0", align="center")
        r += 1
    s.ws.conditional_formatting.add(f"D{top}:H{r-1}", HEAT)
    s.put(r, L, "Max purchase price ($M) = equity ÷ (1 − leverage) ÷ (1 + closing). Green = more buying power.", style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
