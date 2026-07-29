"""
tab_partners.py — PARTNER RETURNS (LP / GP equity waterfall + downside).
Splits the consolidated levered equity cash flow between the LP and the sponsor
(GP) through a standard promote structure — return of capital + preferred, then a
promote on the excess — and reports LP and GP IRR / multiple, the GP's promote $,
and the downside (scenario IRR band + how far proceeds can fall before the LP's
capital + preferred is impaired). This is the equity story for a capital partner.
Every distribution is the model's actual levered cash flow (linked from the Income
Valuation tab); the promote terms are 🔵 blue inputs.
"""
from openpyxl.utils import get_column_letter
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_MULT, F_NUM, F_YR

L = 2
ACQ = 3
def pc(y): return 3 + y
def CL(c): return get_column_letter(c)


def _row(coord):
    return int("".join(c for c in coord if c.isdigit()))


def build(s, regs):
    IV, SC = "Income Valuation", "Scenarios"

    def cell(sheet, name): return f"'{sheet}'!{regs[sheet][name]}"
    def x(sheet, name): return f"={cell(sheet, name)}"

    EQ = cell(IV, "EQ_I")                        # total sponsor+LP equity at the income price
    HOLD = cell(IV, "HOLD")
    lev = _row(regs[IV]["ROW_LEVCF_I"])          # Income tab row holding the levered equity CF
    def LCF(col): return f"'{IV}'!{CL(col)}{lev}"  # C=yr0, D..M = yrs 1..10

    s.colw({"A": 2, "B": 32, "C": 13, "D": 12, "E": 12, "F": 12, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "PARTNER RETURNS  —  LP / GP WATERFALL", style="banner", align="left", merge=(r, 13)); s.rowh(r, 24); r += 1
    s.put(r, L, "DAWN RE · E Sunrise Blvd Assemblage · how the equity splits between the LP and the sponsor — the story for a capital partner. "
                "Distributions are the model's actual levered cash flow; 🔵 promote terms are yours.", style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 18); r += 2

    # ---------------- promote terms ----------------
    s.section(r, L, 13, "PROMOTE STRUCTURE  —  🔵 blue inputs"); r += 1
    def inp(name, label, val, fmt, note):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 3, val, style="input", fmt=fmt, align="center", name=name)
        s.put(r, 4, note, style="note", align="left", merge=(r, 13)); r += 1
    inp("LP_SH", "LP share of equity", 0.90, F_PCT1, "limited partner / investors")
    inp("GP_SH", "GP / sponsor share of equity", 0.10, F_PCT1, "sponsor co-invest")
    inp("PREF", "Preferred return (to all equity)", 0.08, F_PCT1, "8% pref, compounded, before promote")
    inp("PROMO_LP", "LP split above the pref", 0.70, F_PCT1, "LP keeps 70% of the excess")
    inp("PROMO_GP", "GP promote above the pref", 0.30, F_PCT1, "sponsor carry on the excess")
    g = s.reg
    LP_SH, GP_SH, PREF, PLP, PGP = g["LP_SH"], g["GP_SH"], g["PREF"], g["PROMO_LP"], g["PROMO_GP"]
    s.put(r, L, "Total equity (at income price)", style="label_b", align="left")
    s.put(r, 3, f"={EQ}", style="calc", color="008000", fmt=F_ACCT_TOP, align="center", name="WF_EQ")
    s.put(r, 4, "🟢 from the Income Valuation Sources & Uses", style="note", align="left", merge=(r, 13)); r += 1
    WF_EQ = g["WF_EQ"]
    r += 1

    # ---------------- annual waterfall ----------------
    s.section(r, L, 13, "EQUITY WATERFALL  —  annual  (European / whole-deal: capital + pref, then promote)"); r += 1
    s.put(r, L, "Year", style="subhead", align="left")
    s.put(r, ACQ, "0", style="subhead", align="center")
    for y in range(1, 11): s.put(r, pc(y), y, style="subhead", align="center", fmt=F_YR)
    r += 1

    rows = {}
    def wrow(name, label, style="label"):
        nonlocal r
        rows[name] = r
        s.put(r, L, label, style=style, align="left")
        return r
    # total equity cash flow (from the model) — yr0 negative (contribution), yrs = distributions
    rcf = wrow("CF", "Total equity cash flow (levered)")
    s.put(rcf, ACQ, f"={LCF(ACQ)}", style="calc", color="008000", fmt=F_ACCT_TOP, align="right")
    for y in range(1, 11):
        s.put(rcf, pc(y), f"={LCF(pc(y))}", style="calc", color="008000", fmt=F_ACCT, align="right")
    r += 1
    # distribution (positive cash only)
    rd = wrow("DIST", "Distribution to equity")
    for y in range(1, 11):
        s.put(rd, pc(y), f"=MAX(0,{CL(pc(y))}{rows['CF']})", style="calc", fmt=F_ACCT, align="right")
    r += 1
    # unreturned capital + accrued pref (balance) — recursive across years
    rbal = wrow("BAL", "Unreturned capital + pref (end)")
    s.put(rbal, ACQ, f"={WF_EQ}", style="calc", fmt=F_ACCT, align="right")   # capital owed at close
    for y in range(1, 11):
        prev = f"{CL(pc(y)-1)}{rbal}"
        s.put(rbal, pc(y), f"=MAX(0,{prev}*(1+{PREF})-{CL(pc(y))}{rows['DIST']})", style="calc", fmt=F_ACCT, align="right")
    r += 1
    # tier 1: return of capital + pref
    rt1 = wrow("T1", "① Return of capital + pref")
    for y in range(1, 11):
        prev = f"{CL(pc(y)-1)}{rbal}"
        s.put(rt1, pc(y), f"=MIN({CL(pc(y))}{rows['DIST']},{prev}*(1+{PREF}))", style="calc", fmt=F_ACCT, align="right")
    r += 1
    # tier 2: excess (promote base)
    rt2 = wrow("T2", "② Excess above pref (promote base)")
    for y in range(1, 11):
        s.put(rt2, pc(y), f"={CL(pc(y))}{rows['DIST']}-{CL(pc(y))}{rows['T1']}", style="calc", fmt=F_ACCT, align="right")
    r += 1
    # LP / GP cash flows
    rlp = wrow("LPCF", "LP cash flow", style="label_b")
    s.put(rlp, ACQ, f"=-{LP_SH}*{WF_EQ}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rlp, pc(y), f"={LP_SH}*{CL(pc(y))}{rows['T1']}+{PLP}*{CL(pc(y))}{rows['T2']}", style="calc", fmt=F_ACCT, align="right", bold=True)
    r += 1
    rgp = wrow("GPCF", "GP cash flow (incl. promote)", style="label_b")
    s.put(rgp, ACQ, f"=-{GP_SH}*{WF_EQ}", style="calc", fmt=F_ACCT_TOP, align="right", bold=True)
    for y in range(1, 11):
        s.put(rgp, pc(y), f"={GP_SH}*{CL(pc(y))}{rows['T1']}+{PGP}*{CL(pc(y))}{rows['T2']}", style="calc", fmt=F_ACCT, align="right", bold=True)
    r += 2

    # ---------------- returns summary ----------------
    s.section(r, L, 13, "RETURNS  —  LP vs. GP vs. project"); r += 1
    lprange = f"{CL(ACQ)}{rows['LPCF']}:{CL(pc(10))}{rows['LPCF']}"
    gprange = f"{CL(ACQ)}{rows['GPCF']}:{CL(pc(10))}{rows['GPCF']}"
    lp1 = f"{CL(pc(1))}{rows['LPCF']}:{CL(pc(10))}{rows['LPCF']}"
    gp1 = f"{CL(pc(1))}{rows['GPCF']}:{CL(pc(10))}{rows['GPCF']}"
    def three(label, flp, fgp, fpr, fmt):
        nonlocal r
        s.put(r, L, label, style="label", align="left")
        s.put(r, 5, flp, style="calc", fmt=fmt, align="right")
        s.put(r, 7, fgp, style="calc", fmt=fmt, align="right")
        s.put(r, 9, fpr, style="calc", color="008000", fmt=fmt, align="right", merge=(r, 10)); r += 1
    s.put(r, L, "Metric", style="subhead", align="left")
    s.put(r, 5, "LP", style="subhead", align="center")
    s.put(r, 7, "GP / sponsor", style="subhead", align="center")
    s.put(r, 9, "Project", style="subhead", align="center", merge=(r, 10)); r += 1
    three("IRR", f'=IFERROR(IRR({lprange}),"n/m")', f'=IFERROR(IRR({gprange}),"n/m")', f"={cell(IV,'IRRL_I')}", F_PCT1)
    three("Equity multiple", f"=SUM({lp1})/({LP_SH}*{WF_EQ})", f"=SUM({gp1})/({GP_SH}*{WF_EQ})", f"={cell(IV,'EML_I')}", F_MULT)
    three("Equity invested", f"={LP_SH}*{WF_EQ}", f"={GP_SH}*{WF_EQ}", f"={WF_EQ}", F_ACCT)
    three("Total distributions", f"=SUM({lp1})", f"=SUM({gp1})", f"=SUM({CL(pc(1))}{rows['DIST']}:{CL(pc(10))}{rows['DIST']})", F_ACCT)
    s.put(r, L, "GP promote earned (carry above pro-rata)", style="label_b", align="left")
    s.put(r, 5, f"={PGP}*SUM({CL(pc(1))}{rows['T2']}:{CL(pc(10))}{rows['T2']})", style="calc", fmt=F_ACCT_TOP, align="right", name="PROMOTE")
    s.put(r, 7, "the sponsor's incentive fee for outperformance above the pref", style="note", align="left", merge=(r, 13)); r += 2

    # ---------------- downside / capital at risk ----------------
    s.section(r, L, 13, "DOWNSIDE  &  LP CAPITAL PROTECTION"); r += 1
    # scenario IRR band (project, levered)
    s.put(r, L, "Project levered IRR — down / base / up", style="label", align="left")
    s.put(r, 6, x(SC, "IRRL_DOWN"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 7, x(IV, "IRRL_I"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 8, x(SC, "IRRL_UP"), style="calc", color="008000", fmt=F_PCT1, align="center")
    s.put(r, 9, "full consolidated cash flows on the Scenarios tab", style="note", align="left", merge=(r, 13)); r += 1
    # LP protection: how far can total proceeds fall before capital + pref impaired
    s.put(r, L, "Total equity proceeds (base)", style="label", align="left")
    s.put(r, 5, f"=SUM({CL(pc(1))}{rows['DIST']}:{CL(pc(10))}{rows['DIST']})", style="calc", fmt=F_ACCT_TOP, align="right", name="PROCEEDS", merge=(r, 6)); r += 1
    s.put(r, L, "Capital + pref hurdle (all equity, at exit)", style="label", align="left")
    s.put(r, 5, f"={WF_EQ}*(1+{PREF})^{HOLD}", style="calc", fmt=F_ACCT_TOP, align="right", name="HURDLE", merge=(r, 6)); r += 1
    s.put(r, L, "Cushion — proceeds can fall this far before the pref is unmet", style="label_b", align="left")
    s.put(r, 5, f"=1-{g['HURDLE']}/{g['PROCEEDS']}", style="calc", fmt=F_PCT1, align="right", merge=(r, 6))
    s.put(r, 7, "LP sits ahead of the GP promote: the sponsor earns carry only after the LP's capital + 8% pref is returned", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "Read", style="warn", align="left")
    s.put(r, 4, "At the income price the LP earns its pref with room to spare; the GP's upside is the promote. The covered-land price is a "
                "separate, land-appreciation bet (negative going-in income return) — raise LP equity against the income case, not the covered-land case.",
          style="warn", align="left", merge=(r, 13)); r += 1

    s.freeze("C6")
    return s
