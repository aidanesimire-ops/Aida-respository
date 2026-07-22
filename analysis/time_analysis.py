#!/usr/bin/env python3
"""
Time contextualization (2020 -> present) from the Redfin neighborhood layer.

The MLS export has no dates, so the trajectory comes from Redfin's monthly
neighborhood data (All Residential, 90-day rolling). Produces:

  - market_timeline : citywide monthly PPSF / days-on-market / sale-to-list / sales
  - neighborhood_ppsf : per-neighborhood monthly PPSF series (for the explorer)
  - shifts : per-neighborhood 2020 -> peak -> now change table

Output: data/processed/time_bundle.json  (consumed by charts, dashboard, report)
"""
from __future__ import annotations
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, "data", "raw", "redfin_fll_neighborhoods.tsv")
PROC = os.path.join(ROOT, "data", "processed")
START = "2020-01-01"
MIN_MONTHS = 10          # min monthly obs for a neighborhood to enter the shift table
NOW_WINDOW = 6           # "now" = mean of the last N months
PTYPE = "All Residential"


def _wmean(v, w):
    m = v.notna() & w.notna() & (w > 0)
    return float(np.average(v[m], weights=w[m])) if m.sum() else np.nan


def load():
    df = pd.read_csv(RAW, sep="\t", na_values=["NA", ""], low_memory=False)
    df["period"] = pd.to_datetime(df["PERIOD_BEGIN"])
    df["month"] = df["period"].dt.strftime("%Y-%m")
    df["nb"] = (df["REGION"].str.replace(r"^Fort Lauderdale, FL - ", "", regex=True)
                .str.strip())
    df = df[(df["PROPERTY_TYPE"] == PTYPE) & (df["period"] >= START)]
    return df.rename(columns={"MEDIAN_PPSF": "ppsf", "MEDIAN_DOM": "dom",
                              "AVG_SALE_TO_LIST": "s2l", "HOMES_SOLD": "sold"})


def market_timeline(df):
    rows = []
    for m, g in df.groupby("month"):
        rows.append({
            "month": m,
            "ppsf": round(_wmean(g["ppsf"], g["sold"]), 1),
            "dom": round(_wmean(g["dom"], g["sold"]), 1),
            "s2l": round(_wmean(g["s2l"], g["sold"]), 4),
            "sold": int(g["sold"].sum()),
        })
    rows.sort(key=lambda r: r["month"])
    return rows


def neighborhood_series(df, months):
    """Per-neighborhood monthly PPSF aligned to the master month axis.
    Single-sale months are dropped and a 3-month rolling median is applied so a
    lone luxury sale can't spike a thin neighborhood's line."""
    out = {}
    for nb, g in df.groupby("nb"):
        g = g[g["sold"] >= 2].sort_values("month")
        if g["ppsf"].notna().sum() < MIN_MONTHS:
            continue
        g = g.assign(sm=g["ppsf"].rolling(3, min_periods=1, center=True).median())
        s = g.set_index("month")["sm"]
        out[nb] = [None if (m not in s.index or pd.isna(s[m])) else round(float(s[m]), 1)
                   for m in months]
    return out


def shifts(df):
    rows = []
    now_cut = sorted(df["month"].unique())[-NOW_WINDOW:]
    for nb, g in df.groupby("nb"):
        g = g.sort_values("month")
        if g["ppsf"].notna().sum() < MIN_MONTHS:
            continue
        y2020 = g[g["period"].dt.year == 2020]
        base = _wmean(y2020["ppsf"], y2020["sold"]) if len(y2020) >= 3 else np.nan
        now = g[g["month"].isin(now_cut)]
        now_ppsf = _wmean(now["ppsf"], now["sold"])
        # robust peak: only months with >=2 sales, smoothed, to avoid single-sale spikes
        gp = g[g["sold"] >= 2]
        peak = (float(gp["ppsf"].rolling(3, min_periods=2).mean().max())
                if len(gp) >= 3 else np.nan)
        dom_now = _wmean(now["dom"], now["sold"])
        dom_base = _wmean(y2020["dom"], y2020["sold"]) if len(y2020) >= 3 else np.nan
        s2l_now = _wmean(now["s2l"], now["sold"])
        rows.append({
            "neighborhood": nb,
            "ppsf_2020": round(base, 1) if pd.notna(base) else None,
            "ppsf_peak": round(peak, 1) if pd.notna(peak) else None,
            "ppsf_now": round(now_ppsf, 1) if pd.notna(now_ppsf) else None,
            "pct_2020_now": round((now_ppsf / base - 1) * 100, 1)
                if pd.notna(base) and base and pd.notna(now_ppsf) else None,
            "pct_off_peak": round((now_ppsf / peak - 1) * 100, 1)
                if pd.notna(peak) and peak and pd.notna(now_ppsf) else None,
            "dom_2020": round(dom_base, 0) if pd.notna(dom_base) else None,
            "dom_now": round(dom_now, 0) if pd.notna(dom_now) else None,
            "s2l_now": round(s2l_now, 4) if pd.notna(s2l_now) else None,
            "sold_total": int(g["sold"].sum()),
        })
    return sorted(rows, key=lambda r: (r["pct_2020_now"] is None, -(r["pct_2020_now"] or 0)))


def main():
    df = load()
    tl = market_timeline(df)
    months = [r["month"] for r in tl]
    series = neighborhood_series(df, months)
    sh = shifts(df)

    # citywide headline shift numbers
    first, last = tl[0], tl[-1]
    peak_ppsf = max(tl, key=lambda r: r["ppsf"])
    trough_dom = min(tl, key=lambda r: r["dom"])
    bundle = {
        "meta": {
            "source": "Redfin Data Center neighborhood tracker (All Residential, 90-day rolling)",
            "start": months[0], "end": months[-1],
            "n_neighborhoods": len(series),
            "city_2020_ppsf": first["ppsf"], "city_now_ppsf": last["ppsf"],
            "city_pct_since_2020": round((last["ppsf"] / first["ppsf"] - 1) * 100, 1),
            "peak_month": peak_ppsf["month"], "peak_ppsf": peak_ppsf["ppsf"],
            "fastest_month": trough_dom["month"], "fastest_dom": trough_dom["dom"],
        },
        "market_timeline": tl,
        "neighborhood_ppsf": {"months": months, "series": series},
        "shifts": sh,
    }
    with open(os.path.join(PROC, "time_bundle.json"), "w") as f:
        json.dump(bundle, f, separators=(",", ":"))
    m = bundle["meta"]
    print(f"Time bundle: {m['start']}..{m['end']} | {m['n_neighborhoods']} neighborhoods")
    print(f"  citywide PPSF ${m['city_2020_ppsf']:.0f} (2020) -> ${m['city_now_ppsf']:.0f} "
          f"(now), {m['city_pct_since_2020']:+.0f}% | peak ${m['peak_ppsf']:.0f} {m['peak_month']} "
          f"| fastest {m['fastest_dom']:.0f}d {m['fastest_month']}")


if __name__ == "__main__":
    main()
