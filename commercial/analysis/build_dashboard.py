#!/usr/bin/env python3
"""
Self-contained interactive commercial deal dashboard -> dashboard/index.html

The dashboard is the point of this project: because the MLS export has no income, every
income number is derived from ASSUMPTIONS the user controls with live inputs. Drag a rent,
vacancy, expense ratio or cap rate and the whole board — implied caps, values, mispricing
flags, and the single-deal underwriting — recomputes in the browser, instantly. All data,
CSS and JS are inlined (no network).
"""
from __future__ import annotations
import json
import os

import pandas as pd

import cre_common as CRE
import cre_assumptions as A
import cre_scenario as SC

OUT = os.path.join(CRE.ROOT, "dashboard", "index.html")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


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

    # compact per-listing records; income is derived live in JS
    recs = valued[["mls", "address", "submarket", "asset_type", "status", "price", "sqft",
                   "ppsf", "pred_ppsf", "ppsf_gap_pct", "price_band"]].copy()
    recs = recs.where(pd.notna(recs), None)
    listings = recs.to_dict(orient="records")

    df_all = CRE.load_clean()
    live_all = int(df_all["status"].isin(CRE.LIVE).sum())
    live_sale = int((df_all["status"].isin(CRE.LIVE) & df_all["deal_kind"].eq("Sale")).sum())
    live_shown = sum(1 for l in listings if l["status"] in ("Active", "Pending", "UnderContract"))

    seed = SC.seed()
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
        "seed": seed,
        "asset_order": CRE.ASSET_ORDER,
    }

    html = _TEMPLATE.replace("/*__DATA__*/", json.dumps(DATA))
    with open(OUT, "w") as f:
        f.write(html)
    print(f"Dashboard -> {os.path.relpath(OUT, CRE.ROOT)} ({os.path.getsize(OUT)//1024} KB)")


_TEMPLATE = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Commercial Deal Dashboard — Fort Lauderdale</title>
<style>
:root{
 --bg:#f6f5f1; --card:#fff; --ink:#1f2a37; --muted:#6b7280; --line:#e5e3db;
 --accent:#2f6f9f; --accent-soft:#eaf2f9; --good:#3f7d5a; --bad:#b0473a; --warn:#c2703d;
 --yellow:#fff7d6; --yellow-line:#e2d9a6;
}
@media (prefers-color-scheme:dark){:root{
 --bg:#12161c; --card:#1a2029; --ink:#e6e9ee; --muted:#98a1ad; --line:#2b333f;
 --accent:#6db0e0; --accent-soft:#1e2b38; --good:#68b088; --bad:#e0796b; --warn:#e0a06a;
 --yellow:#2a2716; --yellow-line:#4a441f;}}
:root[data-theme=dark]{
 --bg:#12161c; --card:#1a2029; --ink:#e6e9ee; --muted:#98a1ad; --line:#2b333f;
 --accent:#6db0e0; --accent-soft:#1e2b38; --good:#68b088; --bad:#e0796b; --warn:#e0a06a;
 --yellow:#2a2716; --yellow-line:#4a441f;}
:root[data-theme=light]{
 --bg:#f6f5f1; --card:#fff; --ink:#1f2a37; --muted:#6b7280; --line:#e5e3db;
 --accent:#2f6f9f; --accent-soft:#eaf2f9; --good:#3f7d5a; --bad:#b0473a; --warn:#c2703d;
 --yellow:#fff7d6; --yellow-line:#e2d9a6;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1200px;margin:0 auto;padding:0 18px 80px}
header{padding:26px 0 12px}
h1{font-size:26px;margin:0 0 6px}
h2{font-size:20px;margin:0 0 4px}
.sub{color:var(--muted);font-size:13px}
.banner{background:var(--accent-soft);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:12px 0;font-size:13.5px}
nav{position:sticky;top:0;z-index:20;background:var(--bg);border-bottom:1px solid var(--line);padding:8px 0;margin-bottom:18px;display:flex;gap:6px;flex-wrap:wrap}
nav a{font-size:13px;text-decoration:none;color:var(--ink);padding:5px 10px;border-radius:7px;border:1px solid transparent}
nav a:hover{background:var(--accent-soft);border-color:var(--line)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 18px 20px;margin:16px 0;box-shadow:0 1px 2px rgba(0,0,0,.03)}
.grid{display:grid;gap:12px}
.tiles{grid-template-columns:repeat(auto-fit,minmax(150px,1fr))}
.tile{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:12px 13px}
.tile .t{font-size:11.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.tile .v{font-size:22px;font-weight:650;margin-top:3px}
.tile .s{font-size:12px;color:var(--muted);margin-top:2px}
.up{color:var(--good)}.down{color:var(--bad)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:right;padding:7px 9px;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.03em;cursor:default}
thead th{position:sticky;top:44px;background:var(--card)}
tbody tr:hover{background:var(--accent-soft)}
.tnum{font-variant-numeric:tabular-nums}
.scroll{overflow-x:auto}
.pill{display:inline-block;padding:2px 8px;border-radius:20px;font-size:11.5px;font-weight:600}
.pill.u{background:rgba(63,125,90,.15);color:var(--good)}
.pill.o{background:rgba(176,71,58,.15);color:var(--bad)}
.pill.f{background:var(--line);color:var(--muted)}
input,select{font:inherit;color:var(--ink);background:var(--card);border:1px solid var(--line);border-radius:7px;padding:5px 7px}
input[type=number]{width:82px;text-align:right;background:var(--yellow);border-color:var(--yellow-line)}
.asm td input{width:70px}
.ctrl{display:flex;flex-wrap:wrap;gap:14px;align-items:end}
.ctrl label{display:flex;flex-direction:column;font-size:11.5px;color:var(--muted);gap:3px}
.btn{cursor:pointer;background:var(--accent);color:#fff;border:none;border-radius:8px;padding:7px 13px;font-size:13px}
.btn.ghost{background:transparent;color:var(--accent);border:1px solid var(--accent)}
.muted{color:var(--muted)}
.right{text-align:right}
.themeToggle{position:fixed;top:10px;right:12px;z-index:30;cursor:pointer;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:5px 9px;font-size:12px}
.flex{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.chip{font-size:12px;padding:4px 9px;border:1px solid var(--line);border-radius:20px;cursor:pointer;background:var(--card)}
.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.small{font-size:12px}
.bar{height:8px;border-radius:5px;background:var(--accent);display:inline-block;vertical-align:middle}
</style></head>
<body>
<div class="themeToggle" onclick="toggleTheme()">◐ theme</div>
<div class="wrap">
<header>
 <h1>Commercial Deal Dashboard <span class="muted" style="font-weight:400;font-size:16px">— Fort Lauderdale</span></h1>
 <div class="sub" id="subline"></div>
</header>
<div class="banner" id="banner"></div>
<nav>
 <a href="#assumptions">Assumptions</a>
 <a href="#overview">$/SqFt map</a>
 <a href="#inventory">Reprice inventory</a>
 <a href="#underwrite">Underwrite a deal</a>
 <a href="#absorption">Absorption</a>
 <a href="#prospects">Prospects</a>
</nav>

<div class="card" id="assumptions">
 <h2>Assumptions <span class="muted small">— the income the export doesn't give us. Edit any yellow cell; everything below recomputes live.</span></h2>
 <div class="sub" style="margin:6px 0 12px">The MLS export has price &amp; size but no NOI, rent, cap or units. These per-asset-class
  industry norms turn size into income. Defaults are calibrated so a typically-priced building of each type prices near its market cap — tune them to your read.</div>
 <div class="scroll"><table class="asm" id="asmTable"></table></div>
 <div class="flex" style="margin-top:10px">
  <button class="btn ghost" onclick="resetAssumptions()">Reset to defaults</button>
  <span class="muted small">Implied cap = NOI ÷ price on each type's median $/SqFt · Value = NOI ÷ market cap.</span>
 </div>
</div>

<div class="card" id="overview">
 <h2>Normalized $/SqFt</h2>
 <div class="sub" style="margin:6px 0 12px">Factual, from the data — size/age/type/closed-vs-listed removed. This is the price backbone the assumptions sit on.</div>
 <div class="grid" style="grid-template-columns:1fr 1fr;gap:20px" id="ovGrids">
  <div><h3 class="small muted" style="margin:0 0 6px">By submarket (MLS area)</h3><div class="scroll"><table id="subTable"></table></div></div>
  <div><h3 class="small muted" style="margin:0 0 6px">By asset type</h3><div class="scroll"><table id="typeTable"></table></div></div>
 </div>
</div>

<div class="card" id="inventory">
 <h2>Reprice live inventory</h2>
 <div class="sub" style="margin:6px 0 6px">Live for-sale listings <b>with a usable building size</b>, on two lenses: <b>$/SqFt</b> vs comps, and <b>income</b> (asking vs value at your assumed rents &amp; cap). Below value = higher implied cap = a buy.</div>
 <div class="small muted" id="invCoverage" style="margin-bottom:8px"></div>
 <div class="flex" id="typeFilter" style="margin-bottom:10px"></div>
 <div class="scroll"><table id="invTable"></table></div>
</div>

<div class="card" id="underwrite">
 <h2>Underwrite a deal <span class="muted small">— pick a listing or type; NOI is built from the assumptions</span></h2>
 <div class="ctrl" style="margin:8px 0 14px">
  <label>Listing<select id="uPick"></select></label>
  <label>Asset type<select id="uType"></select></label>
  <label>Price ($)<input type="number" id="uPrice" step="25000"></label>
  <label>Size (SqFt)<input type="number" id="uSqft" step="500"></label>
  <label>Rent $/SqFt/yr<input type="number" id="uRent" step="1"></label>
  <label>Vacancy %<input type="number" id="uVac" step="1"></label>
  <label>Opex % of EGI<input type="number" id="uOpex" step="1"></label>
  <label>Market cap %<input type="number" id="uCap" step="0.1"></label>
 </div>
 <div class="ctrl" style="margin:0 0 14px">
  <label>LTV %<input type="number" id="uLtv" step="5"></label>
  <label>Rate %<input type="number" id="uRate" step="0.125"></label>
  <label>Rate shift bps<input type="number" id="uShift" step="25"></label>
  <label>Amort yrs<input type="number" id="uAmort" step="1"></label>
  <label>Exit cap %<input type="number" id="uExit" step="0.1"></label>
  <label>Rent growth %<input type="number" id="uRg" step="0.5"></label>
  <label>Expense growth %<input type="number" id="uEg" step="0.5"></label>
  <label>Hold yrs<input type="number" id="uHold" step="1"></label>
 </div>
 <div class="grid tiles" id="uTiles"></div>
 <div class="grid" style="grid-template-columns:1fr 1fr;gap:20px;margin-top:14px">
  <div><h3 class="small muted">Sensitivity — exit cap</h3><div class="scroll"><table id="uSensCap"></table></div></div>
  <div><h3 class="small muted">Sensitivity — rent $/SqFt</h3><div class="scroll"><table id="uSensRent"></table></div></div>
 </div>
 <div class="sub" style="margin-top:8px">Levered IRR / equity multiple over the hold; NOI grows income &amp; expenses separately; exit = final-year NOI ÷ exit cap, net of debt payoff &amp; sale costs.</div>
</div>

<div class="card" id="absorption">
 <h2>Absorption &amp; supply</h2>
 <div class="sub" id="absNote" style="margin:6px 0 10px"></div>
 <div class="grid" style="grid-template-columns:1fr 1fr;gap:20px">
  <div><h3 class="small muted">By submarket (months of supply)</h3><div class="scroll"><table id="absTable"></table></div></div>
  <div><h3 class="small muted">By asset type</h3><div class="scroll"><table id="segTable"></table></div></div>
 </div>
</div>

<div class="card" id="prospects">
 <h2>Prospecting — failure rate by asset type</h2>
 <div class="sub" style="margin:6px 0 10px">Share of listings that failed (expired / cancelled / withdrawn) vs sold — where deals stall.</div>
 <div class="scroll"><table id="failTable"></table></div>
</div>

<div class="sub" style="margin-top:20px">Generated from user-provided BeachesMLS commercial exports. No income data in source — all income metrics are assumption-derived and tunable above. Screening intelligence, not appraisals.</div>
</div>

<script id="DATA" type="application/json">/*__DATA__*/</script>
<script>
const D=JSON.parse(document.getElementById("DATA").textContent);
const $=s=>document.querySelector(s);
const usd=x=>{if(x==null||isNaN(x))return "—";const a=Math.abs(x);
 if(a>=1e9)return "$"+(x/1e9).toFixed(2)+"B";if(a>=1e6)return "$"+(x/1e6).toFixed(2)+"M";
 if(a>=1e3)return "$"+(x/1e3).toFixed(0)+"K";return "$"+x.toFixed(0);};
const pf=x=>x==null||isNaN(x)?"—":(x*100).toFixed(2)+"%";
const p1=x=>x==null||isNaN(x)?"—":(x*100).toFixed(1)+"%";
const sg=x=>x==null||isNaN(x)?"—":(x>=0?"+":"")+x.toFixed(1)+"%";
const num=x=>x==null||isNaN(x)?"—":Math.round(x).toLocaleString();

// live assumptions state
let ASM={};
function resetAssumptions(){ASM=JSON.parse(JSON.stringify(D.assumptions.by_type));renderAll();}
ASM=JSON.parse(JSON.stringify(D.assumptions.by_type));  // init only; first render happens at bottom

function derive(price,sqft,type){
 const a=ASM[type]||ASM["Commercial (other)"];
 const egi=sqft*a.rent_psf*(1-a.vacancy);
 const noi=egi*(1-a.opex_ratio);
 const impliedCap=price?noi/price:NaN;
 const value=a.cap_rate?noi/a.cap_rate:NaN;
 const gap=value?price/value-1:NaN;
 return {noi,impliedCap,value,gap,marketCap:a.cap_rate};
}

// ---------- assumptions table ----------
function renderAsm(){
 const med={}; // median ppsf by type from D.types
 D.types.forEach(t=>med[t.asset_type]=t.median_ppsf);
 let h="<thead><tr><th>Asset type</th><th>Median $/SqFt</th><th># comps</th>"+
  "<th>Rent $/SqFt</th><th>Vacancy %</th><th>Opex %</th><th>Market cap %</th>"+
  "<th>Implied cap*</th></tr></thead><tbody>";
 D.asset_order.filter(t=>ASM[t]).forEach(t=>{
  const a=ASM[t];const row=D.types.find(x=>x.asset_type===t)||{};
  const mp=med[t]||0;
  const noi=mp*a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio); // per sqft
  const ic=mp?noi/mp:NaN;
  h+=`<tr><td>${t}</td><td class="tnum">${mp?usd(mp):"—"}</td><td class="tnum">${row.n||"—"}</td>`+
   `<td><input type="number" step="1" value="${a.rent_psf}" oninput="setAsm('${t}','rent_psf',this.value,1)"></td>`+
   `<td><input type="number" step="1" value="${(a.vacancy*100).toFixed(0)}" oninput="setAsm('${t}','vacancy',this.value,0.01)"></td>`+
   `<td><input type="number" step="1" value="${(a.opex_ratio*100).toFixed(0)}" oninput="setAsm('${t}','opex_ratio',this.value,0.01)"></td>`+
   `<td><input type="number" step="0.05" value="${(a.cap_rate*100).toFixed(2)}" oninput="setAsm('${t}','cap_rate',this.value,0.01)"></td>`+
   `<td class="tnum ${ic>a.cap_rate?'up':ic<a.cap_rate?'down':''}">${pf(ic)}</td></tr>`;
 });
 $("#asmTable").innerHTML=h+"</tbody>";
}
function setAsm(t,k,val,mult){ASM[t][k]=parseFloat(val)*mult; if(isNaN(ASM[t][k]))ASM[t][k]=0;
 renderAsm();renderTypes();renderInventory();}

// ---------- overview tables ----------
function renderSub(){
 const s=D.submarkets.slice().sort((a,b)=>b.norm_ppsf-a.norm_ppsf);
 const mx=Math.max(...s.map(x=>x.norm_ppsf));
 let h="<thead><tr><th>Submarket</th><th>Norm $/SqFt</th><th>vs city</th><th>Median price</th><th>n</th><th>Top type</th></tr></thead><tbody>";
 s.forEach(r=>{h+=`<tr><td>${r.submarket}</td><td class="tnum">${usd(r.norm_ppsf)} <span class="bar" style="width:${40*r.norm_ppsf/mx}px"></span></td>`+
  `<td class="tnum ${r.vs_city_pct>=0?'up':'down'}">${sg(r.vs_city_pct)}</td><td class="tnum">${usd(r.median_price)}</td>`+
  `<td class="tnum">${r.n}</td><td class="small">${r.top_asset||"—"}</td></tr>`;});
 $("#subTable").innerHTML=h+"</tbody>";
}
function renderTypes(){
 let h="<thead><tr><th>Asset type</th><th>Median $/SqFt</th><th>n</th><th>Assumed rent</th><th>Implied cap</th><th>Market cap</th></tr></thead><tbody>";
 D.asset_order.filter(t=>D.types.find(x=>x.asset_type===t)).forEach(t=>{
  const r=D.types.find(x=>x.asset_type===t);const a=ASM[t];
  const noi=r.median_ppsf*a.rent_psf*(1-a.vacancy)*(1-a.opex_ratio);const ic=noi/r.median_ppsf;
  h+=`<tr><td>${t}</td><td class="tnum">${usd(r.median_ppsf)}</td><td class="tnum">${r.n}</td>`+
   `<td class="tnum">$${a.rent_psf}/sf</td><td class="tnum ${ic>a.cap_rate?'up':'down'}">${pf(ic)}</td>`+
   `<td class="tnum">${pf(a.cap_rate)}</td></tr>`;});
 $("#typeTable").innerHTML=h+"</tbody>";
}

// ---------- inventory ----------
let invFilter="All", invSort={k:"income_gap",dir:1};
function renderTypeFilter(){
 const types=["All",...D.asset_order.filter(t=>D.listings.some(l=>l.asset_type===t&&isLive(l)))];
 $("#typeFilter").innerHTML=types.map(t=>`<span class="chip ${t===invFilter?'on':''}" onclick="invFilter='${t}';renderTypeFilter();renderInventory()">${t}</span>`).join("");
}
const LIVE=["Active","Pending","UnderContract"];
const isLive=l=>LIVE.includes(l.status);
function renderInventory(){
 let rows=D.listings.filter(isLive).filter(l=>invFilter==="All"||l.asset_type===invFilter);
 rows=rows.map(l=>{const d=derive(l.price,l.sqft,l.asset_type);
  return {...l, noi:d.noi, impliedCap:d.impliedCap, value:d.value, income_gap:d.gap*100, marketCap:d.marketCap};});
 const k=invSort.k;rows.sort((a,b)=>((a[k]==null?1e9:a[k])-(b[k]==null?1e9:b[k]))*invSort.dir);
 const flag=g=>g<-10?'<span class="pill u">Underpriced</span>':g>10?'<span class="pill o">Overpriced</span>':'<span class="pill f">Fair</span>';
 let h="<thead><tr>"+
  th("address","Address")+th("asset_type","Type")+th("submarket","Area")+
  th("price","Asking")+th("ppsf","$/SqFt")+th("ppsf_gap_pct","vs comp")+
  th("impliedCap","Implied cap")+th("marketCap","Mkt cap")+th("value","Value")+
  th("income_gap","Gap")+"<th>Flag</th></tr></thead><tbody>";
 rows.slice(0,120).forEach(r=>{h+=`<tr><td>${r.address||r.mls}</td><td class="small">${r.asset_type}</td>`+
  `<td class="small">${r.submarket}</td><td class="tnum">${usd(r.price)}</td><td class="tnum">${usd(r.ppsf)}</td>`+
  `<td class="tnum ${r.ppsf_gap_pct<0?'up':'down'}">${sg(r.ppsf_gap_pct)}</td>`+
  `<td class="tnum ${r.impliedCap>r.marketCap?'up':'down'}">${pf(r.impliedCap)}</td>`+
  `<td class="tnum">${pf(r.marketCap)}</td><td class="tnum">${usd(r.value)}</td>`+
  `<td class="tnum ${r.income_gap<0?'up':'down'}">${sg(r.income_gap)}</td><td>${flag(r.income_gap)}</td></tr>`;});
 $("#invTable").innerHTML=h+"</tbody>";
}
function th(k,label){return `<th style="cursor:pointer" onclick="sortInv('${k}')">${label}</th>`;}
function sortInv(k){invSort.dir=(invSort.k===k?-invSort.dir:1);invSort.k=k;renderInventory();}

// ---------- underwriting scenario ----------
function irr(cfs){const npv=r=>cfs.reduce((s,c,i)=>s+c/Math.pow(1+r,i),0);
 if(cfs.every(c=>c>=0)||cfs.every(c=>c<=0))return NaN;
 let a=-0.95,b=1,g=0;while(npv(a)*npv(b)>0&&g<200){b+=0.5;g++;}if(npv(a)*npv(b)>0)return NaN;
 for(let i=0;i<200;i++){const m=(a+b)/2,fm=npv(m);if(Math.abs(fm)<1e-8)return m;if(npv(a)*fm<0)b=m;else a=m;}
 return (a+b)/2;}
function scen(o){
 const egi0=o.sqft*o.rent*(1-o.vac), exp0=egi0*o.opex, noi0=egi0-exp0;
 const goin=o.price?noi0/o.price:NaN, effr=o.rate+o.shift/10000, loan=o.price*o.ltv;
 const equity=o.price*(1-o.ltv)+o.price*o.acq, m=effr/12, n=o.amort*12;
 const pay=m>0?loan*m/(1-Math.pow(1+m,-n)):loan/n, ads=pay*12;
 const dscr=ads?noi0/ads:NaN, dy=loan?noi0/loan:NaN;
 const hold=Math.round(o.hold), noit=[];
 for(let t=1;t<=hold;t++)noit.push(egi0*Math.pow(1+o.rg,t)-exp0*Math.pow(1+o.eg,t));
 const exitNoi=noit.length?noit[noit.length-1]:noi0;
 const exitVal=o.exitCap>0?exitNoi/o.exitCap:NaN, k=hold*12;
 const rem=m>0?loan*(Math.pow(1+m,n)-Math.pow(1+m,k))/(Math.pow(1+m,n)-1):loan*(1-k/n);
 const net=exitVal*(1-o.sell)-rem;
 const cfs=[-equity];noit.forEach((nc,i)=>{let cf=nc-ads;if(i===hold-1)cf+=net;cfs.push(cf);});
 const li=irr(cfs), dist=cfs.slice(1).reduce((s,c)=>s+c,0), em=equity?dist/equity:NaN;
 const coc1=equity&&noit.length?(noit[0]-ads)/equity:NaN;
 return {noi0,goin,loan,equity,ads,dscr,dy,exitNoi,exitVal,rem,net,li,em,coc1,hold};
}
function readScen(){return {price:+$("#uPrice").value,sqft:+$("#uSqft").value,rent:+$("#uRent").value,
 vac:+$("#uVac").value/100,opex:+$("#uOpex").value/100,exitCap:+$("#uExit").value/100,
 ltv:+$("#uLtv").value/100,rate:+$("#uRate").value/100,shift:+$("#uShift").value,amort:+$("#uAmort").value,
 rg:+$("#uRg").value/100,eg:+$("#uEg").value/100,hold:+$("#uHold").value,sell:D.assumptions.finance.sell_pct,acq:D.assumptions.finance.acq_pct};}
function renderUnderwrite(){
 const o=readScen(), v=scen(o), mktcap=+$("#uCap").value/100;
 const value=mktcap?v.noi0/mktcap:NaN, gap=value?o.price/value-1:NaN;
 const tile=(t,val,s,cls)=>`<div class="tile"><div class="t">${t}</div><div class="v ${cls||''}">${val}</div><div class="s">${s||''}</div></div>`;
 $("#uTiles").innerHTML=[
  tile("Derived NOI",usd(v.noi0),`$${(v.noi0/o.sqft).toFixed(1)}/sf`),
  tile("Going-in cap",pf(v.goin),`mkt ${pf(mktcap)}`,v.goin>mktcap?'up':'down'),
  tile("Value @ mkt cap",usd(value),`ask ${sg(gap*100)}`,gap<0?'up':'down'),
  tile("DSCR",v.dscr.toFixed(2)+"×",`${$("#uLtv").value}% LTV @ ${$("#uRate").value}%`,v.dscr>=1.25?'up':'down'),
  tile("Debt yield",p1(v.dy),`loan ${usd(v.loan)}`),
  tile("Year-1 cash-on-cash",p1(v.coc1),`equity ${usd(v.equity)}`,v.coc1>0?'up':'down'),
  tile(v.hold+"-yr levered IRR",p1(v.li),`exit ${$("#uExit").value}% cap`,v.li>0.1?'up':v.li<0?'down':''),
  tile("Equity multiple",v.em.toFixed(2)+"×",`net sale ${usd(v.net)}`,v.em>1?'up':'down'),
 ].join("");
 // sensitivity: exit cap
 const baseExit=o.exitCap; let h="<thead><tr><th>Exit cap</th><th>IRR</th><th>Equity mult</th><th>Exit value</th></tr></thead><tbody>";
 [-0.75,-0.5,-0.25,0,0.25,0.5,0.75,1].forEach(dd=>{const ec=baseExit+dd/100;const vv=scen({...o,exitCap:ec});
  const hl=Math.abs(dd)<1e-9?' style="background:var(--accent-soft)"':'';
  h+=`<tr${hl}><td class="tnum">${(ec*100).toFixed(2)}%</td><td class="tnum ${vv.li>0?'up':'down'}">${p1(vv.li)}</td>`+
   `<td class="tnum">${vv.em.toFixed(2)}×</td><td class="tnum">${usd(vv.exitVal)}</td></tr>`;});
 $("#uSensCap").innerHTML=h+"</tbody>";
 // sensitivity: rent psf
 const baseRent=o.rent; let h2="<thead><tr><th>Rent $/SqFt</th><th>NOI</th><th>Going-in cap</th><th>IRR</th></tr></thead><tbody>";
 [-4,-2,-1,0,1,2,4].forEach(dr=>{const rr=Math.max(1,baseRent+dr);const vv=scen({...o,rent:rr});
  const hl=dr===0?' style="background:var(--accent-soft)"':'';
  h2+=`<tr${hl}><td class="tnum">$${rr.toFixed(0)}</td><td class="tnum">${usd(vv.noi0)}</td>`+
   `<td class="tnum">${pf(vv.goin)}</td><td class="tnum ${vv.li>0?'up':'down'}">${p1(vv.li)}</td></tr>`;});
 $("#uSensRent").innerHTML=h2+"</tbody>";
}
function seedType(t){const a=ASM[t]||ASM["Commercial (other)"];$("#uRent").value=a.rent_psf;
 $("#uVac").value=(a.vacancy*100).toFixed(0);$("#uOpex").value=(a.opex_ratio*100).toFixed(0);
 $("#uCap").value=(a.cap_rate*100).toFixed(2);$("#uExit").value=((a.cap_rate+D.assumptions.finance.exit_cap_delta_bps/10000)*100).toFixed(2);}
function initUnderwrite(){
 const fin=D.assumptions.finance, s=D.seed;
 const opts=D.listings.filter(isLive).sort((a,b)=>b.price-a.price).slice(0,150);
 $("#uPick").innerHTML='<option value="-1">— manual —</option>'+opts.map((l,i)=>
  `<option value="${i}">${(l.address||l.mls).slice(0,42)} · ${usd(l.price)} · ${l.asset_type}</option>`).join("");
 $("#uType").innerHTML=D.asset_order.filter(t=>ASM[t]).map(t=>`<option>${t}</option>`).join("");
 $("#uType").value=s.asset_type;$("#uPrice").value=s.price;$("#uSqft").value=s.sqft;
 $("#uLtv").value=(fin.ltv*100).toFixed(0);$("#uRate").value=(fin.rate*100).toFixed(3).replace(/0+$/,'').replace(/\.$/,'');
 $("#uShift").value=fin.rate_shift_bps;$("#uAmort").value=fin.amort;$("#uRg").value=(fin.rent_growth*100).toFixed(1);
 $("#uEg").value=(fin.expense_growth*100).toFixed(1);$("#uHold").value=fin.hold;
 seedType(s.asset_type);
 $("#uType").addEventListener("change",e=>{seedType(e.target.value);renderUnderwrite();});
 $("#uPick").addEventListener("change",e=>{const i=+e.target.value;if(i>=0){const l=opts[i];
  $("#uType").value=l.asset_type;$("#uPrice").value=l.price;$("#uSqft").value=l.sqft;seedType(l.asset_type);}renderUnderwrite();});
 ["uPrice","uSqft","uRent","uVac","uOpex","uCap","uLtv","uRate","uShift","uAmort","uExit","uRg","uEg","uHold"]
  .forEach(id=>$("#"+id).addEventListener("input",renderUnderwrite));
 renderUnderwrite();
}

// ---------- absorption / segments / prospects ----------
function renderAbs(){
 const seg=D.segments||[];
 $("#absNote").textContent=(D.meta&&"")+ (window.__absnote||"Months of supply = live ÷ (closed per month); closed assumed to span a fixed window (no dates in export).");
 let h="<thead><tr><th>Submarket</th><th>Mo supply</th><th>Live</th><th>Sold</th><th>Failed</th></tr></thead><tbody>";
 (D.absorption||[]).forEach(r=>{const ms=r.months_supply;
  h+=`<tr><td>${r.submarket}</td><td class="tnum ${ms<12?'up':ms>30?'down':''}">${ms==null?"—":ms.toFixed(1)}</td>`+
   `<td class="tnum">${r.n_live}</td><td class="tnum">${r.n_sold}</td><td class="tnum">${r.n_failed}</td></tr>`;});
 $("#absTable").innerHTML=h+"</tbody>";
 let h2="<thead><tr><th>Asset type</th><th>n</th><th>Median $/SqFt</th><th>Live</th><th>Sold</th><th>Mo supply</th></tr></thead><tbody>";
 seg.forEach(r=>{h2+=`<tr><td>${r.asset_type}</td><td class="tnum">${r.n}</td><td class="tnum">${usd(r.median_ppsf)}</td>`+
  `<td class="tnum">${r.n_live}</td><td class="tnum">${r.n_sold}</td><td class="tnum">${r.months_supply==null?"—":r.months_supply.toFixed(1)}</td></tr>`;});
 $("#segTable").innerHTML=h2+"</tbody>";
}
function renderFail(){
 let h="<thead><tr><th>Asset type</th><th>Failed</th><th>Sold</th><th>Failure rate</th></tr></thead><tbody>";
 (D.failure_type||[]).forEach(r=>{h+=`<tr><td>${r.asset_type}</td><td class="tnum">${r.n_failed}</td>`+
  `<td class="tnum">${r.n_sold}</td><td class="tnum ${r.failure_rate_pct>55?'down':''}">${r.failure_rate_pct==null?"—":r.failure_rate_pct.toFixed(0)+"%"}</td></tr>`;});
 $("#failTable").innerHTML=h+"</tbody>";
}

function renderAll(){renderAsm();renderSub();renderTypes();renderTypeFilter();renderInventory();renderAbs();renderFail();}
function header(){
 const m=D.meta;
 $("#subline").innerHTML=`${m.n_listings} listings · ${m.n_sale_comps} sale comps (${m.n_closed} closed) · `+
  `${m.n_lease} lease listings · normalized $/SqFt R²=${m.hedonic_r2} · city ${usd(m.city_norm_ppsf)}/SqFt`;
 $("#banner").innerHTML="<b>No income in the source.</b> This BeachesMLS export has price, size, type, age &amp; location — but no NOI, rent, cap or unit counts. "+
  "Everything income-based here is built from the <b>editable assumptions</b> at the top and recomputes live. Treat it as a pricing &amp; screening tool, not an appraisal.";
 const c=D.coverage;
 $("#invCoverage").innerHTML=`Showing <b>${c.live_shown}</b> of ${c.live_sale} live for-sale listings — `+
  `the other ${c.live_sale-c.live_shown} have no building SqFt in the export (can't be priced). `+
  `${c.live_all-c.live_sale} additional live listings are leases, excluded here.`;
}
function toggleTheme(){const r=document.documentElement;const cur=r.getAttribute("data-theme")||
 (matchMedia("(prefers-color-scheme:dark)").matches?"dark":"light");
 r.setAttribute("data-theme",cur==="dark"?"light":"dark");}

header();renderAll();initUnderwrite();
</script>
</body></html>"""


if __name__ == "__main__":
    main()
