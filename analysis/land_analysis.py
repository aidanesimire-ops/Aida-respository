#!/usr/bin/env python3
"""
Vacant-land & dock comps for Fort Lauderdale.

Until now land value was *implied* from improved sales (the SFR structure-vs-land
model). This module adds the real thing: actual vacant-land and boat-dock/dockominium
listings and closings, so land $/sqft is comp-backed, lot geography (point/corner/
cul-de-sac/interior, waterfront, East/West of US-1) is observed rather than inferred,
and zoning/density (single-family vs multifamily vs commercial vs acreage) is priced.

INPUT  : data/raw/land/*.csv  (RLD "Residential Land" single-line exports)
         status is carried in the "St" column, not the filename:
           CS=closed sale, PS=pending, A=active, AC=active w/contract,
           X=expired, C=cancelled, W=withdrawn, T=temp-off
OUTPUT : data/processed/land_all.csv + data/processed/land_bundle.json

CAVEATS
-------
- The RLD export spans a wider geography than the improved-residential MLS (it
  includes far-west Broward acreage and other municipalities). Neighborhood and
  geography medians are therefore computed on the Fort Lauderdale subset (canonical
  neighborhoods that also appear in the improved data) so the prime market isn't
  dragged by rural acreage. Acreage-band and dock views use the whole set.
- No close dates in the export, so land "absorption" is a coarse active:sold ratio,
  not months-of-supply. Labeled as such.
- Land $/sqft has enormous natural spread (a $2/sqft 10-acre western parcel vs a
  $800/sqft finger-isle lot); medians + IQR are reported, never means.
"""
from __future__ import annotations
import glob
import json
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mls_normalize as M  # reuse _num + neighborhood canonicalization
from config import CFG

ROOT = os.path.dirname(HERE)
RAWDIR = CFG.folder("land")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)

ST_GROUP = CFG.asset("land")["status_map"]
_LC = CFG.cols("land")
FAILED = {"Expired", "Withdrawn", "Cancelled", "TempOff"}
LIVE = {"Active", "Pending"}

_LAND = CFG.thr("land")
MIN_NBHD_SOLD = _LAND["min_nbhd_sold"]          # land comps a neighborhood needs to be reported
PPSF_LO, PPSF_HI = _LAND["ppsf_bounds"]         # plausible land $/sqft band (drop data errors)
SQFT_PER_ACRE = 43560


def _lot_sqft(psqft, acre):
    """Prefer the explicit lot sqft; else convert acreage. Some rows mislabel sqft
    into the acreage field (e.g. 9,776 'acres') -- anything > 50 is really sqft."""
    if pd.notna(psqft) and psqft > 200:
        return float(psqft)
    if pd.notna(acre) and acre > 0:
        return float(acre) if acre > 50 else float(acre) * SQFT_PER_ACRE
    return np.nan


def _density(style, zn):
    """Coarse buildable-density class. 'Style of Property' already carries a zoning
    hint for most rows; fall back to parsing the raw zoning code."""
    s = (str(style) or "").lower()
    if "boat dock" in s or "dockomin" in s:
        return "Dock"
    if "multifamily" in s:
        return "Multifamily"
    if "duplex" in s:
        return "Duplex"
    if "residential" in s:
        return "Single-family"
    z = re.sub(r"[^A-Z0-9]", "", str(zn).upper().replace("¤", ""))
    if z.startswith(("RS", "RSF", "SF", "R1", "RES", "R2")):
        return "Single-family"
    if z.startswith(("RD", "RC", "RMM", "RMS", "RO", "RAC", "RM")):
        return "Multifamily"
    if z.startswith(("B", "CB", "CF", "SMU", "MU")):
        return "Commercial"
    if z.startswith(("AR", "AG", "RR", "A1", "A")):
        return "Acreage / rural"
    return None


ACRE_BANDS = [
    ("Less Than 1/4 Acre", "< 0.25 ac"), ("1/4 To Less Than 1/2 Acre", "0.25–0.5 ac"),
    ("1/2 To Less Than 3/4 Acre", "0.5–0.75 ac"), ("3/4 To Less Than 1 Acre", "0.75–1 ac"),
    ("1 To Less Than 2 Acre", "1–2 ac"), ("2 To Less Than 3 Acre", "2–3 ac"),
    ("3 To Less Than 4 Acre", "3–4 ac"), ("4 To Less Than 5 Acre", "4–5 ac"),
    ("5 To Less Than 10 Acre", "5–10 ac"), ("10 Or More Acre", "10+ ac"),
]
BAND_ORDER = [b for _, b in ACRE_BANDS]


def _acre_band(desc, lot_sqft):
    d = str(desc or "")
    for key, label in ACRE_BANDS:
        if key in d:
            return label
    if pd.notna(lot_sqft):  # fall back to the derived size
        a = lot_sqft / SQFT_PER_ACRE
        edges = [(.25, "< 0.25 ac"), (.5, "0.25–0.5 ac"), (.75, "0.5–0.75 ac"),
                 (1, "0.75–1 ac"), (2, "1–2 ac"), (3, "2–3 ac"), (4, "3–4 ac"),
                 (5, "4–5 ac"), (10, "5–10 ac")]
        for hi, label in edges:
            if a < hi:
                return label
        return "10+ ac"
    return None


def load_clean():
    frames = []
    for path in sorted(glob.glob(os.path.join(RAWDIR, "*.csv"))):
        frames.append(pd.read_csv(path))
    raw = pd.concat(frames, ignore_index=True)
    C = _LC
    df = pd.DataFrame({
        "status": raw[CFG.asset("land")["status_column"]].map(ST_GROUP),
        "mls": raw[C["mls"]].astype(str),
        "area": raw[C["area"]].map(lambda x: re.sub(r"\.0$", "", str(x)) if pd.notna(x) else None),
        "address": raw[C["address"]].astype(str).str.strip(),
        "neighborhood": raw[C["subdivision"]].map(M._canon_neigh),
        "sub_raw": raw[C["subdivision"]].astype(str).str.upper().str.strip(),
        "list_price": raw[C["list_price"]].map(M._num),
        "sale_price": raw[C["sale_price"]].map(M._num),
        "acre": raw[C["acre"]].map(M._num),
        "psqft": raw[C["psqft"]].map(M._num),
        "lot_desc": raw[C["lot_desc"]].astype(str),
        "zn": raw[C["zn"]].astype(str),
        "style": raw[C["style"]].astype(str),
        "ptype": raw[C["ptype"]].astype(str),
        "waterfront": raw[C["waterfront"]].astype(str).str.strip().str.lower().eq("yes"),
        "road": raw[C["road"]].astype(str),
    })
    df = df[df["status"].notna()].copy()
    df["lot_sqft"] = [_lot_sqft(p, a) for p, a in zip(df["psqft"], df["acre"])]
    df["density"] = [_density(s, z) for s, z in zip(df["style"], df["zn"])]
    df["is_dock"] = df["ptype"].str.contains("Dockominium", case=False, na=False) | \
        df["style"].str.contains("Boat Dock", case=False, na=False) | (df["density"] == "Dock")
    df["acre_band"] = [_acre_band(d, s) for d, s in zip(df["lot_desc"], df["lot_sqft"])]
    # the price that defines the listing: sale for closed, list otherwise
    df["value"] = np.where(df["status"] == "Sold", df["sale_price"], df["list_price"])
    df["land_ppsf"] = df["value"] / df["lot_sqft"]
    for flag, key in [("corner", "Corner Lot"), ("cul_de_sac", "Cul-De-Sac"),
                      ("interior", "Interior Lot"), ("irregular", "Irregular"),
                      ("oversized", "Oversized"), ("flood", "Flood Zone"),
                      ("east_us1", "East Of US 1"), ("west_us1", "West Of US 1")]:
        df[flag] = df["lot_desc"].str.contains(key, na=False)
    return df.reset_index(drop=True)


COMMDIR = CFG.folder("commercial_land")


def _sanitize(o):
    """Recursively replace NaN/inf with None so the bundle is valid JSON (JSON.parse
    in the browser rejects the NaN token that json.dump would otherwise emit)."""
    if isinstance(o, float):
        return None if (o != o or o in (float("inf"), float("-inf"))) else o
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(v) for v in o]
    return o


def _med(s):
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return float(s.median()) if len(s) else None


def commercial_land():
    """Commercial / development land (CLD export) -- a thin but high-value FLL segment
    with its own schema (Location + zoning, no subdivision/waterfront). Comps are the
    value here, so the actual sales are listed rather than over-aggregated."""
    paths = sorted(glob.glob(os.path.join(COMMDIR, "*.csv")))
    if not paths:
        return None
    raw = pd.concat([pd.read_csv(p) for p in paths], ignore_index=True)
    C = CFG.cols("commercial_land")
    d = pd.DataFrame({
        "status": raw[CFG.asset("commercial_land")["status_column"]].map(ST_GROUP),
        "area": raw[C["area"]].map(lambda x: re.sub(r"\.0$", "", str(x)) if pd.notna(x) else None),
        "address": raw[C["address"]].astype(str).str.strip(),
        "list_price": raw[C["list_price"]].map(M._num),
        "sale_price": raw[C["sale_price"]].map(M._num),
        "acre": raw[C["acre"]].map(M._num),
        "lotsf": raw[C["lotsf"]].map(M._num),
        "location": raw[C["location"]].astype(str).str.replace("nan", "", regex=False),
        "zn": raw[C["zn"]].astype(str),
        "style": raw[C["style"]].astype(str),
        "ptype": raw[C["ptype"]].astype(str),
        "for_lease": raw[C["for_lease"]].astype(str).str.strip().str.lower().eq("yes"),
    })
    d = d[d["status"].notna()].copy()
    d["lot_sqft"] = [_lot_sqft(l, a) for l, a in zip(d["lotsf"], d["acre"])]
    d["value"] = np.where(d["status"] == "Sold", d["sale_price"], d["list_price"])
    d["ppsf"] = d["value"] / d["lot_sqft"]
    d["density"] = [_density(s, z) for s, z in zip(d["style"], d["zn"])]
    d = d[d["ppsf"].between(0.5, 5000)]

    def rows(sub):
        return [{"address": r["address"], "area": r["area"],
                 "price": int(r["value"]) if pd.notna(r["value"]) else None,
                 "lot_sqft": int(r["lot_sqft"]) if pd.notna(r["lot_sqft"]) else None,
                 "ppsf": round(float(r["ppsf"]), 1) if pd.notna(r["ppsf"]) else None,
                 "zoning": re.sub(r"[¤]", "", str(r["zn"])).strip() or None,
                 "location": str(r["location"]).strip(" ,").replace("nan", "") or None,
                 "for_lease": bool(r["for_lease"])}
                for _, r in sub.iterrows()]

    sold = d[d["status"] == "Sold"].sort_values("value", ascending=False)
    active = d[d["status"] == "Active"].sort_values("value", ascending=False)
    return {
        "n_sold": int(len(sold)), "n_active": int(len(active)),
        "n_failed": int(d["status"].isin(FAILED).sum()),
        "median_ppsf_sold": round(_med(sold["ppsf"]), 1) if len(sold) else None,
        "median_ppsf_active": round(_med(active["ppsf"]), 1) if len(active) else None,
        "per_acre_sold": round(_med(sold["ppsf"]) * SQFT_PER_ACRE) if len(sold) else None,
        "sales": rows(sold), "actives": rows(active.head(25)),
    }


def _fll_set():
    """Neighborhoods that also appear in the improved-residential layer = the Fort
    Lauderdale market proper (keeps rural acreage out of the prime medians)."""
    try:
        with open(os.path.join(PROC, "mls_bundle.json")) as f:
            mb = json.load(f)
        return {n["neighborhood"] for n in mb["neighborhoods"]}, \
               {n["neighborhood"]: n.get("implied_land_ppsf") for n in mb["neighborhoods"]}
    except FileNotFoundError:
        return set(), {}


def main():
    df = load_clean()
    df.to_csv(os.path.join(PROC, "land_all.csv"), index=False)
    fll, implied = _fll_set()

    sold = df[(df["status"] == "Sold") & ~df["is_dock"]
              & df["land_ppsf"].between(PPSF_LO, PPSF_HI)].copy()
    active = df[(df["status"] == "Active") & ~df["is_dock"]].copy()
    failed = df[df["status"].isin(FAILED) & ~df["is_dock"]].copy()
    # "urban" = city-scale lots (< ~1.4 acre); strips the far-west rural acreage that
    # would otherwise drag the size/zoning gradients toward zero.
    URBAN = _LAND["urban_sqft"]
    urban = sold[sold["lot_sqft"] < URBAN]
    # The RLD export is a multi-county South Florida pull; only a fraction is Fort
    # Lauderdale proper. Isolate the FLL subset (neighborhoods in the improved layer)
    # for the headline land value -- that is what's relevant to this dashboard.
    inf = sold[sold["neighborhood"].isin(fll)] if fll else sold.iloc[0:0]

    # ---- land $/sqft by neighborhood (every neighborhood with enough comps) ----
    by_nbhd = []
    for nb, g in sold.groupby("neighborhood"):
        if nb is None or len(g) < MIN_NBHD_SOLD:
            continue
        a = active[active["neighborhood"] == nb]
        fa = failed[failed["neighborhood"] == nb]
        by_nbhd.append({
            "neighborhood": nb,
            "n_sold": int(len(g)),
            "land_ppsf": round(_med(g["land_ppsf"]), 1),
            "ppsf_p25": round(float(g["land_ppsf"].quantile(.25)), 1),
            "ppsf_p75": round(float(g["land_ppsf"].quantile(.75)), 1),
            "median_price": _med(g["value"]),
            "per_acre": round(_med(g["land_ppsf"]) * SQFT_PER_ACRE) if _med(g["land_ppsf"]) else None,
            "waterfront_share": round(float(g["waterfront"].mean()), 2),
            "waterfront_ppsf": _med(g[g["waterfront"]]["land_ppsf"]) if g["waterfront"].any() else None,
            "n_active": int(len(a)),
            "active_ask_ppsf": _med(a["land_ppsf"]) if len(a) else None,
            "n_failed": int(len(fa)),
            "in_improved": nb in fll,
            "implied_land_ppsf": implied.get(nb),
        })
    by_nbhd.sort(key=lambda r: -(r["land_ppsf"] or 0))

    # ---- lot geography ----
    # Waterfront-vs-dry leads on the Fort Lauderdale subset (the relevant premium);
    # the finer lot cuts use the broader urban set (too thin FLL-only) and are labeled.
    def geo_row(label, mask, base, scope):
        g = base[mask]
        m = _med(g["land_ppsf"])
        return {"geo": label, "n": int(len(g)), "land_ppsf": round(m, 1) if m else None,
                "median_price": _med(g["value"]), "scope": scope} if len(g) >= 3 else None
    fbase = inf if len(inf) >= 12 else urban
    fscope = "Fort Lauderdale" if len(inf) >= 12 else "South Florida urban"
    geography = [r for r in [
        geo_row("Waterfront", fbase["waterfront"], fbase, fscope),
        geo_row("Dry lot", ~fbase["waterfront"], fbase, fscope),
        geo_row("Corner lot", urban["corner"], urban, "South Florida urban"),
        geo_row("Interior lot", urban["interior"], urban, "South Florida urban"),
        geo_row("Cul-de-sac", urban["cul_de_sac"], urban, "South Florida urban"),
        geo_row("Oversized", urban["oversized"], urban, "South Florida urban"),
        geo_row("East of US-1", urban["east_us1"], urban, "South Florida urban"),
        geo_row("West of US-1", urban["west_us1"], urban, "South Florida urban"),
    ] if r]

    # ---- zoning / density (urban lots -- higher density = more value per land sqft) ----
    by_zoning = []
    for dens, g in urban.groupby("density"):
        if dens is None or len(g) < 5:
            continue
        by_zoning.append({"density": dens, "n": int(len(g)),
                          "land_ppsf": round(_med(g["land_ppsf"]), 1),
                          "median_price": _med(g["value"])})
    by_zoning.sort(key=lambda r: -(r["land_ppsf"] or 0))

    # ---- acreage bands (whole market -- the size gradient of land) ----
    acreage = []
    for band, g in sold.groupby("acre_band"):
        if band is None or len(g) < 5:
            continue
        acreage.append({"band": band, "n": int(len(g)),
                        "land_ppsf": round(_med(g["land_ppsf"]), 1),
                        "per_acre": round(_med(g["value"] / (g["lot_sqft"] / SQFT_PER_ACRE))),
                        "median_price": _med(g["value"])})
    acreage.sort(key=lambda r: BAND_ORDER.index(r["band"]) if r["band"] in BAND_ORDER else 99)

    # ---- docks / dockominiums ----
    dock_sold = df[df["is_dock"] & (df["status"] == "Sold") & df["value"].gt(1000)].copy()
    dock_active = df[df["is_dock"] & (df["status"] == "Active") & df["list_price"].gt(1000)].copy()
    dock_list = [{"address": r["address"], "neighborhood": r["neighborhood"],
                  "area": r["area"], "price": int(r["value"]),
                  "waterfront": bool(r["waterfront"])}
                 for _, r in dock_sold.sort_values("value", ascending=False).head(25).iterrows()]
    docks = {
        "n_sold": int(len(dock_sold)), "n_active": int(len(dock_active)),
        "median_sold": _med(dock_sold["value"]),
        "min_sold": int(dock_sold["value"].min()) if len(dock_sold) else None,
        "max_sold": int(dock_sold["value"].max()) if len(dock_sold) else None,
        "median_active_ask": _med(dock_active["list_price"]),
        "sales": dock_list,
    }

    # ---- active land inventory (Fort Lauderdale first, then the rest) ----
    act = active.copy()
    act["_fll"] = act["neighborhood"].isin(fll)
    act = act.sort_values(["_fll", "list_price"], ascending=[False, False])
    actives = [{
        "address": r["address"], "neighborhood": r["neighborhood"], "area": r["area"],
        "price": int(r["list_price"]) if pd.notna(r["list_price"]) else None,
        "lot_sqft": int(r["lot_sqft"]) if pd.notna(r["lot_sqft"]) else None,
        "acre": round(float(r["acre"]), 3) if pd.notna(r["acre"]) and r["acre"] < 50 else None,
        "land_ppsf": round(float(r["land_ppsf"]), 1) if pd.notna(r["land_ppsf"])
        and PPSF_LO <= r["land_ppsf"] <= PPSF_HI else None,
        "waterfront": bool(r["waterfront"]), "density": r["density"],
        "geo": ", ".join([x for x, ok in [("Waterfront", r["waterfront"]),
              ("Corner", r["corner"]), ("Cul-de-sac", r["cul_de_sac"]),
              ("Interior", r["interior"]), ("Oversized", r["oversized"])] if ok]) or "—",
        "is_dock": bool(r["is_dock"]),
    } for _, r in act.head(200).iterrows()]

    # ---- implied (hedonic) vs actual (comps) land value, per neighborhood ----
    iva = [{"neighborhood": r["neighborhood"], "actual_ppsf": r["land_ppsf"],
            "implied_ppsf": r["implied_land_ppsf"],
            "gap_pct": round(100 * (r["land_ppsf"] / r["implied_land_ppsf"] - 1))
            if r["implied_land_ppsf"] else None}
           for r in by_nbhd if r["implied_land_ppsf"]]

    bundle = {
        "meta": {
            "n_sold": int(len(sold)), "n_active": int(len(active)),
            "n_failed": int(len(failed)),
            "n_pending": int((df["status"] == "Pending").sum()),
            "n_dock_sold": docks["n_sold"], "n_dock_active": docks["n_active"],
            "n_fll_sold": int(len(inf)),
            "fll_land_ppsf": round(_med(inf["land_ppsf"]), 1) if len(inf) else None,
            "fll_waterfront_ppsf": round(_med(inf[inf["waterfront"]]["land_ppsf"]), 1) if inf["waterfront"].any() else None,
            "fll_dry_ppsf": round(_med(inf[~inf["waterfront"]]["land_ppsf"]), 1) if (~inf["waterfront"]).any() else None,
            "sf_urban_land_ppsf": round(_med(urban["land_ppsf"]), 1) if len(urban) else None,
            "n_neighborhoods": len(by_nbhd),
            "n_fll_neighborhoods": sum(1 for r in by_nbhd if r["in_improved"]),
            "note": "Comp-backed land $/sqft. The RLD export is a multi-county South Florida "
                    "pull; the Fort Lauderdale figures (n_fll_sold) are the relevant headline, "
                    "the rest is context. Size/zoning gradients use urban lots (< ~1.4 acre). "
                    "No close dates, so supply is a coarse active:sold ratio.",
        },
        "by_neighborhood": by_nbhd,
        "geography": geography,
        "by_zoning": by_zoning,
        "acreage": acreage,
        "docks": docks,
        "actives": actives,
        "implied_vs_actual": iva,
        "commercial": commercial_land(),
    }
    with open(os.path.join(PROC, "land_bundle.json"), "w") as f:
        json.dump(_sanitize(bundle), f, separators=(",", ":"))

    m = bundle["meta"]
    print(f"Land: {m['n_sold']} sold comps ({m['n_fll_sold']} Fort Lauderdale), {m['n_active']} active, "
          f"{m['n_failed']} failed, {m['n_dock_sold']} dock sales")
    print(f"  Fort Lauderdale land ${m['fll_land_ppsf']}/sqft "
          f"(waterfront ${m['fll_waterfront_ppsf']} vs dry ${m['fll_dry_ppsf']}) · "
          f"{m['n_fll_neighborhoods']}/{m['n_neighborhoods']} FLL neighborhoods · "
          f"SF-wide urban ${m['sf_urban_land_ppsf']}/sqft")
    if by_nbhd:
        for r in by_nbhd[:6]:
            iv = f" | implied ${r['implied_land_ppsf']:.0f}" if r["implied_land_ppsf"] else ""
            print(f"   {r['neighborhood']:22s} ${r['land_ppsf']:>6.0f}/sqft  "
                  f"n={r['n_sold']:<3d} wf {int(r['waterfront_share']*100)}%{iv}")


if __name__ == "__main__":
    main()
