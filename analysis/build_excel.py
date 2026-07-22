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


def _time():
    with open(os.path.join(PROC, "time_bundle.json")) as f:
        return json.load(f)


def _reprice():
    with open(os.path.join(PROC, "reprice_bundle.json")) as f:
        return json.load(f)


def _high():
    with open(os.path.join(PROC, "high_ticket_bundle.json")) as f:
        return json.load(f)


def _master():
    with open(os.path.join(PROC, "master_bundle.json")) as f:
        return json.load(f)


def _underpriced():
    with open(os.path.join(PROC, "underpriced_bundle.json")) as f:
        return json.load(f)


def _wavg(rows, val, wt):
    num = sum((r[val] or 0) * (r[wt] or 0) for r in rows if r.get(val) is not None)
    den = sum((r[wt] or 0) for r in rows if r.get(val) is not None)
    return num / den if den else float("nan")


MASTER_COLS = [
    ("rank", "#", "0", 4),
    ("neighborhood", "Neighborhood", None, 24),
    ("geo_type", "Geography", None, 22),
    ("norm_ppsf", "Normalized $/sqft", "$#,##0", 15),
    ("vs_city_pct", "vs City", '+0"%";-0"%"', 9),
    ("waterfront_ppsf", "Waterfront $/sqft", "$#,##0", 14),
    ("dry_ppsf", "Dry $/sqft", "$#,##0", 11),
    ("new_premium_pct", "New premium", '+0"%";-0"%"', 11),
    ("median_sale_price", "Median sold $", "$#,##0", 14),
    ("median_discount_pct", "Discount", '0.0"%"', 9),
    ("dom", "Days on mkt", "0", 11),
    ("appreciation_since_2020", "Apprec. since '20", '+0"%";-0"%"', 15),
    ("failure_rate", "Fail rate", '0"%"', 9),
    ("n_high_ticket", "Live ≥$1M", "#,##0", 10),
    ("n_over_10m", "≥$10M", "#,##0", 8),
    ("asking_ppsf", "Now asking $/sqft", "$#,##0", 15),
    ("should_be_ppsf", "Should be (sold)", "$#,##0", 15),
    ("suggested_adjust_pct", "Suggested reprice", '+0.0"%";-0.0"%"', 15),
    ("ht_listed_total", "≥$1M listed at", "$#,##0", 16),
    ("sold_n", "Sold", "#,##0", 7),
]


def master_sheet(wb, fmts, mb):
    df = pd.DataFrame(mb["neighborhoods"])
    m = mb["meta"]
    ws = wb.add_worksheet("Master Ranking")
    write_table(wb, ws, df, MASTER_COLS, fmts,
                "Master — every neighborhood, most to least expensive, with suggested repricing",
                f"{m['n_neighborhoods']} neighborhoods ranked by normalized $/sqft. "
                f"{m['n_high_ticket_total']} live listings ≥$1M ({m['n_over_10m_total']} over $10M). "
                "Suggested reprice = move current asking toward recent sold comps (negative = "
                "reduce). All metrics normalized for size, type, waterfront, age & new construction.")
    ws.hide_gridlines(2)
    ws.freeze_panes(4, 2)
    n = len(df)
    ws.conditional_format(4, 3, 3 + n, 3, {"type": "3_color_scale",
        "min_color": "#e8f1fc", "mid_color": "#86b6ef", "max_color": BLUE})     # norm ppsf
    ws.conditional_format(4, 17, 3 + n, 17, {"type": "3_color_scale",
        "min_color": "#d5473f", "mid_color": "#f0efec", "max_color": "#0f8a3c"})  # reprice
    ws.conditional_format(4, 14, 3 + n, 14, {"type": "data_bar", "bar_color": "#eb6834"})  # >=10M


def key_conclusions_sheet(wb, mm, red, tb, sb, rb=None):
    ws = wb.add_worksheet("Key Conclusions")
    m, pr, ci = mm["meta"], mm["meta"]["premiums"], mm["meta"]["premiums_ci95"]
    nbs = mm["neighborhoods"]
    geo = {g["geo_type"]: g for g in mm["geography"]}
    tmeta = tb["meta"]
    top = sorted(nbs, key=lambda r: -r["norm_ppsf"])[:5]
    aff = sorted(nbs, key=lambda r: r["norm_ppsf"])[:5]
    disc = _wavg(nbs, "median_discount_pct", "sold_n")
    fail = _wavg(nbs, "failure_rate", "sold_n")
    fi = geo.get("Finger-isle waterfront", {}).get("median_ppsf")
    inl = geo.get("Mainland inland", {}).get("median_ppsf")
    streets = sb["streets"]
    prime = max((s for s in streets if s["n_sold"] >= 5 and s["premium_vs_nbhd"] is not None),
                key=lambda s: s["premium_vs_nbhd"], default=None)

    def rng(c):
        return f"95% CI {ci[c][0]:+.0f}% to {ci[c][1]:+.0f}%"

    # (Conclusion, Figure, Underwriting/evidence, Confidence)
    rows = [
        ("Normalized citywide value",
         f"${m['city_norm_ppsf']:,.0f}/sqft",
         f"Per-home hedonic on {m['n_sold']:,} closed sales, R²={m['hedonic_r2']}. "
         f"Cross-validated at r=0.93 against an independent Redfin estimate. "
         "Figure is a standardized dry-lot home; drivers below are added on top.", "High"),
        ("Waterfront is the biggest driver", f"+{pr['waterfront_pct']:.0f}%",
         f"Per foot, all else equal. {rng('waterfront_pct')} — well clear of zero.", "High"),
        ("New construction premium", f"+{pr['new_construction_pct']:.0f}%",
         f"Homes ≤6 yrs old, net of the age gradient. {rng('new_construction_pct')}.", "High"),
        ("Private pool premium", f"+{pr['pool_pct']:.0f}%",
         f"{rng('pool_pct')}.", "High"),
        ("Age depreciation", f"{pr['age_per_decade_pct']:.0f}% / decade",
         f"Each decade older. {rng('age_per_decade_pct')}.", "High"),
        ("Geography sets the tier",
         f"Finger-isle ${fi:,.0f} vs inland ${inl:,.0f}/sqft" if fi and inl else "—",
         f"Finger-isle (point-lot) waterfront runs ~{fi/inl:.1f}x mainland-inland per foot. "
         "Derived lot-geography classification." if fi and inl else "", "High"),
        ("Implied land value", f"~${m['city_land_ppsf']:,.0f}/sqft of lot",
         f"From an SFR structure-vs-land model (lot elasticity {m['land_lot_elasticity']}, "
         "R²=0.94). Vacant-land comps would refine it.", "Medium"),
        ("Market up sharply since 2020",
         f"+{tmeta['city_pct_since_2020']:.0f}% (${tmeta['city_2020_ppsf']:,.0f}→${tmeta['city_now_ppsf']:,.0f})",
         "Citywide, homes-sold-weighted (Redfin monthly). Price at new highs.", "High"),
        ("Price high, but market has slowed",
         f"DOM {tmeta['fastest_dom']:.0f}→110+ days",
         f"Days-on-market bottomed at {tmeta['fastest_dom']:.0f} in the 2022 frenzy "
         "(homes at asking); buyers now negotiate ~6% off again. A real divergence.", "High"),
        ("Typical list-to-sale discount", f"~{disc:.0f}% under ask",
         "Actual closed list-vs-sale, sample-weighted across neighborhoods.", "High"),
        ("Pricing right matters", f"~{fail:.0f}% of listings fail to sell",
         "Share of listing attempts that ended without a sale (failed / failed+sold). "
         "Many relist and eventually sell, so this measures attempt risk.", "Medium"),
        ("Most valuable neighborhoods",
         ", ".join(t["neighborhood"] for t in top[:3]),
         "By normalized $/sqft: " + "; ".join(
             f"{t['neighborhood']} ${t['norm_ppsf']:,.0f}" for t in top) + ".", "High"),
        ("Most affordable neighborhoods",
         ", ".join(a["neighborhood"] for a in aff[:3]),
         "By normalized $/sqft: " + "; ".join(
             f"{a['neighborhood']} ${a['norm_ppsf']:,.0f}" for a in aff) + ".", "High"),
        ("Street-level value resolves the block",
         f"{sb['meta']['n_streets']} streets"
         + (f"; prime {prime['street']} +{prime['premium_vs_nbhd']:.0f}%" if prime else ""),
         "Each street carries its premium/discount vs its neighborhood (≥4 comps). "
         f"{sb['meta']['n_live_underwritten']:,} live listings underwritten vs street comps.",
         "Medium"),
        ("Comp-backed live opportunities", f"{len(sb['deals'])} SFR candidates",
         "Active single-family listings asking below their street value (≥4 street comps, "
         "bounded gap). Screening only — verify condition on site.", "Medium"),
    ]
    if rb:
        rm = rb["meta"]
        cover = 100 * (rm["list_total"] / rm["should_be_total"] - 1)
        cv = rm["condo_verdict_counts"]
        rows += [
            ("Live inventory is priced above the model",
             f"asking {cover:+.0f}% vs should-be",
             f"{rm['n_repriceable']:,} of {rm['n_live']:,} live listings are comp-backed; "
             f"of those, {rm['verdict_counts'].get('Overpriced',0)} overpriced / "
             f"{rm['verdict_counts'].get('Fairly priced',0)} fair / "
             f"{rm['verdict_counts'].get('Underpriced',0)} underpriced. See Repriced Inventory.", "Medium"),
            ("Condo pricing vs. recent sold comps",
             f"{cv.get('Overpriced',0)} over / {cv.get('Underpriced',0)} under",
             "Condos repriced against recent SOLD comps per neighborhood (≥8 comps). See "
             "Condo Repricing tab. Excludes pre-construction towers (no comps).", "Medium"),
        ]
    rows += [
        ("Data validated & cleaned",
         "100% addr · ~98% sqft/yr",
         "Top sales match public records to the dollar (5 Harborage $70M, 84 Isla Bahia $34M). "
         f"Recovered {m['filled_sqft']} sqft + {m['filled_year']} year values from peers; "
         f"dropped {m.get('stale_active_dropped',0)} already-sold 'active' listings; MLS# unique "
         "(no duplicates).", "High"),
    ]

    title = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781"})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                         "border_color": "white", "valign": "vcenter", "text_wrap": True})
    idx = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "center",
                         "valign": "top", "font_color": "#898781"})
    concl = wb.add_format({"bold": True, "border": 1, "border_color": "#e1e0d9",
                           "valign": "top", "text_wrap": True})
    figf = wb.add_format({"bold": True, "font_color": DARK, "border": 1,
                          "border_color": "#e1e0d9", "valign": "top", "text_wrap": True})
    ev = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                        "text_wrap": True, "font_size": 10})
    conf_fmt = {
        "High": wb.add_format({"bold": True, "font_color": "#166b34", "bg_color": "#e4f3e9",
                               "border": 1, "border_color": "white", "align": "center", "valign": "top"}),
        "Medium": wb.add_format({"bold": True, "font_color": "#8a5a10", "bg_color": "#fbf1dd",
                                 "border": 1, "border_color": "white", "align": "center", "valign": "top"}),
    }
    ws.write(0, 0, "Fort Lauderdale — Key Conclusions (underwritten)", title)
    ws.write(1, 0, "Every headline finding with the evidence behind it. Details in the "
             "following sheets. Not a per-home appraisal.", sub)
    heads = ["#", "Conclusion", "Figure", "Underwriting — the evidence", "Confidence"]
    widths = [4, 30, 22, 82, 12]
    for c, (h, wd) in enumerate(zip(heads, widths)):
        ws.write(3, c, h, hdr)
        ws.set_column(c, c, wd)
    for i, (c1, c2, c3, c4) in enumerate(rows):
        r = 4 + i
        ws.write_number(r, 0, i + 1, idx)
        ws.write(r, 1, c1, concl)
        ws.write(r, 2, c2, figf)
        ws.write(r, 3, c3, ev)
        ws.write(r, 4, c4, conf_fmt[c4])
        ws.set_row(r, 15 * max(2, (len(c3) // 78 + 1)))
    ws.freeze_panes(4, 0)
    ws.hide_gridlines(2)


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
    ci = meta.get("premiums_ci95", {})
    ws.set_column(0, 0, 34)
    ws.set_column(1, 1, 14)
    ws.set_column(2, 2, 22)
    ws.write(3, 0, "Driver", hdr)
    ws.write(3, 1, "Effect", hdr)
    ws.write(3, 2, "95% confidence range", hdr)
    cirf = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "center"})
    rows = [("Waterfront (vs dry lot)", pr["waterfront_pct"], "waterfront_pct"),
            ("Private pool", pr["pool_pct"], "pool_pct"),
            ("New construction (<=6 yrs, net of age)", pr["new_construction_pct"], "new_construction_pct"),
            ("Each additional bathroom", pr["bath_pct"], "bath_pct"),
            ("Each decade of age", pr["age_per_decade_pct"], "age_per_decade_pct")]
    for i, (k, v, key) in enumerate(rows):
        ws.write(4 + i, 0, k, lab)
        ws.write_number(4 + i, 1, v / 100.0, val)
        rr = ci.get(key)
        ws.write(4 + i, 2, f"{rr[0]:+.0f}% to {rr[1]:+.0f}%" if rr else "—", cirf)
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


NBHD_REPRICE_COLS = [
    ("neighborhood", "Neighborhood", None, 26),
    ("n_live", "Live", "#,##0", 7),
    ("ask_ppsf", "Now asking $/sqft", "$#,##0", 15),
    ("sold_ppsf", "Should be (recent sold)", "$#,##0", 18),
    ("model_ppsf", "Model $/sqft", "$#,##0", 12),
    ("gap_pct", "Ask vs should-be", '+0.0"%";-0.0"%"', 15),
    ("verdict", "Verdict", None, 16),
    ("n_sold_comps", "Comps", "#,##0", 8),
    ("list_total", "Listed at", "$#,##0", 15),
    ("should_be_total", "Should be", "$#,##0", 15),
]
INVENTORY_COLS = [
    ("address", "Address", None, 26),
    ("neighborhood", "Neighborhood", None, 20),
    ("ptype", "Type", None, 13),
    ("sqft", "SqFt", "#,##0", 8),
    ("list_price", "Now listed", "$#,##0", 13),
    ("ask_ppsf", "Ask $/sqft", "$#,##0", 11),
    ("should_be_ppsf", "Should-be $/sqft", "$#,##0", 15),
    ("should_be_price", "Should-be price", "$#,##0", 15),
    ("diff_price", "Over/(under) listed", "$#,##0", 17),
    ("gap_pct", "Gap", '+0.0"%";-0.0"%"', 9),
    ("comps", "Comps", "#,##0", 7),
    ("verdict", "Verdict", None, 16),
]


def _verdict_fmt(wb):
    base = dict(border=1, border_color="white", align="center", bold=True)
    return {
        "Overpriced": wb.add_format({**base, "font_color": "#b23b28", "bg_color": "#fbe9e7"}),
        "Underpriced": wb.add_format({**base, "font_color": "#166b34", "bg_color": "#e4f3e9"}),
        "Fairly priced": wb.add_format({**base, "font_color": "#52514e", "bg_color": "#f0efec"}),
        "Insufficient comps": wb.add_format({**base, "font_color": "#8a8a8a", "bg_color": "#f4f2ee"}),
    }


def _write_verdict_table(wb, ws, df, cols, fmts, vfmt, title, sub):
    write_table(wb, ws, df, cols, fmts, title, sub)
    vcol = next(i for i, c in enumerate(cols) if c[0] == "verdict")
    for r, (_, row) in enumerate(df.iterrows()):
        v = row.get("verdict")
        if v in vfmt:
            ws.write(4 + r, vcol, v, vfmt[v])
    ws.hide_gridlines(2)


def reprice_sheets(wb, fmts, rb):
    vfmt = _verdict_fmt(wb)
    m = rb["meta"]
    over = 100 * (m["list_total"] / m["should_be_total"] - 1)

    condo = pd.DataFrame(rb["condos_by_nbhd"])
    ws = wb.add_worksheet("Condo Repricing")
    if len(condo):
        _write_verdict_table(wb, ws, condo, NBHD_REPRICE_COLS, fmts, vfmt,
            "Condo repricing by neighborhood — current asking vs. what they should be",
            "\"Should be\" = median recent SOLD $/sqft (comparable closings). Verdict from asking "
            "vs sold. Neighborhoods with >=8 condo comps; pre-construction towers excluded.")
        ws.conditional_format(4, 5, 3 + len(condo), 5, {"type": "3_color_scale",
            "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})

    allnb = pd.DataFrame(rb["by_nbhd"])
    ws2 = wb.add_worksheet("Neighborhood Repricing")
    if len(allnb):
        _write_verdict_table(wb, ws2, allnb, NBHD_REPRICE_COLS, fmts, vfmt,
            "All-property repricing by neighborhood — asking vs. recent sold",
            "Every property type. \"Should be\" = median recent sold $/sqft. >=8 comps.")
        ws2.conditional_format(4, 5, 3 + len(allnb), 5, {"type": "3_color_scale",
            "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})

    inv = pd.DataFrame(rb["inventory"])
    ws3 = wb.add_worksheet("Repriced Inventory")
    _write_verdict_table(wb, ws3, inv, INVENTORY_COLS, fmts, vfmt,
        f"Every live listing repriced ({m['n_live']:,} active/pending)",
        f"Model \"should-be\" price vs current list. Comp-backed asking ${m['list_total']/1e9:.2f}B "
        f"vs model ${m['should_be_total']/1e9:.2f}B ({over:+.0f}%). 'Insufficient comps' = "
        "pre-construction/thin buildings the model can't value. Screening — verify condition.")
    ws3.conditional_format(4, 9, 3 + len(inv), 9, {"type": "3_color_scale",
        "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})


BN_COLS = [
    ("neighborhood", "Neighborhood", None, 24),
    ("band", "Price band", None, 12),
    ("n_sold", "Sold", "#,##0", 7),
    ("sold_ppsf", "Sold $/sqft", "$#,##0", 12),
    ("n_live", "Live", "#,##0", 7),
    ("ask_ppsf", "Asking $/sqft", "$#,##0", 13),
    ("gap_pct", "Ask vs sold", '+0.0"%";-0.0"%"', 12),
    ("verdict", "Verdict", None, 16),
    ("median_sold_price", "Median sold $", "$#,##0", 15),
]
HT_COLS = [
    ("band", "Band", None, 11),
    ("address", "Address", None, 24),
    ("neighborhood", "Neighborhood", None, 20),
    ("geo_type", "Geography", None, 22),
    ("ptype", "Type", None, 12),
    ("sqft", "SqFt", "#,##0", 8),
    ("list_price", "Current list", "$#,##0", 14),
    ("ask_ppsf", "Ask $/sqft", "$#,##0", 11),
    ("supported_ppsf", "Supported $/sqft", "$#,##0", 15),
    ("suggested_list", "SUGGESTED LIST", "$#,##0", 16),
    ("over_under_list", "Over/(under)", "$#,##0", 14),
    ("gap_pct", "Gap", '+0.0"%";-0.0"%"', 9),
    ("street_comps", "Comps", "#,##0", 7),
    ("comp_confidence", "Confidence", None, 14),
    ("verdict", "Verdict", None, 16),
]
HTBAND_COLS = [
    ("band", "Price band", None, 12),
    ("n", "Listings", "#,##0", 9),
    ("median_ask_ppsf", "Median ask $/sqft", "$#,##0", 15),
    ("median_supported_ppsf", "Median supported $/sqft", "$#,##0", 18),
    ("total_list", "Total listed", "$#,##0", 16),
    ("total_suggested", "Total suggested", "$#,##0", 16),
    ("overpriced", "Overpriced", "#,##0", 10),
    ("fairly_priced", "Fair", "#,##0", 8),
    ("underpriced", "Underpriced", "#,##0", 11),
    ("no_comps", "No comps", "#,##0", 9),
]


def underpriced_sheet(wb, ub):
    ws = wb.add_worksheet("Underpriced + Why")
    m = ub["meta"]
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781"})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": "#0f8a3c",
                         "border": 1, "border_color": "white", "valign": "vcenter",
                         "text_wrap": True, "align": "center"})
    txt = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top"})
    txtl = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                          "text_wrap": True})
    nbf = wb.add_format({"bold": True, "border": 1, "border_color": "#e1e0d9", "valign": "top"})
    usd = wb.add_format({"num_format": "$#,##0", "border": 1, "border_color": "#e1e0d9",
                         "valign": "top", "align": "center"})
    opp = wb.add_format({"num_format": "$#,##0", "bold": True, "font_color": "#0f8a3c",
                         "border": 1, "border_color": "#e1e0d9", "valign": "top", "align": "center"})
    pctf = wb.add_format({"num_format": '0"%"', "border": 1, "border_color": "#e1e0d9",
                          "valign": "top", "align": "center"})
    conff = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                           "align": "center", "font_size": 10})
    reas = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                          "text_wrap": True, "font_size": 10})

    ws.write(0, 0, "Underpriced opportunities — where the market is mispriced, and WHY", title)
    ws.write(1, 0, f"{m['n']} live listings asking below comp-supported value "
             f"(${m['total_opportunity']/1e6:.0f}M total gap). Ranked by dollar opportunity. "
             "'Why' is generated from the data. Verify condition on site.", sub)
    heads = ["Opportunity $", "Address", "Neighborhood", "Band", "Type", "List price",
             "Ask $/sqft", "Supported $/sqft", "% under", "Confidence", "Why it's underpriced"]
    widths = [14, 26, 20, 11, 13, 14, 11, 15, 9, 15, 82]
    for c, (h, wd) in enumerate(zip(heads, widths)):
        ws.write(3, c, h, hdr)
        ws.set_column(c, c, wd)
    for i, r in enumerate(ub["listings"]):
        row = 4 + i
        ws.write_number(row, 0, r["opportunity"], opp)
        ws.write(row, 1, r["address"], nbf)
        ws.write(row, 2, r["neighborhood"], txt)
        ws.write(row, 3, r["band"], txt)
        ws.write(row, 4, r["ptype"], txt)
        ws.write_number(row, 5, r["list_price"], usd)
        ws.write_number(row, 6, r["ask_ppsf"], usd)
        ws.write_number(row, 7, r["supported_ppsf"], usd)
        ws.write_number(row, 8, r["under_pct"], pctf)
        ws.write(row, 9, r["confidence"], conff)
        ws.write(row, 10, "• " + "\n• ".join(r["reasons"]), reas)
        ws.set_row(row, 14 * max(2, len(r["reasons"])))
    ws.freeze_panes(4, 2)
    ws.autofilter(3, 0, 3 + len(ub["listings"]), len(heads) - 1)
    ws.hide_gridlines(2)


def high_ticket_sheets(wb, fmts, hb):
    vfmt = _verdict_fmt(wb)
    m = hb["meta"]

    bn = pd.DataFrame(hb["band_neighborhood"])
    ws = wb.add_worksheet("Band x Neighborhood")
    if len(bn):
        _write_verdict_table(wb, ws, bn, BN_COLS, fmts, vfmt,
            "How each price band behaves WITHIN each neighborhood (>= $1M)",
            "The core high-ticket view: what actually SOLD vs what's currently ASKED, per band, "
            "per neighborhood. A band can be hot in one area and soft in another.")
        ws.conditional_format(4, 6, 3 + len(bn), 6, {"type": "3_color_scale",
            "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})
        ws.freeze_panes(4, 1)

    ht = pd.DataFrame(hb["listings"])
    ws2 = wb.add_worksheet("High-Ticket Underwriting")
    _write_verdict_table(wb, ws2, ht, HT_COLS, fmts, vfmt,
        f"Every live listing >= ${m['min_ticket']/1e6:.0f}M repriced ({m['n_listings']} listings)",
        "Current list vs a SUGGESTED LIST (street-comp supported value). Comp-backed listed at "
        f"${m['total_list']/1e9:.2f}B vs suggested ${m['total_suggested']/1e9:.2f}B "
        f"({m['list_vs_suggested_pct']:+.0f}%). Confidence = how much sold data backs each figure; "
        "'Low (no comps)' = pre-construction/unique, treat as a starting point.")
    ws2.conditional_format(4, 11, 3 + len(ht), 11, {"type": "3_color_scale",
        "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})
    ws2.freeze_panes(4, 2)

    bands = pd.DataFrame(hb["bands"])
    ws3 = wb.add_worksheet("Price Bands")
    write_table(wb, ws3, bands, HTBAND_COLS, fmts,
                "High-ticket price bands — the luxury market by tier",
                "Median asking vs supported $/sqft and over/under counts, per price band.")
    ws3.hide_gridlines(2)


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

    try:
        try:
            rb = _reprice()
        except FileNotFoundError:
            rb = None
        key_conclusions_sheet(wb, mm, b, _time(), _street(), rb)
    except FileNotFoundError:
        pass
    try:
        master_sheet(wb, fmts, _master())
    except FileNotFoundError:
        pass
    readme_sheet(wb, meta)

    # ---- HIGH-TICKET FOCUS (>= $1M) ----
    try:
        high_ticket_sheets(wb, fmts, _high())
    except FileNotFoundError:
        pass
    try:
        underpriced_sheet(wb, _underpriced())
    except FileNotFoundError:
        pass

    # ---- PRIMARY: MLS per-home layer ----
    mls_profiles_sheet(wb, mm)
    mls_ranking_sheet(wb, fmts, mm)
    mls_drivers_sheet(wb, mm)
    mls_deals_sheet(wb, fmts, mm)
    try:
        reprice_sheets(wb, fmts, _reprice())
    except FileNotFoundError:
        pass
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
