#!/usr/bin/env python3
"""Written analysis -> commercial/REPORT.md."""
from __future__ import annotations
import json
import os

import pandas as pd

import cre_common as CRE
import cre_assumptions as A
import cre_scenario as SC

OUT = os.path.join(CRE.ROOT, "REPORT.md")


def _load(n):
    p = os.path.join(CRE.PROC, n)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def main():
    cre = _load("cre_bundle.json")
    meta = cre["meta"]
    master = _load("master_bundle.json")
    reb = _load("reprice_bundle.json")
    seg = _load("segments_bundle.json")
    pros = _load("prospects_bundle.json")

    subs = pd.DataFrame(master["submarkets"]) if master else pd.DataFrame(cre["submarkets"])
    types = pd.DataFrame(cre["types"])

    L = []
    w = L.append
    w("# Commercial Deal Dashboard — Fort Lauderdale\n")
    w(f"Market intelligence on **{meta['n_listings']} commercial listings** "
      f"({meta['n_sale_comps']} valid sale comps, {meta['n_closed']} closed; "
      f"{meta['n_lease']} lease listings) from user-provided BeachesMLS exports "
      f"({', '.join(meta['sources'])}).\n")

    w("> **The source has no income data.** These MLS exports carry price, size, asset type, "
      "age, zoning and location — but **no NOI, rent, cap rate or unit counts**. So the "
      "factual layer here is **price-per-SqFt**, and every income figure (NOI, cap rate, value, "
      "returns) is **derived from editable industry-norm assumptions** you can tune live in the "
      "dashboard. Treat this as pricing & screening intelligence, not appraisal.\n")

    w("## Two layers\n")
    w("**1. Factual — normalized $/SqFt.** A hedonic strips size, age, asset type and the "
      "closed-vs-listed gap out of raw pricing so areas and property types are comparable:\n")
    w("```\nlog($/SqFt) ~ log(sqft) + age + closed + C(asset_type) + C(submarket)\n```\n")
    w(f"Fit R² = **{meta['hedonic_r2']}** (n={meta['hedonic_n']}); closed sales price about "
      f"**{meta['closed_vs_listed_pct']:.0f}%** vs live asks. Market-wide normalized "
      f"**${meta['city_norm_ppsf']:,.0f}/SqFt**.\n")
    w("**2. Assumption-driven — the income view.** For each asset class we assume a market rent "
      "($/SqFt/yr), vacancy, expense ratio and cap rate, then derive "
      "`NOI = SqFt × rent × (1−vacancy) × (1−opex)`, an implied cap at the asking price, and a "
      "value at the market cap. **Every one of those is a live control** — the whole point is to "
      "dial them to your read and watch value, cap and returns move.\n")

    w("### Default assumptions by asset class\n")
    w("| Asset type | Rent $/SqFt | Vacancy | Opex % EGI | Market cap | Median $/SqFt | # |")
    w("|---|---|---|---|---|---|---|")
    for _, r in types.iterrows():
        w(f"| {r['asset_type']} | ${r['assume_rent_psf']:.0f} | {r['assume_vacancy']*100:.0f}% | "
          f"{r['assume_opex_ratio']*100:.0f}% | {r['assume_cap_rate']*100:.2f}% | "
          f"${r['median_ppsf']:,.0f} | {int(r['n'])} |")
    w("\n*Defaults are calibrated so a typically-priced building of each type prices near its "
      "market cap, and are realistic South-Florida gross rents — starting points, not gospel.*\n")

    mrc = meta.get("market_rent_lease_comps", 0)
    have_mr = types[types["market_rent_psf"].notna()] if "market_rent_psf" in types.columns else pd.DataFrame()
    if len(have_mr):
        w(f"\n**Rents anchored to real lease comps.** From **{mrc}** lease listings we derive a median "
          "asking rent $/SqFt per asset type — so the assumption isn't a pure guess where we have data:\n")
        w("\n| Asset type | Assumed rent | Market rent (lease comps) | n |")
        w("|---|---|---|---|")
        for _, r in have_mr.iterrows():
            w(f"| {r['asset_type']} | ${r['assume_rent_psf']:.0f} | ${r['market_rent_psf']:.0f} | "
              f"{int(r['market_rent_n'])} |")
        w("\n*In the dashboard, 'Use market rents' swaps these in with one click.*\n")
    mfc = meta.get("mf_unit_coverage", {})
    if mfc.get("parsed"):
        w(f"\n**Multifamily $/unit.** Unit counts were parsed from addresses (e.g. \"Unit#1-28\") for "
          f"**{mfc['parsed']} of {mfc['total']}** multifamily comps, enabling a per-door metric where "
          "available (units aren't a field in the export).\n")

    w("## Submarkets, ranked (normalized $/SqFt)\n")
    w("| Submarket | Norm $/SqFt | vs city | Median price | Top type | Mo supply | Stance |")
    w("|---|---|---|---|---|---|---|")
    for _, r in subs.iterrows():
        ms = r.get("months_supply")
        w(f"| {r['submarket']} | ${r['norm_ppsf']:,.0f} | {r.get('vs_city_pct', float('nan')):+.0f}% | "
          f"{CRE.usd(r['median_price'])} | {r.get('top_asset','—')} | "
          f"{'—' if pd.isna(ms) else f'{ms:.0f}'} | {r.get('stance','—')} |")

    if reb:
        fc = reb["flag_counts"]
        df_all = CRE.load_clean()
        live_all = int(df_all["status"].isin(CRE.LIVE).sum())
        live_sale = int((df_all["status"].isin(CRE.LIVE) & df_all["deal_kind"].eq("Sale")).sum())
        w("\n## Repricing live inventory (at default assumptions)\n")
        w(f"*Scope: {reb['meta']['n_live']} of {live_sale} live for-sale listings have a usable "
          f"building size; the rest (and {live_all - live_sale} live lease listings) can't be priced "
          f"and are excluded.*\n")
        w(f"Of the **{reb['meta']['n_live']}** priced live listings: **{fc.get('Underpriced',0)} underpriced**, "
          f"{fc.get('Fair',0)} fair, **{fc.get('Overpriced',0)} overpriced** — on the income lens "
          f"(asking vs value at assumed rents/cap). Below value = a higher implied cap = a buy. "
          f"Note these flags **move as you change assumptions**.\n")
        if reb["opportunities"]:
            w("\n**Top underpriced (income basis, default assumptions):**\n")
            w("| Address | Submarket | Type | Asking | Value | Gap | Why |")
            w("|---|---|---|---|---|---|---|")
            for o in reb["opportunities"][:8]:
                w(f"| {str(o['address'])[:34]} | {o['submarket']} | {o['asset_type']} | "
                  f"{CRE.usd(o['price'])} | {CRE.usd(o['assumed_value'])} | "
                  f"{o['income_gap_pct']:.0f}% | {o['reason']} |")

    if seg:
        w("\n## Absorption\n")
        w(seg["meta"]["absorption_note"] + "\n")

    if pros:
        w("\n## Prospecting\n")
        w(f"- **{pros['meta']['n_failed']}** failed listings (expired / cancelled / withdrawn) — "
          "motivated owners, with the $/SqFt overpricing that likely stalled the deal.\n")
        w(f"- **{pros['meta']['n_overpriced_active']}** overpriced actives to reset or re-trade.\n")

    s = SC.seed()
    v = SC.compute(s["price"], s["sqft"], s["rent_psf"], s["vacancy"], s["opex_ratio"],
                   s["market_cap"], s["ltv"], s["rate"], s["amort"], s["shift_bps"],
                   s["exit_cap"], s["rent_growth"], s["expense_growth"], s["hold"],
                   s["sell_pct"], s["acq_pct"])
    w("\n## Underwriting a deal (live model)\n")
    w(f"The dashboard's **Underwrite a deal** card and the Excel **Scenario** tab build NOI from "
      f"the assumptions and run a full levered return. Seeded example — a {s['asset_type']} deal "
      f"at {CRE.usd(s['price'])} / {s['sqft']:,} SqFt (${s['price']/s['sqft']:.0f}/SqFt), assumed "
      f"rent ${s['rent_psf']}/SqFt, {s['ltv']*100:.0f}% LTV @ {s['rate']*100:.2f}%:\n")
    w(f"- Derived NOI **{CRE.usd(v['noi0'])}** → going-in cap **{v['goin_cap']*100:.2f}%**, "
      f"DSCR **{v['dscr']:.2f}×**, debt yield **{v['debt_yield']*100:.1f}%**.\n")
    w(f"- Year-1 cash-on-cash **{v['coc1']*100:.1f}%**, {s['hold']}-yr levered IRR "
      f"**{v['lirr']*100:.1f}%**, equity multiple **{v['em']:.2f}×** (exit at "
      f"{s['exit_cap']*100:.2f}% cap).\n")
    w("*Change the rent, cap, LTV, rate or hold and it all recomputes — this single seeded number "
      "is just a starting point.*\n")

    w("\n## Honest limitations\n")
    w("- **No income in the source** — NOI/cap/returns are only as good as your assumptions. "
      "The tool makes them explicit and adjustable rather than hiding a guess.\n")
    w("- **Thin closed-sale counts** in some submarkets/types; normalized $/SqFt pools across the "
      "market, and low-count cells should be read as indicative.\n")
    w("- **Mixed asset classes and lease vs. sale**; lease listings (different rate bases) are "
      "excluded from the $/SqFt sale analysis.\n")
    w("- **Area = MLS area code**, not a named neighborhood; and **units are unknown**, so "
      "multifamily is analyzed on $/SqFt, not $/unit.\n")
    w("- These are **screening signals, not appraisals** — verify rent rolls, T-12s and cap-ex "
      "before underwriting any specific deal.\n")

    with open(OUT, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"Report -> {os.path.relpath(OUT, CRE.ROOT)}")


if __name__ == "__main__":
    main()
