"""
mblib — Model Builder library
Institutional-grade Excel underwriting formatting helpers (openpyxl).

Color / font discipline (shared by the BuildSpec and the Underwriting skill):
  BLUE on YELLOW      -> hardcoded input   (the only cells a user changes)
  BLACK on white      -> formula / calculation (incl. cross-tab refs)
  GREEN on light-grn  -> public-record VERIFIED fact (BCPA / Sunbiz / deed)
  GOLD on NAVY        -> section headers, total rows, banners, KPI boxes
  SLATE, white text   -> ownership group headers / column sub-headers
  Light-blue, teal    -> child rows in an ownership group
  DARK, gold text     -> grand-total rows, KPI value cells
  ORANGE, dark red    -> warnings / excluded-from notes / high holdout risk
"""
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, NamedStyle
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

# ------------------------------------------------------------------ palette
NAVY      = "1F2D4E"
DARK      = "111B2C"
SLATE     = "2D4159"
GOLD      = "C9A84C"
BLUE      = "0000FF"
YELLOW    = "FFF2CC"
GREEN_TX  = "2D5016"
GREEN_BG  = "E8F5E9"
TEAL      = "1F6F6B"
LTBLUE    = "F0F6FC"
DEBTBLUE  = "D9E8F5"
ORANGE_BG = "FDE8D8"
DKRED     = "9C1B1B"
GREY_HDR  = "D9D9D9"
GREY_BRD  = "BFBFBF"
WHITE     = "FFFFFF"
LTGREY    = "F5F5F5"

# ------------------------------------------------------------------ number formats
F_ACCT_TOP = '_($* #,##0_);_($* (#,##0);_($* "-"??_);_(@_)'   # $ shown (top/total rows)
F_ACCT     = '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'      # comma only (interior)
F_ACCT2_TOP= '_($* #,##0.00_);_($* (#,##0.00);_($* "-"??_);_(@_)'
F_PCT0     = '0%'
F_PCT1     = '0.0%'
F_PCT2     = '0.00%'
F_MULT     = '0.00"x"'
F_PSF      = '#,##0.00'
F_NUM      = '#,##0'
F_NUM2     = '#,##0.00'
F_YR       = '0'
F_DATE     = 'mm/dd/yyyy'

# ------------------------------------------------------------------ borders
_thin  = Side(style="thin",   color=GREY_BRD)
_med   = Side(style="medium", color=NAVY)
_hair  = Side(style="hair",   color=GREY_BRD)
B_ALL   = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)
B_BOX   = Border(left=_med, right=_med, top=_med, bottom=_med)
B_TOP   = Border(top=Side(style="thin", color="000000"))
B_TOPBOT= Border(top=Side(style="thin", color="000000"),
                 bottom=Side(style="double", color="000000"))
B_BOTTOM= Border(bottom=_thin)
B_NONE  = Border()

def _font(color="000000", bold=False, italic=False, size=8, name="Arial"):
    return Font(name=name, size=size, bold=bold, italic=italic, color=color)

def _fill(rgb):
    return PatternFill("solid", fgColor=rgb) if rgb else PatternFill()

# ------------------------------------------------------------------ style presets
# each returns (font, fill, align, number_format, border)
_WRAP   = Alignment(wrap_text=True, vertical="center")
_WRAPL  = Alignment(wrap_text=True, vertical="center", horizontal="left")
_WRAPR  = Alignment(wrap_text=True, vertical="center", horizontal="right")
_WRAPC  = Alignment(wrap_text=True, vertical="center", horizontal="center")


class Sheet:
    """Thin wrapper: write cells by (row, col), track named cells for cross-refs."""

    def __init__(self, ws, book):
        self.ws = ws
        self.book = book
        self.reg = {}          # name -> "B12"
        ws.sheet_view.showGridLines = False

    # ---- core writer ----------------------------------------------------
    def put(self, r, c, value=None, *, style="calc", fmt=None, bold=None,
            italic=None, size=None, color=None, fill=None, align=None,
            border="all", name=None, note=None, wrap=True, merge=None):
        cell = self.ws.cell(row=r, column=c)
        if value is not None:
            cell.value = value

        # ---- resolve style preset ----
        fcolor, fbg, fbold, fital, fsize = "000000", None, False, False, 8
        halign = None
        bord = B_ALL

        if style == "input":            # blue on yellow
            fcolor, fbg = BLUE, YELLOW
        elif style == "calc":           # black on white
            fcolor = "000000"
        elif style == "verified":       # green fact
            fcolor, fbg = GREEN_TX, GREEN_BG
        elif style == "banner":
            fcolor, fbg, fbold, fsize = GOLD, NAVY, True, 16; bord = B_BOX
        elif style == "banner_sub":
            fcolor, fbg, fsize = "FFFFFF", NAVY, 10; bord = B_BOX
        elif style == "header":         # section header gold/navy
            fcolor, fbg, fbold, fsize = GOLD, NAVY, True, 9; bord = B_BOX
        elif style == "subhead":        # slate white
            fcolor, fbg, fbold = "FFFFFF", SLATE, True
        elif style == "total":          # navy/gold total row
            fcolor, fbg, fbold = GOLD, NAVY, True
        elif style == "grand":          # dark/gold grand total
            fcolor, fbg, fbold, fsize = GOLD, DARK, True, 9
        elif style == "subtotal":       # black bold, top border
            fcolor, fbold = "000000", True; bord = Border(top=Side(style="thin", color="000000"),
                                                          left=_thin, right=_thin, bottom=_thin)
        elif style == "label":
            fcolor = "000000"
        elif style == "label_b":
            fcolor, fbold = "000000", True
        elif style == "group":          # ownership group header
            fcolor, fbg, fbold = "FFFFFF", SLATE, True
        elif style == "child":          # child row
            fcolor, fbg = TEAL, LTBLUE
        elif style == "kpi_val":
            fcolor, fbg, fbold, fsize = GOLD, DARK, True, 22; bord = B_BOX
        elif style == "kpi_lab":
            fcolor, fbg, fbold, fsize = GOLD, NAVY, True, 8; bord = B_BOX
        elif style == "kpi_note":
            fcolor, fbg, fsize = "FFFFFF", NAVY, 7; bord = B_BOX
        elif style == "warn":
            fcolor, fbg = DKRED, ORANGE_BG
        elif style == "debt":
            fcolor, fbg = TEAL, DEBTBLUE
        elif style == "note":
            fcolor, fital, fsize = "595959", True, 7
        elif style == "plain":
            fcolor = "000000"; bord = B_NONE

        # ---- explicit overrides ----
        if color is not None:  fcolor = color
        if bold  is not None:  fbold  = bold
        if italic is not None: fital  = italic
        if size  is not None:  fsize  = size
        if fill  is not None:  fbg    = fill

        cell.font = _font(color=fcolor, bold=fbold, italic=fital, size=fsize)
        cell.fill = _fill(fbg)
        if fmt:  cell.number_format = fmt
        # alignment
        if align == "left":   cell.alignment = Alignment(wrap_text=wrap, vertical="center", horizontal="left")
        elif align == "right":cell.alignment = Alignment(wrap_text=wrap, vertical="center", horizontal="right")
        elif align == "center":cell.alignment= Alignment(wrap_text=wrap, vertical="center", horizontal="center")
        else: cell.alignment = Alignment(wrap_text=wrap, vertical="center")

        # borders
        if border == "all":     cell.border = bord
        elif border == "none":  cell.border = B_NONE
        elif border == "top":   cell.border = B_TOP
        elif border == "topbot":cell.border = B_TOPBOT
        elif border == "box":   cell.border = B_BOX
        elif isinstance(border, Border): cell.border = border

        if note:
            cm = Comment(note, "DAWN RE"); cm.width = 260; cm.height = 120
            cell.comment = cm
        if name:
            self.reg[name] = f"{get_column_letter(c)}{r}"
        if merge:
            self.ws.merge_cells(start_row=r, start_column=c,
                                end_row=merge[0], end_column=merge[1])
        return cell

    # convenience -----------------------------------------------------------
    def ref(self, name):
        """Return the local A1 coord of a registered cell."""
        return self.reg[name]

    def section(self, r, c1, c2, text):
        """Full-width section header (gold on navy)."""
        self.put(r, c1, text, style="header", align="left")
        for c in range(c1 + 1, c2 + 1):
            self.put(r, c, style="header")
        self.ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
        self.ws.cell(row=r, column=c1).alignment = Alignment(horizontal="left", vertical="center")

    def fillrow(self, r, c1, c2, style="calc"):
        for c in range(c1, c2 + 1):
            self.put(r, c, style=style)

    def colw(self, widths):
        for col, w in widths.items():
            self.ws.column_dimensions[col].width = w

    def rowh(self, r, h):
        self.ws.row_dimensions[r].height = h

    def freeze(self, coord):
        self.ws.freeze_panes = coord


def new_book():
    from openpyxl import Workbook
    wb = Workbook()
    wb.remove(wb.active)
    wb.calculation.fullCalcOnLoad = True
    return wb


def add_sheet(wb, title, tabcolor=None):
    ws = wb.create_sheet(title=title)
    if tabcolor:
        ws.sheet_properties.tabColor = tabcolor
    return Sheet(ws, wb)
