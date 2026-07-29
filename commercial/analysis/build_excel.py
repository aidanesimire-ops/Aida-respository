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
    f["cell"] = wb.add_format({"border": 1, "border_color": "#ecebe4"})
    return f


def _table(ws, f, df, spec, start=3):
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


def index_sheet(wb, f, meta):
    ws = wb.add_worksheet("Index")
    ws.set_column(0, 0, 22); ws.set_column(1, 1, 86)
    ws.write(0, 0, "Commercial Deal Dashboard — Fort Lauderdale", f["title"])
    ws.merge_range(1, 0, 1, 1, f"Sources: {', '.join(meta['sources'])}. No income in source — "
                   "income metrics are assumption-driven (see Assumptions tab). Click a tab.", f["sub"])
    ws.set_row(1, 28)
    toc = [("Key Conclusions", "Headline takeaways."),
           ("Assumptions", "Editable income norms by asset type — the gap-fill."),
           ("Submarkets", "Normalized $/SqFt by MLS area, ranked."),
           ("Types", "$/SqFt + assumed income by asset class."),
           ("Repricing", "Live inventory: $/SqFt & income mispricing."),
           ("Opportunities", "Underpriced buy list (default assumptions)."),
           ("Absorption", "Months of supply by submarket & type."),
           ("Prospects", "Failed listings + overpriced actives."),
           ("Comps", "The closed sales behind the numbers."),
           ("Scenario", "Live underwriting — NOI built from assumptions.")]
    link = wb.add_format({"font_color": BLUE, "bold": True, "underline": 1, "border": 1, "border_color": "#e1e0d9"})
    for i, (name, desc) in enumerate(toc):
        r = 3 + i
        ws.write_url(r, 0, f"internal:'{name}'!A1", link, name)
        ws.write(r, 1, desc, f["txt"]); ws.set_row(r, 22)


def key_sheet(wb, f, meta, master, reb, pros, seed, v):
    ws = wb.add_worksheet("Key Conclusions")
    ws.set_column(0, 0, 3); ws.set_column(1, 1, 108)
    ws.write(0, 1, "Key conclusions", f["title"])
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
    key_sheet(wb, f, meta, master, reb, pros, seed, v)
    assumptions_sheet(wb, f, types)

    ws = wb.add_worksheet("Submarkets")
    _head(ws, f, "Submarkets — normalized $/SqFt", "Size/age/type/closed-vs-listed removed.", 8)
    ws.set_column(0, 0, 16); ws.set_column(1, 8, 13)
    _table(ws, f, pd.DataFrame(master["submarkets"]),
           [("submarket", "Submarket", "txt"), ("norm_ppsf", "Norm $/SqFt", "usd"),
            ("vs_city_pct", "vs city %", "gap"), ("median_price", "Median price", "usd"),
            ("top_asset", "Top type", "txt"), ("months_supply", "Mo supply", "num1"),
            ("failure_rate_pct", "Fail %", "num1"), ("stance", "Stance", "txt")])

    ws = wb.add_worksheet("Types")
    _head(ws, f, "Asset types — $/SqFt & assumed income", "Median $/SqFt (factual) + default assumptions.", 8)
    ws.set_column(0, 0, 18); ws.set_column(1, 9, 12)
    _table(ws, f, types.reset_index(),
           [("asset_type", "Type", "txt"), ("confidence", "Conf", "txt"),
            ("median_ppsf", "Median $/SqFt", "usd"), ("n", "n", "num"), ("n_sold", "Sold", "num"),
            ("assume_rent_psf", "Rent $/SqFt", "usd"), ("market_rent_psf", "Mkt rent", "usd"),
            ("assume_vacancy", "Vac", "pct0"), ("assume_opex_ratio", "Opex", "pct0"),
            ("assume_cap_rate", "Mkt cap", "pct2"), ("typical_implied_cap", "Implied cap", "pct2")])

    if reb:
        ws = wb.add_worksheet("Repricing")
        _head(ws, f, "Repricing live inventory", "Income flags use DEFAULT assumptions — tune live in the dashboard.", 11)
        ws.set_column(0, 0, 20); ws.set_column(1, 11, 12)
        inv = pd.DataFrame(reb["inventory"])
        _table(ws, f, inv, [("address", "Address", "txt"), ("submarket", "Area", "txt"),
                            ("asset_type", "Type", "txt"), ("price", "Asking", "usd"),
                            ("ppsf", "$/SqFt", "usd"), ("ppsf_gap_pct", "vs comp", "gap"),
                            ("implied_cap", "Impl cap", "pct2"), ("market_cap", "Mkt cap", "pct2"),
                            ("assumed_value", "Value", "usd"), ("income_gap_pct", "Gap", "gap"),
                            ("flag", "Flag", "txt")])
        if reb["opportunities"]:
            ws = wb.add_worksheet("Opportunities")
            _head(ws, f, "Underpriced opportunities", "Income basis, default assumptions. 'Why' explains each.", 7)
            ws.set_column(0, 0, 22); ws.set_column(1, 5, 12); ws.set_column(6, 6, 58)
            _table(ws, f, pd.DataFrame(reb["opportunities"]),
                   [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                    ("price", "Asking", "usd"), ("assumed_value", "Value", "usd"),
                    ("income_gap_pct", "Gap", "gap"), ("reason", "Why", "txt")])

    if seg:
        ws = wb.add_worksheet("Absorption")
        _head(ws, f, "Absorption & segments", seg["meta"]["absorption_note"], 8)
        ws.set_column(0, 0, 18); ws.set_column(1, 7, 12)
        _table(ws, f, pd.DataFrame(seg["by_type"]),
               [("asset_type", "Type", "txt"), ("n", "n", "num"), ("n_sold", "Sold", "num"),
                ("n_live", "Live", "num"), ("median_ppsf", "Median $/SqFt", "usd"),
                ("months_supply", "Mo supply", "num1")])

    if pros:
        ws = wb.add_worksheet("Prospects")
        _head(ws, f, "Prospecting", "Failed listings (motivated owners) + failure rate by type.", 7)
        ws.set_column(0, 0, 20); ws.set_column(1, 6, 12)
        _table(ws, f, pd.DataFrame(pros["failed"]),
               [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                ("price", "Last ask", "usd"), ("ppsf", "$/SqFt", "usd"),
                ("pred_ppsf", "Comp $/SqFt", "usd"), ("ppsf_gap_pct", "Overpricing", "gap")])

    comps = _load("comps_bundle.json")
    if comps and os.path.exists(os.path.join(CRE.PROC, "comps_flat.csv")):
        ws = wb.add_worksheet("Comps")
        _head(ws, f, "Closed comps", "The closed sales behind every $/SqFt number.", 8)
        ws.set_column(0, 0, 22); ws.set_column(1, 8, 12)
        _table(ws, f, pd.read_csv(os.path.join(CRE.PROC, "comps_flat.csv")),
               [("address", "Address", "txt"), ("submarket", "Area", "txt"), ("asset_type", "Type", "txt"),
                ("sqft", "SqFt", "num"), ("year_built", "Built", "num"), ("price", "Price", "usd"),
                ("ppsf", "$/SqFt", "usd"), ("ppsf_gap_pct", "vs model", "gap")])

    assumptions_seed = seed
    scenario_sheet(wb, f, assumptions_seed)
    wb.close()
    print(f"Workbook -> {os.path.relpath(OUT, CRE.ROOT)}")


if __name__ == "__main__":
    main()
