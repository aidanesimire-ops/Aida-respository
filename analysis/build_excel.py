#!/usr/bin/env python3
"""
Build the formatted Excel workbook from the processed tables.
Run after normalize_ppsf.py. Output: outputs/Fort_Lauderdale_PPSF_Normalized.xlsx
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)
XLSX = os.path.join(OUT, "Fort_Lauderdale_PPSF_Normalized.xlsx")

BLUE = "#2a78d6"
DARK = "#0d366b"


def _bundle():
    with open(os.path.join(PROC, "analysis_bundle.json")) as f:
        return json.load(f)


def _mls():
    with open(os.path.join(PROC, "mls_bundle.json")) as f:
        return json.load(f)


def _street():
    with open(os.path.join(PROC, "street_bundle.json")) as f:
        return json.load(f)


# columns: (source_field, header, excel_num_format, width)
HEADLINE_COLS = [
    ("value_rank", "Rank", "0", 6),
    ("neighborhood", "Neighborhood", None, 30),
    ("norm_ppsf", "Normalized $/sqft", "$#,##0", 16),
    ("vs_city_pct", "vs City", '+0"%";-0"%"', 10),
    ("raw_ppsf_recent", "Recent raw $/sqft", "$#,##0", 15),
    ("norm_dom", "Norm. days on mkt", "0", 15),
    ("discount_pct", "Discount to list", '0.0"%"', 14),
    ("ppsf_cagr", "Appreciation (CAGR)", "0.0%", 16),
    ("buyer_leverage", "Buyer leverage", "0.00", 13),
    ("sample_txns", "Sample (txns)", "#,##0", 12),
    ("confidence", "Confidence", None, 12),
]
TYPE_COLS = [
    ("neighborhood", "Neighborhood", None, 30),
    ("norm_ppsf", "Normalized $/sqft", "$#,##0", 16),
    ("vs_city_pct", "vs City", '+0"%";-0"%"', 10),
    ("raw_ppsf_recent", "Recent raw $/sqft", "$#,##0", 15),
    ("ppsf_cagr", "Appreciation (CAGR)", "0.0%", 16),
    ("discount_pct", "Discount to list", '0.0"%"', 14),
    ("months_supply", "Months of supply", "0.0", 14),
    ("sample_txns", "Sample (txns)", "#,##0", 12),
    ("confidence", "Confidence", None, 12),
]


def write_table(wb, ws, df, cols, fmts, title, subtitle):
    ws.set_column(0, 0, 6)
    ws.write(0, 0, title, fmts["title"])
    ws.write(1, 0, subtitle, fmts["sub"])
    top = 3
    for c, (_, header, _, width) in enumerate(cols):
        ws.write(top, c, header, fmts["hdr"])
        ws.set_column(c, c, width)
    for r, (_, row) in enumerate(df.iterrows()):
        xr = top + 1 + r
        for c, (field, _, numfmt, _) in enumerate(cols):
            val = row.get(field)
            key = ("num", numfmt) if numfmt else ("txt", None)
            fmt = fmts["cells"].get(key)
            if pd.isna(val):
                ws.write(xr, c, "", fmts["cells"][("txt", None)])
            elif numfmt:
                ws.write_number(xr, c, float(val), fmt)
            else:
                ws.write(xr, c, str(val), fmt)
    ws.freeze_panes(top + 1, 0)
    ws.autofilter(top, 0, top + len(df), len(cols) - 1)
    return top


def make_formats(wb):
    cells = {}
    numfmts = set()
    for cols in (HEADLINE_COLS, TYPE_COLS):
        for _, _, nf, _ in cols:
            numfmts.add(nf)
    for nf in numfmts:
        if nf:
            cells[("num", nf)] = wb.add_format(
                {"num_format": nf, "border": 1, "border_color": "#e1e0d9",
                 "align": "center"})
    cells[("txt", None)] = wb.add_format(
        {"border": 1, "border_color": "#e1e0d9", "align": "left"})
    return {
        "title": wb.add_format({"bold": True, "font_size": 15, "font_color": DARK}),
        "sub": wb.add_format({"font_size": 10, "font_color": "#898781", "italic": True}),
        "hdr": wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE,
                              "border": 1, "border_color": "white", "align": "center",
                              "valign": "vcenter", "text_wrap": True}),
        "cells": cells,
    }


def readme_sheet(wb, meta):
    ws = wb.add_worksheet("Read Me")
    ws.set_column(0, 0, 100)
    h = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    sub = wb.add_format({"bold": True, "font_size": 12, "font_color": BLUE})
    p = wb.add_format({"font_size": 10, "text_wrap": True, "valign": "top"})
    ws.set_default_row(15)
    mm = _mls()["meta"]
    pr = mm["premiums"]
    lines = [
        (h, "Fort Lauderdale — Normalized Price/SqFt by Neighborhood"),
        (p, "Two data layers, cross-validated against each other (r = 0.93):"),
        (p, f"  1) PRIMARY — a per-home hedonic model on {mm['n_sold']:,} closed MLS sales "
            f"({mm['n_listings']:,} total listings across sold, expired, withdrawn, cancelled, "
            f"temp-off, active and pending). Model R-squared = {mm['hedonic_r2']}."),
        (p, f"  2) CONTEXT — Redfin Data Center neighborhood aggregates "
            f"({meta['generated_span'][0]}–{meta['generated_span'][1]}) supply the time / "
            f"appreciation index and days-on-market the MLS export lacks."),
        (p, ""),
        (sub, "What 'normalized' means"),
        (p, "Raw $/sqft is confounded by home size, property type, age, whether it's on "
            "the water, and when it sold. The hedonic model regresses log($/sqft) on living "
            "area, beds, baths, waterfront, pool, age, new-construction and property type "
            "with a neighborhood fixed effect. 'Normalized $/sqft' is then the model's price "
            "for ONE standardized home — a dry-lot, no-pool home of citywide-median size and "
            f"age (~{mm['standardized_home']['sqft']:,} sqft, {round(mm['standardized_home']['age'])} "
            "yrs) — placed in each neighborhood. That isolates location; everything else is "
            "reported separately as a premium."),
        (p, ""),
        (sub, "Price drivers (per-home model, all else equal)"),
        (p, f"  • Waterfront: +{pr['waterfront_pct']}%   • Private pool: +{pr['pool_pct']}%   "
            f"• New construction: +{pr['new_construction_pct']}%"),
        (p, f"  • Each decade older: {pr['age_per_decade_pct']}%   • Size elasticity: "
            f"{pr['size_elasticity']} (bigger homes = lower $/sqft)"),
        (p, f"  • Implied land value citywide: ~${_mls()['meta']['city_land_ppsf']:,.0f} per "
            "sqft of lot (from the SFR structure-vs-land model)."),
        (p, ""),
        (sub, "Column definitions"),
        (p, "Normalized $/sqft — model price for the standardized home; compare directly "
            "across neighborhoods. Waterfront $/sqft & Dry $/sqft — actual median sale $/sqft "
            "of waterfront vs non-waterfront homes IN that neighborhood. New vs Existing $/sqft "
            "— median for homes <=6 yrs old vs older. House/Condo/Townhouse $/sqft — median by "
            "type. Implied land $/sqft — land value per sqft of lot. Discount — actual median "
            "list-to-sale. Failure rate — failed listings / (failed + sold)."),
        (p, ""),
        (sub, "Validation & honest limits"),
        (p, "Addresses were spot-checked against public records: the top sales (5 Harborage "
            "Isle $70M, 84 Isla Bahia $34M, 2406 Laguna $26M) match to the dollar on price, "
            "sqft and year built. Data is 100% address-complete, ~98% valid sqft/year. LIMITS: "
            "the export has no lot-geography detail (point vs corner vs canal vs ocean-access) "
            "and no dates/days-on-market — add those MLS columns to sharpen further. Condo-level "
            "flags are coarse (floor/view/renovation unobserved). These are neighborhood "
            "benchmarks and screening signals, not per-home appraisals."),
    ]
    r = 0
    for fmt, text in lines:
        ws.write(r, 0, text, fmt)
        r += 2 if fmt in (h, sub) else 1
    ws.hide_gridlines(2)


def market_index_sheet(wb, fmts, mi):
    ws = wb.add_worksheet("Market Index")
    ws.write(0, 0, "Fort Lauderdale market appreciation index", fmts["title"])
    ws.write(1, 0, "Quality-adjusted PPSF, 100 = first month. From hedonic month effects.",
             fmts["sub"])
    ws.write(3, 0, "Month", fmts["hdr"])
    ws.write(3, 1, "Index (100 = base)", fmts["hdr"])
    ws.set_column(0, 0, 14)
    ws.set_column(1, 1, 20)
    numf = wb.add_format({"num_format": "0.0", "border": 1, "border_color": "#e1e0d9",
                          "align": "center"})
    txt = wb.add_format({"border": 1, "border_color": "#e1e0d9"})
    for i, row in enumerate(mi):
        ws.write(4 + i, 0, row["month_key"], txt)
        ws.write_number(4 + i, 1, row["index_100"], numf)
    ws.freeze_panes(4, 0)
    chart = wb.add_chart({"type": "line"})
    n = len(mi)
    chart.add_series({
        "categories": ["Market Index", 4, 0, 3 + n, 0],
        "values": ["Market Index", 4, 1, 3 + n, 1],
        "line": {"color": BLUE, "width": 2.0},
        "name": "PPSF index",
    })
    chart.set_title({"name": "Quality-adjusted PPSF index"})
    chart.set_legend({"none": True})
    chart.set_size({"width": 720, "height": 360})
    ws.insert_chart(3, 3, chart)


MLS_COLS = [
    ("rank", "Rank", "0", 6),
    ("neighborhood", "Neighborhood", None, 26),
    ("basis_type", "Basis", None, 13),
    ("geo_type", "Geography", None, 26),
    ("norm_ppsf", "Norm. $/sqft", "$#,##0", 13),
    ("vs_city_pct", "vs City", '+0"%";-0"%"', 9),
    ("sold_ppsf_median", "Median sold $/sqft", "$#,##0", 15),
    ("house_ppsf", "House $/sqft", "$#,##0", 12),
    ("condo_ppsf", "Condo $/sqft", "$#,##0", 12),
    ("townhouse_ppsf", "Townhome $/sqft", "$#,##0", 13),
    ("waterfront_ppsf", "Waterfront $/sqft", "$#,##0", 14),
    ("dry_ppsf", "Dry-lot $/sqft", "$#,##0", 13),
    ("waterfront_premium_local_pct", "WF premium", '+0"%";-0"%"', 10),
    ("new_ppsf", "New $/sqft", "$#,##0", 12),
    ("existing_ppsf", "Existing $/sqft", "$#,##0", 13),
    ("new_premium_pct", "New premium", '+0"%";-0"%"', 11),
    ("implied_land_ppsf", "Land $/sqft-lot", "$#,##0", 13),
    ("median_sale_price", "Median price", "$#,##0", 14),
    ("median_discount_pct", "Discount", '0.0"%"', 10),
    ("failure_rate", "Failure rate", '0"%"', 11),
    ("sold_n", "Sold n", "#,##0", 9),
]
DEAL_COLS = [
    ("neighborhood", "Neighborhood", None, 24),
    ("status", "Status", None, 10),
    ("list_price", "List price", "$#,##0", 14),
    ("sqft", "SqFt", "#,##0", 9),
    ("ask_ppsf", "Ask $/sqft", "$#,##0", 12),
    ("pred_ppsf", "Model $/sqft", "$#,##0", 13),
    ("gap_pct", "Gap vs model", '0.0"%"', 12),
    ("waterfront", "Waterfront", None, 11),
]


def mls_ranking_sheet(wb, fmts, mm):
    df = pd.DataFrame(mm["neighborhoods"]).sort_values("norm_ppsf", ascending=False)
    df.insert(0, "rank", range(1, len(df) + 1))
    ws = wb.add_worksheet("Normalized Ranking")
    write_table(wb, ws, df, MLS_COLS, fmts,
                "Per-home normalized $/sqft — every neighborhood, every angle",
                "Normalized = model price for a standardized dry-lot home. Waterfront/New/type "
                "columns are actual medians. Source: MLS closed sales.")
    ws.hide_gridlines(2)
    n = len(df)
    ws.conditional_format(4, 4, 3 + n, 4, {"type": "3_color_scale",
        "min_color": "#e8f1fc", "mid_color": "#86b6ef", "max_color": BLUE})
    ws.conditional_format(4, 10, 3 + n, 10, {"type": "3_color_scale",
        "min_color": "#eaf4fb", "mid_color": "#7fb6e0", "max_color": "#0d3b66"})


def mls_profiles_sheet(wb, mm):
    ws = wb.add_worksheet("Neighborhood Profiles")
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "font_color": "#898781", "italic": True})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE,
                         "border": 1, "border_color": "white", "valign": "vcenter"})
    nbf = wb.add_format({"bold": True, "font_size": 11, "valign": "top",
                         "border": 1, "border_color": "#e1e0d9", "text_wrap": True})
    tpf = wb.add_format({"font_size": 10, "valign": "top", "text_wrap": True,
                         "border": 1, "border_color": "#e1e0d9"})
    ws.write(0, 0, "Neighborhood talking points", title)
    ws.write(1, 0, "Copy-ready, data-backed context for homeowner conversations. "
             "One row per neighborhood.", sub)
    ws.write(3, 0, "Neighborhood", hdr)
    ws.write(3, 1, "Talking points", hdr)
    ws.set_column(0, 0, 24)
    ws.set_column(1, 1, 120)
    profiles = sorted(mm["profiles"], key=lambda p: p["neighborhood"])
    for i, prof in enumerate(profiles):
        row = 4 + i
        ws.write(row, 0, prof["neighborhood"], nbf)
        ws.write(row, 1, "• " + "\n• ".join(prof["talking_points"]), tpf)
        ws.set_row(row, 15 * max(3, len(prof["talking_points"])))
    ws.freeze_panes(4, 0)
    ws.hide_gridlines(2)


def mls_drivers_sheet(wb, mm):
    ws = wb.add_worksheet("Price Drivers")
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "font_color": "#898781", "italic": True})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1})
    lab = wb.add_format({"border": 1, "border_color": "#e1e0d9"})
    val = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "center",
                         "bold": True, "num_format": '+0.0"%";-0.0"%"'})
    meta = mm["meta"]
    pr = meta["premiums"]
    ws.write(0, 0, "What drives Fort Lauderdale home value", title)
    ws.write(1, 0, "Marginal effect on price per square foot, all else equal "
             f"(per-home hedonic, R²={meta['hedonic_r2']}).", sub)
    ws.set_column(0, 0, 34)
    ws.set_column(1, 1, 16)
    ws.write(3, 0, "Driver", hdr)
    ws.write(3, 1, "Effect", hdr)
    rows = [("Waterfront (vs dry lot)", pr["waterfront_pct"]),
            ("Private pool", pr["pool_pct"]),
            ("New construction (<=6 yrs, net of age)", pr["new_construction_pct"]),
            ("Each additional bathroom", pr["bath_pct"]),
            ("Each decade of age", pr["age_per_decade_pct"])]
    for i, (k, v) in enumerate(rows):
        ws.write(4 + i, 0, k, lab)
        ws.write_number(4 + i, 1, v / 100.0, val)
    r = 4 + len(rows) + 1
    txt = wb.add_format({"font_size": 10, "text_wrap": True, "valign": "top"})
    ws.write(r, 0, f"Size elasticity {pr['size_elasticity']} — a home twice as large sells "
             f"for about {(2**pr['size_elasticity']-1)*100:.0f}% more total, i.e. lower $/sqft. "
             f"Implied land value ~${meta['city_land_ppsf']:,.0f}/sqft of lot citywide.", txt)
    ws.set_row(r, 46)
    ws.hide_gridlines(2)


def mls_deals_sheet(wb, fmts, mm):
    df = pd.DataFrame(mm["deals"])
    ws = wb.add_worksheet("Live Deals")
    if len(df):
        write_table(wb, ws, df, DEAL_COLS, fmts,
                    "Live single-family listings priced below the model",
                    "Active/pending homes whose asking $/sqft is 8–38% under predicted market "
                    "value. Screening candidates to investigate — verify condition on site.")
        ws.conditional_format(4, 6, 3 + len(df), 6, {"type": "3_color_scale",
            "min_color": "#0f8a3c", "mid_color": "#8fd48f", "max_color": "#eafaea"})
    else:
        ws.write(0, 0, "No single-family deal candidates in the current set.", fmts["title"])
    ws.hide_gridlines(2)


STREET_COLS = [
    ("street", "Street", None, 22),
    ("neighborhood", "Neighborhood", None, 22),
    ("geo_type", "Geography", None, 24),
    ("sold_ppsf", "Sold $/sqft", "$#,##0", 12),
    ("model_ppsf", "Model $/sqft", "$#,##0", 12),
    ("premium_vs_nbhd", "vs Neighborhood", '+0"%";-0"%"', 14),
    ("waterfront_share", "Waterfront", "0%", 11),
    ("median_price", "Median price", "$#,##0", 14),
    ("n_sold", "Sold", "#,##0", 8),
    ("n_active", "Active", "#,##0", 8),
]
DEAL_UW_COLS = [
    ("address", "Address", None, 26),
    ("street", "Street", None, 18),
    ("neighborhood", "Neighborhood", None, 20),
    ("ptype", "Type", None, 13),
    ("sqft", "SqFt", "#,##0", 8),
    ("list_price", "List price", "$#,##0", 13),
    ("ask_ppsf", "Ask $/sqft", "$#,##0", 11),
    ("street_value_ppsf", "Street value $/sqft", "$#,##0", 16),
    ("street_comps", "Comps", "#,##0", 8),
    ("gap_vs_street", "Gap vs street", '0.0"%"', 12),
    ("flag", "Flag", None, 12),
]


def street_sheets(wb, fmts, sb):
    st = pd.DataFrame(sb["streets"]).sort_values("sold_ppsf", ascending=False)
    ws = wb.add_worksheet("Street Value")
    write_table(wb, ws, st, STREET_COLS, fmts,
                "Street-by-street value (>= {} closed sales)".format(sb["meta"]["min_street_sold"]),
                "Sold $/sqft per street and its premium/discount vs the surrounding "
                "neighborhood. Source: MLS closed sales.")
    ws.hide_gridlines(2)
    n = len(st)
    ws.conditional_format(4, 3, 3 + n, 3, {"type": "3_color_scale",
        "min_color": "#e8f1fc", "mid_color": "#86b6ef", "max_color": BLUE})
    ws.conditional_format(4, 5, 3 + n, 5, {"type": "3_color_scale",
        "min_color": "#e34948", "mid_color": "#f0efec", "max_color": "#0f8a3c"})

    deals = pd.DataFrame(sb["deals"])
    ws2 = wb.add_worksheet("Deal Underwriting")
    if len(deals):
        write_table(wb, ws2, deals, DEAL_UW_COLS, fmts,
                    "Live single-family listings priced below their street value",
                    "Asking $/sqft vs a street-comp-adjusted model value (>= {} comps on the "
                    "street). Screening candidates — verify condition on site.".format(
                        sb["meta"]["min_street_sold"]))
        ws2.conditional_format(4, 9, 3 + len(deals), 9, {"type": "3_color_scale",
            "min_color": "#0f8a3c", "mid_color": "#8fd48f", "max_color": "#eafaea"})
    else:
        ws2.write(0, 0, "No comp-backed single-family deal candidates right now.", fmts["title"])
    ws2.hide_gridlines(2)


def main():
    b = _bundle()
    meta = b["meta"]
    head = pd.DataFrame(b["headline"]).sort_values("norm_ppsf", ascending=False)
    condo = pd.DataFrame(b["condo"]).sort_values("norm_ppsf", ascending=False)
    town = pd.DataFrame(b["townhouse"]).sort_values("norm_ppsf", ascending=False)
    lev = head.sort_values("buyer_leverage", ascending=False)
    appr = head.dropna(subset=["ppsf_cagr"]).sort_values("ppsf_cagr", ascending=False)

    mm = _mls()
    wb_writer = pd.ExcelWriter(XLSX, engine="xlsxwriter")
    wb = wb_writer.book
    fmts = make_formats(wb)

    readme_sheet(wb, meta)

    # ---- PRIMARY: MLS per-home layer ----
    mls_profiles_sheet(wb, mm)
    mls_ranking_sheet(wb, fmts, mm)
    mls_drivers_sheet(wb, mm)
    mls_deals_sheet(wb, fmts, mm)
    try:
        street_sheets(wb, fmts, _street())
    except FileNotFoundError:
        pass

    # ---- CONTEXT: Redfin time/appreciation layer ----
    ws = wb.add_worksheet("SFR Rankings (Redfin)")
    write_table(wb, ws, head, HEADLINE_COLS, fmts,
                "Single-Family — normalized price/sqft ranking",
                f"Sorted by normalized $/sqft. Citywide normalized avg "
                f"${meta['city_norm_ppsf_sfr']:,.0f}/sqft. Source: Redfin Data Center.")
    ws.hide_gridlines(2)
    # color scale on normalized ppsf column (index 2)
    n = len(head)
    ws.conditional_format(4, 2, 3 + n, 2,
                          {"type": "3_color_scale", "min_color": "#e8f1fc",
                           "mid_color": "#86b6ef", "max_color": BLUE})
    ws.conditional_format(4, 6, 3 + n, 6,
                          {"type": "data_bar", "bar_color": "#eb6834"})

    for name, df, title in [
        ("Condo Rankings", condo, "Condo/Co-op — normalized price/sqft ranking"),
        ("Townhouse Rankings", town, "Townhouse — normalized price/sqft ranking"),
    ]:
        ws = wb.add_worksheet(name)
        write_table(wb, ws, df, TYPE_COLS, fmts, title,
                    "Sorted by normalized $/sqft. Source: Redfin Data Center.")
        ws.hide_gridlines(2)
        ws.conditional_format(4, 1, 3 + len(df), 1,
                              {"type": "3_color_scale", "min_color": "#e8f1fc",
                               "mid_color": "#86b6ef", "max_color": BLUE})

    ws = wb.add_worksheet("Buyer Leverage")
    write_table(wb, ws, lev, HEADLINE_COLS, fmts,
                "Where buyers have negotiating leverage",
                "Sorted by buyer-leverage score (DOM + discount + price drops + supply).")
    ws.hide_gridlines(2)
    ws.conditional_format(4, 8, 3 + len(lev), 8,
                          {"type": "3_color_scale", "min_color": "#fde8e8",
                           "mid_color": "#f6b6b6", "max_color": "#e34948"})

    ws = wb.add_worksheet("Appreciation")
    write_table(wb, ws, appr, HEADLINE_COLS, fmts,
                "Fastest-appreciating neighborhoods",
                "Sorted by annualized PPSF growth (CAGR).")
    ws.hide_gridlines(2)
    ws.conditional_format(4, 7, 3 + len(appr), 7,
                          {"type": "3_color_scale", "min_color": "#e8f7e8",
                           "mid_color": "#8fd48f", "max_color": "#0ca30c"})

    market_index_sheet(wb, fmts, b["market_index"])

    wb_writer.close()
    print("Wrote", XLSX)


if __name__ == "__main__":
    main()
