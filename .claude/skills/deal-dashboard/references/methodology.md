# Methodology

The statistics behind the pipeline. Read this before changing any model. The guiding
principle throughout: **only emit a number you can defend with comps.** A dashboard is only
as valuable as its most embarrassing false signal.

## 1. The per-home hedonic (core of `mls_normalize.py`)

Raw $/sqft is confounded — a neighborhood can look cheap or expensive purely because its
homes are bigger, older, newer, on the water, or a different type. We strip those out with a
regression on **closed sales only**:

```
log(sale_ppsf) ~ log(sqft) + beds + baths + waterfront + pool + age
                 + C(property_type) + C(geo)
```

- **Why log($/sqft):** price is multiplicative (a waterfront lot is worth *+X%*, not *+$Y*),
  errors are roughly log-normal, and coefficients read as percentages.
- **Why `log(sqft)` on the right too:** bigger homes have lower $/sqft (size elasticity is
  negative, ~−0.3). Including it means the neighborhood effect isn't polluted by which
  neighborhoods happen to have bigger houses.
- **`C(geo)`** is the neighborhood fixed effect — the thing we actually want. A neighborhood
  becomes its own level only with ≥ `MIN_GEO_SOLD` closed sales; otherwise it folds into a
  coarser MLS-area bucket so a 3-sale neighborhood can't throw a wild coefficient.

### Normalized $/sqft = the standardized-home prediction

Take the fitted model and predict the price of **one standardized home** — dry-lot, no pool,
citywide-median size and age — placed in each neighborhood. Only `C(geo)` varies, so the
result is a clean, comparable location price level. Everything else (waterfront, pool, age,
new construction) is reported *separately* as a premium instead of being baked into the
headline number.

### Duan smearing (retransformation bias)

Predicting in log space and exponentiating back **underestimates** the mean (Jensen's
inequality). Multiply retransformed predictions by the Duan smearing factor —
`mean(exp(residuals))` — to correct it. Skipping this biases every normalized $/sqft low by a
few percent; it matters most where residual variance is high (luxury).

### Premiums

The interpretable drivers come straight from the coefficients (with 95% CIs so you can say
"waterfront is worth +X%, and we're confident it's clear of zero"):

- waterfront, pool, new-construction: `exp(coef) − 1` as a percent.
- age: per-decade depreciation.
- size elasticity: the `log(sqft)` coefficient.

Report the CI. A premium whose interval straddles zero is not a talking point.

## 2. Structure vs. land (implied land value)

A second SFR-only model splits the sale into structure and land:

```
log(sale_price) ~ log(sqft) + log(lot_sqft) + age + C(geo)
```

The `log(lot_sqft)` elasticity, evaluated at the neighborhood level, implies **land $/sqft of
lot**. This is *implied* from improved sales, not vacant-land comps — label it as such. It
feeds the teardown/land-play screen.

## 3. Discounts & failure rate

- **Discount** = `(list − sale)/list` on **closed** homes only, summarized per neighborhood.
  This is the real list-to-sale gap, not asking-price wishful thinking.
- **Failure rate** = `failed / (failed + sold)` where failed = expired ∪ withdrawn ∪
  cancelled ∪ temp-off. Many failed listings relist and eventually sell, so this measures
  *attempt risk*, not permanent unsellability — say so.

## 4. Repricing live inventory (`reprice.py`, `master_summary.py`)

For every live listing, compare asking $/sqft to two references: the **model's** predicted
market $/sqft, and the **median recent SOLD $/sqft** for comparable homes in the neighborhood.
"Should-be" leans on actual sold comps because a closed price is harder to argue with than a
model. A neighborhood/building needs ≥ 8 sold comps to get a verdict; below that it is
"Insufficient comps" rather than a fabricated target.

## 5. High-ticket underwriting & bands (`high_ticket.py`)

Above the luxury threshold (default $1M), the same home is underwritten to a **suggested
list** from street/neighborhood comps, and every listing is bucketed into price bands
($1–2M, $2–3M, $3–5M, $5–10M, $10M+). The key view is **band × neighborhood**: the same band
behaves differently by area — Rio Vista is a seller's market ≤ $3M but a buyer's market above.
`band_by_neighborhood()` only emits a cell with ≥ 2 comparable observations.

## 6. Absorption (`absorption.py`)

```
months_of_supply = active_listings / (sold_over_~24_months / 24)
```

Interpretation: **< 6** seller's market · **6–12** balanced · **12–24** buyer's · **> 24**
deep buyer's. Computed per band and per band × neighborhood. This is where the macro story
usually lives — in the reference market, $10M+ ran ~43 months of supply (deeply oversupplied)
even while sub-$3M in prime neighborhoods was a seller's market.

## 7. The financing / capital-markets scenario model

Mirrored in `build_dashboard.py` (`scenAt`/`scCalc`) and `build_excel.py`
(`_scen_compute`/`scenario_sheet`). Given a rate shift `Δbps`:

```
price_factor   = 1 + (price_elast/100)·(Δbps/100)·(1 − cash_share)
adjusted_price = base_price · price_factor
effective_rate = base_rate + Δbps/10000
loan           = adjusted_price · (1 − down)
monthly_P&I    = loan · r/12 / (1 − (1+r/12)^(−n))      # r = effective_rate, n = amort·12
projected_DOM  = base_DOM · (1 + (dom_elast/100)·(Δbps/100))
cash_to_close  = adjusted_price·down + adjusted_price·0.03
exit_value     = adjusted_price · (1 + appreciation)^hold
remaining_loan = loan · ((1+m)^n − (1+m)^k)/((1+m)^n − 1)   # k = hold·12
net_proceeds   = exit_value − exit_value·sell_costs − remaining_loan
equity_multiple= net_proceeds / cash_to_close
annualized_ret = (net_proceeds/cash_to_close)^(1/hold) − 1
```

The crucial design choice: **the elasticities are inputs, not constants.** Price sensitivity
to rates is *dampened by the cash-buyer share* (cash buyers ignore mortgage rates), which is
why luxury coastal markets stayed firm through the 2022–24 hikes. Defaults are deliberately
conservative. Because nothing is hard-coded, the same model recreates for any asset class —
the user dials in their own read of how their market responds. Keep the dashboard JS and the
Excel formulas in sync if you change the math.

## 8. Cross-validation (the main integrity check)

Build the normalized ranking two independent ways — the per-home hedonic (primary layer) and
the neighborhood aggregate hedonic (context layer) — and correlate them. The reference hits
**r ≈ 0.93**. High agreement between methods built on different data is the strongest evidence
the normalization is real and not an artifact of one pipeline. Spot-check the top few sales to
the dollar against public records too.

## 9. Comp-backed gating — why the model is tiered by confidence

The model is **reliable for mid-market single-family and degrades for trophy homes,
pre-construction towers and thin condo buildings**, where heterogeneity is high and comps are
scarce. Rather than hide that, the pipeline is honest about it:

- Deal/mispricing flags require a **minimum comp count** and **bounded gaps** — an
  unbounded "−154%" or "+329%" is a data artifact, not an opportunity.
- Thin segments are labeled **"Insufficient comps"** or **"Condo — verify"** instead of being
  assigned a confident number.
- Luxury figures carry a **confidence** tag tied to how much sold data backs them; "Low
  (no comps)" means "starting point, not appraisal."
- Neighborhood aggregates are smoothed (require ≥ 2 sold + rolling median) so a single odd
  closing doesn't spike a whole neighborhood.

This restraint is the point. One loud false "underpriced!" on a $30M pre-construction penthouse
with no comps poisons trust in the 200 solid mid-market calls beside it. When you adapt the
skill, **preserve the gating** — it is what makes the output defensible in front of a client.

## Honest limitations to state in any deliverable

- Lot geography (point vs corner vs canal vs ocean-access) is *classified* from flags +
  subdivision, not surveyed.
- If the per-listing export lacks dates, per-home time adjustment isn't possible — DOM and
  appreciation come from the context layer at the neighborhood level.
- Implied land value is from improved sales, not vacant-land comps.
- Condo-level detail (floor, view, renovation) is usually unobserved — trust the neighborhood
  aggregates over individual condo call-outs.

These are **neighborhood benchmarks and screening signals, not per-home appraisals.**
