#!/usr/bin/env python3
"""
The assumption engine — fills the income gaps the MLS export leaves blank.

The export gives us price, size, type, age and location, but NO income. So we attach a set
of EDITABLE INDUSTRY-NORM ASSUMPTIONS per asset class — market rent ($/sqft/yr), vacancy,
operating-expense ratio and market cap rate — and DERIVE the income view from them:

    rent      = sqft × market_rent_psf
    EGI       = rent × (1 − vacancy)
    NOI       = EGI × (1 − expense_ratio)
    impliedCap= NOI ÷ asking price          ← the yield you'd buy at, given these assumptions
    value     = NOI ÷ market_cap_rate        ← what it's worth at the market cap
    gap       = price ÷ value − 1            ← >0 overpriced, <0 underpriced (vs assumptions)

These numbers are only as good as the assumptions, which is the point: the dashboard exposes
every one as a live control so the user can dial them to their own read and watch value,
implied cap and returns recompute in real time. The defaults below are round-number
South-Florida norms as of 2025–26 — starting points, not gospel. Edit DEFAULTS or, better,
the sliders in the dashboard.
"""
from __future__ import annotations

# per asset type: market rent $/sqft/yr (on building SF), vacancy, opex ratio (% of EGI),
# going-in / market cap rate. Round-number industry norms — EDIT FREELY.
# rent_psf is calibrated so that, on each type's MEDIAN observed $/sqft in this market, the
# implied cap ≈ the assumed market cap — i.e. the defaults treat the market as fairly priced
# and let genuine outliers stand out. They are also realistic South-Florida gross rents. EDIT.
DEFAULTS = {
    "Multifamily":        {"rent_psf": 18, "vacancy": 0.06, "opex_ratio": 0.42, "cap_rate": 0.0550},
    "Office":             {"rent_psf": 34, "vacancy": 0.15, "opex_ratio": 0.45, "cap_rate": 0.0800},
    "Retail":             {"rent_psf": 23, "vacancy": 0.08, "opex_ratio": 0.22, "cap_rate": 0.0675},
    "Industrial":         {"rent_psf": 12, "vacancy": 0.05, "opex_ratio": 0.15, "cap_rate": 0.0625},
    "Mixed Use":          {"rent_psf": 16, "vacancy": 0.10, "opex_ratio": 0.35, "cap_rate": 0.0675},
    "Hotel":              {"rent_psf": 100, "vacancy": 0.30, "opex_ratio": 0.62, "cap_rate": 0.0850},
    "Restaurant":         {"rent_psf": 33, "vacancy": 0.10, "opex_ratio": 0.20, "cap_rate": 0.0650},
    "Flex":               {"rent_psf": 20, "vacancy": 0.08, "opex_ratio": 0.20, "cap_rate": 0.0700},
    "Special Purpose":    {"rent_psf": 22, "vacancy": 0.15, "opex_ratio": 0.30, "cap_rate": 0.0750},
    "Commercial (other)": {"rent_psf": 22, "vacancy": 0.12, "opex_ratio": 0.30, "cap_rate": 0.0700},
}

# global financing / hold assumptions for the single-deal underwriting scenario
FINANCE = {
    "ltv": 0.60, "rate": 0.0675, "amort": 25, "rate_shift_bps": 0,
    "exit_cap_delta_bps": 25,      # exit cap = market cap + this
    "rent_growth": 0.03, "expense_growth": 0.025, "hold": 5,
    "sell_pct": 0.02, "acq_pct": 0.02,
}


def for_type(asset_type, overrides=None):
    a = dict(DEFAULTS.get(asset_type, DEFAULTS["Commercial (other)"]))
    if overrides and asset_type in overrides:
        a.update(overrides[asset_type])
    return a


def derive(price, sqft, asset_type, assumptions=None):
    """Derive the income view for one property from the type's assumptions."""
    a = assumptions if assumptions else for_type(asset_type)
    rent = sqft * a["rent_psf"]
    egi = rent * (1 - a["vacancy"])
    noi = egi * (1 - a["opex_ratio"])
    implied_cap = noi / price if price else float("nan")
    value = noi / a["cap_rate"] if a["cap_rate"] else float("nan")
    gap = (price / value - 1) if value else float("nan")
    return {"rent": rent, "egi": egi, "noi": noi, "implied_cap": implied_cap,
            "market_cap": a["cap_rate"], "value": value, "value_gap": gap,
            "rent_psf": a["rent_psf"], "noi_psf": noi / sqft if sqft else float("nan")}


if __name__ == "__main__":
    for t, a in DEFAULTS.items():
        d = derive(2_000_000, 12_000, t)
        print(f"{t:20s} rent ${a['rent_psf']}/sf vac {a['vacancy']*100:.0f}% opex "
              f"{a['opex_ratio']*100:.0f}% cap {a['cap_rate']*100:.2f}% -> "
              f"NOI ${d['noi']:,.0f}, implied cap {d['implied_cap']*100:.2f}%, "
              f"value ${d['value']:,.0f}")
