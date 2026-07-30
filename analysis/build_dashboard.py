#!/usr/bin/env python3
"""
Build the self-contained interactive dashboard.
Primary layer  : MLS per-home hedonic (mls_bundle.json) -- normalized $/sqft,
                 price drivers, discounts, failure rates, live deal flags.
Context layer  : Redfin (analysis_bundle.json) -- appreciation index over time.
Writes dashboard/index.html (standalone) and dashboard/artifact.html (publishable).
All data + CSS + JS inlined; no external requests.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
DASH = os.path.join(ROOT, "dashboard")
os.makedirs(DASH, exist_ok=True)

# Live-assumption seed for the in-browser control panel (screening knobs only —
# structural changes like price bands / hedonic premiums need config + refresh).
ASSUMP = {
    "verdictCut": CFG.thr("verdict_cutoff_pct"),
    "incomeCut": CFG.thr("income")["verdict_cutoff_pct"],
    "minComps": CFG.thr("min_comps"),
    "absorption": CFG.thr("absorption"),
}

with open(os.path.join(PROC, "mls_bundle.json")) as f:
    MLS = json.load(f)
with open(os.path.join(PROC, "analysis_bundle.json")) as f:
    REDFIN = json.load(f)
with open(os.path.join(PROC, "time_bundle.json")) as f:
    TIME = json.load(f)
with open(os.path.join(PROC, "street_bundle.json")) as f:
    STREET = json.load(f)
with open(os.path.join(PROC, "reprice_bundle.json")) as f:
    REPRICE = json.load(f)
with open(os.path.join(PROC, "master_bundle.json")) as f:
    _MASTER = json.load(f)
# compact scenario seed: neighborhood -> base ppsf / dom / appreciation / median price
SCEN = {r["neighborhood"]: {
    "ppsf": r.get("norm_ppsf"), "dom": r.get("dom"),
    "apprec": r.get("appreciation_since_2020"), "price": r.get("median_sale_price")}
    for r in _MASTER["neighborhoods"]}
with open(os.path.join(PROC, "absorption_bundle.json")) as f:
    ABSORB = json.load(f)
with open(os.path.join(PROC, "seller_bundle.json")) as f:
    _SL = json.load(f)
SELLER = {"meta": _SL["meta"], "failed": _SL["failed"][:150],
          "overpriced_active": _SL["overpriced_active"][:150]}
with open(os.path.join(PROC, "underpriced_bundle.json")) as f:
    _UP = json.load(f)
UNDER = {"meta": _UP["meta"], "by_band": _UP["by_band"],
         "listings": _UP["listings"][:200]}   # trim payload; full set in the CSV/Excel
with open(os.path.join(PROC, "land_bundle.json")) as f:
    _LAND = json.load(f)
# trim land payload: keep aggregates + a capped inventory/sales tail
LAND = {"meta": _LAND["meta"], "by_neighborhood": _LAND["by_neighborhood"],
        "geography": _LAND["geography"], "by_zoning": _LAND["by_zoning"],
        "acreage": _LAND["acreage"],
        "docks": {**{k: v for k, v in _LAND["docks"].items() if k != "sales"},
                  "sales": _LAND["docks"]["sales"][:15]},
        "commercial": ({**{k: v for k, v in _LAND["commercial"].items() if k not in ("sales", "actives")},
                        "sales": _LAND["commercial"]["sales"][:14]} if _LAND.get("commercial") else None),
        "implied_vs_actual": _LAND["implied_vs_actual"],
        "actives": _LAND["actives"][:80]}
with open(os.path.join(PROC, "income_bundle.json")) as f:
    _INC = json.load(f)
INCOME = {"meta": _INC["meta"], "by_neighborhood": _INC["by_neighborhood"],
          "by_tier": _INC["by_tier"], "actives": _INC["actives"][:80]}
with open(os.path.join(PROC, "marketing_bundle.json")) as f:
    _MK = json.load(f)
MARKETING = {"meta": _MK["meta"], "market_pulse": _MK["market_pulse"],
             "stat_cards": _MK["stat_cards"], "neighborhoods": _MK["neighborhoods"],
             "prospects": _MK["prospects"][:60]}
with open(os.path.join(PROC, "backtest_bundle.json")) as f:
    BACKTEST = json.load(f)
with open(os.path.join(PROC, "context_bundle.json")) as f:
    CONTEXT = json.load(f)
with open(os.path.join(PROC, "lease_bundle.json")) as f:
    LEASE = json.load(f)
with open(os.path.join(PROC, "high_ticket_bundle.json")) as f:
    _HT = json.load(f)
# trim listings out of the dashboard payload (they live in the Excel tab); keep the
# band roll-up and the band x neighborhood matrix -- the interactive insight.
HIGH = {"meta": _HT["meta"], "bands": _HT["bands"],
        "band_neighborhood": _HT["band_neighborhood"]}

INNER = r"""
<style>
:root{
  --sand:#f2efe7; --surface:#ffffff; --surface-2:#f8f6f0; --ink:#0f2233;
  --ink-2:#4a5c6b; --muted:#8a94a0; --line:#e6e1d6; --line-2:#efeadf;
  --accent:#1f6fb2; --accent-deep:#0d3b66; --accent-soft:#e7f0f8;
  --coral:#e0623a; --good:#0f8a3c; --warn:#c98a12; --neg:#d5473f; --pos:#2a78d6;
  --chip-hi-bg:#e4f3e9; --chip-hi-fg:#166b34; --chip-md-bg:#fbf1dd; --chip-md-fg:#8a5a10;
  --chip-lo-bg:#f0ede7; --chip-lo-fg:#6a6a6a;
  --over-bg:#fbe9e7; --over-fg:#b23b28; --under-bg:#e4f3e9; --under-fg:#166b34;
  --shadow:0 1px 2px rgba(15,34,51,.05),0 8px 24px rgba(15,34,51,.05);
}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])){
  --sand:#0a141d; --surface:#12212e; --surface-2:#0f1c27; --ink:#eef4f9;
  --ink-2:#a9b7c3; --muted:#6d7b88; --line:#213240; --line-2:#1a2732;
  --accent:#3f93d8; --accent-deep:#8dc0e8; --accent-soft:#15304a;
  --coral:#f07a4e; --good:#3fb964; --warn:#e0b662; --neg:#e56a62; --pos:#4a92e6;
  --chip-hi-bg:#123322; --chip-hi-fg:#5fce8a; --chip-md-bg:#33280f; --chip-md-fg:#e0b662;
  --chip-lo-bg:#1c2833; --chip-lo-fg:#9aa6b1;
  --over-bg:#3a1f1a; --over-fg:#f0906f; --under-bg:#123322; --under-fg:#5fce8a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}}
:root[data-theme="dark"]{
  --sand:#0a141d; --surface:#12212e; --surface-2:#0f1c27; --ink:#eef4f9;
  --ink-2:#a9b7c3; --muted:#6d7b88; --line:#213240; --line-2:#1a2732;
  --accent:#3f93d8; --accent-deep:#8dc0e8; --accent-soft:#15304a;
  --coral:#f07a4e; --good:#3fb964; --warn:#e0b662; --neg:#e56a62; --pos:#4a92e6;
  --chip-hi-bg:#123322; --chip-hi-fg:#5fce8a; --chip-md-bg:#33280f; --chip-md-fg:#e0b662;
  --chip-lo-bg:#1c2833; --chip-lo-fg:#9aa6b1;
  --over-bg:#3a1f1a; --over-fg:#f0906f; --under-bg:#123322; --under-fg:#5fce8a;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 10px 30px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
.fl-root{background:var(--sand);color:var(--ink);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;
  padding:clamp(16px,3vw,40px);min-height:100%}
.fl-wrap{max-width:1200px;margin:0 auto}
.fl-serif{font-family:ui-serif,Georgia,"Times New Roman",serif}
.tnum{font-variant-numeric:tabular-nums}
header.fl-head{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;
  justify-content:space-between;margin-bottom:6px}
.fl-eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:600;
  color:var(--accent);margin:0 0 6px}
h1.fl-title{font-size:clamp(26px,4vw,42px);line-height:1.06;margin:0;font-weight:600;
  letter-spacing:-.015em;text-wrap:balance}
.fl-sub{color:var(--ink-2);font-size:14px;margin:10px 0 0;max-width:70ch}
.fl-toggle{border:1px solid var(--line);background:var(--surface);color:var(--ink-2);
  border-radius:999px;padding:8px 14px;font-size:13px;cursor:pointer;font-weight:500}
.fl-toggle:hover{border-color:var(--accent)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:13px;
  margin:22px 0 20px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  padding:15px 16px;box-shadow:var(--shadow)}
.kpi .lab{font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);
  font-weight:600}
.kpi .val{font-size:27px;font-weight:600;margin-top:5px;letter-spacing:-.02em}
.kpi .note{font-size:11.5px;color:var(--ink-2);margin-top:2px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:16px;
  padding:18px 20px;box-shadow:var(--shadow);margin-bottom:20px}
.card h2{font-size:16px;margin:0 0 2px;font-weight:600}
.card .cap{font-size:12.5px;color:var(--ink-2);margin:0 0 12px}
.grid2{display:grid;grid-template-columns:1.15fr .85fr;gap:20px}
@media(max-width:860px){.grid2{grid-template-columns:1fr}}
.drivers{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px}
.drv{background:var(--surface-2);border:1px solid var(--line);border-radius:12px;padding:13px 15px}
.drv .d-lab{font-size:12px;color:var(--ink-2);font-weight:600}
.drv .d-val{font-size:23px;font-weight:700;margin-top:3px;letter-spacing:-.01em}
.up{color:var(--good)}.down{color:var(--neg)}
.geo{font-size:11px;color:var(--ink-2)}
.geostrip{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}
.geot{flex:1;min-width:150px;background:var(--surface-2);border:1px solid var(--line);
  border-radius:10px;padding:10px 12px}
.geot.wet{border-left:3px solid var(--accent)}
.opp{border:1px solid var(--line);border-left:3px solid var(--good);border-radius:12px;
  padding:13px 15px;margin-bottom:10px;background:var(--surface-2)}
.opp-head{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:baseline}
.opp-addr{font-weight:700;font-size:15px}
.opp-gap{font-weight:700;color:var(--good);font-size:15px;white-space:nowrap}
.opp-gap span{color:var(--muted);font-weight:600;font-size:12px}
.opp-sub{font-size:12px;color:var(--ink-2);margin:3px 0 8px}
.opp-conf{font-size:11px;padding:1px 8px;border-radius:999px;background:var(--surface);border:1px solid var(--line)}
.opp-reasons{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:4px}
.opp-reasons li{position:relative;padding-left:16px;font-size:13px;color:var(--ink-2);line-height:1.4}
.opp-reasons li:before{content:"";position:absolute;left:3px;top:7px;width:5px;height:5px;border-radius:50%;background:var(--good)}
.scn-grid{display:grid;grid-template-columns:340px 1fr;gap:22px}
@media(max-width:820px){.scn-grid{grid-template-columns:1fr}}
.scn-group{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;
  color:var(--accent);margin:14px 0 6px;border-bottom:1px solid var(--line);padding-bottom:4px}
.scn-inputs label{display:grid;grid-template-columns:1fr auto;align-items:center;gap:6px;
  font-size:12.5px;color:var(--ink-2);margin:7px 0}
.scn-inputs input[type=number],.scn-inputs select{border:1px solid var(--line);background:var(--surface);
  color:var(--ink);border-radius:8px;padding:6px 8px;font-size:13px;width:120px;text-align:right}
.scn-inputs select{width:100%;grid-column:1/3;text-align:left}
.scn-inputs input[type=range]{grid-column:1/3;width:100%;accent-color:var(--accent)}
.scn-inputs .rv{font-weight:700;color:var(--ink)}
.scn-tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:16px}
.scn-tile{background:var(--surface-2);border:1px solid var(--line);border-radius:12px;padding:13px 15px}
.scn-tile.hi{border-left:3px solid var(--accent)}
.scn-tile .t{font-size:11.5px;color:var(--ink-2);font-weight:600}
.scn-tile .v{font-size:22px;font-weight:700;margin-top:3px;letter-spacing:-.01em}
.scn-tile .s{font-size:11.5px;color:var(--muted);margin-top:2px}
.scn-tile .v.up{color:var(--good)}.scn-tile .v.down{color:var(--neg)}
.geot .g-t{font-size:11.5px;color:var(--ink-2);font-weight:600}
.geot .g-v{font-size:19px;font-weight:700;margin-top:2px}
.geot .g-n{font-size:11px;color:var(--muted)}
.controls{display:flex;flex-wrap:wrap;gap:12px;align-items:center;margin-bottom:16px}
.seg{display:inline-flex;background:var(--surface-2);border:1px solid var(--line);
  border-radius:10px;padding:3px}
.seg button{border:0;background:transparent;color:var(--ink-2);padding:7px 13px;
  border-radius:8px;font-size:13px;font-weight:600;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
input.search{flex:1;min-width:150px;border:1px solid var(--line);background:var(--surface);
  color:var(--ink);border-radius:10px;padding:9px 12px;font-size:13.5px}
input.search:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.tbl-scroll{overflow-x:auto}
table.fl{width:100%;border-collapse:collapse;font-size:13.5px;min-width:760px}
table.fl th{position:sticky;top:0;background:var(--surface);text-align:right;padding:10px 11px;
  font-size:11.5px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);
  border-bottom:2px solid var(--line);cursor:pointer;white-space:nowrap}
table.fl th.l,table.fl td.l{text-align:left}
table.fl th:hover{color:var(--accent)}
table.fl th .arw{opacity:.5;font-size:10px}
table.fl td{padding:9px 11px;text-align:right;border-bottom:1px solid var(--line-2)}
table.fl tbody tr:hover{background:var(--surface-2)}
.rank{color:var(--muted);font-variant-numeric:tabular-nums}
.nbh{font-weight:600;color:var(--ink)}
.pos{color:var(--pos);font-weight:600}.neg{color:var(--neg);font-weight:600}
.basis{font-size:11px;color:var(--ink-2);background:var(--surface-2);border:1px solid var(--line);
  padding:1px 7px;border-radius:999px}
.wf{font-size:11px;color:var(--accent-deep)}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:700}
.pill.High{background:var(--chip-hi-bg);color:var(--chip-hi-fg)}
.pill.Medium{background:var(--chip-md-bg);color:var(--chip-md-fg)}
.pill.Low{background:var(--chip-lo-bg);color:var(--chip-lo-fg)}
svg{display:block;width:100%;height:auto;overflow:visible}
.tt{position:fixed;pointer-events:none;background:var(--ink);color:var(--sand);padding:7px 10px;
  border-radius:8px;font-size:12px;line-height:1.35;opacity:0;transition:opacity .1s;z-index:20;
  box-shadow:0 6px 20px rgba(0,0,0,.25);max-width:250px}
.tt b{color:#fff}
.flagrow{display:flex;gap:10px;margin-bottom:12px}
.flagbox{flex:1;border-radius:12px;padding:12px;text-align:center;border:1px solid var(--line)}
.flagbox .n{font-size:24px;font-weight:700}
.flagbox .t{font-size:11.5px;font-weight:600;text-transform:uppercase;letter-spacing:.05em}
.fb-over{background:var(--over-bg)}.fb-over .n,.fb-over .t{color:var(--over-fg)}
.fb-fair{background:var(--surface-2)}.fb-fair .n{color:var(--ink)}.fb-fair .t{color:var(--muted)}
.fb-under{background:var(--under-bg)}.fb-under .n,.fb-under .t{color:var(--under-fg)}
.deals{font-size:13px}
.deal{display:flex;justify-content:space-between;gap:10px;padding:8px 2px;
  border-bottom:1px solid var(--line-2)}
.deal .dn{font-weight:600}
.deal .dg{color:var(--good);font-weight:700;font-variant-numeric:tabular-nums}
.deal .dm{color:var(--muted);font-size:11.5px}
.tps{margin:6px 0 0;padding:0;list-style:none;display:grid;
  grid-template-columns:1fr 1fr;gap:8px 22px}
@media(max-width:720px){.tps{grid-template-columns:1fr}}
.tps li{position:relative;padding-left:16px;font-size:13.5px;color:var(--ink-2);line-height:1.45}
.tps li:before{content:"";position:absolute;left:2px;top:8px;width:6px;height:6px;
  border-radius:50%;background:var(--accent)}
table.fl tbody tr{cursor:pointer}
table.fl tbody tr.sel{background:var(--accent-soft)}
footer.fl-foot{color:var(--muted);font-size:12px;margin-top:8px;text-align:center;
  border-top:1px solid var(--line);padding-top:16px}
footer.fl-foot a{color:var(--accent)}
.note-line{font-size:11.5px;color:var(--muted);margin-top:10px}
.howto{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:10px}
.howto a{display:block;background:var(--surface-2);border:1px solid var(--line);border-radius:11px;
  padding:11px 13px;text-decoration:none;color:var(--ink)}
.howto a:hover{border-color:var(--accent)}
.howto .j{font-weight:700;font-size:13.5px}
.howto .w{font-size:11.5px;color:var(--ink-2);margin-top:2px}
.mk-block{background:var(--surface-2);border:1px solid var(--line);border-radius:12px;
  padding:12px 15px;margin-bottom:10px}
.mk-block .mk-h{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
  color:var(--accent);margin-bottom:6px;display:flex;justify-content:space-between;gap:10px;align-items:center}
.mk-block p{margin:0;font-size:13.5px;color:var(--ink);line-height:1.5}
.mk-block .tps{margin-top:0}
.copybtn{border:1px solid var(--line);background:var(--surface);color:var(--ink-2);border-radius:8px;
  padding:3px 11px;font-size:11.5px;cursor:pointer;font-weight:600;white-space:nowrap;flex:0 0 auto}
.copybtn:hover{border-color:var(--accent);color:var(--accent)}
.copybtn.ok{color:var(--good);border-color:var(--good)}
html{scroll-behavior:smooth}
.fl-nav{position:sticky;top:0;z-index:15;display:flex;gap:6px;overflow-x:auto;
  padding:9px 0;margin:2px 0 4px;background:var(--sand);border-bottom:1px solid var(--line);
  scrollbar-width:thin;-webkit-overflow-scrolling:touch}
.fl-nav a{white-space:nowrap;font-size:12.5px;font-weight:600;color:var(--ink-2);
  text-decoration:none;padding:6px 12px;border-radius:999px;border:1px solid var(--line);
  background:var(--surface);flex:0 0 auto}
.fl-nav a:hover{border-color:var(--accent);color:var(--accent)}
.fl-nav a.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.card,.kpis,.grid2{scroll-margin-top:62px}
</style>

<div class="fl-root"><div class="fl-wrap">
  <header class="fl-head">
    <div>
      <p class="fl-eyebrow">Neighborhood market intelligence</p>
      <h1 class="fl-title fl-serif">Fort&nbsp;Lauderdale, normalized</h1>
      <p class="fl-sub" id="subline"></p>
    </div>
    <button class="fl-toggle" id="themeBtn" type="button">Toggle theme</button>
  </header>

  <nav class="fl-nav" id="secNav" aria-label="Jump to section">
    <a href="#howto">Start here</a>
    <a href="#marketing">Marketing</a>
    <a href="#costs">Costs &amp; realities</a>
    <a href="#leasing">Leasing &amp; yield</a>
    <a href="#assumptions">Assumptions</a>
    <a href="#scenario">Deal scenario</a>
    <a href="#highticket">High-ticket bands</a>
    <a href="#absorption">Absorption</a>
    <a href="#land">Land &amp; docks</a>
    <a href="#multifamily">Multifamily</a>
    <a href="#underpriced">Underpriced</a>
    <a href="#sellers">Seller prospects</a>
    <a href="#trends">Since 2020</a>
    <a href="#ranking">Ranking</a>
    <a href="#repricing">Repricing</a>
    <a href="#streets">Street-by-street</a>
    <a href="#drivers-sec">Price drivers</a>
  </nav>

  <section class="kpis" id="kpis"></section>

  <div class="card" id="howto">
    <h2>Start here <span style="font-weight:400;color:var(--muted);font-size:13px">— what to open for each job</span></h2>
    <div class="howto" style="margin-top:8px">
      <a href="#marketing"><div class="j">Talk to a homeowner</div><div class="w">Market snapshot + talking points to paste</div></a>
      <a href="#repricing"><div class="j">Price a listing (CMA)</div><div class="w">Asking vs comps, suggested list + CMA line</div></a>
      <a href="#sellers"><div class="j">Prospect for listings</div><div class="w">Owners to call + ready outreach lines</div></a>
      <a href="#underpriced"><div class="j">Find a buyer a deal</div><div class="w">Underpriced, ranked by $ opportunity</div></a>
      <a href="#absorption"><div class="j">Hot or cold market?</div><div class="w">Months of supply by band &amp; area</div></a>
      <a href="#highticket"><div class="j">Underwrite luxury (≥$1M)</div><div class="w">Band trends within each neighborhood</div></a>
      <a href="#scenario"><div class="j">Run the numbers</div><div class="w">Financing + rate/appreciation what-ifs</div></a>
      <a href="#costs"><div class="j">Costs &amp; build-vs-buy</div><div class="w">Construction, land, waterfront &amp; replacement cost</div></a>
      <a href="#leasing"><div class="j">Rent or sell?</div><div class="w">Rent, gross yield &amp; sell-vs-hold per area</div></a>
      <a href="#land"><div class="j">Land, docks &amp; multifamily</div><div class="w">The other asset classes</div></a>
    </div>
  </div>

  <div class="card" id="marketing">
    <h2>Marketing kit <span style="font-weight:400;color:var(--muted);font-size:13px">— copy-ready content: paste into emails, CMAs, postcards, posts</span></h2>
    <p class="cap" id="mkNote"></p>
    <div class="mk-block"><div class="mk-h">Citywide market pulse — for a monthly update <button class="copybtn" data-copy="pulse">Copy</button></div><p id="mkPulse"></p></div>
    <div class="geostrip" id="mkCards"></div>
    <div class="controls" style="margin:14px 0 10px"><select id="mkNb" class="search" style="flex:0 0 auto;min-width:220px" aria-label="Pick a neighborhood"></select></div>
    <div id="mkContent"></div>
  </div>

  <div class="card" id="costs">
    <h2>Costs &amp; market realities <span style="font-weight:400;color:var(--muted);font-size:13px">— what it costs to build, renovate, and hold; build-vs-buy per neighborhood</span></h2>
    <p class="cap" id="cxNote"></p>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:2px 0 6px">Cost benchmarks <span style="font-weight:400;color:var(--muted)">— sourced South Florida / Broward estimates, editable in config</span></div>
    <div class="geostrip" id="cxBench"></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:16px 0 6px">Market realities to know &amp; talk to</div>
    <ul class="opp-reasons" id="cxFacts" style="gap:7px"></ul>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:16px 0 6px">Build-vs-buy by neighborhood <span style="font-weight:400;color:var(--muted)">— finished-product resale vs all-in replacement cost (land + construction + soft)</span></div>
    <div class="controls" style="margin:0 0 10px"><input class="search" id="cxSearch" type="search" placeholder="Search neighborhood…" aria-label="Search build-vs-buy"></div>
    <div class="tbl-scroll"><table class="fl" id="cxTbl"><thead></thead><tbody></tbody></table></div>
    <p class="note-line" id="cxSrc"></p>
  </div>

  <div class="card" id="leasing">
    <h2>Leasing &amp; yield <span style="font-weight:400;color:var(--muted);font-size:13px">— rent, gross yield &amp; the sell-vs-hold read per neighborhood</span></h2>
    <p class="cap" id="lxNote"></p>
    <ul class="opp-reasons" id="lxFacts" style="gap:7px;margin-bottom:12px"></ul>
    <div class="controls" style="margin:0 0 10px"><input class="search" id="lxSearch" type="search" placeholder="Search neighborhood…" aria-label="Search leasing"></div>
    <div class="tbl-scroll"><table class="fl" id="lxTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="card" id="assumptions">
    <h2>Live assumptions <span style="font-weight:400;color:var(--muted);font-size:13px">— tune the screening knobs; every verdict, flag &amp; market label recomputes in place</span></h2>
    <p class="cap">These recompute the dashboard live in your browser — no rebuild. Structural changes (price bands, hedonic premiums, adding a data set) live in <code>config/deal_dashboard.yml</code>; run <code>python analysis/refresh.py</code> for those. Settings are remembered on this device.</p>
    <div class="scn-inputs" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:4px 24px">
      <label>Verdict cutoff (± % vs comps) <span class="rv" id="asCutV"></span><input id="asCut" type="range" min="2" max="25" step="1"></label>
      <label>Min sold comps to show <span class="rv" id="asMinV"></span><input id="asMin" type="range" min="1" max="20" step="1"></label>
      <label>Absorption — seller's &lt; (months)<input id="asAbsS" type="number" step="1"></label>
      <label>Balanced &lt; (months)<input id="asAbsB" type="number" step="1"></label>
      <label>Buyer's &lt; (months)<input id="asAbsY" type="number" step="1"></label>
    </div>
    <div class="controls" style="margin-top:10px"><button class="fl-toggle" id="asReset" type="button">Reset to config defaults</button><span class="note-line" id="asEcho" style="margin:0"></span></div>
  </div>

  <div class="card" id="scenario">
    <h2>Deal scenario &amp; financing <span style="font-weight:400;color:var(--muted);font-size:13px">— control the assumptions, watch price / DOM / $/sqft move</span></h2>
    <p class="cap">A live sensitivity model. Pick a neighborhood to seed today's numbers, then adjust financing and capital-markets assumptions. The elasticities are yours to set — nothing is hard-coded, so this recreates for any market or asset class.</p>
    <div class="scn-grid">
      <div class="scn-inputs">
        <div class="scn-group">Deal</div>
        <label>Neighborhood<select id="scNb"></select></label>
        <label>Purchase price ($)<input id="scPrice" type="number" step="50000"></label>
        <label>Size (sqft)<input id="scSqft" type="number" step="100"></label>
        <div class="scn-group">Financing</div>
        <label>Down payment <span class="rv" id="scDownV"></span><input id="scDown" type="range" min="0" max="100" step="5" value="35"></label>
        <label>Mortgage rate <span class="rv" id="scRateV"></span><input id="scRate" type="range" min="3" max="10" step="0.125" value="7"></label>
        <label>Amortization (yrs)<input id="scAmort" type="number" value="30" step="5"></label>
        <div class="scn-group">Capital markets &amp; assumptions</div>
        <label>Rate shift (bps) <span class="rv" id="scShiftV"></span><input id="scShift" type="range" min="-200" max="200" step="25" value="0"></label>
        <label>Price sensitivity (%/+100bps)<input id="scPElast" type="number" value="-3" step="0.5"></label>
        <label>Cash-buyer share <span class="rv" id="scCashV"></span><input id="scCash" type="range" min="0" max="100" step="5" value="45"></label>
        <label>DOM sensitivity (%/+100bps)<input id="scDElast" type="number" value="15" step="1"></label>
        <label>Appreciation (%/yr)<input id="scApprec" type="number" value="4" step="0.5"></label>
        <label>Hold (yrs)<input id="scHold" type="number" value="5" step="1"></label>
        <label>Selling costs (%)<input id="scSell" type="number" value="6" step="0.5"></label>
      </div>
      <div class="scn-out">
        <div class="scn-tiles" id="scTiles"></div>
        <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:4px 0 6px">Sensitivity to rate shift</div>
        <div class="tbl-scroll"><table class="fl" id="scSens"><thead></thead><tbody></tbody></table></div>
        <p class="note-line" id="scNote"></p>
      </div>
    </div>
  </div>

  <div class="card" id="drivers-sec">
    <h2>What drives value — the per-home model</h2>
    <p class="cap">Marginal effect on price per square foot, holding size, type and neighborhood constant. Estimated from actual closed sales.</p>
    <div class="drivers" id="drivers"></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:16px 0 2px">Price by lot geography <span style="font-weight:400;color:var(--muted)">— median $/ft² (derived, indicative)</span></div>
    <div class="geostrip" id="geostrip"></div>
  </div>

  <div class="card" id="highticket">
    <h2>High-ticket (≥$1M) — band trends by neighborhood <span style="font-weight:400;color:var(--muted);font-size:13px" id="htSummary"></span></h2>
    <p class="cap">The same price band behaves differently by neighborhood — what actually <em>sold</em> vs what's currently <em>asked</em>, per band, per area. Search a neighborhood to see its band-by-band pattern.</p>
    <div class="geostrip" id="htBands"></div>
    <div class="controls" style="margin:14px 0 10px"><input class="search" id="htSearch" type="search" placeholder="Search neighborhood (e.g. Coral Ridge, Las Olas)…" aria-label="Search high-ticket neighborhood"></div>
    <div class="tbl-scroll"><table class="fl" id="htTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="card" id="absorption">
    <h2>Absorption — months of supply by band &amp; neighborhood</h2>
    <p class="cap">How hard it is to sell at each level. &lt;6 mo = seller's market · 6–12 balanced · 12–24 buyer's · &gt;24 deep buyer's. Search a neighborhood for its band-level absorption.</p>
    <div class="geostrip" id="absBands"></div>
    <div class="controls" style="margin:14px 0 10px"><input class="search" id="absSearch" type="search" placeholder="Search neighborhood (e.g. Rio Vista, Coral Ridge)…" aria-label="Search absorption"></div>
    <div class="tbl-scroll"><table class="fl" id="absTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="card" id="land">
    <h2>Land &amp; docks — comp-backed lot value <span style="font-weight:400;color:var(--muted);font-size:13px" id="landSummary"></span></h2>
    <p class="cap">Vacant-land sales turn the previously <em>implied</em> land value into real comps: land $/sqft by neighborhood, the lot factors that drive it (waterfront, corner, size, zoning), the dock market, and commercial/development parcels. The RLD export spans South Florida — Fort Lauderdale rows are flagged.</p>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:2px 0 6px">Lot geography <span style="font-weight:400;color:var(--muted)">— median land $/ft²</span></div>
    <div class="geostrip" id="landGeo"></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:14px 0 6px">Zoning / density &amp; the size gradient</div>
    <div class="geostrip" id="landZone"></div>
    <div class="controls" style="margin:14px 0 10px"><input class="search" id="landSearch" type="search" placeholder="Search neighborhood…" aria-label="Search land"></div>
    <div class="tbl-scroll"><table class="fl" id="landTbl"><thead></thead><tbody></tbody></table></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:18px 0 6px">Docks &amp; commercial / development land</div>
    <div class="geostrip" id="landDock"></div>
  </div>

  <div class="card" id="multifamily">
    <h2>Multifamily / income — $/unit &amp; $/sqft <span style="font-weight:400;color:var(--muted);font-size:13px" id="mfSummary"></span></h2>
    <p class="cap">Small multifamily (duplex / triplex / quad) trades on price-per-unit and $/sqft. Medians by neighborhood and building size, with active listings scored against recent closed comps. Price-comp layer — cap rate &amp; GRM need a rent roll.</p>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:2px 0 6px">By building size <span style="font-weight:400;color:var(--muted)">— median $/unit</span></div>
    <div class="geostrip" id="mfTiers"></div>
    <div class="controls" style="margin:14px 0 10px"><input class="search" id="mfSearch" type="search" placeholder="Search neighborhood…" aria-label="Search multifamily"></div>
    <div class="tbl-scroll"><table class="fl" id="mfTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="card" id="underpriced">
    <h2>Underpriced opportunities — where the market is mispriced, and why <span style="font-weight:400;color:var(--muted);font-size:13px" id="upSummary"></span></h2>
    <p class="cap">Live listings asking below comp-supported value, ranked by dollar opportunity. Each reason is generated from the data — verify condition on site.</p>
    <div class="controls" style="margin-bottom:12px">
      <select id="upBand" class="search" style="flex:0 0 auto;min-width:150px" aria-label="Price band">
        <option value="">All bands</option>
        <option value="ht">≥ $1M only</option>
        <option value="$1M–$2M">$1M–$2M</option><option value="$2M–$3M">$2M–$3M</option>
        <option value="$3M–$5M">$3M–$5M</option><option value="$5M–$10M">$5M–$10M</option>
        <option value="$10M+">$10M+</option>
      </select>
      <input class="search" id="upSearch" type="search" placeholder="Search neighborhood or address…" aria-label="Search opportunities">
    </div>
    <div id="upList"></div>
  </div>

  <div class="card" id="sellers">
    <h2>Seller prospects — owners to call for a listing <span style="font-weight:400;color:var(--muted);font-size:13px" id="slSummary"></span></h2>
    <p class="cap">≥$1M owners who tried and couldn't (expired/withdrawn/cancelled), plus overpriced actives. What they asked, what comps support, and the number that moves it.</p>
    <div class="controls" style="margin-bottom:10px">
      <div class="seg" id="slSeg" role="group" aria-label="Prospect type">
        <button data-t="failed" aria-pressed="true">Failed listings</button>
        <button data-t="overpriced_active" aria-pressed="false">Overpriced actives</button>
      </div>
      <input class="search" id="slSearch" type="search" placeholder="Search neighborhood or address…" aria-label="Search prospects">
    </div>
    <div class="tbl-scroll"><table class="fl" id="slTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="grid2">
    <div class="card">
      <h2>Market appreciation</h2>
      <p class="cap">Quality-adjusted $/sqft index, 100 = 2012. Redfin layer (the MLS export has no dates).</p>
      <div id="lineChart"></div>
    </div>
    <div class="card">
      <h2>Live inventory <span style="font-weight:400;color:var(--muted);font-size:13px">vs. the model</span></h2>
      <p class="cap">Every active &amp; pending listing scored against its predicted market value.</p>
      <div class="flagrow" id="flagRow"></div>
      <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:6px 0 4px">Underpriced single-family candidates</div>
      <div class="deals" id="deals"></div>
    </div>
  </div>

  <div class="card" id="trends">
    <div style="display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:10px">
      <h2>The market since 2020 <span style="font-weight:400;color:var(--muted);font-size:13px" id="timeSummary"></span></h2>
    </div>
    <div class="controls" style="margin:10px 0 6px">
      <div class="seg" id="metricSeg" role="group" aria-label="Metric">
        <button data-m="ppsf" aria-pressed="true">Price/ft²</button>
        <button data-m="dom" aria-pressed="false">Days on market</button>
        <button data-m="disc" aria-pressed="false">Discount to list</button>
      </div>
      <select id="nbSelect" class="search" style="flex:0 0 auto;min-width:220px" aria-label="Overlay a neighborhood">
        <option value="">Compare a neighborhood…</option>
      </select>
    </div>
    <div id="timeChart"></div>
    <div class="legend" id="timeLegend"></div>
    <div class="grid2" style="margin-top:16px">
      <div><div style="font-size:12px;font-weight:600;color:var(--ink-2);margin-bottom:6px">Biggest gainers since 2020</div><div id="gainers" class="deals"></div></div>
      <div><div style="font-size:12px;font-weight:600;color:var(--ink-2);margin-bottom:6px">Cooled most from their peak</div><div id="coolers" class="deals"></div></div>
    </div>
  </div>

  <div class="card" id="ranking">
    <div class="controls">
      <div class="seg" id="basisSeg" role="group" aria-label="Property basis">
        <button data-b="all" aria-pressed="true">All</button>
        <button data-b="Single Family" aria-pressed="false">Single-family</button>
        <button data-b="Condo" aria-pressed="false">Condo</button>
      </div>
      <input class="search" id="search" type="search" placeholder="Search neighborhood…" aria-label="Search neighborhood">
    </div>
    <h2 id="barTitle">Top neighborhoods by normalized $/sqft</h2>
    <p class="cap" id="barCap"></p>
    <div id="barChart"></div>
  </div>

  <div class="card" id="profileCard">
    <div style="display:flex;justify-content:space-between;align-items:baseline;gap:10px;flex-wrap:wrap">
      <h2 id="profName">Neighborhood profile</h2>
      <span class="cap" style="margin:0" id="profHead"></span>
    </div>
    <p class="cap">Copy-ready talking points for a homeowner conversation. Click any row in the table below to switch.</p>
    <ul class="tps" id="profTps"></ul>
  </div>

  <div class="card">
    <h2 id="tblTitle">Neighborhood detail</h2>
    <p class="cap">Normalized $/sqft = model price for a standardized dry-lot home (waterfront &amp; pool priced separately). Click headers to sort.</p>
    <div class="tbl-scroll"><table class="fl" id="tbl"><thead></thead><tbody></tbody></table></div>
    <p class="note-line" id="noteLine"></p>
  </div>

  <div class="card" id="repricing">
    <h2>Repricing — is each neighborhood priced right? <span style="font-weight:400;color:var(--muted);font-size:13px" id="repriceSummary"></span></h2>
    <p class="cap">Current asking vs. what it <em>should</em> be (median recent sold comps per neighborhood). Verdict from asking vs sold.</p>
    <div class="controls" style="margin-bottom:10px">
      <div class="seg" id="repSeg" role="group" aria-label="Repricing type">
        <button data-t="condo" aria-pressed="true">Condos</button>
        <button data-t="all" aria-pressed="false">All types</button>
      </div>
    </div>
    <div class="flagrow" id="repFlags"></div>
    <div class="tbl-scroll"><table class="fl" id="repNbhdTbl"><thead></thead><tbody></tbody></table></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:18px 0 4px">Repriced inventory — every live listing vs its should-be price <span style="font-weight:400;color:var(--muted)" id="repInvNote"></span></div>
    <div class="controls" style="margin-bottom:10px"><input class="search" id="repSearch" type="search" placeholder="Search address or neighborhood…" aria-label="Search inventory"></div>
    <div class="tbl-scroll"><table class="fl" id="repInvTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <div class="card" id="streets">
    <h2>Street-by-street underwriting <span style="font-weight:400;color:var(--muted);font-size:13px" id="streetSummary"></span></h2>
    <p class="cap">Value per street (≥4 closed comps) and its premium/discount vs the surrounding neighborhood. Search a street or neighborhood.</p>
    <div class="controls" style="margin-bottom:12px">
      <input class="search" id="streetSearch" type="search" placeholder="Search street or neighborhood…" aria-label="Search street">
    </div>
    <div class="tbl-scroll"><table class="fl" id="streetTbl"><thead></thead><tbody></tbody></table></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:18px 0 4px">Live single-family listings priced below their street value <span style="font-weight:400;color:var(--muted)">(underwritten vs ≥4 street comps — verify condition)</span></div>
    <div class="tbl-scroll"><table class="fl" id="uwTbl"><thead></thead><tbody></tbody></table></div>
  </div>

  <footer class="fl-foot">
    Normalized with a per-home hedonic model on <span id="fn"></span> closed MLS sales
    (cross-validated against <a href="https://www.redfin.com/news/data-center/" target="_blank" rel="noopener">Redfin</a> at r=0.93).
    Neighborhood benchmarks and screening signals — not per-home appraisals. Condo-level flags are coarse (floor/view/renovation unobserved).
  </footer>
</div></div>
<div class="tt" id="tt"></div>

<script id="mls-data" type="application/json">__MLS_JSON__</script>
<script id="redfin-data" type="application/json">__REDFIN_JSON__</script>
<script id="time-data" type="application/json">__TIME_JSON__</script>
<script id="street-data" type="application/json">__STREET_JSON__</script>
<script id="reprice-data" type="application/json">__REPRICE_JSON__</script>
<script id="high-data" type="application/json">__HIGH_JSON__</script>
<script id="under-data" type="application/json">__UNDER_JSON__</script>
<script id="absorb-data" type="application/json">__ABSORB_JSON__</script>
<script id="seller-data" type="application/json">__SELLER_JSON__</script>
<script id="land-data" type="application/json">__LAND_JSON__</script>
<script id="income-data" type="application/json">__INCOME_JSON__</script>
<script id="assump-data" type="application/json">__ASSUMP_JSON__</script>
<script id="marketing-data" type="application/json">__MARKETING_JSON__</script>
<script id="backtest-data" type="application/json">__BACKTEST_JSON__</script>
<script id="context-data" type="application/json">__CONTEXT_JSON__</script>
<script id="lease-data" type="application/json">__LEASE_JSON__</script>
<script id="scen-data" type="application/json">__SCEN_JSON__</script>
<script>
(function(){
"use strict";
const MLS=JSON.parse(document.getElementById("mls-data").textContent);
const RED=JSON.parse(document.getElementById("redfin-data").textContent);
const TM=JSON.parse(document.getElementById("time-data").textContent);
const ST=JSON.parse(document.getElementById("street-data").textContent);
const REP=JSON.parse(document.getElementById("reprice-data").textContent);
const HT=JSON.parse(document.getElementById("high-data").textContent);
const UP=JSON.parse(document.getElementById("under-data").textContent);
const ABS=JSON.parse(document.getElementById("absorb-data").textContent);
const SL=JSON.parse(document.getElementById("seller-data").textContent);
const LAND=JSON.parse(document.getElementById("land-data").textContent);
const INCOME=JSON.parse(document.getElementById("income-data").textContent);
const MKT=JSON.parse(document.getElementById("marketing-data").textContent);
const BT=JSON.parse(document.getElementById("backtest-data").textContent);
const CX=JSON.parse(document.getElementById("context-data").textContent);
const LX=JSON.parse(document.getElementById("lease-data").textContent);
const M=MLS.meta, NB=MLS.neighborhoods;
function mktColor(m){return {"Seller's market":"var(--neg)","Balanced":"var(--ink-2)",
  "Buyer's market":"var(--good)","Deep buyer's market":"var(--good)"}[m]||"var(--ink-2)";}
// ---- live assumptions (screening knobs, recomputed in-browser) ----
const AS_SEED=JSON.parse(document.getElementById("assump-data").textContent);
function asLoad(){try{const s=JSON.parse(localStorage.getItem("fl_assump"));
  if(s&&s.verdictCut!=null&&s.absorption)return s;}catch(e){}
  return {verdictCut:AS_SEED.verdictCut, minComps:AS_SEED.minComps,
          absorption:Object.assign({},AS_SEED.absorption)};}
let AS=asLoad();
function vdictLive(gap,comps){
  if(gap==null)return null;
  if(comps!=null&&comps<1)return "Insufficient comps";
  const c=AS.verdictCut;
  return gap>c?"Overpriced":(gap<-c?"Underpriced":"Fairly priced");}
function mktLive(mos){
  if(mos==null)return null; const a=AS.absorption;
  return mos<a.sellers?"Seller's market":mos<a.balanced?"Balanced":
         mos<a.buyers?"Buyer's market":"Deep buyer's market";}
const $=s=>document.querySelector(s), tt=$("#tt");
const usd=v=>v==null?"—":"$"+Math.round(v).toLocaleString();
const pctS=v=>v==null?"—":(v>=0?"+":"")+v.toFixed(0)+"%";
const cvar=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let state={basis:"all", q:"", sort:{key:"norm_ppsf",dir:-1}, sel:null,
           timeMetric:"ppsf", timeNb:"", streetQ:"", streetSort:{key:"sold_ppsf",dir:-1},
           repType:"condo", repQ:"", htQ:""};
function vpill(v){
  const fg={Overpriced:"var(--over-fg)",Underpriced:"var(--under-fg)","Fairly priced":"var(--ink-2)","Insufficient comps":"var(--muted)"}[v]||"var(--ink-2)";
  const bg={Overpriced:"var(--over-bg)",Underpriced:"var(--under-bg)","Fairly priced":"var(--surface-2)","Insufficient comps":"var(--surface-2)"}[v]||"var(--surface-2)";
  return `<span class="pill" style="background:${bg};color:${fg}">${v||"—"}</span>`;}
const PROFILES={}; (MLS.profiles||[]).forEach(p=>PROFILES[p.neighborhood]=p);
function renderProfile(nb){const p=PROFILES[nb]; if(!p)return; state.sel=nb;
  $("#profName").textContent=nb;
  $("#profHead").textContent=p.headline;
  $("#profTps").innerHTML=p.talking_points.map(t=>`<li>${t}</li>`).join("");
  document.querySelectorAll("#tbl tbody tr").forEach(tr=>
    tr.classList.toggle("sel", tr.dataset.nb===nb));}

const idx=RED.market_index, appr=idx[idx.length-1].index_100/idx[0].index_100;
$("#subline").textContent=
  `${NB.length} neighborhoods priced from ${M.n_sold.toLocaleString()} closed sales · `
  +`per-home hedonic R² ${M.hedonic_r2} · waterfront worth +${M.premiums.waterfront_pct}% · `
  +`market up ${appr.toFixed(1)}× since ${RED.meta.generated_span[0].slice(0,4)}`;
$("#fn").textContent=M.n_sold.toLocaleString();

function kpis(){
  const rows=[
    ["Neighborhoods priced", NB.length, "sample-gated"],
    ["Citywide normalized", usd(M.city_norm_ppsf)+"/ft²", "standardized dry-lot home"],
    ["Waterfront premium", "+"+M.premiums.waterfront_pct+"%", "per-home, all else equal"],
    ["Appreciation", appr.toFixed(1)+"×", "since "+RED.meta.generated_span[0].slice(0,4)],
    ["Model accuracy", "±"+BT.overall.mdape+"%", "median, out-of-sample ("+BT.meta.n_scored.toLocaleString()+" sales)"],
  ];
  $("#kpis").innerHTML=rows.map(r=>`<div class="kpi"><div class="lab">${r[0]}</div>`
    +`<div class="val tnum fl-serif">${r[1]}</div><div class="note">${r[2]}</div></div>`).join("");
}
function drivers(){
  const p=M.premiums;
  const items=[
    ["Waterfront", p.waterfront_pct, true],
    ["Private pool", p.pool_pct, true],
    ["Each extra bath", p.bath_pct, true],
    ["Per decade older", p.age_per_decade_pct, true],
    ["Size elasticity", p.size_elasticity, false],
  ];
  $("#drivers").innerHTML=items.map(it=>{
    const v=it[1], isPct=it[2];
    const cls=isPct?(v>=0?"up":"down"):"";
    const disp=isPct?((v>=0?"+":"")+v.toFixed(1)+"%"):v.toFixed(2);
    return `<div class="drv"><div class="d-lab">${it[0]}</div><div class="d-val ${cls}">${disp}</div></div>`;
  }).join("");
}
function showTT(h,e){tt.innerHTML=h;tt.style.opacity=1;moveTT(e);}
function moveTT(e){const p=12;let x=e.clientX+p,y=e.clientY+p;const r=tt.getBoundingClientRect();
  if(x+r.width>innerWidth)x=e.clientX-r.width-p; if(y+r.height>innerHeight)y=e.clientY-r.height-p;
  tt.style.left=x+"px";tt.style.top=y+"px";}
function hideTT(){tt.style.opacity=0;}

function lineChart(){
  const W=520,H=260,pl=48,pr=16,pt=12,pb=28,d=idx;
  const xs=i=>pl+(W-pl-pr)*i/(d.length-1);
  const vmax=Math.max(...d.map(p=>p.index_100)),vmin=Math.min(100,...d.map(p=>p.index_100));
  const ys=v=>pt+(H-pt-pb)*(1-(v-vmin)/(vmax-vmin));
  const acc=cvar("--accent"),line=cvar("--line"),muted=cvar("--muted");
  let g="";[vmin,(vmin+vmax)/2,vmax].forEach(t=>{const y=ys(t);
    g+=`<line x1="${pl}" y1="${y}" x2="${W-pr}" y2="${y}" stroke="${line}"/>`
      +`<text x="${pl-7}" y="${y+4}" text-anchor="end" font-size="10.5" fill="${muted}">${Math.round(t)}</text>`;});
  const pts=d.map((p,i)=>`${xs(i)},${ys(p.index_100)}`).join(" ");
  let xlab="",seen={};d.forEach((p,i)=>{const yr=p.month_key.slice(0,4);
    if(!(yr in seen)&&+yr%3===0){seen[yr]=1;xlab+=`<text x="${xs(i)}" y="${H-7}" text-anchor="middle" font-size="10" fill="${muted}">${yr}</text>`;}});
  const e=d[d.length-1];
  const hot=`<circle cx="${xs(d.length-1)}" cy="${ys(e.index_100)}" r="4" fill="${acc}"/>`
    +`<text x="${xs(d.length-1)-6}" y="${ys(e.index_100)-9}" text-anchor="end" font-size="12" font-weight="700" fill="${cvar('--accent-deep')}">${e.index_100.toFixed(0)}</text>`;
  const hit=d.map((p,i)=>`<rect x="${xs(i)-4}" y="${pt}" width="8" height="${H-pt-pb}" fill="transparent" data-i="${i}"/>`).join("");
  $("#lineChart").innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Appreciation index">`
    +g+`<polygon points="${pl},${ys(vmin)} ${pts} ${W-pr},${ys(vmin)}" fill="${acc}" opacity="0.08"/>`
    +`<polyline points="${pts}" fill="none" stroke="${acc}" stroke-width="2.2"/>`+hot
    +xlab+`<g id="lh">${hit}</g></svg>`;
  $("#lineChart").querySelectorAll("#lh rect").forEach(r=>{
    r.addEventListener("mousemove",e=>{const p=d[+r.dataset.i];
      showTT(`<b>${p.month_key}</b><br>Index ${p.index_100.toFixed(1)} (${((p.index_100/100-1)*100).toFixed(0)}% vs 2012)`,e);});
    r.addEventListener("mouseleave",hideTT);});
}
function flags(){
  const f=MLS.live_flag_summary, tot=(f.Overpriced||0)+(f.Fair||0)+(f.Underpriced||0);
  $("#flagRow").innerHTML=
    `<div class="flagbox fb-over"><div class="n tnum">${f.Overpriced||0}</div><div class="t">Over</div></div>`
   +`<div class="flagbox fb-fair"><div class="n tnum">${f.Fair||0}</div><div class="t">Fair</div></div>`
   +`<div class="flagbox fb-under"><div class="n tnum">${f.Underpriced||0}</div><div class="t">Under</div></div>`;
  $("#deals").innerHTML=MLS.deals.slice(0,7).map(d=>
    `<div class="deal"><div><span class="dn">${d.neighborhood}</span>`
    +`<div class="dm">${usd(d.list_price)} · ${(d.sqft||0).toLocaleString()} ft² · ask ${usd(d.ask_ppsf)} vs model ${usd(d.pred_ppsf)}</div></div>`
    +`<div class="dg">${d.gap_pct.toFixed(0)}%</div></div>`).join("")
    ||`<div class="dm">No single-family candidates in the current set.</div>`;
}

function filtered(){
  const q=state.q.toLowerCase();
  return NB.filter(r=>(state.basis==="all"||r.basis_type===state.basis)
    &&(!q||r.neighborhood.toLowerCase().includes(q)));
}
function conf(n){return n>=40?"High":(n>=20?"Medium":"Low");}
function barChart(){
  const rows=filtered().slice().sort((a,b)=>b.norm_ppsf-a.norm_ppsf).slice(0,15);
  const acc=cvar("--accent"),orange="#eb6834",ink=cvar("--ink-2");
  const W=560,rowH=26,labW=168,valW=60,H=6+rows.length*rowH+4,bx0=labW,bxW=W-labW-valW;
  const vmax=Math.max(...rows.map(r=>r.norm_ppsf))*1.02;
  let s="";
  rows.forEach((r,i)=>{const y=6+i*rowH,w=bxW*r.norm_ppsf/vmax,col=r.basis_type==="Single Family"?acc:orange;
    s+=`<text x="${labW-10}" y="${y+rowH/2+4}" text-anchor="end" font-size="12" fill="${ink}">${r.neighborhood}</text>`
      +`<rect x="${bx0}" y="${y+3}" width="${bxW}" height="${rowH-8}" rx="3" fill="var(--surface-2)"/>`
      +`<rect x="${bx0}" y="${y+3}" width="${w.toFixed(1)}" height="${rowH-8}" rx="3" fill="${col}" class="barR" `
      +`data-n="${r.neighborhood}" data-v="${r.norm_ppsf}" data-b="${r.basis_type}" data-w="${r.waterfront_share}"/>`
      +`<text x="${bx0+w+6}" y="${y+rowH/2+4}" font-size="12" font-weight="600" fill="${cvar('--ink')}" class="tnum">${usd(r.norm_ppsf)}</text>`;});
  $("#barChart").innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Top neighborhoods by normalized price per square foot">${s}</svg>`;
  $("#barChart").querySelectorAll(".barR").forEach(b=>{
    b.addEventListener("mousemove",e=>showTT(`<b>${b.dataset.n}</b><br>${usd(+b.dataset.v)}/ft² normalized`
      +`<br>${b.dataset.b} basis · ${Math.round(+b.dataset.w*100)}% waterfront`,e));
    b.addEventListener("mouseleave",hideTT);});
  $("#barTitle").textContent=`Top neighborhoods by normalized $/sqft`;
  $("#barCap").textContent=`Blue = single-family basis, orange = condo. Top 15 of ${filtered().length}.`;
}

const COLS=[
  {k:"rank",t:"#",l:1,f:(r,i)=>`<span class="rank">${i+1}</span>`},
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span> <span class="basis">${r.basis_type==="Single Family"?"SFR":r.basis_type}</span>`},
  {k:"geo_type",t:"Geography",l:1,f:r=>`<span class="geo">${r.geo_type||"—"}</span>`},
  {k:"norm_ppsf",t:"Norm. $/ft²",f:r=>`<span class="tnum">${usd(r.norm_ppsf)}</span>`},
  {k:"vs_city_pct",t:"vs City",f:r=>r.vs_city_pct==null?"—":`<span class="tnum ${r.vs_city_pct>=0?'pos':'neg'}">${pctS(r.vs_city_pct)}</span>`},
  {k:"sold_ppsf_median",t:"Median sold $/ft²",f:r=>`<span class="tnum">${usd(r.sold_ppsf_median)}</span>`},
  {k:"waterfront_ppsf",t:"Waterfront $/ft²",f:r=>r.waterfront_ppsf==null?"—":`<span class="tnum wf">${usd(r.waterfront_ppsf)}</span>`},
  {k:"new_premium_pct",t:"New vs exist",f:r=>r.new_premium_pct==null?"—":`<span class="tnum ${r.new_premium_pct>=0?'pos':'neg'}">${pctS(r.new_premium_pct)}</span>`},
  {k:"median_discount_pct",t:"Discount",f:r=>r.median_discount_pct==null?"—":`<span class="tnum">${r.median_discount_pct.toFixed(1)}%</span>`},
  {k:"failure_rate",t:"Failure rate",f:r=>r.failure_rate==null?"—":`<span class="tnum">${r.failure_rate.toFixed(0)}%</span>`},
  {k:"sold_n",t:"Sold",f:r=>`<span class="tnum">${r.sold_n}</span>`},
  {k:"conf",t:"Conf.",f:r=>{const c=conf(r.sold_n);return `<span class="pill ${c}">${c}</span>`;}},
];
function renderTable(){
  $("#tbl thead").innerHTML="<tr>"+COLS.map(c=>{const act=state.sort.key===c.k;
    const arw=act?(state.sort.dir<0?"▼":"▲"):"";
    return `<th class="${c.l?'l':''}" data-k="${c.k}">${c.t} <span class="arw">${arw}</span></th>`;}).join("")+"</tr>";
  let rows=filtered().slice();
  const sk=state.sort.key;
  if(sk==="rank"){rows.sort((a,b)=>b.norm_ppsf-a.norm_ppsf);}
  else if(sk==="conf"){rows.sort((a,b)=>state.sort.dir*((a.sold_n)-(b.sold_n)));}
  else{rows.sort((a,b)=>{let x=a[sk],y=b[sk];
    if(sk==="neighborhood"){return state.sort.dir*(""+x).localeCompare(""+y);}
    x=x==null?-Infinity:x;y=y==null?-Infinity:y;return state.sort.dir*(x-y);});}
  $("#tbl tbody").innerHTML=rows.map((r,i)=>`<tr data-nb="${r.neighborhood}"${r.neighborhood===state.sel?' class="sel"':''}>`
    +COLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r,i)}</td>`).join("")+"</tr>").join("");
  $("#tbl tbody").querySelectorAll("tr").forEach(tr=>tr.onclick=()=>renderProfile(tr.dataset.nb));
  $("#tbl thead").querySelectorAll("th").forEach(th=>th.onclick=()=>{const k=th.dataset.k;
    if(state.sort.key===k)state.sort.dir*=-1; else state.sort={key:k,dir:(k==="neighborhood"?1:-1)};
    renderTable();});
  $("#tblTitle").textContent=`Neighborhood detail (${rows.length})`;
  $("#noteLine").textContent=`Discounts are actual list-to-sale on closed homes. Failure rate = failed listings ÷ (failed + sold). `
    +`Standardized home ≈ ${M.standardized_home.sqft.toLocaleString()} ft², ${Math.round(M.standardized_home.age)} yrs old.`;
}

function geostrip(){
  const wet=new Set(["Finger-isle waterfront","Barrier island / beach","Intracoastal / canal waterfront"]);
  $("#geostrip").innerHTML=(MLS.geography||[]).map(g=>
    `<div class="geot${wet.has(g.geo_type)?' wet':''}"><div class="g-t">${g.geo_type}</div>`
    +`<div class="g-v tnum">${usd(g.median_ppsf)}</div><div class="g-n">${g.n.toLocaleString()} sales`
    +`${g.waterfront_ppsf?` · WF ${usd(g.waterfront_ppsf)}`:''}</div></div>`).join("");
}
// ---------- time explorer ----------
const TMETA=TM.meta;
$("#timeSummary").textContent=`· citywide $${TMETA.city_2020_ppsf}/ft² (2020) → $${TMETA.city_now_ppsf} (${(TMETA.city_pct_since_2020>=0?"+":"")+TMETA.city_pct_since_2020}%)`;
(function initSelect(){
  const names=Object.keys(TM.neighborhood_ppsf.series).sort();
  $("#nbSelect").insertAdjacentHTML("beforeend",
    names.map(n=>`<option value="${n}">${n}</option>`).join(""));
})();
function timeVal(r,m){return m==="ppsf"?r.ppsf:m==="dom"?r.dom:(1-r.s2l)*100;}
function timeFmt(v,m){return m==="ppsf"?usd(v):m==="dom"?Math.round(v)+"d":v.toFixed(1)+"%";}
function renderTime(){
  const tl=TM.market_timeline, months=TM.neighborhood_ppsf.months, m=state.timeMetric;
  const cw=tl.map(r=>timeVal(r,m));
  const overlay=(m==="ppsf"&&state.timeNb)?TM.neighborhood_ppsf.series[state.timeNb]:null;
  const W=1000,H=340,pl=56,pr=16,pt=14,pb=28;
  const xs=i=>pl+(W-pl-pr)*i/(cw.length-1);
  let vals=cw.filter(v=>v!=null); if(overlay)vals=vals.concat(overlay.filter(v=>v!=null));
  let vmin=Math.min(...vals),vmax=Math.max(...vals); if(m==="disc")vmin=Math.min(0,vmin);
  const pad=(vmax-vmin)*0.08; vmin-=pad; vmax+=pad;
  if(m!=="disc")vmin=Math.max(0,vmin);   // price / DOM can't go negative
  const ys=v=>pt+(H-pt-pb)*(1-(v-vmin)/(vmax-vmin));
  const acc=cvar("--accent"),orange="#eb6834",line=cvar("--line"),muted=cvar("--muted");
  let g="";
  for(let k=0;k<=4;k++){const v=vmin+(vmax-vmin)*k/4,y=ys(v);
    g+=`<line x1="${pl}" y1="${y}" x2="${W-pr}" y2="${y}" stroke="${line}"/>`
      +`<text x="${pl-7}" y="${y+4}" text-anchor="end" font-size="11" fill="${muted}">${timeFmt(v,m)}</text>`;}
  let seen={},xlab="";
  months.forEach((mo,i)=>{const yr=mo.slice(0,4);
    if(!(yr in seen)){seen[yr]=1;xlab+=`<text x="${xs(i)}" y="${H-8}" text-anchor="middle" font-size="10.5" fill="${muted}">${yr}</text>`;}});
  // frenzy marker (2022-05)
  const fi=months.indexOf("2022-05");
  if(fi>=0)g+=`<line x1="${xs(fi)}" y1="${pt}" x2="${xs(fi)}" y2="${H-pb}" stroke="${muted}" stroke-width="1" stroke-dasharray="3 3"/>`;
  const path=(arr,col)=>{let d="",started=false;
    arr.forEach((v,i)=>{if(v==null){started=false;return;}
      d+=(started?"L":"M")+xs(i)+" "+ys(v)+" ";started=true;});
    return `<path d="${d}" fill="none" stroke="${col}" stroke-width="2.2"/>`;};
  let paths=path(cw,acc); if(overlay)paths+=path(overlay,orange);
  const hit=months.map((mo,i)=>`<rect x="${xs(i)-4}" y="${pt}" width="8" height="${H-pt-pb}" fill="transparent" data-i="${i}"/>`).join("");
  $("#timeChart").innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Market metric over time">${g}${paths}<g id="th">${hit}</g></svg>`;
  const label={ppsf:"Price per ft²",dom:"Days on market",disc:"Discount to list"}[m];
  $("#timeLegend").innerHTML=`<span><span class="sw" style="background:${acc}"></span>Citywide — ${label}</span>`
    +(overlay?`<span><span class="sw" style="background:${orange}"></span>${state.timeNb}</span>`:"");
  $("#timeChart").querySelectorAll("#th rect").forEach(r=>{
    r.addEventListener("mousemove",e=>{const i=+r.dataset.i,mo=months[i];
      let h=`<b>${mo}</b><br>Citywide ${timeFmt(cw[i],m)}`;
      if(overlay&&overlay[i]!=null)h+=`<br>${state.timeNb} ${usd(overlay[i])}`;
      showTT(h,e);});
    r.addEventListener("mouseleave",hideTT);});
}
function movers(){
  const ok=TM.shifts.filter(s=>s.sold_total>=40);
  const gain=ok.filter(s=>s.pct_2020_now!=null).sort((a,b)=>b.pct_2020_now-a.pct_2020_now).slice(0,6);
  const cool=ok.filter(s=>s.pct_off_peak!=null).sort((a,b)=>a.pct_off_peak-b.pct_off_peak).slice(0,6);
  $("#gainers").innerHTML=gain.map(s=>
    `<div class="deal"><div><span class="dn">${s.neighborhood}</span>`
    +`<div class="dm">$${s.ppsf_2020}→$${s.ppsf_now}/ft² · DOM ${s.dom_2020}→${s.dom_now}</div></div>`
    +`<div class="dg">+${s.pct_2020_now.toFixed(0)}%</div></div>`).join("");
  $("#coolers").innerHTML=cool.map(s=>
    `<div class="deal"><div><span class="dn">${s.neighborhood}</span>`
    +`<div class="dm">peak $${s.ppsf_peak} → now $${s.ppsf_now}/ft²</div></div>`
    +`<div class="dg" style="color:var(--neg)">${s.pct_off_peak.toFixed(0)}%</div></div>`).join("");
}
$("#metricSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  state.timeMetric=b.dataset.m;
  if(state.timeMetric!=="ppsf"){state.timeNb="";$("#nbSelect").value="";}
  [...$("#metricSeg").children].forEach(x=>x.setAttribute("aria-pressed",x===b));renderTime();});
$("#nbSelect").addEventListener("change",e=>{state.timeNb=e.target.value;
  if(state.timeNb&&state.timeMetric!=="ppsf"){state.timeMetric="ppsf";
    [...$("#metricSeg").children].forEach(x=>x.setAttribute("aria-pressed",x.dataset.m==="ppsf"));}
  renderTime();});

// ---------- street underwriting ----------
$("#streetSummary").textContent=`· ${ST.meta.n_streets} streets · ${ST.meta.n_live_underwritten.toLocaleString()} live listings underwritten`;
const SCOLS=[
  {k:"street",t:"Street",l:1,f:r=>`<span class="nbh">${r.street}</span>`},
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="geo">${r.neighborhood}</span>`},
  {k:"sold_ppsf",t:"Sold $/ft²",f:r=>`<span class="tnum">${usd(r.sold_ppsf)}</span>`},
  {k:"premium_vs_nbhd",t:"vs Nbhd",f:r=>r.premium_vs_nbhd==null?"—":`<span class="tnum ${r.premium_vs_nbhd>=0?'pos':'neg'}">${pctS(r.premium_vs_nbhd)}</span>`},
  {k:"waterfront_share",t:"WF",f:r=>`<span class="tnum wf">${Math.round((r.waterfront_share||0)*100)}%</span>`},
  {k:"median_price",t:"Median price",f:r=>`<span class="tnum">${usd(r.median_price)}</span>`},
  {k:"n_sold",t:"Sold",f:r=>`<span class="tnum">${r.n_sold}</span>`},
  {k:"n_active",t:"Active",f:r=>`<span class="tnum">${r.n_active}</span>`},
];
function renderStreets(){
  const q=state.streetQ.toLowerCase();
  let rows=ST.streets.filter(r=>!q||r.street.toLowerCase().includes(q)||(r.neighborhood||"").toLowerCase().includes(q));
  const sk=state.streetSort.key,dir=state.streetSort.dir;
  rows=rows.slice().sort((a,b)=>{let x=a[sk],y=b[sk];
    if(sk==="street"||sk==="neighborhood")return dir*(""+x).localeCompare(""+y);
    x=x==null?-Infinity:x;y=y==null?-Infinity:y;return dir*(x-y);});
  rows=rows.slice(0,120);
  $("#streetTbl thead").innerHTML="<tr>"+SCOLS.map(c=>{const a=state.streetSort.key===c.k;
    return `<th class="${c.l?'l':''}" data-k="${c.k}">${c.t} <span class="arw">${a?(dir<0?"▼":"▲"):""}</span></th>`;}).join("")+"</tr>";
  $("#streetTbl tbody").innerHTML=rows.map(r=>"<tr>"+SCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("");
  $("#streetTbl thead").querySelectorAll("th").forEach(th=>th.onclick=()=>{const k=th.dataset.k;
    if(state.streetSort.key===k)state.streetSort.dir*=-1; else state.streetSort={key:k,dir:(k==="street"||k==="neighborhood"?1:-1)};
    renderStreets();});
}
const UCOLS=[
  {k:"address",t:"Address",l:1,f:r=>`<span class="nbh">${r.address}</span>`},
  {k:"street",t:"Street",l:1,f:r=>`<span class="geo">${r.street}</span>`},
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="geo">${r.neighborhood}</span>`},
  {k:"list_price",t:"List",f:r=>`<span class="tnum">${usd(r.list_price)}</span>`},
  {k:"ask_ppsf",t:"Ask $/ft²",f:r=>`<span class="tnum">${usd(r.ask_ppsf)}</span>`},
  {k:"street_value_ppsf",t:"Street value",f:r=>`<span class="tnum">${usd(r.street_value_ppsf)}</span>`},
  {k:"street_comps",t:"Comps",f:r=>`<span class="tnum">${r.street_comps}</span>`},
  {k:"gap_vs_street",t:"Gap",f:r=>`<span class="tnum" style="color:var(--good);font-weight:700">${r.gap_vs_street.toFixed(0)}%</span>`},
];
function renderUW(){
  const q=state.streetQ.toLowerCase();
  const rows=ST.deals.filter(r=>!q||(r.street||"").toLowerCase().includes(q)||(r.neighborhood||"").toLowerCase().includes(q)||(r.address||"").toLowerCase().includes(q));
  $("#uwTbl thead").innerHTML="<tr>"+UCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#uwTbl tbody").innerHTML=rows.map(r=>"<tr>"+UCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="8" style="color:var(--muted)">No comp-backed candidates match.</td></tr>`;
}
$("#streetSearch").addEventListener("input",e=>{state.streetQ=e.target.value;renderStreets();renderUW();});

// ---------- deal scenario & financing ----------
const SCN=JSON.parse(document.getElementById("scen-data").textContent);
const gv=id=>parseFloat($(id).value)||0;
function scenAt(shiftBps,p){
  const pElast=gv("#scPElast"),cash=gv("#scCash"),dElast=gv("#scDElast"),
        rate=gv("#scRate"),down=gv("#scDown"),amort=gv("#scAmort"),sqft=gv("#scSqft")||1,
        baseDom=(SCN[$("#scNb").value]||{}).dom||90;
  const pf=1+(pElast/100)*(shiftBps/100)*(1-cash/100);
  const price=p*pf, rt=rate+shiftBps/100, loan=price*(1-down/100),
        m=rt/100/12, n=amort*12;
  const pay=m>0?loan*m/(1-Math.pow(1+m,-n)):loan/n;
  return {price,ppsf:price/sqft,dom:baseDom*(1+(dElast/100)*(shiftBps/100)),rate:rt,pay,loan};
}
function scCalc(){
  $("#scDownV").textContent=gv("#scDown").toFixed(0)+"%";
  $("#scRateV").textContent=gv("#scRate").toFixed(3).replace(/0+$/,"").replace(/\.$/,"")+"%";
  $("#scShiftV").textContent=(gv("#scShift")>=0?"+":"")+gv("#scShift")+"bps";
  $("#scCashV").textContent=gv("#scCash").toFixed(0)+"%";
  const price=gv("#scPrice"),shift=gv("#scShift"),down=gv("#scDown"),
        apprec=gv("#scApprec"),hold=gv("#scHold"),sell=gv("#scSell"),
        amort=gv("#scAmort"),rate=gv("#scRate");
  const c=scenAt(shift,price);
  const cashToClose=price*down/100+price*0.03;
  const n=amort*12,k=hold*12,m=rate/100/12;
  const remLoan=m>0?c.loan*(Math.pow(1+m,n)-Math.pow(1+m,k))/(Math.pow(1+m,n)-1):c.loan*(1-k/n);
  const exit=c.price*Math.pow(1+apprec/100,hold);
  const net=exit-exit*sell/100-remLoan;
  const annR=cashToClose>0?(Math.pow(net/cashToClose,1/hold)-1)*100:0;
  const dpx=(c.price/price-1)*100;
  const tile=(t,v,s,cls)=>`<div class="scn-tile${cls&&cls.hi?' hi':''}"><div class="t">${t}</div>`
    +`<div class="v ${cls&&cls.dir||''}">${v}</div><div class="s">${s||""}</div></div>`;
  $("#scTiles").innerHTML=[
    tile("Adjusted market price",usd(c.price),`${dpx>=0?"+":""}${dpx.toFixed(1)}% vs base`,{hi:1,dir:dpx>0?"up":dpx<0?"down":""}),
    tile("Adjusted $/sqft",usd(c.ppsf),`base ${usd(price/(gv("#scSqft")||1))}`,{hi:1}),
    tile("Projected days on market",Math.round(c.dom),`at ${c.rate.toFixed(2)}% rate`,{hi:1}),
    tile("Monthly P&I",usd(c.pay),`loan ${usd(c.loan)}`),
    tile("Cash to close",usd(cashToClose),`${down}% down + ~3% costs`),
    tile(`Exit value (${hold}y @ ${apprec}%)`,usd(exit),`after ${sell}% sell costs`),
    tile("Equity multiple",(net/cashToClose).toFixed(2)+"×",`net ${usd(net)}`,{dir:net>cashToClose?"up":"down"}),
    tile("Annualized return",annR.toFixed(1)+"%",`on ${usd(cashToClose)} equity`,{dir:annR>0?"up":"down"}),
  ].join("");
  const shifts=[-200,-100,-50,0,50,100,200];
  $("#scSens thead").innerHTML="<tr><th class='l'>Rate shift</th><th>Mkt price</th><th>$/sqft</th><th>Proj. DOM</th><th>Monthly P&amp;I</th></tr>";
  $("#scSens tbody").innerHTML=shifts.map(sh=>{const x=scenAt(sh,price);
    const hl=sh===shift?' style="background:var(--accent-soft)"':'';
    return `<tr${hl}><td class="l tnum">${sh>=0?"+":""}${sh}bps</td><td class="tnum">${usd(x.price)}</td>`
      +`<td class="tnum">${usd(x.ppsf)}</td><td class="tnum">${Math.round(x.dom)}</td><td class="tnum">${usd(x.pay)}</td></tr>`;}).join("");
  $("#scNote").textContent="Price sensitivity is dampened by the cash-buyer share (cash buyers ignore rates). "
    +"Set the elasticities to your own read — defaults are conservative and FL luxury is historically rate-insensitive (prices rose through the 2022–24 rate hikes).";
}
function scSeed(){
  const s=SCN[$("#scNb").value]||{};
  const sqft=Math.max(500,Math.round((s.price&&s.ppsf?s.price/s.ppsf:3000)/100)*100);
  $("#scSqft").value=sqft;
  $("#scPrice").value=Math.round((s.price||(s.ppsf||500)*sqft)/50000)*50000;
  if(s.apprec!=null)$("#scApprec").value=((Math.pow(1+s.apprec/100,1/6)-1)*100).toFixed(1);
  scCalc();
}
function scInit(){
  $("#scNb").innerHTML=Object.keys(SCN).sort().map(n=>`<option>${n}</option>`).join("");
  const def=["Rio Vista","Coral Ridge","Las Olas"].find(n=>n in SCN)||Object.keys(SCN)[0];
  $("#scNb").value=def;
  $("#scNb").addEventListener("change",scSeed);
  ["#scPrice","#scSqft","#scDown","#scRate","#scAmort","#scShift","#scPElast","#scCash",
   "#scDElast","#scApprec","#scHold","#scSell"].forEach(id=>$(id).addEventListener("input",scCalc));
  scSeed();
}

// ---------- absorption ----------
let absQ="";
function absBands(){
  $("#absBands").innerHTML=(ABS.by_band||[]).map(b=>{const mk=mktLive(b.months_supply);
    return `<div class="geot"><div class="g-t">${b.band}</div>`
    +`<div class="g-v tnum">${b.months_supply}<span style="font-size:12px;color:var(--muted)"> mo</span></div>`
    +`<div class="g-n" style="color:${mktColor(mk)}">${mk||"—"}</div>`
    +`<div class="g-n">${b.sold_2y} sold / ${b.active} live</div></div>`;}).join("");
}
const ABCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>`},
  {k:"band",t:"Band",l:1,f:r=>`<span class="basis">${r.band}</span>`},
  {k:"sold_2y",t:"Sold (2y)",f:r=>`<span class="tnum">${r.sold_2y}</span>`},
  {k:"active",t:"Active",f:r=>`<span class="tnum">${r.active}</span>`},
  {k:"months_supply",t:"Months supply",f:r=>`<span class="tnum">${r.months_supply==null?"—":r.months_supply}</span>`},
  {k:"market",t:"Market",l:1,f:r=>{const mk=mktLive(r.months_supply);return `<span class="tnum" style="color:${mktColor(mk)};font-weight:600">${mk||"—"}</span>`;}},
];
function absTable(){
  const q=absQ.toLowerCase();
  let rows=ABS.by_band_neighborhood.filter(r=>!q||r.neighborhood.toLowerCase().includes(q));
  if(!q)rows=rows.slice(0,60);
  $("#absTbl thead").innerHTML="<tr>"+ABCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#absTbl tbody").innerHTML=rows.map(r=>"<tr>"+ABCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="6" style="color:var(--muted)">No absorption data for that search.</td></tr>`;
}
$("#absSearch").addEventListener("input",e=>{absQ=e.target.value;absTable();});

// ---------- land & docks ----------
const LM=LAND.meta;
$("#landSummary").textContent=`· FLL land $${LM.fll_land_ppsf}/ft² (wf $${LM.fll_waterfront_ppsf} vs dry $${LM.fll_dry_ppsf}) · ${LM.n_sold.toLocaleString()} comps · ${LM.n_dock_sold} dock sales`;
function landStrips(){
  $("#landGeo").innerHTML=(LAND.geography||[]).map(g=>
    `<div class="geot${/Waterfront/.test(g.geo)?' wet':''}"><div class="g-t">${g.geo}</div>`
    +`<div class="g-v tnum">${usd(g.land_ppsf)}<span style="font-size:11px;color:var(--muted)">/ft²</span></div>`
    +`<div class="g-n">${g.n} sold · ${g.scope}</div></div>`).join("");
  const zones=(LAND.by_zoning||[]).map(z=>
    `<div class="geot"><div class="g-t">${z.density}</div>`
    +`<div class="g-v tnum">${usd(z.land_ppsf)}<span style="font-size:11px;color:var(--muted)">/ft²</span></div>`
    +`<div class="g-n">${z.n} sold</div></div>`).join("");
  const acr=(LAND.acreage||[]).slice(0,4).map(a=>
    `<div class="geot"><div class="g-t">${a.band}</div>`
    +`<div class="g-v tnum">${usd(a.land_ppsf)}<span style="font-size:11px;color:var(--muted)">/ft²</span></div>`
    +`<div class="g-n">$${(a.per_acre||0).toLocaleString()}/ac · ${a.n}</div></div>`).join("");
  $("#landZone").innerHTML=zones+acr;
  const d=LAND.docks, c=LAND.commercial;
  let dh=`<div class="geot wet"><div class="g-t">Docks / dockominiums</div>`
    +`<div class="g-v tnum">${usd(d.median_sold)}</div>`
    +`<div class="g-n">${d.n_sold} sold · $${(d.min_sold||0).toLocaleString()}–$${(d.max_sold||0).toLocaleString()}</div></div>`;
  if(c)dh+=`<div class="geot"><div class="g-t">Commercial / dev land</div>`
    +`<div class="g-v tnum">${usd(c.median_ppsf_sold)}<span style="font-size:11px;color:var(--muted)">/ft²</span></div>`
    +`<div class="g-n">${c.n_sold} sold · $${(c.per_acre_sold||0).toLocaleString()}/ac · ${c.n_active} live</div></div>`;
  const iva=(LAND.implied_vs_actual||[])[0];
  if(iva)dh+=`<div class="geot"><div class="g-t">Implied vs actual (${iva.neighborhood})</div>`
    +`<div class="g-v tnum">${usd(iva.actual_ppsf)}</div>`
    +`<div class="g-n">hedonic $${iva.implied_ppsf} → comps ${iva.gap_pct>=0?"+":""}${iva.gap_pct}%</div></div>`;
  $("#landDock").innerHTML=dh;
}
let landQ="";
const LDCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>${r.in_improved?' <span class="basis">FLL</span>':''}`},
  {k:"n_sold",t:"Sold",f:r=>`<span class="tnum">${r.n_sold}</span>`},
  {k:"land_ppsf",t:"Land $/ft²",f:r=>`<span class="tnum">${usd(r.land_ppsf)}</span>`},
  {k:"per_acre",t:"$/acre",f:r=>`<span class="tnum">${usd(r.per_acre)}</span>`},
  {k:"waterfront_share",t:"WF",f:r=>`<span class="tnum wf">${Math.round((r.waterfront_share||0)*100)}%</span>`},
  {k:"median_price",t:"Median price",f:r=>`<span class="tnum">${usd(r.median_price)}</span>`},
  {k:"n_active",t:"Active",f:r=>`<span class="tnum">${r.n_active}</span>`},
];
function landTable(){
  const q=landQ.toLowerCase();
  let rows=LAND.by_neighborhood.filter(r=>(r.n_sold>=AS.minComps)&&(!q||r.neighborhood.toLowerCase().includes(q)));
  if(!q)rows=rows.slice(0,40);
  $("#landTbl thead").innerHTML="<tr>"+LDCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#landTbl tbody").innerHTML=rows.map(r=>"<tr>"+LDCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="7" style="color:var(--muted)">No land comps match.</td></tr>`;
}
$("#landSearch").addEventListener("input",e=>{landQ=e.target.value;landTable();});

// ---------- multifamily / income ----------
const IM=INCOME.meta;
$("#mfSummary").textContent=`· ${IM.n_sold} sold · median $${IM.median_ppu.toLocaleString()}/unit · $${IM.median_ppsf}/ft² · ${IM.n_over} over / ${IM.n_under} under on ask`;
function mfStrips(){
  $("#mfTiers").innerHTML=(INCOME.by_tier||[]).map(t=>
    `<div class="geot"><div class="g-t">${t.tier}</div>`
    +`<div class="g-v tnum">${usd(t.ppu)}</div>`
    +`<div class="g-n">$${t.ppsf}/ft² · ${t.n} sold</div></div>`).join("");
}
let mfQ="";
const MFCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>${r.in_improved?'':' <span class="basis">wider</span>'}`},
  {k:"n_sold",t:"Sold",f:r=>`<span class="tnum">${r.n_sold}</span>`},
  {k:"ppu",t:"$/unit",f:r=>`<span class="tnum">${usd(r.ppu)}</span>`},
  {k:"ppsf",t:"$/ft²",f:r=>`<span class="tnum">${usd(r.ppsf)}</span>`},
  {k:"median_units",t:"Units",f:r=>`<span class="tnum">${r.median_units||"—"}</span>`},
  {k:"n_active",t:"Active",f:r=>`<span class="tnum">${r.n_active}</span>`},
  {k:"gap_pct",t:"Ask vs sold",f:r=>r.gap_pct==null?"—":`<span class="tnum ${r.gap_pct>0?'neg':'pos'}">${pctS(r.gap_pct)}</span>`},
  {k:"verdict",t:"Verdict",l:1,f:r=>{const v=vdictLive(r.gap_pct,r.n_sold);return v?vpill(v):"—";}},
];
function mfTable(){
  const q=mfQ.toLowerCase();
  let rows=INCOME.by_neighborhood.filter(r=>(r.n_sold>=AS.minComps)&&(!q||r.neighborhood.toLowerCase().includes(q)));
  $("#mfTbl thead").innerHTML="<tr>"+MFCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#mfTbl tbody").innerHTML=rows.map(r=>"<tr>"+MFCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="8" style="color:var(--muted)">No multifamily comps match.</td></tr>`;
}
$("#mfSearch").addEventListener("input",e=>{mfQ=e.target.value;mfTable();});

// ---------- marketing kit ----------
const MKCOPY={};
function copyText(txt,btn){
  const done=()=>{const o=btn.textContent;btn.textContent="Copied!";btn.classList.add("ok");
    setTimeout(()=>{btn.textContent=o;btn.classList.remove("ok");},1200);};
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,done);}
  else{const t=document.createElement("textarea");t.value=txt;t.style.position="fixed";t.style.opacity="0";
    document.body.appendChild(t);t.select();try{document.execCommand("copy");}catch(e){}document.body.removeChild(t);done();}}
document.addEventListener("click",e=>{const b=e.target.closest(".copybtn");if(!b)return;
  copyText(MKCOPY[b.dataset.copy]||"",b);});
function mkCards(){
  $("#mkCards").innerHTML=(MKT.stat_cards||[]).map(c=>
    `<div class="geot"><div class="g-t">${c.label}</div><div class="g-v tnum">${c.value}</div>`
    +`<div class="g-n">${c.note||""}</div></div>`).join("");}
function mkRender(nb){
  const k=MKT.neighborhoods.find(x=>x.neighborhood===nb); if(!k)return;
  MKCOPY.snap=k.snapshot||""; MKCOPY.share=k.shareable||""; MKCOPY.cma=k.cma_line||"";
  MKCOPY.tps=(k.talking_points||[]).map(t=>"• "+t).join("\n");
  const blk=(h,key,html)=>`<div class="mk-block"><div class="mk-h">${h}`
    +`<button class="copybtn" data-copy="${key}">Copy</button></div>${html}</div>`;
  let out="";
  if(k.snapshot)out+=blk("Market snapshot — email / CMA","snap",`<p>${k.snapshot}</p>`);
  if(k.shareable)out+=blk("Shareable stat — social","share",`<p>${k.shareable}</p>`);
  if(k.cma_line)out+=blk("CMA / pricing line","cma",`<p>${k.cma_line}</p>`);
  if((k.talking_points||[]).length)out+=blk("Talking points","tps",
    `<ul class="tps" style="margin-top:0">${k.talking_points.map(t=>`<li>${t}</li>`).join("")}</ul>`);
  if((k.cost_points||[]).length){MKCOPY.cost=k.cost_points.join("\n\n");
    out+=blk("Costs & build-vs-buy","cost",
      `<ul class="opp-reasons">${k.cost_points.map(t=>`<li>${t}</li>`).join("")}</ul>`);}
  if(k.lease_line){MKCOPY.lease=k.lease_line;
    out+=blk("Rent or sell?","lease",`<p>${k.lease_line}</p>`);}
  if((k.opportunities||[]).length){MKCOPY.opps=k.opportunities.map(o=>o.line).join("\n\n");
    out+=blk("Live buyer opportunities here","opps",
      `<ul class="opp-reasons">${k.opportunities.map(o=>`<li>${o.line}</li>`).join("")}</ul>`);}
  $("#mkContent").innerHTML=out;}
function mktInit(){
  $("#mkNote").textContent=MKT.meta.note||"";
  $("#mkPulse").textContent=MKT.market_pulse; MKCOPY.pulse=MKT.market_pulse;
  mkCards();
  const names=MKT.neighborhoods.filter(k=>k.snapshot)
    .sort((a,b)=>(a.rank||999)-(b.rank||999)).map(k=>k.neighborhood);
  $("#mkNb").innerHTML=names.map(n=>`<option>${n}</option>`).join("");
  $("#mkNb").addEventListener("change",e=>mkRender(e.target.value));
  if(names.length)mkRender(names[0]);}

// ---------- costs & market realities ----------
let cxQ="";
function cxBench(){
  const b=CX.benchmarks, tiles=[];
  b.construction.forEach(c=>tiles.push([c.tier,"$"+c.psf+"/ft²","new construction, hard cost"]));
  b.rehab.forEach(c=>tiles.push([c.tier,"$"+c.psf+"/ft²","renovation"]));
  tiles.push(["Soft costs","+"+b.soft_cost_pct+"%","design / permits / GC / financing"]);
  tiles.push(["Seawall","$"+b.seawall_psf_lf[0]+"–"+b.seawall_psf_lf[1],"per linear foot, replacement"]);
  tiles.push(["New dock","$"+(b.dock_build[0]/1000)+"k–$"+(b.dock_build[1]/1000)+"k","typical residential"]);
  tiles.push(["Boat lift","~$"+b.boatlift_per_1000lb+"/1,000 lb","24k-lb ≈ $38k"]);
  const ins=b.insurance_annual;
  tiles.push(["Insurance — canal","$"+(ins.canal[0]/1000)+"–"+(ins.canal[1]/1000)+"k/yr","luxury waterfront carry"]);
  tiles.push(["Insurance — ocean","$"+(ins.oceanfront[0]/1000)+"–"+(ins.oceanfront[1]/1000)+"k/yr","direct oceanfront"]);
  $("#cxBench").innerHTML=tiles.map(t=>
    `<div class="geot"><div class="g-t">${t[0]}</div><div class="g-v tnum">${t[1]}</div>`
    +`<div class="g-n">${t[2]}</div></div>`).join("");
  $("#cxFacts").innerHTML=(CX.market_facts||[]).map(f=>
    `<li>${f.fact} <span class="basis">${f.src}</span></li>`).join("");
  $("#cxSrc").innerHTML="Sourced estimates — "+(CX.sources||[]).map(s=>
    `<a href="${s.url}" target="_blank" rel="noopener">${s.label.split(" — ")[0]}</a>`).join(" · ");
}
const CXCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>`},
  {k:"resale_psf",t:"Resale $/ft²",f:r=>`<span class="tnum">${usd(r.resale_psf)}</span> <span class="basis">${r.resale_basis}</span>`},
  {k:"replacement_psf_typ",t:"Replace $/ft²",f:r=>`<span class="tnum">${usd(r.replacement_psf_typ)}</span>`},
  {k:"land_ppsf",t:"Land $/ft²",f:r=>`<span class="tnum">${usd(r.land_ppsf)}</span> <span class="basis">${r.land_basis}</span>`},
  {k:"premium_to_replacement_pct",t:"vs Replacement",f:r=>r.premium_to_replacement_pct==null?"—":`<span class="tnum ${r.premium_to_replacement_pct>=0?'neg':'pos'}">${pctS(r.premium_to_replacement_pct)}</span>`},
  {k:"verdict",t:"Build vs buy",l:1,f:r=>{const v=r.verdict.split("—")[0].trim();
    const c=v.startsWith("Above")?"var(--neg)":v.startsWith("Below")?"var(--good)":"var(--ink-2)";
    return `<span style="color:${c};font-weight:600">${v}</span>`;}},
];
function cxTable(){
  const q=cxQ.toLowerCase();
  let rows=CX.neighborhoods.filter(r=>!q||r.neighborhood.toLowerCase().includes(q));
  rows=rows.slice().sort((a,b)=>(a.rank||999)-(b.rank||999));
  $("#cxTbl thead").innerHTML="<tr>"+CXCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#cxTbl tbody").innerHTML=rows.map(r=>"<tr>"+CXCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="6" style="color:var(--muted)">No match.</td></tr>`;
}
function cxInit(){$("#cxNote").textContent=CX.meta.note||""; cxBench(); cxTable();
  $("#cxSearch").addEventListener("input",e=>{cxQ=e.target.value;cxTable();});}

// ---------- leasing & yield ----------
let lxQ="";
const LXCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>`},
  {k:"est_monthly_rent",t:"Est. rent/mo",f:r=>`<span class="tnum">${usd(r.est_monthly_rent)}</span>`},
  {k:"rent_psf_yr",t:"Rent $/ft²/yr",f:r=>`<span class="tnum">${usd(r.rent_psf_yr)}</span>`},
  {k:"sale_ppsf",t:"Sale $/ft²",f:r=>`<span class="tnum">${usd(r.sale_ppsf)}</span>`},
  {k:"gross_yield_pct",t:"Gross yield",f:r=>r.gross_yield_pct==null?"—":`<span class="tnum" style="font-weight:700;color:${r.gross_yield_pct>=6?'var(--good)':r.gross_yield_pct<4?'var(--neg)':'var(--ink-2)'}">${r.gross_yield_pct}%</span>`},
  {k:"grm",t:"GRM",f:r=>`<span class="tnum">${r.grm||"—"}</span>`},
  {k:"verdict",t:"Sell vs hold",l:1,f:r=>`<span style="font-size:12px">${(r.verdict||"").split("—")[0].trim()}</span>`},
];
function lxTable(){
  const q=lxQ.toLowerCase();
  let rows=LX.neighborhoods.filter(r=>!q||r.neighborhood.toLowerCase().includes(q));
  rows=rows.slice().sort((a,b)=>(a.rank||999)-(b.rank||999));
  $("#lxTbl thead").innerHTML="<tr>"+LXCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#lxTbl tbody").innerHTML=rows.map(r=>"<tr>"+LXCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="7" style="color:var(--muted)">No match.</td></tr>`;
}
function lxInit(){
  $("#lxNote").textContent=LX.meta.note||"";
  $("#lxFacts").innerHTML=(LX.facts||[]).map(f=>`<li>${f}</li>`).join("");
  lxTable();
  $("#lxSearch").addEventListener("input",e=>{lxQ=e.target.value;lxTable();});
}

// ---------- seller prospects ----------
$("#slSummary").textContent=`· ${SL.meta.n_failed} failed-listing owners, ${SL.meta.n_overpriced_active} overpriced actives`;
let slType="failed", slQ="";
const SLCOLS=[
  {k:"address",t:"Address",l:1,f:r=>`<span class="nbh">${r.address}</span>`},
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="geo">${r.neighborhood}</span>`},
  {k:"status",t:"Status",l:1,f:r=>`<span class="basis">${r.status}</span>`},
  {k:"asked",t:"Asked",f:r=>`<span class="tnum">${usd(r.asked)}</span>`},
  {k:"over_pct",t:"% over",f:r=>`<span class="tnum neg">+${r.over_pct.toFixed(0)}%</span>`},
  {k:"suggested_list",t:"Suggested list",f:r=>`<span class="tnum" style="color:var(--good);font-weight:600">${usd(r.suggested_list)}</span>`},
  {k:"reduce_by",t:"Reduce by",f:r=>`<span class="tnum">${usd(r.reduce_by)}</span>`},
];
function slTable(){
  const q=slQ.toLowerCase();
  let rows=(SL[slType]||[]).filter(r=>!q||(r.neighborhood||"").toLowerCase().includes(q)||(r.address||"").toLowerCase().includes(q));
  rows=rows.slice(0,80);
  $("#slTbl thead").innerHTML="<tr>"+SLCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#slTbl tbody").innerHTML=rows.map(r=>"<tr>"+SLCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="7" style="color:var(--muted)">No prospects match.</td></tr>`;
}
$("#slSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  slType=b.dataset.t;[...$("#slSeg").children].forEach(x=>x.setAttribute("aria-pressed",x===b));slTable();});
$("#slSearch").addEventListener("input",e=>{slQ=e.target.value;slTable();});

// ---------- underpriced opportunities ----------
$("#upSummary").textContent=`· ${UP.meta.n} listings · $${Math.round(UP.meta.total_opportunity/1e6)}M total gap to supported value`;
let upBand="", upQ="";
const HT_BANDS=new Set(["$1M–$2M","$2M–$3M","$3M–$5M","$5M–$10M","$10M+"]);
function renderUnder(){
  const q=upQ.toLowerCase();
  let rows=UP.listings.filter(r=>{
    if(upBand==="ht")return HT_BANDS.has(r.band);
    if(upBand&&r.band!==upBand)return false; return true;});
  rows=rows.filter(r=>!q||(r.neighborhood||"").toLowerCase().includes(q)||(r.address||"").toLowerCase().includes(q));
  rows=rows.slice(0,50);
  $("#upList").innerHTML=rows.map(r=>
    `<div class="opp"><div class="opp-head">`
    +`<div><span class="opp-addr">${r.address}</span> <span class="geo">${r.neighborhood} · ${r.band} · ${r.ptype}</span></div>`
    +`<div class="opp-gap">${usd(r.opportunity)}<span> · ${r.under_pct.toFixed(0)}% under</span></div></div>`
    +`<div class="opp-sub">List ${usd(r.list_price)} · asking ${usd(r.ask_ppsf)}/ft² vs supported ${usd(r.supported_ppsf)}/ft² · <span class="opp-conf">${r.confidence}</span></div>`
    +`<ul class="opp-reasons">${r.reasons.map(x=>`<li>${x}</li>`).join("")}</ul></div>`).join("")
    ||`<div class="cap">No opportunities match.</div>`;
}
$("#upBand").addEventListener("change",e=>{upBand=e.target.value;renderUnder();});
$("#upSearch").addEventListener("input",e=>{upQ=e.target.value;renderUnder();});

// ---------- high-ticket band trends ----------
$("#htSummary").textContent=`· ${HT.meta.n_listings} listings ≥ $${(HT.meta.min_ticket/1e6).toFixed(0)}M, asking ${HT.meta.list_vs_suggested_pct>=0?"+":""}${HT.meta.list_vs_suggested_pct.toFixed(0)}% vs supported`;
function htBands(){
  $("#htBands").innerHTML=(HT.bands||[]).map(b=>{
    const gap=b.median_supported_ppsf?Math.round((b.median_ask_ppsf/b.median_supported_ppsf-1)*100):0;
    return `<div class="geot${gap>10?"":" wet"}"><div class="g-t">${b.band}</div>`
      +`<div class="g-v tnum">${usd(b.median_ask_ppsf)}<span style="font-size:12px;color:var(--muted)">/ft²</span></div>`
      +`<div class="g-n">vs $${b.median_supported_ppsf}/ft² supported (${gap>=0?"+":""}${gap}%) · `
      +`<span style="color:var(--over-fg)">${b.overpriced}▲</span> `
      +`<span style="color:var(--under-fg)">${b.underpriced}▼</span> · ${b.n} live</div></div>`;}).join("");
}
const HTCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>`},
  {k:"band",t:"Band",l:1,f:r=>`<span class="basis">${r.band}</span>`},
  {k:"n_sold",t:"Sold",f:r=>`<span class="tnum">${r.n_sold}</span>`},
  {k:"sold_ppsf",t:"Sold $/ft²",f:r=>`<span class="tnum">${usd(r.sold_ppsf)}</span>`},
  {k:"n_live",t:"Live",f:r=>`<span class="tnum">${r.n_live}</span>`},
  {k:"ask_ppsf",t:"Asking $/ft²",f:r=>`<span class="tnum">${usd(r.ask_ppsf)}</span>`},
  {k:"gap_pct",t:"Ask vs sold",f:r=>r.gap_pct==null?"—":`<span class="tnum ${r.gap_pct>0?'neg':'pos'}">${pctS(r.gap_pct)}</span>`},
  {k:"verdict",t:"Verdict",l:1,f:r=>vpill(vdictLive(r.gap_pct,r.n_sold))},
];
function htTable(){
  const q=state.htQ.toLowerCase();
  let rows=HT.band_neighborhood.filter(r=>!q||r.neighborhood.toLowerCase().includes(q));
  if(!q)rows=rows.slice(0,60);
  $("#htTbl thead").innerHTML="<tr>"+HTCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#htTbl tbody").innerHTML=rows.map(r=>"<tr>"+HTCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="8" style="color:var(--muted)">No multi-band data for that search.</td></tr>`;
}
$("#htSearch").addEventListener("input",e=>{state.htQ=e.target.value;htTable();});

// ---------- repricing ----------
const rover=100*(REP.meta.list_total/REP.meta.should_be_total-1);
$("#repriceSummary").textContent=`· ${REP.meta.n_repriceable.toLocaleString()} comp-backed listings asking ${rover>=0?"+":""}${rover.toFixed(0)}% vs model`;
$("#repInvNote").textContent=`(${REP.meta.n_live.toLocaleString()} live; "insufficient comps" = pre-construction/thin buildings)`;
const RNCOLS=[
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="nbh">${r.neighborhood}</span>`},
  {k:"n_live",t:"Live",f:r=>`<span class="tnum">${r.n_live}</span>`},
  {k:"ask_ppsf",t:"Now asking $/ft²",f:r=>`<span class="tnum">${usd(r.ask_ppsf)}</span>`},
  {k:"sold_ppsf",t:"Should be (sold)",f:r=>`<span class="tnum">${usd(r.sold_ppsf)}</span>`},
  {k:"model_ppsf",t:"Model $/ft²",f:r=>`<span class="tnum" style="color:var(--muted)">${usd(r.model_ppsf)}</span>`},
  {k:"gap_pct",t:"Ask vs should-be",f:r=>`<span class="tnum ${r.gap_pct>0?'neg':'pos'}">${pctS(r.gap_pct)}</span>`},
  {k:"verdict",t:"Verdict",l:1,f:r=>vpill(vdictLive(r.gap_pct,r.n_sold_comps))},
  {k:"n_sold_comps",t:"Comps",f:r=>`<span class="tnum">${r.n_sold_comps}</span>`},
];
function repData(){const d=state.repType==="condo"?REP.condos_by_nbhd:REP.by_nbhd;
  return d.filter(r=>(r.n_sold_comps||0)>=AS.minComps);}
function renderRepFlags(){
  const a=repData(),c={Overpriced:0,"Fairly priced":0,Underpriced:0};
  a.forEach(r=>{const v=vdictLive(r.gap_pct,r.n_sold_comps);if(v in c)c[v]++;});
  $("#repFlags").innerHTML=
    `<div class="flagbox fb-over"><div class="n tnum">${c.Overpriced}</div><div class="t">Overpriced</div></div>`
   +`<div class="flagbox fb-fair"><div class="n tnum">${c["Fairly priced"]}</div><div class="t">Fairly priced</div></div>`
   +`<div class="flagbox fb-under"><div class="n tnum">${c.Underpriced}</div><div class="t">Underpriced (value)</div></div>`;
}
function renderRepNbhd(){
  const rows=repData().slice().sort((a,b)=>b.gap_pct-a.gap_pct);
  $("#repNbhdTbl thead").innerHTML="<tr>"+RNCOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#repNbhdTbl tbody").innerHTML=rows.map(r=>"<tr>"+RNCOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("");
}
const RICOLS=[
  {k:"address",t:"Address",l:1,f:r=>`<span class="nbh">${r.address}</span>`},
  {k:"ptype",t:"Type",l:1,f:r=>`<span class="geo">${r.ptype}</span>`},
  {k:"neighborhood",t:"Neighborhood",l:1,f:r=>`<span class="geo">${r.neighborhood}</span>`},
  {k:"list_price",t:"Now listed",f:r=>`<span class="tnum">${usd(r.list_price)}</span>`},
  {k:"ask_ppsf",t:"Ask $/ft²",f:r=>`<span class="tnum">${usd(r.ask_ppsf)}</span>`},
  {k:"should_be_ppsf",t:"Should-be $/ft²",f:r=>`<span class="tnum">${usd(r.should_be_ppsf)}</span>`},
  {k:"should_be_price",t:"Should-be price",f:r=>`<span class="tnum">${usd(r.should_be_price)}</span>`},
  {k:"gap_pct",t:"Gap",f:r=>`<span class="tnum ${r.gap_pct>0?'neg':'pos'}">${pctS(r.gap_pct)}</span>`},
  {k:"verdict",t:"Verdict",l:1,f:r=>vpill(vdictLive(r.gap_pct,r.comps))},
];
function renderRepInv(){
  const q=state.repQ.toLowerCase();
  let rows=REP.inventory.filter(r=>state.repType!=="condo"||r.ptype==="Condo");
  rows=rows.filter(r=>!q||(r.address||"").toLowerCase().includes(q)||(r.neighborhood||"").toLowerCase().includes(q));
  rows=rows.slice(0,150);
  $("#repInvTbl thead").innerHTML="<tr>"+RICOLS.map(c=>`<th class="${c.l?'l':''}">${c.t}</th>`).join("")+"</tr>";
  $("#repInvTbl tbody").innerHTML=rows.map(r=>"<tr>"+RICOLS.map(c=>`<td class="${c.l?'l':''}">${c.f(r)}</td>`).join("")+"</tr>").join("")
    ||`<tr><td class="l" colspan="9" style="color:var(--muted)">No matches.</td></tr>`;
}
$("#repSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  state.repType=b.dataset.t;[...$("#repSeg").children].forEach(x=>x.setAttribute("aria-pressed",x===b));
  renderRepFlags();renderRepNbhd();renderRepInv();});
$("#repSearch").addEventListener("input",e=>{state.repQ=e.target.value;renderRepInv();});

function renderAll(){kpis();drivers();geostrip();lineChart();flags();barChart();renderTable();
  renderTime();movers();renderStreets();renderUW();renderRepFlags();renderRepNbhd();renderRepInv();
  htBands();htTable();absBands();absTable();slTable();renderUnder();
  landStrips();landTable();mfStrips();mfTable();
  renderProfile(state.sel || (filtered()[0]||NB[0]||{}).neighborhood);}
$("#basisSeg").addEventListener("click",e=>{const b=e.target.closest("button");if(!b)return;
  state.basis=b.dataset.b;[...$("#basisSeg").children].forEach(x=>x.setAttribute("aria-pressed",x===b));
  barChart();renderTable();});
$("#search").addEventListener("input",e=>{state.q=e.target.value;barChart();renderTable();});
$("#themeBtn").addEventListener("click",()=>{const cur=document.documentElement.getAttribute("data-theme");
  const dark=cur?cur==="dark":matchMedia("(prefers-color-scheme:dark)").matches;
  document.documentElement.setAttribute("data-theme",dark?"light":"dark");renderAll();});
matchMedia("(prefers-color-scheme:dark)").addEventListener("change",renderAll);
window.addEventListener("resize",()=>{clearTimeout(window._rz);window._rz=setTimeout(renderAll,150);});
renderAll();
scInit();
mktInit();
cxInit();
lxInit();

// ---------- live assumptions controller ----------
function asApply(){renderRepFlags();renderRepNbhd();renderRepInv();mfTable();htTable();
  absBands();absTable();landTable();}
function asSave(){try{localStorage.setItem("fl_assump",JSON.stringify(AS));}catch(e){}}
function asSync(){
  $("#asCut").value=AS.verdictCut; $("#asCutV").textContent="± "+AS.verdictCut+"%";
  $("#asMin").value=AS.minComps; $("#asMinV").textContent=AS.minComps;
  $("#asAbsS").value=AS.absorption.sellers; $("#asAbsB").value=AS.absorption.balanced;
  $("#asAbsY").value=AS.absorption.buyers;
  $("#asEcho").textContent=` verdict ±${AS.verdictCut}% · min ${AS.minComps} comps · absorption `
    +`${AS.absorption.sellers}/${AS.absorption.balanced}/${AS.absorption.buyers} mo`;}
function asInit(){
  asSync();
  $("#asCut").addEventListener("input",e=>{AS.verdictCut=+e.target.value;asSave();asSync();asApply();});
  $("#asMin").addEventListener("input",e=>{AS.minComps=+e.target.value;asSave();asSync();asApply();});
  const ab=(id,k)=>$(id).addEventListener("input",e=>{AS.absorption[k]=+e.target.value||0;asSave();asSync();asApply();});
  ab("#asAbsS","sellers");ab("#asAbsB","balanced");ab("#asAbsY","buyers");
  $("#asReset").addEventListener("click",()=>{AS={verdictCut:AS_SEED.verdictCut,
    minComps:AS_SEED.minComps,absorption:Object.assign({},AS_SEED.absorption)};asSave();asSync();asApply();});
  asApply();
}
asInit();

// ---------- section nav scrollspy ----------
(function(){
  const links=[...document.querySelectorAll("#secNav a")];
  const map={}; links.forEach(a=>{const el=document.querySelector(a.getAttribute("href"));
    if(el)map[a.getAttribute("href").slice(1)]=a;});
  const targets=Object.keys(map).map(id=>document.getElementById(id)).filter(Boolean);
  if(!("IntersectionObserver"in window)||!targets.length)return;
  const io=new IntersectionObserver(entries=>{
    entries.forEach(en=>{if(en.isIntersecting){
      links.forEach(a=>a.classList.remove("on"));
      const a=map[en.target.id]; if(a){a.classList.add("on");
        a.scrollIntoView({block:"nearest",inline:"nearest"});}}});
  },{rootMargin:"-60px 0px -70% 0px",threshold:0});
  targets.forEach(t=>io.observe(t));
})();
})();
</script>
"""


def build():
    inner = (INNER
             .replace("__MLS_JSON__", json.dumps(MLS, separators=(",", ":")))
             .replace("__REDFIN_JSON__", json.dumps(REDFIN, separators=(",", ":")))
             .replace("__TIME_JSON__", json.dumps(TIME, separators=(",", ":")))
             .replace("__STREET_JSON__", json.dumps(STREET, separators=(",", ":")))
             .replace("__REPRICE_JSON__", json.dumps(REPRICE, separators=(",", ":")))
             .replace("__HIGH_JSON__", json.dumps(HIGH, separators=(",", ":")))
             .replace("__UNDER_JSON__", json.dumps(UNDER, separators=(",", ":")))
             .replace("__ABSORB_JSON__", json.dumps(ABSORB, separators=(",", ":")))
             .replace("__SELLER_JSON__", json.dumps(SELLER, separators=(",", ":")))
             .replace("__LAND_JSON__", json.dumps(LAND, separators=(",", ":")))
             .replace("__INCOME_JSON__", json.dumps(INCOME, separators=(",", ":")))
             .replace("__ASSUMP_JSON__", json.dumps(ASSUMP, separators=(",", ":")))
             .replace("__MARKETING_JSON__", json.dumps(MARKETING, separators=(",", ":")))
             .replace("__BACKTEST_JSON__", json.dumps(BACKTEST, separators=(",", ":")))
             .replace("__CONTEXT_JSON__", json.dumps(CONTEXT, separators=(",", ":")))
             .replace("__LEASE_JSON__", json.dumps(LEASE, separators=(",", ":")))
             .replace("__SCEN_JSON__", json.dumps(SCEN, separators=(",", ":"))))
    standalone = (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
        "<title>Fort Lauderdale PPSF — Normalized Neighborhood Analysis</title>\n"
        "<style>html,body{margin:0;padding:0;background:#f2efe7}"
        "@media(prefers-color-scheme:dark){html,body{background:#0a141d}}"
        ":root[data-theme=\"dark\"] body{background:#0a141d}"
        ":root[data-theme=\"light\"] body{background:#f2efe7}</style>\n</head>\n<body>\n"
        + inner + "\n</body>\n</html>\n")
    with open(os.path.join(DASH, "index.html"), "w") as f:
        f.write(standalone)
    with open(os.path.join(DASH, "artifact.html"), "w") as f:
        f.write(inner)
    print(f"Wrote dashboard/index.html + artifact.html ({len(standalone)//1024} KB)")


if __name__ == "__main__":
    build()
