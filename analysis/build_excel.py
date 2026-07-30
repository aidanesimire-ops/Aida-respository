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


def _jload(name):
    with open(os.path.join(PROC, name)) as f:
        return json.load(f)


def _jload_opt(name):
    try:
        return _jload(name)
    except FileNotFoundError:
        return None


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


def _scen_seed(master):
    """Pick a default neighborhood + its base price / sqft / DOM / appreciation."""
    nbs = master["neighborhoods"]
    pick = None
    for want in ("Rio Vista", "Coral Ridge", "Las Olas"):
        pick = next((n for n in nbs if n["neighborhood"] == want), None)
        if pick:
            break
    if pick is None:
        pick = max(nbs, key=lambda n: n.get("norm_ppsf") or 0)
    ppsf = pick.get("norm_ppsf") or 500
    price = pick.get("median_sale_price") or ppsf * 3000
    sqft = round((price / ppsf) / 100) * 100 if ppsf else 3000
    sqft = max(500, sqft)
    price = round(price / 50000) * 50000
    dom = pick.get("dom") or 90
    a20 = pick.get("appreciation_since_2020")
    apprec = ((1 + a20 / 100) ** (1 / 6) - 1) if a20 is not None else 0.04
    return pick["neighborhood"], price, sqft, dom, round(apprec, 4)


def _scen_compute(price, sqft, down, rate, amort, shift, pelast, cash,
                  delast, basedom, apprec, hold, sell):
    pf = 1 + (pelast / 100) * (shift / 100) * (1 - cash)
    adjp = price * pf
    effr = rate + shift / 10000.0
    loan = adjp * (1 - down)
    m, n = effr / 12.0, amort * 12
    pay = loan * m / (1 - (1 + m) ** -n) if m > 0 else loan / n
    ppsf = adjp / sqft if sqft else 0
    dom = basedom * (1 + (delast / 100) * (shift / 100))
    ctc = adjp * down + adjp * 0.03
    k = hold * 12
    remloan = (loan * ((1 + m) ** n - (1 + m) ** k) / ((1 + m) ** n - 1)
               if m > 0 else loan * (1 - k / n))
    exitv = adjp * (1 + apprec) ** hold
    net = exitv - exitv * sell - remloan
    eqm = net / ctc if ctc else 0
    annr = ((net / ctc) ** (1 / hold) - 1) if (net > 0 and ctc > 0 and hold) else 0
    return dict(pf=pf, adjp=adjp, effr=effr, loan=loan, pay=pay, ppsf=ppsf, dom=dom,
                ctc=ctc, remloan=remloan, exitv=exitv, net=net, eqm=eqm, annr=annr)


def scenario_sheet(wb, master):
    """A fully live financing / capital-markets model: edit the yellow input cells and
    every output + the sensitivity table recompute. Recreate for any asset class."""
    ws = wb.add_worksheet("Scenario")
    nb, price0, sqft0, dom0, apprec0 = _scen_seed(master)
    down0, rate0, amort0, shift0 = 0.35, 0.07, 30, 0
    pelast0, cash0, delast0, sell0, hold0 = -3, 0.45, 15, 0.06, 5

    title = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781", "text_wrap": True})
    grp = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                         "border_color": "white"})
    lab = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "vcenter"})
    olab = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "vcenter", "bold": True})
    hi = {"bg_color": "#fff7d6", "border": 1, "border_color": "#d9cf9a", "align": "right", "bold": True}
    inp_money = wb.add_format({**hi, "num_format": "$#,##0"})
    inp_num = wb.add_format({**hi, "num_format": "#,##0"})
    inp_pct = wb.add_format({**hi, "num_format": "0%"})
    inp_pct1 = wb.add_format({**hi, "num_format": "0.0%"})
    inp_rate = wb.add_format({**hi, "num_format": "0.000%"})
    inp_e = wb.add_format({**hi, "num_format": "0.0"})
    outf = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                          "num_format": "$#,##0"})
    outf_hi = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                             "num_format": "$#,##0", "bold": True, "font_color": DARK,
                             "bg_color": "#eef5fc"})
    outf_x = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                            "num_format": '0.00"×"', "bold": True})
    outf_pct = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                              "num_format": "0.0%", "bold": True})
    outf_n = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                            "num_format": "0"})
    outf_r = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                            "num_format": "0.000%"})
    outf_f = wb.add_format({"border": 1, "border_color": "#e1e0d9", "align": "right",
                            "num_format": "0.000"})
    thdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": DARK, "border": 1,
                          "border_color": "white", "align": "center", "valign": "vcenter",
                          "text_wrap": True})

    ws.set_column(0, 0, 30)
    ws.set_column(1, 1, 15)
    ws.set_column(2, 2, 3)
    ws.set_column(3, 3, 26)
    ws.set_column(4, 4, 16)
    ws.write(0, 0, f"Deal scenario & financing — {nb} (edit the yellow cells)", title)
    ws.write(1, 0, "A live model: change any yellow input and every output plus the sensitivity "
             "table below recompute. Elasticities are yours to set — nothing is hard-coded, so "
             "this recreates for any market or asset class. Seeded from the master ranking.", sub)
    ws.set_row(1, 42)

    v = _scen_compute(price0, sqft0, down0, rate0, amort0, shift0, pelast0, cash0,
                      delast0, dom0, apprec0, hold0, sell0)

    # ---- INPUTS (col A label / col B value, Excel rows are index+1) ----
    ws.merge_range(3, 0, 3, 1, "DEAL", grp)
    ws.write(4, 0, "Purchase price ($)", lab);       ws.write_number(4, 1, price0, inp_money)   # B5
    ws.write(5, 0, "Size (sqft)", lab);              ws.write_number(5, 1, sqft0, inp_num)      # B6
    ws.merge_range(6, 0, 6, 1, "FINANCING", grp)
    ws.write(7, 0, "Down payment (%)", lab);         ws.write_number(7, 1, down0, inp_pct)      # B8
    ws.write(8, 0, "Mortgage rate (%)", lab);        ws.write_number(8, 1, rate0, inp_rate)     # B9
    ws.write(9, 0, "Amortization (yrs)", lab);       ws.write_number(9, 1, amort0, inp_num)     # B10
    ws.merge_range(10, 0, 10, 1, "CAPITAL MARKETS & ASSUMPTIONS", grp)
    ws.write(11, 0, "Rate shift (bps)", lab);        ws.write_number(11, 1, shift0, inp_e)      # B12
    ws.write(12, 0, "Price sensitivity (%/+100bps)", lab); ws.write_number(12, 1, pelast0, inp_e)  # B13
    ws.write(13, 0, "Cash-buyer share (%)", lab);    ws.write_number(13, 1, cash0, inp_pct)     # B14
    ws.write(14, 0, "DOM sensitivity (%/+100bps)", lab);  ws.write_number(14, 1, delast0, inp_e)   # B15
    ws.write(15, 0, "Base days on market", lab);     ws.write_number(15, 1, dom0, inp_num)      # B16
    ws.write(16, 0, "Appreciation (%/yr)", lab);     ws.write_number(16, 1, apprec0, inp_pct1)  # B17
    ws.write(17, 0, "Hold (yrs)", lab);              ws.write_number(17, 1, hold0, inp_num)     # B18
    ws.write(18, 0, "Selling costs (%)", lab);       ws.write_number(18, 1, sell0, inp_pct1)    # B19

    # ---- OUTPUTS (col D label / col E value) ----
    ws.merge_range(3, 3, 3, 4, "LIVE OUTPUTS", grp)
    ws.write(4, 3, "Price factor", olab)
    ws.write_formula(4, 4, "=1+($B$13/100)*($B$12/100)*(1-$B$14)", outf_f, v["pf"])        # E5
    ws.write(5, 3, "Adjusted market price", olab)
    ws.write_formula(5, 4, "=$B$5*E5", outf_hi, v["adjp"])                                  # E6
    ws.write(6, 3, "Adjusted $/sqft", olab)
    ws.write_formula(6, 4, "=E6/$B$6", outf_hi, v["ppsf"])                                  # E7
    ws.write(7, 3, "Effective mortgage rate", olab)
    ws.write_formula(7, 4, "=$B$9+$B$12/10000", outf_r, v["effr"])                          # E8
    ws.write(8, 3, "Loan amount", olab)
    ws.write_formula(8, 4, "=E6*(1-$B$8)", outf, v["loan"])                                 # E9
    ws.write(9, 3, "Monthly P&I", olab)
    ws.write_formula(9, 4, "=E9*(E8/12)/(1-(1+E8/12)^-($B$10*12))", outf_hi, v["pay"])      # E10
    ws.write(10, 3, "Projected days on market", olab)
    ws.write_formula(10, 4, "=$B$16*(1+($B$15/100)*($B$12/100))", outf_n, v["dom"])         # E11
    ws.write(11, 3, "Cash to close", olab)
    ws.write_formula(11, 4, "=E6*$B$8+E6*0.03", outf, v["ctc"])                             # E12
    ws.write(12, 3, "Remaining loan @ exit", olab)
    ws.write_formula(12, 4, "=E9*((1+E8/12)^($B$10*12)-(1+E8/12)^($B$18*12))/((1+E8/12)^($B$10*12)-1)",
                     outf, v["remloan"])                                                    # E13
    ws.write(13, 3, "Exit value (@ hold)", olab)
    ws.write_formula(13, 4, "=E6*(1+$B$17)^$B$18", outf, v["exitv"])                        # E14
    ws.write(14, 3, "Net sale proceeds", olab)
    ws.write_formula(14, 4, "=E14-E14*$B$19-E13", outf_hi, v["net"])                        # E15
    ws.write(15, 3, "Equity multiple", olab)
    ws.write_formula(15, 4, "=E15/E12", outf_x, v["eqm"])                                   # E16
    ws.write(16, 3, "Annualized return", olab)
    ws.write_formula(16, 4, "=(E15/E12)^(1/$B$18)-1", outf_pct, v["annr"])                  # E17

    # ---- SENSITIVITY to rate shift ----
    sr = 20
    ws.write(sr, 0, "Sensitivity to rate shift", title)
    sr += 1
    for c, h in enumerate(["Rate shift (bps)", "Market price", "$/sqft", "Proj. DOM", "Monthly P&I"]):
        ws.write(sr, c, h, thdr)
    shifts = [-200, -100, -50, 0, 50, 100, 200]
    for j, sh in enumerate(shifts):
        r = sr + 1 + j
        er = r + 1  # Excel row number
        cv = _scen_compute(price0, sqft0, down0, rate0, amort0, sh, pelast0, cash0,
                           delast0, dom0, apprec0, hold0, sell0)
        ws.write_number(r, 0, sh, outf_n)
        ws.write_formula(r, 1, f"=$B$5*(1+($B$13/100)*(A{er}/100)*(1-$B$14))", outf, cv["adjp"])
        ws.write_formula(r, 2, f"=B{er}/$B$6", outf, cv["ppsf"])
        ws.write_formula(r, 3, f"=$B$16*(1+($B$15/100)*(A{er}/100))", outf_n, cv["dom"])
        ws.write_formula(
            r, 4,
            f"=(B{er}*(1-$B$8))*(($B$9+A{er}/10000)/12)/(1-(1+($B$9+A{er}/10000)/12)^-($B$10*12))",
            outf, cv["pay"])
    ws.conditional_format(sr + 1, 1, sr + len(shifts), 1,
                          {"type": "3_color_scale", "min_color": "#f6b6b6",
                           "mid_color": "#f0efec", "max_color": "#8fd48f"})

    # ---- neighborhood seed reference (copy these into the inputs) ----
    rr = sr + len(shifts) + 3
    ws.write(rr, 0, "Seed figures by neighborhood — copy into the inputs above", title)
    rr += 1
    for c, h in enumerate(["Neighborhood", "Base price", "Base sqft", "Base DOM", "Apprec/yr"]):
        ws.write(rr, c, h, thdr)
    seedf_txt = wb.add_format({"border": 1, "border_color": "#e1e0d9"})
    seedf_usd = wb.add_format({"border": 1, "border_color": "#e1e0d9", "num_format": "$#,##0", "align": "right"})
    seedf_n = wb.add_format({"border": 1, "border_color": "#e1e0d9", "num_format": "#,##0", "align": "right"})
    seedf_p = wb.add_format({"border": 1, "border_color": "#e1e0d9", "num_format": "0.0%", "align": "right"})
    seed_rows = sorted([n for n in master["neighborhoods"] if n.get("norm_ppsf")],
                       key=lambda n: -(n.get("norm_ppsf") or 0))
    for j, n in enumerate(seed_rows):
        r = rr + 1 + j
        ppsf = n.get("norm_ppsf") or 0
        pr = n.get("median_sale_price") or (ppsf * 3000)
        sq = max(500, round((pr / ppsf) / 100) * 100) if ppsf else 3000
        a20 = n.get("appreciation_since_2020")
        ap = ((1 + a20 / 100) ** (1 / 6) - 1) if a20 is not None else 0.04
        ws.write(r, 0, n["neighborhood"], seedf_txt)
        ws.write_number(r, 1, round(pr / 50000) * 50000, seedf_usd)
        ws.write_number(r, 2, sq, seedf_n)
        ws.write_number(r, 3, n.get("dom") or 90, seedf_n)
        ws.write_number(r, 4, round(ap, 4), seedf_p)
    ws.freeze_panes(3, 0)
    ws.hide_gridlines(2)


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


SELLER_COLS = [
    ("status", "Status", None, 11),
    ("band", "Band", None, 11),
    ("address", "Address", None, 24),
    ("neighborhood", "Neighborhood", None, 20),
    ("ptype", "Type", None, 12),
    ("sqft", "SqFt", "#,##0", 8),
    ("asked", "Asked", "$#,##0", 14),
    ("ask_ppsf", "Ask $/sqft", "$#,##0", 11),
    ("supported_ppsf", "Supported $/sqft", "$#,##0", 15),
    ("over_pct", "% over", '+0"%"', 8),
    ("suggested_list", "SUGGESTED LIST", "$#,##0", 16),
    ("reduce_by", "Reduce by", "$#,##0", 14),
    ("pitch", "The pitch", None, 70),
]
TEARDOWN_COLS = [
    ("band", "Band", None, 11),
    ("address", "Address", None, 24),
    ("neighborhood", "Neighborhood", None, 20),
    ("geo_type", "Geography", None, 22),
    ("list_price", "List price", "$#,##0", 14),
    ("sqft", "Living sqft", "#,##0", 11),
    ("lot_sqft", "Lot sqft", "#,##0", 10),
    ("year_built", "Year built", "0", 10),
    ("land_value", "Land value", "$#,##0", 14),
    ("land_share_pct", "Land % of ask", '0"%"', 12),
    ("note", "Note", None, 48),
]
COMPS_COLS = [
    ("target", "Listing", None, 24),
    ("target_neighborhood", "Neighborhood", None, 18),
    ("target_list", "List price", "$#,##0", 14),
    ("basis", "Comp basis", None, 18),
    ("comp_address", "Comparable sale", None, 24),
    ("comp_sold_price", "Sold for", "$#,##0", 13),
    ("comp_ppsf", "$/sqft", "$#,##0", 10),
    ("comp_sqft", "SqFt", "#,##0", 8),
]


def absorption_sheet(wb, fmts, ab):
    ws = wb.add_worksheet("Absorption")
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781"})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                         "border_color": "white", "align": "center"})
    txt = wb.add_format({"border": 1, "border_color": "#e1e0d9"})
    num = wb.add_format({"num_format": "#,##0", "border": 1, "border_color": "#e1e0d9", "align": "center"})
    mos = wb.add_format({"num_format": "0.0", "border": 1, "border_color": "#e1e0d9", "align": "center"})
    ws.write(0, 0, "Absorption — months of supply by price band", title)
    ws.write(1, 0, "How hard it is to sell at each level. <6 = seller's market, 6–12 balanced, "
             "12–24 buyer's, >24 deep buyer's. active ÷ (sold-per-month over ~2 yrs).", sub)
    heads = ["Price band", "Sold (2y)", "Active", "Months supply", "Market"]
    for c, (h, wd) in enumerate(zip(heads, [12, 10, 8, 14, 20])):
        ws.write(3, c, h, hdr)
        ws.set_column(c, c, wd)
    r = 4
    for row in ab["by_band"]:
        ws.write(r, 0, row["band"], txt)
        ws.write_number(r, 1, row["sold_2y"], num)
        ws.write_number(r, 2, row["active"], num)
        ws.write_number(r, 3, row["months_supply"], mos)
        ws.write(r, 4, row["market"] or "—", txt)
        r += 1
    ws.conditional_format(4, 3, r - 1, 3, {"type": "3_color_scale", "min_color": "#f6b6b6",
        "mid_color": "#f0efec", "max_color": "#8fd48f"})
    # band x neighborhood block
    r += 2
    ws.write(r, 0, "By band within each neighborhood", title)
    r += 1
    bnhead = ["Neighborhood", "Band", "Sold (2y)", "Active", "Months supply", "Market"]
    for c, h in enumerate(bnhead):
        ws.write(r, c, h, hdr)
    ws.set_column(0, 0, 24)
    start = r + 1
    for row in ab["by_band_neighborhood"]:
        r += 1
        ws.write(r, 0, row["neighborhood"], txt)
        ws.write(r, 1, row["band"], txt)
        ws.write_number(r, 2, row["sold_2y"], num)
        ws.write_number(r, 3, row["active"], num)
        ws.write_number(r, 4, row["months_supply"] if row["months_supply"] is not None else 0, mos)
        ws.write(r, 5, row["market"] or "—", txt)
    ws.conditional_format(start, 4, r, 4, {"type": "3_color_scale", "min_color": "#f6b6b6",
        "mid_color": "#f0efec", "max_color": "#8fd48f"})
    ws.freeze_panes(start, 0)
    ws.autofilter(start - 1, 0, r, 5)
    ws.hide_gridlines(2)


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


def seller_sheet(wb, fmts, sb):
    ws = wb.add_worksheet("Seller Prospects")
    df = pd.DataFrame(sb["failed"])
    m = sb["meta"]
    if len(df):
        write_table(wb, ws, df, SELLER_COLS, fmts,
                    "Listing-prospect engine — owners who tried and couldn't (≥$1M)",
                    f"{m['n_failed']} failed-listing owners + {m['n_overpriced_active']} overpriced "
                    "actives (separate sheet/CSV). Each shows what they asked, what comps support, "
                    "and the suggested list that moves it — your listing-appointment pitch.")
        ws.conditional_format(4, 9, 3 + len(df), 9, {"type": "3_color_scale",
            "min_color": "#f0efec", "mid_color": "#f6b6b6", "max_color": "#d5473f"})
    ws.hide_gridlines(2)
    # overpriced actives on their own sheet
    dfa = pd.DataFrame(sb["overpriced_active"])
    ws2 = wb.add_worksheet("Overpriced Actives")
    if len(dfa):
        write_table(wb, ws2, dfa, SELLER_COLS, fmts,
                    "Currently overpriced active listings (≥$1M) — tomorrow's expireds",
                    "Live listings well above comp-supported value — approach for a price "
                    "reduction / relist. Suggested list = comp-supported value.")
    ws2.hide_gridlines(2)


def teardown_sheet(wb, fmts, tb):
    ws = wb.add_worksheet("Teardown Land Plays")
    df = pd.DataFrame(tb["candidates"])
    if len(df):
        write_table(wb, ws, df, TEARDOWN_COLS, fmts,
                    "Teardown / land plays — where the lot is most of the value",
                    f"{tb['meta']['n']} single-family listings ({tb['meta']['n_waterfront']} "
                    "waterfront) where implied land value is the bulk of the ask. Redevelopment "
                    "candidates — confirm zoning & buildable area.")
        ws.conditional_format(4, 9, 3 + len(df), 9, {"type": "3_color_scale",
            "min_color": "#f0efec", "mid_color": "#f6c99a", "max_color": "#eb6834"})
    else:
        ws.write(0, 0, "No land-play candidates in the current set.", fmts["title"])
    ws.hide_gridlines(2)


def comps_sheet(wb, fmts):
    path = os.path.join(PROC, "comps_flat.csv")
    if not os.path.exists(path):
        return
    df = pd.read_csv(path)
    ws = wb.add_worksheet("Comps Drill-Down")
    write_table(wb, ws, df, COMPS_COLS, fmts,
                "Comps behind every live valuation (≥$1M)",
                "The actual comparable sales behind each listing's value — filter by Listing to "
                "defend a number in the room. Prefers same-street sales, then neighborhood + band.")
    ws.hide_gridlines(2)


def _blk_formats(wb):
    return {
        "title": wb.add_format({"bold": True, "font_size": 15, "font_color": DARK}),
        "sub": wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781", "text_wrap": True}),
        "h2": wb.add_format({"bold": True, "font_size": 12, "font_color": BLUE}),
        "hdr": wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                              "border_color": "white", "align": "center", "valign": "vcenter", "text_wrap": True}),
        "txt": wb.add_format({"border": 1, "border_color": "#e1e0d9"}),
        "txtb": wb.add_format({"border": 1, "border_color": "#e1e0d9", "bold": True}),
        "usd": wb.add_format({"num_format": "$#,##0", "border": 1, "border_color": "#e1e0d9", "align": "right"}),
        "num": wb.add_format({"num_format": "#,##0", "border": 1, "border_color": "#e1e0d9", "align": "center"}),
        "pct": wb.add_format({"num_format": '0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"}),
        "sgn": wb.add_format({"num_format": '+0"%";-0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"}),
    }


def _write_block(ws, r, headers, widths, rowdata, f):
    for c, (h, wd) in enumerate(zip(headers, widths)):
        ws.write(r, c, h, f["hdr"])
        ws.set_column(c, c, wd)
    for i, row in enumerate(rowdata):
        for c, (val, kind) in enumerate(row):
            fmt = f.get(kind, f["txt"])
            if val is None or (isinstance(val, float) and pd.isna(val)):
                ws.write(r + 1 + i, c, "", f["txt"])
            elif kind in ("usd", "num", "pct", "sgn"):
                ws.write_number(r + 1 + i, c, float(val), fmt)
            else:
                ws.write(r + 1 + i, c, str(val), fmt)
    return r + 1 + len(rowdata)


def land_comps_sheet(wb, lb):
    f = _blk_formats(wb)
    m = lb["meta"]
    ws = wb.add_worksheet("Land Comps")
    ws.write(0, 0, "Vacant-land comps by neighborhood — comp-backed land $/sqft", f["title"])
    ws.write(1, 0, f"Fort Lauderdale land ${m['fll_land_ppsf']}/sqft (waterfront "
             f"${m['fll_waterfront_ppsf']} vs dry ${m['fll_dry_ppsf']}, n={m['n_fll_sold']}). "
             f"{m['n_sold']:,} sold land comps across South Florida; {m['n_neighborhoods']} "
             "neighborhoods with ≥4. 'Market' flags true Fort Lauderdale vs the wider pull.", f["sub"])
    ws.set_row(1, 30)
    heads = ["Neighborhood", "Market", "Sold", "Land $/sqft", "$/sqft p25", "$/sqft p75",
             "$/acre", "Median price", "WF %", "Active", "Active ask $/sqft"]
    widths = [24, 16, 7, 12, 11, 11, 12, 14, 7, 8, 15]
    rows = []
    for r in lb["by_neighborhood"]:
        rows.append([
            (r["neighborhood"], "txtb"), ("Fort Lauderdale" if r["in_improved"] else "Wider S. Florida", "txt"),
            (r["n_sold"], "num"), (r["land_ppsf"], "usd"), (r["ppsf_p25"], "usd"),
            (r["ppsf_p75"], "usd"), (r["per_acre"], "usd"), (r["median_price"], "usd"),
            (round(r["waterfront_share"] * 100), "pct"), (r["n_active"], "num"),
            (r["active_ask_ppsf"], "usd")])
    end = _write_block(ws, 3, heads, widths, rows, f)
    ws.conditional_format(4, 3, end - 1, 3, {"type": "3_color_scale", "min_color": "#e8f1fc",
        "mid_color": "#86b6ef", "max_color": BLUE})
    # implied vs actual
    if lb["implied_vs_actual"]:
        r0 = end + 2
        ws.write(r0, 0, "Implied (hedonic) vs actual (comps) land value", f["h2"])
        iva = [[(x["neighborhood"], "txtb"), (x["implied_ppsf"], "usd"),
                (x["actual_ppsf"], "usd"), (x["gap_pct"], "sgn")] for x in lb["implied_vs_actual"]]
        _write_block(ws, r0 + 1, ["Neighborhood", "Implied $/sqft", "Actual $/sqft", "Actual vs implied"],
                     [24, 14, 14, 15], iva, f)
    # active land inventory
    r1 = (end + 2) + (len(lb["implied_vs_actual"]) + 4 if lb["implied_vs_actual"] else 0)
    ws.write(r1, 0, "Active land inventory (Fort Lauderdale first)", f["h2"])
    act = [[(a["address"], "txtb"), (a["neighborhood"], "txt"), (a["price"], "usd"),
            (a["lot_sqft"], "num"), (a["land_ppsf"], "usd"), ("Yes" if a["waterfront"] else "", "txt"),
            (a["density"], "txt"), (a["geo"], "txt")] for a in lb["actives"][:60]]
    _write_block(ws, r1 + 1, ["Address", "Neighborhood", "Price", "Lot sqft", "Ask $/sqft",
                 "WF", "Density", "Geography"], [24, 20, 13, 10, 11, 5, 14, 26], act, f)
    ws.hide_gridlines(2)


def land_geo_sheet(wb, lb):
    f = _blk_formats(wb)
    ws = wb.add_worksheet("Land Geography & Docks")
    ws.write(0, 0, "Land by geography, zoning & size — plus docks and commercial land", f["title"])
    ws.write(1, 0, "The lot factors that set land value, now observed from real land sales "
             "rather than inferred. Waterfront-vs-dry uses the Fort Lauderdale subset; finer "
             "cuts, size and zoning use urban lots.", f["sub"])
    ws.set_row(1, 30)
    r = 3
    ws.write(r, 0, "Lot geography — median land $/sqft", f["h2"]); r += 1
    geo = [[(g["geo"], "txtb"), (g["land_ppsf"], "usd"), (g["n"], "num"), (g["scope"], "txt")]
           for g in lb["geography"]]
    r = _write_block(ws, r, ["Lot type", "Land $/sqft", "n", "Scope"], [16, 12, 7, 20], geo, f) + 2
    ws.write(r, 0, "Zoning / density — higher density = more value per land sqft", f["h2"]); r += 1
    zon = [[(z["density"], "txtb"), (z["land_ppsf"], "usd"), (z["n"], "num"), (z["median_price"], "usd")]
           for z in lb["by_zoning"]]
    r = _write_block(ws, r, ["Density", "Land $/sqft", "n", "Median price"], [18, 12, 7, 14], zon, f) + 2
    ws.write(r, 0, "Size gradient — land $/sqft falls as lots get bigger", f["h2"]); r += 1
    acr = [[(a["band"], "txtb"), (a["land_ppsf"], "usd"), (a["per_acre"], "usd"), (a["n"], "num")]
           for a in lb["acreage"]]
    r = _write_block(ws, r, ["Lot size", "Land $/sqft", "$/acre", "n"], [14, 12, 12, 7], acr, f) + 2
    # docks
    dk = lb["docks"]
    ws.write(r, 0, f"Docks & dockominiums — {dk['n_sold']} sold "
             f"(${(dk['min_sold'] or 0):,}–${(dk['max_sold'] or 0):,}, median ${(dk['median_sold'] or 0):,.0f})",
             f["h2"]); r += 1
    dks = [[(s["address"], "txtb"), (s["neighborhood"] or "—", "txt"), (s["area"], "txt"),
            (s["price"], "usd"), ("Yes" if s["waterfront"] else "", "txt")] for s in dk["sales"]]
    r = _write_block(ws, r, ["Dock / slip", "Neighborhood", "Area", "Sold price", "WF"],
                     [24, 18, 8, 13, 5], dks, f) + 2
    # commercial land
    cm = lb.get("commercial")
    if cm:
        ws.write(r, 0, f"Commercial / development land — {cm['n_sold']} sold "
                 f"(median ${cm['median_ppsf_sold']}/sqft, ${cm['per_acre_sold']:,}/acre), "
                 f"{cm['n_active']} active", f["h2"]); r += 1
        cms = [[(s["address"], "txtb"), (s["area"], "txt"), (s["price"], "usd"),
                (s["lot_sqft"], "num"), (s["ppsf"], "usd"), (s["zoning"] or "—", "txt"),
                (s["location"] or "—", "txt")] for s in cm["sales"]]
        _write_block(ws, r, ["Address", "Area", "Sold price", "Lot sqft", "$/sqft", "Zoning", "Location"],
                     [24, 8, 13, 10, 10, 12, 34], cms, f)
    ws.hide_gridlines(2)


def income_sheet(wb, ib):
    f = _blk_formats(wb)
    m = ib["meta"]
    vfmt = _verdict_fmt(wb)
    ws = wb.add_worksheet("Multifamily")
    ws.write(0, 0, "Residential income (small multifamily) — $/unit & $/sqft comps", f["title"])
    ws.write(1, 0, f"{m['n_sold']} sold ({m['n_fll_sold']} Fort Lauderdale). Median "
             f"${m['median_ppu']:,}/unit, ${m['median_ppsf']}/sqft. {m['n_neighborhoods']} "
             f"neighborhoods; {m['n_over']} asking over recent comps, {m['n_under']} under. "
             "Price-comp layer — cap rate/GRM need a rent roll.", f["sub"])
    ws.set_row(1, 30)
    r = 3
    heads = ["Neighborhood", "Sold", "$/unit", "$/sqft", "Median units", "Median price",
             "WF %", "Active", "Active $/unit", "Ask vs sold", "Verdict"]
    widths = [22, 7, 12, 10, 12, 14, 7, 8, 13, 12, 15]
    rows = []
    for x in ib["by_neighborhood"]:
        rows.append([(x["neighborhood"], "txtb"), (x["n_sold"], "num"), (x["ppu"], "usd"),
                     (x["ppsf"], "usd"), (x["median_units"], "num"), (x["median_price"], "usd"),
                     (round(x["waterfront_share"] * 100), "pct"), (x["n_active"], "num"),
                     (x["active_ppu"], "usd"), (x["gap_pct"], "sgn"), (x["verdict"] or "—", "txt")])
    end = _write_block(ws, r, heads, widths, rows, f)
    vcol = len(heads) - 1
    for i, x in enumerate(ib["by_neighborhood"]):
        if x["verdict"] in vfmt:
            ws.write(r + 1 + i, vcol, x["verdict"], vfmt[x["verdict"]])
    ws.conditional_format(r + 1, 2, end - 1, 2, {"type": "3_color_scale", "min_color": "#e8f1fc",
        "mid_color": "#86b6ef", "max_color": BLUE})
    # by tier
    r2 = end + 2
    ws.write(r2, 0, "By building size — $/unit and $/sqft", f["h2"]); r2 += 1
    tier = [[(t["tier"], "txtb"), (t["n"], "num"), (t["ppu"], "usd"), (t["ppsf"], "usd"),
             (t["median_price"], "usd")] for t in ib["by_tier"]]
    r2 = _write_block(ws, r2, ["Unit tier", "n", "$/unit", "$/sqft", "Median price"],
                      [16, 7, 12, 10, 14], tier, f) + 2
    # active inventory repriced
    ws.write(r2, 0, "Active multifamily — asking vs supported (neighborhood $/unit × units)", f["h2"]); r2 += 1
    act = [[(a["address"], "txtb"), (a["neighborhood"], "txt"), (a["units"], "num"),
            (a["price"], "usd"), (a["ppu"], "usd"), (a["supported_price"], "usd"),
            (a["gap_pct"], "sgn"), (a["year_built"], "num"), ("Yes" if a["waterfront"] else "", "txt")]
           for a in ib["actives"][:60]]
    _write_block(ws, r2, ["Address", "Neighborhood", "Units", "List price", "$/unit",
                 "Supported", "Gap", "Year", "WF"], [24, 20, 7, 13, 11, 13, 9, 8, 5], act, f)
    ws.hide_gridlines(2)


def accuracy_sheet(wb, bt):
    f = _blk_formats(wb)
    o, m = bt["overall"], bt["meta"]
    ws = wb.add_worksheet("Model Accuracy")
    ws.write(0, 0, "Model accuracy — how close the pricing model actually gets", f["title"])
    ws.write(1, 0, m["headline"] + "  This is out-of-sample: the model is repeatedly fit on "
             f"{100 - 100 // m['n_folds']}% of sales and scored on the held-out rest it never "
             "saw — an honest error you can quote, not an in-sample fit.", f["sub"])
    ws.set_row(1, 42)
    pct = wb.add_format({"num_format": '0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"})
    r = _write_block(ws, 3, ["Metric", "Value"], [30, 18], [
        [("Median absolute error", "txtb"), (o["mdape"] / 100, "pct")],
        [("Typical dollar error (median)", "txtb"), (o["median_dollar_err"], "usd")],
        [("Within ±10% of sale price", "txtb"), (o["within10"] / 100, "pct")],
        [("Within ±20% of sale price", "txtb"), (o["within20"] / 100, "pct")],
        [("Closed sales scored", "txtb"), (m["n_scored"], "num")],
        [("Coverage of all sales", "txtb"), (m["coverage_pct"] / 100, "pct")],
    ], {**f, "pct": pct}) + 2
    ws.write(r, 0, "Accuracy by price band — tighter in the mid-market, looser in luxury", f["h2"])
    r += 1
    rows = [[(b["band"], "txtb"), (b["n"], "num"), (b["mdape"] / 100, "pct"),
             (b["within10"] / 100, "pct"), (b["within20"] / 100, "pct")] for b in bt["by_band"]]
    r = _write_block(ws, r, ["Price band", "n", "Median error", "Within ±10%", "Within ±20%"],
                     [12, 7, 13, 12, 12], rows, {**f, "pct": pct}) + 2
    ws.write(r, 0, "Accuracy by property type", f["h2"])
    r += 1
    rows = [[(p["ptype"], "txtb"), (p["n"], "num"), (p["mdape"] / 100, "pct"),
             (p["within10"] / 100, "pct")] for p in bt["by_ptype"]]
    _write_block(ws, r, ["Type", "n", "Median error", "Within ±10%"], [16, 7, 13, 12], rows,
                 {**f, "pct": pct})
    ws.hide_gridlines(2)


def marketing_sheet(wb, mk):
    ws = wb.add_worksheet("Marketing Kit")
    title = wb.add_format({"bold": True, "font_size": 16, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781", "text_wrap": True})
    h2 = wb.add_format({"bold": True, "font_size": 12, "font_color": BLUE})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": BLUE, "border": 1,
                         "border_color": "white", "valign": "vcenter", "align": "center", "text_wrap": True})
    nb = wb.add_format({"bold": True, "border": 1, "border_color": "#e1e0d9", "valign": "top"})
    body = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                          "text_wrap": True, "font_size": 10})
    ws.write(0, 0, "Marketing Kit — copy-ready, data-backed content", title)
    ws.write(1, 0, "Paste these into emails, CMAs, postcards and posts. " + (mk["meta"].get("note") or ""),
             sub)
    ws.set_row(1, 28)
    # market pulse + stat cards
    ws.write(3, 0, "Citywide market pulse (for a monthly update email / reel)", h2)
    ws.merge_range(4, 0, 4, 4, mk["market_pulse"], body)
    ws.set_row(4, 60)
    ws.write(6, 0, "Stat cards", h2)
    for c, card in enumerate(mk["stat_cards"]):
        ws.write(7, c, f"{card['value']}\n{card['label']}\n{card['note']}",
                 wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top",
                                "text_wrap": True, "align": "center", "font_size": 10}))
    ws.set_row(7, 54)
    # per-neighborhood content
    r = 9
    ws.write(r, 0, "By neighborhood — snapshot, shareable stat, and the CMA line", h2)
    r += 1
    heads = ["Neighborhood", "Market snapshot (email / CMA)", "Shareable stat (social)", "CMA / pricing line"]
    widths = [20, 74, 40, 60]
    for c, (hh, wd) in enumerate(zip(heads, widths)):
        ws.write(r, c, hh, hdr)
        ws.set_column(c, c, wd)
    r += 1
    for k in sorted(mk["neighborhoods"], key=lambda x: (x["rank"] or 999)):
        if not k.get("snapshot"):
            continue
        ws.write(r, 0, k["neighborhood"], nb)
        ws.write(r, 1, k["snapshot"], body)
        ws.write(r, 2, k.get("shareable") or "", body)
        ws.write(r, 3, k.get("cma_line") or "", body)
        ws.set_row(r, 15 * max(3, len(k["snapshot"]) // 62 + 1))
        r += 1
    # prospect outreach lines
    r += 1
    ws.write(r, 0, f"Prospect outreach lines ({len(mk['prospects'])}) — open a listing conversation", h2)
    r += 1
    for c, hh in enumerate(["Address", "Neighborhood", "Asked", "Outreach message"]):
        ws.write(r, c, hh, hdr)
    ws.set_column(3, 3, 90)
    r += 1
    usd = wb.add_format({"num_format": "$#,##0", "border": 1, "border_color": "#e1e0d9", "valign": "top"})
    for p in mk["prospects"]:
        ws.write(r, 0, p["address"], nb)
        ws.write(r, 1, p["neighborhood"], body)
        ws.write_number(r, 2, p["asked"] or 0, usd)
        ws.write(r, 3, p["line"], body)
        ws.set_row(r, 15 * max(2, len(p["line"]) // 78 + 1))
        r += 1
    ws.freeze_panes(3, 0)
    ws.hide_gridlines(2)


def costs_sheet(wb, cx):
    f = _blk_formats(wb)
    ws = wb.add_worksheet("Costs & Realities")
    ws.write(0, 0, "Costs & market realities — build, renovate, hold, and build-vs-buy", f["title"])
    ws.write(1, 0, cx["meta"].get("note", ""), f["sub"])
    ws.set_row(1, 30)
    b = cx["benchmarks"]
    r = 3
    ws.write(r, 0, "Cost benchmarks (sourced South Florida / Broward estimates — editable in config)", f["h2"])
    r += 1
    rows = [[(c["tier"], "txtb"), (c["psf"], "usd"), ("$/sqft — new construction, hard cost", "txt")]
            for c in b["construction"]]
    rows += [[(c["tier"], "txtb"), (c["psf"], "usd"), ("$/sqft — renovation", "txt")] for c in b["rehab"]]
    rows += [
        [("Soft costs", "txtb"), (b["soft_cost_pct"], "num"), ("% on top of hard cost (design/permits/GC/financing)", "txt")],
        [("Seawall replacement", "txtb"), (b["seawall_psf_lf"][0], "usd"), (f"to ${b['seawall_psf_lf'][1]:,}/linear foot", "txt")],
        [("New dock", "txtb"), (b["dock_build"][0], "usd"), (f"to ${b['dock_build'][1]:,} typical residential", "txt")],
        [("Boat lift", "txtb"), (b["boatlift_per_1000lb"], "usd"), ("per 1,000 lb (~$38k for a 24k-lb lift)", "txt")],
        [("Insurance — canal", "txtb"), (b["insurance_annual"]["canal"][0], "usd"), (f"to ${b['insurance_annual']['canal'][1]:,}/yr", "txt")],
        [("Insurance — Intracoastal", "txtb"), (b["insurance_annual"]["intracoastal"][0], "usd"), (f"to ${b['insurance_annual']['intracoastal'][1]:,}/yr", "txt")],
        [("Insurance — oceanfront", "txtb"), (b["insurance_annual"]["oceanfront"][0], "usd"), (f"to ${b['insurance_annual']['oceanfront'][1]:,}+/yr", "txt")],
    ]
    r = _write_block(ws, r, ["Item", "Figure", "Basis"], [26, 14, 52], rows, f) + 2
    ws.write(r, 0, "Market realities to know & talk to", f["h2"])
    r += 1
    factf = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top", "text_wrap": True, "font_size": 10})
    srcf = wb.add_format({"border": 1, "border_color": "#e1e0d9", "valign": "top", "font_size": 9, "font_color": "#898781"})
    ws.write(r, 0, "Reality", f["hdr"]); ws.write(r, 1, "Source", f["hdr"])
    r += 1
    for fact in cx["market_facts"]:
        ws.write(r, 0, fact["fact"], factf)
        ws.write(r, 1, fact["src"], srcf)
        ws.set_row(r, 15 * max(2, len(fact["fact"]) // 60 + 1))
        r += 1
    r += 1
    ws.write(r, 0, "Build-vs-buy by neighborhood — finished resale vs all-in replacement cost", f["h2"])
    r += 1
    bvb = [[(x["neighborhood"], "txtb"), (x["resale_psf"], "usd"), (x["replacement_psf_typ"], "usd"),
            (x["land_ppsf"], "usd"), (x["build_total_lo"], "usd"), (x["build_total_hi"], "usd"),
            (x["premium_to_replacement_pct"], "sgn"), (x["verdict"].split("—")[0].strip(), "txt")]
           for x in sorted(cx["neighborhoods"], key=lambda z: (z.get("rank") or 999))]
    _write_block(ws, r, ["Neighborhood", "Resale $/sqft", "Replace $/sqft", "Land $/sqft",
                 "Build all-in (low)", "Build all-in (high)", "vs Replace", "Build vs buy"],
                 [20, 13, 14, 11, 16, 16, 11, 30], bvb, f)
    ws.set_column(0, 0, 20)
    # sources footer
    r2 = r + len(bvb) + 2
    ws.write(r2, 0, "Sources", f["h2"])
    for i, s in enumerate(cx.get("sources", [])):
        ws.write_url(r2 + 1 + i, 0, s["url"], wb.add_format({"font_color": BLUE, "underline": 1}), s["label"])
    ws.hide_gridlines(2)


def leasing_sheet(wb, lz):
    f = _blk_formats(wb)
    m = lz["meta"]
    ws = wb.add_worksheet("Leasing & Yield")
    ws.write(0, 0, "Leasing & yield — rent, gross yield, and the sell-vs-hold read", f["title"])
    src = (f"{m['n_lease_comps']} real lease comps" if m.get("has_lease_comps")
           else "sourced rent benchmarks (drop MLS lease exports in data/raw/lease/ for real comps)")
    ws.write(1, 0, f"City rent ~${m['city_median_rent']:,}/mo (houses ~${m['house_median_rent']:,}), "
             f"~${m['city_rent_psf_yr']}/sqft/yr, ~{m['gross_yield_city_pct']}% gross yield at the median. "
             f"Source: {src}. " + (m.get("note") or ""), f["sub"])
    ws.set_row(1, 42)
    r = 3
    for fct in lz.get("facts", []):
        ws.write(r, 0, "• " + fct, wb.add_format({"text_wrap": True, "valign": "top", "font_size": 10}))
        ws.set_row(r, 15 * max(1, len(fct) // 95 + 1)); r += 1
    r += 1
    heads = ["Neighborhood", "Est. rent/mo", "Rent $/sqft/yr", "Sale $/sqft", "Gross yield",
             "GRM", "Basis", "Sell vs hold"]
    widths = [22, 13, 14, 12, 12, 8, 16, 52]
    yv = wb.add_format({"num_format": '0.0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"})
    rows = []
    for x in lz["neighborhoods"]:
        rows.append([(x["neighborhood"], "txtb"), (x["est_monthly_rent"], "usd"),
                     (x["rent_psf_yr"], "usd"), (x["sale_ppsf"], "usd"),
                     (x["gross_yield_pct"] / 100 if x["gross_yield_pct"] is not None else None, "y"),
                     (x["grm"], "num"), (x["rent_basis"], "txt"), (x["verdict"], "txt")])
    _write_block(ws, r, heads, widths, rows, {**f, "y": yv})
    ws.conditional_format(r + 1, 4, r + len(rows), 4, {"type": "3_color_scale",
        "min_color": "#f6b6b6", "mid_color": "#f0efec", "max_color": "#8fd48f"})
    ws.freeze_panes(3, 0)
    ws.hide_gridlines(2)


def _dominant_market(nb, absorb):
    rows = [r for r in (absorb or {}).get("by_band_neighborhood", []) if r["neighborhood"] == nb]
    c = {}
    for r in rows:
        if r.get("market"):
            c[r["market"]] = c.get(r["market"], 0) + 1
    return max(c, key=c.get) if c else None


def neighborhood_systems_sheet(wb, mb, ctx, lease, absorb, mm):
    """One row per neighborhood = the whole system: renormalized pricing (asking vs
    should-be, adjusted up/down), value, waterfront, build-vs-buy, yield, market."""
    ws = wb.add_worksheet("Neighborhood Pricing")
    title = wb.add_format({"bold": True, "font_size": 15, "font_color": DARK})
    sub = wb.add_format({"font_size": 10, "italic": True, "font_color": "#898781", "text_wrap": True})
    hdr = wb.add_format({"bold": True, "font_color": "white", "bg_color": DARK, "border": 1,
                         "border_color": "white", "align": "center", "valign": "vcenter", "text_wrap": True})
    txt = wb.add_format({"border": 1, "border_color": "#e1e0d9"})
    nbf = wb.add_format({"border": 1, "border_color": "#e1e0d9", "bold": True})
    usd = wb.add_format({"num_format": "$#,##0", "border": 1, "border_color": "#e1e0d9", "align": "center"})
    sgn = wb.add_format({"num_format": '+0.0"%";-0.0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"})
    pct = wb.add_format({"num_format": '0.0"%"', "border": 1, "border_color": "#e1e0d9", "align": "center"})
    up = wb.add_format({"bold": True, "font_color": "#0f8a3c", "border": 1, "border_color": "white", "align": "center"})
    dn = wb.add_format({"bold": True, "font_color": "#b23b28", "border": 1, "border_color": "white", "align": "center"})
    fl = wb.add_format({"bold": True, "font_color": "#52514e", "border": 1, "border_color": "white", "align": "center"})

    cxb = {c["neighborhood"]: c for c in (ctx or {}).get("neighborhoods", [])}
    lzb = {l["neighborhood"]: l for l in (lease or {}).get("neighborhoods", [])}
    sqftb = {n["neighborhood"]: n.get("median_sqft") for n in (mm or {}).get("neighborhoods", [])}

    ws.write(0, 0, "Neighborhood pricing & systems — every neighborhood, every metric, one row", title)
    ws.write(1, 0, "Renormalized pricing (now-asking vs should-be, adjusted up or down) plus the full "
             "system: value, waterfront, build-vs-buy, rental yield and market. Same content as the "
             "per-neighborhood PDF reports. 'Action': Reduce = asking above comps, Raise = below.", sub)
    ws.set_row(1, 30)
    heads = ["#", "Neighborhood", "Geography", "Now asking $/ft²", "Should-be $/ft²", "Adjust",
             "Action", "$ impact /home", "Normalized $/ft²", "vs City", "Waterfront $/ft²",
             "Replace $/ft²", "vs Replace", "Est. rent/mo", "Gross yield", "Sell vs hold",
             "Median sold $", "Discount", "Apprec '20", "Live ≥$1M"]
    widths = [4, 22, 20, 14, 14, 9, 10, 13, 14, 8, 14, 12, 10, 12, 10, 30, 14, 9, 10, 9]
    top = 3
    for c, (h, wd) in enumerate(zip(heads, widths)):
        ws.write(top, c, h, hdr)
        ws.set_column(c, c, wd)
    r = top
    for m in mb["neighborhoods"]:
        r += 1
        nb = m["neighborhood"]
        cx, lz = cxb.get(nb, {}), lzb.get(nb, {})
        a, s, adj = m.get("asking_ppsf"), m.get("should_be_ppsf"), m.get("suggested_adjust_pct")
        sqft = sqftb.get(nb)
        impact = (s - a) * sqft if (a is not None and s is not None and sqft) else None
        act = "Reduce" if (adj or 0) < -1 else "Raise" if (adj or 0) > 1 else "Hold" if adj is not None else "—"
        actfmt = dn if act == "Reduce" else up if act == "Raise" else fl

        def w(col, val, fmt):
            if val is None:
                ws.write(r, col, "", txt)
            elif fmt in (usd, sgn, pct):
                ws.write_number(r, col, float(val), fmt)
            else:
                ws.write(r, col, val, fmt)

        w(0, m.get("rank"), txt); w(1, nb, nbf); w(2, m.get("geo_type") or "—", txt)
        w(3, a, usd); w(4, s, usd)
        ws.write_number(r, 5, adj, sgn) if adj is not None else ws.write(r, 5, "", txt)
        ws.write(r, 6, act, actfmt)
        w(7, impact, usd); w(8, m.get("norm_ppsf"), usd)
        ws.write_number(r, 9, m.get("vs_city_pct"), sgn) if m.get("vs_city_pct") is not None else ws.write(r, 9, "", txt)
        w(10, m.get("waterfront_ppsf"), usd)
        w(11, cx.get("replacement_psf_typ"), usd)
        ws.write_number(r, 12, cx["premium_to_replacement_pct"], sgn) if cx.get("premium_to_replacement_pct") is not None else ws.write(r, 12, "", txt)
        w(13, lz.get("est_monthly_rent"), usd)
        ws.write_number(r, 14, lz["gross_yield_pct"] / 100, pct) if lz.get("gross_yield_pct") is not None else ws.write(r, 14, "", txt)
        ws.write(r, 15, (lz.get("verdict") or "—").split("—")[0].strip(), txt)
        w(16, m.get("median_sale_price"), usd)
        ws.write_number(r, 17, m.get("median_discount_pct"), pct) if m.get("median_discount_pct") is not None else ws.write(r, 17, "", txt)
        ws.write_number(r, 18, m.get("appreciation_since_2020"), sgn) if m.get("appreciation_since_2020") is not None else ws.write(r, 18, "", txt)
        w(19, m.get("n_high_ticket"), txt)
    n = len(mb["neighborhoods"])
    ws.conditional_format(top + 1, 5, top + n, 5, {"type": "3_color_scale",
        "min_color": "#0f8a3c", "mid_color": "#f0efec", "max_color": "#d5473f"})   # adjust
    ws.conditional_format(top + 1, 14, top + n, 14, {"type": "3_color_scale",
        "min_color": "#f6b6b6", "mid_color": "#f0efec", "max_color": "#8fd48f"})   # yield
    ws.freeze_panes(top + 1, 2)
    ws.autofilter(top, 0, top + n, len(heads) - 1)
    ws.hide_gridlines(2)


SHEET_INDEX = {
    "Key Conclusions": ("Start here", "Every headline finding with the evidence behind it and a confidence rating."),
    "Neighborhood Pricing": ("Start here", "THE consolidated view — one row per neighborhood: renormalized pricing (asking vs should-be, adjusted up/down), value, waterfront, build-vs-buy, yield & market. Same as the PDF reports."),
    "Leasing & Yield": ("Marketing & proof", "Estimated rent, rent $/sqft, gross yield, GRM and a sell-vs-hold verdict per neighborhood — the owner's rent-or-sell conversation."),
    "Marketing Kit": ("Marketing & proof", "Copy-ready market snapshots, shareable stats, CMA lines, buyer opportunities and prospect outreach — per neighborhood. Paste into emails, CMAs, postcards, posts."),
    "Model Accuracy": ("Marketing & proof", "Out-of-sample backtest of the pricing model — median error in $ and %, by band and type. Your \"data-backed pricing\" proof."),
    "Costs & Realities": ("Marketing & proof", "Construction, renovation, seawall, dock & insurance benchmarks; market realities with sources; and build-vs-buy (replacement cost) per neighborhood."),
    "Master Ranking": ("Start here", "All neighborhoods, most to least expensive, with suggested repricing and every core metric."),
    "Scenario": ("Deal tools", "Live financing / capital-markets model — edit the yellow cells and watch price, $/sqft, DOM & returns move. Recreate for any asset class."),
    "Read Me": ("Start here", "What 'normalized' means, the model, price drivers, validation and honest limits."),
    "Band x Neighborhood": ("High-ticket (≥$1M)", "How each price band behaves WITHIN each neighborhood — sold vs asked, per band, per area."),
    "High-Ticket Underwriting": ("High-ticket (≥$1M)", "Every live listing ≥$1M repriced to a suggested list, with comp confidence."),
    "Underpriced + Why": ("High-ticket (≥$1M)", "Live listings asking below comp-supported value, ranked by dollar opportunity, with generated reasons."),
    "Price Bands": ("High-ticket (≥$1M)", "The luxury market by tier — median asking vs supported $/sqft and over/under counts."),
    "Absorption": ("High-ticket (≥$1M)", "Months of supply by price band and by band within each neighborhood."),
    "Seller Prospects": ("Prospecting", "≥$1M owners who tried and couldn't (failed listings) — your listing-appointment pitch."),
    "Overpriced Actives": ("Prospecting", "Currently overpriced live listings — tomorrow's expireds to approach for a reduction."),
    "Teardown Land Plays": ("Prospecting", "Single-family listings where land value is most of the ask — redevelopment candidates (comp-backed where land sales exist)."),
    "Land Comps": ("Real assets", "Comp-backed vacant-land $/sqft by neighborhood, active land inventory, and implied-vs-actual land value."),
    "Land Geography & Docks": ("Real assets", "Land $/sqft by lot geography, zoning/density and size; plus boat-dock/dockominium sales and commercial-land comps."),
    "Multifamily": ("Real assets", "Small-multifamily (duplex/tri/quad) $/unit & $/sqft comps by neighborhood and unit tier, with active inventory repriced."),
    "Comps Drill-Down": ("High-ticket (≥$1M)", "The actual comparable sales behind each ≥$1M valuation — filter by listing to defend a number."),
    "Neighborhood Profiles": ("Neighborhood detail", "Copy-ready, data-backed talking points for a homeowner conversation, one row per neighborhood."),
    "Normalized Ranking": ("Neighborhood detail", "Per-home normalized $/sqft with waterfront / new / by-type / land angles for every neighborhood."),
    "Price Drivers": ("Neighborhood detail", "Marginal effect of waterfront, pool, new construction, baths and age on $/sqft, with 95% ranges."),
    "Live Deals": ("Neighborhood detail", "Live single-family listings priced below the per-home model."),
    "Condo Repricing": ("Repricing", "Condo asking vs. recent SOLD comps per neighborhood, with a verdict."),
    "Neighborhood Repricing": ("Repricing", "All-property asking vs. recent sold per neighborhood."),
    "Repriced Inventory": ("Repricing", "Every live listing repriced to a should-be price vs its current list."),
    "Street Value": ("Street level", "Sold $/sqft per street and its premium/discount vs the surrounding neighborhood."),
    "Deal Underwriting": ("Street level", "Live single-family listings priced below their own street's comp value."),
    "SFR Rankings (Redfin)": ("Redfin context", "Single-family normalized $/sqft ranking from the independent Redfin layer."),
    "Condo Rankings": ("Redfin context", "Condo/co-op normalized $/sqft ranking (Redfin)."),
    "Townhouse Rankings": ("Redfin context", "Townhouse normalized $/sqft ranking (Redfin)."),
    "Buyer Leverage": ("Redfin context", "Where buyers have negotiating leverage (DOM + discount + price drops + supply)."),
    "Appreciation": ("Redfin context", "Fastest-appreciating neighborhoods by annualized $/sqft growth."),
    "Market Index": ("Redfin context", "Quality-adjusted citywide $/sqft appreciation index over time."),
}


def index_sheet(wb, ws):
    """Populate the Index / table-of-contents sheet with links to every tab. Called
    LAST, once all worksheets exist, so it can enumerate them in order."""
    title = wb.add_format({"bold": True, "font_size": 18, "font_color": DARK})
    sub = wb.add_format({"font_size": 10.5, "italic": True, "font_color": "#898781", "text_wrap": True})
    grp = wb.add_format({"bold": True, "font_size": 12, "font_color": "white", "bg_color": DARK,
                         "border": 1, "border_color": "white", "valign": "vcenter"})
    link = wb.add_format({"font_color": BLUE, "bold": True, "underline": 1, "border": 1,
                          "border_color": "#e1e0d9", "valign": "vcenter"})
    desc = wb.add_format({"font_size": 10, "text_wrap": True, "valign": "vcenter",
                          "border": 1, "border_color": "#e1e0d9", "font_color": "#4a5c6b"})
    ws.set_column(0, 0, 34)
    ws.set_column(1, 1, 92)
    ws.write(0, 0, "Fort Lauderdale — Deal Dashboard", title)
    ws.write(1, 0, "One workbook, everything inside. Click any row below to jump to that tab — tabs "
             "are colour-coded by the coloured section headings here. New to it? Start with "
             "Neighborhood Pricing (every neighborhood in one row) and Key Conclusions.", sub)
    ws.set_row(1, 44)
    names = [w.name for w in wb.worksheets() if w.name != "Index"]
    order = ["Start here", "Marketing & proof", "Deal tools", "High-ticket (≥$1M)",
             "Prospecting", "Real assets", "Repricing", "Neighborhood detail", "Street level",
             "Redfin context", "Other"]
    # a distinct tab colour per section, so the 30+ tabs read as coloured groups
    GCOL = {"Start here": "#0d3b66", "Marketing & proof": "#0f8a3c", "Deal tools": "#e0623a",
            "High-ticket (≥$1M)": "#7b4fa3", "Prospecting": "#c98a12", "Real assets": "#2a9d8f",
            "Repricing": "#d5473f", "Neighborhood detail": "#1f6fb2", "Street level": "#8a5a10",
            "Redfin context": "#8a94a0", "Other": "#8a94a0"}
    grp_fmts = {g: wb.add_format({"bold": True, "font_size": 12, "font_color": "white",
                                  "bg_color": GCOL[g], "border": 1, "border_color": "white",
                                  "valign": "vcenter"}) for g in order}
    grouped = {g: [] for g in order}
    sheet_group = {}
    for nm in names:
        g, d = SHEET_INDEX.get(nm, ("Other", ""))
        grouped[g].append((nm, d))
        sheet_group[nm] = g
    r = 3
    for g in order:
        rows = grouped[g]
        if not rows:
            continue
        ws.merge_range(r, 0, r, 1, g, grp_fmts[g])
        ws.set_row(r, 20)
        r += 1
        for nm, d in rows:
            ws.write_url(r, 0, f"internal:'{nm}'!A1", link, nm)
            ws.write(r, 1, d, desc)
            ws.set_row(r, 28)
            r += 1
    ws.hide_gridlines(2)
    ws.set_zoom(110)
    ws.set_tab_color("#0d3b66")

    # colour every sheet's tab by its section, and drop a "back to Index" link top-right
    back = wb.add_format({"font_color": "#1f6fb2", "bold": True, "underline": 1})
    for w in wb.worksheets():
        if w.name == "Index":
            continue
        w.set_tab_color(GCOL.get(sheet_group.get(w.name, "Other"), "#8a94a0"))
        try:
            w.write_url("H1", "internal:'Index'!A1", back, "◄ Index")
        except Exception:  # noqa: BLE001 -- never let a nav link break the build
            pass
    ws.activate()          # open the workbook on the Index tab


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

    # Index is created FIRST so it lands as tab #1, but populated LAST (needs all sheets).
    ws_index = wb.add_worksheet("Index")

    try:
        try:
            rb = _reprice()
        except FileNotFoundError:
            rb = None
        key_conclusions_sheet(wb, mm, b, _time(), _street(), rb)
    except FileNotFoundError:
        pass
    try:
        _mb = _master()
        master_sheet(wb, fmts, _mb)
        try:
            neighborhood_systems_sheet(wb, _mb, _jload_opt("context_bundle.json"),
                                       _jload_opt("lease_bundle.json"), _jload_opt("absorption_bundle.json"), mm)
        except Exception as e:  # noqa: BLE001 -- consolidated tab is best-effort
            print("  (neighborhood systems tab skipped:", e, ")")
        scenario_sheet(wb, _mb)
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
    for fn, arg in [(absorption_sheet, "absorption_bundle.json"),
                    (seller_sheet, "seller_bundle.json"),
                    (teardown_sheet, "teardown_bundle.json")]:
        try:
            fn(wb, fmts, _jload(arg))
        except FileNotFoundError:
            pass
    try:
        comps_sheet(wb, fmts)
    except FileNotFoundError:
        pass

    # ---- REAL ASSETS: land, docks, commercial land, multifamily ----
    try:
        lb = _jload("land_bundle.json")
        land_comps_sheet(wb, lb)
        land_geo_sheet(wb, lb)
    except FileNotFoundError:
        pass
    try:
        income_sheet(wb, _jload("income_bundle.json"))
    except FileNotFoundError:
        pass

    # ---- MARKETING & PROOF ----
    try:
        marketing_sheet(wb, _jload("marketing_bundle.json"))
    except FileNotFoundError:
        pass
    try:
        accuracy_sheet(wb, _jload("backtest_bundle.json"))
    except FileNotFoundError:
        pass
    try:
        costs_sheet(wb, _jload("context_bundle.json"))
    except FileNotFoundError:
        pass
    try:
        leasing_sheet(wb, _jload("lease_bundle.json"))
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

    index_sheet(wb, ws_index)
    wb_writer.close()
    print("Wrote", XLSX)


if __name__ == "__main__":
    main()
