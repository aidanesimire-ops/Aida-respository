"""
tab_hbu.py — HIGHEST & BEST USE.
Prices the deal three ways so nothing is missed:
  1. Each component priced INDEPENDENTLY, then COMBINED (sum → assemblage premium).
  2. The LAND as regular fragmented parcels vs. as an assembled superblock
     (plottage premium — worth more, but hard to put together).
  3. The office condo FULL BUY-OUT, and the Live Local redevelopment residual (HBU test).
"""
from openpyxl.utils import get_column_letter
from mblib import F_ACCT, F_ACCT_TOP, F_PCT1, F_PCT2, F_PSF, F_NUM

L = 2
def CL(c): return get_column_letter(c)

# component -> (label, price-cell, note)
COMPONENTS = [
    ("Shahidi Retail", "Shahidi Retail (Galleria Plaza)", "PRICE", "acquire fee · value-add retail"),
    ("Publix & Starbucks", "Publix + Starbucks", "PRICE", "sale-leaseback (acquire fee)"),
    ("Sunrise Plaza", "Sunrise Plaza (Kar Luen)", "PRICE", "acquire fee · restaurant value-add"),
    ("Office Condo", "Galleria Corp Centre (full buy-out)", "BUYOUT_TOTAL", "buy out BOTH condo owners"),
    ("Land", "1040 Bayview (entitled land)", "CONCLUDED", "covered land · hold for redevelopment"),
]
# acquisition history: (label, date, orig price, (sheet,our-price-cell) or None, verified, note)
ACQ_HISTORY = [
    ("Shahidi Retail — Shawnick Galleria LLC (Shahidi)", "11/09/2021", 17100000, ("Shahidi Retail", "PRICE"), True, "Special Warranty Deed (flagged disqualified sale)"),
    ("Publix + Starbucks — REAL SUB LLC (Publix)", "03/14/2025", 25000000, ("Publix & Starbucks", "PRICE"), True, "Trustee's Deed · $679/SF bldg"),
    ("Sunrise Plaza — Kar Luen Inc", "Oct 2000", 128000, ("Sunrise Plaza", "PRICE"), False, "stale/nominal — held since; no recent arm's-length"),
    ("Office — Grove Gate bulk (57.4%)", "09/23/2019", 10000000, ("Office Condo", "BUYOUT1"), False, "$103/SF from Intl Sunrise (dissolved 2020); now reselling units $270–381/SF"),
    ("Office — 42.6% individual owners", "2011→2026", None, None, False, "~40 small owners (Merrimac, Cosmo, Jorgensen, Hublot); un-itemizable without BCPA"),
    ("1040 Bayview — Sunrise & Bayview Partners", "2014 (JV)", None, ("Land", "CONCLUDED"), False, "Procacci; BBX exited 2022; stale 1961 deed $801,933"),
]
# land parcels -> (label, land-SF cell, $/SF cell or None, land-value cell)
LANDPARCELS = [
    ("Shahidi Retail", "Shahidi Retail", "LANDSF", "GLAND_PSF", "LANDVAL"),
    ("Publix & Starbucks", "Publix + Starbucks", "GLANDSF", "GLAND_PSF", "LANDVAL"),
    ("Sunrise Plaza", "Sunrise Plaza (Kar Luen)", "GLANDSF", "GLAND_PSF", "LANDVAL"),
    ("Land", "1040 Bayview", "LANDSF", None, "CONCLUDED"),
]


def build(s, regs):
    def x(sheet, name):
        return f"'{sheet}'!{regs[sheet][name]}"
    AS = lambda n: x("Assumptions", n)
    s.colw({"A": 2.5, "B": 40, "C": 15, "D": 14, "E": 14, "F": 14, "G": 12,
            "H": 12, "I": 12, "J": 12, "K": 12, "L": 12, "M": 12})
    r = 1
    s.put(r, L, "HIGHEST & BEST USE  —  INDIVIDUAL vs. ASSEMBLED", style="banner", align="left", merge=(r, 13)); s.rowh(r, 26); r += 1
    s.put(r, L, "Every component priced on its own, then combined; the land valued as regular fragmented parcels and as an assembled "
                "superblock (worth more, but hard to put together); the office FULL BUY-OUT; and the Live Local redevelopment test.",
          style="banner_sub", align="left", merge=(r, 13)); s.rowh(r, 30); r += 2

    # ============ 1. component pricing: independent -> combined ============
    s.section(r, L, 13, "①  COMPONENT PRICING  —  each priced independently, then combined  (🟢 live links)"); r += 1
    s.put(r, L, "Component", style="subhead", align="left")
    s.put(r, 3, "Independent price", style="subhead", align="center")
    s.put(r, 5, "Basis / note", style="subhead", align="left", merge=(r, 13)); r += 1
    c_first = r
    for sheet, label, cell, note in COMPONENTS:
        s.put(r, L, label, style="calc", align="left")
        s.put(r, 3, f"={x(sheet, cell)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 5, note, style="note", align="left", merge=(r, 13)); r += 1
    c_last = r - 1
    s.put(r, L, "SUM OF THE PARTS  (priced independently)", style="subtotal", align="left")
    s.put(r, 3, f"=SUM({CL(3)}{c_first}:{CL(3)}{c_last})", style="calc", fmt=F_ACCT_TOP, align="right", bold=True, name="SUM_PARTS")
    s.put(r, 5, "what you'd pay buying each one at a time", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "＋ Assemblage premium (hard to put together)", style="label", align="left")
    s.put(r, 3, f"={s.reg['SUM_PARTS']}*{AS('PREM_BASE')}", style="calc", fmt=F_ACCT, align="right", name="ASM_PREM")
    s.put(r, 4, f"={AS('PREM_BASE')}", style="calc", color="008000", fmt=F_PCT1, align="right")
    s.put(r, 5, "5 owners · a sale-leaseback · a fractured condo · holdout risk", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "PRICED AS AN ASSEMBLAGE (base)", style="grand", align="left")
    s.put(r, 3, f"={s.reg['SUM_PARTS']}+{s.reg['ASM_PREM']}", style="grand", fmt=F_ACCT_TOP, align="right", name="ASM_TOTAL")
    s.put(r, 5, "total to control the whole block", style="note", align="left", merge=(r, 13)); r += 2

    # ============ acquisition history / seller cost basis ============
    s.section(r, L, 13, "ACQUISITION HISTORY  —  what each owner paid, and when  (seller basis = negotiation leverage)"); r += 1
    s.put(r, L, "Component / owner", style="subhead", align="left")
    s.put(r, 3, "Bought", style="subhead", align="center")
    s.put(r, 4, "For", style="subhead", align="center")
    s.put(r, 5, "Our modeled price", style="subhead", align="center")
    s.put(r, 6, "note", style="subhead", align="left", merge=(r, 13)); r += 1
    for label, date, price, ourcell, verified, note in ACQ_HISTORY:
        st = "verified" if verified else "calc"
        s.put(r, L, label, style=st, align="left")
        s.put(r, 3, date, style=st, align="center")
        s.put(r, 4, (price if price else "—"), style=st, fmt=(F_ACCT if price else None), align="right")
        if ourcell:
            sheet, cell = ourcell
            s.put(r, 5, f"={x(sheet, cell)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        else:
            s.put(r, 5, "—", style="note", align="right")
        s.put(r, 6, note, style="note", align="left", merge=(r, 13)); r += 1
    r += 1

    # ============ 2. land: regular parcels vs assembled ============
    s.section(r, L, 13, "②  LAND VALUE  —  as REGULAR (fragmented) parcels"); r += 1
    s.put(r, L, "Parcel", style="subhead", align="left")
    s.put(r, 3, "Land SF", style="subhead", align="center")
    s.put(r, 4, "$/SF", style="subhead", align="center")
    s.put(r, 5, "Land value", style="subhead", align="center")
    s.put(r, 6, "note", style="subhead", align="left", merge=(r, 13)); r += 1
    l_first = r
    for sheet, label, sfcell, psfcell, valcell in LANDPARCELS:
        s.put(r, L, label, style="calc", align="left")
        s.put(r, 3, f"={x(sheet, sfcell)}", style="calc", color="008000", fmt=F_NUM, align="right")
        if psfcell:
            s.put(r, 4, f"={x(sheet, psfcell)}", style="calc", color="008000", fmt=F_PSF, align="right")
        else:
            s.put(r, 4, f"={x(sheet, valcell)}/{x(sheet, sfcell)}", style="calc", fmt=F_PSF, align="right")
        s.put(r, 5, f"={x(sheet, valcell)}", style="calc", color="008000", fmt=F_ACCT, align="right")
        s.put(r, 6, "standalone parcel", style="note", align="left", merge=(r, 13)); r += 1
    l_last = r - 1
    s.put(r, L, "SUM OF THE PARTS  (fragmented land)", style="subtotal", align="left")
    s.put(r, 3, f"=SUM({CL(3)}{l_first}:{CL(3)}{l_last})", style="subtotal", fmt=F_NUM, align="right", bold=True, name="LAND_SF")
    s.put(r, 4, f"=SUM({CL(5)}{l_first}:{CL(5)}{l_last})/SUM({CL(3)}{l_first}:{CL(3)}{l_last})", style="subtotal", fmt=F_PSF, align="right")
    s.put(r, 5, f"=SUM({CL(5)}{l_first}:{CL(5)}{l_last})", style="subtotal", fmt=F_ACCT_TOP, align="right", bold=True, name="LAND_FRAG")
    s.put(r, 6, "office excluded — building, not land (buy-out below)", style="note", align="left", merge=(r, 13)); r += 1

    s.section(r, L, 13, "②  LAND VALUE  —  as an ASSEMBLED SUPERBLOCK  (plottage: worth more, hard to assemble)"); r += 1
    def kv(label, formula, fmt, name=None, note="", style="calc"):
        nonlocal r
        s.put(r, L, label, style=("grand" if style == "grand" else "label"), align="left")
        s.put(r, 3, formula, style=("grand" if style == "grand" else "calc"), fmt=fmt, align="right", name=name, bold=(style == "grand"))
        if note: s.put(r, 5, note, style="note", align="left", merge=(r, 13))
        r += 1
    kv("Assembled land (SF)", f"={s.reg['LAND_SF']}", F_NUM, note="4 contiguous land parcels, one plat block")
    kv("Assembled land (acres)", f"={s.reg['LAND_SF']}/43560", "#,##0.00")
    kv("Plottage / assemblage premium (base)", f"={AS('PREM_BASE')}", F_PCT1, note="uplift for a large contiguous development site")
    kv("Assembled land value — low", f"={s.reg['LAND_FRAG']}*(1+{AS('PREM_LOW')})", F_ACCT)
    kv("Assembled land value — BASE", f"={s.reg['LAND_FRAG']}*(1+{AS('PREM_BASE')})", F_ACCT_TOP, name="LAND_ASM", style="grand")
    kv("Assembled land value — high", f"={s.reg['LAND_FRAG']}*(1+{AS('PREM_HIGH')})", F_ACCT)
    kv("Implied assembled $/SF (base)", f"={s.reg['LAND_ASM']}/{s.reg['LAND_SF']}", F_PSF, note="vs. fragmented blend above")
    kv("PLOTTAGE PREMIUM (assembled − fragmented)", f"={s.reg['LAND_ASM']}-{s.reg['LAND_FRAG']}", F_ACCT_TOP, name="PLOTTAGE",
       note="the value created / cost incurred by assembling the hard-to-put-together block")
    kv("Entitlement lift (post-Live Local approval)", f"={AS('ELIFT')}", F_PCT1, note="value bump once entitled for Live Local density")
    kv("POST-APPROVAL assembled land value", f"={s.reg['LAND_ASM']}*(1+{AS('ELIFT')})", F_ACCT_TOP, name="LAND_ENTITLED", style="grand",
       note="what the ENTITLED dirt is worth — the redevelopment upside the premium buys you the option on")
    r += 1

    # ============ 3. office condo full buy-out ============
    s.section(r, L, 13, "③  OFFICE CONDO  —  FULL BUY-OUT  (the building on the corner, two dominant owners)"); r += 1
    s.put(r, L, "Main Street Fund LLC (Grove Gate, 57.4%)", style="calc", align="left")
    s.put(r, 3, f"={x('Office Condo', 'BUYOUT1')}", style="calc", color="008000", fmt=F_ACCT, align="right")
    s.put(r, 5, "bought 96,930 SF + 2 parking lots for $10M (2019)", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "International Sunrise Partners LLC (42.6%)", style="calc", align="left")
    s.put(r, 3, f"={x('Office Condo', 'BUYOUT2')}", style="calc", color="008000", fmt=F_ACCT, align="right")
    s.put(r, 5, "prior bulk owner (2011 condo-conversion sponsor)", style="note", align="left", merge=(r, 13)); r += 1
    s.put(r, L, "FULL BUY-OUT VALUE (both owners)", style="grand", align="left")
    s.put(r, 3, f"={x('Office Condo', 'BUYOUT_TOTAL')}", style="grand", fmt=F_ACCT_TOP, align="right")
    s.put(r, 5, "income value + buy-out premium; adjust the premium on the Office Condo tab", style="note", align="left", merge=(r, 13)); r += 2

    # ============ 4. redevelopment residual (HBU test) ============
    s.section(r, L, 13, "④  REDEVELOPMENT — LIVE LOCAL RESIDUAL  (assemblage scale · ⚠️ negative → HOLD)"); r += 1
    s.put(r, L, "Buildable density (units/acre)", style="label", align="left")
    s.put(r, 3, 100, style="input", fmt=F_NUM, align="right", name="DENSITY")
    s.put(r, 4, "🔵 Live Local target", style="note", align="left", merge=(r, 13)); r += 1
    kv("Assemblage buildable units", f"={s.reg['LAND_SF']}/43560*{s.reg['DENSITY']}", F_NUM, name="UNITS", note="acres × density")
    kv("Gross development value (GDV)", f"={s.reg['UNITS']}*{AS('REVUNIT')}", F_ACCT_TOP, name="GDV", note="units × achievable value/unit (Assumptions)")
    kv("Buildable GBA (SF)", f"={s.reg['UNITS']}*{AS('GBAUNIT')}", F_NUM, name="GBA")
    kv("− Hard cost", f"=-{s.reg['GBA']}*{AS('HARDPSF')}", F_ACCT, name="HARD")
    kv("− Soft cost", f"=-{s.reg['GBA']}*{AS('HARDPSF')}*{AS('SOFT')}", F_ACCT)
    kv("− Developer profit", f"=-{s.reg['GDV']}*{AS('PROFIT')}", F_ACCT)
    kv("RESIDUAL LAND VALUE (supports acquisition?)", f"={s.reg['GDV']}+{s.reg['HARD']}-{s.reg['GBA']}*{AS('HARDPSF')}*{AS('SOFT')}-{s.reg['GDV']}*{AS('PROFIT')}",
       F_ACCT_TOP, name="RESID", style="grand")
    s.put(r, L, "HBU verdict", style="warn", align="left")
    s.put(r, 3, "HOLD", style="warn", align="center")
    s.put(r, 4, "Residual runs NEGATIVE at coastal AE-zone hard costs — redevelopment does not pencil today. Highest & best use = "
                "acquire and HOLD the income-covered assemblage; redevelop when achievable rents / hard costs support Live Local density.",
          style="warn", align="left", merge=(r, 13)); r += 2

    # ============ 5. conclusion ============
    s.section(r, L, 13, "⑤  CONCLUSION"); r += 1
    for t in [
        "• Priced independently, the components sum to ~$86M; as an assemblage (base premium) ~$103M — the premium is the cost of controlling",
        "  a contiguous block held by five owners (a sale-leaseback, a fractured condo, and holdout risk).",
        "• The land alone is worth more assembled (plottage) than as fragmented parcels — but redevelopment does not yet pencil, so the",
        "  return today is income-covered land banking, with the Live Local density as the option you are paying the premium to hold.",
    ]:
        s.put(r, L, t, style="calc", align="left", merge=(r, 13)); r += 1

    s.freeze("C3")
    return s
