# Data schema & how to adapt a new market

The only market-specific code is the **loader** (`mls_normalize.load_clean()` and, for the
optional context layer, `normalize_ppsf.py`). Everything downstream reads a cleaned
DataFrame with canonical column names, so once your data maps onto that frame the whole
pipeline runs unchanged.

## Primary layer — the per-listing export

Place one CSV per status in `data/raw/mls/`, named by status. The filename (minus `.csv`)
must be a key in `STATUS_GROUP`:

| Filename | Bucket | Counts as |
|---|---|---|
| `sold.csv` | Sold | closed comp (trains the model, defines discounts & absorption denominator) |
| `active_coming_soon.csv` | Active | live inventory (repriced / flagged) |
| `active_pending.csv` | Pending | live inventory |
| `expired.csv` | Expired | failed listing (failure-rate + seller prospect) |
| `withdrawn.csv` | Withdrawn | failed |
| `cancelled.csv` | Cancelled | failed |
| `temp_off.csv` | TempOff | failed |

If your source uses one file with a status column instead of seven files, change the loop in
`load_clean()` to read that one file and map its status values through `STATUS_GROUP`.

### Columns `load_clean()` reads (rename your export to match, or edit the mapping)

| Canonical field | Raw column in the reference export | Notes |
|---|---|---|
| status | *(from filename)* | see table above |
| area | `Area` | MLS area code — fallback geo bucket when a neighborhood is thin |
| address | `Address` | used for dedup, street extraction, comps |
| neighborhood | `Subdivision/Complex` | cleaned + canonicalized via `CANON` / `_canon_neigh()` |
| list_price | `List Price` | |
| sale_price | `Sale Price` | only populated for Sold |
| beds | `#Beds` | |
| fbaths / hbaths | `#FBaths` / `#HBaths` | combined as full + 0.5·half |
| sqft | `SqFt LA` | living area — the $/sqft denominator |
| ptype | `Type of Property` | normalized to Single Family / Condo / Townhouse via `_ptype()` |
| year_built | `Year Built` | → age = current year − year_built |
| garage | `#Garage Spaces` | |
| pool | `Pool YN` | "yes"/"no" |
| waterfront | `Waterfront Property (Y/N)` | "yes"/"no" — the single biggest residential premium |
| lot_sqft | `Lot SqFt` | drives the implied-land model |

Most real exports need only a `rename()` dict at the top of `load_clean()`. Keep the cleaning
helpers (`_num` strips `$`/commas, `_ptype` normalizes type, `_canon_neigh` canonicalizes the
messy subdivision field) — they are generic.

### Tunable constants (top of `mls_normalize.py`)

- `THIS_YEAR` — anchor for age.
- `MIN_GEO_SOLD` (10) — closed sales a neighborhood needs to be its own model level; below
  this it folds into its MLS-area bucket so a thin neighborhood can't distort the fixed effect.
- `MIN_REPORT_SOLD` (12) — closed sales to appear in the ranking.
- `NEW_MAX_AGE` (6) — years-old cutoff for "new construction".
- `PPSF_LO`, `PPSF_HI` (40, 6000) — plausible $/sqft band; anything outside is a data error.

## Context layer — the neighborhood aggregate (optional but recommended)

`normalize_ppsf.py` reads a neighborhood tracker with **dates** (the reference uses a filtered
Redfin Data Center TSV, `data/raw/redfin_fll_neighborhoods.tsv`). It supplies the time series
(`time_analysis.py`) and days-on-market the per-listing export usually lacks. If you have no
dated aggregate, skip this layer — every consumer guards the missing bundle with
`FileNotFoundError` and degrades gracefully (you lose appreciation, DOM and the r≈0.93
cross-check, not the core normalization).

## Adapting to a different asset class

The hedonic right-hand side is just a formula string in `fit_hedonic()`:

```
log(sale_ppsf) ~ log(sqft) + beds + baths + waterfront + pool + age
                 + C(ptype) + C(geo)
```

Swap the physical drivers for what sets value in your asset class and populate those columns
in `load_clean()`:

- **Office:** floor/stack, building class, renovation/build-out vintage, parking ratio.
- **Industrial:** clear height, dock-door count, office finish %, power.
- **Retail:** frontage, corner, anchor co-tenancy, traffic count.
- **Multifamily:** unit mix, vintage, renovation status (price per unit or per sqft).

`C(geo)` (the location fixed effect) and `log(sqft)` (size elasticity) stay — they are the
backbone of "normalize away everything but location." Update `high_ticket.py`'s ticket
threshold and band edges to your market's luxury cutoffs, and relabel geography in
`_geo_type()` if lot/waterfront classification is irrelevant.
