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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
DASH = os.path.join(ROOT, "dashboard")
os.makedirs(DASH, exist_ok=True)

with open(os.path.join(PROC, "mls_bundle.json")) as f:
    MLS = json.load(f)
with open(os.path.join(PROC, "analysis_bundle.json")) as f:
    REDFIN = json.load(f)

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

  <section class="kpis" id="kpis"></section>

  <div class="card">
    <h2>What drives value — the per-home model</h2>
    <p class="cap">Marginal effect on price per square foot, holding size, type and neighborhood constant. Estimated from actual closed sales.</p>
    <div class="drivers" id="drivers"></div>
    <div style="font-size:12px;font-weight:600;color:var(--ink-2);margin:16px 0 2px">Price by lot geography <span style="font-weight:400;color:var(--muted)">— median $/ft² (derived, indicative)</span></div>
    <div class="geostrip" id="geostrip"></div>
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

  <div class="card">
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

  <footer class="fl-foot">
    Normalized with a per-home hedonic model on <span id="fn"></span> closed MLS sales
    (cross-validated against <a href="https://www.redfin.com/news/data-center/" target="_blank" rel="noopener">Redfin</a> at r=0.93).
    Neighborhood benchmarks and screening signals — not per-home appraisals. Condo-level flags are coarse (floor/view/renovation unobserved).
  </footer>
</div></div>
<div class="tt" id="tt"></div>

<script id="mls-data" type="application/json">__MLS_JSON__</script>
<script id="redfin-data" type="application/json">__REDFIN_JSON__</script>
<script>
(function(){
"use strict";
const MLS=JSON.parse(document.getElementById("mls-data").textContent);
const RED=JSON.parse(document.getElementById("redfin-data").textContent);
const M=MLS.meta, NB=MLS.neighborhoods;
const $=s=>document.querySelector(s), tt=$("#tt");
const usd=v=>v==null?"—":"$"+Math.round(v).toLocaleString();
const pctS=v=>v==null?"—":(v>=0?"+":"")+v.toFixed(0)+"%";
const cvar=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
let state={basis:"all", q:"", sort:{key:"norm_ppsf",dir:-1}, sel:null};
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
    ["Model agreement", "r 0.93", "MLS vs Redfin, independent"],
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
function renderAll(){kpis();drivers();geostrip();lineChart();flags();barChart();renderTable();
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
})();
</script>
"""


def build():
    inner = (INNER
             .replace("__MLS_JSON__", json.dumps(MLS, separators=(",", ":")))
             .replace("__REDFIN_JSON__", json.dumps(REDFIN, separators=(",", ":"))))
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
