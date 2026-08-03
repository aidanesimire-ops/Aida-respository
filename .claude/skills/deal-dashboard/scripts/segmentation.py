#!/usr/bin/env python3
"""
Micro-segmentation — the market's internal structure, per neighborhood.

Within each neighborhood, how do closed sales split by asset type, price bracket,
floor plan (bed count / bed-bath config) and square-footage band — and what SHARE of
the market does each slice hold, both of the whole neighborhood and *within* an asset
class or a price bracket? Plus median $/sqft, price and size for every slice.

Answers questions like: "In Rio Vista, what % of $2–3M sales are 4-bed single-family,
and what do they run per foot?"

Input : mls_all_valued.csv (per-home closed + live). Output: segmentation_bundle.json
(nested per-neighborhood for the dashboard/PDF + a flat, filterable table for Excel).
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
SEG = CFG.segmentation
MIN_NB = SEG["min_nbhd_sold"]
MIN_CELL = SEG["min_cell"]


def _band_labels(edges):
    def m(x):
        return f"${x/1e6:g}M" if x >= 1e6 else f"${round(x/1e3)}K"
    out = []
    full = [0] + list(edges) + [float("inf")]
    for lo, hi in zip(full[:-1], full[1:]):
        out.append(f"<{m(hi)}" if lo == 0 else f"{m(lo)}+" if hi == float("inf") else f"{m(lo)}–{m(hi)}")
    return full, out


def _sqft_labels(edges):
    def m(x):
        return f"{x/1000:g}k" if x >= 1000 else str(int(x))
    full = [0] + list(edges) + [float("inf")]
    out = []
    for lo, hi in zip(full[:-1], full[1:]):
        out.append(f"<{m(hi)} ft²" if lo == 0 else f"{m(lo)}+ ft²" if hi == float("inf")
                   else f"{m(lo)}–{m(hi)} ft²")
    return full, out


PB_EDGES, PB_LABELS = _band_labels(SEG["price_bands"])
SB_EDGES, SB_LABELS = _sqft_labels(SEG["sqft_bands"])


def _beds_label(b):
    if pd.isna(b) or b <= 0:
        return None
    b = int(b)
    return "6+ bed" if b >= 6 else f"{b} bed"


def _bedbath(b, ba):
    if pd.isna(b) or b <= 0 or pd.isna(ba):
        return None
    return f"{int(b)}BR/{ba:g}BA"


def _med(s, col):
    s = pd.to_numeric(s[col], errors="coerce").dropna()
    return round(float(s.median())) if len(s) >= MIN_CELL else None


def _slices(df, key, total):
    """Count + share + medians for each value of `key`, share of `total`."""
    out = []
    for val, g in df.groupby(key, observed=True):
        if val is None or (isinstance(val, float) and pd.isna(val)):
            continue
        out.append({"key": str(val), "n": int(len(g)),
                    "share": round(100 * len(g) / total, 1) if total else None,
                    "median_ppsf": _med(g, "actual_ppsf"), "median_price": _med(g, "price"),
                    "median_sqft": _med(g, "sqft")})
    return out


def segment_neighborhood(df, name):
    n = len(df)
    if n < MIN_NB:
        return None
    TYPE_ORDER = {"Single Family": 0, "Condo": 1, "Townhouse": 2, "Villa": 3}
    # by asset type, with the floor-plan (beds) mix WITHIN each type
    by_type = []
    for t in sorted(df["ptype"].dropna().unique(), key=lambda x: TYPE_ORDER.get(x, 9)):
        g = df[df["ptype"] == t]
        beds_mix = []
        for bl, bg in g.groupby("beds_lbl", observed=True):
            if bl:
                beds_mix.append({"key": bl, "n": int(len(bg)),
                                 "share": round(100 * len(bg) / len(g), 1),
                                 "median_ppsf": _med(bg, "actual_ppsf")})
        beds_mix.sort(key=lambda z: -z["n"])
        by_type.append({"key": t, "n": int(len(g)), "share": round(100 * len(g) / n, 1),
                        "median_ppsf": _med(g, "actual_ppsf"), "median_price": _med(g, "price"),
                        "median_sqft": _med(g, "sqft"), "beds_mix": beds_mix})

    # by price bracket, with the asset-type mix WITHIN each bracket
    by_band = []
    for b in PB_LABELS:
        g = df[df["price_band"] == b]
        if not len(g):
            continue
        type_mix = [{"key": t, "n": int(len(tg)), "share": round(100 * len(tg) / len(g), 1)}
                    for t, tg in g.groupby("ptype", observed=True)]
        type_mix.sort(key=lambda z: -z["n"])
        by_band.append({"key": b, "n": int(len(g)), "share": round(100 * len(g) / n, 1),
                        "median_ppsf": _med(g, "actual_ppsf"), "median_sqft": _med(g, "sqft"),
                        "median_price": _med(g, "price"), "type_mix": type_mix})

    by_beds = sorted(_slices(df, "beds_lbl", n),
                     key=lambda z: int(z["key"].replace("+ bed", "").replace(" bed", "")))
    by_sqft = [s for lab in SB_LABELS for s in _slices(df[df["sqft_band"] == lab], "sqft_band", n)]

    return {"neighborhood": name, "n_sold": n, "by_type": by_type, "by_band": by_band,
            "by_beds": by_beds, "by_sqft": by_sqft}


def main():
    df = pd.read_csv(os.path.join(PROC, "mls_all_valued.csv"))
    sold = df[(df["status"] == "Sold") & df["price"].gt(0) & df["sqft"].gt(0)].copy()
    sold["price_band"] = pd.cut(sold["price"], PB_EDGES, labels=PB_LABELS, right=False)
    sold["sqft_band"] = pd.cut(sold["sqft"], SB_EDGES, labels=SB_LABELS, right=False)
    sold["beds_lbl"] = sold["beds"].map(_beds_label)
    sold["bedbath"] = [_bedbath(b, ba) for b, ba in zip(sold["beds"], sold["baths"])]

    nbhds = []
    for name, g in sold.groupby("neighborhood"):
        seg = segment_neighborhood(g, name)
        if seg:
            nbhds.append(seg)
    nbhds.sort(key=lambda z: -z["n_sold"])
    citywide = segment_neighborhood(sold, "Citywide")

    # ---- flat, filterable table for Excel: one row per slice ----
    flat = []

    def add_flat(nb, dim, cat, within, rows, extra_cols=True):
        for r in rows:
            flat.append({
                "neighborhood": nb, "dimension": dim, "category": r["key"], "within": within,
                "n": r["n"], "share_pct": r["share"],
                "median_ppsf": r.get("median_ppsf"), "median_price": r.get("median_price"),
                "median_sqft": r.get("median_sqft")})

    for seg in [citywide] + nbhds:
        if not seg:
            continue
        nb = seg["neighborhood"]
        add_flat(nb, "Asset type", None, "neighborhood", seg["by_type"])
        for t in seg["by_type"]:
            add_flat(nb, "Floor plan (beds) within type", None, t["key"],
                     [{**b, "median_price": None, "median_sqft": None} for b in t["beds_mix"]])
        add_flat(nb, "Price bracket", None, "neighborhood", seg["by_band"])
        for b in seg["by_band"]:
            add_flat(nb, "Asset type within bracket", None, b["key"],
                     [{**t, "median_ppsf": None, "median_price": None, "median_sqft": None}
                      for t in b["type_mix"]])
        add_flat(nb, "Floor plan (beds)", None, "neighborhood", seg["by_beds"])
        add_flat(nb, "SqFt band", None, "neighborhood", seg["by_sqft"])

    bundle = {
        "meta": {"market": CFG.market["name"], "n_neighborhoods": len(nbhds),
                 "min_nbhd_sold": MIN_NB, "n_sold": int(len(sold)),
                 "price_bands": PB_LABELS, "sqft_bands": SB_LABELS,
                 "note": "Closed-sale market structure within each neighborhood. Shares are % of "
                         "sold count at the stated level (of the neighborhood, of an asset class, "
                         "or of a price bracket). Medians shown where a slice has >= "
                         f"{MIN_CELL} sales."},
        "citywide": citywide, "neighborhoods": nbhds, "flat": flat,
    }
    with open(os.path.join(PROC, "segmentation_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    print(f"Segmentation: {len(nbhds)} neighborhoods segmented ({len(flat)} slice rows) "
          f"from {len(sold):,} closed sales.")
    # sample: top neighborhood type + band mix
    if nbhds:
        s = nbhds[0]
        tm = ", ".join(f"{t['key']} {t['share']:.0f}%" for t in s["by_type"])
        print(f"   {s['neighborhood']} (n={s['n_sold']}): {tm}")


if __name__ == "__main__":
    main()
