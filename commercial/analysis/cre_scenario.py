#!/usr/bin/env python3
"""
Single-deal commercial underwriting scenario.

Because the export has no income, NOI is BUILT from assumptions: pick an asset type (or a real
listing) and the model uses that type's rent/vacancy/opex to derive NOI from price × sqft, then
runs a full levered return. Every lever — rents, vacancy, opex, cap, LTV, rate, a rate shift,
exit cap, growth, hold — is an input, so it recomputes live in the dashboard. This module holds
the Python reference math (mirrored in the dashboard JS) and seeds a representative deal.
"""
from __future__ import annotations
import json
import os

import cre_common as CRE
import cre_assumptions as A

MAX_YEARS = 10


def irr(cfs, lo=-0.95, hi=1.0):
    def npv(r):
        return sum(c / (1 + r) ** i for i, c in enumerate(cfs))
    if not cfs or all(c >= 0 for c in cfs) or all(c <= 0 for c in cfs):
        return float("nan")
    a, b = lo, hi
    g = 0
    while npv(a) * npv(b) > 0 and g < 200:
        b += 0.5
        g += 1
    if npv(a) * npv(b) > 0:
        return float("nan")
    for _ in range(200):
        mid = (a + b) / 2
        fm = npv(mid)
        if abs(fm) < 1e-8:
            return mid
        if npv(a) * fm < 0:
            b = mid
        else:
            a = mid
    return (a + b) / 2


def compute(price, sqft, rent_psf, vacancy, opex_ratio, market_cap,
            ltv, rate, amort, shift_bps, exit_cap, rent_growth, expense_growth,
            hold, sell_pct, acq_pct):
    hold = int(round(hold))
    egi0 = sqft * rent_psf * (1 - vacancy)
    exp0 = egi0 * opex_ratio
    noi0 = egi0 - exp0
    goin_cap = noi0 / price if price else float("nan")
    effr = rate + shift_bps / 10000.0
    loan = price * ltv
    equity = price * (1 - ltv) + price * acq_pct
    m, n = effr / 12.0, amort * 12
    pay = loan * m / (1 - (1 + m) ** -n) if m > 0 else loan / max(n, 1)
    ads = pay * 12
    dscr = noi0 / ads if ads else float("nan")
    debt_yield = noi0 / loan if loan else float("nan")

    egi_t = [egi0 * (1 + rent_growth) ** t for t in range(1, hold + 1)]
    exp_t = [exp0 * (1 + expense_growth) ** t for t in range(1, hold + 1)]
    noi_t = [e - x for e, x in zip(egi_t, exp_t)]
    exit_noi = noi_t[-1] if noi_t else noi0
    exit_value = exit_noi / exit_cap if exit_cap > 0 else float("nan")
    k = hold * 12
    remloan = (loan * ((1 + m) ** n - (1 + m) ** k) / ((1 + m) ** n - 1)
               if m > 0 else loan * (1 - k / n))
    net_sale = exit_value * (1 - sell_pct) - remloan

    cfs = [-equity]
    for i, ncf in enumerate(noi_t):
        cf = ncf - ads
        if i == hold - 1:
            cf += net_sale
        cfs.append(cf)
    lirr = irr(cfs)
    distributions = sum(cfs[1:])
    em = distributions / equity if equity else float("nan")
    coc1 = (noi_t[0] - ads) / equity if noi_t and equity else float("nan")
    return dict(noi0=noi0, goin_cap=goin_cap, effr=effr, loan=loan, equity=equity, ads=ads,
                dscr=dscr, debt_yield=debt_yield, egi0=egi0, exp0=exp0, noi_t=noi_t,
                exit_noi=exit_noi, exit_value=exit_value, remloan=remloan, net_sale=net_sale,
                lirr=lirr, em=em, coc1=coc1, cfs=cfs, hold=hold)


def seed():
    """Seed from the median Multifamily closed sale if available, else a generic deal."""
    price, sqft, atype = 2_000_000, 12_000, "Multifamily"
    path = os.path.join(CRE.PROC, "cre_all_valued.csv")
    if os.path.exists(path):
        import pandas as pd
        v = pd.read_csv(path)
        mf = v[(v["asset_type"] == "Multifamily") & (v["status"] == CRE.SOLD)]
        pool = mf if len(mf) else v[v["status"] == CRE.SOLD]
        if len(pool):
            row = pool.sort_values("price").iloc[len(pool) // 2]
            price, sqft, atype = float(row["price"]), float(row["sqft"]), row["asset_type"]
    a = A.for_type(atype)
    f = A.FINANCE
    return dict(price=round(price / 25000) * 25000, sqft=int(sqft), asset_type=atype,
                rent_psf=a["rent_psf"], vacancy=a["vacancy"], opex_ratio=a["opex_ratio"],
                market_cap=a["cap_rate"], exit_cap=round(a["cap_rate"] + f["exit_cap_delta_bps"] / 10000, 4),
                ltv=f["ltv"], rate=f["rate"], amort=f["amort"], shift_bps=f["rate_shift_bps"],
                rent_growth=f["rent_growth"], expense_growth=f["expense_growth"],
                hold=f["hold"], sell_pct=f["sell_pct"], acq_pct=f["acq_pct"])


if __name__ == "__main__":
    s = seed()
    v = compute(s["price"], s["sqft"], s["rent_psf"], s["vacancy"], s["opex_ratio"],
                s["market_cap"], s["ltv"], s["rate"], s["amort"], s["shift_bps"],
                s["exit_cap"], s["rent_growth"], s["expense_growth"], s["hold"],
                s["sell_pct"], s["acq_pct"])
    print(f"Seed {s['asset_type']} deal: {CRE.usd(s['price'])} / {s['sqft']:,} sqft "
          f"(${s['price']/s['sqft']:.0f}/sqft)")
    print(f"  assumed rent ${s['rent_psf']}/sf, vac {s['vacancy']*100:.0f}%, opex "
          f"{s['opex_ratio']*100:.0f}% -> NOI {CRE.usd(v['noi0'])} ({v['goin_cap']*100:.2f}% cap)")
    print(f"  DSCR {v['dscr']:.2f}x | debt yield {v['debt_yield']*100:.1f}% | "
          f"Y1 CoC {v['coc1']*100:.1f}% | {s['hold']}-yr IRR {v['lirr']*100:.1f}% | EM {v['em']:.2f}x")
