"""
tab_devt.py — DEVELOPMENT PRO FORMA (quantifying the redevelopment vision).
What can be built on the assembled block, what it costs, and what it's worth — at
merchant-developer standard. Program (density · height · product · unit mix) →
total development cost (land · demo · hard · parking · soft · fees · contingency ·
construction financing · developer fee) → value on completion, tested BOTH ways
(Class-A rental and for-sale condo) → developer profit, yield-on-cost spread, and
the RESIDUAL LAND VALUE the vision supports (the max you can pay for the dirt).
Blue cells are inputs; grounded in mid-2026 Fort Lauderdale research (see Notes).
"""
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
from mblib import (F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_PSF, F_NUM, F_NUM2, F_YR)

L = 2
def CL(c): return get_column_letter(c)
HEAT = ColorScaleRule(start_type="min", start_color="F8696B",
                      mid_type="percentile", mid_value=50, mid_color="FFEB84",
                      end_type="max", end_color="63BE7B")


def build(s, regs):
    A, HB = "Assemblage", "Highest & Best Use"
    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"

    s.colw({"A": 2, "B": 34, "C": 15, "D": 13, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "DEVELOPMENT PRO FORMA  —  quantifying the vision", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "What can be built on the assembled Galleria corner, what it costs, and what it's worth — program → cost → value → "
                "residual land value. Tested as Class-A rental AND for-sale condo. 🔵 blue = inputs (mid-2026 FTL research).",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    g = s.reg
    def R(n): return g[n]
    def inp(name, label, val, fmt, note=""):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="right", name=name)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1
    def der(name, label, formula, fmt, note="", style="calc", bold=False):
        nonlocal r
        s.put(r, L, label, style=("subtotal" if style == "sub" else ("grand" if style == "grand" else "label")), align="left")
        s.put(r, 3, formula, style=("grand" if style == "grand" else "calc"), fmt=fmt, align="right", name=name, bold=bold)
        if note: s.put(r, 4, note, style="note", align="left", merge=(r, 13))
        r += 1

    # ================= 1. SITE & PROGRAM =================
    s.section(r, L, 13, "①  THE SITE & THE PROGRAM  —  what gets built"); r += 1
    inp("DEV_CORE_AC", "Core site — retail parcels + office footprint (ac)", 6.77, F_NUM2, "3 retail parcels 4.77 ac + office ~2.0 ac (buy out EVERY condo unit & terminate the condominium)")
    inp("INCL_BAY", "Include Bayview JV?  (1 = yes, 0 = no)", 0, F_NUM, "🔵 Bayview SOLD to Willow Bridge (~Aug 2026) — only adds to the site via a JV")
    inp("BAY_AC", "Bayview parcel (acres)", 2.39, F_NUM2, "🔵 Willow Bridge JV upside")
    der("DEV_AC", "DEVELOPABLE LAND (acres)", f"={R('DEV_CORE_AC')}+{R('INCL_BAY')}*{R('BAY_AC')}", F_NUM2, "core (4 parcels + office) + Bayview JV toggle", style="sub", bold=True)
    inp("DENS", "Density (units / acre)", 108, F_NUM, "🔵 codified base 60/ac; Bayview did 108/ac (city bonus); Galleria next door ≈140/ac (Live Local) → ~730–950 units")
    der("UNITS", "TOTAL UNITS", f"={R('DEV_AC')}*{R('DENS')}", F_NUM, "acres × density", style="sub", bold=True)
    inp("STORIES", "Height (stories)", 30, F_NUM, "🔵 Live Local height = tallest within 1 mi ≈ Selene 300 ft / Galleria 342 ft ≈ 30 stories")
    inp("NRSF_UNIT", "Avg net saleable/rentable SF per unit", 950, F_NUM, "🔵 mix of 1BR/2BR")
    der("NRSF", "Net saleable/rentable SF", f"={R('UNITS')}*{R('NRSF_UNIT')}", F_NUM, "the sellable/leasable area")
    inp("EFFIC", "Building efficiency (net ÷ gross)", 0.82, F_PCT1, "🔵 corridors, lobby, amenity, MEP")
    der("GBA_RES", "Residential gross buildable (GBA)", f"={R('NRSF')}/{R('EFFIC')}", F_NUM, "what you actually build & pay to build")
    inp("PARK_RATIO", "Parking ratio (spaces / unit)", 1.50, F_NUM2, "🔵 Bayview built 2.19/unit; Live Local cuts required parking ≥20% near transit")
    der("SPACES", "Parking spaces", f"={R('UNITS')}*{R('PARK_RATIO')}", F_NUM)
    inp("PARK_SF", "SF per structured space", 350, F_NUM, "🔵 incl. ramps/circulation")
    der("PARK_GBA", "Parking garage GBA", f"={R('SPACES')}*{R('PARK_SF')}", F_NUM)
    inp("COMM_SF", "Ground-floor retail / commercial SF", 8081, F_NUM, "🔵 activates the corner (Bayview plan)")
    der("GBA", "TOTAL GROSS BUILDABLE (all uses)", f"={R('GBA_RES')}+{R('PARK_GBA')}+{R('COMM_SF')}", F_NUM, "residential + parking + retail", style="sub", bold=True)
    der("FAR", "Implied FAR (GBA ÷ land)", f"={R('GBA')}/({R('DEV_AC')}*43560)", F_NUM2, "check vs allowable — Live Local ≥150% of base")
    s.put(r, L, "Product type", style="label_b", align="left")
    s.put(r, 3, "Mid/high-rise multifamily", style="calc", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "", style="label"); s.put(r, 3, "over a parking podium + ground-floor retail — coastal AE-zone concrete construction", style="note", align="left", merge=(r, 13)); r += 2

    # ================= 2. DEVELOPMENT COST (TDC) =================
    s.section(r, L, 13, "②  TOTAL DEVELOPMENT COST  (TDC)  —  the full cost stack"); r += 1
    inp("LAND", "Land basis (assemblage acquisition)", 92800000, F_ACCT_TOP, "🔵 4-parcel sum-of-parts ≈ $92.8M (covered-land ≈ $111M); + ~$24.7M if Bayview JV — the RESIDUAL below tells you the MAX to pay")
    s.put(r, L, "  (model: 4-parcel sum-of-parts / covered-land)", style="note", align="left")
    s.put(r, 4, f"={cell(A,'RAW_COST')}", style="calc", color="008000", fmt=F_ACCT, align="right")
    s.put(r, 6, f"={cell(A,'ACQ')}", style="calc", color="008000", fmt=F_ACCT, align="right"); r += 1
    inp("EXIST_SF", "Existing building SF (to demolish)", 341501, F_NUM, "🔵 sum of the five buildings")
    inp("DEMO_PSF", "Demolition ($/SF)", 15, F_PSF, "🔵")
    der("DEMO", "Demolition", f"={R('EXIST_SF')}*{R('DEMO_PSF')}", F_ACCT)
    inp("HARDPSF", "Residential hard cost ($/GBA SF)", 400, F_PSF, "🔵 AE-coastal concrete $300–450/SF (research); + HVHZ premium")
    der("HARD_RES", "Residential hard cost", f"={R('GBA_RES')}*{R('HARDPSF')}", F_ACCT)
    inp("PARK_PSF", "Parking hard cost ($/GBA SF)", 90, F_PSF, "🔵 structured podium")
    der("HARD_PARK", "Parking hard cost", f"={R('PARK_GBA')}*{R('PARK_PSF')}", F_ACCT)
    inp("RET_PSF", "Retail shell hard cost ($/SF)", 200, F_PSF, "🔵")
    der("HARD_RET", "Retail hard cost", f"={R('COMM_SF')}*{R('RET_PSF')}", F_ACCT)
    der("HARD", "TOTAL HARD COST", f"={R('HARD_RES')}+{R('HARD_PARK')}+{R('HARD_RET')}", F_ACCT_TOP, "residential + parking + retail", style="sub", bold=True)
    inp("SOFT_PCT", "Soft costs (% of hard)", 0.22, F_PCT1, "🔵 A&E, legal, permits, insurance, marketing")
    der("SOFT", "Soft costs", f"={R('HARD')}*{R('SOFT_PCT')}", F_ACCT)
    inp("IMPACT_UNIT", "Impact / mobility fees ($/unit)", 6000, F_ACCT, "🔵 Broward road/rec fees SUSPENDED ($0) since 10/24; school ~$461/unit + city park + water/sewer")
    der("FEES", "Impact / permit fees", f"={R('UNITS')}*{R('IMPACT_UNIT')}", F_ACCT)
    inp("CONT_PCT", "Contingency (% of hard)", 0.06, F_PCT1, "🔵")
    der("CONT", "Contingency", f"={R('HARD')}*{R('CONT_PCT')}", F_ACCT)
    inp("CLTC", "Construction loan (% of cost ex-land)", 0.60, F_PCT1, "🔵 LTC on vertical cost")
    inp("CRATE", "Construction loan rate", 0.085, F_PCT2, "🔵 SOFR + spread")
    inp("CMONTHS", "Construction + lease-up (months)", 30, F_NUM, "🔵")
    der("FIN", "Construction financing (carry)",
        f"=({R('HARD')}+{R('SOFT')}+{R('FEES')}+{R('CONT')}+{R('DEMO')})*{R('CLTC')}*{R('CRATE')}*({R('CMONTHS')}/12)*0.55", F_ACCT,
        "loan × rate × term × ~55% avg outstanding")
    inp("DEVFEE_PCT", "Developer fee (% of hard+soft)", 0.03, F_PCT1, "🔵")
    der("DEVFEE", "Developer fee", f"=({R('HARD')}+{R('SOFT')})*{R('DEVFEE_PCT')}", F_ACCT)
    der("TDC", "TOTAL DEVELOPMENT COST", f"={R('LAND')}+{R('DEMO')}+{R('HARD')}+{R('SOFT')}+{R('FEES')}+{R('CONT')}+{R('FIN')}+{R('DEVFEE')}", F_ACCT_TOP, style="grand", bold=True)
    der("TDC_UNIT", "  TDC per unit", f"={R('TDC')}/{R('UNITS')}", F_ACCT)
    der("TDC_SF", "  TDC per net SF", f"={R('TDC')}/{R('NRSF')}", F_PSF)
    r += 1

    # ================= 3a. VALUE — RENTAL =================
    s.section(r, L, 13, "③a  VALUE ON COMPLETION  —  as CLASS-A RENTAL"); r += 1
    inp("RENT_MO", "Achievable rent ($/SF / month)", 3.40, F_NUM2, "🔵 Downtown FTL Class-A ~$3.44/SF (RentCafe/Yardi 6/26); soft — ~2mo concessions")
    der("GPR", "Gross potential rent (annual)", f"={R('NRSF')}*{R('RENT_MO')}*12", F_ACCT_TOP)
    inp("OTHER_PCT", "Other income (% of GPR)", 0.05, F_PCT1, "🔵 parking, fees, RUBS")
    inp("VAC", "Vacancy + concessions", 0.08, F_PCT1, "🔵 Class-A lease-up ~9% vacancy + concession burn (Matthews)")
    der("EGI", "Effective gross income", f"={R('GPR')}*(1+{R('OTHER_PCT')})*(1-{R('VAC')})", F_ACCT)
    inp("OPEX_PCT", "Operating expenses (% of EGI)", 0.40, F_PCT1, "🔵 FL insurance 15–20% of rents pushes OER to ~40%")
    der("NOI_R", "Stabilized NOI", f"={R('EGI')}*(1-{R('OPEX_PCT')})", F_ACCT_TOP, style="sub", bold=True)
    inp("STAB_CAP", "Stabilized cap rate (exit)", 0.0525, F_PCT2, "🔵 Class-A South FL multifamily")
    der("VAL_R", "Stabilized value", f"={R('NOI_R')}/{R('STAB_CAP')}", F_ACCT_TOP, style="sub", bold=True)
    der("YOC", "Yield on cost (NOI ÷ TDC)", f"={R('NOI_R')}/{R('TDC')}", F_PCT2)
    der("SPREAD", "Development spread (YoC − exit cap)", f"={R('YOC')}-{R('STAB_CAP')}", F_PCT2, "positive ≈ +100–200 bps to pencil")
    der("PROFIT_R", "Development profit (value − TDC)", f"={R('VAL_R')}-{R('TDC')}", F_ACCT_TOP, style="grand", bold=True)
    der("MARGIN_R", "  Margin on cost", f"={R('PROFIT_R')}/{R('TDC')}", F_PCT1)
    r += 1

    # ================= 3b. VALUE — FOR-SALE CONDO =================
    s.section(r, L, 13, "③b  VALUE ON COMPLETION  —  as FOR-SALE CONDO"); r += 1
    inp("SELL_PSF", "Sellout price ($/net SF)", 900, F_PSF, "🔵 FTL new condo $700–1,200+/SF; oceanfront $1,100+; this site non-oceanfront (CondoBlackBook)")
    der("GSELL", "Gross sellout", f"={R('NRSF')}*{R('SELL_PSF')}", F_ACCT_TOP)
    inp("SALES_PCT", "Sales & marketing (% of sellout)", 0.07, F_PCT1, "🔵 commissions, marketing, closing")
    der("NSELL", "Net sellout", f"={R('GSELL')}*(1-{R('SALES_PCT')})", F_ACCT_TOP, style="sub", bold=True)
    der("PROFIT_S", "Development profit (net sellout − TDC)", f"={R('NSELL')}-{R('TDC')}", F_ACCT_TOP, style="grand", bold=True)
    der("MARGIN_S", "  Margin on cost", f"={R('PROFIT_S')}/{R('TDC')}", F_PCT1)
    der("SELL_UNIT", "  Avg price per unit", f"={R('GSELL')}/{R('UNITS')}", F_ACCT)
    r += 1

    # ================= 4. RESIDUAL LAND VALUE & VERDICT =================
    s.section(r, L, 13, "④  RESIDUAL LAND VALUE  —  the max the vision supports for the dirt"); r += 1
    inp("REQ_MARGIN", "Required developer margin (on cost)", 0.15, F_PCT1, "🔵 the profit the deal must clear")
    der("RLV_R", "Residual land value — as RENTAL", f"={R('VAL_R')}/(1+{R('REQ_MARGIN')})-({R('TDC')}-{R('LAND')})", F_ACCT_TOP,
        "value ÷ (1+margin) − all costs except land")
    der("RLV_S", "Residual land value — as CONDO", f"={R('NSELL')}/(1+{R('REQ_MARGIN')})-({R('TDC')}-{R('LAND')})", F_ACCT_TOP, style="sub", bold=True)
    der("RLV_BEST", "Supported land value (best use)", f"=MAX({R('RLV_R')},{R('RLV_S')})", F_ACCT_TOP, "the higher of the two products", style="grand", bold=True)
    der("RLV_GAP", "vs. your land basis", f"={R('RLV_BEST')}-{R('LAND')}", F_ACCT_TOP, "positive = the vision covers your acquisition; negative = pay less")
    der("RLV_UNIT", "  Supported land value / unit", f"={R('RLV_BEST')}/{R('UNITS')}", F_ACCT)
    s.put(r, L, "  Market check — entitled-land comp", style="note", align="left")
    s.put(r, 3, 95000, style="calc", fmt=F_ACCT, align="right")
    s.put(r, 4, "$/unit — the Bayview parcel (259 units) sold entitled to Willow Bridge for $24.7M, ~Aug 2026 (The Real Deal)", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "VERDICT", style="warn", align="left")
    s.put(r, 4, "The dirt is worth the higher of the two products above. If that exceeds your land basis, redevelopment pencils and sets your "
                "MAX acquisition price; if not, HOLD as income-covered land until rents/sellout rise or costs fall. Rental vs. condo is the "
                "product decision — condo pricing carries the coastal land basis that rental cannot.",
          style="warn", align="left", merge=(r, 13)); r += 2

    # ================= 5. SENSITIVITY =================
    s.section(r, L, 13, "⑤  SENSITIVITY  —  supported land value ($M)  ·  sellout $/SF (rows) × hard cost $/SF (cols)  🔵 editable axes"); r += 1
    s.put(r, L, "Sellout ╲ hard", style="subhead", align="center")
    hards = [350, 400, 450, 500, 550]
    for j, h in enumerate(hards):
        s.put(r, 4 + j, h, style="input", fmt=F_PSF, align="center")
    hrow = r; r += 1
    sells = [750, 850, 1000, 1200, 1400]
    top = r
    # supported land (condo) = NSELL/(1+margin) - (nonland TDC with flexed hard) ; nonland TDC = TDC - LAND - HARD_RES + GBA_RES*hard
    for sp in sells:
        s.put(r, L, sp, style="input", fmt=F_PSF, align="center")
        for j in range(len(hards)):
            h = f"{CL(4+j)}{hrow}"
            nsell = f"({R('NRSF')}*{CL(L)}{r}*(1-{R('SALES_PCT')}))"
            hard_res2 = f"({R('GBA_RES')}*{h})"
            # non-land, non-fin TDC rebuilt with flexed residential hard (parking+retail+demo+soft+fees+cont+devfee+fin approximated at base share)
            nonland = f"({R('TDC')}-{R('LAND')}-{R('HARD_RES')}+{hard_res2})"
            s.put(r, 4 + j, f"=({nsell}/(1+{R('REQ_MARGIN')})-{nonland})/1000000", style="calc", fmt="#,##0.0", align="center")
        r += 1
    s.ws.conditional_formatting.add(f"D{top}:H{r-1}", HEAT)
    s.put(r, L, "Green = the vision supports a land value ≥ your basis. Read across to find the sellout you need at a given cost.",
          style="note", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
