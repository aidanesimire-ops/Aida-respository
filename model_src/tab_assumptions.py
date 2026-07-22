"""
tab_assumptions.py — ASSUMPTIONS & DATA-GAP CONTROL PANEL.
Single place to flex every driver of the ultimate numbers. All blue cells here
feed the model by cross-sheet link (Income Valuation, Assemblage, Land). The
lower half is a live register of every gap in our knowledge — reported/estimated
figures — each shown from its source cell so you can see status and jump to adjust.
"""
from openpyxl.utils import get_column_letter
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR

L = 2
def CL(c): return get_column_letter(c)


def build_inputs(s):
    """Blue driver inputs the model links to. Built first (no external deps)."""
    s.colw({"A": 2.5, "B": 40, "C": 14, "D": 12, "E": 14, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "ASSUMPTIONS  &  DATA-GAP CONTROL PANEL", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "Every blue cell is an input. These drive the Income Valuation, Assemblage, and Land tabs by live link — "
                "change one and the ultimate numbers (price, IRR, value) recalculate. The register below indexes every gap.",
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

    sect("VALUATION & HOLD  (→ Income Valuation tab)")
    inp("CAP", "Blended going-in cap (as-is)", 0.0650, F_PCT2, "🔶", "income price = as-is NOI ÷ this")
    inp("SCAP", "Blended stabilized / exit cap", 0.0675, F_PCT2, "🔶", "reversion & stabilized value")
    inp("TYLD", "Target unlevered yield (DCF discount)", 0.085, F_PCT1, "🔶", "DCF value; NPV hurdle")
    inp("GROW", "Blended NOI growth", 0.025, F_PCT1, "🔶", "reversion & sensitivities")
    inp("HOLD", "Hold period (yrs)", 5, F_YR, "🔶", "exit year for all assets")
    inp("COS", "Cost of sale at exit", 0.02, F_PCT1, "🔶", "net reversion")

    sect("SENIOR FINANCING  (→ Income Valuation tab)")
    inp("LTV", "Max senior LTV", 0.60, F_PCT1, "🔶", "debt sizing constraint 1")
    inp("DSCRMIN", "Min DSCR", 1.30, F_MULT, "🔶", "debt sizing constraint 2")
    inp("DYMIN", "Min debt yield", 0.085, F_PCT1, "🔶", "debt sizing constraint 3")
    inp("RATE", "Senior rate", 0.065, F_PCT2, "🔶", "debt service")
    inp("AMORT", "Amortization (yrs)", 30, F_YR, "🔶", "mortgage constant")

    sect("ACQUISITION COSTS  (→ Income Valuation Sources & Uses)")
    inp("DOCSTAMP", "Doc-stamp / transfer tax (% price)", 0.0070, F_PCT2, "🔶", "FL Broward $0.70/$100")
    inp("TITLE", "Title insurance (% price)", 0.0050, F_PCT2, "🔶", "closing cost")
    inp("LEGALDD", "Legal & due diligence (% price)", 0.0040, F_PCT2, "🔶", "closing cost")
    inp("ORIG", "Loan origination (% loan)", 0.0100, F_PCT2, "🔶", "financing cost → equity")

    sect("ASSEMBLAGE PREMIUM  (→ Assemblage tab, covered-land price)")
    inp("PREM_LOW", "Assemblage premium — low", 0.15, F_PCT1, "🔶", "control-cost premium (holdouts)")
    inp("PREM_BASE", "Assemblage premium — base", 0.20, F_PCT1, "🔶", "the headline covered-land price")
    inp("PREM_HIGH", "Assemblage premium — high", 0.25, F_PCT1, "🔶", "aggressive assemblage case")

    sect("LAND VALUATION — 1040 BAYVIEW  (→ Land tab matrix)")
    inp("LPSF_LOW", "Land value — low ($/SF)", 64.0, F_PSF, "🔶", "BCPA-implied floor")
    inp("LPSF_BASE", "Land value — base ($/SF)", 125.0, F_PSF, "🔶", "mid-block corridor")
    inp("LPSF_HIGH", "Land value — high ($/SF)", 200.0, F_PSF, "🔶", "toward hard-corner comps")
    inp("UNIT_LOW", "Per entitled unit — low ($)", 40000, F_ACCT, "🔶", "259 units")
    inp("UNIT_BASE", "Per entitled unit — base ($)", 55000, F_ACCT, "🔶", "entitled-land value")
    inp("UNIT_HIGH", "Per entitled unit — high ($)", 70000, F_ACCT, "🔶", "strong entitlement")

    sect("REDEVELOPMENT RESIDUAL — 1040 BAYVIEW  (→ Land tab)")
    inp("REVUNIT", "Achievable value per unit ($)", 600000, F_ACCT, "🔶", "sellout / cap'd rental value")
    inp("HARDPSF", "Hard cost ($/GBA SF)", 500.0, F_PSF, "🔶", "AE-zone coastal build")
    inp("GBAUNIT", "GBA per unit (SF)", 950, F_NUM, "🔶", "gross buildable per unit")
    inp("SOFT", "Soft cost (% hard)", 0.20, F_PCT1, "🔶", "A&E, financing, fees")
    inp("PROFIT", "Developer profit (% GDV)", 0.15, F_PCT1, "🔶", "required margin")
    r += 1
    return r   # first free row for the index


def build_index(s, regs, start_row):
    """Live register of every knowledge gap + asset-level driver, linked from source."""
    r = start_row
    def x(sheet, name):
        try:
            return f"='{sheet}'!{regs[sheet][name]}"
        except KeyError:
            return None

    s.section(r, L, 13, "DATA-GAP REGISTER  —  reported/estimated figures you can adjust (each shown from its source cell)"); r += 1
    s.put(r, L, "Gap / figure", style="subhead", align="left")
    s.put(r, 3, "Current", style="subhead", align="center")
    s.put(r, 4, "Flag", style="subhead", align="center")
    s.put(r, 5, "Adjust on tab → cell", style="subhead", align="left", merge=(r, 13)); r += 1

    # (sheet, name, label, fmt, flag, where-to-adjust)
    GAPS = [
        ("Sunrise Plaza", "GLA", "Sunrise Plaza — building SF", F_NUM, "⚠️", "Sunrise Plaza · Rentable SF"),
        ("Sunrise Plaza", "GLANDSF", "Sunrise Plaza — land SF", F_NUM, "⚠️", "Sunrise Plaza · Land SF"),
        ("Sunrise Plaza", "PRICE", "Sunrise Plaza — value / basis", F_ACCT, "⚠️", "Sunrise Plaza · Purchase price"),
        ("Publix & Starbucks", "GLANDSF", "Publix — land SF", F_NUM, "✅", "Publix & Starbucks · Land SF"),
        ("Office Condo", "GLA", "Office — building SF", F_NUM, "⚠️", "Office Condo · Rentable SF"),
        ("Office Condo", "OWN1_SF", "Office — Main St Fund SF (57.4%)", F_NUM, "⚠️", "Office Condo · owner-1 SF"),
        ("Office Condo", "OWN2_SF", "Office — Intl Sunrise SF (42.6%)", F_NUM, "⚠️", "Office Condo · owner-2 SF"),
        ("Office Condo", "PRICE", "Office — acquisition basis", F_ACCT, "🔶", "Office Condo · Acquisition basis"),
        ("Land", "LANDSF", "1040 Bayview — land SF", F_NUM, "⚠️", "Land · Land SF"),
        ("Land", "OFFSF", "1040 Bayview — office SF", F_NUM, "⚠️", "Land · Existing office SF"),
        ("Land", "UNITS", "1040 Bayview — entitled units", F_NUM, "⚠️", "Land · Entitled units"),
        ("Land", "BCPA", "1040 Bayview — BCPA value", F_ACCT, "⚠️", "Land · BCPA market value"),
    ]
    for sheet, name, label, fmt, flag, where in GAPS:
        link = x(sheet, name)
        s.put(r, L, label, style="label", align="left")
        if link:
            s.put(r, 3, link, style="calc", color="008000", fmt=fmt, align="center")
        else:
            s.put(r, 3, "n/a", style="note", align="center")
        s.put(r, 4, flag, style="calc", align="center")
        s.put(r, 5, where, style="note", align="left", merge=(r, 13)); r += 1
    r += 1

    s.section(r, L, 13, "ASSET OPERATING-ASSUMPTION INDEX  —  market rents & caps (blue on each asset tab)"); r += 1
    s.put(r, L, "Asset — driver", style="subhead", align="left")
    s.put(r, 3, "Current", style="subhead", align="center")
    s.put(r, 4, "Flag", style="subhead", align="center")
    s.put(r, 5, "Adjust on tab", style="subhead", align="left", merge=(r, 13)); r += 1
    IDX = [
        ("Shahidi Retail", "MRENT", "Shahidi — market rent ($/SF NNN)", F_PSF, "🔶"),
        ("Shahidi Retail", "STABOCC", "Shahidi — stabilized occupancy", F_PCT1, "🔶"),
        ("Shahidi Retail", "EXITCAP", "Shahidi — exit cap", F_PCT2, "🔶"),
        ("Publix & Starbucks", "MRENT", "Publix — blended market rent ($/SF)", F_PSF, "🔶"),
        ("Publix & Starbucks", "GICAP", "Publix — going-in cap", F_PCT2, "🔶"),
        ("Sunrise Plaza", "MRENT", "Sunrise Plaza — market rent ($/SF)", F_PSF, "🔶"),
        ("Sunrise Plaza", "GICAP", "Sunrise Plaza — going-in cap", F_PCT2, "🔶"),
        ("Office Condo", "MRENT", "Office — rent ($/SF MG)", F_PSF, "⚠️"),
        ("Office Condo", "GICAP", "Office — going-in cap", F_PCT2, "🔶"),
        ("Land", "IRENT", "1040 Bayview — interim office rent", F_PSF, "🔶"),
    ]
    for sheet, name, label, fmt, flag in IDX:
        link = x(sheet, name)
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, link if link else "n/a", style=("calc" if link else "note"), color=("008000" if link else None), fmt=fmt, align="center")
        s.put(r, 4, flag, style="calc", align="center")
        s.put(r, 5, sheet, style="note", align="left", merge=(r, 13)); r += 1
    r += 1
    s.put(r, L, "How to use", style="warn", align="left")
    s.put(r, 4, "Blue cells at the top of THIS tab drive valuation, financing, assemblage premium, and the land/redevelopment math. "
                "Asset-specific rents & caps are blue on each asset tab (green figures above are live and clickable). Change any blue cell → the whole model recalculates.",
          style="warn", align="left", merge=(r, 13)); r += 1
    s.freeze("C3")
    return s
