"""
tab_scenarios.py — DOWNSIDE / BASE / UPSIDE scenario analysis.
Holds the acquisition at the base income price and stresses the business plan:
NOI achievement, exit cap, and financing rate. Each scenario is a full
consolidated cash flow (unlevered + levered) with its own IRR / multiple /
DSCR / cash-on-cash — the format an investment committee decides on.
"""
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_YR

L = 2
ACQ = 3
def pc(y): return 3 + y
def CL(c): return get_column_letter(c)
def _row(coord): return int("".join(c for c in coord if c.isdigit()))
HEAT = ColorScaleRule(start_type="min", start_color="F8696B",
                      mid_type="percentile", mid_value=50, mid_color="FFEB84",
                      end_type="max", end_color="63BE7B")

# scenario, NOI factor, exit cap, senior rate
SCEN = [("Downside", 0.92, 0.0725, 0.0725),
        ("Base",     1.00, 0.0675, 0.0650),
        ("Upside",   1.06, 0.0625, 0.0600)]


def build(s, regs):
    iv = regs["Income Valuation"]
    def C(n): return f"'Income Valuation'!{iv[n]}"
    op = _row(iv["ROW_OPCF"])                      # income-tab operating-CF row
    def opcf(y): return f"'Income Valuation'!{CL(pc(y))}{op}"
    s.colw({"A": 2.5, "B": 30, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "SCENARIO ANALYSIS  —  DOWNSIDE / BASE / UPSIDE", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "Acquisition held at the base income price; the business plan is stressed on NOI achievement, exit cap, and financing rate. "
                "Each case is a full consolidated cash flow with its own levered/unlevered return.",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    # ---- scenario inputs ----
    s.section(r, L, 13, "SCENARIO DRIVERS  —  🔵 blue inputs"); r += 1
    s.put(r, L, "Scenario", style="subhead", align="left")
    s.put(r, 3, "NOI achieved", style="subhead", align="center")
    s.put(r, 4, "Exit cap", style="subhead", align="center")
    s.put(r, 5, "Senior rate", style="subhead", align="center"); r += 1
    scen_rows = {}
    for nm, fac, xc, rt in SCEN:
        scen_rows[nm] = r
        s.put(r, L, nm, style="label_b", align="left")
        s.put(r, 3, fac, style="input", fmt="0%", align="center")
        s.put(r, 4, xc, style="input", fmt=F_PCT2, align="center")
        s.put(r, 5, rt, style="input", fmt=F_PCT2, align="center")
        r += 1
    s.put(r, L, "Base income price (fixed basis)", style="note", align="left")
    s.put(r, 3, f"={C('PRICE')}", style="calc", color="008000", fmt=F_ACCT, align="right")
    s.put(r, 5, "loan & equity held fixed; only the senior rate varies debt service across cases", style="note", align="left", merge=(r, 13)); r += 2

    # ---- per-scenario cash flows ----
    s.section(r, L, 13, "CONSOLIDATED CASH FLOW BY SCENARIO  (unlevered & levered)"); r += 1
    s.put(r, L, "Year", style="subhead", align="left")
    s.put(r, ACQ, "0/Acq", style="subhead", align="center")
    for y in range(1, 11): s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1

    hold = C("HOLD"); grow = C("GROW"); cos = C("COS"); close = C("CLOSE")
    orig = C("ORIG"); loan = C("LOAN"); exitnoi = C("EXITNOI"); asis = C("ASIS_NOI"); cap = C("CAP")
    amort = C("AMORT"); revbase = C("REV_BASE")
    base_xc = f"{CL(4)}{scen_rows['Base']}"    # Base-case exit cap — anchors reversion to the headline
    cf = {}   # scenario -> dict(unlev=row, lev=row, mr, mc, ds, bal, eq)
    for nm, _, _, _ in SCEN:
        sr = scen_rows[nm]
        fac = f"{CL(3)}{sr}"; xc = f"{CL(4)}{sr}"; rt = f"{CL(5)}{sr}"
        mr = f"({rt}/12)"
        mc = f"({mr}/(1-(1+{mr})^(-{amort}*12))*12)"
        ds = f"({loan}*{mc})"
        bal = f"({loan}*(1+{mr})^(12*{hold})-({ds}/12)*((1+{mr})^(12*{hold})-1)/{mr})"
        eq = f"({C('PRICE')}*(1+{close})+{orig}*{loan}-{loan})"
        # reversion anchored to the headline base reversion (asset-specific caps),
        # scaled by NOI achievement and the exit-cap move → Base ties to Income Valuation exactly
        rev = f"({revbase}*{fac}*{base_xc}/{xc})"
        # unlevered
        s.put(r, L, f"  {nm} — unlevered CF", style="note", align="left")
        s.put(r, ACQ, f"=-{C('PRICE')}*(1+{close})", style="calc", fmt=F_ACCT, align="right")
        for y in range(1, 11):
            s.put(r, pc(y), f"=IF({y}<={hold},{opcf(y)}*{fac},0)+IF({y}={hold},{rev},0)",
                  style="calc", fmt=F_ACCT, align="right")
        u = r; r += 1
        # levered
        s.put(r, L, f"  {nm} — levered CF", style="note", align="left")
        s.put(r, ACQ, f"=-{eq}", style="calc", fmt=F_ACCT, align="right")
        for y in range(1, 11):
            s.put(r, pc(y), f"=IF({y}<={hold},{opcf(y)}*{fac}-{ds},0)+IF({y}={hold},{rev}-{bal},0)",
                  style="calc", fmt=F_ACCT, align="right")
        lv = r; r += 1
        cf[nm] = dict(u=u, lv=lv, ds=ds, eq=eq, fac=fac, xc=xc)
    r += 1

    # ---- summary ----
    s.section(r, L, 13, "SCENARIO SUMMARY  —  returns at the base income price"); r += 1
    cols = ["Scenario", "Income value", "Unlev IRR", "Lev IRR", "Lev EM", "Yr-1 DSCR", "Avg CoC"]
    cpos = [L, 4, 6, 7, 8, 9, 10]
    span = {4: 5}
    for h, c in zip(cols, cpos):
        s.put(r, c, h, style="subhead", align="left" if c == L else "center",
              merge=(r, span[c]) if c in span else None)
    r += 1
    sum_top = r
    for nm, _, _, _ in SCEN:
        d = cf[nm]
        fac = d["fac"]
        st = "total" if nm == "Base" else "label"
        s.put(r, L, nm, style=st, align="left")
        s.put(r, 4, f"={asis}*{fac}/{cap}", style=("calc" if nm != "Base" else "total"), fmt=F_ACCT, align="right", merge=(r, 5))
        s.put(r, 6, f"=IRR({CL(ACQ)}{d['u']}:{CL(pc(10))}{d['u']})", style=("calc" if nm != "Base" else "total"), fmt=F_PCT1, align="center")
        s.put(r, 7, f"=IRR({CL(ACQ)}{d['lv']}:{CL(pc(10))}{d['lv']})", style=("calc" if nm != "Base" else "total"), fmt=F_PCT1, align="center")
        s.put(r, 8, f"=SUM({CL(pc(1))}{d['lv']}:{CL(pc(10))}{d['lv']})/{d['eq']}", style=("calc" if nm != "Base" else "total"), fmt=F_MULT, align="center")
        s.put(r, 9, f"={asis}*{fac}/{d['ds']}", style=("calc" if nm != "Base" else "total"), fmt=F_MULT, align="center")
        s.put(r, 10, f"=({C('SUMOP5')}*{d['fac']}-{hold}*{d['ds']})/{hold}/{d['eq']}",
              style=("calc" if nm != "Base" else "total"), fmt=F_PCT1, align="center", merge=(r, 13))
        r += 1
    s.ws.conditional_formatting.add(f"G{sum_top}:H{r-1}", HEAT)
    # expose scenario levered IRRs
    s.reg["IRRL_DOWN"] = f"G{sum_top}"
    s.reg["IRRL_UP"] = f"G{sum_top+2}"
    r += 1
    s.put(r, L, "Read", style="warn", align="left")
    s.put(r, 4, "Downside stresses NOI −8%, exit cap +50 bps, and rate +75 bps simultaneously (a compound recession case). "
                "The base case is highlighted; the levered IRR range brackets the deal for the investment committee.",
          style="warn", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
