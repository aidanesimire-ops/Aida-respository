"""
tab_land.py — 1040 Bayview land / covered-land underwrite.
Existing 1967 office on 2.39 ac, entitled for 259 units. Underwritten as a
covered-land play: interim office income covers carry while the land is held
for redevelopment optionality. Four valuation approaches, interim income,
levered + unlevered hold returns, and a redevelopment residual (flagged).
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR)

L = 2
ACQ = 3
def pc(y): return 3 + y
def CL(c): return get_column_letter(c)

A = dict(
    land_sf=104108, office_sf=84495, units=259, commercial_sf=8081,
    bcpa_value=6685580,
    # valuation inputs
    land_psf_low=64.0, land_psf_base=125.0, land_psf_high=200.0,
    perunit_low=40000, perunit_base=55000, perunit_high=70000,
    # interim income (covered land)
    interim_occ=0.72, interim_rent=23.00, interim_opex_psf=8.00,
    interim_mgmt=0.03, millage=0.0191,
    # hold  (basis reset to the Willow Bridge trade: $24.7M / ~$95k per entitled unit, ~Aug 2026)
    price=24700000, closing_pct=0.02, land_growth=0.04, hold=5,
    ltv=0.40, loan_rate=0.0850, cost_sale=0.02, disc=0.10, exp_growth=0.03,
    # redevelopment residual (flagged — AE zone, hard costs high)
    rev_per_unit_value=600000,       # achievable per-unit value (rental cap'd / condo)
    hard_cost_psf=500.0, gba_per_unit=950, soft_pct=0.20, dev_profit=0.15,
)


def build(s, regs, amap=None):
    amap = amap or {}
    a = A
    def AS(name):   # link to the Assumptions control-panel cell
        return f"'Assumptions'!{regs['Assumptions'][name]}"
    s.colw({"A": 2.5, "B": 36, "C": 14, "D": 13, "E": 13, "F": 13, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "1040 BAYVIEW  ·  JV UPSIDE  (NOT in the 4-parcel core)", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "1040 Bayview Dr   |   Folio -0040   |   SOLD to WILLOW BRIDGE ~Aug 2026 for $24.7M (~$95k/entitled unit) · 2.39 ac · entitled 259 units "
                "· modeled here as a JV-upside case only — the base assemblage is the four parcels DAWN RE can control", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    s.section(r, L, 13, "PROPERTY FACTS  —  ⚠️ REPORTED (LoopNet / Florida YIMBY / BBX / Procacci; BCPA blocked in build env)"); r += 1
    facts = [
        ("⚠️ JUST TRADED (Aug 2026)", "Per The Real Deal, Procacci SOLD this entitled parcel to WILLOW BRIDGE PROPERTY CO. for $24.7M (~$95k per entitled unit; buyer financed $14.5M via RGA). This parcel appears to have changed hands — VERIFY, then re-approach as a JV with Willow Bridge or treat the block as four parcels."),
        ("Prior owner", "Sunrise & Bayview Partners, LLC (Procacci; folio -0040). Bought 2014 ≈ $7.9–8.0M (Procacci/BBX JV); BBX exited to Procacci 2022; Procacci sold to Willow Bridge ~Aug 2026"),
        ("Land", "2.39 ac ≈ 103,982 SF (BCPA) — same plat block (49-42-36-12) as the assemblage"),
        ("Existing improvement", "office building, built 1968 — leasable ≈ 84,495 SF (Redfin) / BCPA living area 101,803 SF; a redevelopment site, not raw land"),
        ("Zoning", "B-1 (Boulevard Business) / CB core commercial; rezoning case UDP-Z25002 filed Oct 2025, under P&Z review"),
        ("Entitlement (current)", "“The Residences at Bayview” — 259 units (247 market + 12 affordable @ ≤120% AMI), 8,081 SF commercial, 8 stories / 81 ft, 273,212 SF residential; MSA Architects, Lochrie & Chakas land-use counsel"),
        ("Entitlement (prior)", "2023 Site Plan Level III (superseded): two towers, 14-story N / 10-story S, 180 units, 14,671 SF commercial, 505-space garage"),
        ("Entitlement path", "City affordable-housing DENSITY BONUS via conventional rezoning (12 affordable units unlock the bonus) — NOT a Live Local approval"),
        ("Live Local optionality", "The B-1 commercial site independently QUALIFIES for the Live Local Act (SB 102/328/1730): ≥40% units ≤120% AMI would unlock citywide-max density + tallest-within-1-mile height administratively — a separate, higher-density path"),
        ("BCPA market value", "2015 assessed ≈ $8.25M (stale); current just value not confirmed (verify at BCPA)"),
        ("Status", "SOLD to Willow Bridge ~Aug 2026 at $24.7M / ~$95k per entitled unit — a live market comp for entitled land, and a changed counterparty for the assemblage"),
        ("Covered-land thesis", "Interim office income covers carry; the value is the entitled land + the redevelopment/Live Local density option"),
    ]
    for lab, val in facts:
        s.put(r, L, lab, style="calc", align="left")
        s.put(r, 4, val, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # inputs
    s.section(r, L, 13, "ASSUMPTIONS  —  🔵 blue = hardcoded inputs"); r += 1
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
    inp("LANDSF", "Land (SF)", "land_sf", F_NUM, "⚠️ 2.39 ac")
    inp("OFFSF", "Existing office SF", "office_sf", F_NUM, "⚠️ 1967 bldg")
    inp("UNITS", "Entitled units", "units", F_NUM, "⚠️ approved 259")
    inp("BCPA", "BCPA market value", "bcpa_value", F_ACCT_TOP, "⚠️ reported")
    inp("IOCC", "Interim office occupancy", "interim_occ", F_PCT1, "🔶 covered-land income")
    inp("IRENT", "Interim office rent ($/SF MG)", "interim_rent", F_PSF, "🔶")
    inp("IOPEX", "Interim office opex ($/SF)", "interim_opex_psf", F_PSF, "🔶 landlord (MG)")
    inp("IMGMT", "Management fee (% EGR)", "interim_mgmt", F_PCT1, "🔶")
    inp("MILL", "Effective millage", "millage", F_PCT2, "✅ area")
    inp("PRICE", "Acquisition basis (entitled land)", "price", F_ACCT_TOP, "🔶 ≈ 259 units × ~$50k")
    inp("CLOSE", "Closing & acq costs (% price)", "closing_pct", F_PCT1, "🔶")
    inp("LGROW", "Land value growth", "land_growth", F_PCT1, "🔶")
    inp("HOLD", "Hold period (yrs)", "hold", F_YR, "🔶 to redevelopment")
    inp("LTV", "Land loan LTV (IO)", "ltv", F_PCT1, "🔶 land/bridge")
    inp("RATE", "Land loan rate (IO)", "loan_rate", F_PCT2, "🔶 land premium")
    inp("COS", "Cost of sale at exit", "cost_sale", F_PCT1, "🔶")
    inp("DISC", "Discount rate (NPV)", "disc", F_PCT1, "🔶")
    inp("EGROW", "Expense growth", "exp_growth", F_PCT1, "🔶")
    r += 1
    g = s.reg
    def R(n): return g[n]

    # ---- valuation matrix ----
    s.section(r, L, 13, "LAND VALUATION  —  four approaches (Low / Base / High)"); r += 1
    s.put(r, L, "Approach", style="subhead", align="left")
    s.put(r, 4, "Low", style="subhead", align="right")
    s.put(r, 5, "Base", style="subhead", align="right")
    s.put(r, 6, "High", style="subhead", align="right")
    s.put(r, 7, "Basis / note", style="subhead", align="left", merge=(r, 13)); r += 1
    # per-SF land
    s.put(r, L, "① Per SF of land", style="label", align="left")
    s.put(r, 4, f"={R('LANDSF')}*{AS('LPSF_LOW')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 5, f"={R('LANDSF')}*{AS('LPSF_BASE')}", style="calc", fmt=F_ACCT_TOP, align="right", name="VAL_PSF")
    s.put(r, 6, f"={R('LANDSF')}*{AS('LPSF_HIGH')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 7, "land SF × $/SF (low/base/high on Assumptions tab)", style="note", align="left", merge=(r, 13)); r += 1
    # per unit
    s.put(r, L, "② Per entitled unit", style="label", align="left")
    s.put(r, 4, f"={R('UNITS')}*{AS('UNIT_LOW')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 5, f"={R('UNITS')}*{AS('UNIT_BASE')}", style="calc", fmt=F_ACCT_TOP, align="right", name="VAL_UNIT")
    s.put(r, 6, f"={R('UNITS')}*{AS('UNIT_HIGH')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 7, "units × $/unit (low/base/high on Assumptions tab)", style="note", align="left", merge=(r, 13)); r += 1
    # BCPA
    s.put(r, L, "③ BCPA market value (floor)", style="label", align="left")
    s.put(r, 4, f"={R('BCPA')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 5, f"={R('BCPA')}", style="calc", fmt=F_ACCT_TOP, align="right")
    s.put(r, 6, f"={R('BCPA')}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 7, "assessed just value — conservative floor", style="note", align="left", merge=(r, 13)); r += 1
    # income value
    s.put(r, L, "④ Interim income value", style="label", align="left")
    s.put(r, 4, "=INCVAL_L", style="calc", fmt=F_ACCT, align="right")   # patched below
    inc_row = r; r += 1
    s.put(r, L, "Concluded acquisition basis", style="subtotal", align="left")
    s.put(r, 5, f"={R('PRICE')}", style="subtotal", fmt=F_ACCT_TOP, align="right", name="CONCLUDED", bold=True)
    s.put(r, 7, "🔶 entitled-land basis used in the hold model & assemblage", style="note", align="left", merge=(r, 13)); r += 2

    # ---- interim income (covered land) ----
    s.section(r, L, 13, "INTERIM INCOME  —  existing office (the “cover” on the land)"); r += 1
    def der(name, label, formula, fmt, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    der("IGROSS", "Interim gross rent", f"={R('OFFSF')}*{R('IOCC')}*{R('IRENT')}", F_ACCT_TOP)
    der("IOPX", "Interim office opex", f"=-{R('OFFSF')}*{R('IOPEX')}", F_ACCT)
    der("ITAX", "Interim taxes (on basis)", f"=-{R('PRICE')}*{R('MILL')}", F_ACCT)
    der("IMG", "Interim management fee", f"=-{R('IGROSS')}*{R('IMGMT')}", F_ACCT)
    der("INOI", "Interim NOI (covers carry)", f"={R('IGROSS')}+{R('IOPX')}+{R('ITAX')}+{R('IMG')}", F_ACCT_TOP)
    der("INCVAL", "Interim income value @ 8% cap", f"={R('INOI')}/0.08", F_ACCT_TOP)
    r += 1
    # patch approach-④ income value cell now that INCVAL exists
    s.ws[f"D{inc_row}"] = f"={R('INCVAL')}"
    s.ws[f"E{inc_row}"] = f"={R('INCVAL')}"
    s.ws[f"F{inc_row}"] = f"={R('INCVAL')}"
    s.put(inc_row, 7, "existing office NOI ÷ 8% cap (income the land throws off)", style="note", align="left", merge=(inc_row, 13))

    # debt
    der("LOAN", "Land loan (IO)", f"={R('PRICE')}*{R('LTV')}", F_ACCT_TOP, "price × LTV")
    der("DS", "Annual interest (IO)", f"={R('LOAN')}*{R('RATE')}", F_ACCT_TOP)
    der("EQ_ACQ", "Equity at acquisition", f"={R('PRICE')}*(1+{R('CLOSE')})-{R('LOAN')}", F_ACCT_TOP)
    der("NETCARRY", "Interim net carry (NOI − interest)", f"={R('INOI')}-{R('DS')}", F_ACCT_TOP, "covered-land carry")
    r += 1

    # ---- covered-land hold cash flow ----
    s.section(r, L, 13, "COVERED-LAND HOLD  —  interim income + land appreciation (10-yr; unlevered & levered)"); r += 1
    s.put(r, L, "Year", style="subhead", align="left")
    s.put(r, ACQ, "0 / Acq", style="subhead", align="center")
    for y in range(1, 11): s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1
    rows = {}
    def cfrow(name, label, bold=False, top=False):
        nonlocal r
        rows[name] = r
        st = "subtotal" if top else ("label_b" if bold else "label")
        s.put(r, L, label, style=st, align="left"); return r
    # land value path
    rlv = cfrow("LANDVAL", "Land value (appreciating)")
    for y in range(1, 11): s.put(rlv, pc(y), f"={R('PRICE')}*(1+{R('LGROW')})^{y}", fmt=F_ACCT, align="right")
    r += 1
    rin = cfrow("INOIY", "Interim NOI")
    for y in range(1, 11): s.put(rin, pc(y), f"={R('INOI')}*(1+{R('EGROW')})^({y}-1)", fmt=F_ACCT, align="right")
    r += 1
    rsale = cfrow("SALE", "Net land sale (exit year)")
    for y in range(1, 11): s.put(rsale, pc(y), f"=IF({y}={R('HOLD')},{CL(pc(y))}{rows['LANDVAL']}*(1-{R('COS')}),0)", fmt=F_ACCT, align="right")
    r += 1
    run = cfrow("PROJCF", "UNLEVERED PROJECT CASH FLOW", bold=True, top=True)
    s.put(run, ACQ, f"=-{R('PRICE')}*(1+{R('CLOSE')})", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(run, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['INOIY']},0)+{CL(pc(y))}{rows['SALE']}",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 1
    rlbal = cfrow("LBAL", "Loan balance (IO — constant)")
    for y in range(1, 11): s.put(rlbal, pc(y), f"=IF({y}<={R('HOLD')},{R('LOAN')},0)", fmt=F_ACCT, align="right")
    r += 1
    rlev = cfrow("LEVCF", "LEVERED CASH FLOW (equity)", bold=True, top=True)
    s.put(rlev, ACQ, f"=-{R('EQ_ACQ')}", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rlev, pc(y), f"=IF({y}<={R('HOLD')},{CL(pc(y))}{rows['INOIY']}-{R('DS')},0)"
              f"+IF({y}={R('HOLD')},{CL(pc(y))}{rows['SALE']}-{R('LOAN')},0)",
              fmt=(F_ACCT_TOP if y == 1 else F_ACCT), align="right", bold=True)
    r += 2

    # returns
    s.section(r, L, 13, "COVERED-LAND RETURNS  —  unlevered & levered"); r += 1
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
    ret("GOINGIN", "Interim yield on basis (NOI ÷ price)", f"={R('INOI')}/{R('PRICE')}", F_PCT2)
    r += 1

    # ---- redevelopment residual (flagged) ----
    s.section(r, L, 13, "REDEVELOPMENT RESIDUAL  —  ⚠️ AE flood zone; residual runs NEGATIVE — DO NOT force positive"); r += 1
    def rd(name, label, formula, fmt, style="calc", note=""):
        nonlocal r
        s.put(r, L, label, style=("subtotal" if style == "sub" else "label"), align="left")
        s.put(r, 3, formula, style=("calc"), fmt=fmt, align="right", name=name, bold=(style == "sub"))
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    rd("GDV", "Gross development value", f"={R('UNITS')}*{AS('REVUNIT')}", F_ACCT_TOP,
       note="units × achievable value/unit (Assumptions tab)")
    rd("GBA", "Buildable GBA (SF)", f"={R('UNITS')}*{AS('GBAUNIT')}", F_NUM, note="units × GBA/unit (Assumptions tab)")
    rd("HARD", "Hard cost", f"=-{R('GBA')}*{AS('HARDPSF')}", F_ACCT, note="$/GBA SF (AE-zone coastal, Assumptions tab)")
    rd("SOFT", "Soft cost", f"=-{R('GBA')}*{AS('HARDPSF')}*{AS('SOFT')}", F_ACCT, note="% of hard (Assumptions tab)")
    rd("PROFIT", "Developer profit", f"=-{R('GDV')}*{AS('PROFIT')}", F_ACCT, note="% of GDV (Assumptions tab)")
    rd("RESID", "RESIDUAL LAND VALUE", f"={R('GDV')}+{R('HARD')}+{R('SOFT')}+{R('PROFIT')}", F_ACCT_TOP, style="sub")
    s.put(r, L, "Conclusion", style="warn", align="left")
    s.put(r, 3, "HOLD", style="warn", align="center")
    s.put(r, 4, "Residual < entitled-land basis at the modeled $500/SF hard cost → redevelopment does not pencil TODAY; hold as covered land. "
                "But note: mid-2026 research puts defensible AE-coastal concrete at $300–450/SF — dial the hard cost toward that on the Assumptions "
                "tab and the residual approaches break-even. The option is closer to the money than a single point implies.",
          style="warn", align="left", merge=(r, 13)); r += 1

    # row anchors for the consolidated income tab (land: interim NOI, no capital)
    s.reg["ROW_NOI"] = f"D{rows['INOIY']}"
    s.reg["ROW_REV"] = f"D{rows['SALE']}"

    s.freeze("C6")
    return s
