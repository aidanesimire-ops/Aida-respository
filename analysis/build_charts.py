#!/usr/bin/env python3
"""
Build report charts (PNG) from the processed analysis bundle.

Design follows the data-viz method: form chosen by the data's job, validated
palette (sequential blue for magnitude, blue<->red diverging for polarity),
recessive axes/grid, thin marks, direct value labels, no dual axes.
Run after normalize_ppsf.py.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)

# Validated palette (light surface)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
BLUE = "#2a78d6"
BLUE_DK = "#184f95"
RED = "#e34948"
GREEN = "#0ca30c"

plt.rcParams.update({
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Segoe UI", "Arial"],
    "text.color": INK,
    "axes.labelcolor": INK2,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.edgecolor": BASE,
    "font.size": 11,
})


def _style(ax, grid_axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASE)
    ax.grid(axis=grid_axis, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def load():
    with open(os.path.join(PROC, "analysis_bundle.json")) as f:
        return json.load(f)


def load_mls():
    with open(os.path.join(PROC, "mls_bundle.json")) as f:
        return json.load(f)


def chart_top_ppsf(b):
    h = pd.DataFrame(b["headline"]).sort_values("norm_ppsf", ascending=False).head(20)
    h = h.iloc[::-1]
    fig, ax = plt.subplots(figsize=(10.5, 8.5))
    ax.barh(h["neighborhood"], h["norm_ppsf"], color=BLUE, height=0.72, zorder=3)
    for y, v in enumerate(h["norm_ppsf"]):
        ax.text(v + 12, y, f"${v:,.0f}", va="center", ha="left",
                fontsize=9.5, color=INK2)
    _style(ax, "x")
    ax.set_xlim(0, h["norm_ppsf"].max() * 1.13)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Normalized $/sqft  (time- and property-type-adjusted, single-family)")
    ax.set_title("Fort Lauderdale — Top 20 neighborhoods by normalized price/sqft",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Source: Redfin Data Center (neighborhood tracker), Fort Lauderdale FL. "
             "Normalized via weighted hedonic index.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_top_ppsf.png"), dpi=150)
    plt.close(fig)


def chart_market_index(b):
    mi = pd.DataFrame(b["market_index"])
    mi["date"] = pd.to_datetime(mi["month_key"] + "-01")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(mi["date"], mi["index_100"], color=BLUE, linewidth=2.2, zorder=3)
    ax.fill_between(mi["date"], mi["index_100"], 100, color=BLUE, alpha=0.07, zorder=2)
    end = mi.iloc[-1]
    ax.scatter([end["date"]], [end["index_100"]], color=BLUE, s=36, zorder=4)
    ax.annotate(f"{end['index_100']:.0f}", (end["date"], end["index_100"]),
                textcoords="offset points", xytext=(8, 0), va="center",
                fontsize=11, fontweight="bold", color=BLUE_DK)
    ax.axhline(100, color=BASE, linewidth=1)
    _style(ax, "y")
    ax.set_ylabel("Quality-adjusted PPSF index  (100 = Jan 2012)")
    ax.set_title("Fort Lauderdale market appreciation, 2012–2026",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    ax.margins(x=0.01)
    fig.text(0.01, 0.005, "Month fixed effects from the hedonic model (controls for "
             "neighborhood & property-type mix). Source: Redfin Data Center.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_market_index.png"), dpi=150)
    plt.close(fig)


def chart_vs_city(b):
    h = pd.DataFrame(b["headline"]).dropna(subset=["vs_city_pct"])
    top = h.nlargest(12, "vs_city_pct")
    bot = h.nsmallest(12, "vs_city_pct")
    d = pd.concat([bot, top]).sort_values("vs_city_pct")
    colors = [BLUE if v >= 0 else RED for v in d["vs_city_pct"]]
    fig, ax = plt.subplots(figsize=(10.5, 9))
    ax.barh(d["neighborhood"], d["vs_city_pct"], color=colors, height=0.72, zorder=3)
    for y, v in enumerate(d["vs_city_pct"]):
        ax.text(v + (3 if v >= 0 else -3), y, f"{v:+.0f}%", va="center",
                ha="left" if v >= 0 else "right", fontsize=9, color=INK2)
    ax.axvline(0, color=BASE, linewidth=1.2)
    _style(ax, "x")
    lim = d["vs_city_pct"].abs().max() * 1.2
    ax.set_xlim(-lim, lim)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:+.0f}%"))
    ax.set_xlabel("Normalized $/sqft vs. city average  (single-family)")
    ax.set_title("Premium vs. discount to the citywide average",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Blue = above citywide normalized PPSF; red = below. "
             "Source: Redfin Data Center.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_vs_city.png"), dpi=150)
    plt.close(fig)


def chart_leverage(b):
    h = pd.DataFrame(b["headline"]).dropna(subset=["norm_dom", "discount_pct"])
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    sizes = (h["sample_txns"].clip(20, 800) / 800 * 380) + 25
    sc = ax.scatter(h["norm_dom"], h["discount_pct"], s=sizes,
                    c=h["buyer_leverage"], cmap="Blues", edgecolors="white",
                    linewidths=1.1, zorder=3, vmin=h["buyer_leverage"].min())
    # label notable points (highest leverage + a couple of anchors)
    notable = set(h.nlargest(5, "buyer_leverage")["neighborhood"]) | \
        set(h.nsmallest(3, "discount_pct")["neighborhood"])
    for _, r in h.iterrows():
        if r["neighborhood"] in notable:
            ax.annotate(r["neighborhood"], (r["norm_dom"], r["discount_pct"]),
                        textcoords="offset points", xytext=(7, 4),
                        fontsize=8.5, color=INK2)
    _style(ax, "both")
    ax.set_xlabel("Normalized days on market")
    ax.set_ylabel("Typical discount to list  (%, positive = sells under ask)")
    ax.set_title("Where buyers have negotiating leverage",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    cb = fig.colorbar(sc, ax=ax, pad=0.015)
    cb.set_label("Buyer-leverage score", color=INK2)
    cb.outline.set_visible(False)
    fig.text(0.01, 0.005, "Bubble size = transaction sample. Upper-right = longer on "
             "market + bigger discounts. Source: Redfin Data Center.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_leverage.png"), dpi=150)
    plt.close(fig)


def chart_appreciation(b):
    h = pd.DataFrame(b["headline"]).dropna(subset=["ppsf_cagr"])
    h = h[h["confidence"].isin(["High", "Medium"])].nlargest(15, "ppsf_cagr").iloc[::-1]
    fig, ax = plt.subplots(figsize=(10.5, 7.5))
    ax.barh(h["neighborhood"], h["ppsf_cagr"] * 100, color=GREEN, height=0.72, zorder=3)
    for y, v in enumerate(h["ppsf_cagr"] * 100):
        ax.text(v + 0.15, y, f"{v:.1f}%", va="center", fontsize=9.5, color=INK2)
    _style(ax, "x")
    ax.set_xlim(0, h["ppsf_cagr"].max() * 100 * 1.13)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:.0f}%"))
    ax.set_xlabel("Annualized PPSF growth (CAGR), full available span")
    ax.set_title("Fastest-appreciating neighborhoods (reliable sample)",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Single-family, medium/high-confidence neighborhoods only. "
             "Source: Redfin Data Center.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_appreciation.png"), dpi=150)
    plt.close(fig)


def chart_mls_ranking(mb):
    df = pd.DataFrame(mb["neighborhoods"]).sort_values("norm_ppsf", ascending=False).head(20)
    df = df.iloc[::-1]
    colors = [BLUE if t == "Single Family" else "#eb6834" for t in df["basis_type"]]
    fig, ax = plt.subplots(figsize=(10.5, 8.5))
    ax.barh(df["neighborhood"], df["norm_ppsf"], color=colors, height=0.72, zorder=3)
    for y, v in enumerate(df["norm_ppsf"]):
        ax.text(v + 8, y, f"${v:,.0f}", va="center", fontsize=9.5, color=INK2)
    _style(ax, "x")
    ax.set_xlim(0, df["norm_ppsf"].max() * 1.13)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Normalized $/sqft — per-home hedonic, standardized dry-lot home")
    ax.set_title("Top 20 neighborhoods by normalized $/sqft (MLS per-home model)",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Single-family basis"),
                       Patch(color="#eb6834", label="Condo basis")],
              loc="lower right", frameon=False, fontsize=9)
    fig.text(0.01, 0.005, "Source: user-provided Fort Lauderdale MLS closed sales, "
             "hedonic-normalized. Cross-validated vs. Redfin at r=0.94.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_mls_ranking.png"), dpi=150)
    plt.close(fig)


def chart_premiums(mb):
    p = mb["meta"]["premiums"]
    items = [("Waterfront", p["waterfront_pct"]),
             ("Pool", p["pool_pct"]),
             ("Each extra\nbathroom", p["bath_pct"]),
             ("Per decade\nolder", p["age_per_decade_pct"])]
    labels = [i[0] for i in items]
    vals = [i[1] for i in items]
    colors = [GREEN if v >= 0 else RED for v in vals]
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    bars = ax.bar(labels, vals, color=colors, width=0.6, zorder=3)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + (0.6 if v >= 0 else -0.6),
                f"{v:+.1f}%", ha="center", va="bottom" if v >= 0 else "top",
                fontsize=11, fontweight="bold", color=INK2)
    ax.axhline(0, color=BASE, linewidth=1.2)
    _style(ax, "y")
    ax.set_ylabel("Effect on price per square foot")
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("{x:+.0f}%"))
    ax.set_title("What drives Fort Lauderdale home value (per-home hedonic)",
                 fontsize=13.5, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Marginal effect holding size, type, neighborhood constant. "
             f"Size elasticity {p['size_elasticity']}. Source: MLS closed sales.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_premiums.png"), dpi=150)
    plt.close(fig)


def chart_crosscheck(mb):
    r = pd.DataFrame(load()["headline"])[["neighborhood", "norm_ppsf"]].rename(
        columns={"norm_ppsf": "redfin"})
    m = pd.DataFrame(mb["neighborhoods"])
    m = m[m["basis_type"] == "Single Family"][["neighborhood", "norm_ppsf"]].rename(
        columns={"norm_ppsf": "mls"})
    c = m.merge(r, on="neighborhood")
    fig, ax = plt.subplots(figsize=(7.8, 7.4))
    lim = max(c["mls"].max(), c["redfin"].max()) * 1.08
    ax.plot([0, lim], [0, lim], color=MUTED, linewidth=1, linestyle=(0, (4, 4)), zorder=1)
    ax.scatter(c["redfin"], c["mls"], s=60, color=BLUE, edgecolors="white",
               linewidths=1, zorder=3)
    for _, row in c.iterrows():
        if row["mls"] > 500 or abs(row["mls"] - row["redfin"]) > 90:
            ax.annotate(row["neighborhood"], (row["redfin"], row["mls"]),
                        textcoords="offset points", xytext=(6, 3), fontsize=8, color=INK2)
    _style(ax, "both")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.yaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Redfin aggregate normalized $/sqft")
    ax.set_ylabel("MLS per-home hedonic normalized $/sqft")
    corr = c["mls"].corr(c["redfin"])
    ax.set_title(f"Independent validation — two methods agree (r={corr:.2f})",
                 fontsize=13.5, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Dashed line = perfect agreement. Each dot is a neighborhood "
             "priced by both methods. Sources: MLS + Redfin.", fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_crosscheck.png"), dpi=150)
    plt.close(fig)


def chart_geography(mb):
    g = pd.DataFrame(mb["geography"]).sort_values("median_ppsf")
    wet = {"Finger-isle waterfront", "Barrier island / beach",
           "Intracoastal / canal waterfront"}
    colors = [BLUE if t in wet else "#8a94a0" for t in g["geo_type"]]
    fig, ax = plt.subplots(figsize=(10, 5.2))
    ax.barh(g["geo_type"], g["median_ppsf"], color=colors, height=0.66, zorder=3)
    for y, (v, n) in enumerate(zip(g["median_ppsf"], g["n"])):
        ax.text(v + 8, y, f"${v:,.0f}  (n={n:,})", va="center", fontsize=9.5, color=INK2)
    _style(ax, "x")
    ax.set_xlim(0, g["median_ppsf"].max() * 1.22)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("${x:,.0f}"))
    ax.set_xlabel("Median sale $/sqft (closed homes)")
    ax.set_title("Price by lot geography — the water tiers",
                 fontsize=14, fontweight="bold", color=INK, pad=12, loc="left")
    fig.text(0.01, 0.005, "Derived classification (waterfront flag + subdivision + MLS area) — "
             "indicative, not an official survey. Blue = on water. Source: MLS closed sales.",
             fontsize=8, color=MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(os.path.join(OUT, "chart_geography.png"), dpi=150)
    plt.close(fig)


def main():
    b = load()
    chart_top_ppsf(b)
    chart_market_index(b)
    chart_vs_city(b)
    chart_leverage(b)
    chart_appreciation(b)
    try:
        mb = load_mls()
        chart_mls_ranking(mb)
        chart_premiums(mb)
        chart_crosscheck(mb)
        chart_geography(mb)
    except FileNotFoundError:
        print("(mls_bundle.json not found — skipping MLS charts)")
    print("Charts written to outputs/:", ", ".join(sorted(
        f for f in os.listdir(OUT) if f.endswith(".png"))))


if __name__ == "__main__":
    main()
