"""
tab_dealbook.py — DEAL BOOK (acquisition & execution package).
The bridge from valuation to a closeable deal — one coherent narrative for sellers,
capital partners, and lenders:
  §1 Deal at a glance      — the ask, the price ladder, the recommendation (live)
  §2 Acquisition strategy  — per-owner: what they paid, our basis, structure, motivation,
                             approach, contingency (the negotiation map; strategy fields editable)
  §3 Whole-deal Sources &  — total capital to control all five at the covered-land price:
     Uses                    purchase + premium + closing + financing + reserves → equity check
  §4 Financing & returns   — what a lender / LP underwrites (live links)
  §5 Risk register         — kill-risks + mitigants (editable)
  §6 Execution timeline    — LOIs → diligence → financing → entitlement → close (editable)
Quant is live-linked to the model; deal intel (blue) is yours to refine in the sheet.
"""
from openpyxl.utils import get_column_letter
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_YR

L = 2
def CL(c): return get_column_letter(c)

# ---- per-owner acquisition strategy (the negotiation map) ----
# (sheet, "Asset — Owner", prior-sale Assumptions name|None, (control sheet, control cell),
#  structure, motivation, approach, contingency)
ACQ_STRATEGY = [
    ("Shahidi Retail", "Shahidi Retail — Shawnick Galleria LLC (Esmail Shahidi, mgr)", "SHA_ACQ",
     ("Shahidi Retail", "PRICE"), "Fee purchase",
     "Bought 11/2021 at $17.1M; owner-operator; value-add lease-up (~17% vacant) is our upside, not their basis.",
     "Approach the owner / listing broker directly with a fee offer near income value.",
     "Clean fee; abstract every lease in DD; confirm the 2021 deed was arm's-length."),
    ("Publix & Starbucks", "Publix + Starbucks — REAL SUB LLC (Publix Super Markets)", "PUB_ACQ",
     ("Publix & Starbucks", "PRICE"), "Sale-leaseback (acquire fee → Publix leases back)",
     "Fee owner, NOT a listed seller. Motive to engage = monetize the real estate while keeping the store open on a leaseback.",
     "Publix real-estate dept (Lakeland) — a corporate SLB conversation, not a broker deal.",
     "DEAL HINGES on leaseback terms (rent/term). Confirm appetite BEFORE spending; no leaseback → re-underwrite dark carry."),
    ("Sunrise Plaza", "Sunrise Plaza — Kar Luen Inc (FL corp, est. 1994)", "SUN_ACQ",
     ("Sunrise Plaza", "PRICE"), "Fee purchase (value-add)",
     "Held since 2000 at a $128k basis — large embedded gain, likely tax-motivated and flexible on structure/timing.",
     "Approach the owner directly; long-time holder, possibly ready to monetize (1031 / installment).",
     "Value is UNVERIFIED — full DD + BCPA/Clerk confirmation before any hard money."),
    ("Office Condo", "Galleria Corp Centre — Grove Gate/Main St Fund (B. Weiss) + ~40 unit owners", "OFF_ACQ",
     ("Office Condo", "BUYOUT_TOTAL"), "Condo buy-out (every unit at unit-market $/SF)",
     "Weiss (Grove Gate) controls 57.4% (bought 2019 at ~$103/SF) AND the board; asking $367–475/SF on units. Grove Gate carries a 2021 Berkadia ~$24M bridge loan across a 3-property FL office portfolio incl. this one — levered, likely open to a portfolio-clearing price.",
     "Weiss first (via building attorney Neale Poller), then pick off holdouts; Merrimac/Motwani & Cosmo/Blaison are known owners.",
     "Condo declaration termination / super-majority vote; confirm the recorded declaration; fragmentation premium is budgeted in the buy-out."),
    ("Land", "1040 Bayview — JV UPSIDE (now WILLOW BRIDGE)", "LND_ACQ",
     ("Land", "CONCLUDED"), "JV / not in the core",
     "SOLD ~Aug 2026: Procacci sold the entitled site to Willow Bridge Property Co. for $24.7M (~$95k/entitled unit; RGA financed $14.5M). The parcel has changed hands — it is NO LONGER a fee purchase; it is a JV target with a new, well-capitalized owner.",
     "Approach Willow Bridge for a JV / assemblage partnership — they hold entitled dirt, you hold the surrounding block; a combined site is worth more than either alone.",
     "Bayview is OUTSIDE the 4-parcel base. Model it as upside only until a JV is agreed; verify the sale at the county."),
]

# ---- risk register: (risk, likelihood/impact, mitigant [editable]) ----
RISKS = [
    ("Office holdouts (fractured condo)", "High / High",
     "Lead with Weiss (57.4% + board); option/contingent PSAs on holdout units; fragmentation premium budgeted; pursue condo-termination vote."),
    ("Publix declines the sale-leaseback", "Med / High",
     "DEAL-CRITICAL — confirm leaseback appetite before spending. Fallback: underwrite dark/vacant carry or an interim tenant on that pad."),
    ("Live Local / entitlement denied or delayed", "Med / Med",
     "Base case is HOLD income-covered land; the redevelopment residual is optionality, never underwritten as base value."),
    ("AE-flood insurance spike (coastal FL)", "Med / Med",
     "Bindable quotes in DD; pass through NNN where structured; fund an insurance reserve; re-run NOI at the real premium."),
    ("Financing cost / availability", "Med / Med",
     "Conservative LTV; DSCR and break-even-exit-cap cushion; senior sized on as-is NOI (lesser-of), not pro-forma."),
    ("Reported values wrong (Sunrise / office / land)", "Med / Med",
     "DD contingencies on every ⚠️ figure; verify at BCPA/Clerk/Sunbiz before hard money; overrides.json tracks each gap."),
    ("Negative going-in carry at the covered-land price", "High / Med",
     "Expected by design — equity funds the carry; entitlement-carry reserve is sized below; the return is the dirt, not current yield."),
    ("Tax reassessment on purchase (FL reassess-to-price)", "High / Low",
     "Modeled to each asset's price and budgeted in opex; an assemblage close will reallocate basis across parcels."),
]

# ---- execution timeline: (phase, window, detail [editable]) ----
TIMELINE = [
    ("0 · Approach & LOIs", "0–2 mo",
     "Sequence: office (Weiss) → Shahidi → Sunrise → Publix RE → Procacci JV. Non-binding LOIs / indications of interest."),
    ("1 · PSAs & due diligence", "2–5 mo",
     "Fee PSAs (Shahidi, Sunrise) + condo buy-out agreements; title, survey, Phase I ESA, estoppels, BCPA verification, insurance quotes."),
    ("2 · Financing", "3–5 mo",
     "Senior term sheet, appraisal, lender DD; secure equity-partner commitments for the equity check below."),
    ("3 · Publix + entitlement", "3–9 mo",
     "Negotiate the Publix leaseback; file the Live Local / density application; refine the redevelopment residual."),
    ("4 · Close", "6–9 mo",
     "Simultaneous close where possible; option/backstop any holdout unit; fund equity per the Sources & Uses."),
    ("5 · Hold / entitle / decide", "yr 1–5",
     "Collect the income-covered carry; advance entitlement; make the redevelopment decision when the residual turns positive."),
]


def build(s, regs):
    IV, A, HB, AS = "Income Valuation", "Assemblage", "Highest & Best Use", "Assumptions"

    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"
    def x(sheet, name): return f"={cell(sheet, name)}"

    ACQ = cell(A, "ACQ"); RAW = cell(A, "RAW_COST")
    CLOSE = cell(IV, "CLOSE"); DOCS = cell(IV, "DOCSTAMP"); TITLE = cell(IV, "TITLE")
    LEGAL = cell(IV, "LEGALDD"); ORIG = cell(IV, "ORIG")
    LN_H = cell(IV, "LN_H")

    s.colw({"A": 2, "B": 30, "C": 13, "D": 14, "E": 13, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "DEAL BOOK  —  ACQUISITION & EXECUTION", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "DAWN RE · E Sunrise Blvd Assemblage · the package to make the deal — for sellers, capital partners & lenders. "
                "Numbers are live from the model; blue deal-intel is yours to refine.", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # ===================== §1 DEAL AT A GLANCE =====================
    s.section(r, L, 13, "§1  DEAL AT A GLANCE"); r += 1
    def glance(label, formula, fmt, note, link=True, style="calc"):
        nonlocal r
        s.put(r, L, label, style=("label_b" if style == "b" else "label"), align="left", merge=(r, 4))
        s.put(r, 5, formula, style=("grand" if style == "grand" else "calc"),
              color=(None if style == "grand" else "008000") if link else None, fmt=fmt, align="right", merge=(r, 6))
        s.put(r, 7, note, style="note", align="left", merge=(r, 13)); r += 1
    glance("What we control", f"={cell(A,'TOT_AC')}", "#,##0.0", "acres of fee land · 4 core parcels + office buy-out (Bayview = JV upside) · Galleria hard corner")
    glance("① Income basis (floor)", f"={cell(IV,'PX_INCOME')}", F_ACCT_TOP, "what the combined rent supports")
    glance("② Sum of the parts", f"={cell(HB,'SUM_PARTS')}", F_ACCT_TOP, "each component bought independently")
    glance("③ COVERED-LAND PRICE (the ask)", f"={ACQ}", F_ACCT_TOP, "control the whole block — sum-of-parts + assemblage premium", style="grand")
    glance("In-place NOI / blended cap", f"={cell(A,'TOT_NOI')}", F_ACCT, "covers carry; blended cap on next line")
    glance("Blended in-place cap", f"={cell(A,'BLEND_CAP2')}", F_PCT2, "covered-land range ~3–5% — income covers carry, not a yield play")
    glance("Senior debt (at covered-land price)", f"={LN_H}", F_ACCT_TOP, "sized lesser-of; income-limited at this price")
    glance("EQUITY TO CLOSE (before reserves)", f"={cell(IV,'EQ_H')}", F_ACCT_TOP, "the sponsor + LP check; full Sources & Uses in §3", style="grand")
    s.put(r, L, "Recommendation", style="warn", align="left", merge=(r, 4))
    s.put(r, 5, "ACQUIRE & HOLD", style="warn", align="center", merge=(r, 6))
    s.put(r, 7, "covered land play — buy the income, control the dirt, hold the Live Local density option", style="warn", align="left", merge=(r, 13)); r += 2

    # ===================== §2 ACQUISITION STRATEGY =====================
    s.section(r, L, 13, "§2  ACQUISITION STRATEGY  —  per owner  (🟢 numbers live · 🔵 strategy editable)"); r += 1
    s.put(r, L, "Asset — Owner", style="subhead", align="left", merge=(r, 3))
    s.put(r, 4, "They paid", style="subhead", align="center")
    s.put(r, 5, "Our basis", style="subhead", align="center")
    s.put(r, 6, "Structure", style="subhead", align="left", merge=(r, 7))
    s.put(r, 8, "Motivation · Approach · Contingency", style="subhead", align="left", merge=(r, 13)); r += 1
    for sheet, label, acqname, (csheet, ccell), structure, motive, approach, contingency in ACQ_STRATEGY:
        s.put(r, L, label, style="calc", align="left", merge=(r, 3))
        if acqname:
            s.put(r, 4, f"={cell(AS, acqname)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        else:
            s.put(r, 4, "—", style="note", align="center")
        s.put(r, 5, f"={cell(csheet, ccell)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 6, structure, style="input", align="left", merge=(r, 7))
        s.put(r, 8, f"{motive}  ▸ {approach}  ▸ ⚠ {contingency}", style="input", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Total to control (independently)", style="total", align="left", merge=(r, 3))
    s.put(r, 4, "—", style="total", align="center")
    s.put(r, 5, f"={RAW}", style="total", fmt=F_ACCT_TOP, align="right")
    s.put(r, 6, "sum of the parts", style="total", align="left", merge=(r, 7))
    s.put(r, 8, "＋ assemblage premium → covered-land price (§3)", style="total", align="left", merge=(r, 13)); r += 2

    # ===================== §3 WHOLE-DEAL SOURCES & USES =====================
    s.section(r, L, 13, "§3  WHOLE-DEAL SOURCES & USES  —  capital to control all five at the covered-land price"); r += 1
    # two editable reserves + optional mezz
    s.put(r, L, "Operating / capex reserve", style="label", align="left", merge=(r, 4))
    s.put(r, 5, 2000000, style="input", fmt=F_ACCT_TOP, align="right", name="RESERVE", merge=(r, 6))
    s.put(r, 7, "🔵 sized cushion for lease-up & capex", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Entitlement-period carry reserve", style="label", align="left", merge=(r, 4))
    s.put(r, 5, 3000000, style="input", fmt=F_ACCT_TOP, align="right", name="ENTCARRY", merge=(r, 6))
    s.put(r, 7, "🔵 funds negative carry while entitling (covered-land)", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Mezzanine / preferred", style="label", align="left", merge=(r, 4))
    s.put(r, 5, 0, style="input", fmt=F_ACCT_TOP, align="right", name="MEZZ", merge=(r, 6))
    s.put(r, 7, "🔵 optional second debt layer (0 = none)", style="note", align="left", merge=(r, 13)); r += 1
    RESERVE = s.reg["RESERVE"]; ENTCARRY = s.reg["ENTCARRY"]; MEZZ = s.reg["MEZZ"]
    r += 1

    # USES / SOURCES side by side
    s.put(r, L, "USES", style="subhead", align="left", merge=(r, 6))
    s.put(r, 8, "SOURCES", style="subhead", align="left", merge=(r, 13)); r += 1
    u0 = r
    def use(label, formula, fmt=F_ACCT, bold=False):
        nonlocal r
        s.put(r, L, label, style=("subtotal" if bold else "label"), align="left", merge=(r, 5))
        s.put(r, 6, formula, style="calc", fmt=fmt, align="right", bold=bold)
    def src(row, label, formula, fmt=F_ACCT, bold=False, name=None):
        s.put(row, 8, label, style=("subtotal" if bold else "label"), align="left", merge=(row, 11))
        s.put(row, 12, formula, style="calc", fmt=fmt, align="right", bold=bold, name=name, merge=(row, 13))
    use("Purchase — sum of the parts", f"={RAW}"); src(r, "Senior debt (sized)", f"={LN_H}", F_ACCT_TOP, name="DB_SEN"); r += 1
    use("＋ Assemblage premium", f"={ACQ}-{RAW}"); src(r, "Mezzanine / preferred", f"={MEZZ}", name="DB_MEZ"); r += 1
    use("＝ Covered-land purchase", f"={ACQ}", F_ACCT_TOP, bold=True); r += 1
    use("Doc-stamp / transfer tax", f"={ACQ}*{DOCS}"); r += 1
    use("Title insurance", f"={ACQ}*{TITLE}"); r += 1
    use("Legal & due diligence", f"={ACQ}*{LEGAL}"); r += 1
    use("Loan origination", f"={ORIG}*{LN_H}"); r += 1
    use("Operating / capex reserve", f"={RESERVE}"); r += 1
    use("Entitlement-period carry reserve", f"={ENTCARRY}"); r += 1
    uN = r - 1
    # total uses
    s.put(r, L, "TOTAL USES", style="grand", align="left", merge=(r, 5))
    s.put(r, 6, f"={ACQ}*(1+{DOCS}+{TITLE}+{LEGAL})+{ORIG}*{LN_H}+{RESERVE}+{ENTCARRY}", style="grand", fmt=F_ACCT_TOP, align="right", name="DB_USES")
    USES = s.reg["DB_USES"]
    # equity plug as a source
    src(r, "Sponsor + LP equity (plug)", f"={USES}-{s.reg['DB_SEN']}-{s.reg['DB_MEZ']}", F_ACCT_TOP, bold=True, name="DB_EQ")
    r += 1
    s.put(r, L, "Check (sources − uses)", style="note", align="left", merge=(r, 5))
    s.put(r, 6, f"=({s.reg['DB_SEN']}+{s.reg['DB_MEZ']}+{s.reg['DB_EQ']})-{USES}", style="calc", fmt=F_ACCT, align="right")
    s.put(r, 8, "TOTAL SOURCES", style="grand", align="left", merge=(r, 11))
    s.put(r, 12, f"={s.reg['DB_SEN']}+{s.reg['DB_MEZ']}+{s.reg['DB_EQ']}", style="grand", fmt=F_ACCT_TOP, align="right", merge=(r, 13)); r += 1
    s.put(r, L, "Loan-to-cost  ·  equity as % of cost", style="note", align="left", merge=(r, 5))
    s.put(r, 6, f"=({s.reg['DB_SEN']}+{s.reg['DB_MEZ']})/{USES}", style="calc", fmt=F_PCT1, align="right")
    s.put(r, 8, f"={s.reg['DB_EQ']}/{USES}", style="calc", fmt=F_PCT1, align="left", merge=(r, 13)); r += 2

    # ===================== §4 FINANCING & RETURNS =====================
    s.section(r, L, 13, "§4  FINANCING & RETURNS  —  what a lender / LP underwrites  (live)"); r += 1
    def kv2(l1, f1, fmt1, l2, f2, fmt2):
        nonlocal r
        s.put(r, L, l1, style="label", align="left", merge=(r, 4))
        s.put(r, 5, f1, style="calc", color="008000", fmt=fmt1, align="right", merge=(r, 6))
        s.put(r, 7, l2, style="label", align="left", merge=(r, 9))
        s.put(r, 10, f2, style="calc", color="008000", fmt=fmt2, align="right", merge=(r, 13)); r += 1
    kv2("Senior rate", f"={cell(IV,'RATE')}", F_PCT2, "Year-1 DSCR (at covered-land)", f"={cell(IV,'DSCR_H')}", F_MULT)
    kv2("Max senior LTV", f"={cell(IV,'LTV')}", F_PCT1, "Break-even exit cap", f"={cell(IV,'BE_EXITCAP')}", F_PCT2)
    kv2("Levered IRR — income price", f"={cell(IV,'IRRL_I')}", F_PCT1, "Levered IRR — covered-land price", f"={cell(IV,'IRRL_H')}", F_PCT1)
    kv2("Unlevered IRR — income price", f"={cell(IV,'IRRU_I')}", F_PCT1, "Levered equity multiple — income", f"={cell(IV,'EML_I')}", F_MULT)
    kv2("Land CAGR to justify the premium", f"={cell(IV,'BE_APPREC')}", F_PCT1, "Post-approval entitled land", f"={cell(HB,'LAND_ENTITLED')}", F_ACCT_TOP)
    s.put(r, L, "The thesis", style="warn", align="left", merge=(r, 4))
    s.put(r, 5, "Income covers the carry; the return is the dirt + the Live Local option. At the covered-land price the going-in income return is "
                "negative by design — equity buys optionality, underwritten to a HOLD, and pays off if land compounds at ≥ the CAGR at left.",
          style="warn", align="left", merge=(r, 13)); r += 2

    # ===================== §5 RISK REGISTER =====================
    s.section(r, L, 13, "§5  RISK REGISTER & MITIGANTS  (🔵 mitigants editable)"); r += 1
    s.put(r, L, "Risk", style="subhead", align="left", merge=(r, 4))
    s.put(r, 5, "L / I", style="subhead", align="center")
    s.put(r, 6, "Mitigant", style="subhead", align="left", merge=(r, 13)); r += 1
    for risk, li, mit in RISKS:
        s.put(r, L, risk, style="calc", align="left", merge=(r, 4))
        s.put(r, 5, li, style="warn", align="center")
        s.put(r, 6, mit, style="input", align="left", merge=(r, 13)); r += 1
    r += 1

    # ===================== §6 EXECUTION TIMELINE =====================
    s.section(r, L, 13, "§6  EXECUTION TIMELINE  (🔵 detail editable)"); r += 1
    s.put(r, L, "Phase", style="subhead", align="left", merge=(r, 4))
    s.put(r, 5, "Window", style="subhead", align="center")
    s.put(r, 6, "Detail", style="subhead", align="left", merge=(r, 13)); r += 1
    for phase, window, detail in TIMELINE:
        s.put(r, L, phase, style="label_b", align="left", merge=(r, 4))
        s.put(r, 5, window, style="calc", align="center")
        s.put(r, 6, detail, style="input", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
