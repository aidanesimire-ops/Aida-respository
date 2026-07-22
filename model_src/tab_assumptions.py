"""
tab_assumptions.py — ASSUMPTIONS CONTROL PANEL (the system's single input surface).
Top:    GLOBAL drivers (valuation, financing, acquisition costs, assemblage
        premium, land-value ladder, redevelopment residual).
Middle: PER-ASSET blocks — each asset's price, rents, occupancy, OPERATING
        EXPENSES, caps, and debt. Every asset tab reads these by live link.
Bottom: a DATA-GAP register of reported figures to verify.
Change any blue cell here → the whole model recalculates.
"""
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR
from data import SH
from configs import PUBLIX_CFG, KARLUEN_CFG
from tab_office import A as OFFICE_A
from tab_land import A as LAND_A

L = 2

# -------- per-asset input blocks (driver name, label, default, format) --------
def _blocks():
    PI, KI, OA, LA = PUBLIX_CFG["inp"], KARLUEN_CFG["inp"], OFFICE_A, LAND_A
    retail = lambda d, price_label, psf: [
        ("PRICE", price_label, d["price"], F_ACCT_TOP),
        (d["_landsf_name"], "Land (SF)", d["land_sf"], F_NUM),
        ("GLAND_PSF", "Land value ($/SF)", psf, F_PSF),
        ("MRENT", "Market rent ($/SF NNN)", d["market_rent"], F_PSF),
        ("OCC0", "In-place occupancy", d["occ0"], F_PCT1),
        ("STABOCC", "Stabilized occupancy", d["stab_occ"], F_PCT1),
        ("INS", "Insurance ($/yr)", d["insurance"], F_ACCT),
        ("CAM", "CAM ($/yr, recoverable)", d["cam"], F_ACCT),
        ("RM", "Repairs & maintenance ($/yr)", d["rm"], F_ACCT),
        ("MGMT", "Management fee (% EGR)", d["mgmt_pct"], F_PCT1),
        ("GICAP", "Going-in cap", d["goingin_cap"], F_PCT2),
        ("EXITCAP", "Exit cap", d["exit_cap"], F_PCT2),
        ("LTV", "Senior LTV", d["ltv"], F_PCT1),
        ("RATE", "Senior rate", d["loan_rate"], F_PCT2),
    ]
    sh = dict(SH); sh["_landsf_name"] = "LANDSF"
    pu = dict(PI); pu["_landsf_name"] = "GLANDSF"
    ka = dict(KI); ka["_landsf_name"] = "GLANDSF"
    return [
        ("SHA", "Shahidi Retail (Galleria Plaza) — NNN retail  ✅ verified parcel", retail(sh, "Purchase price / basis", 254.92)),
        ("PUB", "Publix + Starbucks — SALE-LEASEBACK (acquire fee, lease back during entitlement)  ✅ verified parcel", [
            ("PRICE", "SLB acquisition price (fee)", 25000000, F_ACCT_TOP),
            ("GLANDSF", "Land (SF)", PI["land_sf"], F_NUM),
            ("GLAND_PSF", "Land value ($/SF)", PUBLIX_CFG["land_psf"], F_PSF),
            ("SLB_RENT", "Publix leaseback rent ($/SF NNN)", 22.00, F_PSF),
            ("SLB_SF", "Publix leaseback SF", 34622, F_NUM),
            ("SBUX_RENT", "Starbucks pad rent ($/SF NNN)", 60.00, F_PSF),
            ("SBUX_SF", "Starbucks pad SF", 2200, F_NUM),
            ("TERM", "Leaseback term / entitlement (yrs)", 4, F_YR),
            ("OCC0", "In-place occupancy", 1.00, F_PCT1),
            ("STABOCC", "Stabilized occupancy", 1.00, F_PCT1),
            ("INS", "Insurance ($/yr)", PI["insurance"], F_ACCT),
            ("CAM", "CAM ($/yr, recoverable)", PI["cam"], F_ACCT),
            ("RM", "Repairs & maintenance ($/yr)", PI["rm"], F_ACCT),
            ("MGMT", "Management fee (% EGR)", PI["mgmt_pct"], F_PCT1),
            ("GICAP", "Going-in cap (reference)", PI["goingin_cap"], F_PCT2),
            ("EXITCAP", "Exit cap", PI["exit_cap"], F_PCT2),
            ("LTV", "Senior LTV (covered-land, conservative)", 0.45, F_PCT1),
            ("RATE", "Senior rate", PI["loan_rate"], F_PCT2),
        ]),
        ("SUN", "Sunrise Plaza (Kar Luen) — value-add retail  ⚠️ reported parcel", retail(ka, "Purchase price / basis", KARLUEN_CFG["land_psf"])),
        ("OFF", "Galleria Corporate Centre — office, Modified Gross  ⚠️ reported parcel", [
            ("PRICE", "Acquisition basis", OA["price"], F_ACCT_TOP),
            ("MRENT", "Market rent ($/SF MG)", OA["market_rent"], F_PSF),
            ("OCC0", "In-place occupancy", OA["occ0"], F_PCT1),
            ("STABOCC", "Stabilized occupancy", OA["stab_occ"], F_PCT1),
            ("OPEX", "Office opex ex-taxes ($/SF, landlord)", OA["opex_psf"], F_PSF),
            ("MGMT", "Management fee (% EGR)", OA["mgmt_pct"], F_PCT1),
            ("GICAP", "Going-in cap", OA["goingin_cap"], F_PCT2),
            ("EXITCAP", "Exit cap", OA["exit_cap"], F_PCT2),
            ("LTV", "Senior LTV", OA["ltv"], F_PCT1),
            ("RATE", "Senior rate", OA["loan_rate"], F_PCT2),
        ]),
        ("LND", "1040 Bayview — covered land (interim office)  ⚠️ reported parcel", [
            ("PRICE", "Acquisition basis (entitled land)", LA["price"], F_ACCT_TOP),
            ("IOCC", "Interim office occupancy", LA["interim_occ"], F_PCT1),
            ("IRENT", "Interim office rent ($/SF MG)", LA["interim_rent"], F_PSF),
            ("IOPEX", "Interim office opex ($/SF)", LA["interim_opex_psf"], F_PSF),
            ("IMGMT", "Management fee (% EGR)", LA["interim_mgmt"], F_PCT1),
            ("LTV", "Land loan LTV", LA["ltv"], F_PCT1),
            ("RATE", "Land loan rate", LA["loan_rate"], F_PCT2),
        ]),
    ]


def build_inputs(s):
    s.colw({"A": 2.5, "B": 42, "C": 14, "D": 10, "E": 14, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "ASSUMPTIONS  —  CONTROL PANEL", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "The single input surface. GLOBAL drivers first, then a block per asset (price · rents · occupancy · OPERATING EXPENSES · caps · "
                "debt). Every blue cell drives the model by live link — change one and price, IRR, DSCR, and value all recalculate.",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    def sect(t):
        nonlocal r
        s.section(r, L, 13, t); r += 1
        s.put(r, L, "Driver", style="subhead", align="left")
        s.put(r, 3, "Input", style="subhead", align="center")
        s.put(r, 4, "Flag", style="subhead", align="center")
        s.put(r, 5, "Drives / note", style="subhead", align="left", merge=(r, 13)); r += 1
    def inp(name, label, val, fmt, flag, note):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="center", name=name)
        s.put(r, 4, flag, style="calc", align="center")
        s.put(r, 5, note, style="note", align="left", merge=(r, 13)); r += 1

    sect("GLOBAL — VALUATION & HOLD  (→ Income Valuation)")
    inp("CAP", "Blended going-in cap (as-is)", 0.0650, F_PCT2, "🔶", "income price = as-is NOI ÷ this")
    inp("SCAP", "Blended stabilized / exit cap", 0.0675, F_PCT2, "🔶", "reversion & stabilized value")
    inp("TYLD", "Target unlevered yield (DCF discount)", 0.085, F_PCT1, "🔶", "DCF value; NPV hurdle")
    inp("GROW", "Blended NOI growth", 0.025, F_PCT1, "🔶", "reversion & sensitivities")
    inp("HOLD", "Hold period (yrs)", 5, F_YR, "🔶", "exit year for all assets")
    inp("COS", "Cost of sale at exit", 0.02, F_PCT1, "🔶", "net reversion")

    sect("GLOBAL — SENIOR FINANCING  (→ Income Valuation)")
    inp("LTV", "Max senior LTV", 0.60, F_PCT1, "🔶", "debt sizing constraint 1")
    inp("DSCRMIN", "Min DSCR", 1.30, F_MULT, "🔶", "debt sizing constraint 2")
    inp("DYMIN", "Min debt yield", 0.085, F_PCT1, "🔶", "debt sizing constraint 3")
    inp("RATE", "Senior rate", 0.065, F_PCT2, "🔶", "debt service")
    inp("AMORT", "Amortization (yrs)", 30, F_YR, "🔶", "mortgage constant")

    sect("GLOBAL — ACQUISITION COSTS  (→ Income Valuation Sources & Uses)")
    inp("DOCSTAMP", "Doc-stamp / transfer tax (% price)", 0.0070, F_PCT2, "🔶", "FL Broward $0.70/$100")
    inp("TITLE", "Title insurance (% price)", 0.0050, F_PCT2, "🔶", "closing cost")
    inp("LEGALDD", "Legal & due diligence (% price)", 0.0040, F_PCT2, "🔶", "closing cost")
    inp("ORIG", "Loan origination (% loan)", 0.0100, F_PCT2, "🔶", "financing cost → equity")

    sect("GLOBAL — ASSEMBLAGE PREMIUM  (→ Assemblage / covered-land price)")
    inp("PREM_LOW", "Assemblage premium — low", 0.15, F_PCT1, "🔶", "control-cost premium")
    inp("PREM_BASE", "Assemblage premium — base", 0.20, F_PCT1, "🔶", "headline covered-land price")
    inp("PREM_HIGH", "Assemblage premium — high", 0.25, F_PCT1, "🔶", "aggressive case")

    sect("GLOBAL — LAND & REDEVELOPMENT (1040 Bayview)  (→ Land tab)")
    inp("LPSF_LOW", "Land value — low ($/SF)", 64.0, F_PSF, "🔶", "BCPA-implied floor")
    inp("LPSF_BASE", "Land value — base ($/SF)", 125.0, F_PSF, "🔶", "mid-block corridor")
    inp("LPSF_HIGH", "Land value — high ($/SF)", 200.0, F_PSF, "🔶", "toward hard-corner comps")
    inp("UNIT_LOW", "Per entitled unit — low ($)", 40000, F_ACCT, "🔶", "259 units")
    inp("UNIT_BASE", "Per entitled unit — base ($)", 55000, F_ACCT, "🔶", "entitled-land value")
    inp("UNIT_HIGH", "Per entitled unit — high ($)", 70000, F_ACCT, "🔶", "strong entitlement")
    inp("REVUNIT", "Achievable value per unit ($)", 600000, F_ACCT, "🔶", "sellout / cap'd rental")
    inp("HARDPSF", "Hard cost ($/GBA SF)", 500.0, F_PSF, "🔶", "AE-zone coastal")
    inp("GBAUNIT", "GBA per unit (SF)", 950, F_NUM, "🔶", "gross buildable/unit")
    inp("SOFT", "Soft cost (% hard)", 0.20, F_PCT1, "🔶", "A&E, financing, fees")
    inp("PROFIT", "Developer profit (% GDV)", 0.15, F_PCT1, "🔶", "required margin")
    r += 1

    # -------- per-asset blocks --------
    s.section(r, L, 13, "PER-ASSET INPUTS  —  value drivers & OPERATING EXPENSES  (each asset tab reads these)"); r += 1
    for prefix, title, rows in _blocks():
        s.put(r, L, title, style="subhead", align="left", merge=(r, 13)); r += 1
        for name, label, val, fmt in rows:
            s.put(r, L, "   " + label, style="label", align="left")
            s.put(r, 3, val, style="input", fmt=fmt, align="center", name=f"{prefix}_{name}")
            r += 1
        r += 1
    return r


def build_index(s, regs, start_row):
    r = start_row
    def x(sheet, name, fmt):
        try:
            return f"='{sheet}'!{regs[sheet][name]}"
        except KeyError:
            return None

    s.section(r, L, 13, "DATA-GAP REGISTER  —  reported figures to verify at BCPA (shown live from source)"); r += 1
    s.put(r, L, "Figure", style="subhead", align="left")
    s.put(r, 3, "Current", style="subhead", align="center")
    s.put(r, 4, "Flag", style="subhead", align="center")
    s.put(r, 5, "Lives on", style="subhead", align="left", merge=(r, 13)); r += 1
    GAPS = [
        ("Assumptions", "SUN_PRICE", "Sunrise Plaza — value / basis", F_ACCT, "⚠️", "Assumptions · Sunrise block"),
        ("Sunrise Plaza", "GLA", "Sunrise Plaza — building SF", F_NUM, "⚠️", "Sunrise Plaza tab"),
        ("Assumptions", "SUN_GLANDSF", "Sunrise Plaza — land SF", F_NUM, "⚠️", "Assumptions · Sunrise block"),
        ("Office Condo", "GLA", "Office — building SF", F_NUM, "⚠️", "Office Condo tab"),
        ("Office Condo", "OWN1_SF", "Office — Main St Fund SF (57.4%)", F_NUM, "⚠️", "Office Condo tab"),
        ("Office Condo", "OWN2_SF", "Office — Intl Sunrise SF (42.6%)", F_NUM, "⚠️", "Office Condo tab"),
        ("Assumptions", "OFF_PRICE", "Office — acquisition basis", F_ACCT, "🔶", "Assumptions · Office block"),
        ("Land", "LANDSF", "1040 Bayview — land SF", F_NUM, "⚠️", "Land tab"),
        ("Land", "OFFSF", "1040 Bayview — office SF", F_NUM, "⚠️", "Land tab"),
        ("Land", "UNITS", "1040 Bayview — entitled units", F_NUM, "⚠️", "Land tab"),
        ("Land", "BCPA", "1040 Bayview — BCPA value", F_ACCT, "⚠️", "Land tab"),
    ]
    for sheet, name, label, fmt, flag, where in GAPS:
        link = x(sheet, name, fmt)
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, link if link else "n/a", style=("calc" if link else "note"), color=("008000" if link else None), fmt=fmt, align="center")
        s.put(r, 4, flag, style="calc", align="center")
        s.put(r, 5, where, style="note", align="left", merge=(r, 13)); r += 1
    r += 1
    s.put(r, L, "How to use", style="warn", align="left")
    s.put(r, 4, "Everything you tune is on THIS tab: global drivers up top, then a block per asset (price · rents · occupancy · operating "
                "expenses · caps · debt). Standard modeling params (rent/expense growth, TI/LC, reserves, closing detail) remain blue on each "
                "asset tab. ⚠️ = reported, verify at bcpa.net. Change any blue cell → the model recalculates.",
          style="warn", align="left", merge=(r, 13)); r += 1
    s.freeze("C3")
    return s
