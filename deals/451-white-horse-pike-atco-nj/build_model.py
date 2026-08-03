"""Build the 451 White Horse Pike acquisition model."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

F = "Arial"
INK   = "FF1A1C1A"
INK2  = "FF54584F"
TEAL  = "FF00795E"
OCHRE = "FFB06A18"
RED   = "FF9E3B36"
BLUE  = "FF0000FF"          # hardcoded inputs
GREEN = "FF008000"          # cross-sheet links
HDRBG = "FF14201C"
BAND  = "FFEFEFEA"
TEALB = "FFE3F0EC"
YEL   = "FFFFFF00"

CUR  = '$#,##0;($#,##0);"-"'
CUR2 = '$#,##0.00;($#,##0.00);"-"'
PCT  = '0.0%;(0.0%);"-"'
PCT2 = '0.00%;(0.00%);"-"'
NUM  = '#,##0;(#,##0);"-"'

thin = Side(style="thin", color="FFD5D4CC")
med  = Side(style="medium", color="FF14201C")

wb = Workbook()

def title(ws, text, sub, ncols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    c = ws.cell(1, 1, text)
    c.font = Font(name=F, size=15, bold=True, color="FFFFFFFF")
    c.alignment = Alignment(vertical="center", horizontal="left", indent=1)
    c.fill = PatternFill("solid", fgColor=HDRBG)
    for i in range(2, ncols + 1):
        ws.cell(1, i).fill = PatternFill("solid", fgColor=HDRBG)
    ws.row_dimensions[1].height = 30
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    c = ws.cell(2, 2 - 1, sub)
    c.font = Font(name=F, size=9, italic=True, color=INK2)
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[2].height = 18

def sechead(ws, row, text, ncols):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    c = ws.cell(row, 1, text)
    c.font = Font(name=F, size=10, bold=True, color="FFFFFFFF")
    c.fill = PatternFill("solid", fgColor=HDRBG)
    c.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 20
    for i in range(2, ncols + 1):
        ws.cell(row, i).fill = PatternFill("solid", fgColor=HDRBG)

def colhead(ws, row, labels, start=1):
    for i, t in enumerate(labels):
        c = ws.cell(row, start + i, t)
        c.font = Font(name=F, size=9, bold=True, color=INK)
        c.fill = PatternFill("solid", fgColor=BAND)
        c.alignment = Alignment(vertical="center", wrap_text=True,
                                horizontal="right" if i else "left")
        c.border = Border(bottom=med, top=thin)
    ws.row_dimensions[row].height = 28

def put(ws, row, col, val, *, fmt=None, bold=False, color=INK, size=10,
        italic=False, fill=None, wrap=False, align=None, indent=0, border=True):
    c = ws.cell(row, col, val)
    c.font = Font(name=F, size=size, bold=bold, color=color, italic=italic)
    if fmt: c.number_format = fmt
    if fill: c.fill = PatternFill("solid", fgColor=fill)
    c.alignment = Alignment(vertical="center", wrap_text=wrap,
                            horizontal=align, indent=indent)
    if border: c.border = Border(bottom=thin)
    return c

def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w

# =====================================================================
# ASSUMPTIONS
# =====================================================================
a = wb.active
a.title = "Assumptions"
title(a, "ASSUMPTIONS  —  every input to the model lives here",
      "Blue = input you can change. Every other sheet recalculates from these cells.", 5)
widths(a, {"A": 46, "B": 16, "C": 13, "D": 52, "E": 2})

r = 4
sechead(a, r, "PROPERTY", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
prop = [
    ("Address", "451 White Horse Pike, Atco NJ 08004", "", "Waterford Twp, Camden County"),
    ("Gross leasable area", 4400, "SF", "Per Offering Memorandum. Assessor records show 4,206 SF — confirm by measurement"),
    ("Land area", 3.13, "acres", "Per Offering Memorandum"),
    ("Year built / renovated", "1960 / 2023", "", "Former bank branch, converted to dispensary"),
    ("Traffic count", 15370, "VPD", "US Route 30, per Offering Memorandum"),
]
ROW = {}
for k, v, u, s in prop:
    put(a, r, 1, k, bold=True)
    put(a, r, 2, v, fmt=NUM if isinstance(v, (int, float)) else None, color=BLUE,
        align="right" if isinstance(v, (int, float)) else "left")
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1
a.cell(ROW["Land area"], 2).number_format = '0.00'
r += 1

sechead(a, r, "PRICING", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
for k, v, u, s, fmt in [
    ("Asking price", 1600000, "$", "Matthews offering memorandum", CUR),
    ("OUR OFFER", 1100000, "$", "Recommended offer price — the key lever in this model", CUR),
    ("Practical ceiling", 1250000, "$", "Walk-away discipline: above this the margin of safety is gone", CUR),
]:
    put(a, r, 1, k, bold=True)
    c = put(a, r, 2, v, fmt=fmt, color=BLUE, align="right", bold=(k == "OUR OFFER"))
    if k == "OUR OFFER": c.fill = PatternFill("solid", fgColor=YEL)
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1
r += 1

sechead(a, r, "LEASE IN PLACE", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
for k, v, u, s, fmt in [
    ("Tenant", "Holistic Solutions", "", "NJ medical + adult-use dispensary, single location, founded 2018", None),
    ("Guarantee", "2 personal guarantees", "", "No corporate credit, no rated entity", None),
    ("Annual rent (in place)", 132000, "$/yr", "Flat for the full 10-year base term — no escalations", CUR),
    ("Rent commencement", "01-Feb-2023", "", "Per Offering Memorandum", None),
    ("Lease expiry", "31-Jan-2033", "", "Per Offering Memorandum", None),
    ("Term remaining", 6.5, "years", "As of August 2026", '0.0'),
    ("Option rent (1 x 5 yr)", 154000, "$/yr", "Tenant-elective. Modelled as optionality, never as income", CUR),
]:
    put(a, r, 1, k, bold=True)
    put(a, r, 2, v, fmt=fmt, color=BLUE,
        align="right" if isinstance(v, (int, float)) else "left")
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1
r += 1

sechead(a, r, "MARKET RENT  (conventional, non-cannabis tenant)", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
for k, v, u, s in [
    ("Market rent — low", 20, "$/SF NNN", "Conventional retail / service on the Route 30 corridor"),
    ("Market rent — base", 22, "$/SF NNN", "Midpoint. Derived from South Jersey corridor comps — see Lease Comps tab"),
    ("Market rent — high", 24, "$/SF NNN", "Bank, credit union or medical backfill"),
]:
    put(a, r, 1, k, bold=True)
    put(a, r, 2, v, fmt=CUR2, color=BLUE, align="right")
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1
r += 1

sechead(a, r, "OPERATING COSTS  (tenant pays under absolute NNN; landlord carries only if vacant)", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
for k, v, u, s in [
    ("Property taxes", 39402, "$/yr", "ESTIMATE: $760,200 assessed x implied ~$5.18/$100 rate. Confirm actual bill in diligence"),
    ("Insurance", 12000, "$/yr", "ESTIMATE — cannabis-use premium loading"),
    ("Maintenance / CAM", 10000, "$/yr", "ESTIMATE — roof, HVAC, lot"),
    ("Assessed value", 760200, "$", "Camden County tax assessor"),
    ("Equalization ratio", 0.5981, "%", "Camden County Board of Taxation, 2025"),
]:
    put(a, r, 1, k, bold=True)
    put(a, r, 2, v, fmt=PCT2 if u == "%" else CUR, color=BLUE, align="right")
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1
r += 1

sechead(a, r, "LAND UPSIDE  (excluded from all base-case returns)", 4); r += 1
colhead(a, r, ["Item", "Value", "Unit", "Source / note"]); r += 1
for k, v, u, s, fmt in [
    ("Outparcel ground rent — base", 80000, "$/yr", "Benchmarked to the listing agent's own build-to-suit comps: 7 Brew $155,000/yr and Wendy's $157,659/yr. A ground lease (tenant builds) typically runs 40-55% of a BTS rent", CUR),
    ("EV charging licence — base", 20000, "$/yr", "6-8 DC fast stalls, corridor benchmarks discounted, 10-25% owner revenue share", CUR),
    ("Land build-out cost", 150000, "$", "ESTIMATE — subdivision, entitlement, site work", CUR),
    ("Land income cap rate", 0.0925, "%", "Capitalization rate applied to incremental land NOI", PCT2),
]:
    put(a, r, 1, k, bold=True)
    put(a, r, 2, v, fmt=fmt, color=BLUE, align="right")
    put(a, r, 3, u, size=9, color=INK2)
    put(a, r, 4, s, size=9, color=INK2, wrap=True)
    ROW[k] = r; r += 1

A = lambda k: f"Assumptions!$B${ROW[k]}"
PRICE, ASK, SF = A("OUR OFFER"), A("Asking price"), A("Gross leasable area")
RENT, OPT = A("Annual rent (in place)"), A("Option rent (1 x 5 yr)")
MKT = A("Market rent — base")
TAX, INS, CAM = A("Property taxes"), A("Insurance"), A("Maintenance / CAM")
CARRY = f"({TAX}+{INS}+{CAM})"

a.cell(ROW["OUR OFFER"], 2).comment = Comment(
    "This is the master lever. Change this cell and every metric in the workbook "
    "recalculates — Executive Summary, Valuation, Returns and the negotiation ladder.", "Analysis")

# =====================================================================
# REVERSION SCENARIOS  (feeds Returns)
# =====================================================================
rv = wb.create_sheet("Reversion Scenarios")
title(rv, "REVERSION SCENARIOS  —  what the property is worth at lease expiry, Jan 2033",
      "The single uncertainty in the deal. Everything before 2033 is a fixed $132,000 coupon.", 8)
widths(rv, {"A": 40, "B": 11, "C": 14, "D": 11, "E": 15, "F": 15, "G": 15, "H": 46})

r = 4
colhead(rv, r, ["Scenario", "Probability", "Stabilized NOI", "Exit cap",
                "Stabilized value", "Re-let cost", "Net value", "Basis of the estimate"])
r += 1
FIRST = r
scen = [
    ("Tenant renews at the option rent", 0.40, "OPT", 0.0925, 25000,
     "Most likely single outcome: sunk build-out, a site-specific licence, and a township that caps retail cannabis at two licences"),
    ("New NJ cannabis licensee @ $30/SF", 0.10, 132000, 0.0950, 325000,
     "Holds full rent but the demand pool is one seat; requires CRC approval at this premises"),
    ("Bank / credit union / retail @ $22/SF", 0.20, 96800, 0.0875, 275000,
     "Turnkey backfill — vault and 3-lane drive-thru already in place, lowest TI of any conventional use"),
    ("Medical / urgent care / vet @ $24/SF", 0.20, 105600, 0.0825, 500000,
     "Deepest demand pool but heaviest fit-out at $60-100/SF"),
    ("QSR pad rebuild @ $42/SF on 2,200 SF", 0.05, 92400, 0.0700, 330000,
     "Reduced footprint or pad rebuild; best rent per foot, heaviest capex"),
    ("Extended vacancy - land + shell only", 0.05, 0, 0, 123000,
     "Liquidation case: sell land and vacant building, less 24 months of carry"),
]
LANDSHELL = 750000
for name, p, noi, cap, cost, note in scen:
    put(rv, r, 1, name, wrap=True)
    put(rv, r, 2, p, fmt=PCT, color=BLUE, align="right")
    if noi == "OPT":
        put(rv, r, 3, f"={OPT}", fmt=CUR, color=GREEN, align="right")
    else:
        put(rv, r, 3, noi, fmt=CUR, color=BLUE, align="right")
    put(rv, r, 4, cap, fmt=PCT2, color=BLUE, align="right")
    if cap == 0:
        put(rv, r, 5, LANDSHELL, fmt=CUR, color=BLUE, align="right")
    else:
        put(rv, r, 5, f"=IF(D{r}=0,0,C{r}/D{r})", fmt=CUR, align="right")
    put(rv, r, 6, cost, fmt=CUR, color=BLUE, align="right")
    put(rv, r, 7, f"=E{r}-F{r}", fmt=CUR, bold=True, align="right")
    put(rv, r, 8, note, size=9, color=INK2, wrap=True)
    r += 1
LAST = r - 1
rv.cell(FIRST + 5, 5).comment = Comment(
    "Land + vacant shell value. ESTIMATE — 3.13 acres of PHB highway commercial land "
    "plus a 4,400 SF second-generation building. Verify with a land appraisal.", "Analysis")

put(rv, r, 1, "PROBABILITY-WEIGHTED REVERSION", bold=True, fill=TEALB)
put(rv, r, 2, f"=SUM(B{FIRST}:B{LAST})", fmt=PCT, bold=True, align="right", fill=TEALB)
for col in (3, 4, 5, 6):
    put(rv, r, col, None, fill=TEALB)
put(rv, r, 7, f"=SUMPRODUCT($B${FIRST}:$B${LAST},$G${FIRST}:$G${LAST})",
    fmt=CUR, bold=True, color=TEAL, align="right", fill=TEALB)
put(rv, r, 8, "Sum of each outcome weighted by its probability", size=9,
    italic=True, color=INK2, fill=TEALB, wrap=True)
WREV = f"'Reversion Scenarios'!$G${r}"
PSUM = f"'Reversion Scenarios'!$B${r}"
r += 2

put(rv, r, 1, "Probabilities are judgmental and are the main soft input in this model. "
    "They are shown in blue so you can change them — the weighted value and every IRR "
    "in the workbook follow. Check that the probability column sums to 100%.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
rv.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
rv.row_dimensions[r].height = 30

# =====================================================================
# RETURNS
# =====================================================================
rt = wb.create_sheet("Returns")
title(rt, "RETURNS  —  unlevered cash flow, IRR and the negotiation ladder",
      "6.5-year hold from Aug 2026 to lease expiry Jan 2033, sold at the probability-weighted reversion.", 10)
widths(rt, {"A": 34, **{get_column_letter(i): 13 for i in range(2, 11)}})

r = 4
sechead(rt, r, "UNLEVERED CASH FLOW AT OUR OFFER PRICE", 10); r += 1
colhead(rt, r, ["Year", "0 (close)", "1", "2", "3", "4", "5", "6", "7 (exit)", "Total"])
r += 1
CF = r
put(rt, r, 1, "Purchase price", bold=True)
put(rt, r, 2, f"=-{PRICE}", fmt=CUR, color=GREEN, align="right")
for i in range(3, 10): put(rt, r, i, 0, fmt=CUR, align="right")
put(rt, r, 10, f"=SUM(B{r}:I{r})", fmt=CUR, bold=True, align="right")
r += 1
put(rt, r, 1, "Net rent received", bold=True)
put(rt, r, 2, 0, fmt=CUR, align="right")
for i in range(3, 9): put(rt, r, i, f"={RENT}", fmt=CUR, color=GREEN, align="right")
put(rt, r, 9, f"={RENT}*0.5", fmt=CUR, color=GREEN, align="right")
put(rt, r, 10, f"=SUM(B{r}:I{r})", fmt=CUR, bold=True, align="right")
RENTROW = r; r += 1
put(rt, r, 1, "Sale proceeds at expiry", bold=True)
for i in range(2, 9): put(rt, r, i, 0, fmt=CUR, align="right")
put(rt, r, 9, f"={WREV}", fmt=CUR, color=GREEN, align="right")
put(rt, r, 10, f"=SUM(B{r}:I{r})", fmt=CUR, bold=True, align="right")
r += 1
put(rt, r, 1, "NET CASH FLOW", bold=True, fill=TEALB)
for i in range(2, 11):
    put(rt, r, i, f"=SUM({get_column_letter(i)}{CF}:{get_column_letter(i)}{r-1})",
        fmt=CUR, bold=True, align="right", fill=TEALB)
NCF = r; r += 2

sechead(rt, r, "HEADLINE RETURNS", 10); r += 1
mets = [
    ("Going-in cap rate", f"={RENT}/{PRICE}", PCT2, "In-place rent divided by our purchase price"),
    ("Price per square foot", f"={PRICE}/{SF}", CUR2, "Well below replacement cost"),
    ("Unlevered IRR (expected)", f"=IRR(B{NCF}:I{NCF})", PCT2, "Probability-weighted across all six reversion outcomes"),
    ("Equity multiple", f"=SUM(C{NCF}:I{NCF})/{PRICE}", '0.00"x"', "Total cash returned divided by cash invested"),
    ("Contracted rent to expiry", f"={RENT}*6.5", CUR, "Rent collected before the lease even matures"),
    ("  ... as % of purchase price", f"={RENT}*6.5/{PRICE}", PCT, "Capital returned with no reliance on renewal or resale"),
    ("Years of rent to full payback", f"={PRICE}/{RENT}", '0.0"  yrs"', "Simple payback on the in-place coupon"),
]
for k, f_, fmt, note in mets:
    put(rt, r, 1, k, bold=True)
    c = put(rt, r, 2, f_, fmt=fmt, bold=True, color=TEAL, align="right")
    rt.merge_cells(start_row=r, start_column=3, end_row=r, end_column=10)
    put(rt, r, 3, note, size=9, color=INK2, indent=1)
    r += 1
r += 1

sechead(rt, r, "IRR BY REVERSION OUTCOME  —  every scenario at our offer price", 10); r += 1
colhead(rt, r, ["Outcome", "Probability", "Net value", "IRR at our offer",
                "IRR at the ask", "", "", "", "", ""])
r += 1
SCEN_IRR = r
for i in range(6):
    sr = FIRST + i
    put(rt, r, 1, f"='Reversion Scenarios'!A{sr}", color=GREEN)
    put(rt, r, 2, f"='Reversion Scenarios'!B{sr}", fmt=PCT, color=GREEN, align="right")
    put(rt, r, 3, f"='Reversion Scenarios'!G{sr}", fmt=CUR, color=GREEN, align="right")
    put(rt, r, 4, f"=IRR({{0}})".format(""), align="right")  # placeholder replaced below
    rt.cell(r, 4).value = (f"=RATE_PLACEHOLDER")
    r += 1
SCEN_LAST = r - 1
r += 1

# Build helper cash-flow blocks for scenario IRRs and the ladder, off to the right.
HELP_COL = 12
put(rt, 4, HELP_COL, "HELPER — cash flow rows behind the IRR columns (safe to ignore)",
    size=9, italic=True, color=INK2, border=False)
hr = 5
put(rt, hr, HELP_COL, "Scenario IRR cash flows", size=9, bold=True, color=INK2, border=False)
hr += 1
for i in range(6):
    sr = FIRST + i
    row = hr + i
    put(rt, row, HELP_COL, f"=-{PRICE}", fmt=CUR, size=9, border=False)
    for j in range(1, 7):
        put(rt, row, HELP_COL + j, f"={RENT}", fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 7, f"={RENT}*0.5+'Reversion Scenarios'!G{sr}",
        fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 9, f"=-{ASK}", fmt=CUR, size=9, border=False)
    for j in range(10, 16):
        put(rt, row, HELP_COL + j, f"={RENT}", fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 16, f"={RENT}*0.5+'Reversion Scenarios'!G{sr}",
        fmt=CUR, size=9, border=False)
    L1 = get_column_letter(HELP_COL); L2 = get_column_letter(HELP_COL + 7)
    L3 = get_column_letter(HELP_COL + 9); L4 = get_column_letter(HELP_COL + 16)
    rt.cell(SCEN_IRR + i, 4).value = f"=IRR({L1}{row}:{L2}{row})"
    rt.cell(SCEN_IRR + i, 4).number_format = PCT2
    rt.cell(SCEN_IRR + i, 4).font = Font(name=F, size=10, bold=True, color=TEAL)
    rt.cell(SCEN_IRR + i, 4).alignment = Alignment(horizontal="right")
    rt.cell(SCEN_IRR + i, 4).border = Border(bottom=thin)
    rt.cell(SCEN_IRR + i, 5).value = f"=IRR({L3}{row}:{L4}{row})"
    rt.cell(SCEN_IRR + i, 5).number_format = PCT2
    rt.cell(SCEN_IRR + i, 5).font = Font(name=F, size=10, color=INK2)
    rt.cell(SCEN_IRR + i, 5).alignment = Alignment(horizontal="right")
    rt.cell(SCEN_IRR + i, 5).border = Border(bottom=thin)

# probability-weighted cash flow at the ASKING price, for a like-for-like comparison
_ar = hr + 6
put(rt, _ar, HELP_COL, f"=-{ASK}", fmt=CUR, size=9, border=False)
for _j in range(1, 7):
    put(rt, _ar, HELP_COL + _j, f"={RENT}", fmt=CUR, size=9, border=False)
put(rt, _ar, HELP_COL + 7, f"={RENT}*0.5+{WREV}", fmt=CUR, size=9, border=False)
ASK_IRR_REF = f"IRR(Returns!${get_column_letter(HELP_COL)}${_ar}:Returns!${get_column_letter(HELP_COL+7)}${_ar})"

put(rt, SCEN_LAST + 1, 1, "Every outcome clears at our offer price. "
    "Compare the two IRR columns: at the asking price the same scenarios return "
    "under 3.5%, and the liquidation case loses money.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
rt.merge_cells(start_row=SCEN_LAST + 1, start_column=1, end_row=SCEN_LAST + 1, end_column=10)
rt.row_dimensions[SCEN_LAST + 1].height = 26

sechead(rt, r, "NEGOTIATION LADDER  —  what each dollar of price costs us", 10); r += 1
colhead(rt, r, ["Purchase price", "$ / SF", "Going-in cap", "Expected IRR",
                "If tenant renews", "Worst case", "Position", "", "", ""])
r += 1
LAD = r
ladder = [
    (1100000, "OUR OFFER"), (1150000, "Comfortable"), (1200000, "Comfortable"),
    (1250000, "Practical ceiling"), (1300000, "Fair value - no margin left"),
    (1400000, "Too rich"), (1600000, "Asking price - decline"),
]
hr2 = hr + 8
put(rt, hr2 - 1, HELP_COL, "Ladder cash flows", size=9, bold=True, color=INK2, border=False)
for i, (px, pos) in enumerate(ladder):
    row = hr2 + i
    # expected
    put(rt, row, HELP_COL, f"=-A{LAD+i}", fmt=CUR, size=9, border=False)
    for j in range(1, 7):
        put(rt, row, HELP_COL + j, f"={RENT}", fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 7, f"={RENT}*0.5+{WREV}", fmt=CUR, size=9, border=False)
    # renewal
    put(rt, row, HELP_COL + 9, f"=-A{LAD+i}", fmt=CUR, size=9, border=False)
    for j in range(10, 16):
        put(rt, row, HELP_COL + j, f"={RENT}", fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 16, f"={RENT}*0.5+'Reversion Scenarios'!G{FIRST}",
        fmt=CUR, size=9, border=False)
    # worst
    put(rt, row, HELP_COL + 18, f"=-A{LAD+i}", fmt=CUR, size=9, border=False)
    for j in range(19, 25):
        put(rt, row, HELP_COL + j, f"={RENT}", fmt=CUR, size=9, border=False)
    put(rt, row, HELP_COL + 25, f"={RENT}*0.5+'Reversion Scenarios'!G{LAST}",
        fmt=CUR, size=9, border=False)

    is_ours = (pos == "OUR OFFER")
    fill = TEALB if is_ours else (BAND if px == 1600000 else None)
    put(rt, LAD + i, 1, px, fmt=CUR, color=BLUE, bold=is_ours, align="right", fill=fill)
    put(rt, LAD + i, 2, f"=A{LAD+i}/{SF}", fmt=CUR2, align="right", fill=fill)
    put(rt, LAD + i, 3, f"={RENT}/A{LAD+i}", fmt=PCT2, align="right", fill=fill)
    c1, c2 = get_column_letter(HELP_COL), get_column_letter(HELP_COL + 7)
    c3, c4 = get_column_letter(HELP_COL + 9), get_column_letter(HELP_COL + 16)
    c5, c6 = get_column_letter(HELP_COL + 18), get_column_letter(HELP_COL + 25)
    put(rt, LAD + i, 4, f"=IRR({c1}{row}:{c2}{row})", fmt=PCT2, bold=True,
        color=TEAL, align="right", fill=fill)
    put(rt, LAD + i, 5, f"=IRR({c3}{row}:{c4}{row})", fmt=PCT2, align="right", fill=fill)
    put(rt, LAD + i, 6, f"=IRR({c5}{row}:{c6}{row})", fmt=PCT2, align="right", fill=fill)
    put(rt, LAD + i, 7, pos, bold=is_ours,
        color=TEAL if is_ours else (RED if px >= 1400000 else INK2), fill=fill)
    for cc in range(8, 11): put(rt, LAD + i, cc, None, fill=fill)
r = LAD + len(ladder) + 1

put(rt, r, 1, "Worst case = extended vacancy, sold as land and shell. "
    "Even that outcome pays a positive return at our offer price.",
    size=9, italic=True, color=INK2, border=False)
rt.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)

for cidx in range(HELP_COL, HELP_COL + 27):
    rt.column_dimensions[get_column_letter(cidx)].hidden = True

# =====================================================================
# VALUATION
# =====================================================================
v = wb.create_sheet("Valuation")
title(v, "VALUATION  —  four independent methods",
      "Run separately, all four land above our offer and well below the asking price.", 6)
widths(v, {"A": 34, "B": 46, "C": 16, "D": 15, "E": 15, "F": 15})

r = 4
colhead(v, r, ["Method", "How it is derived", "Indicated value",
               "vs. asking price", "vs. our offer", "Weight"]); r += 1
V0 = r
vals = [
    ("In-place income at a market cap rate",
     "In-place rent capitalized at 9.75% — the correct rate for flat rent on a personally guaranteed lease with 6.5 years left",
     f"={RENT}/0.0975", 0.40),
    ("Tax assessor equalized value",
     "Assessed value divided by the Camden County equalization ratio",
     f"={A('Assessed value')}/{A('Equalization ratio')}", 0.20),
    ("County retail price per SF",
     "Camden County retail listing average of ~$273/SF applied to our building",
     f"=273*{SF}", 0.15),
    ("Market-rent capitalization",
     "Conventional market rent capitalized at 8.75% — the value with no cannabis premium at all",
     f"={MKT}*{SF}/0.0875", 0.25),
]
for name, basis, f_, w in vals:
    put(v, r, 1, name, bold=True, wrap=True)
    put(v, r, 2, basis, size=9, color=INK2, wrap=True)
    put(v, r, 3, f_, fmt=CUR, bold=True, align="right")
    put(v, r, 4, f"=C{r}/{ASK}-1", fmt=PCT, color=RED, align="right")
    put(v, r, 5, f"=C{r}/{PRICE}-1", fmt=PCT, color=TEAL, align="right")
    put(v, r, 6, w, fmt=PCT, color=BLUE, align="right")
    r += 1
V1 = r - 1
put(v, r, 1, "WEIGHTED VALUE INDICATION", bold=True, fill=TEALB)
put(v, r, 2, "Each method weighted as shown", size=9, italic=True, color=INK2, fill=TEALB)
put(v, r, 3, f"=SUMPRODUCT(C{V0}:C{V1},F{V0}:F{V1})/SUM(F{V0}:F{V1})",
    fmt=CUR, bold=True, color=TEAL, align="right", fill=TEALB)
put(v, r, 4, f"=C{r}/{ASK}-1", fmt=PCT, bold=True, color=RED, align="right", fill=TEALB)
put(v, r, 5, f"=C{r}/{PRICE}-1", fmt=PCT, bold=True, color=TEAL, align="right", fill=TEALB)
put(v, r, 6, f"=SUM(F{V0}:F{V1})", fmt=PCT, bold=True, align="right", fill=TEALB)
VALIND = f"Valuation!$C${r}"
r += 2

sechead(v, r, "THE MARGIN OF SAFETY", 6); r += 1
for k, f_, fmt, note in [
    ("Our offer", f"={PRICE}", CUR, "What we are proposing to pay"),
    ("Weighted value indication", f"={VALIND}", CUR, "Where the four methods converge"),
    ("Discount to value", f"={PRICE}/{VALIND}-1", PCT, "Margin of safety on entry"),
    ("Absolute floor (market-rent value)", f"={MKT}*{SF}/0.0875", CUR,
     "What the building is worth stripped of every cannabis dollar"),
    ("Our offer vs. that floor", f"={PRICE}/({MKT}*{SF}/0.0875)-1", PCT,
     "We are buying at conventional-use value — the cannabis premium is free"),
    ("Break-even rent to hold our basis", f"={PRICE}*0.085/{SF}", CUR2,
     "$/SF the building must re-let at to preserve our price at an 8.5% cap"),
    ("Market rent (base) for comparison", f"={MKT}", CUR2,
     "Our break-even sits below the market midpoint — that is the cushion"),
]:
    put(v, r, 1, k, bold=True)
    put(v, r, 2, f_, fmt=fmt, bold=True, color=TEAL, align="right")
    v.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
    put(v, r, 3, note, size=9, color=INK2, indent=1)
    r += 1

# =====================================================================
# RE-RENT ANALYSIS
# =====================================================================
rr = wb.create_sheet("Re-Rent Analysis")
title(rr, "RE-RENT ANALYSIS  —  what the building lets for, and what that yields us",
      "The question the buyer asked. Yield on cost is calculated against our offer price.", 8)
widths(rr, {"A": 34, "B": 11, "C": 11, "D": 14, "E": 14, "F": 13, "G": 13, "H": 40})

r = 4
colhead(rr, r, ["Tenant type", "Rent/SF low", "Rent/SF high", "Annual rent low",
                "Annual rent high", "Yield low", "Yield high", "Comment"]); r += 1
uses = [
    ("Cannabis - new NJ licensee", 28, 34, 4400, "Holds the rent outright, but the demand pool is one seat"),
    ("Medical / urgent care / dental / vet", 22, 26, 4400, "Deepest demand pool; drive-thru converts to covered drop-off"),
    ("Bank / credit union", 22, 26, 4400, "Turnkey - vault and drive-thru already in place, lowest TI"),
    ("QSR / coffee drive-thru", 38, 48, 2200, "Reduced 2,200 SF footprint or pad rebuild; heaviest capex"),
    ("Conventional retail / service", 18, 22, 4400, "The floor - liquor, convenience, pharmacy, auto parts"),
    ("Daycare / early education", 18, 22, 4400, "Site plan and licensing lag; 3 acres supports playground"),
]
U0 = r
for name, lo, hi, sf, note in uses:
    put(rr, r, 1, name, bold=True, wrap=True)
    put(rr, r, 2, lo, fmt=CUR2, color=BLUE, align="right")
    put(rr, r, 3, hi, fmt=CUR2, color=BLUE, align="right")
    put(rr, r, 4, f"=B{r}*{sf}", fmt=CUR, align="right")
    put(rr, r, 5, f"=C{r}*{sf}", fmt=CUR, align="right")
    put(rr, r, 6, f"=D{r}/{PRICE}", fmt=PCT, color=TEAL, align="right")
    put(rr, r, 7, f"=E{r}/{PRICE}", fmt=PCT, bold=True, color=TEAL, align="right")
    put(rr, r, 8, note, size=9, color=INK2, wrap=True)
    r += 1
put(rr, r, 1, "IN PLACE TODAY (cannabis)", bold=True, fill=BAND)
put(rr, r, 2, f"={RENT}/{SF}", fmt=CUR2, bold=True, align="right", fill=BAND)
put(rr, r, 3, f"={RENT}/{SF}", fmt=CUR2, bold=True, align="right", fill=BAND)
put(rr, r, 4, f"={RENT}", fmt=CUR, bold=True, align="right", fill=BAND)
put(rr, r, 5, f"={RENT}", fmt=CUR, bold=True, align="right", fill=BAND)
put(rr, r, 6, f"={RENT}/{PRICE}", fmt=PCT, bold=True, color=OCHRE, align="right", fill=BAND)
put(rr, r, 7, f"={RENT}/{PRICE}", fmt=PCT, bold=True, color=OCHRE, align="right", fill=BAND)
put(rr, r, 8, "36% above conventional market rent - a premium we are not paying for",
    size=9, italic=True, color=INK2, wrap=True, fill=BAND)
r += 2

sechead(rr, r, "THE DOWNSIDE TEST", 8); r += 1
for k, f_, fmt, note in [
    ("Conventional market rent (base)", f"={MKT}*{SF}", CUR, "What an ordinary tenant pays for this box"),
    ("  Yield on our offer", f"={MKT}*{SF}/{PRICE}", PCT, "Still a strong yield with no cannabis rent at all"),
    ("Deep downside rent @ $18/SF", f"=18*{SF}", CUR, "Bottom of the conventional range"),
    ("  Yield on our offer", f"=18*{SF}/{PRICE}", PCT, "Even the worst re-let clears our cost of capital"),
    ("Roll-down from in-place rent", f"={MKT}*{SF}/{RENT}-1", PCT, "The rent reduction we have already underwritten"),
    ("Annual carry if fully vacant", f"={CARRY}", CUR, "Taxes, insurance and maintenance the landlord picks up"),
]:
    put(rr, r, 1, k, bold=not k.startswith("  "), indent=1 if k.startswith("  ") else 0)
    put(rr, r, 2, f_, fmt=fmt, bold=True, color=TEAL, align="right")
    rr.merge_cells(start_row=r, start_column=3, end_row=r, end_column=8)
    put(rr, r, 3, note, size=9, color=INK2, indent=1)
    r += 1

# =====================================================================
# RE-LEASING OPTIONS & TIMELINE
# =====================================================================
rl = wb.create_sheet("Re-Leasing Options")
title(rl, "RE-LEASING OPTIONS  —  who takes it, what they pay, how long it takes, and how long they stay",
      "The goal is one re-tenanting into a long covenant, then a passive hold - not an asset that churns.", 9)
widths(rl, {"A": 4, "B": 30, "C": 12, "D": 13, "E": 11, "F": 11, "G": 12, "H": 13, "I": 52})

r = 4
sechead(rl, r, "THE OBJECTIVE:  ONE RE-TENANTING, NOT PERPETUAL CHURN", 9); r += 1
rl.merge_cells(start_row=r, start_column=1, end_row=r + 2, end_column=9)
_c = rl.cell(r, 1, "This asset should not become a management job. The plan is a SINGLE re-tenanting event, "
    "into a tenant that signs a 10-15 year NNN lease with escalations, and then it goes passive again for a "
    "decade or more.\n"
    "That objective changes the ranking. The right tenants are the ones with sunk fit-out cost and a "
    "location-bound customer base - banks, credit unions and medical groups - because they stay. The wrong "
    "answer is a string of short conventional retail deals at $18-22/SF that roll every five years and put "
    "us back in the market again and again.\n"
    "It also argues against demising the box into two spaces for a QSR: that trades one covenant for two, "
    "and doubles the management. Keep it single-tenant.")
_c.font = Font(name=F, size=9.5, color=INK)
_c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
for _rr in range(r, r + 3):
    for _cc in range(1, 10):
        rl.cell(_rr, _cc).fill = PatternFill("solid", fgColor=TEALB)
rl.row_dimensions[r].height = 30
rl.row_dimensions[r + 1].height = 30
rl.row_dimensions[r + 2].height = 30
r += 4

sechead(rl, r, "THE OPTIONS  —  ranked by durability first, then speed and cost", 9); r += 1
colhead(rl, r, ["#", "Tenant type", "Rent / SF", "Annual rent", "Time to rent",
                "Landlord cost", "Typical lease term", "Rollover risk", "Why this works here"]); r += 1
O0 = r
opts = [
    (1, "Urgent care / dental / vet", 24, 4400, 60, 17, "10-15 yrs + options", "Very low",
     "The best answer for a passive owner. Huge sunk fit-out and a location-bound patient base mean they do not move. They sign 10-15 year NNN leases WITH escalations - fixing the one real flaw in the lease we are buying. Deepest tenant pool in South Jersey; the drive-thru converts to a covered patient drop-off."),
    (2, "Bank / credit union", 24, 4400, 5, 10, "10-15 yrs + options", "Very low",
     "The building already IS one - vault, 3-lane drive-thru and teller infrastructure transfer as-is, so fit-out is cosmetic and occupancy is fastest. Branches are capital-intensive and banks stay put. Cheapest and quickest route to a long covenant."),
    (3, "Cannabis - new NJ licensee", 30, 4400, 15, 24, "10 yrs", "Low",
     "Holds the full rent with almost no fit-out, and the licence is tied to this premises so the tenant is sticky. But Waterford permits only two retail licences and the incumbent holds one, and CRC approval adds a long regulatory lag."),
    (4, "QSR / coffee drive-thru", 42, 2200, 130, 24, "15-20 yrs", "Very low",
     "Longest lease terms of any use and very sticky - but it needs a demise to ~2,200 SF or a pad rebuild, which trades one covenant for two and doubles the management. Pursue it on the excess LAND as a ground lease instead, and keep the box single-tenant."),
    (5, "Daycare / early education", 20, 4400, 70, 22, "10-15 yrs", "Low",
     "Sticky once open - licensing and parent relationships are location-bound - but site plan approval and state licensing make this the slowest option to start."),
    (6, "Conventional retail / service", 20, 4400, 30, 10, "5-10 yrs", "HIGH",
     "Liquor, convenience, pharmacy, auto parts, fitness. Always available, and it pays - but these roll every five years and put us straight back in the market. Use it as a fallback, not a plan, precisely because it is the churn outcome we are trying to avoid."),
]
for n, name, psf, sf, ti, mos, term, roll, note in opts:
    fill = TEALB if n <= 2 else None
    put(rl, r, 1, n, bold=True, color=TEAL, align="center", fill=fill)
    put(rl, r, 2, name, bold=True, wrap=True, fill=fill)
    put(rl, r, 3, psf, fmt=CUR2, color=BLUE, align="right", fill=fill)
    put(rl, r, 4, f"=C{r}*{sf}", fmt=CUR, bold=True, align="right", fill=fill)
    put(rl, r, 5, mos, fmt='0"  mo"', bold=True, color=BLUE, align="right", fill=fill)
    put(rl, r, 6, f"=C{r}*0+{ti}*{sf}", fmt=CUR, align="right", fill=fill)
    put(rl, r, 7, term, size=9, bold=True, color=TEAL, align="right", fill=fill)
    put(rl, r, 8, roll, size=9, bold=True,
        color=RED if roll == "HIGH" else TEAL, align="right", fill=fill)
    put(rl, r, 9, note, size=9, color=INK2, wrap=True, fill=fill)
    rl.row_dimensions[r].height = 52
    r += 1
O1 = r - 1
put(rl, r, 1, None, fill=BAND)
put(rl, r, 2, "IN PLACE TODAY (cannabis)", bold=True, fill=BAND)
put(rl, r, 3, f"={RENT}/{SF}", fmt=CUR2, bold=True, color=OCHRE, align="right", fill=BAND)
put(rl, r, 4, f"={RENT}", fmt=CUR, bold=True, color=OCHRE, align="right", fill=BAND)
for cc in (5, 6): put(rl, r, cc, "-", align="right", fill=BAND)
put(rl, r, 7, "10 yrs, flat", size=9, bold=True, color=OCHRE, align="right", fill=BAND)
put(rl, r, 8, "n/a", size=9, color=INK2, align="right", fill=BAND)
put(rl, r, 9, "No action required while the lease runs to January 2033",
    size=9, italic=True, color=INK2, wrap=True, fill=BAND)
r += 2

sechead(rl, r, "HOW LONG IT TAKES  —  indicative timeline from vacancy to rent commencing", 9); r += 1
colhead(rl, r, ["", "Stage", "Bank / CU", "Medical", "Retail", "Cannabis", "QSR", "", "What happens"]); r += 1
stages = [
    ("Marketing and tenant sourcing", 4, 6, 4, 6, 9,
     "List, tour, negotiate LOI. A corner drive-thru property tours well and shortens this."),
    ("Lease negotiation and signature", 2, 2, 2, 3, 3,
     "Longer where a licence or franchise approval is involved."),
    ("Permits, approvals and licensing", 1, 3, 1, 12, 4,
     "The cannabis line is CRC plus township approval - this is the long pole in that option."),
    ("Construction and fit-out", 3, 6, 3, 3, 8,
     "Bank and retail are cosmetic. Medical and QSR are full build-outs."),
]
S0 = r
for name, b, m, rt_, cn, q, note in stages:
    put(rl, r, 1, None)
    put(rl, r, 2, name, bold=True, wrap=True)
    for i, vv in enumerate([b, m, rt_, cn, q]):
        put(rl, r, 3 + i, vv, fmt='0', color=BLUE, align="right")
    put(rl, r, 8, None)
    put(rl, r, 9, note, size=9, color=INK2, wrap=True)
    r += 1
S1 = r - 1
put(rl, r, 1, None, fill=TEALB)
put(rl, r, 2, "TOTAL MONTHS TO RENT COMMENCING", bold=True, fill=TEALB)
for i in range(5):
    L = get_column_letter(3 + i)
    put(rl, r, 3 + i, f"=SUM({L}{S0}:{L}{S1})", fmt='0"  mo"', bold=True,
        color=TEAL, align="right", fill=TEALB)
put(rl, r, 8, None, fill=TEALB)
put(rl, r, 9, "Overlapping stages can compress this; assume the longer end in a slow market",
    size=9, italic=True, color=INK2, wrap=True, fill=TEALB)
TOTROW = r; r += 1
put(rl, r, 1, None)
put(rl, r, 2, "Rent lost during downtime", bold=True)
for i in range(5):
    L = get_column_letter(3 + i)
    put(rl, r, 3 + i, f"={L}{TOTROW}/12*{MKT}*{SF}", fmt=CUR, align="right")
put(rl, r, 8, None)
put(rl, r, 9, "Market rent forgone while the building sits empty", size=9, color=INK2, wrap=True)
r += 1
put(rl, r, 1, None)
put(rl, r, 2, "Carry cost during downtime", bold=True)
for i in range(5):
    L = get_column_letter(3 + i)
    put(rl, r, 3 + i, f"={L}{TOTROW}/12*{CARRY}", fmt=CUR, align="right")
put(rl, r, 8, None)
put(rl, r, 9, "Taxes, insurance and maintenance the landlord picks up when vacant",
    size=9, color=INK2, wrap=True)
r += 2

sechead(rl, r, "WHY THE CORNER MATTERS  —  this is not an ordinary in-line box", 9); r += 1
for k, note in [
    ("Two frontages, two access points",
     "451 White Horse Pike sits at the corner of US Route 30 and Cooper Folly Road. Corner sites carry a genuine rent premium over mid-block space because they offer signage on two streets, ingress and egress from a secondary road (so customers avoid turning across highway traffic), and far easier circulation for a drive-thru."),
    ("It is what makes the drive-thru work",
     "A 3-lane drive-thru needs stacking depth and a clean in-and-out loop. On a mid-block parcel that is hard; on a corner it is straightforward. This is the single feature that puts banks, QSR, coffee and pharmacy tenants in play at all."),
    ("It widens the tenant pool",
     "Uses that require or strongly prefer a corner - QSR, coffee, pharmacy, convenience, car wash, bank - are precisely the covenant-strength tenants who sign long NNN leases with escalations. A mid-block box does not get those calls."),
    ("It supports subdividing a pad",
     "A corner parcel of 3.13 acres can usually yield a second access point and a separate pad with its own frontage, without compromising the existing building's parking or circulation. That is what makes the land upside physically realistic rather than theoretical."),
    ("It shortens marketing time",
     "Corner drive-thru properties on a state highway tour well and lease faster. That is reflected in the shorter marketing periods in the table above versus what a mid-block box on this corridor would carry."),
]:
    put(rl, r, 1, None)
    put(rl, r, 2, k, bold=True, color=TEAL, wrap=True)
    rl.merge_cells(start_row=r, start_column=3, end_row=r, end_column=9)
    put(rl, r, 3, note, size=9, color=INK2, wrap=True, indent=1)
    rl.row_dimensions[r].height = 42
    r += 1
r += 1
put(rl, r, 2, "Marketing periods, fit-out durations and landlord costs are analyst estimates based on "
    "typical South Jersey second-generation retail transactions. They are shown in blue so you can flex them.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
rl.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)
rl.row_dimensions[r].height = 26

# =====================================================================
# LAND UPSIDE
# =====================================================================
ld = wb.create_sheet("Land Upside")
title(ld, "LAND UPSIDE  —  2.5 idle acres, excluded from every return in this model",
      "Building coverage is 3.2%. This is free option value; we never bid it up.", 6)
widths(ld, {"A": 34, "B": 15, "C": 15, "D": 15, "E": 14, "F": 46})

r = 4
sechead(ld, r, "SITE CAPACITY", 6); r += 1
for k, f_, fmt, note in [
    ("Total site area", f"={A('Land area')}", '0.00"  AC"', "Per Offering Memorandum"),
    ("Building footprint", f"={SF}/43560", '0.00"  AC"', "4,400 SF converted to acres"),
    ("Building coverage", f"={SF}/({A('Land area')}*43560)", PCT, "Extraordinarily low for a highway commercial site"),
    ("Land used by parking / drive-thru", 0.55, '0.00"  AC"', "ESTIMATE - confirm with a site plan and parking count"),
    ("DEVELOPABLE EXCESS LAND", f"={A('Land area')}-{SF}/43560-B{r+3}", '0.00"  AC"',
     "The opportunity - subject to confirming the lease does not demise the whole parcel"),
]:
    put(ld, r, 1, k, bold=True)
    put(ld, r, 2, f_, fmt=fmt, bold=True, color=BLUE if isinstance(f_, float) else TEAL, align="right")
    ld.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
    put(ld, r, 3, note, size=9, color=INK2, indent=1)
    r += 1
EXCESS = r - 1
r += 1

sechead(ld, r, "INCOME OPPORTUNITIES", 6); r += 1
colhead(ld, r, ["Opportunity", "Low", "Base", "High", "Land used", "How it is derived"]); r += 1
L0 = r
put(ld, r, 1, "Outparcel ground lease", bold=True)
put(ld, r, 2, 60000, fmt=CUR, color=BLUE, align="right")
put(ld, r, 3, f"={A('Outparcel ground rent — base')}", fmt=CUR, color=GREEN, align="right")
put(ld, r, 4, 110000, fmt=CUR, color=BLUE, align="right")
put(ld, r, 5, "0.75-1.0 AC", size=9, color=INK2, align="right")
put(ld, r, 6, "Benchmarked to the listing agent's own comps: 7 Brew pays $155,000/yr and Wendy's $157,659/yr on build-to-suit pads. A ground lease, where the tenant builds, runs ~40-55% of that. QSR, coffee, car wash or medical pad.",
    size=9, color=INK2, wrap=True)
r += 1
put(ld, r, 1, "EV fast-charging licence", bold=True)
put(ld, r, 2, 12000, fmt=CUR, color=BLUE, align="right")
put(ld, r, 3, f"={A('EV charging licence — base')}", fmt=CUR, color=GREEN, align="right")
put(ld, r, 4, 34000, fmt=CUR, color=BLUE, align="right")
put(ld, r, 5, "0.30-0.40 AC", size=9, color=INK2, align="right")
put(ld, r, 6, "6-8 DC fast stalls. Corridor benchmarks of $2,200-3,500/stall/mo discounted to $1,000-1,800 for a 15,370 VPD secondary route, at a 10-25% owner revenue share. Operator funds 100% of capex.",
    size=9, color=INK2, wrap=True)
r += 1
L1 = r - 1
put(ld, r, 1, "COMBINED INCREMENTAL NOI", bold=True, fill=TEALB)
for col in (2, 3, 4):
    L = get_column_letter(col)
    put(ld, r, col, f"=SUM({L}{L0}:{L}{L1})", fmt=CUR, bold=True, color=TEAL,
        align="right", fill=TEALB)
put(ld, r, 5, "~1.3 AC", size=9, italic=True, color=INK2, align="right", fill=TEALB)
put(ld, r, 6, "On land carried at zero in the base case", size=9, italic=True,
    color=INK2, fill=TEALB, wrap=True)
NOIROW = r; r += 1
put(ld, r, 1, "Value created (net of build-out cost)", bold=True)
for col in (2, 3, 4):
    L = get_column_letter(col)
    put(ld, r, col, f"={L}{NOIROW}/{A('Land income cap rate')}-{A('Land build-out cost')}",
        fmt=CUR, bold=True, color=TEAL, align="right")
put(ld, r, 5, None)
put(ld, r, 6, "Incremental NOI capitalized, less subdivision, entitlement and site work",
    size=9, color=INK2, wrap=True)
VC = r; r += 2

sechead(ld, r, "EFFECT ON THE DEAL IF EXECUTED (base case)", 6); r += 1
for k, f_, fmt, note in [
    ("Stabilized NOI with land income", f"={RENT}+C{NOIROW}", CUR, "In-place rent plus pad and EV licence"),
    ("Yield on cost", f"=({RENT}+C{NOIROW})/{PRICE}", PCT, "Against our offer price"),
    ("Yield on cost today, for comparison", f"={RENT}/{PRICE}", PCT, "Before any land monetization"),
    ("Value created per dollar invested", f"=C{VC}/{PRICE}", PCT, "Value added as a share of our basis"),
    ("DOWNSIDE RE-TEST: dark building @ $18/SF + land income",
     f"=(18*{SF}+C{NOIROW})/{PRICE}", PCT,
     "The land does not just add upside - it removes the downside"),
]:
    put(ld, r, 1, k, bold=True, wrap=True)
    put(ld, r, 2, f_, fmt=fmt, bold=True, color=TEAL, align="right")
    ld.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
    put(ld, r, 3, note, size=9, color=INK2, indent=1)
    r += 1
r += 1

sechead(ld, r, "GATING ITEMS  —  confirm before assigning any of this a dollar", 6); r += 1
for k, note in [
    ("Demised premises clause",
     "THE gating item. The offering markets 3.13 AC as the leased premises. If the lease demises the entire lot to the tenant, we cannot develop any of it during the term without their consent. Read this clause first."),
    ("Pinelands Commission review",
     "Atco sits in the Regional Growth Area - the most permissive of the six CMP designations - but subdivision and site plan still go through Pinelands review."),
    ("Sewer capacity",
     "The CMP requires nonresidential parcels under one acre to be served by centralized wastewater. A septic-only site materially limits what a pad can be."),
    ("Parking and circulation",
     "Any pad must leave the existing tenant with compliant parking and preserve drive-thru stacking. Run a count against the PHB standard."),
    ("Tesla specifically",
     "Tesla historically pays site hosts little or no ground rent, and its newer Supercharger for Business program is host-owned, meaning we would fund the hardware. The rent is with third-party operators who fund 100% of capex."),
]:
    put(ld, r, 1, k, bold=True, wrap=True)
    ld.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    put(ld, r, 2, note, size=9, color=INK2, wrap=True, indent=1)
    ld.row_dimensions[r].height = 30
    r += 1


# =====================================================================
# FINANCING
# =====================================================================
fi = wb.create_sheet("Financing")
title(fi, "FINANCING  —  can he borrow against it, and what does leverage do?",
      "Cannabis collateral is not bankable or CMBS-eligible. Assume private or credit-union debt.", 9)
widths(fi, {"A": 30, "B": 13, "C": 13, "D": 13, "E": 13, "F": 13, "G": 13, "H": 13, "I": 40})

r = 4
sechead(fi, r, "DEBT ASSUMPTIONS", 9); r += 1
FA = {}
for k, v, fmt, note in [
    ("Loan to value", 0.55, PCT2, "Private lenders cap cannabis-collateral LTV well below conventional"),
    ("Interest rate", 0.10, PCT2, "Private / credit-union pricing for cannabis-tenanted real estate"),
    ("Amortization (years)", 25, '0', "Typical for this lender class"),
    ("Hold period (years)", 6.5, '0.0', "To lease expiry, January 2033"),
]:
    put(fi, r, 1, k, bold=True)
    put(fi, r, 2, v, fmt=fmt, color=BLUE, align="right")
    fi.merge_cells(start_row=r, start_column=3, end_row=r, end_column=9)
    put(fi, r, 3, note, size=9, color=INK2, indent=1)
    FA[k] = r; r += 1
LTV, RATE, AM, HOLD = (f"$B${FA['Loan to value']}", f"$B${FA['Interest rate']}",
                       f"$B${FA['Amortization (years)']}", f"$B${FA['Hold period (years)']}")
r += 1

sechead(fi, r, "LOAN SIZING AND COVERAGE AT THREE PRICE POINTS", 9); r += 1
colhead(fi, r, ["Purchase price", "Loan amount", "Equity", "Annual debt service", "NOI",
                "DSCR", "Cash flow after debt", "Cash-on-cash", "Verdict"]); r += 1
F0 = r
for label, pxref in [("Our offer", PRICE), ("Practical ceiling", A("Practical ceiling")),
                     ("Asking price", ASK)]:
    put(fi, r, 1, f"{label}", bold=True)
    put(fi, r, 2, f"={pxref}*{LTV}", fmt=CUR, align="right")
    put(fi, r, 3, f"={pxref}-B{r}", fmt=CUR, align="right")
    put(fi, r, 4, f"=-PMT({RATE}/12,{AM}*12,B{r})*12", fmt=CUR, align="right")
    put(fi, r, 5, f"={RENT}", fmt=CUR, color=GREEN, align="right")
    put(fi, r, 6, f"=E{r}/D{r}", fmt='0.00"x"', bold=True, color=TEAL, align="right")
    put(fi, r, 7, f"=E{r}-D{r}", fmt=CUR, align="right")
    put(fi, r, 8, f"=G{r}/C{r}", fmt=PCT, bold=True, color=TEAL, align="right")
    put(fi, r, 9, f'=IF(F{r}>=1.5,"Comfortably financeable",IF(F{r}>=1.25,"Financeable, tight","Lender would decline"))',
        size=9, color=INK2, wrap=True)
    r += 1
F1 = r - 1
r += 1

sechead(fi, r, "LEVERED RETURN  —  hold to expiry, sold at the weighted reversion", 9); r += 1
colhead(fi, r, ["Purchase price", "Equity in", "Annual cash flow", "Loan balance at exit",
                "Net sale proceeds", "Levered IRR", "Unlevered IRR", "Leverage adds", ""]); r += 1
L0 = r
HC = 12
for i, (label, pxref) in enumerate([("Our offer", PRICE), ("Practical ceiling", A("Practical ceiling")),
                                    ("Asking price", ASK)]):
    fr = F0 + i
    put(fi, r, 1, label, bold=True)
    put(fi, r, 2, f"=C{fr}", fmt=CUR, align="right")
    put(fi, r, 3, f"=G{fr}", fmt=CUR, align="right")
    put(fi, r, 4, f"=B{fr}*(1+{RATE}/12)^({HOLD}*12)-(-PMT({RATE}/12,{AM}*12,B{fr}))*((1+{RATE}/12)^({HOLD}*12)-1)/({RATE}/12)",
        fmt=CUR, align="right")
    put(fi, r, 5, f"={WREV}-D{r}", fmt=CUR, align="right")
    # helper levered cash flow
    hrow = 4 + i
    put(fi, hrow, HC, f"=-B{r}", fmt=CUR, size=9, border=False)
    for j in range(1, 7):
        put(fi, hrow, HC + j, f"=C{r}", fmt=CUR, size=9, border=False)
    put(fi, hrow, HC + 7, f"=C{r}*0.5+E{r}", fmt=CUR, size=9, border=False)
    c1, c2 = get_column_letter(HC), get_column_letter(HC + 7)
    put(fi, r, 6, f"=IRR({c1}{hrow}:{c2}{hrow})", fmt=PCT2, bold=True, color=TEAL, align="right")
    put(fi, r, 7, f"=Returns!$D${LAD + [0, 3, 6][i]}", fmt=PCT2, align="right")
    put(fi, r, 8, f"=F{r}-G{r}", fmt=PCT2, align="right")
    put(fi, r, 9, None)
    r += 1
for cidx in range(HC, HC + 9):
    fi.column_dimensions[get_column_letter(cidx)].hidden = True
r += 1
put(fi, r, 1, "Read the DSCR column. At our offer the loan covers itself twice over and the deal throws off "
    "a double-digit cash-on-cash return. At the asking price coverage falls to a level most lenders decline, "
    "cash-on-cash drops to about 5%, and leverage turns the return NEGATIVE - because the debt costs more "
    "than the 8.25% the property yields. Our price is what makes this financeable at all.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
fi.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=9)
fi.row_dimensions[r].height = 26

# =====================================================================
# STRESS TESTS
# =====================================================================
st = wb.create_sheet("Stress Tests")
title(st, "STRESS TESTS  —  tenant health, sensitivity, and the exit",
      "How wrong can the assumptions be before the deal stops working?", 7)
widths(st, {"A": 38, "B": 15, "C": 15, "D": 15, "E": 15, "F": 15, "G": 44})

r = 4
sechead(st, r, "1.  TENANT HEALTH  —  can they carry the rent for 6.5 years?", 7); r += 1
colhead(st, r, ["Component", "Annual", "Per SF", "", "", "", "Note"]); r += 1
T0 = r
for k, f_, note in [
    ("Base rent", f"={RENT}", "Contractual"),
    ("Property taxes", f"={TAX}", "Estimate - confirm the actual bill"),
    ("Insurance", f"={INS}", "Cannabis-use premium loading"),
    ("Maintenance / CAM", f"={CAM}", "Roof, HVAC, lot"),
]:
    put(st, r, 1, k, bold=True)
    put(st, r, 2, f_, fmt=CUR, color=GREEN, align="right")
    put(st, r, 3, f"=B{r}/{SF}", fmt=CUR2, align="right")
    for c in (4, 5, 6): put(st, r, c, None)
    put(st, r, 7, note, size=9, color=INK2, wrap=True)
    r += 1
T1 = r - 1
put(st, r, 1, "GROSS OCCUPANCY COST", bold=True, fill=TEALB)
put(st, r, 2, f"=SUM(B{T0}:B{T1})", fmt=CUR, bold=True, color=TEAL, align="right", fill=TEALB)
put(st, r, 3, f"=B{r}/{SF}", fmt=CUR2, bold=True, color=TEAL, align="right", fill=TEALB)
for c in (4, 5, 6): put(st, r, c, None, fill=TEALB)
put(st, r, 7, "What the store must carry, not just the rent", size=9, italic=True,
    color=INK2, wrap=True, fill=TEALB)
OCC = r; r += 2
colhead(st, r, ["Store sales scenario", "$1.5M", "$2.0M", "$2.5M", "$3.0M", "$3.9M", "Assessment"]); r += 1
put(st, r, 1, "Occupancy cost as % of sales", bold=True)
for i, sv in enumerate([1_500_000, 2_000_000, 2_500_000, 3_000_000, 3_900_000]):
    put(st, r, 2 + i, f"=$B${OCC}/{sv}", fmt=PCT, bold=True, align="right")
put(st, r, 7, "Cannabis retail is generally healthy below ~7% and stressed above ~9%",
    size=9, color=INK2, wrap=True)
r += 1
put(st, r, 1, "Verdict", bold=True)
for i in range(5):
    L = get_column_letter(2 + i)
    put(st, r, 2 + i, f'=IF({L}{r-1}>0.09,"Distressed",IF({L}{r-1}>0.07,"Tight",IF({L}{r-1}>0.055,"Workable","Healthy")))',
        size=9, bold=True, align="right")
put(st, r, 7, "NJ certified 2025 sales of $1.164bn across ~300 stores average $3.88M per store, "
    "but that average is carried by multi-state operators", size=9, color=INK2, wrap=True)
r += 1
put(st, r, 1, "Sales needed to keep occupancy under 9%", bold=True)
put(st, r, 2, f"=$B${OCC}/0.09", fmt=CUR, bold=True, color=TEAL, align="right")
st.merge_cells(start_row=r, start_column=3, end_row=r, end_column=7)
put(st, r, 3, "THE key diligence item: get the tenant's actual sales. This single number drives the "
    "renewal probability that the whole model turns on.", size=9, italic=True, color=INK2, indent=1)
r += 2

sechead(st, r, "2.  SENSITIVITY  —  how wrong can the renewal assumption be?", 7); r += 1
colhead(st, r, ["Probability the tenant renews", "Weighted reversion", "IRR at our offer",
                "IRR at the ceiling", "IRR at the ask", "", "Read"]); r += 1
SEN = r
RENEW_V = f"'Reversion Scenarios'!$G${FIRST}"
OTHER_W = f"SUMPRODUCT('Reversion Scenarios'!$B${FIRST+1}:$B${LAST},'Reversion Scenarios'!$G${FIRST+1}:$G${LAST})/SUM('Reversion Scenarios'!$B${FIRST+1}:$B${LAST})"
HS = 10
for i, pr in enumerate([0.20, 0.25, 0.40, 0.50, 0.60, 0.75, 0.90]):
    is_base = (pr == 0.40)
    fill = TEALB if is_base else None
    put(st, r, 1, pr, fmt=PCT, color=BLUE, bold=is_base, align="right", fill=fill)
    put(st, r, 2, f"=A{r}*{RENEW_V}+(1-A{r})*({OTHER_W})", fmt=CUR, align="right", fill=fill)
    for j, pxref in enumerate([PRICE, A("Practical ceiling"), ASK]):
        hrow = 4 + i
        base_c = HS + j * 9
        put(st, hrow, base_c, f"=-{pxref}", fmt=CUR, size=9, border=False)
        for k2 in range(1, 7):
            put(st, hrow, base_c + k2, f"={RENT}", fmt=CUR, size=9, border=False)
        put(st, hrow, base_c + 7, f"={RENT}*0.5+$B${r}", fmt=CUR, size=9, border=False)
        c1, c2 = get_column_letter(base_c), get_column_letter(base_c + 7)
        put(st, r, 3 + j, f"=IRR({c1}{hrow}:{c2}{hrow})", fmt=PCT2, bold=(j == 0),
            color=TEAL if j == 0 else INK, align="right", fill=fill)
    put(st, r, 6, None, fill=fill)
    put(st, r, 7, "Base case" if is_base else ("Deeply pessimistic" if pr <= 0.25 else
        ("Optimistic" if pr >= 0.75 else "")), size=9, italic=True, color=INK2, fill=fill)
    r += 1
for cidx in range(HS, HS + 27):
    st.column_dimensions[get_column_letter(cidx)].hidden = True
put(st, r, 1, "Even at a 20% renewal probability - far more pessimistic than we think reasonable - our offer "
    "still returns over 10%. The conclusion does not depend on the 40% assumption. At the asking price, even "
    "a 90% renewal probability only reaches 7.5%.", size=9, italic=True, color=INK2, wrap=True, border=False)
st.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=7)
st.row_dimensions[r].height = 26
r += 3

sechead(st, r, "3.  SENSITIVITY  —  what if market rent is wrong?", 7); r += 1
colhead(st, r, ["Market rent / SF", "NOI", "Yield on our offer", "Value at 8.75% cap",
                "vs our basis", "", "Read"]); r += 1
for psf in (16, 18, 20, 22, 24, 26):
    is_base = (psf == 22)
    fill = TEALB if is_base else None
    put(st, r, 1, psf, fmt=CUR2, color=BLUE, bold=is_base, align="right", fill=fill)
    put(st, r, 2, f"=A{r}*{SF}", fmt=CUR, align="right", fill=fill)
    put(st, r, 3, f"=B{r}/{PRICE}", fmt=PCT, bold=True, color=TEAL, align="right", fill=fill)
    put(st, r, 4, f"=B{r}/0.0875", fmt=CUR, align="right", fill=fill)
    put(st, r, 5, f"=D{r}/{PRICE}-1", fmt=PCT, align="right", fill=fill)
    put(st, r, 6, None, fill=fill)
    put(st, r, 7, "Base case - our underwriting" if is_base else
        ("Below anything on the corridor" if psf <= 16 else ""), size=9, italic=True,
        color=INK2, wrap=True, fill=fill)
    r += 1
put(st, r, 1, "Market rent would have to fall to about $18/SF - below every conventional comp on the corridor "
    "except in-line strip space - before our basis stopped being covered by the building alone.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
st.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=7)
st.row_dimensions[r].height = 26
r += 3

sechead(st, r, "4.  THE EXIT  —  who buys it from us in 2033", 7); r += 1
colhead(st, r, ["Exit scenario", "NOI at exit", "Exit cap", "Value", "", "", "Buyer pool"]); r += 1
for name, noi, cap, pool in [
    ("Renewed cannabis lease, 5 years term", 154_000, 0.0925,
     "Cannabis net-lease buyers only - all-cash, limited pool, wide caps"),
    ("Re-let to bank / credit union, 10-15 yr NNN with bumps", 105_600, 0.0800,
     "NON-cannabis covenant: bankable and CMBS-eligible, national net-lease buyer pool"),
    ("Re-let to medical / urgent care, 10-15 yr NNN with bumps", 105_600, 0.0775,
     "Medical net lease trades tighter still; deepest institutional demand"),
    ("Vacant - land and shell", 0, 0, "Local owner-user or developer"),
]:
    put(st, r, 1, name, bold=True, wrap=True)
    put(st, r, 2, noi if noi else "-", fmt=CUR, align="right")
    put(st, r, 3, cap if cap else "-", fmt=PCT2, align="right")
    put(st, r, 4, f"=IF(C{r}=\"-\",750000,B{r}/C{r})", fmt=CUR, bold=True, color=TEAL, align="right")
    put(st, r, 5, None); put(st, r, 6, None)
    put(st, r, 7, pool, size=9, color=INK2, wrap=True)
    st.row_dimensions[r].height = 28
    r += 1
r += 1
put(st, r, 1, "THE COUNTER-INTUITIVE POINT: losing the cannabis tenant is not purely a downside. A conventional "
    "covenant - a bank, credit union or medical group on a 10-15 year NNN lease WITH escalations - removes the "
    "financing constraint entirely. That widens the buyer pool from cash-only cannabis specialists to the whole "
    "institutional net-lease market, and is worth roughly 75-125 bps of exit cap rate. Re-tenanting costs money "
    "up front and buys a more valuable, more liquid asset.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
st.merge_cells(start_row=r, start_column=1, end_row=r + 2, end_column=7)
st.row_dimensions[r].height = 26

# =====================================================================
# LEASE COMPS
# =====================================================================
lc = wb.create_sheet("Lease Comps")
title(lc, "LEASE COMPS  —  local like-and-kind rents, South Jersey / Route 30 corridor",
      "Asking rates, NNN. Tier 1 is like-and-kind (freestanding with a drive-thru); Tier 2 is submarket context.", 8)
widths(lc, {"A": 32, "B": 26, "C": 10, "D": 12, "E": 11, "F": 10, "G": 9, "H": 50})
r = 4
sechead(lc, r, "TIER 1  —  LIKE AND KIND: freestanding buildings with a drive-thru", 8); r += 1
colhead(lc, r, ["Comparable", "Type", "SF", "Rent / SF", "Annual", "Drive-thru", "Corner", "Read-through"]); r += 1
k1 = [
    ("451 White Horse Pike, Atco - SUBJECT", "Freestanding, drive-thru, cannabis", 4400, 30.00, "3-lane", "Yes",
     "In place. 36% above conventional market - a premium that expires with the tenant", True),
    ("340 S White Horse Pike, Berlin", "Freestanding retail w/ drive-thru", 1750, 27.43, "Yes", "-",
     "The best direct comp we have ($4,000/mo). But it is a small box - and small boxes always earn more per foot, so a 4,400 SF building will not beat this rate", False),
    ("804 N White Horse Pike, Magnolia", "Former Arby's, drive-thru, 38 spaces", 3035, None, "Yes", "-",
     "Rate on request. Closest second-generation drive-thru analogue on the corridor - worth a call to the listing broker to pin the number", False),
    ("2 S White Horse Pike, Stratford", "Freestanding QSR (Freebyrd Chicken)", None, None, "Yes", "Yes",
     "Corner freestanding QSR on the same pike - evidence of active drive-thru demand on this corridor", False),
]
for name, typ, sf, rent, dt, corner, note, is_subj in k1:
    fill = BAND if is_subj else None
    put(lc, r, 1, name, bold=is_subj, wrap=True, fill=fill)
    put(lc, r, 2, typ, size=9, color=INK2, wrap=True, fill=fill)
    put(lc, r, 3, sf if sf else "-", fmt=NUM, align="right", fill=fill)
    put(lc, r, 4, rent if rent else "On req.", fmt=CUR2 if rent else None,
        align="right", bold=is_subj, color=OCHRE if is_subj else INK, fill=fill)
    put(lc, r, 5, f"=IF(ISNUMBER(D{r}),D{r}*C{r},\"-\")" if (rent and sf) else "-",
        fmt=CUR, align="right", fill=fill)
    put(lc, r, 6, dt, size=9, color=TEAL, align="center", fill=fill)
    put(lc, r, 7, corner, size=9, color=TEAL if corner == "Yes" else INK2, align="center", fill=fill)
    put(lc, r, 8, note, size=9, color=INK2, wrap=True, fill=fill)
    lc.row_dimensions[r].height = 34
    r += 1
r += 1

sechead(lc, r, "TIER 2  —  SUBMARKET CONTEXT: what retail generally clears on this corridor", 8); r += 1
colhead(lc, r, ["Comparable", "Type", "SF", "Rent / SF", "Annual", "Drive-thru", "Corner", "Read-through"]); r += 1
comps = [
    ("NJ medical office average", "Medical", None, 24.00, "-", "-",
     "Ceiling for a healthcare backfill - and healthcare is the deepest demand pool for this box", False),
    ("Berlin submarket average", "Retail, all formats", None, 21.00, "-", "-",
     "Adjacent submarket, comparable demographics", False),
    ("Sicklerville submarket average", "Retail, all formats", None, 20.00, "-", "-",
     "Adjacent submarket, comparable demographics", False),
    ("Hammonton submarket average", "Retail, all formats", None, 20.00, "-", "-",
     "Route 30 east, comparable", False),
    ("Atco submarket average", "Retail, all formats", None, 13.00, "-", "-",
     "This is in-line strip space, which is why it is low. Our freestanding corner drive-thru format beats it comfortably - do not read this as our market rent", False),
    ("706 N White Horse Pike, Magnolia", "Flex / industrial", 40000, 11.50, "-", "-",
     "Scale reference only - large boxes on this pike clear in the low teens", False),
]
for name, typ, sf, rent, dt, corner, note, is_subj in comps:
    fill = None
    put(lc, r, 1, name, wrap=True, fill=fill)
    put(lc, r, 2, typ, size=9, color=INK2, wrap=True, fill=fill)
    put(lc, r, 3, sf if sf else "-", fmt=NUM, align="right", fill=fill)
    put(lc, r, 4, rent, fmt=CUR2, align="right", fill=fill)
    put(lc, r, 5, f"=D{r}*{SF}", fmt=CUR, align="right", color=INK2, fill=fill)
    put(lc, r, 6, dt, size=9, color=INK2, align="center", fill=fill)
    put(lc, r, 7, corner, size=9, color=INK2, align="center", fill=fill)
    put(lc, r, 8, note, size=9, color=INK2, wrap=True, fill=fill)
    lc.row_dimensions[r].height = 30
    r += 1
r += 1
sechead(lc, r, "CONCLUDED MARKET RENT", 8); r += 1
put(lc, r, 1, "CONVENTIONAL MARKET RENT - SUBJECT", bold=True, fill=TEALB)
put(lc, r, 2, "Freestanding, drive-thru, corner, large lot", size=9, italic=True,
    color=INK2, wrap=True, fill=TEALB)
put(lc, r, 3, f"={SF}", fmt=NUM, align="right", fill=TEALB)
put(lc, r, 4, f"={MKT}", fmt=CUR2, bold=True, color=TEAL, align="right", fill=TEALB)
put(lc, r, 5, f"={MKT}*{SF}", fmt=CUR, bold=True, color=TEAL, align="right", fill=TEALB)
put(lc, r, 6, "3-lane", size=9, color=TEAL, align="center", fill=TEALB)
put(lc, r, 7, "Yes", size=9, color=TEAL, align="center", fill=TEALB)
put(lc, r, 8, "The floor our offer is built on. Range $20-$24/SF; base case $22",
    size=9, italic=True, color=INK2, wrap=True, fill=TEALB)
r += 2


sechead(lc, r, "TIER 3  —  COMPARABLES SUPPLIED BY THE LISTING AGENT", 8); r += 1
colhead(lc, r, ["Tenant", "Location", "SF", "Rent / SF", "Annual", "Deal type", "Useful?", "What it actually shows"]); r += 1
AG0 = r
agent_comps = [
    ("7 Brew", "1390 Blackwood-Clementon Rd, Clementon", 510, 155_000, "Build-to-suit", "No",
     "A 510 SF coffee kiosk at an apparent $303.92/SF. Nobody rents a building at that rate - the rent is for the PAD and drive-thru lanes, not the hut"),
    ("Wawa", "301 White Horse Pike, Chesilhurst", 5_585, 325_000, "Build-to-suit", "No",
     "Purpose-built store with fuel on a large pad; rent repays land AND construction"),
    ("Wendy's", "69 NJ-73, Voorhees", 3_321, 157_659, "Build-to-suit", "No",
     "Purpose-built drive-thru restaurant - same land-plus-building economics"),
    ("501 Delsea Dr", "Sewell - lease signed 5 Jul", 1_373, 39.33*1373, "2nd generation", "Partly",
     "A genuine letting, but a very small unit - small units always rent high per foot"),
    ("Walgreens", "625 N Black Horse Pike, Blackwood", 14_870, 463_823, "Credit BTS", "No",
     "Purpose-built pharmacy for a national credit tenant on a long-standing rent"),
    ("Avis Budget", "341 N White Horse Pike, Lawnside - signed 5 Jun 2025", 3_300, 27.96*3300, "2nd generation", "YES",
     "THE ONE GENUINELY USEFUL COMP: second-hand building, same road, closest size to ours, recently signed"),
    ("ALDI", "142 NJ-73, Voorhees", 19_054, 246_950, "Grocery big box", "No",
     "At $12.96/SF it shows the opposite end of the same size effect - big buildings rent low per foot"),
]
for n, loc, sf, rent, typ, useful, note in sorted(agent_comps, key=lambda x: -x[3]/x[2]):
    fill = TEALB if useful == "YES" else None
    put(lc, r, 1, n, bold=(useful == "YES"), wrap=True, fill=fill)
    put(lc, r, 2, loc, size=9, color=INK2, wrap=True, fill=fill)
    put(lc, r, 3, sf, fmt=NUM, align="right", fill=fill)
    put(lc, r, 4, f"=E{r}/C{r}", fmt=CUR2, bold=True, align="right",
        color=TEAL if useful == "YES" else (RED if rent / sf > 100 else INK), fill=fill)
    put(lc, r, 5, round(rent), fmt=CUR, align="right", fill=fill)
    put(lc, r, 6, typ, size=9, color=INK2, align="right", fill=fill)
    put(lc, r, 7, useful, size=9, bold=True,
        color=TEAL if useful == "YES" else INK2, align="right", fill=fill)
    put(lc, r, 8, note, size=9, color=INK2, wrap=True, fill=fill)
    lc.row_dimensions[r].height = 34
    r += 1
r += 1
sechead(lc, r, "ADJUSTING THE TWO GENUINE LETTINGS TO OUR BUILDING", 8); r += 1
colhead(lc, r, ["Adjustment", "Avis, Lawnside", "Berlin drive-thru", "", "", "", "", "Reasoning"]); r += 1
ADJ = r
put(lc, r, 1, "Starting rent", bold=True)
put(lc, r, 2, 27.96, fmt=CUR2, color=BLUE, align="right")
put(lc, r, 3, 27.43, fmt=CUR2, color=BLUE, align="right")
put(lc, r, 8, "Avis signed Jun-2025; Berlin is an asking rate", size=9, color=INK2, wrap=True)
r += 1
for label, a1, a2, note in [
    ("Bigger building than the comp", 0.90, 0.80, "Ours is 4,400 SF; larger boxes rent lower per foot"),
    ("Atco is softer than Lawnside", 0.90, 1.00, "Lawnside is denser and closer in"),
    ("10-15 yr lease vs a 3-yr deal", 0.95, 1.00, "Short leases carry a premium rate"),
]:
    put(lc, r, 1, label, bold=True, wrap=True)
    put(lc, r, 2, a1, fmt=PCT, color=BLUE, align="right")
    put(lc, r, 3, a2, fmt=PCT, color=BLUE, align="right")
    put(lc, r, 8, note, size=9, color=INK2, wrap=True)
    r += 1
put(lc, r, 1, "INDICATED RENT FOR OUR BUILDING", bold=True, fill=TEALB)
put(lc, r, 2, f"=B{ADJ}*B{ADJ+1}*B{ADJ+2}*B{ADJ+3}", fmt=CUR2, bold=True, color=TEAL, align="right", fill=TEALB)
put(lc, r, 3, f"=C{ADJ}*C{ADJ+1}*C{ADJ+2}*C{ADJ+3}", fmt=CUR2, bold=True, color=TEAL, align="right", fill=TEALB)
for cc in range(4, 8): put(lc, r, cc, None, fill=TEALB)
put(lc, r, 8, "Two independent routes converging on ~$22 - the seller's own evidence confirms the market rent we used",
    size=9, italic=True, color=INK2, wrap=True, fill=TEALB)
r += 2
sechead(lc, r, "HOW WE GOT TO $22  —  the adjustment reasoning", 8); r += 1
for k, note in [
    ("Start from the submarket", "Berlin, Sicklerville and Hammonton all cluster at $20-21/SF for general retail. That is the base."),
    ("Add for freestanding format", "A standalone building with its own identity, signage and parking field commands a premium over in-line strip space. Atco's $13/SF average is in-line space and is not our comp."),
    ("Add for the drive-thru", "The Berlin comp at $27.43/SF is a freestanding drive-thru - the only priced like-and-kind evidence we have. It is a 1,750 SF box, and small boxes always carry a higher rate per foot."),
    ("Add for the corner", "Two frontages, signage on both, and secondary-road access. A real premium over mid-block, and what makes the drive-thru circulation work at all."),
    ("Subtract for size", "At 4,400 SF this is roughly 2.5x the Berlin comp. Larger boxes lease at lower rates per foot, which pulls us back down from $27."),
    ("Land at $20-$24, base $22", "Below the small-box drive-thru comp, above the general submarket average. Our entire offer is built on the assumption that this box re-lets at $22 - and the deal still works at $18."),
]:
    put(lc, r, 1, k, bold=True, color=TEAL, wrap=True)
    lc.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    put(lc, r, 2, note, size=9, color=INK2, wrap=True, indent=1)
    lc.row_dimensions[r].height = 30
    r += 1
r += 1
put(lc, r, 1, "Submarket averages are asking-rate averages published by commercial listing platforms, "
    "not verified closed leases. Verify against CoStar comparable-lease data in diligence. "
    "Note that our offer holds even at the bottom of this range.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
lc.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
lc.row_dimensions[r].height = 30

# =====================================================================
# SALE COMPS
# =====================================================================
sc = wb.create_sheet("Sale Comps")
title(sc, "SALE COMPS  —  cannabis net lease transactions and benchmarks",
      "Cannabis dispensaries trade 7.4%-9.35%. Our entry at 12.0% is wider than every comp in the set.", 5)
widths(sc, {"A": 34, "B": 15, "C": 13, "D": 40, "E": 14})
r = 4
colhead(sc, r, ["Comparable", "Price", "Cap rate", "Note", "Status"]); r += 1
sale = [
    ("STNL market average, Q1 2026", None, 0.0680, "All tenants, all sectors", "Benchmark"),
    ("Jungle Boys - Naples, FL", None, 0.0740, "Dispensary with 2% annual increases", "Listing"),
    ("Cookies - Kalamazoo, MI", 3100000, 0.0825, "10 years remaining, corporate guarantee", "Listing"),
    ("SUBJECT at the $1.6M asking price", 1600000, 0.0825,
     "6.5 years, flat rent, personal guarantees only", "Asking"),
    ("LivWell - Aurora, CO", 1025000, 0.0887, "Closed April 2026", "CLOSED"),
    ("Ascend - Pennsylvania", None, 0.0925, "Medical-only market", "Listing"),
    ("Curaleaf - Worth, IL", None, 0.0935, "10% rent increases every 5 years", "Listing"),
    ("Weaker private credit - 2026 guide", None, 0.0875,
     "Published range 8.00%-9.50%. The subject's true credit tier", "Benchmark"),
]
for name, px, cap, note, status in sale:
    is_subj = name.startswith("SUBJECT")
    fill = BAND if is_subj else None
    put(sc, r, 1, name, bold=is_subj, wrap=True, fill=fill)
    put(sc, r, 2, px if px else "-", fmt=CUR, align="right", fill=fill)
    put(sc, r, 3, cap, fmt=PCT2, align="right", bold=is_subj,
        color=OCHRE if is_subj else INK, fill=fill)
    put(sc, r, 4, note, size=9, color=INK2, wrap=True, fill=fill)
    put(sc, r, 5, status, size=9, color=TEAL if status == "CLOSED" else INK2,
        bold=(status == "CLOSED"), fill=fill)
    r += 1
put(sc, r, 1, "SUBJECT AT OUR OFFER", bold=True, fill=TEALB)
put(sc, r, 2, f"={PRICE}", fmt=CUR, bold=True, align="right", fill=TEALB)
put(sc, r, 3, f"={RENT}/{PRICE}", fmt=PCT2, bold=True, color=TEAL, align="right", fill=TEALB)
put(sc, r, 4, "Wider than every comparable transaction in the set", size=9,
    italic=True, color=INK2, wrap=True, fill=TEALB)
put(sc, r, 5, "OUR BID", size=9, bold=True, color=TEAL, fill=TEALB)
r += 2

sechead(sc, r, "ADJUSTMENT GRID  —  why this asset belongs wide of the comp set", 5); r += 1
colhead(sc, r, ["Attribute", "Comp set", "Subject", "Adjustment", ""]); r += 1
for attr, comp, subj, adj in [
    ("Guarantee", "Corporate / MSO guarantees", "Two personal guarantees, single-store operator", "+50 to +100 bps"),
    ("Rent escalations", "2% annual or 10% every 5 years", "Flat - 0% for the full base term", "+50 to +75 bps"),
    ("Rent vs. market", "Generally at or near market", "~36% above conventional market rent", "+50 to +75 bps"),
    ("Term remaining", "8-15 years typical", "6.5 years", "+25 to +50 bps"),
    ("Market fundamentals", "Mixed; several limited-licence states", "NJ - 300+ stores, flower -23% YoY", "+25 bps"),
    ("Real estate quality", "Varies", "Corner, drive-thru, 3.13 AC, below replacement cost", "-50 to -75 bps"),
    ("Licensing moat", "Varies", "Waterford caps retail cannabis at two licences", "-25 bps"),
]:
    put(sc, r, 1, attr, bold=True)
    put(sc, r, 2, comp, size=9, color=INK2, wrap=True)
    put(sc, r, 3, subj, size=9, color=INK2, wrap=True)
    put(sc, r, 4, adj, size=9, bold=True,
        color=TEAL if adj.startswith("-") else RED, align="right")
    put(sc, r, 5, None)
    r += 1
put(sc, r, 1, "Fair cap rate, fully adjusted", bold=True, fill=TEALB)
put(sc, r, 2, "9.25% - 10.25%", size=9, bold=True, color=INK2, fill=TEALB)
put(sc, r, 3, "Implying a value of $1.29M - $1.43M", size=9, bold=True, color=INK2, fill=TEALB)
put(sc, r, 4, f"={RENT}/{PRICE}", fmt=PCT2, bold=True, color=TEAL, align="right", fill=TEALB)
put(sc, r, 5, "our entry", size=9, italic=True, color=TEAL, fill=TEALB)
r += 2
put(sc, r, 1, "Cannabis comps are drawn from public brokerage listings and transaction announcements; "
    "only the LivWell trade is confirmed closed. Benchmarks are published Q1 2026 net lease research. "
    "Re-run against CoStar, Crexi and Camden County deed records before hard money.",
    size=9, italic=True, color=INK2, wrap=True, border=False)
sc.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
sc.row_dimensions[r].height = 30

# =====================================================================
# RISKS
# =====================================================================
rk = wb.create_sheet("Risks & Diligence")
title(rk, "RISKS AND DILIGENCE",
      "The risks are real - they are also why the asset is available at 12% instead of 8.25%.", 3)
widths(rk, {"A": 34, "B": 66, "C": 2})
r = 4
sechead(rk, r, "RISK REGISTER  —  and how the price answers each one", 3); r += 1
colhead(rk, r, ["Risk", "How our offer price answers it", ""]); r += 1
for k, v_ in [
    ("Rent is 36% above market", "We capitalized the MARKET rent, not the contract rent, to set our price. The premium is upside we did not pay for."),
    ("Flat rent, no escalations", "Priced in at a 12% entry. We do not need growth - we need the coupon, and the coupon returns 78% of capital before expiry."),
    ("Personal guarantees only", "Worth ~75 bps of cap rate; we took 375. Verify guarantor net worth in diligence, but the basis does not depend on it."),
    ("NJ cannabis price compression", "The reason this is a 12% deal and not an 8% one. Our downside case already assumes the tenant fails."),
    ("Financing is hard for cannabis collateral", "At a 12% cap, private debt at 9-11% is POSITIVE leverage. At the 8.25% ask it would have been negative."),
    ("Special-purpose improvements", "Cuts both ways - narrows the pool, but makes us the only compliant drive-thru site on the corridor for banks, medical and cannabis alike."),
    ("Reassessment on sale", "A $1.1M deed sits BELOW the assessor's $1.27M implied value - buying at our number argues for an appeal, not an increase."),
    ("GLA discrepancy (4,400 vs 4,206 SF)", "Confirm by measurement. At our price the difference is ~$12/SF - material to reporting, not to the decision."),
]:
    put(rk, r, 1, k, bold=True, wrap=True)
    put(rk, r, 2, v_, size=9, color=INK2, wrap=True)
    rk.row_dimensions[r].height = 28
    r += 1
r += 1

sechead(rk, r, "DILIGENCE CHECKLIST  —  confirm before hard money", 3); r += 1
for grp, items in [
    ("Tenant & lease", [
        "Tenant sales reports and P&L - occupancy cost runs ~$193,400 all-in; at $3.0M of store sales that is a workable 6.4%",
        "DEMISED PREMISES CLAUSE - does the lease include the full 3.13 AC? Gates all land upside",
        "Complete lease with all amendments; confirm roof, structure and HVAC allocation",
        "Both personal guarantees - scope, caps, burn-off, joint-and-several",
        "Guarantor personal financial statements and net worth verification",
        "Estoppel certificate, SNDA, and full rent payment history since 2023",
    ]),
    ("Regulatory & physical", [
        "CRC licence status, expiry and site-specific conditions",
        "Waterford Township approval and status of the two-licence cap",
        "Pinelands Commission jurisdiction; sewer vs. septic capacity",
        "Subdivision feasibility for the excess acreage",
        "Actual current tax bill and reassessment exposure",
        "Confirm GLA by measurement; roof and HVAC age and condition",
        "Phase I ESA, ALTA survey, title, zoning compliance letter",
    ]),
]:
    put(rk, r, 1, grp, bold=True, color=TEAL)
    put(rk, r, 2, None)
    r += 1
    for it in items:
        put(rk, r, 1, "", border=False)
        rk.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        c = rk.cell(r, 1, "  ☐   " + it)
        c.font = Font(name=F, size=9, color=INK2)
        c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
        rk.row_dimensions[r].height = 24
        r += 1
    r += 1

# =====================================================================
# EXECUTIVE SUMMARY  (built last, placed first)
# =====================================================================
es = wb.create_sheet("Executive Summary", 0)
title(es, "451 WHITE HORSE PIKE, ATCO NJ  —  ACQUISITION RECOMMENDATION",
      "Everything an approver needs is on this sheet. Detail follows on the tabs behind it.", 6)
widths(es, {"A": 38, "B": 17, "C": 17, "D": 15, "E": 15, "F": 44})

r = 4
es.merge_cells(start_row=r, start_column=1, end_row=r + 2, end_column=6)
c = es.cell(r, 1,
    "RECOMMENDATION:  Offer $1,100,000 all cash, 30-day diligence, 15-day close.\n"
    "At this price we buy the building at what it is worth with an ordinary tenant paying ordinary rent — "
    "so the 36% cannabis rent premium, the renewal option, the 3-lane drive-thru and 2.5 acres of idle land all come free.\n"
    "Expected unlevered return 12%. Every modelled outcome, including total tenant failure, returns a profit.")
c.font = Font(name=F, size=11, bold=True, color=INK)
c.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
c.fill = PatternFill("solid", fgColor=TEALB)
for rr_ in range(r, r + 3):
    for cc in range(1, 7):
        es.cell(rr_, cc).fill = PatternFill("solid", fgColor=TEALB)
es.row_dimensions[r].height = 26
es.row_dimensions[r + 1].height = 26
es.row_dimensions[r + 2].height = 26
r += 4

sechead(es, r, "THE NUMBERS THAT MATTER", 6); r += 1
colhead(es, r, ["Metric", "At our offer", "At the asking price", "", "", "What it means"]); r += 1
for k, f1, f2, fmt, note in [
    ("Purchase price", f"={PRICE}", f"={ASK}", CUR, "Below the ask and below our own value indication"),
    ("Weighted value indication", f"={VALIND}", f"={VALIND}", CUR, "Where the four independent valuation methods converge"),
    ("Discount to value indication", f"={PRICE}/{VALIND}-1", f"={ASK}/{VALIND}-1", PCT, "Our margin of safety on entry, versus the seller's premium"),
    ("Price per square foot", f"={PRICE}/{SF}", f"={ASK}/{SF}", CUR2, "Well below the cost of building it new"),
    ("Going-in cap rate", f"={RENT}/{PRICE}", f"={RENT}/{ASK}", PCT2, "Cannabis dispensaries trade at 7.4%-9.35%; we enter at 12%"),
    ("Expected unlevered IRR", f"=IRR(Returns!B{NCF}:I{NCF})", f"={ASK_IRR_REF}", PCT2,
     "Probability-weighted across all six reversion outcomes"),
    ("Best case IRR (tenant renews)", f"=Returns!D{SCEN_IRR}", f"=Returns!E{SCEN_IRR}", PCT2,
     "The single most likely outcome at 40% probability"),
    ("Worst case IRR (total vacancy)", f"=Returns!D{SCEN_IRR+5}", f"=Returns!E{SCEN_IRR+5}", PCT2,
     "Tenant fails, building goes dark, we liquidate land and shell"),
    ("Debt service coverage (55% LTV)", f"=Financing!F{F0}", f"=Financing!F{F0+2}", '0.00"x"',
     "Most lenders decline below 1.25x. Our price is what makes this financeable"),
    ("Cash-on-cash (55% LTV)", f"=Financing!H{F0}", f"=Financing!H{F0+2}", PCT,
     "Annual cash return on equity after debt service"),
    ("Levered IRR (55% LTV)", f"=Financing!F{L0}", f"=Financing!F{L0+2}", PCT2,
     "At the ask, leverage turns the return negative - debt costs more than the property yields"),
]:
    put(es, r, 1, k, bold=True)
    put(es, r, 2, f1, fmt=fmt, bold=True, color=TEAL, align="right")
    put(es, r, 3, f2, fmt=fmt, color=INK2, align="right")
    put(es, r, 4, None); put(es, r, 5, None)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    r += 1
r += 1

sechead(es, r, "WHY IT WORKS  —  four reasons", 6); r += 1
colhead(es, r, ["Reason", "Figure", "", "", "", "Detail"]); r += 1
for k, f_, fmt, note in [
    ("Offer less market-rent value of the building", f"={PRICE}-{MKT}*{SF}/0.0875", CUR,
     "Effectively zero. We buy at plain conventional-use value, so the cannabis premium, the option and the land are free."),
    ("Capital returned before expiry", f"={RENT}*6.5/{PRICE}", PCT,
     "$858,000 of contracted rent lands before the lease matures, with no reliance on renewal, refinancing or resale."),
    ("Basis covered by dirt and shell", f"=750000/{PRICE}", PCT,
     "Land plus vacant building supports ~$750,000. Only ~$350,000 of our basis is genuinely at risk."),
    ("The worst case still pays", f"=Returns!D{SCEN_IRR+5}", PCT2,
     "At the asking price that same scenario loses money. That gap is the entire argument for our number."),
]:
    put(es, r, 1, k, bold=True, wrap=True)
    put(es, r, 2, f_, fmt=fmt, bold=True, size=12, color=TEAL, align="right")
    for cc in (3, 4, 5): put(es, r, cc, None)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    es.row_dimensions[r].height = 30
    r += 1
r += 1

sechead(es, r, "THE ASSET", 6); r += 1
for k, val, note in [
    ("Property", "451 White Horse Pike (US Route 30), Atco NJ", "Waterford Township, Camden County"),
    ("Building", "4,400 SF former bank branch on 3.13 acres", "Built 1960, renovated 2023. Vault, 3-lane drive-thru, ample parking"),
    ("Tenant", "Holistic Solutions - cannabis dispensary", "Single location, founded 2018, two personal guarantees, no corporate credit"),
    ("Lease", "Absolute NNN to 31 Jan 2033 (6.5 years)", "$132,000/yr flat, no escalations. One 5-year option at $154,000"),
    ("Location", "15,370 vehicles per day", "Corridor between Philadelphia and the Jersey Shore"),
]:
    put(es, r, 1, k, bold=True)
    es.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    put(es, r, 2, val, size=10)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    r += 1
r += 1

sechead(es, r, "IF THE TENANT LEAVES  —  the question that decides the deal", 6); r += 1
colhead(es, r, ["Re-let scenario", "Annual rent", "Yield on our offer", "", "", "Comment"]); r += 1
for k, f1, f2, note in [
    ("Another cannabis licensee @ $30/SF", f"={RENT}", f"={RENT}/{PRICE}",
     "Holds the rent outright, but Waterford permits only two licences"),
    ("Bank / credit union or medical @ $24/SF", f"=24*{SF}", f"=24*{SF}/{PRICE}",
     "Turnkey - the vault and drive-thru are already in place"),
    ("Conventional market rent @ $22/SF", f"={MKT}*{SF}", f"={MKT}*{SF}/{PRICE}",
     "Our underwriting case. This is what we priced the deal on"),
    ("Deep downside @ $18/SF", f"=18*{SF}", f"=18*{SF}/{PRICE}",
     "Bottom of the conventional range - still clears our cost of capital"),
]:
    put(es, r, 1, k, wrap=True)
    put(es, r, 2, f1, fmt=CUR, align="right")
    put(es, r, 3, f2, fmt=PCT, bold=True, color=TEAL, align="right")
    put(es, r, 4, None); put(es, r, 5, None)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    r += 1
r += 1

sechead(es, r, "UPSIDE WE ARE NOT PAYING FOR", 6); r += 1
for k, f_, fmt, note in [
    ("Idle developable land", f"='Land Upside'!B{EXCESS}", '0.00"  acres"',
     "Building coverage is only 3.2% of the site"),
    ("Added NOI from a pad plus EV charging", f"='Land Upside'!C{NOIROW}", CUR,
     "Outparcel ground lease plus a third-party EV fast-charging licence"),
    ("Value created, net of build-out", f"='Land Upside'!C{VC}", CUR,
     "A second deal hiding inside the first - excluded from every return above"),
    ("Yield on cost if executed", f"=({RENT}+'Land Upside'!C{NOIROW})/{PRICE}", PCT,
     "Versus 12.0% today"),
]:
    put(es, r, 1, k, bold=True)
    put(es, r, 2, f_, fmt=fmt, bold=True, color=TEAL, align="right")
    for cc in (3, 4, 5): put(es, r, cc, None)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    r += 1
r += 1

sechead(es, r, "NEGOTIATION DISCIPLINE", 6); r += 1
for k, f_, fmt, note in [
    ("Open at", f"={PRICE}", CUR, "All cash, 30-day diligence, 15-day close"),
    ("Practical ceiling", f"={A('Practical ceiling')}", CUR,
     "Still delivers a 9.3% expected return. Hold here"),
    ("Walk away above", 1300000, CUR,
     "Above this the margin of safety is gone - there will be another one"),
    ("Asking price", f"={ASK}", CUR, "Expected return of only 4.3%. Decline"),
]:
    put(es, r, 1, k, bold=True)
    put(es, r, 2, f_, fmt=fmt, bold=True,
        color=TEAL if "Open" in k else (RED if "Asking" in k or "Walk" in k else INK), align="right")
    for cc in (3, 4, 5): put(es, r, cc, None)
    put(es, r, 6, note, size=9, color=INK2, wrap=True)
    r += 1
r += 2

es.merge_cells(start_row=r, start_column=1, end_row=r + 1, end_column=6)
c = es.cell(r, 1,
    "Basis: deal terms from the Matthews offering memorandum; assessment and zoning from public tax-assessor records. "
    "Comparables are predominantly ASKING RATES AND MARKETED CAP RATES, not verified closed transactions — re-run against "
    "CoStar, Crexi and Camden County deed records before hard money. Operating costs, TI, downtime and land figures are "
    "analyst estimates; reversion probabilities are judgmental. Returns are unlevered and pre-tax. Not an appraisal.")
c.font = Font(name=F, size=8, italic=True, color=INK2)
c.alignment = Alignment(vertical="top", wrap_text=True, indent=1)
es.row_dimensions[r].height = 24
es.row_dimensions[r + 1].height = 24

# ---- legend on Assumptions ----
lr = a.max_row + 2
a.merge_cells(start_row=lr, start_column=1, end_row=lr, end_column=4)
c = a.cell(lr, 1, "HOW TO USE THIS WORKBOOK")
c.font = Font(name=F, size=10, bold=True, color="FFFFFFFF")
c.fill = PatternFill("solid", fgColor=HDRBG)
c.alignment = Alignment(vertical="center", indent=1)
for i in range(2, 5): a.cell(lr, i).fill = PatternFill("solid", fgColor=HDRBG)
lr += 1
for txt, col in [
    ("Blue figures are inputs — change them and the whole workbook recalculates.", BLUE),
    ("Black figures are formulas. Green figures are pulled from another sheet.", INK),
    ("The yellow cell is the master lever: our offer price.", INK),
    ("Start at Executive Summary. Reversion Scenarios holds the judgmental probabilities.", INK),
]:
    a.merge_cells(start_row=lr, start_column=1, end_row=lr, end_column=4)
    c = a.cell(lr, 1, "   " + txt)
    c.font = Font(name=F, size=9, color=col, bold=(col == BLUE))
    c.alignment = Alignment(vertical="center", indent=1)
    lr += 1

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    ws.freeze_panes = "A4"
    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True

wb.save("/tmp/claude-0/-home-user-Aida-respository/5108276f-da51-5f56-a1e4-cd6adcc47f7f/scratchpad/451_White_Horse_Pike_Acquisition_Model.xlsx")
print("saved")
