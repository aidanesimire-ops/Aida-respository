"""
tab_shahidi.py — Shahidi Retail (Galleria Plaza) asset tab.
Self-contained: property facts, tenant rent roll, assumptions (blue),
10-year DCF, reversion & debt, NPV, unlevered + levered returns, and a P&L.
Reproduces BuildSpec §8 QA targets.
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_ACCT2_TOP, F_PCT1, F_PCT2, F_MULT,
                   F_PSF, F_NUM, F_NUM2, F_YR, F_DATE)
from data import PARCELS, SH

L = 2          # label column B
ACQ = 3        # C
def pc(y):     # period column for year y (1..10)
    return 3 + y
def CL(c):
    return get_column_letter(c)

# Shahidi tenant rent roll (SF-weighted blended ~ model market rent).
# Occupied 21,850 SF (83.17%) + vacant 4,422 SF = 26,272 GLA.
ROLL = [
    ("2541", "Primo Liquors & Fine Wine", "Retail – liquor/wine", 4000, 48.00, "Local"),
    ("2577", "Wells Fargo Bank", "Bank / financial", 3500, 62.00, "NATIONAL credit"),
    ("2543–75", "In-line shops (mid-strip)", "Various local retail/service", 3700, 52.00, "Local"),
    ("2587", "Verizon Wireless", "Wireless / electronics", 2200, 58.00, "NATIONAL credit"),
    ("2595", "First Impressions Smile Center", "Medical – dentistry", 2200, 54.00, "Local"),
    ("2549", "Freeman's Luggage & Gifts", "Retail – luggage/gifts", 2000, 50.00, "Local"),
    ("2583", "Eyes on Sunrise", "Medical – optometry", 1800, 56.00, "Local"),
    ("2541", "Lilac & Lilies Boutique", "Retail – apparel", 1250, 58.00, "Local"),
    ("2595", "Roxanne Jackson – GEICO", "Insurance agency", 1200, 56.00, "Regional"),
]
VACANT_SF = 4422


def build(s):
    p = PARCELS["shahidi"]
    s.colw({"A": 2.5, "B": 34, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    # ---------------------------------------------------------- banner
    s.put(r, L, "SHAHIDI RETAIL CENTER  ·  “GALLERIA PLAZA”", style="banner",
          align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, f"{p['addr']}   |   Folio {p['folio']}   |   26,272 SF NNN "
                f"neighborhood retail · 83.17% leased · value-add lease-up",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # ---------------------------------------------------------- property facts (verified)
    s.section(r, L, 13, "PROPERTY FACTS  —  ✅ public record (BCPA / Sunbiz / recorded deed)"); r += 1
    facts = [
        ("Record owner", p["owner"]), ("Principal / manager", p["principal"]),
        ("Gross leasable area (GLA)", f"{p['gla']:,} SF"),
        ("Land", f"{p['land_sf']:,} SF  ({p['land_ac']} ac)"),
        ("Year built", p["year_built"]), ("Zoning / flood", p["zoning"]),
        ("Last sale", f"{p['last_sale_date']}  —  ${p['last_sale']:,}  (Special Warranty Deed)"),
        ("2025 real-estate taxes", f"${p['tax_2025']:,}   (2024: ${p['tax_2024']:,})"),
        ("2026 just / market value (BCPA)", f"${p['just_2026']:,}"),
        ("Effective millage", f"{p['millage']*100:.2f}%   (2025 tax ÷ just value)"),
        ("Derived basis on $17.1M", f"${p['basis_land']:.2f}/SF land · ${p['basis_bldg']:.2f}/SF building"),
        ("In-place occupancy", f"{p['occ']*100:.2f}%   →  ~{VACANT_SF:,} SF vacant to lease"),
    ]
    for lab, val in facts:
        s.put(r, L, lab, style="verified", align="left")
        s.put(r, 4, val, style="verified", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---------------------------------------------------------- tenant rent roll
    s.section(r, L, 13, "TENANT RENT ROLL  —  🔶 suites/rents estimated from corridor comps ($45–60/SF NNN); SF-weighted blend ties to model market rent"); r += 1
    hdr = ["Suite", "Tenant", "Category", "SF", "$/SF NNN", "Annual rent", "Tenant type"]
    cols = [L, 3, 4, 6, 7, 8, 11]
    spans = {4: 5, 8: 10, 11: 13}   # merges: Category D:E, Annual rent H:J, type K:M
    for h, c in zip(hdr, cols):
        endc = spans.get(c, c)
        s.put(r, c, h, style="subhead", align="center" if c not in (3, 4) else "left",
              merge=(r, endc) if endc != c else None)
    r += 1
    roll_start = r
    for suite, ten, cat, sf, rent, ttype in ROLL:
        s.put(r, L, suite, style="calc", align="center")
        s.put(r, 3, ten, style="calc", align="left")
        s.put(r, 4, cat, style="calc", align="left", merge=(r, 5))
        s.put(r, 6, sf, style="calc", fmt=F_NUM, align="right")
        s.put(r, 7, rent, style="input", fmt=F_PSF, align="right")
        s.put(r, 8, f"={CL(6)}{r}*{CL(7)}{r}", style="calc", fmt=F_ACCT, align="right", merge=(r, 10))
        cr = "NATIONAL credit" in ttype
        s.put(r, 11, ttype, style="verified" if cr else "calc", align="left", merge=(r, 13))
        r += 1
    # vacant line
    s.put(r, L, "—", style="warn", align="center")
    s.put(r, 3, "VACANT / available (mid-strip)", style="warn", align="left")
    s.put(r, 4, "Lease-up target to 95%", style="warn", align="left", merge=(r, 5))
    s.put(r, 6, VACANT_SF, style="warn", fmt=F_NUM, align="right")
    s.put(r, 7, "—", style="warn", align="right")
    s.put(r, 8, "—", style="warn", align="right", merge=(r, 10))
    s.put(r, 11, "value-add upside", style="warn", align="left", merge=(r, 13))
    r += 1
    # totals
    occ_end = r - 2
    s.put(r, L, "TOTAL / WEIGHTED AVG", style="total", align="left")
    s.put(r, 3, "9 tenants + vacancy", style="total", align="left")
    s.put(r, 4, "", style="total", merge=(r, 5))
    s.put(r, 6, f"=SUM({CL(6)}{roll_start}:{CL(6)}{r-1})", style="total", fmt=F_NUM, align="right")
    s.put(r, 7, f"=IFERROR(SUM({CL(8)}{roll_start}:{CL(8)}{occ_end})/SUM({CL(6)}{roll_start}:{CL(6)}{occ_end}),0)",
          style="total", fmt=F_PSF, align="right")
    s.put(r, 8, f"=SUM({CL(8)}{roll_start}:{CL(8)}{occ_end})", style="total", fmt=F_ACCT_TOP, align="right", merge=(r, 10))
    s.put(r, 11, "Wells Fargo + Verizon = credit", style="total", align="left", merge=(r, 13))
    r += 2

    # ---------------------------------------------------------- assumptions (blue inputs)
    s.section(r, L, 13, "ASSUMPTIONS  —  🔵 blue = hardcoded inputs (the only cells you change)"); r += 1

    def grp(title):
        nonlocal r
        s.put(r, L, title, style="subhead", align="left", merge=(r, 13)); r += 1

    def inp(name, label, val, fmt, note):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="right", name=name)
        s.put(r, 4, note, style="note", align="left", merge=(r, 13)); r += 1

    grp("Property")
    inp("GLA", "GLA (SF)", SH["gla"], F_NUM, "✅ BCPA")
    inp("OCC0", "In-place occupancy", SH["occ0"], F_PCT2, "✅ BCPA")
    inp("LANDSF", "Land (SF)", SH["land_sf"], F_NUM, "✅ BCPA")
    inp("MILL", "Effective millage", SH["millage"], F_PCT2, "✅ 2025 tax ÷ just value")
    grp("Revenue")
    inp("BRENT", "In-place base rent ($/SF NNN)", SH["base_rent"], F_PSF, "🔶 owner says $60; corridor $45–60")
    inp("MRENT", "Market rent ($/SF NNN)", SH["market_rent"], F_PSF, "🔶 drives DCF base rent")
    inp("RGROW", "Market rent growth", SH["rent_growth"], F_PCT1, "🔶")
    inp("STABOCC", "Stabilized occupancy", SH["stab_occ"], F_PCT1, "🔶 lease-up target")
    inp("CLOSS", "Credit & collection loss", SH["credit_loss"], F_PCT1, "🔶")
    grp("Operating expenses")
    inp("REASS", "Reassessed value (= price, FL rule)", SH["reassessed"], F_ACCT_TOP, "🔶 FL reassess-to-price")
    inp("INS", "Insurance ($/yr)", SH["insurance"], F_ACCT_TOP, "🔶 AE flood wildcard")
    inp("CAM", "CAM ($/yr, recoverable)", SH["cam"], F_ACCT_TOP, "🔶")
    inp("RM", "Repairs & maintenance ($/yr)", SH["rm"], F_ACCT_TOP, "🔶 non-recoverable")
    inp("MGMT", "Management fee (% EGR)", SH["mgmt_pct"], F_PCT1, "🔶")
    inp("EGROW", "Expense growth", SH["exp_growth"], F_PCT1, "🔶")
    grp("Capital")
    inp("TI", "Tenant improvements ($/SF)", SH["ti_psf"], F_PSF, "🔶 on leased-up SF")
    inp("LC", "Leasing commissions ($/SF)", SH["lc_psf"], F_PSF, "🔶 on leased-up SF")
    inp("RES", "Replacement reserves ($/SF/yr)", SH["reserve_psf"], F_PSF, "🔶")
    inp("ROLL", "Rollover leasing reserve ($/SF/yr)", SH["rollover_psf"], F_PSF, "🔶")
    grp("Acquisition & financing")
    inp("PRICE", "Purchase price", SH["price"], F_ACCT_TOP, "🔶 = last sale; negotiated")
    inp("CLOSE", "Closing & acq costs (% price)", SH["closing_pct"], F_PCT1, "🔶")
    inp("LTV", "Senior loan LTV", SH["ltv"], F_PCT1, "🔶")
    inp("RATE", "Senior loan rate", SH["loan_rate"], F_PCT2, "🔶 mid-2026")
    inp("AMORT", "Senior loan amortization (yrs)", SH["amort"], F_YR, "🔶")
    grp("Valuation & hold")
    inp("GICAP", "Going-in cap (reference)", SH["goingin_cap"], F_PCT1, "🔶")
    inp("EXITCAP", "Exit / reversion cap", SH["exit_cap"], F_PCT1, "🔶")
    inp("COS", "Cost of sale at exit", SH["cost_sale"], F_PCT1, "🔶")
    inp("HOLD", "Hold period (yrs)", SH["hold"], F_YR, "🔶 reversion in this year")
    inp("DISC", "Discount rate (unlevered, for NPV)", 0.09, F_PCT1, "🔶 target unlevered yield")
    r += 1

    # convenience refs
    g = s.reg
    def R(n): return g[n]

    # ---------------------------------------------------------- derived / debt block
    s.section(r, L, 13, "DERIVED VALUES  &  DEBT SIZING"); r += 1
    def der(name, label, formula, fmt, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    der("LOAN", "Senior loan amount", f"={R('PRICE')}*{R('LTV')}", F_ACCT_TOP, "price × LTV")
    der("MRATE", "Monthly rate", f"={R('RATE')}/12", F_PCT2)
    der("NPER", "Amortization periods", f"={R('AMORT')}*12", F_NUM)
    der("DS", "Annual debt service (amortizing)",
        f"={R('LOAN')}*({R('MRATE')}/(1-(1+{R('MRATE')})^(-{R('NPER')})))*12", F_ACCT_TOP)
    der("EQ_ACQ", "Equity at acquisition", f"={R('PRICE')}*(1+{R('CLOSE')})-{R('LOAN')}", F_ACCT_TOP,
        "price×(1+closing) − loan")
    der("ABSORB", "Absorption SF (lease-up)", f"={R('GLA')}*({R('STABOCC')}-{R('OCC0')})", F_NUM)
    der("INIT_LEASE", "Initial leasing capital (TI/LC on absorbed SF)",
        f"={R('ABSORB')}*({R('TI')}+{R('LC')})", F_ACCT_TOP)
    der("TCB", "Total cost basis (incl. initial leasing)",
        f"={R('PRICE')}*(1+{R('CLOSE')})+{R('INIT_LEASE')}", F_ACCT_TOP)
    der("EQ_REQ", "Total equity required", f"={R('TCB')}-{R('LOAN')}", F_ACCT_TOP)
    s.put(r, L, "Land value ($/SF)", style="label", align="left")
    s.put(r, 3, 254.92, style="input", fmt=F_PSF, align="right", name="GLAND_PSF")
    s.put(r, 4, "🔶 arm's-length basis ($254.92/SF)", style="note", align="left", merge=(r, 13)); r += 1
    der("LANDVAL", "Land value (land SF × $/SF)", f"={R('LANDSF')}*{R('GLAND_PSF')}", F_ACCT_TOP,
        "both blue inputs above")
    r += 1

    # ---------------------------------------------------------- 10-year cash flow
    s.section(r, L, 13, "OPERATING CASH FLOW  —  10-year annual (black = formulas; expenses positive, subtracted in subtotals)"); r += 1
    # period headers
    s.put(r, L, "Year", style="subhead", align="left")
    s.put(r, ACQ, "0 / Acq", style="subhead", align="center")
    for y in range(1, 11):
        s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1
    s.put(r, L, "Year ending", style="note", align="left")
    s.put(r, ACQ, "At close", style="note", align="center")
    for y in range(1, 11):
        s.put(r, pc(y), f"Dec-{2026+y}", style="note", align="center")
    r += 1

    rows = {}
    def cfrow(name, label, style="calc", fmt=F_ACCT, bold=False, top=False):
        nonlocal r
        rows[name] = r
        st = "subtotal" if top else ("label_b" if bold else "label")
        s.put(r, L, label, style=st, align="left")
        return r

    # occupancy & leased SF
    ro = cfrow("OCC", "Occupancy")
    for y in range(1, 11):
        f = (f"=({R('OCC0')}+{R('STABOCC')})/2" if y == 1 else f"={R('STABOCC')}")
        s.put(ro, pc(y), f, fmt=F_PCT1, align="right")
    r += 1
    rl = cfrow("LEASED", "Leased SF")
    for y in range(1, 11):
        s.put(rl, pc(y), f"={R('GLA')}*{CL(pc(y))}{rows['OCC']}", fmt=F_NUM, align="right")
    r += 1
    # revenue
    s.put(r, L, "REVENUE", style="subhead", align="left", merge=(r, 13)); r += 1
    rb = cfrow("BASE", "Base rental income")
    for y in range(1, 11):
        s.put(rb, pc(y), f"={CL(pc(y))}{rows['LEASED']}*{R('MRENT')}*(1+{R('RGROW')})^({y}-1)",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    rreco = cfrow("RECOV", "Recoverable opex (gross)")
    for y in range(1, 11):
        s.put(rreco, pc(y), f"=({R('REASS')}*{R('MILL')}+{R('INS')}+{R('CAM')})*(1+{R('EGROW')})^({y}-1)",
              fmt=F_ACCT, align="right")
    r += 1
    rreim = cfrow("REIMB", "Expense reimbursements (NNN)")
    for y in range(1, 11):
        s.put(rreim, pc(y), f"={CL(pc(y))}{rows['RECOV']}*{CL(pc(y))}{rows['OCC']}", fmt=F_ACCT, align="right")
    r += 1
    rcl = cfrow("CLOSS", "Less: credit & collection loss")
    for y in range(1, 11):
        s.put(rcl, pc(y), f"=-{CL(pc(y))}{rows['BASE']}*{R('CLOSS')}", fmt=F_ACCT, align="right")
    r += 1
    regr = cfrow("EGR", "Effective Gross Revenue", top=True)
    for y in range(1, 11):
        s.put(regr, pc(y), f"={CL(pc(y))}{rows['BASE']}+{CL(pc(y))}{rows['REIMB']}+{CL(pc(y))}{rows['CLOSS']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    # opex
    s.put(r, L, "OPERATING EXPENSES", style="subhead", align="left", merge=(r, 13)); r += 1
    rtax = cfrow("TAX", "Real-estate taxes (reassessed)")
    for y in range(1, 11):
        s.put(rtax, pc(y), f"={R('REASS')}*{R('MILL')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rins = cfrow("INSX", "Insurance")
    for y in range(1, 11):
        s.put(rins, pc(y), f"={R('INS')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rcam = cfrow("CAMX", "CAM")
    for y in range(1, 11):
        s.put(rcam, pc(y), f"={R('CAM')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rrm = cfrow("RMX", "Repairs & maintenance")
    for y in range(1, 11):
        s.put(rrm, pc(y), f"={R('RM')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rmg = cfrow("MGX", "Management fee")
    for y in range(1, 11):
        s.put(rmg, pc(y), f"={CL(pc(y))}{rows['EGR']}*{R('MGMT')}", fmt=F_ACCT, align="right")
    r += 1
    rtox = cfrow("TOPEX", "Total operating expenses", top=True)
    for y in range(1, 11):
        s.put(rtox, pc(y),
              f"=SUM({CL(pc(y))}{rows['TAX']}:{CL(pc(y))}{rows['MGX']})",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    rnoi = cfrow("NOI", "NET OPERATING INCOME", bold=True, top=True)
    for y in range(1, 11):
        s.put(rnoi, pc(y), f"={CL(pc(y))}{rows['EGR']}-{CL(pc(y))}{rows['TOPEX']}",
              style="calc", fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    # capital
    s.put(r, L, "CAPITAL", style="subhead", align="left", merge=(r, 13)); r += 1
    rres = cfrow("RESV", "Replacement reserves")
    for y in range(1, 11):
        s.put(rres, pc(y), f"={R('GLA')}*{R('RES')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rlease = cfrow("LEASECAP", "Leasing costs (TI/LC + rollover)")
    for y in range(1, 11):
        if y == 1:
            f = f"={R('ABSORB')}*({R('TI')}+{R('LC')})+{R('GLA')}*{R('ROLL')}"
        else:
            f = f"={R('GLA')}*{R('ROLL')}*(1+{R('EGROW')})^({y}-1)"
        s.put(rlease, pc(y), f, fmt=F_ACCT, align="right")
    r += 1
    rtcap = cfrow("TCAP", "Total capital", top=True)
    for y in range(1, 11):
        s.put(rtcap, pc(y), f"={CL(pc(y))}{rows['RESV']}+{CL(pc(y))}{rows['LEASECAP']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right")
    r += 1
    # unlevered CF
    runcf = cfrow("UNCF", "Unlevered cash flow (before reversion)", bold=True, top=True)
    s.put(runcf, ACQ, f"=-{R('PRICE')}*(1+{R('CLOSE')})", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(runcf, pc(y), f"={CL(pc(y))}{rows['NOI']}-{CL(pc(y))}{rows['TCAP']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    r += 1

    # ---------------------------------------------------------- reversion & levered CF
    s.section(r, L, 13, "REVERSION, DEBT SERVICE  &  LEVERED CASH FLOW"); r += 1
    # net sale proceeds (hold year only)
    rns = cfrow("NETSALE", "Net sale proceeds (exit year)")
    for y in range(1, 11):
        f = (f"=IF({y}={R('HOLD')},({CL(pc(y))}{rows['NOI']}*(1+{R('RGROW')})/{R('EXITCAP')})*(1-{R('COS')}),0)")
        s.put(rns, pc(y), f, fmt=F_ACCT, align="right")
    r += 1
    rupcf = cfrow("PROJCF", "UNLEVERED PROJECT CASH FLOW", bold=True, top=True)
    s.put(rupcf, ACQ, f"={CL(ACQ)}{rows['UNCF']}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rupcf, pc(y),
              f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['UNCF']},0)+{CL(pc(y))}{rows['NETSALE']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    # debt service
    rds = cfrow("DSV", "Debt service")
    for y in range(1, 11):
        s.put(rds, pc(y), f"=IF({y}<={R('HOLD')},-{R('DS')},0)", fmt=F_ACCT, align="right")
    r += 1
    # loan balance
    rlb = cfrow("LBAL", "Loan balance (year-end)")
    for y in range(1, 11):
        f = (f"={R('LOAN')}*(1+{R('MRATE')})^(12*{y})-({R('DS')}/12)*"
             f"((1+{R('MRATE')})^(12*{y})-1)/{R('MRATE')}")
        s.put(rlb, pc(y), f, fmt=F_ACCT, align="right")
    r += 1
    rdscr = cfrow("DSCR", "DSCR (NOI ÷ DS)")
    for y in range(1, 11):
        s.put(rdscr, pc(y), f"={CL(pc(y))}{rows['NOI']}/{R('DS')}", fmt=F_MULT, align="right")
    r += 1
    rdy = cfrow("DYLD", "Debt yield (NOI ÷ loan)")
    for y in range(1, 11):
        s.put(rdy, pc(y), f"={CL(pc(y))}{rows['NOI']}/{R('LOAN')}", fmt=F_PCT1, align="right")
    r += 1
    rlev = cfrow("LEVCF", "LEVERED CASH FLOW (equity)", bold=True, top=True)
    s.put(rlev, ACQ, f"=-{R('EQ_ACQ')}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        f = (f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['UNCF']}-{R('DS')},0)"
             f"+IF({y}={R('HOLD')},{CL(pc(y))}{rows['NETSALE']}-{CL(pc(y))}{rows['LBAL']},0)")
        s.put(rlev, pc(y), f, fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    r += 1

    # ---------------------------------------------------------- returns
    s.section(r, L, 13, "RETURNS  —  unlevered & levered"); r += 1
    proj_range = f"{CL(ACQ)}{rows['PROJCF']}:{CL(pc(10))}{rows['PROJCF']}"
    lev_range  = f"{CL(ACQ)}{rows['LEVCF']}:{CL(pc(10))}{rows['LEVCF']}"
    proj_y1_10 = f"{CL(pc(1))}{rows['PROJCF']}:{CL(pc(10))}{rows['PROJCF']}"
    lev_y1_10  = f"{CL(pc(1))}{rows['LEVCF']}:{CL(pc(10))}{rows['LEVCF']}"

    def ret(name, label, formula, fmt):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name)
        r += 1

    ret("IRR_U", "Unlevered IRR", f"=IRR({proj_range})", F_PCT1)
    ret("EM_U", "Unlevered equity multiple",
        f"=SUM({proj_y1_10})/-{CL(ACQ)}{rows['PROJCF']}", F_MULT)
    ret("NPV_U", "Unlevered NPV @ discount rate",
        f"={CL(ACQ)}{rows['PROJCF']}+NPV({R('DISC')},{proj_y1_10})", F_ACCT_TOP)
    ret("IRR_L", "Levered IRR", f"=IRR({lev_range})", F_PCT1)
    ret("EM_L", "Levered equity multiple",
        f"=SUM({lev_y1_10})/{R('EQ_ACQ')}", F_MULT)
    ret("INPLACE_NOI", "In-place NOI (Yr-1 $, 83.17% occ)",
        f"=({R('GLA')}*{R('OCC0')}*{R('BRENT')})"
        f"+({R('REASS')}*{R('MILL')}+{R('INS')}+{R('CAM')})*{R('OCC0')}"
        f"-({R('GLA')}*{R('OCC0')}*{R('BRENT')})*{R('CLOSS')}"
        f"-({R('REASS')}*{R('MILL')}+{R('INS')}+{R('CAM')}+{R('RM')})"
        f"-(({R('GLA')}*{R('OCC0')}*{R('BRENT')})+({R('REASS')}*{R('MILL')}+{R('INS')}+{R('CAM')})*{R('OCC0')}"
        f"-({R('GLA')}*{R('OCC0')}*{R('BRENT')})*{R('CLOSS')})*{R('MGMT')}", F_ACCT_TOP)
    ret("GOINGIN", "Going-in cap (in-place NOI ÷ price)",
        f"={R('INPLACE_NOI')}/{R('PRICE')}", F_PCT2)
    ret("STABNOI", "Stabilized NOI (Yr 2)", f"={CL(pc(2))}{rows['NOI']}", F_ACCT_TOP)
    ret("STABVAL", "Stabilized value (÷ exit cap)", f"={R('STABNOI')}/{R('EXITCAP')}", F_ACCT_TOP)
    ret("YOC", "Stabilized yield on cost", f"={R('STABNOI')}/{R('TCB')}", F_PCT1)
    ret("VCREATE", "Value created (lease-up)", f"={R('STABVAL')}-{R('TCB')}", F_ACCT_TOP)
    ret("DSCR1", "Year-1 DSCR", f"={CL(pc(1))}{rows['NOI']}/{R('DS')}", F_MULT)
    ret("DY1", "Year-1 debt yield", f"={CL(pc(1))}{rows['NOI']}/{R('LOAN')}", F_PCT1)
    r += 1

    # ---------------------------------------------------------- P&L statement
    s.section(r, L, 13, "PROFIT & LOSS STATEMENT  —  In-place (Yr 1) vs. Stabilized (Yr 2)"); r += 1
    s.put(r, L, "$ / year", style="subhead", align="left")
    s.put(r, 6, "In-place (Yr 1)", style="subhead", align="right", merge=(r, 7))
    s.put(r, 8, "Stabilized (Yr 2)", style="subhead", align="right", merge=(r, 9))
    s.put(r, 10, "Per SF (stab.)", style="subhead", align="right", merge=(r, 13)); r += 1
    y1, y2 = pc(1), pc(2)
    def pl(label, rowname, sign=1, bold=False, top=False, pct=False):
        nonlocal r
        st = "subtotal" if top else ("label_b" if bold else "label")
        s.put(r, L, label, style=st, align="left")
        c1 = f"={'-' if sign<0 else ''}{CL(y1)}{rows[rowname]}"
        c2 = f"={'-' if sign<0 else ''}{CL(y2)}{rows[rowname]}"
        s.put(r, 6, c1, style="calc", fmt=F_ACCT, align="right", bold=bold, merge=(r, 7))
        s.put(r, 8, c2, style="calc", fmt=(F_ACCT_TOP if top or bold else F_ACCT), align="right", bold=bold, merge=(r, 9))
        s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", style="calc", fmt=F_PSF, align="right", bold=bold, merge=(r, 13))
        r += 1
    pl("Base rental income", "BASE", bold=True)
    pl("Expense reimbursements", "REIMB")
    pl("Less: credit loss", "CLOSS")
    pl("Effective Gross Income", "EGR", bold=True, top=True)
    pl("Real-estate taxes", "TAX", sign=-1)
    pl("Insurance", "INSX", sign=-1)
    pl("CAM", "CAMX", sign=-1)
    pl("Repairs & maintenance", "RMX", sign=-1)
    pl("Management fee", "MGX", sign=-1)
    pl("Net Operating Income", "NOI", bold=True, top=True)
    pl("Replacement reserves", "RESV", sign=-1)
    pl("Leasing costs", "LEASECAP", sign=-1)
    pl("Cash Flow Before Debt", "UNCF", bold=True, top=True)
    # debt service line (constant)
    s.put(r, L, "Debt service", style="label", align="left")
    s.put(r, 6, f"=-{R('DS')}", style="calc", fmt=F_ACCT, align="right", merge=(r, 7))
    s.put(r, 8, f"=-{R('DS')}", style="calc", fmt=F_ACCT, align="right", merge=(r, 9))
    s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", style="calc", fmt=F_PSF, align="right", merge=(r, 13)); r += 1
    cfad = r
    s.put(r, L, "Cash Flow After Debt (levered)", style="subtotal", align="left")
    s.put(r, 6, f"={CL(6)}{cfad-2}-{R('DS')}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True, merge=(r, 7))
    s.put(r, 8, f"={CL(8)}{cfad-2}-{R('DS')}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True, merge=(r, 9))
    s.put(r, 10, f"={CL(8)}{r}/{R('GLA')}", style="calc", fmt=F_PSF, align="right", bold=True, merge=(r, 13)); r += 1

    # row anchors for the consolidated income tab
    s.reg["ROW_NOI"] = f"D{rows['NOI']}"
    s.reg["ROW_CAP"] = f"D{rows['TCAP']}"
    s.reg["ROW_REV"] = f"D{rows['NETSALE']}"

    s.freeze("C6")
    return s
