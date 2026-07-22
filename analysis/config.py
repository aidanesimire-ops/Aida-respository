#!/usr/bin/env python3
"""
Central configuration for the deal dashboard.

Every tunable that used to be a hard-coded constant scattered across the modules
lives here: model thresholds, price bands, comp minimums, verdict cutoffs, and the
per-asset ingestion spec (folder + status map + column map). The DEFAULTS below
reproduce the original behaviour exactly, so with no YAML file present nothing
changes. Drop a `config/deal_dashboard.yml` at the repo root to override any subset
of these — deep-merged over the defaults — then re-run `python analysis/refresh.py`.

Usage in a module:
    from config import CFG
    THIS_YEAR = CFG.year
    MIN_GEO_SOLD = CFG.thr("min_geo_sold")
    cols = CFG.cols("residential")           # canonical -> raw column name
    edges, labels = CFG.full_bands()         # price bands incl. "<$1M"
"""
from __future__ import annotations
import copy
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CFG_PATH = os.path.join(ROOT, "config", "deal_dashboard.yml")

DEFAULTS = {
    "market": {"name": "Fort Lauderdale", "this_year": 2026},
    "thresholds": {
        # improved-residential hedonic
        "min_geo_sold": 10,          # closed sales for a neighborhood to be its own model level
        "min_report_sold": 12,       # closed sales to appear in the ranking
        "new_max_age": 6,            # <= years old counts as "new construction"
        "ppsf_bounds": [40, 6000],   # plausible $/sqft (drop data errors)
        # luxury / high-ticket
        "high_ticket": 1_000_000,    # underwrite listings at or above this
        "price_bands": [1_000_000, 2_000_000, 3_000_000, 5_000_000, 10_000_000],
        "min_band_cell": 2,          # min obs in a (neighborhood, band) cell to report
        # repricing / verdicts
        "min_nbhd_live": 3,
        "min_comps": 5,
        "min_nbhd_sold": 8,
        "verdict_cutoff_pct": 10,    # +/- this % = over/under, else fairly priced
        # prospecting
        "min_over_pct": 10,
        "max_over_pct": 60,
        # absorption (months of supply) verdict boundaries
        "absorption": {"sellers": 6, "balanced": 12, "buyers": 24},
        # redfin context layer
        "redfin_min_sample": 20,
        # land
        "land": {"min_nbhd_sold": 4, "ppsf_bounds": [0.2, 3000], "urban_sqft": 60000},
        # income / multifamily
        "income": {"min_nbhd_sold": 5, "ppu_bounds": [40_000, 3_000_000],
                   "ppsf_bounds": [60, 2000], "verdict_cutoff_pct": 8},
    },
    "assets": {
        "residential": {
            "folder": "data/raw/mls",
            "status_from": "filename",
            "status_map": {"sold": "Sold", "expired": "Expired", "withdrawn": "Withdrawn",
                           "cancelled": "Cancelled", "temp_off": "TempOff",
                           "active_coming_soon": "Active", "active_pending": "Pending"},
            "columns": {
                "area": "Area", "address": "Address", "subdivision": "Subdivision/Complex",
                "list_price": "List Price", "sale_price": "Sale Price", "beds": "#Beds",
                "fbaths": "#FBaths", "hbaths": "#HBaths", "sqft": "SqFt LA",
                "ptype": "Type of Property", "year_built": "Year Built",
                "garage": "#Garage Spaces", "pool": "Pool YN",
                "waterfront": "Waterfront Property (Y/N)", "lot_sqft": "Lot SqFt"},
        },
        "land": {
            "folder": "data/raw/land",
            "status_from": "column", "status_column": "St",
            "status_map": {"CS": "Sold", "PS": "Pending", "A": "Active", "AC": "Active",
                           "X": "Expired", "C": "Cancelled", "W": "Withdrawn", "T": "TempOff"},
            "columns": {
                "mls": "MLS # Link", "area": "Area", "address": "Address",
                "subdivision": "Subdivision Name", "list_price": "Current Price",
                "sale_price": "Sale Price", "acre": "Total Acreage", "psqft": "Property SqFt",
                "lot_desc": "Lot Description", "zn": "ZN", "style": "Style of Property",
                "ptype": "Type of Property", "waterfront": "Waterfront Property (Y/N)",
                "road": "Road Description"},
        },
        "commercial_land": {
            "folder": "data/raw/commercial_land",
            "status_from": "column", "status_column": "St",
            "status_map": {"CS": "Sold", "PS": "Pending", "A": "Active", "AC": "Active",
                           "X": "Expired", "C": "Cancelled", "W": "Withdrawn", "T": "TempOff"},
            "columns": {
                "area": "Area", "address": "Address", "list_price": "Current Price",
                "sale_price": "Sale Price", "acre": "Total Acreage", "lotsf": "Lot SqFt",
                "location": "Location", "zn": "ZN", "style": "Style of Property",
                "ptype": "Type of Property", "for_lease": "For Lease"},
        },
        "income": {
            "folder": "data/raw/income",
            "status_from": "column", "status_column": "St",
            "status_map": {"CS": "Sold", "PS": "Pending", "A": "Active", "AC": "Active",
                           "X": "Expired", "C": "Cancelled", "W": "Withdrawn", "T": "TempOff"},
            "columns": {
                "mls": "MLS # Link", "area": "Area", "address": "Address",
                "subdivision": "Subdivision Name", "list_price": "Current Price",
                "sale_price": "Sale Price", "units": "Total Units", "style": "Style ",
                "sqft": "SqFt LA", "year_built": "Year Built", "parking": "#Parking Spaces",
                "pool": "Pool YN", "waterfront": "Waterfront Property (Y/N)"},
        },
    },
}


def _deep_merge(base, over):
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def _m(x):
    return f"${x / 1e6:g}M"


def _labels(edges_with_zero):
    """Human band labels from finite edges that start at 0 and end at +inf."""
    out = []
    for lo, hi in zip(edges_with_zero[:-1], edges_with_zero[1:]):
        if lo == 0:
            out.append(f"<{_m(hi)}")
        elif hi == float("inf"):
            out.append(f"{_m(lo)}+")
        else:
            out.append(f"{_m(lo)}–{_m(hi)}")
    return out


class Config:
    def __init__(self, d):
        self._d = d

    @property
    def market(self):
        return self._d["market"]

    @property
    def year(self):
        return self._d["market"]["this_year"]

    def thr(self, key):
        return self._d["thresholds"][key]

    @property
    def thresholds(self):
        return self._d["thresholds"]

    def asset(self, name):
        return self._d["assets"][name]

    def cols(self, name):
        return self._d["assets"][name]["columns"]

    def folder(self, name):
        return os.path.join(ROOT, self._d["assets"][name]["folder"])

    def full_bands(self):
        """Edges incl. 0 and +inf, with a '<$1M' first band. For absorption/seller/comps."""
        edges = [0] + list(self.thr("price_bands")) + [float("inf")]
        return edges, _labels(edges)

    def ht_bands(self):
        """Edges from the high-ticket floor up (no '<$1M'). For high_ticket."""
        edges = list(self.thr("price_bands")) + [float("inf")]
        return edges, _labels([0] + edges)[1:]

    def as_dict(self):
        return self._d


def load():
    d = copy.deepcopy(DEFAULTS)
    if os.path.exists(CFG_PATH):
        try:
            import yaml
            with open(CFG_PATH) as f:
                _deep_merge(d, yaml.safe_load(f) or {})
        except Exception as e:  # noqa: BLE001 -- config is best-effort; fall back to defaults
            print(f"[config] could not read {CFG_PATH} ({e}); using defaults")
    return Config(d)


CFG = load()
