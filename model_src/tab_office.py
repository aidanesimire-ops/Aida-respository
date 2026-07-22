"""
tab_office.py — Galleria Corporate Centre office condominium.
Two dominant owners; the deal question is the value of each owner's LEASED
position. Modified-Gross office income (landlord pays opex, no NNN recoveries).
Full 10-yr DCF, unlevered + levered returns, per-owner lease valuation, P&L.
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR)

L = 2
ACQ = 3
def pc(y): return 3 + y
def CL(c): return get_column_letter(c)

A = dict(
    gla=168807, occ0=0.85, stab_occ=0.88,
    market_rent=26.00,        # $/SF Modified Gross
    rent_growth=0.03, credit_loss=0.03, millage=0.0191,
    opex_psf=8.00,            # office opex ex-taxes (utilities, R&M, ins, CAM) — landlord pays (MG)
    mgmt_pct=0.03, exp_growth=0.03, reserve_psf=0.20,
    price=21700000, closing_pct=0.02, ltv=0.55, loan_rate=0.0750, amort=30,
    goingin_cap=0.080, exit_cap=0.0825, cost_sale=0.02, hold=5, disc=0.10,
    land_sf=None,
    sale_comp_psf=300.00,
)

OWNERS = [
    ("Main Street Fund LLC", "Grove Gate affiliate", 96930, 0.574, 10000000,
     "Bought 57.4% + 2 parking lots for $10.0M (Sept 2019) — dominant owner / lessor"),
    ("International Sunrise Partners LLC", "Bush Development entity", 71877, 0.426, None,
     "Prior bulk owner (2011 condo-conversion sponsor); retains the balance of units"),
]


def build(s, amap=None):
    amap = amap or {}
    a = A
    s.colw({"A": 2.5, "B": 34, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "GALLERIA CORPORATE CENTRE  ·  OFFICE CONDOMINIUM", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "2455 E Sunrise Blvd   |   13-story Class B office condo · ~168,807 SF · built 1973 (renov. 2007) "
                "· two dominant owners — lease-position valuation", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # facts
    s.section(r, L, 13, "PROPERTY FACTS  —  ⚠️ REPORTED (LoopNet / Daily Business Review / Sunbiz; BCPA blocked in build env)"); r += 1
    facts = [
        ("Building", "~168,807 SF, 13-story Class B office condominium (+ ground-floor retail)"),
        ("Year built / reno", "1973 (renovated 2007)"),
        ("Condo regime", "Created 2007; converted to condos 2011 by Bush Development Group"),
        ("Association", "Galleria Corporate Centre Condominium Association, Inc. (Sunbiz N07000001902)"),
        ("Lease economics", "Office units leased ≈ $26/SF Modified Gross"),
        ("Sale comp (historical)", "Unit sales ≈ $300/SF (pre-2020; office values since softened)"),
        ("Amenities", "Covered/valet parking, concierge, on-site café, two conference facilities"),
        ("Deal note", "Assembling the building = buying out BOTH dominant owners' condo positions"),
    ]
    for lab, val in facts:
        s.put(r, L, lab, style="calc", align="left")
        s.put(r, 4, val, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---- assumptions ----
    s.section(r, L, 13, "ASSUMPTIONS  —  🔵 blue = hardcoded inputs (Modified-Gross office)"); r += 1
    def inp(name, label, key, fmt, note):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        if name in amap:
            s.put(r, 3, f"='Assumptions'!{amap[name]}", style="calc", color="008000", fmt=fmt, align="right", name=name)
            s.put(r, 4, "🟢 Assumptions", style="note", align="left", merge=(r, 13))
        else:
            s.put(r, 3, a[key], style="input", fmt=fmt, align="right", name=name)
            s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    inp("GLA", "Rentable SF (both owners)", "gla", F_NUM, "⚠️ ~168,807 SF")
    inp("OCC0", "In-place occupancy", "occ0", F_PCT1, "🔶 office vacancy ~12%")
    inp("STABOCC", "Stabilized occupancy", "stab_occ", F_PCT1, "🔶")
    inp("MRENT", "Market rent ($/SF Modified Gross)", "market_rent", F_PSF, "⚠️ ~$26/SF MG")
    inp("RGROW", "Rent growth", "rent_growth", F_PCT1, "🔶")
    inp("CLOSS", "Credit & vacancy loss", "credit_loss", F_PCT1, "🔶")
    inp("MILL", "Effective millage", "millage", F_PCT2, "✅ area millage")
    inp("OPEX", "Office opex ex-taxes ($/SF, landlord)", "opex_psf", F_PSF, "🔶 MG — landlord pays")
    inp("MGMT", "Management fee (% EGR)", "mgmt_pct", F_PCT1, "🔶")
    inp("EGROW", "Expense growth", "exp_growth", F_PCT1, "🔶")
    inp("RES", "Replacement reserves ($/SF/yr)", "reserve_psf", F_PSF, "🔶")
    inp("PRICE", "Acquisition basis (income value)", "price", F_ACCT_TOP, "🔶 both positions @ ~8% cap")
    inp("CLOSE", "Closing & acq costs (% price)", "closing_pct", F_PCT1, "🔶")
    inp("LTV", "Senior loan LTV", "ltv", F_PCT1, "🔶 office conservative")
    inp("RATE", "Senior loan rate", "loan_rate", F_PCT2, "🔶 office premium")
    inp("AMORT", "Amortization (yrs)", "amort", F_YR, "🔶")
    inp("GICAP", "Going-in cap", "goingin_cap", F_PCT2, "🔶 small Class B office 8%")
    inp("EXITCAP", "Exit cap", "exit_cap", F_PCT2, "🔶")
    inp("COS", "Cost of sale", "cost_sale", F_PCT1, "🔶")
    inp("HOLD", "Hold period (yrs)", "hold", F_YR, "🔶")
    inp("DISC", "Discount rate (NPV)", "disc", F_PCT1, "🔶")
    inp("SALEPSF", "Sale comp ($/SF)", "sale_comp_psf", F_PSF, "⚠️ historical ~$300/SF")
    r += 1

    g = s.reg
    def R(n): return g[n]

    # derived / debt
    s.section(r, L, 13, "DERIVED VALUES  &  DEBT SIZING"); r += 1
    def der(name, label, formula, fmt, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    der("LOAN", "Senior loan amount", f"={R('PRICE')}*{R('LTV')}", F_ACCT_TOP, "price × LTV")
    der("MRATE", "Monthly rate", f"={R('RATE')}/12", F_PCT2)
    der("DS", "Annual debt service", f"={R('LOAN')}*({R('MRATE')}/(1-(1+{R('MRATE')})^(-{R('AMORT')}*12)))*12", F_ACCT_TOP)
    der("EQ_ACQ", "Equity at acquisition", f"={R('PRICE')}*(1+{R('CLOSE')})-{R('LOAN')}", F_ACCT_TOP)
    der("TCB", "Total cost basis", f"={R('PRICE')}*(1+{R('CLOSE')})", F_ACCT_TOP)
    der("EQ_REQ", "Total equity required", f"={R('TCB')}-{R('LOAN')}", F_ACCT_TOP)
    r += 1

    # ---- cash flow (Modified Gross: no NNN reimbursements) ----
    s.section(r, L, 13, "OPERATING CASH FLOW  —  10-year annual (Modified Gross)"); r += 1
    s.put(r, L, "Year", style="subhead", align="left")
    s.put(r, ACQ, "0 / Acq", style="subhead", align="center")
    for y in range(1, 11): s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1
    s.put(r, L, "Year ending", style="note", align="left")
    s.put(r, ACQ, "At close", style="note", align="center")
    for y in range(1, 11): s.put(r, pc(y), f"Dec-{2026+y}", style="note", align="center")
    r += 1

    rows = {}
    def cfrow(name, label, bold=False, top=False):
        nonlocal r
        rows[name] = r
        st = "subtotal" if top else ("label_b" if bold else "label")
        s.put(r, L, label, style=st, align="left"); return r
    ro = cfrow("OCC", "Occupancy")
    for y in range(1, 11):
        s.put(ro, pc(y), (f"=({R('OCC0')}+{R('STABOCC')})/2" if y == 1 else f"={R('STABOCC')}"), fmt=F_PCT1, align="right")
    r += 1
    rl = cfrow("LEASED", "Leased SF")
    for y in range(1, 11): s.put(rl, pc(y), f"={R('GLA')}*{CL(pc(y))}{rows['OCC']}", fmt=F_NUM, align="right")
    r += 1
    rb = cfrow("BASE", "Gross rental income (MG)", bold=True)
    for y in range(1, 11):
        s.put(rb, pc(y), f"={CL(pc(y))}{rows['LEASED']}*{R('MRENT')}*(1+{R('RGROW')})^({y}-1)",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    rcl = cfrow("CLOSSX", "Less: credit & vacancy loss")
    for y in range(1, 11): s.put(rcl, pc(y), f"=-{CL(pc(y))}{rows['BASE']}*{R('CLOSS')}", fmt=F_ACCT, align="right")
    r += 1
    regr = cfrow("EGR", "Effective Gross Revenue", top=True)
    for y in range(1, 11):
        s.put(regr, pc(y), f"={CL(pc(y))}{rows['BASE']}+{CL(pc(y))}{rows['CLOSSX']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    s.put(r, L, "OPERATING EXPENSES (landlord — Modified Gross)", style="subhead", align="left", merge=(r, 13)); r += 1
    rtax = cfrow("TAX", "Real-estate taxes")
    for y in range(1, 11): s.put(rtax, pc(y), f"={R('PRICE')}*{R('MILL')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rop = cfrow("OPX", "Office opex (utilities, R&M, ins, CAM)")
    for y in range(1, 11): s.put(rop, pc(y), f"={R('GLA')}*{R('OPEX')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rmg = cfrow("MGX", "Management fee")
    for y in range(1, 11): s.put(rmg, pc(y), f"={CL(pc(y))}{rows['EGR']}*{R('MGMT')}", fmt=F_ACCT, align="right")
    r += 1
    rtox = cfrow("TOPEX", "Total operating expenses", top=True)
    for y in range(1, 11):
        s.put(rtox, pc(y), f"=SUM({CL(pc(y))}{rows['TAX']}:{CL(pc(y))}{rows['MGX']})",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    rnoi = cfrow("NOI", "NET OPERATING INCOME", bold=True, top=True)
    for y in range(1, 11):
        s.put(rnoi, pc(y), f"={CL(pc(y))}{rows['EGR']}-{CL(pc(y))}{rows['TOPEX']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    rres = cfrow("RESV", "Replacement reserves")
    for y in range(1, 11): s.put(rres, pc(y), f"={R('GLA')}*{R('RES')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    runcf = cfrow("UNCF", "Unlevered cash flow (before reversion)", bold=True, top=True)
    s.put(runcf, ACQ, f"=-{R('PRICE')}*(1+{R('CLOSE')})", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(runcf, pc(y), f"={CL(pc(y))}{rows['NOI']}-{CL(pc(y))}{rows['RESV']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 2

    # reversion & levered
    s.section(r, L, 13, "REVERSION, DEBT SERVICE  &  LEVERED CASH FLOW"); r += 1
    rns = cfrow("NETSALE", "Net sale proceeds (exit year)")
    for y in range(1, 11):
        s.put(rns, pc(y), f"=IF({y}={R('HOLD')},({CL(pc(y))}{rows['NOI']}*(1+{R('RGROW')})/{R('EXITCAP')})*(1-{R('COS')}),0)", fmt=F_ACCT, align="right")
    r += 1
    rupcf = cfrow("PROJCF", "UNLEVERED PROJECT CASH FLOW", bold=True, top=True)
    s.put(rupcf, ACQ, f"={CL(ACQ)}{rows['UNCF']}", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rupcf, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['UNCF']},0)+{CL(pc(y))}{rows['NETSALE']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    rlb = cfrow("LBAL", "Loan balance (year-end)")
    for y in range(1, 11):
        s.put(rlb, pc(y), f"={R('LOAN')}*(1+{R('MRATE')})^(12*{y})-({R('DS')}/12)*((1+{R('MRATE')})^(12*{y})-1)/{R('MRATE')}", fmt=F_ACCT, align="right")
    r += 1
    rdscr = cfrow("DSCR", "DSCR (NOI ÷ DS)")
    for y in range(1, 11): s.put(rdscr, pc(y), f"={CL(pc(y))}{rows['NOI']}/{R('DS')}", fmt=F_MULT, align="right")
    r += 1
    rlev = cfrow("LEVCF", "LEVERED CASH FLOW (equity)", bold=True, top=True)
    s.put(rlev, ACQ, f"=-{R('EQ_ACQ')}", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rlev, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['UNCF']}-{R('DS')},0)"
              f"+IF({y}={R('HOLD')},{CL(pc(y))}{rows['NETSALE']}-{CL(pc(y))}{rows['LBAL']},0)",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 2

    # returns
    s.section(r, L, 13, "RETURNS  —  unlevered & levered"); r += 1
    proj = f"{CL(ACQ)}{rows['PROJCF']}:{CL(pc(10))}{rows['PROJCF']}"
    lev = f"{CL(ACQ)}{rows['LEVCF']}:{CL(pc(10))}{rows['LEVCF']}"
    proj1 = f"{CL(pc(1))}{rows['PROJCF']}:{CL(pc(10))}{rows['PROJCF']}"
    lev1 = f"{CL(pc(1))}{rows['LEVCF']}:{CL(pc(10))}{rows['LEVCF']}"
    def ret(name, label, formula, fmt):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name); r += 1
    ret("IRR_U", "Unlevered IRR", f"=IRR({proj})", F_PCT1)
    ret("EM_U", "Unlevered equity multiple", f"=SUM({proj1})/-{CL(ACQ)}{rows['PROJCF']}", F_MULT)
    ret("NPV_U", "Unlevered NPV @ discount rate", f"={CL(ACQ)}{rows['PROJCF']}+NPV({R('DISC')},{proj1})", F_ACCT_TOP)
    ret("IRR_L", "Levered IRR", f"=IRR({lev})", F_PCT1)
    ret("EM_L", "Levered equity multiple", f"=SUM({lev1})/{R('EQ_ACQ')}", F_MULT)
    ret("NOI1", "Year-1 NOI (pro-forma)", f"={CL(pc(1))}{rows['NOI']}", F_ACCT_TOP)
    ret("AS_IS_NOI", "As-is in-place NOI (at occ0, no lease-up)",
        f"=({R('GLA')}*{R('OCC0')}*{R('MRENT')})"
        f"-({R('GLA')}*{R('OCC0')}*{R('MRENT')})*{R('CLOSS')}"
        f"-({R('PRICE')}*{R('MILL')}+{R('GLA')}*{R('OPEX')})"
        f"-(({R('GLA')}*{R('OCC0')}*{R('MRENT')})-({R('GLA')}*{R('OCC0')}*{R('MRENT')})*{R('CLOSS')})*{R('MGMT')}", F_ACCT_TOP)
    ret("GOINGIN", "Going-in cap (as-is NOI ÷ price)", f"={R('AS_IS_NOI')}/{R('PRICE')}", F_PCT2)
    ret("STABNOI", "Stabilized NOI (Yr 2)", f"={CL(pc(2))}{rows['NOI']}", F_ACCT_TOP)
    ret("STABVAL", "Stabilized value (÷ exit cap)", f"={R('STABNOI')}/{R('EXITCAP')}", F_ACCT_TOP)
    ret("NOIPSF", "In-place NOI per SF", f"={CL(pc(1))}{rows['NOI']}/{R('GLA')}", F_PSF)
    ret("INCVAL", "Income value (Yr-1 NOI ÷ going-in cap)", f"={CL(pc(1))}{rows['NOI']}/{R('GICAP')}", F_ACCT_TOP)
    ret("COMPVAL", "Sale-comp value (SF × $/SF)", f"={R('GLA')}*{R('SALEPSF')}", F_ACCT_TOP)
    r += 1

    # ---- two-owner lease valuation ----
    s.section(r, L, 13, "LEASE-POSITION VALUATION BY OWNER  —  the two dominant condo owners"); r += 1
    hdr = ["Owner", "SF owned", "% bldg", "2019 basis", "Income value", "$300/SF comp", "Note"]
    cols = [L, 4, 5, 6, 7, 8, 9]
    spans = {2: 3, 9: 13}
    for h, c in zip(hdr, cols):
        endc = spans.get(c, c)
        s.put(r, c, h, style="subhead", align="left" if c in (L, 9) else "center", merge=(r, endc) if endc != c else None)
    r += 1
    for i, (nm, sub, sf, pct, basis, note) in enumerate(OWNERS):
        s.put(r, L, nm, style="calc", align="left", merge=(r, 3))
        s.put(r, 4, sf, style="input", fmt=F_NUM, align="right", name=f"OWN{i+1}_SF")   # 🔵 adjustable
        s.put(r, 5, f"={CL(4)}{r}/{R('GLA')}", style="calc", fmt=F_PCT1, align="right")
        s.put(r, 6, (basis if basis else "—"), style=("calc" if basis else "note"), fmt=(F_ACCT if basis else None), align="right")
        s.put(r, 7, f"={R('NOIPSF')}*{CL(4)}{r}/{R('GICAP')}", style="calc", fmt=F_ACCT, align="right")
        s.put(r, 8, f"={CL(4)}{r}*{R('SALEPSF')}", style="calc", fmt=F_ACCT, align="right")
        s.put(r, 9, note, style="calc", align="left", merge=(r, 13)); r += 1
    otot = r
    s.put(r, L, "TOTAL BUILDING", style="total", align="left", merge=(r, 3))
    s.put(r, 4, f"=SUM({CL(4)}{otot-2}:{CL(4)}{otot-1})", style="total", fmt=F_NUM, align="right")
    s.put(r, 5, f"=SUM({CL(5)}{otot-2}:{CL(5)}{otot-1})", style="total", fmt=F_PCT1, align="right")
    s.put(r, 6, "—", style="total", align="right")
    s.put(r, 7, f"=SUM({CL(7)}{otot-2}:{CL(7)}{otot-1})", style="total", fmt=F_ACCT_TOP, align="right", name="OWN_INCVAL")
    s.put(r, 8, f"=SUM({CL(8)}{otot-2}:{CL(8)}{otot-1})", style="total", fmt=F_ACCT_TOP, align="right")
    s.put(r, 9, "buy out both to assemble", style="total", align="left", merge=(r, 13)); r += 2

    # ---- full buy-out value (both owners) ----
    s.section(r, L, 13, "FULL BUY-OUT VALUE  —  cost to acquire BOTH condo owners' positions"); r += 1
    s.put(r, L, "Condo buyout premium (fractured ownership / holdout)", style="label", align="left")
    s.put(r, 3, 0.12, style="input", fmt=F_PCT1, align="right", name="BUYOUT_PREM")
    s.put(r, 4, "🔵 uplift over income value to get both owners to sell", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Main Street Fund LLC (57.4%) — buyout", style="label", align="left")
    s.put(r, 3, f"={CL(7)}{otot-2}*(1+{R('BUYOUT_PREM')})", style="calc", fmt=F_ACCT, align="right", name="BUYOUT1"); r += 1
    s.put(r, L, "International Sunrise Partners LLC (42.6%) — buyout", style="label", align="left")
    s.put(r, 3, f"={CL(7)}{otot-1}*(1+{R('BUYOUT_PREM')})", style="calc", fmt=F_ACCT, align="right", name="BUYOUT2"); r += 1
    s.put(r, L, "FULL BUY-OUT VALUE (both owners)", style="grand", align="left")
    s.put(r, 3, f"={R('BUYOUT1')}+{R('BUYOUT2')}", style="grand", fmt=F_ACCT_TOP, align="right", name="BUYOUT_TOTAL")
    s.put(r, 4, "cost to control the whole building (income value + buyout premium)", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "  cross-check — income value (no premium)", style="note", align="left")
    s.put(r, 3, f"={R('OWN_INCVAL')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 5, "vs. $300/SF sale comp (stale/high) shown in Returns above", style="note", align="left", merge=(r, 13)); r += 2

    # P&L
    s.section(r, L, 13, "PROFIT & LOSS STATEMENT  —  Year 1 vs. Stabilized (Yr 2)"); r += 1
    s.put(r, L, "$ / year", style="subhead", align="left")
    s.put(r, 6, "Year 1", style="subhead", align="right", merge=(r, 7))
    s.put(r, 8, "Stabilized", style="subhead", align="right", merge=(r, 9))
    s.put(r, 10, "Per SF (stab.)", style="subhead", align="right", merge=(r, 13)); r += 1
    y1, y2 = pc(1), pc(2)
    def pl(label, rn, sign=1, bold=False, top=False):
        nonlocal r
        st = "subtotal" if top else ("label_b" if bold else "label")
        s.put(r, L, label, style=st, align="left")
        s.put(r, 6, f"={'-' if sign<0 else ''}{CL(y1)}{rows[rn]}", fmt=F_ACCT, align="right", bold=bold, merge=(r, 7))
        s.put(r, 8, f"={'-' if sign<0 else ''}{CL(y2)}{rows[rn]}", fmt=(F_ACCT_TOP if top or bold else F_ACCT), align="right", bold=bold, merge=(r, 9))
        s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", fmt=F_PSF, align="right", bold=bold, merge=(r, 13)); r += 1
    pl("Gross rental income (MG)", "BASE", bold=True)
    pl("Less: credit & vacancy loss", "CLOSSX")
    pl("Effective Gross Income", "EGR", bold=True, top=True)
    pl("Real-estate taxes", "TAX", sign=-1)
    pl("Office opex (landlord)", "OPX", sign=-1)
    pl("Management fee", "MGX", sign=-1)
    pl("Net Operating Income", "NOI", bold=True, top=True)
    pl("Replacement reserves", "RESV", sign=-1)
    pl("Cash Flow Before Debt", "UNCF", bold=True, top=True)
    s.put(r, L, "Debt service", style="label", align="left")
    s.put(r, 6, f"=-{R('DS')}", fmt=F_ACCT, align="right", merge=(r, 7))
    s.put(r, 8, f"=-{R('DS')}", fmt=F_ACCT, align="right", merge=(r, 9))
    s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", fmt=F_PSF, align="right", merge=(r, 13)); r += 1
    cfad = r
    s.put(r, L, "Cash Flow After Debt (levered)", style="subtotal", align="left")
    s.put(r, 6, f"={CL(6)}{cfad-2}-{R('DS')}", fmt=F_ACCT_TOP, align="right", bold=True, merge=(r, 7))
    s.put(r, 8, f"={CL(8)}{cfad-2}-{R('DS')}", fmt=F_ACCT_TOP, align="right", bold=True, merge=(r, 9))
    s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", fmt=F_PSF, align="right", bold=True, merge=(r, 13)); r += 1

    # row anchors for the consolidated income tab
    s.reg["ROW_NOI"] = f"D{rows['NOI']}"
    s.reg["ROW_CAP"] = f"D{rows['RESV']}"
    s.reg["ROW_REV"] = f"D{rows['NETSALE']}"

    s.freeze("C6")
    return s
