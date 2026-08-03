#!/usr/bin/env python3
"""
Per-neighborhood "systems" report — each submarket on its own page, as a self-contained system:
what it supports (normalized $/SqFt), what things are GOING FOR vs what they SHOULD go for
(adjusted basis, up or down), sale + lease + yield, absorption/failure, the playbook, and every
live/failed listing repriced.

OUTPUT: dashboard/neighborhood_report.html  (render to PDF for download)
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


def usd(x):
    return CRE.usd(x)


def main():
    cre = _load("cre_bundle.json")
    master = {s["submarket"]: s for s in (_load("master_bundle.json") or {"submarkets": []})["submarkets"]}
    leases = _load("leases_bundle.json") or {"by_submarket": []}
    lease_sub = {r["submarket"]: r for r in leases["by_submarket"]}
    seg = _load("segmentation_bundle.json") or {}
    v = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    subs = sorted(cre["submarkets"], key=lambda s: -(s.get("norm_ppsf") or 0))

    def mix_html(sub):
        """Small type/price/size composition blocks for one submarket."""
        def block(title, rows, key):
            rows = [r for r in rows if r.get("submarket") == sub]
            rows = sorted(rows, key=lambda r: -(r.get("share_pct") or 0))[:6]
            if not rows:
                return ""
            items = "".join(
                f"<div class='mixrow'><span>{esc(r[key])}</span>"
                f"<b>{(r.get('share_pct') or 0):.0f}%</b>"
                f"<i>{('$'+format(int(r['median_ppsf']),',')+'/SF') if r.get('median_ppsf') else ''}</i></div>"
                for r in rows)
            return f"<div class='mixcol'><h4>{title}</h4>{items}</div>"
        t = block("By type", seg.get("nbhd_by_type", []), "asset_type")
        p = block("By price", seg.get("nbhd_by_price", []), "price_band")
        z = block("By size (SqFt)", seg.get("nbhd_by_size", []), "size_band")
        return (f"<div class='mix'>{t}{p}{z}</div>" if (t or p or z) else "")

    def esc(x):
        return str(x).replace("&", "&amp;").replace("<", "&lt;")

    # ---- summary comparison table ----
    srow = ""
    for s in subs:
        m = master.get(s["submarket"], {})
        lz = lease_sub.get(s["submarket"], {})
        srow += (f"<tr><td>{esc(s['submarket'])}</td><td class='c'>{esc(s.get('corridors',''))}</td>"
                 f"<td>{usd(s['norm_ppsf'])}</td><td>{s.get('vs_city_pct',0):+.0f}%</td>"
                 f"<td>{'$'+format(int(lz['lease_psf']),',') if lz.get('lease_psf') else '—'}</td>"
                 f"<td>{(str(round(lz['gross_yield']*100,1))+'%') if lz.get('gross_yield') else '—'}</td>"
                 f"<td>{('%.0f'%m['months_supply']) if m.get('months_supply') is not None else '—'}</td>"
                 f"<td>{('%.0f%%'%m['failure_rate_pct']) if m.get('failure_rate_pct') is not None else '—'}</td>"
                 f"<td>{esc(m.get('stance','—'))}</td></tr>")

    pages = []
    for s in subs:
        sub = s["submarket"]
        m = master.get(sub, {})
        lz = lease_sub.get(sub, {})
        prof_key, _ = MKT.AREA_TO_PROFILE.get(sub, (None, None))
        prof = MKT.SUBMARKET_PROFILES.get(prof_key, {}) if prof_key else {}
        g = v[v["submarket"] == sub]
        live = g[g["status"].isin(CRE.LIVE)]
        failed = g[g["status"].isin(("Cancelled", "Expired", "Withdrawn", "TempOff"))]
        soldg = g[g["status"] == CRE.SOLD]

        def kpi(lab, val):
            return f"<div class='kpi'><div class='l'>{lab}</div><div class='n'>{val}</div></div>"
        kpis = "".join([
            kpi("Normalized $/SqFt", usd(s["norm_ppsf"])),
            kpi("Median sold $/SqFt", usd(s.get("sold_ppsf_median"))),
            kpi("vs city", f"{s.get('vs_city_pct',0):+.0f}%"),
            kpi("Lease $/SqFt", ("$"+format(int(lz['lease_psf']),',')) if lz.get("lease_psf") else "—"),
            kpi("Gross yield", (f"{lz['gross_yield']*100:.1f}%") if lz.get("gross_yield") else "—"),
            kpi("Months supply", (f"{m['months_supply']:.0f}") if m.get("months_supply") is not None else "—"),
            kpi("Failure rate", (f"{m['failure_rate_pct']:.0f}%") if m.get("failure_rate_pct") is not None else "—"),
            kpi("Sold · Active · Failed", f"{len(soldg)} · {len(live)} · {len(failed)}"),
        ])

        # repricing table: going-for vs should-be (adjusted basis up/down)
        def reprice_rows(df):
            out = ""
            for _, r in df.sort_values("ppsf_gap_pct").iterrows():
                going, model, sqft = r["ppsf"], r["pred_ppsf"], r["sqft"]
                if pd.isna(going) or pd.isna(model):
                    continue
                adj_pct = (model / going - 1) * 100
                adj_d = (model - going) * (sqft or 0)
                up = adj_pct > 0
                arrow = "▲ up" if up else "▼ down"
                cls = "up" if up else "down"
                out += (f"<tr><td>{esc(str(r['address'])[:32])}</td><td class='c'>{esc(r['asset_type'])}</td>"
                        f"<td class='c'>{esc(r['status'])}</td><td>{usd(r['price'])}</td>"
                        f"<td>${going:,.0f}</td><td>${model:,.0f}</td>"
                        f"<td class='{cls}'>{arrow} {abs(adj_pct):.0f}%</td>"
                        f"<td class='{cls}'>{'+' if adj_d>=0 else '−'}{usd(abs(adj_d))}</td></tr>")
            return out
        rep = reprice_rows(pd.concat([live, failed]))
        rep_tbl = (f"<table class='rep'><tr><th>Address</th><th>Type</th><th>Status</th><th>Asking</th>"
                   f"<th>Going $/SF</th><th>Model $/SF</th><th>Adjust</th><th>Basis Δ</th></tr>{rep}</table>"
                   if rep else "<p class='muted'>No live or failed listings with a modeled $/SqFt here.</p>")

        comps = ""
        for _, r in soldg.sort_values("price", ascending=False).head(6).iterrows():
            comps += (f"<tr><td>{esc(str(r['address'])[:32])}</td><td class='c'>{esc(r['asset_type'])}</td>"
                      f"<td>{int(r['sqft']):,}</td><td>{usd(r['price'])}</td><td>${r['ppsf']:,.0f}</td></tr>")
        comps_tbl = (f"<table><tr><th>Address</th><th>Type</th><th>SF</th><th>Price</th><th>$/SF</th></tr>{comps}</table>"
                     if comps else "<p class='muted'>No closed comps in file.</p>")

        pages.append(f"""<section class="page">
 <div class="ph"><div><div class="eyebrow">Neighborhood system</div>
   <h2>{esc(sub)}{' · '+esc(s['corridors']) if s.get('corridors') else ''}</h2>
   <div class="sub">{esc(prof_key or '')}{f" · <span class='conf'>{esc(s.get('confidence',''))} confidence</span>" if s.get('confidence') else ''}</div></div></div>
 <div class="kpis">{kpis}</div>
 {f'<div class="play"><b>{esc(prof.get("blurb",""))}</b><br><span class="muted"><b>Recent:</b> {esc(prof.get("deals",""))}</span><br><b>The play:</b> {esc(prof.get("angle",""))}</div>' if prof else ''}
 <h3>What this area is made of — market share</h3>
 {mix_html(sub)}
 <h3 style="margin-top:14px">Going for vs. should be going for — adjusted basis</h3>
 <p class="note">"Model $/SF" is the normalized value for that exact building (size / age / type removed). "Adjust" is how far its asking is from the model — <span class="up">▲ up</span> = priced below the market (room to raise / a buy), <span class="down">▼ down</span> = priced above.</p>
 {rep_tbl}
 <h3 style="margin-top:14px">Closed comps</h3>
 {comps_tbl}
</section>""")

    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Fort Lauderdale Commercial — Neighborhood Systems Report</title>
<style>
:root{{--ink:#1e2732;--muted:#6b7280;--line:#d8d5cc;--accent:#2f6f9f;--good:#3f7d5a;--bad:#b0473a;--bg:#f6f5f1}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:13.5px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif}}
.wrap{{max-width:920px;margin:0 auto;padding:24px}}
h1{{font-size:25px;margin:0 0 3px}}.lead{{color:var(--muted);margin:0 0 16px}}
.summary{{width:100%;border-collapse:collapse;font-size:12px;margin-bottom:8px}}
.summary th,.summary td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:right}}
.summary th:first-child,.summary td:first-child,.summary td.c{{text-align:left}}
.summary th{{color:var(--muted);text-transform:uppercase;font-size:10px;letter-spacing:.03em}}
.summary td.c{{color:var(--muted);font-size:11px}}
.page{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:20px 22px;margin:16px 0;break-inside:avoid}}
.eyebrow{{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--accent);font-weight:700}}
h2{{font-size:20px;margin:2px 0}}.sub{{color:var(--muted);font-size:12.5px}}
.conf{{color:var(--good);font-weight:600}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin:14px 0}}
.kpi{{border:1px solid var(--line);border-radius:8px;padding:8px 10px}}
.kpi .l{{font-size:9.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--muted)}}
.kpi .n{{font-size:16px;font-weight:650;font-variant-numeric:tabular-nums}}
.play{{background:var(--bg);border-radius:8px;padding:11px 13px;font-size:13px;margin-bottom:6px}}
h3{{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin:14px 0 5px}}
.note{{font-size:11.5px;color:var(--muted);margin:0 0 8px}}
table{{width:100%;border-collapse:collapse;font-size:11.5px}}
th,td{{text-align:right;padding:4px 7px;border-bottom:1px solid var(--line);white-space:nowrap}}
th:first-child,td:first-child,td.c{{text-align:left}}
th{{color:var(--muted);font-size:9.5px;text-transform:uppercase;font-weight:600}}
td.c{{color:var(--muted)}}.up{{color:var(--good);font-weight:600}}.down{{color:var(--bad);font-weight:600}}.muted{{color:var(--muted)}}
.mix{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:2px 0 4px}}
.mixcol h4{{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 5px;font-weight:700}}
.mixrow{{display:flex;justify-content:space-between;gap:6px;font-size:12px;padding:2px 0;border-bottom:1px solid var(--line)}}
.mixrow b{{font-variant-numeric:tabular-nums}}.mixrow i{{color:var(--muted);font-style:normal;font-size:11px}}
@media print{{body{{background:#fff}}.wrap{{max-width:100%;padding:0}}.page{{border:none;border-radius:0;page-break-after:always;padding:0 0 10px}}.summary{{page-break-after:always}}}}
</style></head><body><div class="wrap">
<h1>Fort Lauderdale Commercial — Neighborhood Systems</h1>
<p class="lead">Each submarket as its own system: what it supports, what's trading vs. what it should, and every live/failed listing repriced. Normalized $/SqFt removes size/age/type; income figures are assumption/comp-based — verify before quoting.</p>
<table class="summary"><tr><th>Submarket</th><th>Corridors</th><th>Norm $/SF</th><th>vs city</th><th>Lease $/SF</th><th>Gross yld</th><th>Mo supply</th><th>Fail %</th><th>Stance</th></tr>{srow}</table>
{''.join(pages)}
</div></body></html>"""
    with open(os.path.join(DASH, "neighborhood_report.html"), "w") as f:
        f.write(html)
    print(f"Neighborhood report -> dashboard/neighborhood_report.html ({len(subs)} submarket systems)")


if __name__ == "__main__":
    main()
