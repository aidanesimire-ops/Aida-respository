#!/usr/bin/env python3
"""
Self-contained interactive commercial deal dashboard.

Writes two files:
  * dashboard/index.html   — full standalone HTML document (repo / open locally)
  * dashboard/artifact.html — content-only (no <html>/<head>/<body>) for publishing as an Artifact

Because the MLS export has no income, every income figure is derived from ASSUMPTIONS the user
controls. This build makes the whole thing dynamic: editable per-type income assumptions, GLOBAL
financing controls, filters, a live "Answers" summary (deal pricing · returns · market · supply),
a full single-deal underwriting model, and a GOAL-SEEK solver that reverse-solves price / rent /
cap for a target cap rate, IRR, DSCR or cash-on-cash. Everything recomputes in the browser.
"""
from __future__ import annotations
import json
import math
import os

import pandas as pd

import cre_common as CRE
import cre_assumptions as A
import cre_scenario as SC

DASHDIR = os.path.join(CRE.ROOT, "dashboard")
os.makedirs(DASHDIR, exist_ok=True)


def _load(name):
    p = os.path.join(CRE.PROC, name)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


def main():
    cre = _load("cre_bundle.json")
    meta = cre["meta"]
    valued = pd.read_csv(os.path.join(CRE.PROC, "cre_all_valued.csv"))
    seg_b = _load("segments_bundle.json") or {}
    pros_b = _load("prospects_bundle.json") or {}
    master_b = _load("master_bundle.json") or {"submarkets": cre["submarkets"]}

    recs = valued[["mls", "address", "submarket", "asset_type", "status", "price", "sqft",
                   "units", "price_per_unit", "ppsf", "pred_ppsf", "ppsf_gap_pct", "year_built",
                   "price_band"]].copy()
    recs = recs.where(pd.notna(recs), None)
    listings = recs.to_dict(orient="records")

    df_all = CRE.load_clean()
    live_all = int(df_all["status"].isin(CRE.LIVE).sum())
    live_sale = int((df_all["status"].isin(CRE.LIVE) & df_all["deal_kind"].eq("Sale")).sum())
    live_shown = sum(1 for l in listings if l["status"] in ("Active", "Pending", "UnderContract"))

    DATA = {
        "meta": meta,
        "coverage": {"live_all": live_all, "live_sale": live_sale, "live_shown": live_shown},
        "assumptions": {"by_type": A.DEFAULTS, "finance": A.FINANCE},
        "submarkets": master_b["submarkets"],
        "types": cre["types"],
        "listings": listings,
        "segments": seg_b.get("by_type", []),
        "absorption": seg_b.get("absorption_by_submarket", []),
        "failure_type": pros_b.get("failure_rate_type", []),
        "market_rents": cre.get("market_rents", {}),
        "seed": SC.seed(),
        "asset_order": CRE.ASSET_ORDER,
    }
    def _clean(o):
        if isinstance(o, float):
            return None if (math.isnan(o) or math.isinf(o)) else o
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_clean(v) for v in o]
        return o

    data_json = json.dumps(_clean(DATA), allow_nan=False)
    script = _SCRIPT.replace("/*__DATA__*/", data_json)

    head = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Commercial Deal Dashboard — Fort Lauderdale</title>')
    with open(os.path.join(DASHDIR, "index.html"), "w") as f:
        f.write(head + _STYLE + "</head><body>" + _BODY + script + "</body></html>")
    with open(os.path.join(DASHDIR, "artifact.html"), "w") as f:
        f.write(_STYLE + _BODY + script)
    print(f"Dashboard -> dashboard/index.html + artifact.html "
          f"({os.path.getsize(os.path.join(DASHDIR, 'index.html'))//1024} KB)")


# --------------------------------------------------------------------------- #
_STYLE = r"""<style>
:root{
 --bg:#f5f4f0; --card:#fff; --ink:#1e2732; --muted:#69727e; --line:#e5e3db;
 --accent:#2f6f9f; --accent2:#245680; --accent-soft:#e9f1f8; --good:#3f7d5a; --bad:#b0473a;
 --warn:#c2703d; --yellow:#fff7d6; --yellow-line:#e0d6a2;
}
@media (prefers-color-scheme:dark){:root{
 --bg:#11151b; --card:#1a2028; --ink:#e7eaef; --muted:#9aa3af; --line:#2a323d;
 --accent:#6db0e0; --accent2:#8cc4ea; --accent-soft:#1d2a37; --good:#68b088; --bad:#e0796b;
 --warn:#e0a06a; --yellow:#2b2814; --yellow-line:#4c451e;}}
:root[data-theme=dark]{
 --bg:#11151b; --card:#1a2028; --ink:#e7eaef; --muted:#9aa3af; --line:#2a323d;
 --accent:#6db0e0; --accent2:#8cc4ea; --accent-soft:#1d2a37; --good:#68b088; --bad:#e0796b;
 --warn:#e0a06a; --yellow:#2b2814; --yellow-line:#4c451e;}
:root[data-theme=light]{
 --bg:#f5f4f0; --card:#fff; --ink:#1e2732; --muted:#69727e; --line:#e5e3db;
 --accent:#2f6f9f; --accent2:#245680; --accent-soft:#e9f1f8; --good:#3f7d5a; --bad:#b0473a;
 --warn:#c2703d; --yellow:#fff7d6; --yellow-line:#e0d6a2;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 -webkit-font-smoothing:antialiased}
.wrap{max-width:1220px;margin:0 auto;padding:0 20px 80px}
header{padding:26px 0 10px}
h1{font-size:27px;margin:0 0 6px;letter-spacing:-.01em}
h2{font-size:19px;margin:0 0 3px;letter-spacing:-.01em}
h3{font-size:12px;margin:0 0 8px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:700}
.sub{color:var(--muted);font-size:13px}
.banner{background:var(--accent-soft);border:1px solid var(--line);border-radius:11px;padding:12px 15px;margin:12px 0;font-size:13.5px}
nav{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:8px 0;margin-bottom:16px;display:flex;gap:5px;flex-wrap:wrap}
nav a{font-size:12.5px;text-decoration:none;color:var(--ink);padding:5px 11px;border-radius:8px;border:1px solid transparent}
nav a:hover{background:var(--accent-soft);border-color:var(--line)}
.card{background:var(--card);border:1px solid var(--line);border-radius:15px;padding:18px 18px 20px;margin:16px 0;box-shadow:0 1px 2px rgba(20,30,45,.04)}
.grid{display:grid;gap:14px}
.two{grid-template-columns:1fr 1fr}
.answers{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}
.tiles{grid-template-columns:repeat(auto-fit,minmax(146px,1fr))}
@media(max-width:760px){.two{grid-template-columns:1fr}}
.ans{background:linear-gradient(180deg,var(--accent-soft),transparent);border:1px solid var(--line);border-radius:12px;padding:13px 14px}
.ans .q{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700;margin-bottom:5px}
.ans .a{font-size:15px;line-height:1.35}
.ans .a b{font-size:20px;letter-spacing:-.01em}
.tile{background:var(--bg);border:1px solid var(--line);border-radius:11px;padding:12px 13px}
.tile .t{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:22px;font-weight:660;margin-top:3px;letter-spacing:-.01em}
.tile .s{font-size:11.5px;color:var(--muted);margin-top:2px}
.up{color:var(--good)}.down{color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:right;padding:7px 9px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:650;font-size:11px;text-transform:uppercase;letter-spacing:.03em}
thead th{position:sticky;top:45px;background:var(--card);cursor:default}
tbody tr:hover{background:var(--accent-soft)}
.tnum{font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:650}
.pill.u{background:color-mix(in srgb,var(--good) 20%,transparent);color:var(--good)}
.pill.o{background:color-mix(in srgb,var(--bad) 20%,transparent);color:var(--bad)}
.pill.f{background:var(--line);color:var(--muted)}
label{font-size:11px;color:var(--muted);display:flex;flex-direction:column;gap:3px}
input,select{font:inherit;font-size:13px;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:8px;padding:6px 8px}
input:focus,select:focus{outline:2px solid var(--accent);outline-offset:0}
input[type=number]{width:88px;text-align:right;background:var(--yellow);border-color:var(--yellow-line);font-variant-numeric:tabular-nums}
.asm input{width:74px}
.ctrl{display:flex;flex-wrap:wrap;gap:12px 14px;align-items:end}
.btn{cursor:pointer;background:var(--accent);color:#fff;border:none;border-radius:9px;padding:8px 15px;font-size:13px;font-weight:600}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.muted{color:var(--muted)}.small{font-size:12px}
.flex{display:flex;gap:9px;flex-wrap:wrap;align-items:center}
.chip{font-size:12px;padding:4px 10px;border:1px solid var(--line);border-radius:20px;cursor:pointer;background:var(--card);user-select:none}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.bar{height:7px;border-radius:5px;background:var(--accent);display:inline-block;vertical-align:middle;opacity:.55}
.solveOut{background:var(--accent-soft);border:1px solid var(--line);border-radius:11px;padding:14px 16px;margin-top:12px;font-size:15px}
.themeToggle{position:fixed;top:9px;right:12px;z-index:30;cursor:pointer;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:5px 10px;font-size:12px}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
.guide summary{cursor:pointer;font-weight:650;font-size:14px;list-style:none}
.guide summary::-webkit-details-marker{display:none}
.guide summary::before{content:"▸ ";color:var(--accent)}
.guide[open] summary::before{content:"▾ "}
.guide ul{margin:10px 0 0;padding-left:0;list-style:none;display:grid;gap:8px}
.guide li{padding-left:0}.guide b{color:var(--accent2)}
.conf{font-size:10px;padding:1px 6px;border-radius:10px;border:1px solid var(--line);color:var(--muted);margin-left:5px}
.conf.hi{color:var(--good);border-color:var(--good)}
.conf.lo{color:var(--warn);border-color:var(--warn)}
.sheet{border:2px solid var(--ink);border-radius:12px;padding:22px 24px;background:var(--card);max-width:820px}
.sheet .sh-h{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:2px solid var(--ink);padding-bottom:10px;margin-bottom:14px}
.sheet h3{font-size:22px;text-transform:none;letter-spacing:-.01em;color:var(--ink);margin:0}
.sheet .kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:14px 0}
.sheet .kpi{border:1px solid var(--line);border-radius:8px;padding:9px 10px}
.sheet .kpi .l{font-size:10px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted)}
.sheet .kpi .n{font-size:17px;font-weight:650;font-variant-numeric:tabular-nums}
.sheet .pitch{background:var(--accent-soft);border-radius:8px;padding:11px 13px;font-size:14px;margin:12px 0}
@media print{
 body{background:#fff}
 .themeToggle,nav,.banner,.guide,#answers,#assumptions,#financing,#overview,#inventory,
 #underwrite,#solver,#absorption,#prospects,header .sub,.wrap>.sub{display:none!important}
 #dealsheet{display:block!important;margin:0;border:none;box-shadow:none;padding:0}
 .sheet{border-color:#000;max-width:100%}
 .card{border:none;box-shadow:none;padding:0;margin:0}
}
</style>"""

_BODY = r"""<div class="themeToggle" onclick="toggleTheme()">◐ theme</div>
<div class="wrap">
<header>
 <h1>Commercial Deal Dashboard <span class="muted" style="font-weight:400;font-size:16px">— Fort Lauderdale</span></h1>
 <div class="sub" id="subline"></div>
</header>
<div class="banner" id="banner"></div>
<details class="guide card">
 <summary>How to use this for marketing &amp; deals</summary>
 <ul>
  <li><b>Find sellers to call</b> → <a href="#prospects">Prospects</a> + the failed-listing screen: motivated owners whose deal stalled, with the overpricing that likely killed it. Great cold-call list.</li>
  <li><b>Win a listing (seller pitch)</b> → load the property in <a href="#underwrite">Underwrite</a>, then <b>Print deal sheet</b> — a one-page "here's what the market says it's worth, and the price that sells" you can hand the owner.</li>
  <li><b>Pitch a buyer</b> → <a href="#inventory">Reprice inventory</a>, filter to <b>Underpriced</b>, open a deal in Underwrite and print the sheet: implied cap, value, and projected return on your assumptions.</li>
  <li><b>Price a deal / answer "what should I pay?"</b> → <a href="#solver">Goal-seek</a>: solve price for your target cap or IRR.</li>
  <li><b>Pick a market</b> → the <a href="#answers">Answers</a> band names the cheapest basis, highest yield, and tightest supply, live.</li>
  <li><b>Trust the numbers</b> → income figures use editable assumptions (rents anchored to real lease comps where the tag says "comps"); cells marked <span class="conf lo">Indicative</span> have few sales — verify before quoting.</li>
 </ul>
</details>
<nav>
 <a href="#answers">Answers</a><a href="#assumptions">Assumptions</a><a href="#financing">Financing</a>
 <a href="#overview">$/SqFt map</a><a href="#inventory">Reprice inventory</a>
 <a href="#underwrite">Underwrite</a><a href="#solver">Goal-seek</a>
 <a href="#absorption">Absorption</a><a href="#prospects">Prospects</a>
</nav>

<div class="card" id="answers">
 <h2>Answers <span class="muted small">— recomputed live from your assumptions &amp; financing below</span></h2>
 <div class="grid answers" id="ansGrid" style="margin-top:12px"></div>
</div>

<div class="card" id="assumptions">
 <h2>Income assumptions <span class="muted small">— the income the export doesn't give us. Edit any yellow cell; everything recomputes.</span></h2>
 <div class="sub" style="margin:6px 0 12px">Per asset class: market rent ($/SqFt/yr), vacancy, operating-expense ratio, market cap. Implied cap = NOI ÷ price on the type's median $/SqFt.</div>
 <div class="scroll"><table class="asm" id="asmTable"></table></div>
 <div class="flex" style="margin-top:10px">
  <button class="btn" onclick="useMarketRents()">Use market rents (from lease comps)</button>
  <button class="btn ghost" onclick="resetAll()">Reset to defaults</button>
  <span class="muted small" id="mktRentNote"></span>
 </div>
</div>

<div class="card" id="financing">
 <h2>Financing &amp; hold <span class="muted small">— global; drives every return below, the inventory IRR column, and the underwriting</span></h2>
 <div class="ctrl" style="margin-top:12px">
  <label>LTV %<input type="number" id="gLtv" step="5"></label>
  <label>Interest rate %<input type="number" id="gRate" step="0.125"></label>
  <label>Rate shift bps<input type="number" id="gShift" step="25"></label>
  <label>Amortization yrs<input type="number" id="gAmort" step="1"></label>
  <label>Exit cap Δ bps<input type="number" id="gExitDelta" step="5"></label>
  <label>Rent growth %<input type="number" id="gRg" step="0.5"></label>
  <label>Expense growth %<input type="number" id="gEg" step="0.5"></label>
  <label>Hold yrs<input type="number" id="gHold" step="1"></label>
  <label>Selling costs %<input type="number" id="gSell" step="0.5"></label>
  <label>Acquisition costs %<input type="number" id="gAcq" step="0.5"></label>
 </div>
</div>

<div class="card" id="overview">
 <h2>Normalized $/SqFt <span class="muted small">— factual; size / age / type / closed-vs-listed removed</span></h2>
 <div class="grid two" style="margin-top:12px">
  <div><h3>By submarket (MLS area)</h3><div class="scroll"><table id="subTable"></table></div></div>
  <div><h3>By asset type</h3><div class="scroll"><table id="typeTable"></table></div></div>
 </div>
</div>

<div class="card" id="inventory">
 <h2>Reprice live inventory</h2>
 <div class="sub" style="margin:6px 0 6px">Two lenses: <b>$/SqFt</b> vs comps and <b>income</b> (asking vs value at your assumed rents &amp; cap). IRR uses the global financing. Below value = higher implied cap = a buy.</div>
 <div class="small muted" id="invCoverage" style="margin-bottom:8px"></div>
 <div class="flex" style="margin-bottom:8px">
  <input type="text" id="invSearch" placeholder="search address…" style="width:180px" oninput="renderInventory()">
  <select id="invSub" onchange="renderInventory()"></select>
  <select id="invFlag" onchange="renderInventory()">
   <option value="All">All flags</option><option>Underpriced</option><option>Fair</option><option>Overpriced</option><option>Check</option></select>
 </div>
 <div class="flex" id="typeFilter" style="margin-bottom:10px"></div>
 <div class="scroll"><table id="invTable"></table></div>
</div>

<div class="card" id="underwrite">
 <h2>Underwrite a deal <span class="muted small">— pick a listing or type; NOI is built from the assumptions, returns from the global financing</span></h2>
 <div class="ctrl" style="margin:10px 0 4px">
  <label>Listing<select id="uPick"></select></label>
  <label>Asset type<select id="uType"></select></label>
  <label>Price ($)<input type="number" id="uPrice" step="25000"></label>
  <label>Size (SqFt)<input type="number" id="uSqft" step="500"></label>
  <label>Rent $/SqFt<input type="number" id="uRent" step="1"></label>
  <label>Vacancy %<input type="number" id="uVac" step="1"></label>
  <label>Opex % EGI<input type="number" id="uOpex" step="1"></label>
  <label>Market cap %<input type="number" id="uCap" step="0.1"></label>
  <label>Exit cap %<input type="number" id="uExit" step="0.1"></label>
 </div>
 <div class="grid tiles" id="uTiles" style="margin-top:12px"></div>
 <div class="grid two" style="margin-top:14px">
  <div><h3>Sensitivity — exit cap</h3><div class="scroll"><table id="uSensCap"></table></div></div>
  <div><h3>Sensitivity — rent $/SqFt</h3><div class="scroll"><table id="uSensRent"></table></div></div>
 </div>
 <div class="flex" style="margin-top:14px">
  <button class="btn" onclick="printSheet()">🖨 Print deal sheet (PDF)</button>
  <label class="small">for<select id="sheetAudience" onchange="renderDealSheet()"><option value="buyer">a buyer</option><option value="seller">the seller</option></select></label>
 </div>
</div>

<div class="card" id="dealsheet"><div class="sheet" id="sheetBody"></div></div>


<div class="card" id="solver">
 <h2>Goal-seek <span class="muted small">— reverse-solve one input to hit a target on the deal loaded above</span></h2>
 <div class="ctrl" style="margin-top:12px">
  <label>Solve for<select id="sVar">
   <option value="price">Purchase price</option><option value="rent">Rent $/SqFt</option>
   <option value="exitCap">Exit cap %</option><option value="ltv">LTV %</option>
   <option value="mcap">Market cap %</option></select></label>
  <label>so that<select id="sMetric">
   <option value="irr">Levered IRR %</option><option value="goin">Going-in cap %</option>
   <option value="dscr">DSCR ×</option><option value="coc">Year-1 cash-on-cash %</option>
   <option value="em">Equity multiple ×</option><option value="fair">Asking = value (fair)</option></select></label>
  <label>equals<input type="number" id="sTarget" step="0.5" value="15"></label>
  <button class="btn" onclick="runSolve()" style="align-self:end">Solve</button>
 </div>
 <div class="solveOut" id="sOut">Set a target and press <b>Solve</b>. It reverse-solves on the deal currently in the Underwrite card.</div>
</div>

<div class="card" id="absorption">
 <h2>Absorption &amp; supply</h2>
 <div class="sub" id="absNote" style="margin:6px 0 10px"></div>
 <div class="grid two">
  <div><h3>By submarket (months of supply)</h3><div class="scroll"><table id="absTable"></table></div></div>
  <div><h3>By asset type</h3><div class="scroll"><table id="segTable"></table></div></div>
 </div>
</div>

<div class="card" id="prospects">
 <h2>Prospecting — failure rate by asset type</h2>
 <div class="sub" style="margin:6px 0 10px">Share of listings that failed (expired / cancelled / withdrawn) vs sold — where deals stall.</div>
 <div class="scroll"><table id="failTable"></table></div>
</div>

<div class="sub" style="margin-top:20px">Built from user-provided BeachesMLS commercial exports. No income in source — income metrics are assumption-driven and tunable above. Screening intelligence, not appraisals.</div>
</div>"""

_SCRIPT = r"""<script id="DATA" type="application/json">/*__DATA__*/</script>
<script>
const D=JSON.parse(document.getElementById("DATA").textContent);
const $=s=>document.querySelector(s);
const usd=x=>{if(x==null||isNaN(x))return "—";const a=Math.abs(x);
 if(a>=1e9)return "$"+(x/1e9).toFixed(2)+"B";if(a>=1e6)return "$"+(x/1e6).toFixed(2)+"M";
 if(a>=1e3)return "$"+(x/1e3).toFixed(0)+"K";return "$"+x.toFixed(0);};
const pf=x=>x==null||isNaN(x)?"—":(x*100).toFixed(2)+"%";
const p1=x=>x==null||isNaN(x)?"—":(x*100).toFixed(1)+"%";
const sg=x=>x==null||isNaN(x)?"—":(x>=0?"+":"")+x.toFixed(1)+"%";
const LIVE=["Active","Pending","UnderContract"];
const isLive=l=>LIVE.includes(l.status);
const med=arr=>{const a=arr.filter(x=>x!=null&&!isNaN(x)).sort((p,q)=>p-q);return a.length?a[Math.floor(a.length/2)]:NaN;};

let ASM={};
function readFin(){return{ltv:+$("#gLtv").value/100,rate:+$("#gRate").value/100,shift:+$("#gShift").value,
 amort:+$("#gAmort").value,exitDelta:+$("#gExitDelta").value,rg:+$("#gRg").value/100,eg:+$("#gEg").value/100,
 hold:+$("#gHold").value,sell:+$("#gSell").value/100,acq:+$("#gAcq").value/100};}

function derive(price,sqft,type){const a=ASM[type]||ASM["Commercial (other)"];
 const egi=sqft*a.rent_psf*(1-a.vacancy),noi=egi*(1-a.opex_ratio);
 return{noi,impliedCap:price?noi/price:NaN,value:a.cap_rate?noi/a.cap_rate:NaN,
  gap:a.cap_rate?price/(noi/a.cap_rate)-1:NaN,marketCap:a.cap_rate};}
// an implied cap outside a plausible band almost always means the listing's SqFt (or its
// assumed rent) is off — flag it "Check" rather than calling it a screaming buy.
const suspect=d=>!(d.impliedCap>0.005&&d.impliedCap<=0.15);

function irr(cfs){const npv=r=>cfs.reduce((s,c,i)=>s+c/Math.pow(1+r,i),0);
 if(cfs.every(c=>c>=0)||cfs.every(c=>c<=0))return NaN;
 let a=-0.95,b=1,g=0;while(npv(a)*npv(b)>0&&g<200){b+=0.5;g++;}if(npv(a)*npv(b)>0)return NaN;
 for(let i=0;i<200;i++){const m=(a+b)/2,fm=npv(m);if(Math.abs(fm)<1e-8)return m;if(npv(a)*fm<0)b=m;else a=m;}return(a+b)/2;}
function scen(o){
 const egi0=o.sqft*o.rent*(1-o.vac),exp0=egi0*o.opex,noi0=egi0-exp0;
 const goin=o.price?noi0/o.price:NaN,effr=o.rate+o.shift/10000,loan=o.price*o.ltv;
 const equity=o.price*(1-o.ltv)+o.price*o.acq,m=effr/12,n=o.amort*12;
 const pay=m>0?loan*m/(1-Math.pow(1+m,-n)):loan/n,ads=pay*12;
 const dscr=ads?noi0/ads:NaN,dy=loan?noi0/loan:NaN,hold=Math.round(o.hold),noit=[];
 for(let t=1;t<=hold;t++)noit.push(egi0*Math.pow(1+o.rg,t)-exp0*Math.pow(1+o.eg,t));
 const exitNoi=noit.length?noit[noit.length-1]:noi0,exitVal=o.exitCap>0?exitNoi/o.exitCap:NaN,k=hold*12;
 const rem=m>0?loan*(Math.pow(1+m,n)-Math.pow(1+m,k))/(Math.pow(1+m,n)-1):loan*(1-k/n);
 const net=exitVal*(1-o.sell)-rem,cfs=[-equity];
 noit.forEach((nc,i)=>{let cf=nc-ads;if(i===hold-1)cf+=net;cfs.push(cf);});
 const li=irr(cfs),dist=cfs.slice(1).reduce((s,c)=>s+c,0),em=equity?dist/equity:NaN;
 const coc1=equity&&noit.length?(noit[0]-ads)/equity:NaN;
 return{noi0,goin,loan,equity,ads,dscr,dy,exitNoi,exitVal,net,li,em,coc1,hold};}
function listingScen(l){const a=ASM[l.asset_type]||ASM["Commercial (other)"],f=readFin();
 const o={price:l.price,sqft:l.sqft,rent:a.rent_psf,vac:a.vacancy,opex:a.opex_ratio,
  exitCap:a.cap_rate+f.exitDelta/10000,ltv:f.ltv,rate:f.rate,shift:f.shift,amort:f.amort,
  rg:f.rg,eg:f.eg,hold:f.hold,sell:f.sell,acq:f.acq};return scen(o);}

// ---------- Answers ----------
function renderAnswers(){
 const subs=D.submarkets.slice().sort((a,b)=>b.norm_ppsf-a.norm_ppsf);
 const cheap=subs[subs.length-1],rich=subs[0];
 const ty=D.types.map(t=>{const a=ASM[t.asset_type];
  return{...t,ic:t.median_ppsf?a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio)/t.median_ppsf:NaN};})
  .filter(t=>t.ic>0&&t.ic<=0.15);
 const bestYield=ty.slice().sort((a,b)=>b.ic-a.ic)[0];
 const live=D.listings.filter(isLive).map(l=>({l,d:derive(l.price,l.sqft,l.asset_type),s:listingScen(l)}));
 const liveP=live.filter(x=>!suspect(x.d));
 const under=liveP.filter(x=>x.d.gap<-0.10),over=liveP.filter(x=>x.d.gap>0.10);
 const topU=under.slice().sort((a,b)=>a.d.gap-b.d.gap)[0];
 const irrMed=med(liveP.map(x=>x.s.li)),cocMed=med(liveP.map(x=>x.s.coc1)),dscrMed=med(liveP.map(x=>x.s.dscr));
 const abs=(D.absorption||[]).filter(r=>r.months_supply!=null).sort((a,b)=>a.months_supply-b.months_supply);
 const tight=abs[0],soft=abs[abs.length-1];
 const askMed=med(live.map(x=>x.l.ppsf));
 const card=(q,a)=>`<div class="ans"><div class="q">${q}</div><div class="a">${a}</div></div>`;
 $("#ansGrid").innerHTML=[
  card("Deal pricing — what's mispriced now",
    `<b class="up">${under.length}</b> underpriced · <b class="down">${over.length}</b> overpriced of ${live.length} live.`+
    (topU?`<br><span class="muted small">Most underpriced: ${(topU.l.address||topU.l.mls).slice(0,30)} — ${sg(topU.d.gap*100)} vs value (${pf(topU.d.impliedCap)} implied cap).</span>`:"")),
  card("Returns — the median for-sale deal",
    `<b class="${irrMed>0.1?'up':'down'}">${p1(irrMed)}</b> levered IRR<br>`+
    `<span class="muted small">${p1(cocMed)} Y1 cash-on-cash · ${isNaN(dscrMed)?'—':dscrMed.toFixed(2)}× DSCR · at ${$("#gLtv").value}% LTV / ${$("#gRate").value}% / ${$("#gHold").value}yr.</span>`),
  card("Market — basis &amp; yield",
    `Cheapest: <b>${cheap.submarket}</b> ${usd(cheap.norm_ppsf)}/SqFt · priciest ${rich.submarket} ${usd(rich.norm_ppsf)}.<br>`+
    `<span class="muted small">Highest implied yield: ${bestYield?bestYield.asset_type:'—'} at ${bestYield?pf(bestYield.ic):'—'} (your assumptions).</span>`),
  card("Supply — where it's tight",
    tight?`Tightest: <b>${tight.submarket}</b> ${tight.months_supply.toFixed(0)} mo<br>`+
    `<span class="muted small">Softest: ${soft.submarket} ${soft.months_supply.toFixed(0)} mo · median asking ${usd(askMed)}/SqFt.</span>`:"—"),
 ].join("");
}

// ---------- assumptions (built once; only derived cell updates on edit) ----------
function renderAsm(){
 let h="<thead><tr><th>Asset type</th><th>Median $/SqFt</th><th>#</th><th>Rent $/SqFt</th>"+
  "<th>Mkt rent (comps)</th><th>Vacancy %</th><th>Opex %</th><th>Market cap %</th><th>Implied cap*</th></tr></thead><tbody>";
 D.asset_order.filter(t=>ASM[t]).forEach(t=>{const a=ASM[t];const row=D.types.find(x=>x.asset_type===t)||{};
  const mp=row.median_ppsf||0,ic=mp?a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio)/mp:NaN;
  const mr=D.market_rents[t];
  h+=`<tr><td>${t}</td><td class="tnum">${mp?usd(mp):"—"}</td><td class="tnum">${row.n||"—"}</td>`+
   `<td><input type="number" step="1" value="${a.rent_psf}" oninput="setAsm('${t}','rent_psf',this.value,1)"></td>`+
   `<td class="tnum small ${mr?'up':'muted'}">${mr?('$'+mr.rate+' · n='+mr.n):'—'}</td>`+
   `<td><input type="number" step="1" value="${(a.vacancy*100).toFixed(0)}" oninput="setAsm('${t}','vacancy',this.value,0.01)"></td>`+
   `<td><input type="number" step="1" value="${(a.opex_ratio*100).toFixed(0)}" oninput="setAsm('${t}','opex_ratio',this.value,0.01)"></td>`+
   `<td><input type="number" step="0.05" value="${(a.cap_rate*100).toFixed(2)}" oninput="setAsm('${t}','cap_rate',this.value,0.01)"></td>`+
   `<td class="tnum" id="ic-${t.replace(/\W/g,'')}">${pf(ic)}</td></tr>`;});
 $("#asmTable").innerHTML=h+"</tbody>";}
function useMarketRents(){let n=0;Object.keys(D.market_rents||{}).forEach(t=>{if(ASM[t]){ASM[t].rent_psf=D.market_rents[t].rate;n++;}});
 renderAsm();recompute();$("#mktRentNote").textContent=`Applied lease-comp rents to ${n} asset types; the rest keep your assumption (no lease comps).`;}
const confBadge=c=>c?`<span class="conf ${c==='High'?'hi':c==='Indicative'?'lo':''}">${c}</span>`:"";
function setAsm(t,k,val,mult){ASM[t][k]=parseFloat(val)*mult||0;
 const row=D.types.find(x=>x.asset_type===t)||{},a=ASM[t],mp=row.median_ppsf||0;
 const ic=mp?a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio)/mp:NaN;
 const cell=$("#ic-"+t.replace(/\W/g,''));if(cell)cell.textContent=pf(ic);
 recompute();}

// ---------- overview ----------
function renderSub(){const s=D.submarkets.slice().sort((a,b)=>b.norm_ppsf-a.norm_ppsf),mx=Math.max(...s.map(x=>x.norm_ppsf));
 let h="<thead><tr><th>Submarket</th><th>Norm $/SqFt</th><th>vs city</th><th>Median price</th><th>n</th><th>Top type</th></tr></thead><tbody>";
 s.forEach(r=>{h+=`<tr><td>${r.submarket} ${confBadge(r.confidence)}</td><td class="tnum">${usd(r.norm_ppsf)} <span class="bar" style="width:${38*r.norm_ppsf/mx}px"></span></td>`+
  `<td class="tnum ${r.vs_city_pct>=0?'up':'down'}">${sg(r.vs_city_pct)}</td><td class="tnum">${usd(r.median_price)}</td>`+
  `<td class="tnum">${r.n}</td><td class="small">${r.top_asset||"—"}</td></tr>`;});
 $("#subTable").innerHTML=h+"</tbody>";}
function renderTypes(){let h="<thead><tr><th>Asset type</th><th>Median $/SqFt</th><th>n</th><th>Rent</th><th>Implied cap</th><th>Market cap</th></tr></thead><tbody>";
 D.asset_order.filter(t=>D.types.find(x=>x.asset_type===t)).forEach(t=>{const r=D.types.find(x=>x.asset_type===t),a=ASM[t];
  const ic=r.median_ppsf?a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio)/r.median_ppsf:NaN;
  h+=`<tr><td>${t} ${confBadge(r.confidence)}</td><td class="tnum">${usd(r.median_ppsf)}</td><td class="tnum">${r.n}</td>`+
   `<td class="tnum">$${a.rent_psf}</td><td class="tnum ${ic>a.cap_rate?'up':'down'}">${pf(ic)}</td><td class="tnum">${pf(a.cap_rate)}</td></tr>`;});
 $("#typeTable").innerHTML=h+"</tbody>";}

// ---------- inventory ----------
let invFilter="All",invSort={k:"gap",dir:1};
function renderTypeFilter(){const types=["All",...D.asset_order.filter(t=>D.listings.some(l=>l.asset_type===t&&isLive(l)))];
 $("#typeFilter").innerHTML=types.map(t=>`<span class="chip ${t===invFilter?'on':''}" onclick="invFilter='${t}';renderTypeFilter();renderInventory()">${t}</span>`).join("");}
function fillSubFilter(){const subs=[...new Set(D.listings.filter(isLive).map(l=>l.submarket))].sort();
 $("#invSub").innerHTML='<option value="All">All areas</option>'+subs.map(s=>`<option>${s}</option>`).join("");}
function renderInventory(){
 const q=($("#invSearch").value||"").toLowerCase(),subf=$("#invSub").value,flagf=$("#invFlag").value;
 let rows=D.listings.filter(isLive).filter(l=>invFilter==="All"||l.asset_type===invFilter)
  .filter(l=>subf==="All"||l.submarket===subf)
  .filter(l=>!q||((l.address||"")+l.mls).toLowerCase().includes(q))
  .map(l=>{const d=derive(l.price,l.sqft,l.asset_type),s=listingScen(l);
   return{...l,...d,income_gap:d.gap*100,irr:s.li,
    flag:suspect(d)?"Check":d.gap<-0.10?"Underpriced":d.gap>0.10?"Overpriced":"Fair"};})
  .filter(r=>flagf==="All"||r.flag===flagf);
 const k=invSort.k;rows.sort((a,b)=>((a[k]==null||isNaN(a[k])?1e9:a[k])-(b[k]==null||isNaN(b[k])?1e9:b[k]))*invSort.dir);
 const fl=f=>f==="Underpriced"?'<span class="pill u">Under</span>':f==="Overpriced"?'<span class="pill o">Over</span>':f==="Check"?'<span class="pill f" title="implied cap outside a plausible band — verify SqFt / rent">Check</span>':'<span class="pill f">Fair</span>';
 const th=(k,l)=>`<th style="cursor:pointer" onclick="sortInv('${k}')">${l}</th>`;
 let h="<thead><tr>"+th("address","Address")+th("asset_type","Type")+th("submarket","Area")+th("price","Asking")+
  th("ppsf","$/SqFt")+th("ppsf_gap_pct","vs comp")+th("impliedCap","Impl cap")+th("marketCap","Mkt cap")+
  th("value","Value")+th("income_gap","Gap")+th("irr","IRR*")+"<th>Flag</th></tr></thead><tbody>";
 rows.slice(0,140).forEach(r=>{h+=`<tr><td title="${r.address||''}">${(r.address||r.mls).slice(0,34)}</td><td class="small">${r.asset_type}</td>`+
  `<td class="small">${r.submarket}</td><td class="tnum">${usd(r.price)}</td><td class="tnum">${usd(r.ppsf)}</td>`+
  `<td class="tnum ${r.ppsf_gap_pct<0?'up':'down'}">${sg(r.ppsf_gap_pct)}</td>`+
  `<td class="tnum ${r.impliedCap>r.marketCap?'up':'down'}">${pf(r.impliedCap)}</td><td class="tnum">${pf(r.marketCap)}</td>`+
  `<td class="tnum">${usd(r.value)}</td><td class="tnum ${r.income_gap<0?'up':'down'}">${sg(r.income_gap)}</td>`+
  `<td class="tnum ${r.irr>0.1?'up':r.irr<0?'down':''}">${p1(r.irr)}</td><td>${fl(r.flag)}</td></tr>`;});
 $("#invTable").innerHTML=h+"</tbody>"+(rows.length>140?`<caption class="muted small" style="caption-side:bottom;text-align:left;padding-top:6px">showing 140 of ${rows.length}</caption>`:"");}
function sortInv(k){invSort.dir=(invSort.k===k?-invSort.dir:1);invSort.k=k;renderInventory();}

// ---------- underwrite ----------
function readScen(){const f=readFin();return{price:+$("#uPrice").value,sqft:+$("#uSqft").value,rent:+$("#uRent").value,
 vac:+$("#uVac").value/100,opex:+$("#uOpex").value/100,mcap:+$("#uCap").value/100,exitCap:+$("#uExit").value/100,
 ltv:f.ltv,rate:f.rate,shift:f.shift,amort:f.amort,rg:f.rg,eg:f.eg,hold:f.hold,sell:f.sell,acq:f.acq};}
function renderUnderwrite(){const o=readScen(),v=scen(o),value=o.mcap?v.noi0/o.mcap:NaN,gap=value?o.price/value-1:NaN;
 const tile=(t,val,s,cls)=>`<div class="tile"><div class="t">${t}</div><div class="v ${cls||''}">${val}</div><div class="s">${s||''}</div></div>`;
 $("#uTiles").innerHTML=[
  tile("Derived NOI",usd(v.noi0),`$${(v.noi0/o.sqft).toFixed(1)}/sf`),
  tile("Going-in cap",pf(v.goin),`mkt ${pf(o.mcap)}`,v.goin>o.mcap?'up':'down'),
  tile("Value @ mkt cap",usd(value),`ask ${sg(gap*100)}`,gap<0?'up':'down'),
  tile("DSCR",v.dscr.toFixed(2)+"×",`${$("#gLtv").value}% LTV @ ${$("#gRate").value}%`,v.dscr>=1.25?'up':'down'),
  tile("Debt yield",p1(v.dy),`loan ${usd(v.loan)}`),
  tile("Year-1 cash-on-cash",p1(v.coc1),`equity ${usd(v.equity)}`,v.coc1>0?'up':'down'),
  tile(v.hold+"-yr levered IRR",p1(v.li),`exit ${$("#uExit").value}% cap`,v.li>0.1?'up':v.li<0?'down':''),
  tile("Equity multiple",v.em.toFixed(2)+"×",`net sale ${usd(v.net)}`,v.em>1?'up':'down'),
 ].join("");
 let h="<thead><tr><th>Exit cap</th><th>IRR</th><th>Equity mult</th><th>Exit value</th></tr></thead><tbody>";
 [-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1].forEach(dd=>{const ec=o.exitCap+dd/100,vv=scen({...o,exitCap:ec}),hl=Math.abs(dd)<1e-9?' style="background:var(--accent-soft)"':'';
  h+=`<tr${hl}><td class="tnum">${(ec*100).toFixed(2)}%</td><td class="tnum ${vv.li>0?'up':'down'}">${p1(vv.li)}</td><td class="tnum">${vv.em.toFixed(2)}×</td><td class="tnum">${usd(vv.exitVal)}</td></tr>`;});
 $("#uSensCap").innerHTML=h+"</tbody>";
 let h2="<thead><tr><th>Rent $/SqFt</th><th>NOI</th><th>Going-in cap</th><th>IRR</th></tr></thead><tbody>";
 [-4,-2,-1,0,1,2,4].forEach(dr=>{const rr=Math.max(1,o.rent+dr),vv=scen({...o,rent:rr}),hl=dr===0?' style="background:var(--accent-soft)"':'';
  h2+=`<tr${hl}><td class="tnum">$${rr.toFixed(0)}</td><td class="tnum">${usd(vv.noi0)}</td><td class="tnum">${pf(vv.goin)}</td><td class="tnum ${vv.li>0?'up':'down'}">${p1(vv.li)}</td></tr>`;});
 $("#uSensRent").innerHTML=h2+"</tbody>";}
function seedType(t){const a=ASM[t]||ASM["Commercial (other)"],f=readFin();$("#uRent").value=a.rent_psf;
 $("#uVac").value=(a.vacancy*100).toFixed(0);$("#uOpex").value=(a.opex_ratio*100).toFixed(0);
 $("#uCap").value=(a.cap_rate*100).toFixed(2);$("#uExit").value=((a.cap_rate+f.exitDelta/10000)*100).toFixed(2);}

// ---------- goal-seek ----------
function metricOf(o,name){const v=scen(o);
 if(name==="irr")return v.li;if(name==="goin")return v.goin;if(name==="dscr")return v.dscr;
 if(name==="coc")return v.coc1;if(name==="em")return v.em;
 if(name==="fair"){const val=o.mcap?v.noi0/o.mcap:NaN;return val?o.price/val-1:NaN;}return NaN;}
function solve(varName,metric,target){
 const base=readScen();
 const rng={price:[50000,150e6],rent:[1,400],exitCap:[0.02,0.20],ltv:[0,0.90],mcap:[0.02,0.20]}[varName];
 const set=(x)=>({...base,[varName]:x});
 const f=x=>{const m=metricOf(set(x),metric);return m-target;};
 const N=160,lo=rng[0],hi=rng[1];let prev=lo,pf0=f(lo),root=null;
 for(let i=1;i<=N;i++){const x=lo+(hi-lo)*i/N,fx=f(x);
  if(pf0!=null&&!isNaN(pf0)&&!isNaN(fx)&&pf0*fx<=0){let a=prev,b=x;
   for(let j=0;j<80;j++){const mid=(a+b)/2,fm=f(mid);if(Math.abs(fm)<1e-7){root=mid;break;}if(f(a)*fm<0)b=mid;else a=mid;root=(a+b)/2;}break;}
  prev=x;pf0=fx;}
 return root;}
function runSolve(){const varName=$("#sVar").value,metric=$("#sMetric").value;
 let target=+$("#sTarget").value;
 const asPct=["irr","goin","coc"].includes(metric);if(metric==="fair")target=0;else if(asPct)target/=100;
 const x=solve(varName,metric,target);
 const unit={price:v=>usd(v),rent:v=>"$"+v.toFixed(1)+"/SqFt",exitCap:v=>(v*100).toFixed(2)+"%",ltv:v=>(v*100).toFixed(1)+"%",mcap:v=>(v*100).toFixed(2)+"%"}[varName];
 const vlab={price:"Purchase price",rent:"Rent $/SqFt",exitCap:"Exit cap",ltv:"LTV",mcap:"Market cap"}[varName];
 const mlab={irr:"levered IRR",goin:"going-in cap",dscr:"DSCR",coc:"Y1 cash-on-cash",em:"equity multiple",fair:"asking = value"}[metric];
 const tlab=metric==="fair"?"":(asPct?(+$("#sTarget").value)+"%":(+$("#sTarget").value)+(metric==="dscr"||metric==="em"?"×":""));
 if(x==null){$("#sOut").innerHTML=`No solution in range — <b>${vlab}</b> can't reach ${mlab} ${tlab} for this deal. Try a different variable or loosen the target.`;return;}
 const o2={...readScen(),[varName]:x},v=scen(o2),value=o2.mcap?v.noi0/o2.mcap:NaN;
 $("#sOut").innerHTML=`To hit <b>${mlab} ${tlab}</b>, set <b>${vlab} = ${unit(x)}</b>.`+
  `<div class="muted small" style="margin-top:6px">Then: going-in cap ${pf(v.goin)} · DSCR ${v.dscr.toFixed(2)}× · Y1 CoC ${p1(v.coc1)} · ${v.hold}-yr IRR ${p1(v.li)} · EM ${v.em.toFixed(2)}× · value ${usd(value)}.</div>`;}

// ---------- deal sheet (printable, marketing) ----------
let curListing=null;
function nearestComps(sub,type,sqft){
 let pool=D.listings.filter(l=>l.status==="Sold"&&l.submarket===sub);
 if(pool.length<3)pool=D.listings.filter(l=>l.status==="Sold"&&l.asset_type===type);
 return pool.map(l=>({...l,d:Math.abs((l.sqft||0)-(sqft||0))})).sort((a,b)=>a.d-b.d).slice(0,3);}
function renderDealSheet(){
 const o=readScen(),v=scen(o),value=o.mcap?v.noi0/o.mcap:NaN,gap=value?o.price/value-1:NaN;
 const l=curListing,type=$("#uType").value,aud=$("#sheetAudience").value;
 const addr=l?(l.address||l.mls):"Custom deal",sub=l?l.submarket:"—";
 const units=l&&l.units?l.units:null,ppu=units?o.price/units:null;
 let date="";try{date=new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"});}catch(e){}
 const kpi=(l,n)=>`<div class="kpi"><div class="l">${l}</div><div class="n">${n}</div></div>`;
 let pitch;
 if(aud==="seller"){
  pitch=gap>0.05?`Comparable buildings support about <b>${usd(value)}</b> at market rents (a ${pf(o.mcap)} cap). The current ask is ${sg(gap*100)} above that — pricing nearer ${usd(value)} typically clears faster.`
   :gap<-0.05?`The market supports roughly <b>${usd(value)}</b> at a ${pf(o.mcap)} cap — above where this is positioned. There may be room to raise the ask.`
   :`Priced in line with the market — about <b>${usd(value)}</b> at a ${pf(o.mcap)} cap.`;
 }else{
  pitch=gap<-0.08?`<b>Underpriced.</b> At market rents this underwrites to a ${pf(v.goin)} going-in cap and a ${p1(v.li)} ${v.hold}-yr levered IRR — roughly ${sg(gap*100)} below its ${usd(value)} value. Acquisition candidate.`
   :gap>0.08?`Priced <b>above</b> value (${usd(value)}) on these assumptions — build negotiation room into any offer; it only pencils to ${p1(v.li)} IRR if rents and cap hold.`
   :`Priced near value (${usd(value)}); underwrites to a ${pf(v.goin)} cap and ${p1(v.li)} IRR at ${$("#gLtv").value}% LTV.`;
 }
 const comps=l?nearestComps(sub,type,o.sqft):[];
 const compRows=comps.map(c=>`<tr><td>${(c.address||c.mls).slice(0,30)}</td><td class="tnum">${(c.sqft||0).toLocaleString()}</td><td class="tnum">${usd(c.price)}</td><td class="tnum">${usd(c.ppsf)}</td></tr>`).join("");
 $("#sheetBody").innerHTML=`
  <div class="sh-h"><div><h3>${addr}</h3><div class="muted small">${type} · ${sub} · ${l?l.status:"custom"}</div></div>
   <div class="muted small" style="text-align:right">Deal sheet<br>${date}</div></div>
  <div class="kpis">
   ${kpi("Price",usd(o.price))}${kpi("$/SqFt",usd(o.price/o.sqft))}${kpi("Size",Math.round(o.sqft).toLocaleString()+" SqFt")}
   ${units?kpi("Units / $per unit",units+" · "+usd(ppu)):kpi("Year built",l&&l.year_built?l.year_built:"—")}
   ${kpi("NOI (assumed)",usd(v.noi0))}${kpi("Going-in cap",pf(v.goin))}${kpi("Value @ mkt cap",usd(value))}${kpi("Ask vs value",sg(gap*100))}
  </div>
  <div class="pitch">${pitch}</div>
  <div class="kpis" style="grid-template-columns:repeat(4,1fr)">
   ${kpi("Financing",$("#gLtv").value+"% LTV @ "+$("#gRate").value+"%")}${kpi("DSCR",v.dscr.toFixed(2)+"×")}
   ${kpi("Yr-1 cash-on-cash",p1(v.coc1))}${kpi(v.hold+"-yr levered IRR",p1(v.li))}
  </div>
  ${comps.length?`<h3 style="font-size:12px;text-transform:uppercase;color:var(--muted);margin:14px 0 6px">Nearest closed comps</h3>
   <table><thead><tr><th>Address</th><th>SqFt</th><th>Price</th><th>$/SqFt</th></tr></thead><tbody>${compRows}</tbody></table>`:""}
  <div class="muted small" style="margin-top:14px">Income figures are assumption-based (rents ${D.market_rents[type]?'anchored to lease comps':'assumed'}); verify rent roll &amp; T-12 before relying on them. Not an appraisal.</div>`;}
function printSheet(){renderDealSheet();window.print();}

// ---------- static tables ----------
function renderAbs(){$("#absNote").textContent=window.__absnote||"Months of supply = live ÷ (closed per month); closed assumed to span a fixed window (no dates in export).";
 let h="<thead><tr><th>Submarket</th><th>Mo supply</th><th>Live</th><th>Sold</th><th>Failed</th></tr></thead><tbody>";
 (D.absorption||[]).forEach(r=>{const ms=r.months_supply;h+=`<tr><td>${r.submarket}</td><td class="tnum ${ms<12?'up':ms>30?'down':''}">${ms==null?"—":ms.toFixed(1)}</td>`+
  `<td class="tnum">${r.n_live}</td><td class="tnum">${r.n_sold}</td><td class="tnum">${r.n_failed}</td></tr>`;});$("#absTable").innerHTML=h+"</tbody>";
 let h2="<thead><tr><th>Asset type</th><th>n</th><th>Median $/SqFt</th><th>Live</th><th>Sold</th><th>Mo supply</th></tr></thead><tbody>";
 (D.segments||[]).forEach(r=>{h2+=`<tr><td>${r.asset_type}</td><td class="tnum">${r.n}</td><td class="tnum">${usd(r.median_ppsf)}</td>`+
  `<td class="tnum">${r.n_live}</td><td class="tnum">${r.n_sold}</td><td class="tnum">${r.months_supply==null?"—":r.months_supply.toFixed(1)}</td></tr>`;});$("#segTable").innerHTML=h2+"</tbody>";}
function renderFail(){let h="<thead><tr><th>Asset type</th><th>Failed</th><th>Sold</th><th>Failure rate</th></tr></thead><tbody>";
 (D.failure_type||[]).forEach(r=>{h+=`<tr><td>${r.asset_type}</td><td class="tnum">${r.n_failed}</td><td class="tnum">${r.n_sold}</td>`+
  `<td class="tnum ${r.failure_rate_pct>55?'down':''}">${r.failure_rate_pct==null?"—":r.failure_rate_pct.toFixed(0)+"%"}</td></tr>`;});$("#failTable").innerHTML=h+"</tbody>";}

// ---------- init / recompute ----------
function recompute(){renderTypes();renderAnswers();renderInventory();renderUnderwrite();renderDealSheet();}
function resetAll(){ASM=JSON.parse(JSON.stringify(D.assumptions.by_type));initFin();renderAsm();recompute();}
function initFin(){const f=D.assumptions.finance;
 $("#gLtv").value=(f.ltv*100).toFixed(0);$("#gRate").value=(f.rate*100).toFixed(3).replace(/0+$/,'').replace(/\.$/,'');
 $("#gShift").value=f.rate_shift_bps;$("#gAmort").value=f.amort;$("#gExitDelta").value=f.exit_cap_delta_bps;
 $("#gRg").value=(f.rent_growth*100).toFixed(1);$("#gEg").value=(f.expense_growth*100).toFixed(1);
 $("#gHold").value=f.hold;$("#gSell").value=(f.sell_pct*100).toFixed(1);$("#gAcq").value=(f.acq_pct*100).toFixed(1);}
function loadListing(l){$("#uType").value=l.asset_type;$("#uPrice").value=l.price;$("#uSqft").value=l.sqft;seedType(l.asset_type);curListing=l;}
function initUnderwrite(){const s=D.seed;
 const opts=D.listings.filter(isLive).sort((a,b)=>b.price-a.price);
 $("#uPick").innerHTML='<option value="-1">— manual —</option>'+opts.map((l,i)=>`<option value="${i}">${(l.address||l.mls).slice(0,40)} · ${usd(l.price)} · ${l.asset_type}</option>`).join("");
 $("#uType").innerHTML=D.asset_order.filter(t=>ASM[t]).map(t=>`<option>${t}</option>`).join("");
 // default to the largest CREDIBLE underpriced deal (plausible implied cap) so the deal sheet
 // opens on a real, compelling — not artifact — listing
 const scored=opts.map((l,i)=>({i,l,d:derive(l.price,l.sqft,l.asset_type)}))
  .filter(x=>!suspect(x.d)&&x.d.gap<-0.05).sort((a,b)=>b.l.price-a.l.price);
 if(scored.length){loadListing(scored[0].l);$("#uPick").value=scored[0].i;}
 else{$("#uType").value=s.asset_type;$("#uPrice").value=s.price;$("#uSqft").value=s.sqft;seedType(s.asset_type);}
 $("#uType").addEventListener("change",e=>{seedType(e.target.value);renderUnderwrite();renderDealSheet();});
 $("#uPick").addEventListener("change",e=>{const i=+e.target.value;curListing=i>=0?opts[i]:null;if(i>=0)loadListing(opts[i]);renderUnderwrite();renderDealSheet();});
 ["uPrice","uSqft","uRent","uVac","uOpex","uCap","uExit"].forEach(id=>$("#"+id).addEventListener("input",()=>{renderUnderwrite();renderDealSheet();}));
 ["gLtv","gRate","gShift","gAmort","gExitDelta","gRg","gEg","gHold","gSell","gAcq"].forEach(id=>$("#"+id).addEventListener("input",()=>{renderAnswers();renderInventory();renderUnderwrite();renderDealSheet();}));}
function header(){const m=D.meta,c=D.coverage;
 $("#subline").innerHTML=`${m.n_listings} listings · ${m.n_sale_comps} sale comps (${m.n_closed} closed) · ${m.n_lease} leases · $/SqFt R²=${m.hedonic_r2} · city ${usd(m.city_norm_ppsf)}/SqFt`;
 $("#banner").innerHTML="<b>No income in the source.</b> This BeachesMLS export has price, size, type, age &amp; location — but no NOI, rent, cap or unit counts. "+
  "Every income figure here is built from the <b>editable assumptions</b> and <b>global financing</b> below and recomputes live. Pricing &amp; screening tool, not an appraisal.";
 $("#invCoverage").innerHTML=`Showing <b>${c.live_shown}</b> of ${c.live_sale} live for-sale listings — the other ${c.live_sale-c.live_shown} have no building SqFt (can't be priced). ${c.live_all-c.live_sale} live leases excluded.`;}
function toggleTheme(){const r=document.documentElement,cur=r.getAttribute("data-theme")||(matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");r.setAttribute("data-theme",cur==="dark"?"light":"dark");}

ASM=JSON.parse(JSON.stringify(D.assumptions.by_type));
header();initFin();renderAsm();renderSub();renderTypeFilter();fillSubFilter();renderAbs();renderFail();initUnderwrite();recompute();
</script>"""


if __name__ == "__main__":
    main()
