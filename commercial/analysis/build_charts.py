#!/usr/bin/env python3
"""Charts (PNG) -> outputs/*.png."""
from __future__ import annotations
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import cre_common as CRE
import cre_assumptions as A

OUT = os.path.join(CRE.ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)
INK, ACCENT, WARM, GOOD, BAD, GRID = "#1f2a37", "#2f6f9f", "#c2703d", "#3f7d5a", "#b0473a", "#e6e4dd"
plt.rcParams.update({"font.size": 11, "axes.edgecolor": "#c9c6bd", "axes.labelcolor": INK,
                     "text.color": INK, "xtick.color": INK, "ytick.color": INK, "figure.dpi": 130})


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def _load(n):
    with open(os.path.join(CRE.PROC, n)) as f:
        return json.load(f)


def chart_sub(cre):
    d = pd.DataFrame(cre["submarkets"]).sort_values("norm_ppsf")
    fig, ax = plt.subplots(figsize=(8.6, max(3, 0.45 * len(d))))
    ax.barh(d["submarket"], d["norm_ppsf"], color=ACCENT)
    for y, v in enumerate(d["norm_ppsf"]):
        ax.text(v + 3, y, f"${v:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Normalized $/SqFt (standardized building)")
    ax.set_title("Normalized $/SqFt by submarket", fontweight="bold", loc="left")
    _style(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_submarket_ppsf.png")); plt.close(fig)


def chart_type(cre):
    d = pd.DataFrame(cre["types"]).sort_values("median_ppsf")
    fig, ax = plt.subplots(figsize=(8.6, max(3, 0.45 * len(d))))
    ax.barh(d["asset_type"], d["median_ppsf"], color=WARM)
    for y, v in enumerate(d["median_ppsf"]):
        ax.text(v + 3, y, f"${v:,.0f}", va="center", fontsize=9)
    ax.set_xlabel("Median sale $/SqFt")
    ax.set_title("Median $/SqFt by asset type", fontweight="bold", loc="left")
    _style(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_type_ppsf.png")); plt.close(fig)


def chart_implied_cap(cre):
    d = pd.DataFrame(cre["types"])
    d = d.sort_values("typical_implied_cap")
    y = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(8.6, max(3, 0.5 * len(d))))
    ax.barh(y - 0.2, d["typical_implied_cap"] * 100, height=0.4, color=ACCENT, label="Implied cap (assumed rents)")
    ax.barh(y + 0.2, d["assume_cap_rate"] * 100, height=0.4, color="#b9b6ad", label="Assumed market cap")
    ax.set_yticks(y); ax.set_yticklabels(d["asset_type"])
    ax.set_xlabel("Cap rate (%)  ·  at DEFAULT assumptions — tune live in the dashboard")
    ax.set_title("Implied vs. market cap by asset type", fontweight="bold", loc="left")
    ax.legend(fontsize=9, frameon=False); _style(ax)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_implied_cap.png")); plt.close(fig)


def chart_absorption():
    try:
        d = pd.DataFrame(_load("segments_bundle.json")["absorption_by_submarket"]).dropna(subset=["months_supply"])
    except (FileNotFoundError, KeyError):
        return
    if not len(d):
        return
    d = d.sort_values("months_supply")
    colors = [GOOD if m < 12 else (BAD if m > 30 else ACCENT) for m in d["months_supply"]]
    fig, ax = plt.subplots(figsize=(8.6, max(3, 0.45 * len(d))))
    ax.barh(d["submarket"], d["months_supply"], color=colors)
    for y, v in enumerate(d["months_supply"]):
        ax.text(v + 0.3, y, f"{v:.0f}", va="center", fontsize=9)
    ax.set_xlabel("Months of supply  ·  green < 12 · red > 30")
    ax.set_title("Absorption by submarket", fontweight="bold", loc="left")
    _style(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_absorption.png")); plt.close(fig)


def chart_mispricing():
    try:
        fc = _load("reprice_bundle.json")["flag_counts"]
    except FileNotFoundError:
        return
    order = ["Underpriced", "Fair", "Overpriced"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(order, [fc.get(k, 0) for k in order], color=[GOOD, ACCENT, BAD])
    for x, k in enumerate(order):
        ax.text(x, fc.get(k, 0) + 0.2, str(fc.get(k, 0)), ha="center")
    ax.set_ylabel("Live listings")
    ax.set_title("Live inventory mispricing (default assumptions)", fontweight="bold", loc="left")
    ax.spines[["top", "right"]].set_visible(False); ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_mispricing.png")); plt.close(fig)


def chart_failure():
    try:
        d = pd.DataFrame(_load("prospects_bundle.json")["failure_rate_type"]).dropna(subset=["failure_rate_pct"])
    except (FileNotFoundError, KeyError):
        return
    d = d.sort_values("failure_rate_pct")
    fig, ax = plt.subplots(figsize=(8.6, max(3, 0.45 * len(d))))
    ax.barh(d["asset_type"], d["failure_rate_pct"], color=WARM)
    for y, v in enumerate(d["failure_rate_pct"]):
        ax.text(v + 0.5, y, f"{v:.0f}%", va="center", fontsize=9)
    ax.set_xlabel("Failure rate (failed ÷ (failed + sold))")
    ax.set_title("Listing failure rate by asset type", fontweight="bold", loc="left")
    _style(ax); fig.tight_layout(); fig.savefig(os.path.join(OUT, "chart_failure_rate.png")); plt.close(fig)


def main():
    cre = _load("cre_bundle.json")
    chart_sub(cre); chart_type(cre); chart_implied_cap(cre)
    chart_absorption(); chart_mispricing(); chart_failure()
    print("Charts -> outputs/*.png")


if __name__ == "__main__":
    main()
