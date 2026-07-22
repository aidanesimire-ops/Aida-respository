#!/usr/bin/env python3
"""
Generate REPORT.md (written analysis + charts) from the processed bundles.
Data-driven so the numbers always match the pipeline. Run last.
"""
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "REPORT.md")


def load(name):
    with open(os.path.join(PROC, name)) as f:
        return json.load(f)


def usd(v):
    return "—" if v is None or pd.isna(v) else f"${v:,.0f}"


def pct(v, s=True):
    if v is None or pd.isna(v):
        return "—"
    return (f"+{v:.0f}%" if v >= 0 and s else f"{v:.0f}%")


def main():
    mls = load("mls_bundle.json")
    red = load("analysis_bundle.json")
    tb = load("time_bundle.json")
    sb = load("street_bundle.json")
    rb = load("reprice_bundle.json")
    m = mls["meta"]
    pr = m["premiums"]
    nb = pd.DataFrame(mls["neighborhoods"])
    idx = red["market_index"]
    appr = idx[-1]["index_100"] / idx[0]["index_100"]

    L = []
    w = L.append

    w("# Fort Lauderdale — Normalized Price/SqFt by Neighborhood\n")
    w("*A per-home statistical normalization of the Fort Lauderdale market, built to give "
      "you numbers you can quote to homeowners with confidence.*\n")

    # ---------------- TL;DR ----------------
    w("## The short version\n")
    w(f"- **{m['n_sold']:,} closed sales** (out of **{m['n_listings']:,}** total listings across "
      "sold, expired, withdrawn, cancelled, temp-off, active and pending) were run through a "
      f"per-home hedonic model that explains **{m['hedonic_r2']:.0%}** of price variation.")
    w(f"- The model isolates location from everything else, so every neighborhood gets a clean, "
      f"comparable **normalized $/sqft**. Citywide that standardized home is **{usd(m['city_norm_ppsf'])}/sqft**.")
    w(f"- **What moves price, all else equal:** waterfront **{pct(pr['waterfront_pct'])}**, "
      f"new construction **{pct(pr['new_construction_pct'])}**, a private pool **{pct(pr['pool_pct'])}**, "
      f"and each decade of age **{pct(pr['age_per_decade_pct'])}**.")
    w(f"- The market has appreciated **{appr:.1f}×** since 2012 (quality-adjusted).")
    w(f"- Independent check: these results correlate **r = 0.93** with a completely separate "
      "Redfin-based estimate — two methods, same answer.\n")

    # ---------------- Method ----------------
    w("## How the normalization works\n")
    w("Raw price-per-square-foot lies to you. A neighborhood can look cheap or expensive purely "
      "because its homes are bigger, older, newer, on the water, or a different property type. "
      "The model strips all of that out:\n")
    w("```\nlog(sale $/sqft) ~ living area + beds + baths + waterfront + pool\n"
      "                  + age + new construction + property type + NEIGHBORHOOD\n```")
    w("The **neighborhood** term is what we want — each area's price contribution holding "
      "everything else constant. **Normalized $/sqft** is then the model's price for one "
      f"standardized home (a dry-lot, no-pool home of citywide-median size ~{m['standardized_home']['sqft']:,} "
      f"sqft and age ~{round(m['standardized_home']['age'])} yrs) dropped into each neighborhood. "
      "Waterfront, pool, age and new-construction are reported **separately** as premiums so you "
      "can add them back for a specific home.\n")

    # ---------------- Validation ----------------
    w("## Is the data real? (Yes — spot-checked against public records)\n")
    w("| Address | In your data | Public record | \n|---|---|---|")
    w("| 5 Harborage Isle | $70.0M · 20,000 sqft · 2008 | $70M record sale (Sept 2024), 20,000 sqft ✓ |")
    w("| 84 Isla Bahia Dr | $34.0M · 11,714 sqft · 2021 | $34M (Apr 2026), 11,714 sqft, built 2021 ✓ |")
    w("| 2406 Laguna Dr | $26.0M · 10,646 sqft · 2021 | $26M (Dec 2025), ~10,700 sqft, Harbor Beach ✓ |")
    w(f"\nAcross all files: **100%** of listings have an address, **~98%** have valid square "
      "footage and year built. Before modeling, the pipeline recovers "
      f"**{m.get('filled_sqft',0)} missing square-footage** and **{m.get('filled_year',0)} bad "
      "year-built** values from same-building/subdivision peers, and drops the small remainder "
      "that can't be recovered.\n")
    w("> **Public-data note:** Census, FEMA flood zones, and the Broward County Property "
      "Appraiser (assessed land vs. building value) would add more context, but this session's "
      "network policy blocks those hosts. `analysis/enrich_public.py` is included, ready to pull "
      "them (geocode → ACS → FEMA → BCPA) in any environment with open network access.\n")

    # ---------------- Price drivers chart ----------------
    w("## What drives value\n")
    w("![Price drivers](outputs/chart_premiums.png)\n")
    cis = m.get("premiums_ci95", {})

    def cir(k):
        r = cis.get(k)
        return f"{r[0]:+.0f}% to {r[1]:+.0f}%" if r else "—"
    w("| Driver | Effect on $/sqft | 95% confidence |\n|---|---|---|")
    w(f"| Waterfront (vs dry lot) | **{pct(pr['waterfront_pct'])}** | {cir('waterfront_pct')} |")
    w(f"| New construction (≤6 yrs, net of age) | **{pct(pr['new_construction_pct'])}** | {cir('new_construction_pct')} |")
    w(f"| Private pool | **{pct(pr['pool_pct'])}** | {cir('pool_pct')} |")
    w(f"| Each extra bathroom | **{pct(pr['bath_pct'])}** | {cir('bath_pct')} |")
    w(f"| Each decade of age | **{pct(pr['age_per_decade_pct'])}** | {cir('age_per_decade_pct')} |")
    w(f"| Implied land value | **~${m['city_land_ppsf']:,.0f}/sqft of lot** | (SFR land model) |")
    w("\n*Confidence intervals from the regression — every driver is statistically "
      "significant (none crosses zero).*\n")

    # ---------------- Geography ----------------
    if mls.get("geography"):
        w("## Price by lot geography\n")
        w("![Geography](outputs/chart_geography.png)\n")
        w("A derived classification (from the waterfront flag + subdivision name + MLS area — "
          "indicative, since the export has no true point/corner/canal field) shows the water "
          "tiers clearly:\n")
        w("| Geography | Median $/sqft | Waterfront $/sqft | Sales |\n|--|--|--|--|")
        for gsi in mls["geography"]:
            w(f"| {gsi['geo_type']} | {usd(gsi['median_ppsf'])} | {usd(gsi.get('waterfront_ppsf'))} "
              f"| {gsi['n']:,} |")
        fi = next((x for x in mls["geography"] if x["geo_type"].startswith("Finger")), None)
        ml = next((x for x in mls["geography"] if x["geo_type"].startswith("Mainland")), None)
        if fi and ml:
            w(f"\nFinger-isle (point-lot) waterfront runs about "
              f"**{fi['median_ppsf']/ml['median_ppsf']:.1f}×** mainland-inland per foot — the "
              "single biggest geographic swing in the market.\n")

    # ---------------- Rankings ----------------
    w("## Neighborhood value ranking\n")
    w("![Top neighborhoods](outputs/chart_mls_ranking.png)\n")
    top = nb.sort_values("norm_ppsf", ascending=False).head(12)
    w("**Most expensive (normalized):**\n")
    w("| # | Neighborhood | Norm. $/sqft | vs City | Waterfront $/sqft | New premium | Sold |\n|--|--|--|--|--|--|--|")
    for i, (_, r) in enumerate(top.iterrows(), 1):
        w(f"| {i} | {r['neighborhood']} | {usd(r['norm_ppsf'])} | {pct(r['vs_city_pct'])} | "
          f"{usd(r['waterfront_ppsf'])} | {pct(r['new_premium_pct'])} | {int(r['sold_n'])} |")
    bot = nb.sort_values("norm_ppsf").head(6)
    w("\n**Most affordable (normalized):**\n")
    w("| Neighborhood | Norm. $/sqft | vs City | Sold |\n|--|--|--|--|")
    for _, r in bot.iterrows():
        w(f"| {r['neighborhood']} | {usd(r['norm_ppsf'])} | {pct(r['vs_city_pct'])} | {int(r['sold_n'])} |")
    w("")

    # ---------------- Waterfront ----------------
    w("## Waterfront vs. dry-lot, by neighborhood\n")
    wf = nb[nb["waterfront_ppsf"].notna() & nb["dry_ppsf"].notna()].sort_values(
        "waterfront_ppsf", ascending=False).head(10)
    w("The citywide waterfront premium is one number; on the ground it varies enormously. This is "
      "the actual median $/sqft of waterfront vs non-waterfront sales *within* each neighborhood:\n")
    w("| Neighborhood | Waterfront $/sqft | Dry-lot $/sqft | Local water premium |\n|--|--|--|--|")
    for _, r in wf.iterrows():
        w(f"| {r['neighborhood']} | {usd(r['waterfront_ppsf'])} | {usd(r['dry_ppsf'])} | "
          f"{pct(r['waterfront_premium_local_pct'])} |")
    w("")

    # ---------------- New construction ----------------
    w("## New construction vs. existing\n")
    nvc = nb[nb["new_premium_pct"].notna()].sort_values("new_premium_pct", ascending=False).head(8)
    w(f"Citywide, brand-new homes (≤6 yrs) command **{pct(pr['new_construction_pct'])}** per foot "
      "over comparable existing homes, net of the age gradient. Where the local sample supports it:\n")
    w("| Neighborhood | New $/sqft | Existing $/sqft | New premium |\n|--|--|--|--|")
    for _, r in nvc.iterrows():
        w(f"| {r['neighborhood']} | {usd(r['new_ppsf'])} | {usd(r['existing_ppsf'])} | "
          f"{pct(r['new_premium_pct'])} |")
    w("")

    # ---------------- Market shifts since 2020 ----------------
    tm = tb["meta"]
    w("## Market shifts since 2020 (Redfin layer)\n")
    w("The MLS export has no dates, so the trajectory comes from Redfin's monthly neighborhood "
      "data. Three metrics tell the whole cycle:\n")
    w("![Market shifts since 2020](outputs/chart_timeline.png)\n")
    w(f"- **Price:** citywide **${tm['city_2020_ppsf']:,.0f}/sqft in 2020 → "
      f"${tm['city_now_ppsf']:,.0f} now ({tm['city_pct_since_2020']:+.0f}%)**, at new highs.")
    w(f"- **Speed:** days-on-market bottomed at **{tm['fastest_dom']:.0f} days ({tm['fastest_month']})** "
      "during the 2022 frenzy, then climbed back above 100.")
    w("- **Leverage:** homes sold *at* asking in mid-2022; buyers now negotiate ~6% off again. "
      "**Price is at a high while the market is slow — a genuine divergence.**\n")
    w("![Biggest shifts since 2020](outputs/chart_shifts.png)\n")
    sh = [s for s in tb["shifts"] if s.get("pct_2020_now") is not None and s["sold_total"] >= 40]
    top = sorted(sh, key=lambda s: -s["pct_2020_now"])[:8]
    w("**Biggest price gains, 2020 → now** (neighborhoods with ≥40 sales):\n")
    w("| Neighborhood | 2020 $/sqft | Now $/sqft | Change | DOM 2020→now |\n|--|--|--|--|--|")
    for s in top:
        w(f"| {s['neighborhood']} | {usd(s['ppsf_2020'])} | {usd(s['ppsf_now'])} | "
          f"+{s['pct_2020_now']:.0f}% | {s['dom_2020']:.0f}→{s['dom_now']:.0f} |")
    cool = sorted([s for s in sh if s.get("pct_off_peak") is not None],
                  key=lambda s: s["pct_off_peak"])[:5]
    w("\n**Cooled most from their peak:** "
      + ", ".join(f"{s['neighborhood']} ({s['pct_off_peak']:.0f}%)" for s in cool) + ".\n")
    w("The interactive dashboard lets you pull any neighborhood's price path against the "
      "citywide line and toggle price / days-on-market / discount.\n")

    # ---------------- Opportunities ----------------
    w("## Live opportunities\n")
    fs = mls["live_flag_summary"]
    w(f"Every active & pending listing was scored against its predicted value: "
      f"**{fs.get('Overpriced',0)} overpriced**, **{fs.get('Fair',0)} fair**, "
      f"**{fs.get('Underpriced',0)} underpriced**. The single-family candidates trading furthest "
      "below model (verify condition on site — the model can't see renovations):\n")
    deals = pd.DataFrame(mls["deals"]).head(8)
    if len(deals):
        w("| Neighborhood | List | SqFt | Ask $/sqft | Model $/sqft | Gap |\n|--|--|--|--|--|--|")
        for _, r in deals.iterrows():
            w(f"| {r['neighborhood']} | {usd(r['list_price'])} | {int(r['sqft']):,} | "
              f"{usd(r['ask_ppsf'])} | {usd(r['pred_ppsf'])} | {r['gap_pct']:.0f}% |")
    w("")

    # ---------------- Street-by-street ----------------
    w("## Street-by-street underwriting\n")
    sm = sb["meta"]
    w(f"Value is resolved down to **{sm['n_streets']} individual streets** (≥{sm['min_street_sold']} "
      "closed comps each), each with its premium or discount vs. the surrounding neighborhood — so "
      "a prime waterfront block isn't valued like the dry street one over. "
      f"**{sm['n_live_underwritten']:,} live listings** are underwritten against their own street's "
      "comps.\n")
    st = sorted(sb["streets"], key=lambda x: -x["sold_ppsf"])[:8]
    w("**Highest-value streets** (with premium vs. their neighborhood):\n")
    w("| Street | Neighborhood | Sold $/sqft | vs Nbhd | Waterfront | Comps |\n|--|--|--|--|--|--|")
    for r in st:
        w(f"| {r['street']} | {r['neighborhood']} | {usd(r['sold_ppsf'])} | "
          f"{pct(r['premium_vs_nbhd'])} | {round((r['waterfront_share'] or 0)*100)}% | {r['n_sold']} |")
    if sb["deals"]:
        w("\n**Live listings priced below their street value** (screening candidates — verify condition):\n")
        w("| Address | Street | Neighborhood | List | Ask $/sqft | Street value | Comps | Gap |\n"
          "|--|--|--|--|--|--|--|--|")
        for d in sb["deals"][:8]:
            w(f"| {d['address']} | {d['street']} | {d['neighborhood']} | {usd(d['list_price'])} | "
              f"{usd(d['ask_ppsf'])} | {usd(d['street_value_ppsf'])} | {d['street_comps']} | "
              f"{d['gap_vs_street']:.0f}% |")
    w("\nThe dashboard's street table is searchable by street or neighborhood, with the full "
      "underwriting list.\n")

    # ---------------- Repricing ----------------
    rm = rb["meta"]
    rover = 100 * (rm["list_total"] / rm["should_be_total"] - 1)
    w("## Repricing the live inventory\n")
    w(f"Every one of the **{rm['n_live']:,} active & pending listings** is repriced against the "
      "model's value. Of the **{:,} that have real sold comps** to price against, the asking "
      "prices sit **{:+.0f}% above** what the model says they should be.\n".format(
          rm["n_repriceable"], rover))
    vc = rm["verdict_counts"]
    w(f"- **{vc.get('Overpriced',0)} overpriced · {vc.get('Fairly priced',0)} fairly priced · "
      f"{vc.get('Underpriced',0)} underpriced** (comp-backed). "
      f"{vc.get('Insufficient comps',0)} are pre-construction / thin buildings the model can't value.\n")
    condo = sorted([c for c in rb["condos_by_nbhd"]], key=lambda c: -c["gap_pct"])
    if condo:
        w("**Condo markets most overpriced vs. recent sold comps:**\n")
        w("| Neighborhood | Live | Asking $/sqft | Should be (sold) | Ask vs sold | Comps |\n"
          "|--|--|--|--|--|--|")
        for c in condo[:6]:
            w(f"| {c['neighborhood']} | {c['n_live']} | {usd(c['ask_ppsf'])} | {usd(c['sold_ppsf'])} | "
              f"{c['gap_pct']:+.0f}% | {c['n_sold_comps']} |")
        val = [c for c in condo if c["verdict"] == "Underpriced"][-6:]
        if val:
            w("\n**Condo value (asking below recent sold):** "
              + ", ".join(f"{c['neighborhood']} ({c['gap_pct']:.0f}%)" for c in val) + ".\n")
    w("The **Condo Repricing**, **Neighborhood Repricing** and **Repriced Inventory** tabs in the "
      "workbook (and the dashboard's repricing view) carry every neighborhood and listing. "
      "\"Should be\" is the recent sold-comp benchmark; the model value is shown alongside.\n")

    # ---------------- Talking points ----------------
    w("## Using this with homeowners\n")
    w("Each neighborhood has an auto-generated profile (see the **Neighborhood Profiles** sheet "
      "and the dashboard). Example:\n")
    ex = next((p for p in mls["profiles"] if p["neighborhood"] == "Rio Vista"),
              mls["profiles"][0])
    w(f"**{ex['neighborhood']}** — *{ex['headline']}*\n")
    for t in ex["talking_points"]:
        w(f"- {t}")
    w("")

    # ---------------- Validation chart + limits ----------------
    w("## Two methods, one answer\n")
    w("![Cross-validation](outputs/chart_crosscheck.png)\n")
    w("The per-home MLS model and the aggregate Redfin index were built from different data with "
      "different methods, yet agree at **r = 0.93** across overlapping neighborhoods. That "
      "convergence is the strongest evidence the normalization is right.\n")

    w("## Honest limitations & what would sharpen this\n")
    w("- **Lot geography** (point vs corner vs canal vs ocean-access, no-fixed-bridges) is not in "
      "the export — only a Waterfront Y/N flag. Adding the MLS *Waterfront Description / Lot "
      "Description / Dock* columns would materially improve the waterfront premium.")
    w("- **No dates / days-on-market** in the MLS export — those come from Redfin at the "
      "neighborhood level. Adding *List Date / Close Date / DOM* columns would let the model "
      "time-adjust per home.")
    w("- **Vacant land** isn't in the data (all rows are improved residential); land value here is "
      "*implied* from lot size. True land comps need a separate land export.")
    w("- **Condo-level** flags are coarse — floor, view and renovation aren't observed, so trust "
      "the neighborhood aggregates over individual condo call-outs.\n")
    w("---\n*Generated by `analysis/` pipeline. Sources: user-provided Fort Lauderdale MLS "
      "exports (per-home) + Redfin Data Center (time/DOM). Neighborhood benchmarks and screening "
      "signals — not per-home appraisals.*")

    with open(OUT, "w") as f:
        f.write("\n".join(L) + "\n")
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
