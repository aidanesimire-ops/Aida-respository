"""
tab_exec.py — EXECUTIVE DASHBOARD (Tab 1). One dense command center for the whole
assemblage: headline KPIs, the valuation ladder, a per-component scorecard (what
each owner paid vs. our price + returns), land / highest-and-best-use, returns +
scenario range, and capital. Outputs only — every value is a live green link.
Template note: swap the component list + Assumptions inputs to reuse for any assemblage.
"""
from openpyxl.utils import get_column_letter
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM

L = 2
def CL(c): return get_column_letter(c)

# component -> (sheet, label, size, control-cost cell, in-place NOI cell,
#               Assumptions prior-sale price name | None, Assumptions prior-sale year name)
COMP = [
    ("Shahidi Retail", "Shahidi Retail (Galleria Plaza)", "26,272 SF retail", "PRICE", "INPLACE_NOI", "SHA_ACQ", "SHA_ACQYR"),
    ("Publix & Starbucks", "Publix + Starbucks (SLB)", "36,822 SF grocery+pad", "PRICE", "NOI1", "PUB_ACQ", "PUB_ACQYR"),
    ("Sunrise Plaza", "Sunrise Plaza (Kar Luen)", "25,105 SF retail", "PRICE", "NOI1", "SUN_ACQ", "SUN_ACQYR"),
    ("Office Condo", "Galleria Corp Centre (buy-out)", "168,807 SF office condo", "BUYOUT_TOTAL", "NOI1", "OFF_ACQ", "OFF_ACQYR"),
]


def build(s, regs):
    def x(sheet, name):
        return f"'{sheet}'!{regs[sheet][name]}"
    A, IV, HB, SC = "Assemblage", "Income Valuation", "Highest & Best Use", "Scenarios"
    s.colw({"A": 2, "B": 30, "C": 20, "D": 13, "E": 7, "F": 14, "G": 13, "H": 9,
            "I": 9, "J": 9, "K": 9, "L": 9, "M": 9})
    r = 1
    # ---------------- banner ----------------
    s.put(r, L, "DAWN RE ENTERPRISES CORP.  ·  EXECUTIVE DASHBOARD", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "E SUNRISE BLVD ASSEMBLAGE  —  COVERED LAND PLAY", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 1
    s.put(r, L, "Fort Lauderdale FL 33304 · Galleria hard corner · 4-parcel core (+ Bayview JV upside) · plat 49-42-36-12 · 341,501 SF existing · CONFIDENTIAL",
          style="kpi_note", align="left", merge=(r, 13)); s.rowh(r, 15); r += 2

    # ---------------- KPI strip (6 across) ----------------
    kpis = [
        ("INCOME PRICE", f"={x(IV,'PX_INCOME')}", F_ACCT_TOP),
        ("COVERED-LAND", f"={x(A,'ACQ')}", F_ACCT_TOP),
        ("BLENDED CAP", f"={x(A,'BLEND_CAP2')}", F_PCT2),
        ("LEVERED IRR", f"={x(IV,'IRR_L')}", F_PCT1),
        ("EQUITY", f"={x(IV,'EQ_I')}", F_ACCT_TOP),
        ("LAND (AC)", f"={x(A,'TOT_AC')}", "#,##0.0"),
    ]
    c = 2
    for lab, val, fmt in kpis:
        s.put(r, c, lab, style="kpi_lab", align="center", merge=(r, c+1))
        s.put(r+1, c, val, style="kpi_val", fmt=fmt, align="center", merge=(r+1, c+1))
        c += 2
    s.rowh(r, 14); s.rowh(r+1, 30); r += 3

    # ---------------- valuation ladder ----------------
    s.section(r, L, 13, "VALUATION LADDER  —  three ways to price the block"); r += 1
    def band(label, formula, fmt, note, style="calc", nm=None):
        nonlocal r
        s.put(r, L, label, style=("grand" if style == "grand" else "label"), align="left", merge=(r, 4))
        s.put(r, 5, formula, style=("grand" if style == "grand" else "calc"), color=(None if style == "grand" else "008000"),
              fmt=fmt, align="right", merge=(r, 6), name=nm)
        s.put(r, 7, note, style="note", align="left", merge=(r, 13)); r += 1
    band("① Income basis (combined cash flows)", f"={x(IV,'PX_INCOME')}", F_ACCT_TOP, "direct cap on consolidated in-place NOI — what the rent supports")
    band("② Sum of the parts (each priced alone)", f"={x(HB,'SUM_PARTS')}", F_ACCT_TOP, "buy each component independently")
    band("③ COVERED-LAND / HBU (assembled)", f"={x(A,'ACQ')}", F_ACCT_TOP, "sum of parts + assemblage premium — control the whole block", style="grand")
    band("Premium over income (dirt + optionality)", f"={x(IV,'PREMIUM')}", F_ACCT_TOP, "③ − ① = what you pay for the land / Live Local option")
    band("Post-approval assembled land (upside)", f"={x(HB,'LAND_ENTITLED')}", F_ACCT_TOP, "entitled dirt once Live Local is approved")
    r += 1

    # ---------------- component scorecard ----------------
    s.section(r, L, 13, "COMPONENT SCORECARD  —  priced independently  (what they paid → our price → return)"); r += 1
    hdr = [(L, "Component"), (3, "Size"), (4, "They paid"), (5, "Yr"), (6, "Our price"),
           (7, "In-place NOI"), (8, "Cap"), (9, "Lev IRR"), (10, "Basis / note")]
    for c, h in hdr:
        endc = 13 if c == 10 else c
        s.put(r, c, h, style="subhead", align="left" if c in (L, 10) else "center", merge=(r, endc) if endc != c else None)
    r += 1
    first = r
    for key, label, size, ctrl, noic, acqname, yrname in COMP:
        s.put(r, L, label, style="calc", align="left")
        s.put(r, 3, size, style="note", align="left")
        if acqname:
            s.put(r, 4, f"={x('Assumptions', acqname)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        else:
            s.put(r, 4, "—", style="note", align="right")
        s.put(r, 5, f"={x('Assumptions', yrname)}", style="calc", color="008000", fmt="0", align="center")
        s.put(r, 6, f"={x(key, ctrl)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 7, f"={x(key, noic)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 8, f"={CL(7)}{r}/{CL(6)}{r}", style="calc", fmt=F_PCT2, align="center")
        s.put(r, 9, f"={x(key, 'IRR_L')}", style="calc", color="008000", fmt=F_PCT1, align="center")
        note = {"Publix & Starbucks": "sale-leaseback · land exit",
                "Office Condo": "unit-market buy-out; fractured condo",
                "Land": "entitled 259 units · covered land"}.get(key, "acquire fee")
        s.put(r, 10, note, style="note", align="left", merge=(r, 13)); r += 1
    last = r - 1
    s.put(r, L, "ASSEMBLAGE — priced independently", style="total", align="left")
    s.put(r, 3, "4 parcels", style="total", align="left")
    s.put(r, 4, "—", style="total", align="center")
    s.put(r, 5, "", style="total")
    s.put(r, 6, f"={x(A,'RAW_COST')}", style="total", fmt=F_ACCT_TOP, align="right")
    s.put(r, 7, f"={x(A,'TOT_NOI')}", style="total", fmt=F_ACCT_TOP, align="right")
    s.put(r, 8, f"={x(A,'BLEND_CAP2')}", style="total", fmt=F_PCT2, align="center")
    s.put(r, 9, f"={x(IV,'IRR_L')}", style="total", fmt=F_PCT1, align="center")
    s.put(r, 10, "portfolio lev IRR = consolidated cash-flow IRR", style="total", align="left", merge=(r, 13)); r += 2

    # ---------------- land & HBU + returns (two columns) ----------------
    s.section(r, L, 6, "LAND  &  HIGHEST-AND-BEST-USE")
    s.section(r, 7, 13, "RETURNS  (at income price)"); r += 1
    def twocol(l1, f1, fmt1, l2, f2, fmt2):
        nonlocal r
        s.put(r, L, l1, style="label", align="left", merge=(r, 3))
        s.put(r, 4, f1, style="calc", color="008000", fmt=fmt1, align="right", merge=(r, 6))
        s.put(r, 7, l2, style="label", align="left", merge=(r, 9))
        s.put(r, 10, f2, style="calc", color="008000", fmt=fmt2, align="right", merge=(r, 13)); r += 1
    twocol("Land — fragmented parcels", f"={x(HB,'LAND_FRAG')}", F_ACCT, "Unlevered / levered IRR", f"={x(IV,'IRR_U')}", F_PCT1)
    twocol("Land — assembled (plottage)", f"={x(HB,'LAND_ASM')}", F_ACCT, "Levered equity multiple", f"={x(IV,'EML_I')}", F_MULT)
    twocol("Plottage premium", f"={x(HB,'PLOTTAGE')}", F_ACCT, "Avg cash-on-cash (levered)", f"={x(IV,'COC_AVG_I')}", F_PCT1)
    twocol("Office condo FULL BUY-OUT", f"={x('Office Condo','BUYOUT_TOTAL')}", F_ACCT, "Year-1 DSCR", f"={x(IV,'DSCR_I')}", F_MULT)
    twocol("Blended land basis ($/SF)", f"={x(A,'BLEND_LANDPSF')}", F_PSF, "Break-even exit cap", f"={x(IV,'BE_EXITCAP')}", F_PCT2)
    twocol("Redevelopment (see Development Pro Forma)", f"={x('Bayview JV','RESID')}", F_ACCT, "Total senior debt", f"={x(IV,'LOAN')}", F_ACCT)
    # scenario range row
    s.put(r, L, "HBU verdict", style="warn", align="left", merge=(r, 3))
    s.put(r, 4, "HOLD — residual negative", style="warn", align="left", merge=(r, 6))
    s.put(r, 7, "Lev IRR down/base/up", style="label", align="left", merge=(r, 9))
    s.put(r, 10, f"={x(SC,'IRRL_DOWN')}", style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 11, f"={x(IV,'IRR_L')}", style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 12, f"={x(SC,'IRRL_UP')}", style="calc", color="008000", fmt=F_PCT1, align="center", merge=(r, 13)); r += 2

    # ---------------- thesis + recommendation ----------------
    s.section(r, L, 13, "THESIS  &  RECOMMENDATION"); r += 1
    for t in [
        "ACQUIRE & HOLD a covered land play on the Galleria hard corner. Buy/value each asset off the rent it produces; the blended in-place income",
        "covers the carry while we control the four-parcel corner (+ the office footprint) for eventual Live Local density. Structure Publix as a sale-leaseback (rent covers carry, then it",
        "vacates for redevelopment) and buy out the fractured office condo through Grove Gate (Brad Weiss controls the majority + the board).",
        "Redevelopment does NOT pencil today (AE flood zone, coastal hard costs → negative residual) — the return is optionality on the dirt, paid for by the rent.",
    ]:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1
    r += 1
    s.put(r, L, "Confidence", style="note", align="left", merge=(r, 3))
    s.put(r, 4, "✅ Shahidi & Publix = BCPA-verified · ⚠️ Sunrise, Office, Land = web-sourced (BCPA/Clerk/Sunbiz egress-blocked — verify at county) · 🔶 all rents/caps/premiums modeled on the Assumptions tab",
          style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
