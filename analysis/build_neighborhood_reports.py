#!/usr/bin/env python3
"""
Per-neighborhood "system" reports — one print-ready page per neighborhood, plus a master
repricing summary page. Centerpiece: what inventory is ASKING vs what comps say it SHOULD
be, and the adjustment (up or down). Then the full system: normalized value, waterfront,
build-vs-buy, leasing/yield, market conditions, live opportunities, and talking points.

Writes outputs/neighborhood_reports.html (print-styled). Render to PDF with:
    node analysis/render_pdf.cjs
Output PDF: outputs/Neighborhood_System_Reports.pdf
"""
from __future__ import annotations
import html
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs")


def _load(name):
    try:
        with open(os.path.join(PROC, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def usd(v, d=0):
    return f"${v:,.{d}f}" if v is not None else "—"


def pct(v, dp=0):
    return f"{v:+.{dp}f}%" if v is not None else "—"


def esc(s):
    return html.escape(str(s)) if s is not None else ""


def slugify(name):
    keep = "".join(c if (c.isalnum() or c == " ") else " " for c in str(name))
    return "-".join(keep.split()).lower() or "neighborhood"


def dominant_market(nb, absorb):
    rows = [r for r in (absorb or {}).get("by_band_neighborhood", []) if r["neighborhood"] == nb]
    c = {}
    for r in rows:
        if r.get("market"):
            c[r["market"]] = c.get(r["market"], 0) + 1
    return max(c, key=c.get) if c else None


def main():
    master = _load("master_bundle.json")
    mls = _load("mls_bundle.json")
    if not master or not mls:
        raise SystemExit("Run the pipeline first.")
    prof = {p["neighborhood"]: p for p in mls.get("profiles", [])}
    mnb = {n["neighborhood"]: n for n in mls["neighborhoods"]}
    ctx = {c["neighborhood"]: c for c in (_load("context_bundle.json") or {}).get("neighborhoods", [])}
    lease = {l["neighborhood"]: l for l in (_load("lease_bundle.json") or {}).get("neighborhoods", [])}
    absorb = _load("absorption_bundle.json")
    under = {}
    for o in (_load("underpriced_bundle.json") or {}).get("listings", []):
        under.setdefault(o["neighborhood"], []).append(o)
    back = _load("backtest_bundle.json")
    acc = (back or {}).get("overall", {}).get("mdape")

    nbs = master["neighborhoods"]
    gen = master.get("meta", {})

    # ---------- master repricing summary rows ----------
    srows = []
    for r in nbs:
        a, s, adj = r.get("asking_ppsf"), r.get("should_be_ppsf"), r.get("suggested_adjust_pct")
        if a is None or s is None:
            continue
        ly = lease.get(r["neighborhood"], {}).get("gross_yield_pct")
        dir_cls = "up" if (adj or 0) > 1 else "down" if (adj or 0) < -1 else "flat"
        srows.append((r, a, s, adj, ly, dir_cls))

    def metric(label, val, sub=""):
        return (f'<div class="m"><div class="ml">{esc(label)}</div>'
                f'<div class="mv">{val}</div>'
                + (f'<div class="ms">{esc(sub)}</div>' if sub else "") + "</div>")

    pages = []
    nb_pages = []   # (slug, name, page_html) for the individual one-pagers

    # ===== cover / master summary =====
    head = (f'<div class="rpt cover"><div class="eyebrow">{esc(CFG.market["name"])} · '
            'Neighborhood system reports</div>'
            '<h1>Renormalized pricing by neighborhood</h1>'
            '<p class="lede">What inventory is <b>asking</b> vs what comparable sales say it '
            '<b>should be</b> — and the adjustment, up or down. Each of the following pages is one '
            'neighborhood as a complete system: value, waterfront, build-vs-buy, leasing yield, '
            'market conditions and live opportunities.</p>')
    if acc is not None:
        head += (f'<p class="note">Pricing model validated out-of-sample to ±{acc:.0f}% median error. '
                 'Figures are comp-based screening signals, not appraisals.</p>')
    # summary table
    trows = ""
    for (r, a, s, adj, ly, dir_cls) in srows:
        word = "Reduce" if dir_cls == "down" else "Raise" if dir_cls == "up" else "Hold"
        trows += (f'<tr><td class="l">{r.get("rank")}</td><td class="l nb">{esc(r["neighborhood"])}</td>'
                  f'<td>{usd(a)}</td><td>{usd(s)}</td>'
                  f'<td class="{dir_cls}">{pct(adj,1)}</td>'
                  f'<td class="{dir_cls} l">{word}</td>'
                  f'<td>{(str(ly)+"%") if ly is not None else "—"}</td></tr>')
    head += ('<table class="sum"><thead><tr><th class="l">#</th><th class="l">Neighborhood</th>'
             '<th>Now asking $/ft²</th><th>Should-be $/ft²</th><th>Adjust</th>'
             '<th class="l">Action</th><th>Yield</th></tr></thead>'
             f'<tbody>{trows}</tbody></table>'
             '<p class="foot">Should-be = recent sold comps, size/type/waterfront-normalized. '
             'Yield = est. gross rental yield. Reduce = asking above comps; Raise = below.</p></div>')
    pages.append(head)

    # ===== one page per neighborhood =====
    for r in nbs:
        nb = r["neighborhood"]
        m = mnb.get(nb, {})
        a, s, adj = r.get("asking_ppsf"), r.get("should_be_ppsf"), r.get("suggested_adjust_pct")
        sqft = m.get("median_sqft")
        dir_cls = "up" if (adj or 0) > 1 else "down" if (adj or 0) < -1 else "flat"
        word = ("Reduce asking" if dir_cls == "down" else "Raise asking" if dir_cls == "up"
                else "Hold — priced right")

        # hero pricing
        if a is not None and s is not None:
            dollar = (s - a) * sqft if sqft else None
            hero = (
                '<div class="hero">'
                f'<div class="hcell"><div class="hl">Now asking</div><div class="hv">{usd(a)}<span>/ft²</span></div></div>'
                f'<div class="hcell"><div class="hl">Should be (comps)</div><div class="hv">{usd(s)}<span>/ft²</span></div></div>'
                f'<div class="hcell {dir_cls}"><div class="hl">Adjustment</div><div class="hv">{pct(adj,1)}</div>'
                f'<div class="hs">{word}' + (f' · {usd(dollar)} on a ~{sqft:,.0f} ft² home' if dollar else "") + '</div></div>'
                '</div>')
        else:
            hero = ('<div class="hero"><div class="hcell flat" style="flex:1">'
                    '<div class="hl">Repricing signal</div><div class="hv" style="font-size:18px">'
                    'Insufficient live inventory or sold comps</div>'
                    '<div class="hs">Showing normalized value &amp; market context below.</div></div></div>')

        # value metrics
        vm = "".join([
            metric("Normalized $/ft²", usd(r.get("norm_ppsf")), pct(r.get("vs_city_pct")) + " vs city"),
            metric("Waterfront $/ft²", usd(r.get("waterfront_ppsf")),
                   ("vs " + usd(r.get("dry_ppsf")) + " dry") if r.get("dry_ppsf") else ""),
            metric("Median sold", usd(r.get("median_sale_price")),
                   (f'{r.get("median_discount_pct"):.0f}% under ask' if r.get("median_discount_pct") is not None else "")),
            metric("New vs existing", pct(r.get("new_premium_pct")), "new-construction premium"),
            metric("Appreciation", pct(r.get("appreciation_since_2020")), "since 2020"),
            metric("Days on market", f'{r.get("dom"):.0f}' if r.get("dom") is not None else "—", "Redfin layer"),
        ])

        # build-vs-buy
        cx = ctx.get(nb)
        bvb = ""
        if cx:
            bvb = ('<div class="sec"><div class="sh">Build vs buy (replacement cost)</div>'
                   '<div class="mrow">'
                   + metric("Resale $/ft²", usd(cx["resale_psf"]), cx["resale_basis"])
                   + metric("Replace $/ft²", usd(cx["replacement_psf_typ"]), "land + construction + soft")
                   + metric("vs Replacement", pct(cx["premium_to_replacement_pct"]), "")
                   + metric("Land $/ft²", usd(cx["land_ppsf"]), cx["land_basis"])
                   + '</div>'
                   f'<p class="verdict">{esc(cx["verdict"])}</p></div>')

        # leasing
        lz = lease.get(nb)
        lzhtml = ""
        if lz:
            lzhtml = ('<div class="sec"><div class="sh">Leasing &amp; yield</div><div class="mrow">'
                      + metric("Est. rent", usd(lz["est_monthly_rent"]) + "/mo", lz["rent_basis"])
                      + metric("Rent $/ft²/yr", usd(lz["rent_psf_yr"], 0), "")
                      + metric("Gross yield", (str(lz["gross_yield_pct"]) + "%") if lz["gross_yield_pct"] else "—", "")
                      + metric("GRM", str(lz["grm"]) if lz.get("grm") else "—", "price ÷ annual rent")
                      + '</div>'
                      f'<p class="verdict">{esc(lz.get("verdict"))}</p></div>')

        # market conditions strip
        mk = dominant_market(nb, absorb)
        cond = ('<div class="chips">'
                + (f'<span class="chip">{esc(mk)}</span>' if mk else "")
                + (f'<span class="chip">{r.get("n_high_ticket")} live ≥$1M</span>' if r.get("n_high_ticket") else "")
                + (f'<span class="chip">{r.get("n_over_10m")} over $10M</span>' if r.get("n_over_10m") else "")
                + (f'<span class="chip">Fail rate {r.get("failure_rate"):.0f}%</span>' if r.get("failure_rate") is not None else "")
                + (f'<span class="chip">{r.get("sold_n")} sold</span>' if r.get("sold_n") else "")
                + '</div>')

        # opportunities
        opps = under.get(nb, [])[:3]
        oh = ""
        if opps:
            items = "".join(
                f'<li><b>{esc(o["address"])}</b> — {usd(o["list_price"])}, asking '
                f'{usd(o["ask_ppsf"])}/ft² vs {usd(o["supported_ppsf"])}/ft² supported '
                f'({o["under_pct"]:.0f}% under)</li>' for o in opps)
            oh = f'<div class="sec"><div class="sh">Live opportunities</div><ul class="opps">{items}</ul></div>'

        # talking points
        tps = prof.get(nb, {}).get("talking_points", [])[:5]
        th = ""
        if tps:
            th = ('<div class="sec"><div class="sh">Talking points</div><ul class="tps">'
                  + "".join(f'<li>{esc(t)}</li>' for t in tps) + '</ul></div>')

        page = (f'<div class="rpt"><div class="rhead"><div><span class="rk">#{r.get("rank")}</span>'
                f'<span class="rname">{esc(nb)}</span></div>'
                f'<div class="geo">{esc(r.get("geo_type"))}</div></div>'
                + hero + f'<div class="mrow">{vm}</div>' + cond + bvb + lzhtml + oh + th
                + '<div class="pfoot">Comp-based screening signals — verify condition &amp; exact '
                'comps before pricing. Cost/rent figures are sourced market estimates.</div></div>')
        pages.append(page)
        nb_pages.append((slugify(nb), nb, page))

    css = """
<style>
@page { size: Letter; margin: 14mm; }
* { box-sizing: border-box; }
body { font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #12212e; margin: 0; font-size: 12px; }
.rpt { page-break-after: always; padding: 2mm 0; }
.rpt:last-child { page-break-after: auto; }
h1 { font-size: 30px; margin: 4px 0 6px; letter-spacing: -.01em; }
.eyebrow { text-transform: uppercase; letter-spacing: .12em; font-size: 10px; font-weight: 700;
  color: #1f6fb2; }
.lede { font-size: 13px; color: #33475a; max-width: 62em; line-height: 1.5; }
.note { font-size: 11px; color: #6a7886; font-style: italic; }
.cover .foot { font-size: 10px; color: #8a94a0; margin-top: 8px; }
table.sum { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 10.5px; }
table.sum th { background: #0d3b66; color: #fff; padding: 6px 7px; text-align: right; font-weight: 600; }
table.sum th.l, table.sum td.l { text-align: left; }
table.sum td { padding: 5px 7px; border-bottom: 1px solid #eee; text-align: right;
  font-variant-numeric: tabular-nums; }
table.sum td.nb { font-weight: 600; }
.up { color: #0f8a3c; } .down { color: #c0392b; } .flat { color: #6a7886; }
.rhead { display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 2px solid #0d3b66; padding-bottom: 6px; margin-bottom: 12px; }
.rk { color: #8a94a0; font-weight: 700; margin-right: 8px; }
.rname { font-size: 24px; font-weight: 700; }
.geo { color: #6a7886; font-size: 12px; }
.hero { display: flex; gap: 10px; margin-bottom: 14px; }
.hcell { flex: 1; border: 1px solid #e3e8ee; border-radius: 10px; padding: 12px 14px; background: #f7f9fb; }
.hcell.down { border-left: 4px solid #c0392b; } .hcell.up { border-left: 4px solid #0f8a3c; }
.hcell.flat { border-left: 4px solid #8a94a0; }
.hl { font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: #6a7886; font-weight: 600; }
.hv { font-size: 26px; font-weight: 700; margin-top: 2px; letter-spacing: -.01em; }
.hv span { font-size: 13px; color: #8a94a0; font-weight: 500; }
.hs { font-size: 11px; color: #33475a; margin-top: 3px; font-weight: 600; }
.mrow { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 6px; }
.m { flex: 1; min-width: 120px; border: 1px solid #eef1f4; border-radius: 8px; padding: 8px 10px; }
.ml { font-size: 9.5px; text-transform: uppercase; letter-spacing: .04em; color: #8a94a0; font-weight: 600; }
.mv { font-size: 17px; font-weight: 700; margin-top: 1px; }
.ms { font-size: 10px; color: #6a7886; }
.sec { margin-top: 12px; }
.sh { font-size: 11px; font-weight: 700; color: #1f6fb2; text-transform: uppercase;
  letter-spacing: .05em; border-bottom: 1px solid #e3e8ee; padding-bottom: 3px; margin-bottom: 7px; }
.verdict { font-size: 12px; font-weight: 600; margin: 6px 0 0; }
.chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 2px; }
.chip { background: #eef5fc; color: #0d3b66; border-radius: 999px; padding: 3px 10px;
  font-size: 10.5px; font-weight: 600; }
ul.opps, ul.tps { margin: 0; padding-left: 16px; }
ul.opps li, ul.tps li { font-size: 11.5px; color: #33475a; margin-bottom: 3px; line-height: 1.4; }
.pfoot { margin-top: 14px; border-top: 1px solid #eee; padding-top: 6px; font-size: 9px; color: #a7b0ba; }
</style>
"""
    def _doc(title, body):
        return ("<!doctype html><html><head><meta charset='utf-8'><title>" + esc(title)
                + "</title>" + css + "</head><body>" + body + "</body></html>")

    os.makedirs(OUT, exist_ok=True)
    # combined book (cover + every neighborhood)
    path = os.path.join(OUT, "neighborhood_reports.html")
    with open(path, "w") as f:
        f.write(_doc("Neighborhood System Reports", "".join(pages)))
    # individual one-pagers (one file per neighborhood)
    indiv_dir = os.path.join(OUT, "neighborhoods")
    os.makedirs(indiv_dir, exist_ok=True)
    for slug, name, page in nb_pages:
        with open(os.path.join(indiv_dir, slug + ".html"), "w") as f:
            f.write(_doc(f"{name} — {CFG.market['name']}", page))
    print(f"Wrote {os.path.relpath(path, ROOT)} (cover + {len(nb_pages)} pages) and "
          f"{len(nb_pages)} individual one-pagers in outputs/neighborhoods/. "
          "Render to PDF: node analysis/render_pdf.cjs")


if __name__ == "__main__":
    main()
