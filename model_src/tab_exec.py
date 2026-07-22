"""
tab_exec.py — Executive Summary (Tab 1). Outputs only; every value is a live
green cross-sheet link. KPI banner, the covered-land deal, per-asset scorecard,
capital & returns, and the recommendation.
"""
from openpyxl.utils import get_column_letter
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM)

L = 2
def CL(c): return get_column_letter(c)

ORDER = ["Shahidi Retail", "Publix & Starbucks", "Sunrise Plaza", "Office Condo", "Land"]
LABEL = {"Shahidi Retail": "Shahidi Retail (Galleria Plaza)",
         "Publix & Starbucks": "Publix + Starbucks",
         "Sunrise Plaza": "Sunrise Plaza (Kar Luen)",
         "Office Condo": "Galleria Corporate Centre",
         "Land": "1040 Bayview (land)"}
ADDR = {"Shahidi Retail": "2541–2595 E Sunrise · 26,272 SF retail",
        "Publix & Starbucks": "2501–2519 E Sunrise · 36,822 SF grocery + pad",
        "Sunrise Plaza": "2465–2485 E Sunrise · 25,105 SF retail",
        "Office Condo": "2455 E Sunrise · 168,807 SF office condo",
        "Land": "1040 Bayview Dr · 2.39 ac · 259 units entitled"}
CONTROL = {"Shahidi Retail": "PRICE", "Publix & Starbucks": "LANDVAL",
           "Sunrise Plaza": "PRICE", "Office Condo": "PRICE", "Land": "CONCLUDED"}
NOICELL = {"Shahidi Retail": "INPLACE_NOI", "Publix & Starbucks": "NOI1",
           "Sunrise Plaza": "NOI1", "Office Condo": "NOI1", "Land": "INOI"}


def build(s, regs):
    def x(sheet, name):
        return f"'{sheet}'!{regs[sheet][name]}"
    s.colw({"A": 2.5, "B": 30, "C": 17, "D": 17, "E": 17, "F": 17, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    A = "Assemblage"
    r = 1
    # banner
    s.put(r, L, "DAWN RE ENTERPRISES CORP.", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "E SUNRISE BLVD ASSEMBLAGE  ·  COVERED LAND PLAY  —  EXECUTIVE SUMMARY", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 20); r += 1
    s.put(r, L, "Fort Lauderdale, FL 33304  ·  Galleria hard corner  ·  five contiguous assets, plat block 49-42-36-12  ·  prepared 2026-07-21  ·  CONFIDENTIAL",
          style="kpi_note", align="left", merge=(r, 13)); s.rowh(r, 16); r += 2

    # ---- KPI boxes (4 across) ----
    IV = "Income Valuation"
    kpis = [
        ("INCOME-BASED PRICE", f"={x(IV,'PX_INCOME')}", F_ACCT_TOP, "what the combined cash flows support"),
        ("COVERED-LAND PRICE", f"={x(A,'ACQ')}", F_ACCT_TOP, "HBU: land value + assemblage premium"),
        ("BLENDED IN-PLACE CAP", f"={x(A,'BLEND_CAP2')}", F_PCT2, "income covers carry"),
        ("LAND CONTROLLED", f"={x(A,'TOT_AC')}", "#,##0.00", "acres of E Sunrise frontage"),
    ]
    c = 2
    for lab, val, fmt, note in kpis:
        s.put(r, c, lab, style="kpi_lab", align="center", merge=(r, c+2))
        s.put(r+1, c, val, style="kpi_val", fmt=fmt, align="center", merge=(r+1, c+2))
        s.put(r+2, c, note, style="kpi_note", align="center", merge=(r+2, c+2))
        c += 3
    s.rowh(r, 16); s.rowh(r+1, 34); s.rowh(r+2, 16); r += 4

    # ---- the deal ----
    s.section(r, L, 13, "THE DEAL"); r += 1
    deal = [
        "Assemble the entire E Sunrise Blvd frontage at the Galleria hard corner (~60,000 vehicles/day, across from the 31.5-ac Galleria",
        "redevelopment and the Live Local corridor). Five contiguous assets on one plat block. Strategy: buy/value each asset off the rent it",
        "produces, let the in-place income cover the carry, and control ~7+ acres for eventual Live Local high-density redevelopment. The",
        "redevelopment residual is negative today (AE flood zone, coastal hard costs), so the disciplined play is to HOLD income-covered land.",
        "Publix already validated the thesis — it paid land value ($679/SF building), not income value, to control its parcel.",
    ]
    for t in deal:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1

    # ---- per-asset scorecard ----
    s.section(r, L, 13, "ASSET SCORECARD  —  🟢 live links to each asset tab"); r += 1
    hdr = ["Asset", "Address / size", "Control cost", "In-place NOI", "Unlev IRR", "Lev IRR"]
    cols = [L, 4, 7, 8, 10, 11]
    spans = {4: 6, 8: 9, 11: 13}
    for h, c in zip(hdr, cols):
        endc = spans.get(c, c)
        s.put(r, c, h, style="subhead", align="left" if c in (L, 4) else "center", merge=(r, endc) if endc != c else None)
    r += 1
    first = r
    for a in ORDER:
        s.put(r, L, LABEL[a], style="calc", align="left")
        s.put(r, 4, ADDR[a], style="calc", align="left", merge=(r, 6))
        s.put(r, 7, f"={x(a, CONTROL[a])}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 8, f"={x(a, NOICELL[a])}", style="calc", color="008000", fmt=F_ACCT, align="right", merge=(r, 9))
        s.put(r, 10, f"={x(a, 'IRR_U')}", style="calc", color="008000", fmt=F_PCT1, align="right")
        s.put(r, 11, f"={x(a, 'IRR_L')}", style="calc", color="008000", fmt=F_PCT1, align="right", merge=(r, 13))
        r += 1
    last = r - 1
    s.put(r, L, "ASSEMBLAGE (pre-premium)", style="total", align="left")
    s.put(r, 4, "5 assets · ~7+ ac · 341,501 SF bldg", style="total", align="left", merge=(r, 6))
    s.put(r, 7, f"={x(A,'RAW_COST')}", style="total", color=None, fmt=F_ACCT_TOP, align="right")
    s.put(r, 8, f"={x(A,'TOT_NOI')}", style="total", fmt=F_ACCT_TOP, align="right", merge=(r, 9))
    s.put(r, 10, f"={x(IV,'IRR_U')}", style="total", fmt=F_PCT1, align="right")
    s.put(r, 11, f"={x(IV,'IRR_L')}", style="total", fmt=F_PCT1, align="right", merge=(r, 13))
    r += 1
    s.put(r, L, "Portfolio IRR (unlev / lev) = consolidated cash-flow IRR at the income price (Income Valuation tab)",
          style="note", align="left", merge=(r, 13)); r += 2

    # ---- capital & valuation ----
    s.section(r, L, 13, "CAPITAL, VALUATION  &  COVERED-LAND MATH"); r += 1
    def kv(label, formula, fmt, col=3, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, formula, style="calc", color="008000", fmt=fmt, align="right")
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    kv("① Income-based price (assemblage cash flows)", f"={x(IV,'PX_INCOME')}", F_ACCT_TOP, note="direct cap on consolidated in-place NOI")
    kv("② Covered-land / HBU price (control cost)", f"={x(A,'ACQ')}", F_ACCT_TOP, note="land value + 20% assemblage premium")
    kv("Premium over income value (dirt + optionality)", f"={x(IV,'PREMIUM')}", F_ACCT_TOP, note="② − ① = the land / Live Local option cost")
    kv("Summed control cost (pre-premium)", f"={x(A,'RAW_COST')}", F_ACCT_TOP)
    kv("Total equity required (all assets, HBU)", f"={x(A,'TOT_EQ')}", F_ACCT_TOP)
    kv("Total in-place NOI", f"={x(A,'TOT_NOI')}", F_ACCT_TOP, note="covers debt service + taxes during hold")
    kv("Blended in-place cap", f"={x(A,'BLEND_CAP2')}", F_PCT2, note="covered-land ~3–5% range")
    kv("Total land assembled (SF)", f"={x(A,'TOT_LANDSF')}", F_NUM)
    kv("Blended land basis ($/SF)", f"={x(A,'BLEND_LANDPSF')}", F_PSF, note="vs. subject comps $228–255/SF")
    kv("Total land value", f"={x(A,'TOT_LANDVAL')}", F_ACCT_TOP)
    kv("Redevelopment residual (Live Local)", f"={x('Land','RESID')}", F_ACCT_TOP, note="NEGATIVE → hold, do not redevelop yet")
    r += 1

    # ---- returns at income price + scenario range ----
    s.section(r, L, 13, "RETURNS AT THE INCOME PRICE  &  SCENARIO RANGE"); r += 1
    SC = "Scenarios"
    kv("Portfolio unlevered / levered IRR (base)", f"={x(IV,'IRR_L')}", F_PCT1, note="levered; unlevered on Income Valuation tab")
    s.put(r, L, "Levered IRR — downside / base / upside", style="label", align="left")
    s.put(r, 3, f"={x(SC,'IRRL_DOWN')}", style="calc", color="008000", fmt=F_PCT1, align="right")
    s.put(r, 4, f"={x(IV,'IRR_L')}", style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 5, f"={x(SC,'IRRL_UP')}", style="calc", color="008000", fmt=F_PCT1, align="left")
    s.put(r, 6, "recession → plan → tailwind (see Scenarios tab)", style="note", align="left", merge=(r, 13)); r += 1
    kv("Avg cash-on-cash (base, levered)", f"={x(IV,'COC_AVG_I')}", F_PCT1, note="current yield on equity")
    kv("Break-even exit cap (return of capital)", f"={x(IV,'BE_EXITCAP')}", F_PCT2, note="downside guardrail; underwritten exit 6.75%")
    kv("Total equity (income price) / LTC", f"={x(IV,'EQ_I')}", F_ACCT_TOP, note="see Sources & Uses on Income Valuation tab")
    r += 1

    # ---- recommendation ----
    s.section(r, L, 13, "RECOMMENDATION"); r += 1
    rec = [
        "ACQUIRE & HOLD as a covered land play. Pursue the acquirable parcels (Shahidi, Sunrise Plaza, the two office-condo owners, and",
        "the Bayview land); treat Publix as a long-dated, land-value option (not a current seller). The blended in-place income covers the",
        "carry, individual assets deliver value-add / income returns in their own right, and the assemblage banks ~7+ acres of the Galleria",
        "hard corner for Live Local density once coastal hard costs and achievable rents make redevelopment pencil. Do not underwrite the",
        "redevelopment as accretive today — the residual is negative. The return is optionality on the dirt, paid for by the rent.",
    ]
    for t in rec:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1
    s.put(r, L, "Confidence flags", style="note", align="left")
    s.put(r, 4, "✅ Shahidi & Publix = BCPA-verified · ⚠️ Sunrise Plaza, Office, Land = reported (BCPA blocked in build env — verify at bcpa.net) · 🔶 all rents/caps modeled",
          style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
