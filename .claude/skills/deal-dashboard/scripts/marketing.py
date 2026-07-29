#!/usr/bin/env python3
"""
Marketing Kit — turn the analysis into copy-ready content you can actually send.

Everywhere else in this project is *analysis*; this module is *output you paste*. For
each neighborhood it composes a market-snapshot paragraph (for emails / CMAs / posts),
seller talking points, a punchy shareable stat, a pricing (CMA) line, and the live buyer
opportunities in that area. It also writes a citywide "market pulse" blurb + stat cards,
and a ready outreach line for every listing prospect.

Consumes the bundles the rest of the pipeline already produced. No new data.
Output: marketing_bundle.json  (rendered in the dashboard "Marketing" card + Excel tab).
"""
from __future__ import annotations
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
MARKET = CFG.market["name"]


def _load(name):
    try:
        with open(os.path.join(PROC, name)) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _usd(v):
    return f"${v:,.0f}" if v not in (None, "") else None


def _pct(v, plus=True):
    if v is None:
        return None
    return f"{'+' if plus and v >= 0 else ''}{v:.0f}%"


def _market_condition(nb, absorb):
    """A plain sentence on how the neighborhood is trending, from absorption."""
    if not absorb:
        return None
    rows = [r for r in absorb.get("by_band_neighborhood", []) if r["neighborhood"] == nb]
    if not rows:
        return None
    mk = {}
    for r in rows:
        if r.get("market"):
            mk[r["market"]] = mk.get(r["market"], 0) + 1
    if not mk:
        return None
    dom = max(mk, key=mk.get)
    phrase = {"Seller's market": "a seller's market — inventory moves quickly",
              "Balanced": "a balanced market",
              "Buyer's market": "a buyer's market — buyers have negotiating room",
              "Deep buyer's market": "a deep buyer's market — well-supplied, room to negotiate"}
    return phrase.get(dom)


def neighborhood_kit(r, n_total, profiles, premiums, absorb, under_by_nb):
    nb = r["neighborhood"]
    norm, vs = r.get("norm_ppsf"), r.get("vs_city_pct")
    wf, dry = r.get("waterfront_ppsf"), r.get("dry_ppsf")
    price, disc = r.get("median_sale_price"), r.get("median_discount_pct")
    appr, newp = r.get("appreciation_since_2020"), r.get("new_premium_pct")

    # ---- market snapshot paragraph ----
    s = []
    if norm:
        rank = r.get("rank")
        tier = (f"ranks #{rank} of {n_total} {MARKET} neighborhoods by normalized value"
                if rank else "is one to watch")
        vtxt = f" — {_pct(vs)} vs the citywide average" if vs is not None else ""
        s.append(f"{nb} {tier}, at about {_usd(norm)}/sqft{vtxt}.")
    if wf and dry:
        s.append(f"Waterfront homes trade around {_usd(wf)}/sqft versus {_usd(dry)}/sqft on "
                 "dry lots — the water is the premium.")
    if price:
        d = f", about {disc:.0f}% under asking" if disc else ""
        s.append(f"The typical home last sold near {_usd(price)}{d}.")
    if appr is not None:
        s.append(f"Values are up roughly {_pct(appr)} since 2020.")
    if newp is not None and abs(newp) >= 3:
        s.append(f"New construction commands about a {_pct(newp)} premium over comparable "
                 "existing homes.")
    cond = _market_condition(nb, absorb)
    if cond:
        s.append(f"Today it reads as {cond}.")
    snapshot = " ".join(s)

    # ---- pricing / CMA line ----
    cma = None
    ask, should = r.get("asking_ppsf"), r.get("should_be_ppsf")
    adj = r.get("suggested_adjust_pct")
    if should and ask:
        move = (f" — a {_pct(adj)} adjustment from where inventory is currently asking "
                f"({_usd(ask)}/sqft)") if adj else ""
        cma = (f"Recent comparable sales in {nb} support about {_usd(should)}/sqft{move}. "
               "Priced to the comps, not to hope.")

    # ---- shareable stat (one punchy line) ----
    share = None
    if appr is not None and appr >= 5:
        extra = f" Waterfront now averages {_usd(wf)}/sqft." if wf else ""
        share = f"📈 {nb} is up {_pct(appr)} since 2020.{extra}"
    elif wf and dry:
        prem = round((wf / dry - 1) * 100) if dry else None
        share = (f"🌊 In {nb}, waterfront runs about {_usd(wf)}/sqft"
                 + (f" — a {prem:+d}% premium over dry lots." if prem else "."))
    elif vs is not None:
        share = f"📍 {nb} prices about {_pct(vs)} vs the {MARKET} average, at {_usd(norm)}/sqft."

    # ---- talking points (reuse the generated profile bullets) ----
    prof = profiles.get(nb, {})
    tps = prof.get("talking_points", [])[:6]

    # ---- live buyer opportunities in this neighborhood ----
    opps = []
    for o in under_by_nb.get(nb, [])[:3]:
        opps.append({
            "address": o["address"], "list_price": o["list_price"],
            "under_pct": o["under_pct"], "opportunity": o["opportunity"],
            "line": (f"{o['address']} — listed {_usd(o['list_price'])}, asking "
                     f"{_usd(o['ask_ppsf'])}/sqft vs {_usd(o['supported_ppsf'])}/sqft "
                     f"supported ({o['under_pct']:.0f}% under, ~{_usd(o['opportunity'])} "
                     "of value on paper). Verify condition.")})

    return {"neighborhood": nb, "rank": r.get("rank"), "geo_type": r.get("geo_type"),
            "snapshot": snapshot, "cma_line": cma, "shareable": share,
            "talking_points": tps, "opportunities": opps}


def main():
    master = _load("master_bundle.json")
    mls = _load("mls_bundle.json")
    time_b = _load("time_bundle.json")
    absorb = _load("absorption_bundle.json")
    under = _load("underpriced_bundle.json")
    seller = _load("seller_bundle.json")
    back = _load("backtest_bundle.json")
    if not master or not mls:
        raise SystemExit("Run the pipeline first (needs master + mls bundles).")

    profiles = {p["neighborhood"]: p for p in mls.get("profiles", [])}
    premiums = mls["meta"]["premiums"]
    nbs = master["neighborhoods"]
    n_total = len(nbs)

    under_by_nb = {}
    for o in (under or {}).get("listings", []):
        under_by_nb.setdefault(o["neighborhood"], []).append(o)

    kits = [neighborhood_kit(r, n_total, profiles, premiums, absorb, under_by_nb)
            for r in nbs]

    # ---- citywide market pulse ----
    tm = (time_b or {}).get("meta", {})
    pulse_bits = []
    if tm.get("city_pct_since_2020") is not None:
        pulse_bits.append(
            f"The {MARKET} market is up about {tm['city_pct_since_2020']:.0f}% since 2020 "
            f"(${tm.get('city_2020_ppsf')}→${tm.get('city_now_ppsf')}/sqft)")
    if tm.get("fastest_dom"):
        pulse_bits.append(
            f"days-on-market bottomed near {tm['fastest_dom']:.0f} in the 2022 frenzy and "
            "buyers now negotiate again")
    pulse_bits.append(f"waterfront is worth about +{premiums['waterfront_pct']:.0f}% per foot, "
                      f"new construction about +{premiums['new_construction_pct']:.0f}%")
    market_pulse = ". ".join(b[0].upper() + b[1:] for b in pulse_bits) + "."

    # ---- stat cards (punchy, shareable) ----
    top = sorted(nbs, key=lambda r: -(r.get("norm_ppsf") or 0))[:3]
    cards = [
        {"label": "Waterfront premium", "value": f"+{premiums['waterfront_pct']:.0f}%",
         "note": "per foot, all else equal"},
        {"label": "Market since 2020",
         "value": (f"+{tm.get('city_pct_since_2020', 0):.0f}%" if tm else "—"),
         "note": "citywide, quality-adjusted"},
        {"label": "Most valuable",
         "value": top[0]["neighborhood"] if top else "—",
         "note": f"{_usd(top[0].get('norm_ppsf'))}/sqft" if top else ""},
        {"label": "Typical discount",
         "value": (f"{_wavg(nbs):.0f}%"),
         "note": "list-to-sale on closed homes"},
    ]
    if back:
        cards.append({"label": "Model accuracy", "value": f"±{back['overall']['mdape']:.0f}%",
                      "note": f"median, out-of-sample ({back['meta']['n_scored']:,} sales)"})

    # ---- prospect outreach lines ----
    prospects = []
    for r in (seller or {}).get("failed", [])[:120]:
        prospects.append({
            "address": r["address"], "neighborhood": r["neighborhood"],
            "status": r.get("status"), "band": r.get("band"),
            "asked": r.get("asked"), "suggested_list": r.get("suggested_list"),
            "line": (f"I noticed {r['address']} came off the market. It was asking "
                     f"{_usd(r.get('asked'))}; comparable {r['neighborhood']} sales support "
                     f"closer to {_usd(r.get('suggested_list'))}. I'd love to walk you "
                     "through the data behind a pricing strategy that actually sells.")})

    bundle = {
        "meta": {"market": MARKET, "n_neighborhoods": n_total,
                 "n_prospects": len(prospects),
                 "accuracy": (back or {}).get("meta", {}).get("headline"),
                 "note": "Copy-ready, data-backed content. Figures are model-normalized "
                         "screening signals — confirm specifics before publishing."},
        "market_pulse": market_pulse,
        "stat_cards": cards,
        "neighborhoods": kits,
        "prospects": prospects,
    }
    with open(os.path.join(PROC, "marketing_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"Marketing kit: {n_total} neighborhood write-ups, {len(cards)} stat cards, "
          f"{len(prospects)} prospect outreach lines.")


def _wavg(nbs):
    num = sum((r.get("median_discount_pct") or 0) * (r.get("sold_n") or 0) for r in nbs)
    den = sum((r.get("sold_n") or 0) for r in nbs if r.get("median_discount_pct") is not None)
    return num / den if den else 0.0


if __name__ == "__main__":
    main()
