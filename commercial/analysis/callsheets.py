#!/usr/bin/env python3
"""
Cold-call toolkit — per-owner call sheets for prospecting owners to list/sell.

Targets the motivated owners (failed/expired/withdrawn listings) and overpriced actives, and
for each builds what you need on the phone: the property, what it's WORTH and what it RENTS
for, the implied cap, the nearest comps, a tailored opener, owner-FAQ answers, and the "why
now" angle from the submarket playbook.

OUTPUT: data/processed/call_list.csv, callsheets_bundle.json, dashboard/call_sheets.html
"""
from __future__ import annotations
import json
import os

import pandas as pd

import cre_common as CRE
import market_context as MKT

DASH = os.path.join(CRE.ROOT, "dashboard")


def _load(n):
    p = os.path.join(CRE.PROC, n)
    return json.load(open(p)) if os.path.exists(p) else None


SPOKEN = {"Commercial (other)": "commercial", "Mixed Use": "mixed-use", "Multifamily": "multifamily",
          "Office": "office", "Retail": "retail", "Industrial": "industrial", "Hotel": "hotel",
          "Restaurant": "restaurant/bar", "Flex": "flex", "Special Purpose": "special-purpose"}
FAILED = ("Cancelled", "Expired", "Withdrawn", "TempOff")


def main():
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    leases = _load("leases_bundle.json") or {"by_type": []}
    lease_by_type = {r["asset_type"]: r for r in leases["by_type"]}
    cre = _load("cre_bundle.json")
    sold = v[v["status"].eq(CRE.SOLD)]
    # corridor label for EVERY area in the data (not just the 9 ranked)
    area_corr = {sub: CRE.corridor_hint(g["address"]) for sub, g in v.groupby("submarket")}

    prospects = v[v["status"].isin(FAILED)
                  | (v["status"].isin(CRE.LIVE) & v["income_gap_pct"].gt(12))].copy()
    prospects["_mot"] = prospects["status"].isin(FAILED).map({True: 0, False: 1})
    prospects = prospects.sort_values(["_mot", "price"], ascending=[True, False])

    def nearest(sub, at, sqft, n=3):
        pool = sold[sold["submarket"] == sub]
        if len(pool) < n:
            pool = sold[sold["asset_type"] == at]
        pool = pool.assign(_d=(pool["sqft"] - (sqft or 0)).abs()).sort_values("_d").head(n)
        return [{"address": str(x["address"])[:34], "sqft": int(x["sqft"]),
                 "price": x["price"], "ppsf": x["ppsf"]} for _, x in pool.iterrows()]

    sheets = []
    for _, r in prospects.iterrows():
        at, sub = r["asset_type"], r["submarket"]
        sqft, ask, ppsf, comp = r["sqft"], r["price"], r["ppsf"], r["pred_ppsf"]
        cap, mcap, gap = r["implied_cap"], r["market_cap"], r["ppsf_gap_pct"]
        # credibility gate: need size + a comp; drop where BOTH the cap is implausible and the
        # $/SqFt gap is extreme (misclassified / trophy — a wrong number blows the call)
        if pd.isna(sqft) or sqft <= 0 or pd.isna(comp) or comp <= 0:
            continue
        cap_ok = pd.notna(cap) and 0.03 <= cap <= 0.15
        if not cap_ok and (pd.isna(gap) or abs(gap) > 60):
            continue
        comp_value = round(comp * sqft, -3)                     # comp-based value ($/SF × SF)
        lt = lease_by_type.get(at, {})
        lease_psf = lt.get("lease_psf")
        annual_rent = (lease_psf * sqft) if lease_psf else None
        prof_key, _ = MKT.AREA_TO_PROFILE.get(sub, (None, None))
        prof = MKT.SUBMARKET_PROFILES.get(prof_key, {}) if prof_key else {}
        failed = r["status"] in FAILED
        loc = area_corr.get(sub) or prof_key or "the area"
        sp = SPOKEN.get(at, at.lower())
        cap_phrase = f" — about a {cap*100:.1f}% cap at market rents" if cap_ok else ""

        # ---- opener ----
        if failed:
            opener = f"Hi, I saw {r['address']} came off the market — I cover {loc}. "
            opener += (f"{sp.capitalize()} around here is trading near ${comp:,.0f}/SF"
                       + (f" and leasing around ${lease_psf:,.0f}/SF" if lease_psf else "")
                       + ". I think it can be positioned to actually sell — got two minutes?")
        else:
            opener = (f"Hi — you're on the market at {r['address']} for {CRE.usd(ask)} "
                      f"(${ppsf:,.0f}/SF). Comparable {sp} on {loc} has been closer to "
                      f"${comp:,.0f}/SF; I have a read on where it clears and a few active buyers. "
                      "Worth a quick call?")

        # ---- value read (comp-led; cap only if plausible) ----
        vr = f"Comps put it around {CRE.usd(comp_value)} (~${comp:,.0f}/SF){cap_phrase}."
        if lease_psf and annual_rent:
            vr += f" It should rent ~${lease_psf:,.0f}/SF — about {CRE.usd(annual_rent)}/yr gross."

        # ---- owner FAQ ----
        ask_str = f"You're listed at {CRE.usd(ask)}." if not failed else f"You were asking {CRE.usd(ask)}."
        faq = [f"What's it worth? Comps support ~{CRE.usd(comp_value)} (~${comp:,.0f}/SF). {ask_str}"]
        if lease_psf and annual_rent:
            faq.append(f"What does it rent for? ~${lease_psf:,.0f}/SF/yr — about "
                       f"{CRE.usd(annual_rent)}/yr gross on {int(sqft):,} SF.")
        if cap_ok:
            faq.append(f"What cap? ~{cap*100:.1f}% implied from lease-vs-sale comps "
                       f"(market benchmark {MKT.ASSET_BENCHMARKS.get(at, {}).get('cap','—')}).")
        if prof.get("blurb"):
            faq.append(f"How's demand? {prof['blurb']}")
        faq.append("Why now? 1031 buyers are active, the Live Local Act unlocks density on "
                   "commercial land, and rising insurance is nudging owners to test the market.")

        sheets.append({
            "address": r["address"], "asset_type": at, "submarket": sub,
            "corridors": area_corr.get(sub, ""), "status": r["status"], "motivated": bool(failed),
            "sqft": int(sqft), "year_built": None if pd.isna(r["year_built"]) else int(r["year_built"]),
            "last_ask": ask, "ppsf": round(ppsf) if pd.notna(ppsf) else None,
            "comp_ppsf": round(comp), "value": comp_value,
            "implied_cap": round(cap, 4) if cap_ok else None,
            "market_cap": None if pd.isna(mcap) else round(mcap, 4),
            "lease_psf": lease_psf, "annual_rent_est": None if not annual_rent else round(annual_rent, -2),
            "opener": opener, "value_read": vr, "faq": faq,
            "angle": prof.get("angle"), "recent_deal": prof.get("deals"), "profile_key": prof_key,
            "comps": nearest(sub, at, sqft),
        })

    flat = pd.DataFrame([{
        "address": s["address"], "asset_type": s["asset_type"], "submarket": s["submarket"],
        "status": s["status"], "last_ask": s["last_ask"], "value": s["value"],
        "implied_cap": s["implied_cap"], "lease_psf": s["lease_psf"],
        "comp_ppsf": s["comp_ppsf"], "opener": s["opener"],
    } for s in sheets])
    flat.to_csv(os.path.join(CRE.PROC, "call_list.csv"), index=False)
    with open(os.path.join(CRE.PROC, "callsheets_bundle.json"), "w") as f:
        json.dump({"meta": {"n": len(sheets),
                            "n_motivated": int(sum(s["motivated"] for s in sheets))},
                   "sheets": sheets}, f, indent=2)

    _write_html(sheets)
    print(f"Call sheets: {len(sheets)} owners ({sum(s['motivated'] for s in sheets)} motivated / "
          f"failed) -> call_list.csv, callsheets_bundle.json, dashboard/call_sheets.html")


def _write_html(sheets):
    def esc(x):
        return str(x).replace("&", "&amp;").replace("<", "&lt;")

    cards = []
    shown = sheets[:80]
    for i, s in enumerate(shown, 1):
        comps = "".join(
            f"<tr><td>{esc(c['address'])}</td><td>{c['sqft']:,}</td><td>{CRE.usd(c['price'])}</td>"
            f"<td>${c['ppsf']:,.0f}</td></tr>" for c in s["comps"])
        faq = "".join(f"<li>{esc(q)}</li>" for q in s["faq"])
        badge = '<span class="mot">MOTIVATED · came off-market</span>' if s["motivated"] else \
                '<span class="over">Overpriced active</span>'
        cards.append(f"""<article class="sheet">
 <div class="hd"><div><div class="num">#{i}</div><h2>{esc(s['address'])}</h2>
   <div class="sub">{esc(s['asset_type'])} · {esc(s['corridors'] or s['submarket'])} · {esc(s['status'])} {badge}</div></div>
   <div class="facts">
     <div><b>{CRE.usd(s['last_ask'])}</b><span>last ask</span></div>
     <div><b>{('$'+format(s['comp_ppsf'],',')) if s['comp_ppsf'] else '—'}/SF</b><span>comp</span></div>
     <div><b>{CRE.usd(s['value']) if s['value'] else '—'}</b><span>value</span></div>
     <div><b>{(str(round(s['implied_cap']*100,1))+'%') if s['implied_cap'] else '—'}</b><span>impl. cap</span></div>
     <div><b>{('$'+format(int(s['lease_psf']),',')+'/SF') if s['lease_psf'] else '—'}</b><span>rent</span></div>
   </div></div>
 <p class="opener">“{esc(s['opener'])}”</p>
 {f'<p class="vr"><b>Value read:</b> {esc(s["value_read"])}</p>' if s['value_read'] else ''}
 {f'<p class="angle"><b>The angle:</b> {esc(s["angle"])}</p>' if s['angle'] else ''}
 {f'<p class="recent"><b>Recent in the area:</b> {esc(s["recent_deal"])}</p>' if s['recent_deal'] else ''}
 <div class="two"><div><h3>If they ask…</h3><ul>{faq}</ul></div>
   <div><h3>Nearest closed comps</h3><table><tr><th>Address</th><th>SF</th><th>Price</th><th>$/SF</th></tr>{comps}</table>
     <div class="notes"><h3>Notes</h3><div class="line"></div><div class="line"></div><div class="line"></div></div></div></div>
</article>""")

    n_mot = sum(s["motivated"] for s in sheets)
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Cold-Call Sheets — Fort Lauderdale Commercial</title>
<style>
:root{{--ink:#1e2732;--muted:#6b7280;--line:#d8d5cc;--accent:#2f6f9f;--good:#3f7d5a;--warn:#c2703d;--bg:#f6f5f1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:900px;margin:0 auto;padding:22px}}
h1{{font-size:24px;margin:0 0 3px}}.lead{{color:var(--muted);margin:0 0 18px}}
.sheet{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin:0 0 16px;break-inside:avoid}}
.hd{{display:flex;justify-content:space-between;gap:16px;border-bottom:2px solid var(--ink);padding-bottom:10px;margin-bottom:12px;flex-wrap:wrap}}
.num{{font-size:11px;color:var(--muted);font-weight:700}}h2{{font-size:19px;margin:2px 0}}
.sub{{color:var(--muted);font-size:12.5px}}
.mot{{background:rgba(63,125,90,.15);color:var(--good);font-weight:700;padding:1px 8px;border-radius:20px;font-size:11px;margin-left:6px}}
.over{{background:rgba(194,112,61,.15);color:var(--warn);font-weight:700;padding:1px 8px;border-radius:20px;font-size:11px;margin-left:6px}}
.facts{{display:flex;gap:14px;text-align:right}}.facts div{{display:flex;flex-direction:column}}
.facts b{{font-size:16px;font-variant-numeric:tabular-nums}}.facts span{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}}
.opener{{background:var(--bg);border-left:3px solid var(--accent);padding:10px 13px;border-radius:6px;font-size:15px;font-style:italic}}
.vr,.angle,.recent{{margin:8px 0;font-size:13.5px}}.recent{{color:var(--muted)}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:10px}}
h3{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:0 0 6px}}
ul{{margin:0;padding-left:18px}}li{{margin-bottom:5px;font-size:13px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}th,td{{text-align:right;padding:4px 6px;border-bottom:1px solid var(--line)}}th:first-child,td:first-child{{text-align:left}}
th{{color:var(--muted);font-weight:600;font-size:10px;text-transform:uppercase}}
.notes{{margin-top:10px}}.notes .line{{border-bottom:1px solid var(--line);height:20px}}
@media print{{body{{background:#fff}}.wrap{{max-width:100%;padding:0}}.sheet{{border:none;border-bottom:2px solid var(--ink);border-radius:0;page-break-inside:avoid}}}}
</style></head><body><div class="wrap">
<h1>Cold-Call Sheets — Fort Lauderdale Commercial</h1>
<p class="lead">Showing top {len(shown)} of {len(sheets)} owners · {n_mot} motivated (came off-market) sorted first · sale + lease + value read on each · full list in call_list.csv · print or save to PDF. Income figures are assumption/comp-based — verify before quoting.</p>
{''.join(cards)}
</div></body></html>"""
    with open(os.path.join(DASH, "call_sheets.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
