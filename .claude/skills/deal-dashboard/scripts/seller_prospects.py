#!/usr/bin/env python3
"""
Seller / listing-prospect engine: the owners to call for a listing.

Two lists, both >=$1M and comp-backed (neighborhood with real sold volume):
  1. FAILED listings (expired / withdrawn / cancelled / temp-off) -- owners who tried
     and couldn't. For each: what they asked, what the comps support, how far over, and
     the suggested list that would actually move it. Your listing-appointment pitch.
  2. OVERPRICED actives -- currently listed well above comps, i.e. likely to become
     tomorrow's expired. Approach for a price-reduction / relist conversation.

Reads mls_all_valued.csv + mls_bundle.json.
Output: seller_prospects_failed.csv, seller_prospects_overpriced_active.csv, seller_bundle.json
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
MIN_TICKET = CFG.thr("high_ticket")
MIN_NBHD_SOLD = CFG.thr("min_nbhd_sold")
MIN_OVER = CFG.thr("min_over_pct")     # >= this % over supported = overpricing story
MAX_OVER = CFG.thr("max_over_pct")     # beyond this the model can't value it (trophy) -- skip
EDGES, LABELS = CFG.full_bands()
FAILED = {"Expired", "Withdrawn", "Cancelled", "TempOff"}


def _load_nbh():
    with open(os.path.join(PROC, "mls_bundle.json")) as f:
        return {n["neighborhood"]: n for n in json.load(f)["neighborhoods"]}


def _build(df, nbh, statuses):
    d = df[df["status"].isin(statuses) & (df["price"] >= MIN_TICKET) & df["pred_ppsf"].gt(0)].copy()
    d["band"] = pd.cut(d["price"], EDGES, labels=LABELS, right=False)
    rows = []
    for _, r in d.iterrows():
        nb = nbh.get(r["neighborhood"], {})
        if (nb.get("sold_n") or 0) < MIN_NBHD_SOLD:
            continue
        over = (r["actual_ppsf"] / r["pred_ppsf"] - 1) * 100
        if not (MIN_OVER <= over <= MAX_OVER):
            continue
        suggested = int(round(r["pred_ppsf"] * r["sqft"], -3))
        sold_med = nb.get("sold_ppsf_median")
        rows.append({
            "status": r["status"], "band": str(r["band"]), "address": r["address"],
            "neighborhood": r["neighborhood"], "ptype": r["ptype"], "sqft": int(r["sqft"]),
            "asked": int(r["price"]), "ask_ppsf": round(r["actual_ppsf"], 0),
            "supported_ppsf": round(r["pred_ppsf"], 0),
            "over_pct": round(over, 1),
            "suggested_list": suggested,
            "reduce_by": int(round(r["price"] - suggested, -3)),
            "pitch": (f"Listed {over:.0f}% over supported value — comparable {r['neighborhood']} "
                      f"homes sell near ${sold_med:,.0f}/sqft. Suggested list ${suggested:,.0f}."
                      if sold_med else
                      f"Listed {over:.0f}% over supported value. Suggested list ${suggested:,.0f}."),
        })
    return pd.DataFrame(rows).sort_values("asked", ascending=False)


def main():
    df = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    nbh = _load_nbh()
    failed = _build(df, nbh, FAILED)
    active = _build(df, nbh, {"Active", "Pending"})

    failed.to_csv(os.path.join(PROC, "seller_prospects_failed.csv"), index=False)
    active.to_csv(os.path.join(PROC, "seller_prospects_overpriced_active.csv"), index=False)

    bundle = {
        "meta": {
            "n_failed": int(len(failed)), "n_overpriced_active": int(len(active)),
            "min_ticket": MIN_TICKET,
            "failed_over_10m": int((failed["band"] == "$10M+").sum()) if len(failed) else 0,
        },
        "failed": json.loads(failed.head(300).to_json(orient="records")),
        "overpriced_active": json.loads(active.head(300).to_json(orient="records")),
    }
    with open(os.path.join(PROC, "seller_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))

    print(f"Seller prospects >= ${MIN_TICKET/1e6:.0f}M: {len(failed)} failed-listing owners, "
          f"{len(active)} overpriced actives")
    for _, r in failed.head(4).iterrows():
        print(f"  {r['status']:9s} {r['address'][:30]:30s} {r['neighborhood'][:16]:16s} "
              f"asked ${r['asked']/1e6:.1f}M, {r['over_pct']:.0f}% over -> list ${r['suggested_list']/1e6:.1f}M")


if __name__ == "__main__":
    main()
