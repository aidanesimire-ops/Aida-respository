"""
tab_assemblage.py — the assemblage rolled up as a COVERED LAND PLAY.
Combines all five assets (green cross-sheet links), derives the blended
going-in cap, land basis, and total acquisition cost, tests highest-and-best-use
(redevelopment residual — negative → hold), and blends levered/unlevered returns.
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM)

L = 2
def CL(c): return get_column_letter(c)

# per-asset land SF (verified BCPA facts; office is a condo -> no land parcel)
LANDSFCELL = {"Shahidi Retail": "LANDSF", "Publix & Starbucks": "GLANDSF",
              "Sunrise Plaza": "GLANDSF", "Office Condo": None, "Land": "LANDSF"}
LANDSF = {"Shahidi Retail": 67080, "Publix & Starbucks": 109791,
          "Sunrise Plaza": 30928, "Office Condo": 0, "Land": 104108}
GLA = {"Shahidi Retail": 26272, "Publix & Starbucks": 36822,
       "Sunrise Plaza": 25105, "Office Condo": 168807, "Land": 84495}

# control-cost source cell per asset (covered-land control basis)
CONTROL = {"Shahidi Retail": "PRICE", "Publix & Starbucks": "PRICE",
           "Sunrise Plaza": "PRICE", "Office Condo": "BUYOUT_TOTAL", "Land": "CONCLUDED"}
NOICELL = {"Shahidi Retail": "INPLACE_NOI", "Publix & Starbucks": "NOI1",
           "Sunrise Plaza": "NOI1", "Office Condo": "NOI1", "Land": "INOI"}
LANDVALCELL = {"Shahidi Retail": "LANDVAL", "Publix & Starbucks": "LANDVAL",
               "Sunrise Plaza": "LANDVAL", "Office Condo": None, "Land": "CONCLUDED"}
EQCELL = {"Shahidi Retail": "EQ_REQ", "Publix & Starbucks": "EQ_REQ",
          "Sunrise Plaza": "EQ_REQ", "Office Condo": "EQ_REQ", "Land": "EQ_ACQ"}

# CORE assemblage = the four parcels DAWN RE controls. Bayview (the "Land" tab) sold
# to Willow Bridge (~Aug 2026); it is modeled separately as a JV-upside, not in the base.
ORDER = ["Shahidi Retail", "Publix & Starbucks", "Sunrise Plaza", "Office Condo"]
LABEL = {"Shahidi Retail": "Shahidi Retail (Galleria Plaza)",
         "Publix & Starbucks": "Publix + Starbucks",
         "Sunrise Plaza": "Sunrise Plaza (Kar Luen)",
         "Office Condo": "Galleria Corporate Centre (office)",
         "Land": "1040 Bayview (covered land)"}
NOTE = {"Shahidi Retail": "acquirable · value-add lease-up",
        "Publix & Starbucks": "sale-leaseback · acquire fee, lease back",
        "Sunrise Plaza": "acquirable · restaurant value-add",
        "Office Condo": "buy out both condo owners",
        "Land": "entitled 259 units · hold for redevelopment"}


def build(s, regs):
    def x(sheet, name):
        return f"'{sheet}'!{regs[sheet][name]}"
    s.colw({"A": 2.5, "B": 34, "C": 16, "D": 15, "E": 13, "F": 15, "G": 11,
            "H": 11, "I": 20, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "THE ASSEMBLAGE  ·  COVERED LAND PLAY", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "E Sunrise Blvd @ the Galleria — four core parcels (Bayview, a 5th, sold to Willow Bridge → JV upside), plat block 49-42-36-12 · "
                "buy the income, control the dirt · highest & best use = hold for Live Local density",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # thesis
    s.section(r, L, 13, "THE COVERED-LAND THESIS"); r += 1
    thesis = [
        "Assemble the whole E Sunrise Blvd frontage at the Galleria hard corner. Each asset is bought/valued off the rent it produces;",
        "the in-place income covers the carry (debt service, taxes, insurance) while DAWN RE controls ~7+ acres for eventual redevelopment.",
        "Redevelopment does NOT pencil today (AE flood zone, coastal hard costs → negative residual), so the play is to HOLD the income-",
        "covered land and hold the Live Local density option. Publix already proved the model — it paid land value ($679/SF bldg), not income value.",
    ]
    for t in thesis:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---- asset roll-up ----
    s.section(r, L, 13, "ASSET ROLL-UP  —  🟢 green = live links to each asset tab"); r += 1
    hdr = ["Asset", "Control cost", "In-place NOI", "Going-in cap", "Land SF",
           "Land value", "Unlev IRR", "Lev IRR", "Note"]
    cols = [L, 3, 4, 5, 6, 7, 8, 9, 10]
    spans = {10: 13}
    for h, c in zip(hdr, cols):
        endc = spans.get(c, c)
        s.put(r, c, h, style="subhead", align="left" if c in (L, 10) else "center",
              merge=(r, endc) if endc != c else None)
    r += 1
    first = r
    for a in ORDER:
        s.put(r, L, LABEL[a], style="calc", align="left")
        s.put(r, 3, f"={x(a, CONTROL[a])}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 4, f"={x(a, NOICELL[a])}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 5, f"={CL(4)}{r}/{CL(3)}{r}", style="calc", fmt=F_PCT2, align="right")
        if LANDSFCELL[a]:
            s.put(r, 6, f"={x(a, LANDSFCELL[a])}", style="calc", color="008000", fmt=F_NUM, align="right")
        else:
            s.put(r, 6, 0, style="calc", fmt=F_NUM, align="right")   # office condo: no land parcel
        if LANDVALCELL[a]:
            s.put(r, 7, f"={x(a, LANDVALCELL[a])}", style="calc", color="008000", fmt=F_ACCT, align="right")
        else:
            s.put(r, 7, "=0", style="calc", fmt=F_ACCT, align="right")   # office condo: no land parcel
        s.put(r, 8, f"={x(a, 'IRR_U')}", style="calc", color="008000", fmt=F_PCT1, align="right")
        s.put(r, 9, f"={x(a, 'IRR_L')}", style="calc", color="008000", fmt=F_PCT1, align="right")
        s.put(r, 10, NOTE[a], style="calc", align="left", merge=(r, 13))
        r += 1
    last = r - 1
    s.put(r, L, "ASSEMBLAGE TOTAL (pre-premium)", style="total", align="left")
    s.put(r, 3, f"=SUM({CL(3)}{first}:{CL(3)}{last})", style="total", fmt=F_ACCT_TOP, align="right", name="RAW_COST")
    s.put(r, 4, f"=SUM({CL(4)}{first}:{CL(4)}{last})", style="total", fmt=F_ACCT_TOP, align="right", name="TOT_NOI")
    s.put(r, 5, f"={CL(4)}{r}/{CL(3)}{r}", style="total", fmt=F_PCT2, align="right", name="BLEND_CAP")
    s.put(r, 6, f"=SUM({CL(6)}{first}:{CL(6)}{last})", style="total", fmt=F_NUM, align="right", name="TOT_LANDSF")
    s.put(r, 7, f"=SUM({CL(7)}{first}:{CL(7)}{last})", style="total", fmt=F_ACCT_TOP, align="right", name="TOT_LANDVAL")
    s.put(r, 8, "—", style="total", align="center")
    s.put(r, 9, "—", style="total", align="center")
    s.put(r, 10, "blended going-in cap covers carry", style="total", align="left", merge=(r, 13))
    r += 2

    # ---- covered-land metrics ----
    s.section(r, L, 13, "COVERED-LAND METRICS  &  ACQUISITION COST"); r += 1
    def m(name, label, formula, fmt, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", fmt=fmt, align="right", name=name)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    m("TOT_GLA", "Total existing building (GLA, SF)", f"={sum(GLA.values())}", F_NUM, "existing improvements across all five")
    m("TOT_AC", "Total land assembled (acres)", f"={s.reg['TOT_LANDSF']}/43560", "#,##0.00", "≈ 7+ acres of E Sunrise frontage")
    m("BLEND_LANDPSF", "Blended land basis ($/SF)", f"={s.reg['TOT_LANDVAL']}/{s.reg['TOT_LANDSF']}", F_PSF,
      "vs. subject comps $228–255/SF; Galleria bulk $53/SF")
    m("BLEND_CAP2", "Blended in-place cap (income ÷ cost)", f"={s.reg['TOT_NOI']}/{s.reg['RAW_COST']}", F_PCT2,
      "covered-land range ~3–5% — income covers carry, not a yield play")
    r += 1
    # assemblage premium (rates live on the Assumptions tab)
    pl = f"'Assumptions'!{regs['Assumptions']['PREM_LOW']}"
    pb = f"'Assumptions'!{regs['Assumptions']['PREM_BASE']}"
    ph = f"'Assumptions'!{regs['Assumptions']['PREM_HIGH']}"
    s.put(r, L, "Assemblage premium (to control holdouts)", style="subhead", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "  Low", style="label", align="left")
    s.put(r, 3, f"={s.reg['RAW_COST']}*(1+{pl})", style="calc", fmt=F_ACCT, align="right", name="ACQ_LOW")
    s.put(r, 4, f"={pl}", style="calc", color="008000", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "  Base", style="label_b", align="left")
    s.put(r, 3, f"={s.reg['RAW_COST']}*(1+{pb})", style="calc", fmt=F_ACCT_TOP, align="right", name="ACQ_BASE", bold=True)
    s.put(r, 4, f"={pb}", style="calc", color="008000", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "  High", style="label", align="left")
    s.put(r, 3, f"={s.reg['RAW_COST']}*(1+{ph})", style="calc", fmt=F_ACCT, align="right", name="ACQ_HIGH")
    s.put(r, 4, f"={ph}", style="calc", color="008000", fmt=F_PCT1, align="right"); r += 1
    s.put(r, L, "TOTAL ASSEMBLAGE ACQUISITION COST (base)", style="grand", align="left")
    s.put(r, 3, f"={s.reg['ACQ_BASE']}", style="grand", fmt=F_ACCT_TOP, align="right", name="ACQ")
    s.put(r, 4, "🔶 base premium (Assumptions tab) on the summed control cost", style="note", align="left", merge=(r, 13)); r += 2

    # ---- HBU ----
    s.section(r, L, 13, "HIGHEST & BEST USE  —  redevelopment residual (Live Local) vs. hold"); r += 1
    s.put(r, L, "Redevelopment residual — 1040 Bayview (per Land tab)", style="label", align="left")
    s.put(r, 3, f"={x('Land', 'RESID')}", style="calc", color="008000", fmt=F_ACCT_TOP, align="right"); r += 1
    s.put(r, L, "Redevelopment verdict", style="warn", align="left")
    s.put(r, 3, "HOLD", style="warn", align="center")
    s.put(r, 4, "Residual runs NEGATIVE in the AE flood zone at current coastal hard costs — do not force it positive. "
                "Best use today = hold the income-covered land + Live Local density option until costs/rents support redevelopment.",
          style="warn", align="left", merge=(r, 13)); r += 2

    # ---- portfolio capital (returns live on the Income Valuation tab) ----
    s.section(r, L, 13, "PORTFOLIO CAPITAL  —  consolidated returns computed on the Income Valuation tab"); r += 1
    eqsum = "+".join(x(a, EQCELL[a]) for a in ORDER)
    s.put(r, L, "Total equity required (all assets, at asset prices)", style="label", align="left")
    s.put(r, 3, f"={eqsum}", style="calc", fmt=F_ACCT_TOP, align="right", name="TOT_EQ"); r += 1
    s.put(r, L, "Total in-place NOI (covers carry)", style="label", align="left")
    s.put(r, 3, f"={s.reg['TOT_NOI']}", style="calc", fmt=F_ACCT_TOP, align="right"); r += 1
    s.put(r, L, "Portfolio IRR (unlevered / levered)", style="warn", align="left")
    s.put(r, 4, "Computed from the CONSOLIDATED cash flows on the Income Valuation tab — never by averaging asset IRRs "
                "(mathematically invalid). See that tab for portfolio returns at both the income and covered-land prices.",
          style="warn", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
