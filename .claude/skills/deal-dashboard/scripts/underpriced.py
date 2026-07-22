#!/usr/bin/env python3
"""
Underpriced opportunities: find live listings priced below comp-supported value and
EXPLAIN WHY, from the data. This is the mispricing-hunting page.

A listing is flagged only when it's below a COMP-BACKED benchmark (its street's recent
sales when there are >=3, otherwise its neighborhood's per-home model where the
neighborhood has real sold volume). For each, it computes the dollar opportunity and
generates data-driven reasons:
  - how far below the comps it is
  - waterfront home priced like a dry lot
  - new construction priced like an existing home
  - land value alone covers much of the ask
  - its price band sells higher in this neighborhood

Reads street_active_deals.csv + mls_all_valued.csv + mls_bundle.json + high_ticket bands.
Output: underpriced_opportunities.csv + underpriced_bundle.json
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")

MIN_UNDER = 8          # asking must be >= this % below benchmark to flag
MIN_STREET_COMPS = 3
MIN_NBHD_SOLD = 10
BAND_EDGES = [0, 1e6, 2e6, 3e6, 5e6, 10e6, np.inf]
BAND_LABELS = ["<$1M", "$1M–$2M", "$2M–$3M", "$3M–$5M", "$5M–$10M", "$10M+"]


def _load(n):
    with open(os.path.join(PROC, n)) as f:
        return json.load(f)


def main():
    deals = pd.read_csv(os.path.join(PROC, "street_active_deals.csv"))
    valued = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    feats = valued[["address", "age", "lot_sqft", "is_new", "year_built", "beds"]].drop_duplicates("address")
    d = deals.merge(feats, on="address", how="left")

    nbh = {n["neighborhood"]: n for n in _load("mls_bundle.json")["neighborhoods"]}
    band_sold = {(b["neighborhood"], b["band"]): b for b in _load("high_ticket_bundle.json")["band_neighborhood"]}

    d["band"] = pd.cut(d["list_price"], BAND_EDGES, labels=BAND_LABELS, right=False)

    rows = []
    for _, r in d.iterrows():
        nb = nbh.get(r["neighborhood"], {})
        street_ok = r["street_comps"] >= MIN_STREET_COMPS
        nbhd_ok = (nb.get("sold_n") or 0) >= MIN_NBHD_SOLD
        if not (street_ok or nbhd_ok):
            continue
        bench = r["street_value_ppsf"]          # street-comp adjusted model value
        if pd.isna(bench) or bench <= 0:
            continue
        ask = r["ask_ppsf"]
        under = (bench / ask - 1) * 100          # how far below supported (%)
        # Real deal range only: 8-40% under. Beyond 40% is almost always unit-level
        # heterogeneity (condo floor/view/reno) or a data quirk, not a bargain.
        if not (MIN_UNDER <= under <= 40):
            continue
        # Condos in a single tower vary too much floor-to-floor for a building median to
        # be a clean comp -- keep them, but cap tighter and mark them for verification.
        is_condo = r["ptype"] in ("Condo", "Co-Op")
        if is_condo and under > 25:
            continue
        basis = (f"{int(r['street_comps'])} sales on {r['street']}" if street_ok
                 else f"{int(nb.get('sold_n',0))} sales in {r['neighborhood']}")
        opp_total = round((bench - ask) * r["sqft"], -3)

        reasons = [f"Asking ${ask:,.0f}/sqft — {under:.0f}% under supported ${bench:,.0f}/sqft "
                   f"({basis})."]
        # waterfront priced like a dry lot
        wf = nb.get("waterfront_ppsf")
        if r.get("waterfront") and wf and ask < wf * 0.9:
            reasons.append(f"Waterfront, yet priced below the area's waterfront median "
                           f"(${wf:,.0f}/sqft).")
        # new construction priced like existing
        if r.get("is_new") and nb.get("existing_ppsf") and ask < (nb.get("new_ppsf") or 1e9):
            yb = f" (built {int(r['year_built'])})" if pd.notna(r.get("year_built")) else ""
            reasons.append(f"Newer construction{yb} priced near existing-home levels "
                           f"(${nb['existing_ppsf']:,.0f}/sqft).")
        # land value alone
        land = nb.get("implied_land_ppsf")
        if r["ptype"] == "Single Family" and pd.notna(r.get("lot_sqft")) and land:
            land_total = land * r["lot_sqft"]
            if land_total > 0.55 * r["list_price"]:
                reasons.append(f"~{int(r['lot_sqft']):,} sqft lot — land alone is worth "
                               f"~${land_total:,.0f} of the ${r['list_price']:,.0f} ask.")
        # band sells higher here
        bs = band_sold.get((r["neighborhood"], str(r["band"])))
        if bs and bs.get("sold_ppsf") and bs["sold_ppsf"] > ask * 1.08:
            reasons.append(f"In {r['neighborhood']}'s {r['band']} band, homes sell around "
                           f"${bs['sold_ppsf']:,.0f}/sqft.")
        if is_condo:
            reasons.append("Condo — confirm floor, view and condition; unit-level features "
                           "aren't in the model.")
        conf = ("Condo — verify" if is_condo else
                ("High" if street_ok and r["street_comps"] >= 5 else
                 ("Medium" if street_ok else "Neighborhood")))

        rows.append({
            "band": str(r["band"]), "address": r["address"], "street": r["street"],
            "neighborhood": r["neighborhood"], "geo_type": r["geo_type"], "ptype": r["ptype"],
            "sqft": int(r["sqft"]), "waterfront": bool(r.get("waterfront")),
            "list_price": int(r["list_price"]), "ask_ppsf": round(ask, 0),
            "supported_ppsf": round(bench, 0),
            "supported_value": int(round(bench * r["sqft"], -3)),
            "under_pct": round(under, 1), "opportunity": int(opp_total),
            "street_comps": int(r["street_comps"]),
            "confidence": conf,
            "reasons": reasons,
        })

    df = pd.DataFrame(rows).sort_values("opportunity", ascending=False)
    flat = df.copy()
    flat["reasons"] = flat["reasons"].map(lambda xs: " | ".join(xs))
    flat.to_csv(os.path.join(PROC, "underpriced_opportunities.csv"), index=False)

    by_band = (df.groupby("band", observed=True)
               .agg(n=("address", "size"), median_under=("under_pct", "median"),
                    total_opportunity=("opportunity", "sum")).reset_index())
    by_nbhd = (df.groupby("neighborhood").agg(n=("address", "size"),
               total_opportunity=("opportunity", "sum"),
               median_under=("under_pct", "median")).reset_index()
               .sort_values("total_opportunity", ascending=False))

    bundle = {
        "meta": {
            "n": int(len(df)),
            "total_opportunity": int(df["opportunity"].sum()),
            "min_under_pct": MIN_UNDER,
        },
        "by_band": json.loads(by_band.to_json(orient="records")),
        "by_neighborhood": json.loads(by_nbhd.head(25).to_json(orient="records")),
        "listings": json.loads(df.head(400).to_json(orient="records")),
    }
    with open(os.path.join(PROC, "underpriced_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    m = bundle["meta"]
    print(f"Underpriced opportunities: {m['n']} listings | "
          f"${m['total_opportunity']/1e6:.0f}M total gap to supported value")
    for _, r in df.head(5).iterrows():
        print(f"  ${r['opportunity']/1e6:>5.1f}M  {r['address'][:34]:34s} {r['neighborhood'][:16]:16s} "
              f"{r['under_pct']:.0f}% under  [{r['confidence']}]")


if __name__ == "__main__":
    main()
