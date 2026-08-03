#!/usr/bin/env python3
"""
Multi-tab Excel workbook -> outputs/Commercial_Deal_Dashboard.xlsx

Tabs: Index · Key Conclusions · Assumptions · Submarkets · Types · Repricing · Opportunities ·
Absorption · Prospects · Comps · Scenario (formula-driven underwriting; NOI built from the
Assumptions, every yellow cell live).
"""
from __future__ import annotations
import json
import os

import pandas as pd
import xlsxwriter  # noqa: F401

import cre_common as CRE
import cre_assumptions as A
import cre_scenario as SC
import market_context as MKT

OUT = os.path.join(CRE.ROOT, "outputs", "Commercial_Deal_Dashboard.xlsx")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
DARK, BLUE, GOOD, BAD = "#1f2a37", "#2f6f9f", "#3f7d5a", "#b0473a"


def _load(n):
    p = os.path.join(CRE.PROC, n)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def _fmts(wb):
    f = {}
    f["title"] = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    f["sub"] = wb.add_format({"font_size": 10, "italic": True, "font_color": "#7a786f",
                              "text_wrap": True, "valign": "top"})
    f["hdr"] = wb.add_format({"bold": True, "font_color": "white", "bg_color": DARK, "border": 1,
                              "border_color": "white", "align": "center", "valign": "vcenter",
                              "text_wrap": True})
    f["grp"] = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                              "border_color": "white"})
    f["lab"] = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "vcenter"})
    f["olab"] = wb.add_format({"border": 1, "border_color": "#e1e0d9", "bold": True})
    f["txt"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "valign": "top", "text_wrap": True})
    f["usd"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "$#,##0", "align": "right"})
    f["pct2"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "0.00%", "align": "right"})
    f["pct0"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "0%", "align": "right"})
    f["gap"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "+0.0;-0.0", "align": "right"})
    f["num"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "#,##0", "align": "right"})
    f["num1"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "0.0", "align": "right"})
    f["pctn"] = wb.add_format({"border": 1, "border_color": "#ecebe4", "num_format": "0.0\"%\"", "align": "right"})
    f["cell"] = wb.add_format({"border": 1, "border_color": "#ecebe4"})
    return f


def _matrix_block(ws, f, mtx, title, start):
    """Write a count matrix then a %-share matrix (share within each row)."""
    cols = mtx["cols"]
    recs = mtx["counts"]
    rowkey = next((k for k in recs[0].keys() if k not in cols), "row") if recs else "row"
    r = start
    ws.write(r, 0, title, f["title"]); r += 1
    ws.write(r, 0, "Count", f["olab"])
    for j, c in enumerate(cols):
        ws.write(r, 1 + j, c, f["hdr"])
    ws.write(r, 1 + len(cols), "Total", f["hdr"]); r += 1
    for rec in recs:
        ws.write(r, 0, rec.get(rowkey), f["lab"]); tot = 0
        for j, c in enumerate(cols):
            val = int(rec.get(c, 0) or 0); tot += val; ws.write_number(r, 1 + j, val, f["num"])
        ws.write_number(r, 1 + len(cols), tot, f["olab"] if False else f["num"]); r += 1
    r += 1
    ws.write(r, 0, "% share (within row)", f["olab"])
    for j, c in enumerate(cols):
        ws.write(r, 1 + j, c, f["hdr"])
    r += 1
    for rec in mtx["share"]:
        ws.write(r, 0, rec.get(rowkey), f["lab"])
        for j, c in enumerate(cols):
            val = rec.get(c)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                ws.write(r, 1 + j, "—", f["cell"])
            else:
                ws.write_number(r, 1 + j, float(val), f["pctn"])
        r += 1
    return r + 2


def _comp_block(ws, f, records, label, start, title):
    r = start
    ws.write(r, 0, title, f["title"]); r += 1
    for j, h in enumerate([label, "Count", "% of market", "Median $/SqFt"]):
        ws.write(r, j, h, f["hdr"])
    r += 1
    for rec in records:
        k = next(iter(rec))
        ws.write(r, 0, rec.get(k), f["lab"])
        ws.write_number(r, 1, int(rec["n"]), f["num"])
        ws.write_number(r, 2, float(rec["share_pct"]), f["pctn"])
        mp = rec.get("median_ppsf")
        ws.write_number(r, 3, float(mp), f["usd"]) if mp is not None and not pd.isna(mp) else ws.write(r, 3, "—", f["cell"])
        r += 1
    return r + 2


def _table(ws, f, df, spec, start=3, autofilter=True):
    for j, (_, h, _) in enumerate(spec):
        ws.write(start, j, h, f["hdr"])
    for i, (_, row) in enumerate(df.iterrows()):
        for j, (col, _, fk) in enumerate(spec):
            v = row.get(col)
            fmt = f.get(fk, f["cell"])
            if v is None or (isinstance(v, float) and pd.isna(v)):
                ws.write(start + 1 + i, j, "—", f["cell"])
            elif fk in ("usd", "pct2", "pct0", "gap", "num", "num1"):
                ws.write_number(start + 1 + i, j, float(v), fmt)
            else:
                ws.write(start + 1 + i, j, v, fmt)
    if autofilter and len(df):
        ws.autofilter(start, 0, start + len(df), len(spec) - 1)
    ws.freeze_panes(start + 1, 0)


def _head(ws, f, title, sub, n=8):
    ws.write(0, 0, title, f["title"])
    ws.merge_range(1, 0, 1, n, sub, f["sub"])
    ws.set_row(1, 30)


# ---------------------------------------------------------------------------
def assumptions_sheet(wb, f, types):
    ws = wb.add_worksheet("Assumptions")
    _head(ws, f, "Income assumptions (edit the yellow cells)",
          "The export has no income. These per-asset-class norms turn size into NOI. Implied cap "
          "= NOI ÷ price on the type's median $/SqFt; it recomputes when you edit an input.", 7)
    hi = {"bg_color": "#fff7d6", "border": 1, "border_color": "#d9cf9a", "align": "right"}
    im = wb.add_format({**hi, "num_format": "$#,##0"})
    ipct = wb.add_format({**hi, "num_format": "0%"})
    ipct2 = wb.add_format({**hi, "num_format": "0.00%"})
    ws.set_column(0, 0, 20); ws.set_column(1, 7, 13)
    heads = ["Asset type", "Median $/SqFt", "Rent $/SqFt", "Vacancy %", "Opex % EGI",
             "Market cap %", "Implied cap", "Mkt rent (comps)", "Conf"]
    for j, h in enumerate(heads):
        ws.write(3, j, h, f["hdr"])
    icfmt = wb.add_format({"border": 1, "border_color": "#e1e0d9", "num_format": "0.00%",
                           "align": "right", "bold": True})
    for i, (_, r) in enumerate(types.iterrows()):
        rr = 4 + i
        er = rr + 1
        ws.write(rr, 0, r["asset_type"], f["lab"])
        ws.write_number(rr, 1, float(r["median_ppsf"]), f["usd"])
        ws.write_number(rr, 2, float(r["assume_rent_psf"]), im)
        ws.write_number(rr, 3, float(r["assume_vacancy"]), ipct)
        ws.write_number(rr, 4, float(r["assume_opex_ratio"]), ipct)
        ws.write_number(rr, 5, float(r["assume_cap_rate"]), ipct2)
        # implied cap = rent*(1-vac)*(1-opex)/median_ppsf
        ic = float(r["assume_rent_psf"]) * (1 - r["assume_vacancy"]) * (1 - r["assume_opex_ratio"]) / max(float(r["median_ppsf"]), 1)
        ws.write_formula(rr, 6, f"=C{er}*(1-D{er})*(1-E{er})/B{er}", icfmt, ic)
        mr = r.get("market_rent_psf")
        if mr is not None and not pd.isna(mr):
            ws.write_number(rr, 7, float(mr), f["usd"])
        else:
            ws.write(rr, 7, "—", f["cell"])
        ws.write(rr, 8, r.get("confidence", "—"), f["cell"])
    ws.set_column(7, 8, 14)
    ws.write(4 + len(types) + 1, 0,
             "'Mkt rent (comps)' is the median asking lease rate from the lease listings — where present, "
             "consider replacing the assumed Rent $/SqFt with it.", f["sub"])


def scenario_sheet(wb, f, seed):
    ws = wb.add_worksheet("Scenario")
    s = seed
    v = SC.compute(s["price"], s["sqft"], s["rent_psf"], s["vacancy"], s["opex_ratio"],
                   s["market_cap"], s["ltv"], s["rate"], s["amort"], s["shift_bps"],
                   s["exit_cap"], s["rent_growth"], s["expense_growth"], s["hold"],
                   s["sell_pct"], s["acq_pct"])
    hi = {"bg_color": "#fff7d6", "border": 1, "border_color": "#d9cf9a", "align": "right", "bold": True}
    im = wb.add_format({**hi, "num_format": "$#,##0"})
    inum = wb.add_format({**hi, "num_format": "#,##0"})
    ipct = wb.add_format({**hi, "num_format": "0%"})
    ipct2 = wb.add_format({**hi, "num_format": "0.00%"})
    ibps = wb.add_format({**hi, "num_format": "0"})
    o = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "$#,##0"})
    ohi = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "$#,##0",
                         "bold": True, "bg_color": "#eef5fc"})
    opct = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "0.00%", "bold": True})
    opct1 = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "0.0%", "bold": True})
    ox = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "0.00\"×\"", "bold": True})
    onum = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right", "num_format": "#,##0"})

    ws.set_column(0, 0, 30); ws.set_column(1, 1, 15); ws.set_column(2, 2, 13)
    ws.set_column(3, 3, 24); ws.set_column(4, 6, 15)
    ws.write(0, 0, f"Underwrite — {s['asset_type']} deal (edit the yellow cells)", f["title"])
    ws.merge_range(1, 0, 1, 6, "NOI is BUILT from the income assumptions (no income in the source). "
                   "Change any yellow input — rents, cap, LTV, rate, exit — and every output plus the "
                   "10-yr cash flow and exit-cap sensitivity recompute.", f["sub"])
    ws.set_row(1, 42)

    ws.merge_range(3, 0, 3, 1, "DEAL", f["grp"])
    ws.write(4, 0, "Purchase price ($)", f["lab"]);   ws.write_number(4, 1, s["price"], im)       # B5
    ws.write(5, 0, "Size (SqFt)", f["lab"]);          ws.write_number(5, 1, s["sqft"], inum)      # B6
    ws.merge_range(6, 0, 6, 1, "INCOME ASSUMPTIONS", f["grp"])
    ws.write(7, 0, "Rent $/SqFt/yr", f["lab"]);       ws.write_number(7, 1, s["rent_psf"], im)    # B8
    ws.write(8, 0, "Vacancy (%)", f["lab"]);          ws.write_number(8, 1, s["vacancy"], ipct)   # B9
    ws.write(9, 0, "Opex (% of EGI)", f["lab"]);      ws.write_number(9, 1, s["opex_ratio"], ipct)  # B10
    ws.write(10, 0, "Market cap (%)", f["lab"]);      ws.write_number(10, 1, s["market_cap"], ipct2)  # B11
    ws.merge_range(11, 0, 11, 1, "FINANCING", f["grp"])
    ws.write(12, 0, "Loan-to-value (%)", f["lab"]);   ws.write_number(12, 1, s["ltv"], ipct)      # B13
    ws.write(13, 0, "Interest rate (%)", f["lab"]);   ws.write_number(13, 1, s["rate"], ipct2)    # B14
    ws.write(14, 0, "Amortization (yrs)", f["lab"]);  ws.write_number(14, 1, s["amort"], inum)    # B15
    ws.write(15, 0, "Rate shift (bps)", f["lab"]);    ws.write_number(15, 1, s["shift_bps"], ibps)  # B16
    ws.merge_range(16, 0, 16, 1, "EXIT & GROWTH", f["grp"])
    ws.write(17, 0, "Exit cap (%)", f["lab"]);        ws.write_number(17, 1, s["exit_cap"], ipct2)  # B18
    ws.write(18, 0, "Rent growth (%/yr)", f["lab"]);  ws.write_number(18, 1, s["rent_growth"], ipct)  # B19
    ws.write(19, 0, "Expense growth (%/yr)", f["lab"]); ws.write_number(19, 1, s["expense_growth"], ipct)  # B20
    ws.write(20, 0, "Hold (yrs, ≤10)", f["lab"]);     ws.write_number(20, 1, s["hold"], inum)     # B21
    ws.write(21, 0, "Selling costs (%)", f["lab"]);   ws.write_number(21, 1, s["sell_pct"], ipct)  # B22
    ws.write(22, 0, "Acquisition costs (%)", f["lab"]); ws.write_number(22, 1, s["acq_pct"], ipct)  # B23

    EGI0 = "($B$6*$B$8*(1-$B$9))"
    EXP0 = f"({EGI0}*$B$10)"
    proj_hdr = 26
    proj0 = proj_hdr + 1

    ws.merge_range(3, 3, 3, 4, "LIVE OUTPUTS", f["grp"])
    ws.write(4, 3, "In-place EGI", f["olab"]);   ws.write_formula(4, 4, f"={EGI0}", o, v["egi0"])   # E5
    ws.write(5, 3, "In-place NOI", f["olab"]);   ws.write_formula(5, 4, "=E5*(1-$B$10)", ohi, v["noi0"])  # E6
    ws.write(6, 3, "Going-in cap", f["olab"]);   ws.write_formula(6, 4, "=E6/$B$5", opct, v["goin_cap"])  # E7
    ws.write(7, 3, "Value @ market cap", f["olab"]); ws.write_formula(7, 4, "=E6/$B$11", ohi, v["noi0"]/s["market_cap"])  # E8
    ws.write(8, 3, "Effective rate", f["olab"]); ws.write_formula(8, 4, "=$B$14+$B$16/10000", opct, v["effr"])  # E9
    ws.write(9, 3, "Loan", f["olab"]);           ws.write_formula(9, 4, "=$B$5*$B$13", o, v["loan"])  # E10
    ws.write(10, 3, "Equity (incl. costs)", f["olab"]); ws.write_formula(10, 4, "=$B$5*(1-$B$13)+$B$5*$B$23", ohi, v["equity"])  # E11
    ws.write(11, 3, "Annual debt service", f["olab"])
    ws.write_formula(11, 4, "=E10*(E9/12)/(1-(1+E9/12)^-($B$15*12))*12", o, v["ads"])  # E12
    ws.write(12, 3, "DSCR", f["olab"]);          ws.write_formula(12, 4, "=E6/E12", ox, v["dscr"])  # E13
    ws.write(13, 3, "Debt yield", f["olab"]);    ws.write_formula(13, 4, "=E6/E10", opct1, v["debt_yield"])  # E14
    y1 = f"D{proj0 + 2}"
    ws.write(14, 3, "Year-1 cash-on-cash", f["olab"]); ws.write_formula(14, 4, f"=({y1}-E12)/E11", opct1, v["coc1"])  # E15
    ws.write(15, 3, "Exit NOI (@ hold)", f["olab"])
    ws.write_formula(15, 4, f"={EGI0}*(1+$B$19)^$B$21-{EXP0}*(1+$B$20)^$B$21", o, v["exit_noi"])  # E16
    ws.write(16, 3, "Exit value", f["olab"]);    ws.write_formula(16, 4, "=E16/$B$18", ohi, v["exit_value"])  # E17
    ws.write(17, 3, "Loan balance @ exit", f["olab"])
    ws.write_formula(17, 4, "=E10*((1+E9/12)^($B$15*12)-(1+E9/12)^($B$21*12))/((1+E9/12)^($B$15*12)-1)", o, v["remloan"])  # E18
    ws.write(18, 3, "Net sale proceeds", f["olab"]); ws.write_formula(18, 4, "=E17*(1-$B$22)-E18", ohi, v["net_sale"])  # E19
    g_lo, g_hi = f"G{proj0 + 1}", f"G{proj0 + 11}"
    ws.write(19, 3, "Levered IRR", f["olab"]);   ws.write_formula(19, 4, f"=IRR({g_lo}:{g_hi})", opct1, v["lirr"])  # E20
    ws.write(20, 3, "Equity multiple", f["olab"]); ws.write_formula(20, 4, f"=SUM(G{proj0+2}:G{proj0+11})/E11", ox, v["em"])  # E21

    ws.write(proj_hdr - 1, 0, "10-year levered cash flow", f["title"])
    for j, h in enumerate(["Year", "EGI", "Expenses", "NOI", "Debt service", "Op cash flow", "Levered CF"]):
        ws.write(proj_hdr, j, h, f["hdr"])
    ws.write_number(proj0, 0, 0, onum)
    for c in range(1, 6):
        ws.write_blank(proj0, c, None, f["cell"])
    ws.write_formula(proj0, 6, "=-E11", o, -v["equity"])
    for yr in range(1, 11):
        r = proj0 + yr
        er = r + 1
        ws.write_number(r, 0, yr, onum)
        ws.write_formula(r, 1, f"=IF({yr}<=$B$21,{EGI0}*(1+$B$19)^{yr},0)", o,
                         (v["egi0"] * (1 + s["rent_growth"]) ** yr) if yr <= s["hold"] else 0)
        ws.write_formula(r, 2, f"=IF({yr}<=$B$21,{EXP0}*(1+$B$20)^{yr},0)", o,
                         (v["exp0"] * (1 + s["expense_growth"]) ** yr) if yr <= s["hold"] else 0)
        ws.write_formula(r, 3, f"=B{er}-C{er}", o,
                         v["noi_t"][yr - 1] if yr <= s["hold"] else 0)
        ws.write_formula(r, 4, f"=IF({yr}<=$B$21,E12,0)", o, v["ads"] if yr <= s["hold"] else 0)
        ws.write_formula(r, 5, f"=IF({yr}<=$B$21,D{er}-E{er},0)", o,
                         (v["noi_t"][yr - 1] - v["ads"]) if yr <= s["hold"] else 0)
        cf = ((v["noi_t"][yr - 1] - v["ads"]) if yr <= s["hold"] else 0) + (v["net_sale"] if yr == s["hold"] else 0)
        ws.write_formula(r, 6, f"=F{er}+IF({yr}=$B$21,E19,0)", o, cf)

    sr = proj0 + 13
    ws.write(sr - 1, 0, "Sensitivity to exit cap", f["title"])
    for j, h in enumerate(["Exit cap", "Exit value", "Net proceeds", "Equity multiple"]):
        ws.write(sr, j, h, f["hdr"])
    for i, dd in enumerate((-0.0075, -0.005, -0.0025, 0, 0.0025, 0.005, 0.0075, 0.01)):
        cap = round(s["exit_cap"] + dd, 4)
        r = sr + 1 + i
        er = r + 1
        ws.write_number(r, 0, cap, wb.add_format({"border": 1, "border_color": "#ecebe4",
                                                  "num_format": "0.00%", "align": "right", "bold": dd == 0}))
        ws.write_formula(r, 1, f"=$E$16/A{er}", o, v["exit_noi"] / cap)
        netp = (v["exit_noi"] / cap) * (1 - s["sell_pct"]) - v["remloan"]
        ws.write_formula(r, 2, f"=B{er}*(1-$B$22)-$E$18", o, netp)
        em = v["em"] + (netp - v["net_sale"]) / v["equity"]
        ws.write_formula(r, 3, f"=$E$21+(C{er}-$E$19)/$E$11", ox, em)


def market_sheet(wb, f):
    mk = MKT.to_dict()
    ws = wb.add_worksheet("Market")
    _head(ws, f, "Market context — researched benchmarks",
          f"External Broward / Fort Lauderdale benchmarks, {mk['as_of']}. The market backdrop to "
          "compare your data against — verify before quoting a specific deal.", 5)
    ws.set_column(0, 0, 36)
    ws.set_column(1, 5, 22)
    r = 3
    ws.write(r, 0, "Benchmarks by asset class", f["title"]); r += 1
    for j, h in enumerate(["Asset type", "Cap", "Rent", "Sale $/SF", "Vacancy", "Trend"]):
        ws.write(r, j, h, f["hdr"])
    r += 1
    for a, b in mk["assets"].items():
        ws.write(r, 0, a, f["olab"]); ws.write(r, 1, b["cap"], f["txt"]); ws.write(r, 2, b["rent"], f["txt"])
        ws.write(r, 3, b["sale_ppsf"], f["txt"]); ws.write(r, 4, b["vacancy"], f["txt"])
        ws.write(r, 5, b["trend"], f["txt"]); ws.set_row(r, 30); r += 1
    r += 1

    def kv(title, obj, r):
        ws.write(r, 0, title, f["title"]); r += 1
        for k, v in obj.items():
            ws.write(r, 0, k, f["olab"]); ws.merge_range(r, 1, r, 5, v, f["txt"]); r += 1
        return r + 1

    r = kv("Construction (hard $/SqFt)", mk["construction"], r)
    r = kv("Renovation / rehab", mk["rehab"], r)
    r = kv("Florida cost adders", mk["adders"], r)
    r = kv("Land basis", mk["land"], r)
    r = kv("Waterfront & dockage", mk["waterfront"], r)
    r = kv("Insurance", mk["insurance"], r)
    r = kv("Incentives", mk["incentives"], r)

    ws.write(r, 0, "Neighborhood playbook", f["title"]); r += 1
    for area, ap in mk["area_to_profile"].items():
        prof = mk["submarket_profiles"][ap["key"]]
        ws.write(r, 0, f"{area} → {ap['key']}", f["olab"])
        ws.merge_range(r, 1, r, 5, f"{prof['blurb']}  RECENT: {prof['deals']}  PLAY: {prof['angle']}", f["txt"])
        ws.set_row(r, 58); r += 1
    r += 1
    ws.write(r, 0, "Sources", f["title"]); r += 1
    link = wb.add_format({"font_color": BLUE, "underline": 1})
    for s in mk["sources"]:
        ws.write_url(r, 0, s["url"], link, s["name"]); r += 1


def index_sheet(wb, f, meta):
    ws = wb.add_worksheet("Start Here")
    ws.hide_gridlines(2)
    ws.set_column(0, 0, 24); ws.set_column(1, 1, 96)
    ws.write(0, 0, "Commercial Deal Dashboard — Fort Lauderdale", f["title"])
    ws.merge_range(1, 0, 1, 1, "Everything in one workbook. The MLS export has no income, so cap / "
                   "rent / value figures are assumption- or comp-based — a screening & pitching tool, "
                   "not an appraisal. Verify before quoting. Click any tab below.", f["sub"])
    ws.set_row(1, 42)
    ws.write(3, 0, "How to use it on a call", f["title"])
    howto = [
        "Call List — your prospect list: a ready opener to say, the value read, and owner-FAQ answers for each owner (motivated/failed first).",
        "Neighborhoods — every submarket as a system: what it supports, rents, yield, supply, and the pitch angle.",
        "Repricing — what each listing is GOING FOR vs what it SHOULD be — adjusted basis, up ▲ or down ▼, in % and $.",
        "Opportunities / Prospects — the underpriced buys, and failed listings + overpriced actives to call.",
        "Leasing — asking rents by type & submarket + data-derived cap rates. Comps — the closed sales behind every number.",
        "Market — researched benchmarks + construction / land / waterfront / insurance costs + incentives (Live Local, OZ, CRA).",
        "Assumptions / Scenario — tune the income assumptions (yellow cells) and underwrite a single deal.",
    ]
    for i, t in enumerate(howto):
        ws.write(4 + i, 0, "•", f["olab"]); ws.write(4 + i, 1, t, f["txt"]); ws.set_row(4 + i, 28)
    base = 4 + len(howto) + 1
    ws.write(base, 0, "Tabs", f["title"])
    toc = [("Guide", "Plain-English glossary + how to recreate this on new data."),
           ("Key Takeaways", "The headlines in plain English."),
           ("Call List", "Owners to cold-call — opener + value read + FAQ."),
           ("Neighborhoods", "Every submarket as a system, side by side."),
           ("Repricing", "Going-for vs should-be, adjusted basis up/down."),
           ("Segmentation", "Market share by asset type, price bracket & size class."),
           ("Neighborhood Mix", "What each area is made of (type / price / size)."),
           ("Opportunities", "Underpriced buys."),
           ("Prospects", "Failed listings + overpriced actives."),
           ("Leasing", "Asking rents + data-derived cap rates."),
           ("Comps", "Closed sales behind the numbers."),
           ("Market", "Benchmarks, costs & the neighborhood playbook."),
           ("Assumptions", "Editable income norms by asset type."),
           ("Scenario", "Live single-deal underwriting."),
           ("Types", "$/SqFt + assumed income by asset class."),
           ("Absorption", "Months of supply by submarket & type.")]
    link = wb.add_format({"font_color": BLUE, "bold": True, "underline": 1, "border": 1, "border_color": "#e1e0d9"})
    for i, (name, desc) in enumerate(toc):
        r = base + 1 + i
        ws.write_url(r, 0, f"internal:'{name}'!A1", link, name)
        ws.write(r, 1, desc, f["txt"]); ws.set_row(r, 20)


def key_sheet(wb, f, meta, master, reb, pros, seed, v):
    ws = wb.add_worksheet("Key Takeaways")
    ws.hide_gridlines(2)
    ws.set_column(0, 0, 3); ws.set_column(1, 1, 112)
    ws.write(0, 1, "Key takeaways", f["title"])
    subs = pd.DataFrame(master["submarkets"])
    top, bot = subs.iloc[0], subs.iloc[-1]
    lines = [
        "No income in the source MLS export — every NOI/cap/return here is derived from the "
        "editable assumptions (Assumptions tab & dashboard). This is pricing & screening, not appraisal.",
        f"{meta['n_listings']} listings, {meta['n_sale_comps']} sale comps ({meta['n_closed']} closed). "
        f"Normalized $/SqFt fit R²={meta['hedonic_r2']}; market-wide ${meta['city_norm_ppsf']:,.0f}/SqFt.",
        f"Priciest area: {top['submarket']} ${top['norm_ppsf']:,.0f}/SqFt; cheapest: "
        f"{bot['submarket']} ${bot['norm_ppsf']:,.0f}/SqFt.",
    ]
    if reb:
        fc = reb["flag_counts"]
        lines.append(f"Live inventory at default assumptions: {fc.get('Underpriced',0)} underpriced / "
                     f"{fc.get('Overpriced',0)} overpriced of {reb['meta']['n_live']} — flags move as you tune.")
    if pros:
        lines.append(f"Prospecting: {pros['meta']['n_failed']} failed listings + "
                     f"{pros['meta']['n_overpriced_active']} overpriced actives to call.")
    lines.append(f"Seed underwrite ({seed['asset_type']}, {CRE.usd(seed['price'])}, ${seed['rent_psf']}/SqFt "
                 f"rent): NOI {CRE.usd(v['noi0'])}, going-in cap {v['goin_cap']*100:.2f}%, DSCR {v['dscr']:.2f}×, "
                 f"{seed['hold']}-yr IRR {v['lirr']*100:.1f}%, EM {v['em']:.2f}×. Model it live on the Scenario tab.")
    for i, t in enumerate(lines):
        ws.write(2 + i, 0, "•", f["olab"]); ws.write(2 + i, 1, t, f["txt"]); ws.set_row(2 + i, 30)


def callist_sheet(wb, f):
    cb = _load("callsheets_bundle.json")
    if not cb:
        return
    ws = wb.add_worksheet("Call List")
    _head(ws, f, "Cold-call list — owners to work",
          f"{cb['meta']['n']} owners · {cb['meta']['n_motivated']} motivated (came off-market) first. "
          "Say the opener, use the value read, answer with the FAQ. Comp/assumption-based — verify before quoting.", 14)
    rows = [{"n": i, "address": s["address"], "asset_type": s["asset_type"], "submarket": s["submarket"],
             "status": s["status"], "motivated": "YES" if s["motivated"] else "",
             "sqft": s["sqft"], "last_ask": s["last_ask"], "value": s["value"],
             "comp_ppsf": s["comp_ppsf"], "implied_cap": s["implied_cap"], "lease_psf": s["lease_psf"],
             "opener": s["opener"], "value_read": s["value_read"], "faq": "  •  ".join(s["faq"])}
            for i, s in enumerate(cb["sheets"], 1)]
    df = pd.DataFrame(rows)
    ws.set_column(0, 0, 4); ws.set_column(1, 1, 26); ws.set_column(2, 3, 15); ws.set_column(4, 5, 11)
    ws.set_column(6, 11, 11); ws.set_column(12, 12, 62); ws.set_column(13, 13, 48); ws.set_column(14, 14, 80)
    _table(ws, f, df, [("n", "#", "num"), ("address", "Address", "txt"), ("asset_type", "Type", "txt"),
                       ("submarket", "Area", "txt"), ("status", "Status", "txt"), ("motivated", "Motiv.", "txt"),
                       ("sqft", "SqFt", "num"), ("last_ask", "Last ask", "usd"), ("value", "Comp value", "usd"),
                       ("comp_ppsf", "Comp $/SF", "usd"), ("implied_cap", "Impl cap", "pct2"),
                       ("lease_psf", "Lease $/SF", "usd"), ("opener", "Opener — say this", "txt"),
                       ("value_read", "Value read", "txt"), ("faq", "If they ask…", "txt")])
    good = wb.add_format({"font_color": GOOD, "bold": True})
    ws.conditional_format(4, 5, 3 + len(df), 5, {"type": "text", "criteria": "containing", "value": "YES", "format": good})


def neighborhoods_sheet(wb, f):
    cre = _load("cre_bundle.json")
    master = {s["submarket"]: s for s in (_load("master_bundle.json") or {"submarkets": []})["submarkets"]}
    lb = _load("leases_bundle.json") or {"by_submarket": []}
    lz = {r["submarket"]: r for r in lb["by_submarket"]}
    rows = []
    for s in sorted(cre["submarkets"], key=lambda x: -(x.get("norm_ppsf") or 0)):
        sub = s["submarket"]; m = master.get(sub, {}); l = lz.get(sub, {})
        prof_key, _ = MKT.AREA_TO_PROFILE.get(sub, (None, None))
        rows.append({"submarket": sub, "corridors": s.get("corridors"), "profile": prof_key,
                     "norm_ppsf": s.get("norm_ppsf"), "sold_ppsf": s.get("sold_ppsf_median"),
                     "vs_city": s.get("vs_city_pct"), "lease_psf": l.get("lease_psf"),
                     "gross_yield": l.get("gross_yield"), "months_supply": m.get("months_supply"),
                     "failure": m.get("failure_rate_pct"), "under": m.get("live_underpriced"),
                     "over": m.get("live_overpriced"), "stance": m.get("stance")})
    ws = wb.add_worksheet("Neighborhoods")
    _head(ws, f, "Neighborhoods — each submarket as a system",
          "Normalized $/SqFt, rents, yield, supply and stance side by side. Per-area repricing detail is in "
          "the Repricing tab and the Neighborhood Report PDF.", 12)
    ws.set_column(0, 0, 14); ws.set_column(1, 1, 26); ws.set_column(2, 2, 24); ws.set_column(3, 12, 12)
    _table(ws, f, pd.DataFrame(rows),
           [("submarket", "Submarket", "txt"), ("corridors", "Corridors", "txt"), ("profile", "Profile", "txt"),
            ("norm_ppsf", "Norm $/SF", "usd"), ("sold_ppsf", "Median sold $/SF", "usd"),
            ("vs_city", "vs city %", "gap"), ("lease_psf", "Lease $/SF", "usd"),
            ("gross_yield", "Gross yld", "pct2"), ("months_supply", "Mo supply", "num1"),
            ("failure", "Fail %", "num1"), ("under", "Under", "num"), ("over", "Over", "num"),
            ("stance", "Stance", "txt")])


def repricing_sheet(wb, f):
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    d = v[v["status"].isin(list(CRE.LIVE) + ["Cancelled", "Expired", "Withdrawn", "TempOff"])].copy()
    d = d[d["ppsf"].notna() & d["pred_ppsf"].notna() & d["ppsf"].gt(0)]
    d["adjust_pct"] = (d["pred_ppsf"] / d["ppsf"] - 1) * 100
    d["basis_delta"] = (d["pred_ppsf"] - d["ppsf"]) * d["sqft"].fillna(0)
    d = d.sort_values("adjust_pct", ascending=False)
    ws = wb.add_worksheet("Repricing")
    _head(ws, f, "Repricing — going for vs. should be going for",
          "Model $/SF = normalized value for that exact building (size/age/type removed). Adjust ▲ up = priced "
          "below the market (room to raise / a buy); ▼ down = priced above. Live + failed listings.", 9)
    ws.set_column(0, 0, 26); ws.set_column(1, 3, 13); ws.set_column(4, 9, 12)
    _table(ws, f, d, [("address", "Address", "txt"), ("asset_type", "Type", "txt"), ("submarket", "Area", "txt"),
                      ("status", "Status", "txt"), ("price", "Asking", "usd"), ("ppsf", "Going $/SF", "usd"),
                      ("pred_ppsf", "Model $/SF", "usd"), ("adjust_pct", "Adjust %", "gap"),
                      ("basis_delta", "Basis Δ $", "usd"), ("income_gap_pct", "Income gap %", "gap")])
    good = wb.add_format({"font_color": GOOD, "bold": True})
    bad = wb.add_format({"font_color": BAD, "bold": True})
    lo, hi = 4, 3 + len(d)
    for col in (7, 8):
        ws.conditional_format(lo, col, hi, col, {"type": "cell", "criteria": ">", "value": 0, "format": good})
        ws.conditional_format(lo, col, hi, col, {"type": "cell", "criteria": "<", "value": 0, "format": bad})


def guide_sheet(wb, f, meta):
    import math
    ws = wb.add_worksheet("Guide")
    ws.hide_gridlines(2)
    ws.set_column(0, 0, 30); ws.set_column(1, 1, 112)
    ws.write(0, 0, "Guide — understand it & recreate it", f["title"])
    ws.merge_range(1, 0, 1, 1, "A plain-English glossary of every number, what's real vs assumed, and "
                   "how to run this on a new set of properties.", f["sub"]); ws.set_row(1, 24)
    r = [3]

    def sec(t):
        ws.write(r[0], 0, t, f["title"]); r[0] += 1

    def item(term, desc):
        ws.write(r[0], 0, term, f["olab"]); ws.write(r[0], 1, desc, f["txt"])
        ws.set_row(r[0], 15 * max(1, math.ceil(len(desc) / 105)) + 6); r[0] += 1

    sec("What this is")
    item("The short version", "A comp-based commercial screening & pitching tool built from an MLS export. "
         "The export has price, size, type, age and location but NO income — so cap rate, rent and value "
         "figures are ASSUMPTION- or COMP-based. Use it to screen, prospect and price — not to appraise.")
    sec("What's real vs. what's assumed")
    item("Real (from your data)", "Price, building SqFt, asset type, year built, MLS area, status — and everything "
         "derived from them: $/SqFt, the price/size/type brackets, market share, closed comps, and asking lease rates.")
    item("Assumed (editable)", "Rent $/SqFt, vacancy, operating-expense ratio, market cap rate, rent/expense growth, "
         "and financing (LTV, rate, hold). Change these on the Assumptions & Scenario tabs (yellow cells) or in the dashboard.")
    sec("Glossary — every number explained")
    for term, desc in [
        ("Normalized $/SqFt", "The model's price per SqFt for a STANDARDIZED building in that area — size, age, type "
         "and the closed-vs-listed gap removed — so areas compare apples-to-apples."),
        ("Going $/SF", "What a listing is actually asking per SqFt right now."),
        ("Model $/SF", "What comps say that exact building SHOULD be per SqFt (its normalized value for size/age/type/area)."),
        ("Adjust ▲ up / ▼ down", "How far the asking is from the model. ▲ up = priced BELOW market (room to raise, or a buy); "
         "▼ down = priced ABOVE market."),
        ("Adjusted basis (Δ $)", "The dollar version of the adjustment: (Model $/SF − Going $/SF) × SqFt."),
        ("Implied cap (assumptions)", "NOI ÷ price, where NOI = SqFt × assumed rent × (1−vacancy) × (1−opex). Moves when you "
         "change assumptions."),
        ("Implied cap (data)", "Anchored to real rents & prices: (lease $/SF ÷ sale $/SF gross yield) × (1−vacancy) × (1−opex). "
         "A market-level proxy, not a specific building's cap."),
        ("Gross yield", "Annual asking lease $/SF ÷ sale $/SF — rent per dollar of price, before expenses."),
        ("Lease $/SF", "Asking rent per SqFt per year (rate basis inferred from the listing)."),
        ("Value / Comp value", "What comps or assumptions say it's worth — compare against the asking price."),
        ("Market share %", "What percentage a category (asset type, price bracket, size class) makes up of its parent — "
         "the whole market, an asset class, or a neighborhood."),
    ]:
        item(term, desc)
    sec("The brackets")
    item("Price brackets", "< $1M · $1–2.5M · $2.5–5M · $5–10M · $10M+")
    item("Size classes (SqFt)", "< 2.5K · 2.5–5K · 5–10K · 10–25K · 25–50K · 50K+  — the 'floor plan' analog "
         "(the export has no unit-mix / bed-bath data).")
    item("Multifamily unit brackets", "< 10 · 10–25 · 25–50 · 50–100 · 100+ units — only where a unit count could be "
         "parsed from the address (limited coverage).")
    sec("Confidence & flags")
    item("Confidence: High / Med / Indicative", "How many closed comps back a number (≥8 High, ≥4 Med, else Indicative). "
         "Treat 'Indicative' cells as directional.")
    item("Flag: Underpriced / Fair / Overpriced", "Asking vs value on the income lens (>10% under, within ±10%, >10% over).")
    item("Flag: Check", "Implied cap outside a plausible band — usually the SqFt or assumed rent is off; verify before quoting.")
    sec("How to recreate this for other properties")
    ws.merge_range(r[0], 0, r[0], 1, "The whole workbook + dashboard regenerate from a folder of CSVs. To analyze a "
                   "different set of properties (a new MLS pull, another market, or a specific list):", f["sub"])
    ws.set_row(r[0], 26); r[0] += 1
    for term, desc in [
        ("1. Export", "From the MLS, export the properties as a CSV in the 'Agent Single Line — COM' layout "
         "(or any CSV with the columns below)."),
        ("2. Add / replace the data", "Put your CSV(s) in  commercial/data/raw/. To fully replace, delete the old "
         "files; to UPDATE OVER TIME just add the newer pull — the tool reads every CSV and, for any listing that "
         "appears in more than one, keeps the most-progressed status and the NEWEST pull."),
        ("3. Run", "In a terminal from the commercial/ folder:  pip install -r requirements.txt   then   "
         "python analysis/run_all.py   (or double-click run.sh). ~30 seconds."),
        ("4. Open", "outputs/Commercial_Deal_Dashboard.xlsx  and  dashboard/index.html — everything is rebuilt on your data."),
        ("Columns it reads", "MLS #, St (status), Area, Address, Current Price, Sale Price, Year Built, Prop Type "
         "(Sale/Lease), Type of Property, Property SqFt, Waterfront (Y/N), #Bays. Different headers? Edit the mapping "
         "at the top of  analysis/cre_common.py."),
        ("Tune the assumptions", "Rents/vacancy/opex/cap live in  analysis/cre_assumptions.py  (or edit live on the "
         "dashboard). Refresh the market benchmarks in  analysis/market_context.py."),
    ]:
        item(term, desc)
    sec("Sources & freshness")
    item("Market benchmarks", f"Researched from CBRE, Colliers, JLL, Matthews, Yardi, The Real Deal, RSMeans/Turner/RLB, "
         f"LandSearch, Holland & Knight and others ({MKT.AS_OF}). Full list on the Market tab — refresh periodically.")
    item("Your data", f"Source: {', '.join(meta.get('sources', []))}. {meta.get('n_listings','')} listings, "
         f"{meta.get('n_sale_comps','')} priced sale comps.")


def segmentation_sheet(wb, f):
    sb = _load("segmentation_bundle.json")
    if not sb:
        return
    ws = wb.add_worksheet("Segmentation")
    _head(ws, f, "Segmentation & market share — by asset type, price bracket, size class",
          sb["meta"]["note"] + " Size class = SqFt bracket (no floor-plan data in the export).", 7)
    ws.set_column(0, 0, 22); ws.set_column(1, 8, 12)
    r = 3
    r = _comp_block(ws, f, sb["market"]["by_type"], "Asset type", r, "Market composition — by asset type")
    r = _comp_block(ws, f, sb["market"]["by_price"], "Price bracket", r, "Market composition — by price bracket")
    r = _comp_block(ws, f, sb["market"]["by_size"], "Size class (SqFt)", r, "Market composition — by size class")
    r = _matrix_block(ws, f, sb["matrix_type_price"], "Asset type × price bracket", r)
    r = _matrix_block(ws, f, sb["matrix_type_size"], "Asset type × size class (SqFt)", r)
    if sb.get("matrix_price_size"):
        r = _matrix_block(ws, f, sb["matrix_price_size"], "Price bracket × size class (which sizes trade in which price bands)", r)
    if sb.get("mf_unit_mix"):
        _comp_block(ws, f, sb["mf_unit_mix"], "Units",
                    r, f"Multifamily unit-count mix ({sb['meta'].get('mf_units_parsed',0)} parsed — limited coverage)")


def nbhd_mix_sheet(wb, f):
    sb = _load("segmentation_bundle.json")
    if not sb:
        return
    ws = wb.add_worksheet("Neighborhood Mix")
    _head(ws, f, "Neighborhood mix — what each area is made of",
          "Share is within the neighborhood: e.g. what % of Area X is each asset type / price bracket / size class.", 8)
    ws.set_column(0, 0, 16); ws.set_column(1, 11, 12)
    r = 3
    r = _matrix_block(ws, f, sb["matrix_nbhd_type"], "Neighborhood × asset type", r)
    r = _matrix_block(ws, f, sb["matrix_nbhd_price"], "Neighborhood × price bracket", r)
    r = _matrix_block(ws, f, sb["matrix_nbhd_size"], "Neighborhood × size class (SqFt)", r)


def main():
    cre = _load("cre_bundle.json")
    meta = cre["meta"]
    master = _load("master_bundle.json") or {"submarkets": cre["submarkets"]}
    reb, pros, seg = _load("reprice_bundle.json"), _load("prospects_bundle.json"), _load("segments_bundle.json")
    types = pd.DataFrame(cre["types"])
    seed = SC.seed()
    v = SC.compute(seed["price"], seed["sqft"], seed["rent_psf"], seed["vacancy"], seed["opex_ratio"],
                   seed["market_cap"], seed["ltv"], seed["rate"], seed["amort"], seed["shift_bps"],
                   seed["exit_cap"], seed["rent_growth"], seed["expense_growth"], seed["hold"],
                   seed["sell_pct"], seed["acq_pct"])

    wb = xlsxwriter.Workbook(OUT, {"nan_inf_to_errors": True})
    f = _fmts(wb)
    index_sheet(wb, f, meta)
    guide_sheet(wb, f, meta)
    key_sheet(wb, f, meta, master, reb, pros, seed, v)
    callist_sheet(wb, f)
    neighborhoods_sheet(wb, f)
    repricing_sheet(wb, f)
    segmentation_sheet(wb, f)
    nbhd_mix_sheet(wb, f)

    if reb and reb["opportunities"]:
        ws = wb.add_worksheet("Opportunities")
        _head(ws, f, "Underpriced opportunities", "The comp-backed buy list. 'Why' explains each.", 7)
        ws.set_column(0, 0, 24); ws.set_column(1, 5, 12); ws.set_column(6, 6, 60)
        _table(ws, f, pd.DataFrame(reb["opportunities"]),
               [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                ("price", "Asking", "usd"), ("assumed_value", "Value", "usd"),
                ("income_gap_pct", "Gap", "gap"), ("reason", "Why", "txt")])

    if pros:
        ws = wb.add_worksheet("Prospects")
        _head(ws, f, "Prospects — failed listings & overpriced actives", "Motivated owners to call.", 7)
        ws.set_column(0, 0, 22); ws.set_column(1, 6, 12)
        _table(ws, f, pd.DataFrame(pros["failed"]),
               [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                ("price", "Last ask", "usd"), ("ppsf", "$/SqFt", "usd"),
                ("pred_ppsf", "Comp $/SqFt", "usd"), ("ppsf_gap_pct", "Overpricing", "gap")])

    lb = _load("leases_bundle.json")
    if lb:
        ws = wb.add_worksheet("Leasing")
        _head(ws, f, "Leasing — asking rents & data-derived caps",
              f"{lb['meta']['n_lease_rated']} lease listings ({lb['meta']['n_active_lease']} active, "
              f"{lb['meta']['n_leased']} leased). Implied cap = (lease÷sale gross yield) × (1−vac) × (1−opex).", 8)
        ws.set_column(0, 0, 18); ws.set_column(1, 8, 12)
        _table(ws, f, pd.DataFrame(lb["by_type"]),
               [("asset_type", "Type", "txt"), ("lease_psf", "Lease $/SF", "usd"),
                ("lease_p25", "P25", "usd"), ("lease_p75", "P75", "usd"), ("n_lease", "n", "num"),
                ("sale_psf", "Sale $/SF", "usd"), ("gross_yield", "Gross yld", "pct2"),
                ("implied_cap_data", "Implied cap", "pct2"), ("assumed_cap", "Assumed cap", "pct2")])
        sub = pd.DataFrame(lb["by_submarket"])
        if len(sub):
            start = 3 + len(lb["by_type"]) + 3
            ws.write(start - 1, 0, "Lease $/SqFt by submarket", f["title"])
            _table(ws, f, sub, [("submarket", "Submarket", "txt"), ("corridors", "Corridors", "txt"),
                                ("lease_psf", "Lease $/SF", "usd"), ("n_lease", "n", "num"),
                                ("n_active", "Active", "num"), ("n_leased", "Leased", "num"),
                                ("sale_psf", "Sale $/SF", "usd"), ("gross_yield", "Gross yld", "pct2")],
                   start=start)

    if os.path.exists(os.path.join(CRE.PROC, "comps_flat.csv")):
        ws = wb.add_worksheet("Comps")
        _head(ws, f, "Closed comps", "The closed sales behind every $/SqFt number.", 8)
        ws.set_column(0, 0, 24); ws.set_column(1, 8, 12)
        _table(ws, f, pd.read_csv(os.path.join(CRE.PROC, "comps_flat.csv")),
               [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                ("sqft", "SqFt", "num"), ("year_built", "Built", "num"), ("price", "Price", "usd"),
                ("ppsf", "$/SqFt", "usd"), ("ppsf_gap_pct", "vs model", "gap")])

    market_sheet(wb, f)
    assumptions_sheet(wb, f, types)
    scenario_sheet(wb, f, seed)

    ws = wb.add_worksheet("Types")
    _head(ws, f, "Asset types — $/SqFt & assumed income", "Median $/SqFt (factual) + default assumptions.", 10)
    ws.set_column(0, 0, 18); ws.set_column(1, 10, 12)
    _table(ws, f, types.reset_index(),
           [("asset_type", "Type", "txt"), ("confidence", "Conf", "txt"),
            ("median_ppsf", "Median $/SqFt", "usd"), ("n", "n", "num"), ("n_sold", "Sold", "num"),
            ("assume_rent_psf", "Rent $/SqFt", "usd"), ("market_rent_psf", "Mkt rent", "usd"),
            ("assume_vacancy", "Vac", "pct0"), ("assume_opex_ratio", "Opex", "pct0"),
            ("assume_cap_rate", "Mkt cap", "pct2"), ("typical_implied_cap", "Implied cap", "pct2")])

    if seg:
        ws = wb.add_worksheet("Absorption")
        _head(ws, f, "Absorption & segments", seg["meta"]["absorption_note"], 8)
        ws.set_column(0, 0, 18); ws.set_column(1, 7, 12)
        _table(ws, f, pd.DataFrame(seg["by_type"]),
               [("asset_type", "Type", "txt"), ("n", "n", "num"), ("n_sold", "Sold", "num"),
                ("n_live", "Live", "num"), ("median_ppsf", "Median $/SqFt", "usd"),
                ("months_supply", "Mo supply", "num1")])

    wb.close()
    print(f"Workbook -> {os.path.relpath(OUT, CRE.ROOT)} ({len(wb.worksheets())} tabs)")


if __name__ == "__main__":
    main()
