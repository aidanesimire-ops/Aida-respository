# Fort Lauderdale — Neighborhood Price/SqFt Normalization

Statistical normalization of the Fort Lauderdale residential market that turns raw,
confounded price-per-square-foot into **clean, comparable $/sqft by neighborhood** — and
the context to back it up in a homeowner conversation: waterfront vs dry-lot pricing,
new-construction vs existing, implied land value, real list-to-sale discounts, market
appreciation, listing failure rates, live over/under-priced inventory, and
**street-by-street value** — each street's premium vs. its neighborhood, with live
listings underwritten against their own street's comps.

It also ships as a **deal dashboard**: a live financing / capital-markets scenario model
(in both the HTML dashboard and an editable Excel tab) where you set the assumptions —
down payment, mortgage rate, a rate shift, price/DOM elasticities, cash-buyer share,
appreciation, hold — and watch sale price, $/sqft, days-on-market, cash-to-close and
hold-period returns recompute. Nothing is hard-coded, so the same tool recreates for
other markets and asset classes.

**Multiple asset classes.** Beyond improved residential, three more comp layers are folded
in from the same style of MLS exports:

- **Vacant land & docks** — real land $/sqft by neighborhood (turning the previously
  *implied* land value into comps), the lot factors that drive it (waterfront, corner,
  cul-de-sac, size, zoning/density), and the boat-dock / dockominium market.
- **Commercial / development land** — a thin but high-value Fort Lauderdale segment, with
  the actual sold parcels listed.
- **Small multifamily (residential income)** — duplex / triplex / quad **price-per-unit**
  and **$/sqft** comps by neighborhood and unit tier, live listings scored against recent
  closings. (Price-comp layer — cap rate / GRM need a rent roll.)

**Start here:** [`USER_GUIDE.md`](USER_GUIDE.md) (which tool for which job + how to use it
in your marketing) · [`REPORT.md`](REPORT.md) (written analysis) ·
[`outputs/Fort_Lauderdale_PPSF_Normalized.xlsx`](outputs/) (workbook — open the **Index**
tab for a linked table of contents) · [`dashboard/index.html`](dashboard/index.html)
(open in a browser — the **Start here** card maps each job to a section).

**For marketing:** the dashboard's **Marketing** card and the Excel **Marketing Kit** tab
generate copy-ready content per neighborhood — a market-snapshot paragraph, a shareable
stat, the CMA/pricing line, talking points, live buyer opportunities, and a prospect
outreach line for every failed/overpriced listing. A **Model Accuracy** backtest (dashboard
KPI + Excel tab) reports the model's out-of-sample error — your "data-backed pricing" proof.
Want to sharpen it further? [`docs/DATA_TO_ADD.md`](docs/DATA_TO_ADD.md) lists the exact
columns to add to your next export and what each unlocks.

## Why raw $/sqft misleads

A neighborhood can look cheap or expensive purely because its homes are bigger, older,
newer, on the water, or a different property type. This project removes those confounders
with a **per-home hedonic model** so what's left is the neighborhood's true price level.

## Two data layers (cross-validated at r = 0.93)

| Layer | Source | Gives us |
|---|---|---|
| **Primary** | User-provided Fort Lauderdale **MLS** exports — 12k+ listings across sold / expired / withdrawn / cancelled / temp-off / active / pending | Per-home hedonic normalized $/sqft, waterfront & new-construction premiums, real discounts, overpricing & live-listing flags |
| **Context** | **Redfin Data Center** neighborhood tracker (2012–2026), public & free | Market appreciation index, days-on-market, and the **2020→now shift analysis** (the MLS export has no dates) |

The dashboard includes a **"since 2020" time explorer** — toggle price / days-on-market /
discount and overlay any neighborhood's price path against the citywide line — plus the
COVID-cycle story: +70% price, the 2022 frenzy (45-day market), and today's divergence of
new-high prices with a slow market.

The two are built from different data with different methods and agree at **r = 0.93** —
the main validation that the normalization is sound. Top sales were also spot-checked
to the dollar against public records (e.g. 5 Harborage Isle, $70M).

## The model

```
log(sale $/sqft) ~ living area + beds + baths + waterfront + pool
                  + age + new construction + property type + NEIGHBORHOOD
```

**Normalized $/sqft** = the model's price for one *standardized* home (dry-lot, no pool,
citywide-median size and age) placed in each neighborhood, so only location varies.
Waterfront, pool, age and new-construction are reported separately as premiums. A second
SFR-only model splits structure value from lot value to imply land $/sqft.

## Run it

```bash
pip install -r requirements.txt
python analysis/refresh.py          # discover data + rebuild everything (the front door)
python analysis/refresh.py --check  # just validate data & column maps, no rebuild
```

`refresh.py` reports what data it found for each asset class and checks your column
maps against the actual export headers before building — so a renamed column is caught,
not silently dropped. (`python analysis/run_all.py` still runs the raw 18-step pipeline
if you prefer.)

## Dynamic — config-driven & live

Nothing is hard-coded. **[`config/deal_dashboard.yml`](config/deal_dashboard.yml)** is a
single control panel for the whole model:

- **Thresholds** — comp minimums, price bands, the high-ticket floor, verdict cutoffs,
  absorption boundaries, age/size bounds. Change a value, run `refresh.py`, everything
  downstream (bundles, Excel, dashboard, report) rebuilds.
- **Data sources** — each asset class declares its `folder`, `status_map`, and a
  `columns` map (canonical field → the raw column name in *your* export). Onboarding a
  differently-named export is a config edit, not code. Adding a whole new asset class is
  cloning one block and pointing an analysis module at it.

Deleting any line falls back to the built-in default, so you only keep what you change.

The **dashboard also carries a "Live assumptions" panel** — verdict cutoff, minimum comps,
and absorption boundaries — that recomputes every verdict, flag and market label **in the
browser, no rebuild.** Structural changes (price bands, hedonic premiums, new data) go
through the config + `refresh.py`; day-to-day what-if screening is live. Settings persist
per device.

Or step by step:

```bash
python analysis/normalize_ppsf.py   # Redfin layer  -> data/processed/*.csv, analysis_bundle.json
python analysis/mls_normalize.py    # MLS per-home  -> data/processed/mls_*.csv, mls_bundle.json
python analysis/land_analysis.py    # vacant land + docks + commercial land -> land_bundle.json
python analysis/income_analysis.py  # small-multifamily $/unit & $/sqft comps -> income_bundle.json
python analysis/street_underwrite.py# street-by-street value + deal underwriting -> street_bundle.json
python analysis/high_ticket.py      # >=$1M underwriting + band x neighborhood -> high_ticket_bundle.json
python analysis/underpriced.py      # underpriced opportunities + reasons -> underpriced_bundle.json
python analysis/absorption.py       # months-of-supply by band x neighborhood -> absorption_bundle.json
python analysis/seller_prospects.py # failed + overpriced owners to list -> seller_bundle.json
python analysis/teardown.py         # land-play screen -> teardown_bundle.json
python analysis/comps.py            # comps behind each valuation -> comps_bundle.json
python analysis/reprice.py          # reprice live inventory vs should-be -> reprice_bundle.json
python analysis/time_analysis.py    # 2020->now shifts -> data/processed/time_bundle.json
python analysis/backtest.py         # out-of-sample model accuracy -> backtest_bundle.json
python analysis/marketing.py        # copy-ready marketing content -> marketing_bundle.json
python analysis/build_charts.py     # -> outputs/*.png
python analysis/build_excel.py      # -> outputs/Fort_Lauderdale_PPSF_Normalized.xlsx
python analysis/build_dashboard.py  # -> dashboard/index.html (+ artifact.html)
python analysis/build_report.py     # -> REPORT.md
```

**Public-data enrichment (optional):** `python analysis/enrich_public.py` geocodes every
address and appends Census demographics, FEMA flood zones, and Broward County assessed
land-vs-building values. It needs open outbound HTTPS — the environment this was built in
blocks those hosts, so run it on a machine with normal network access.

Re-run any time you get fresh data — drop new MLS exports in `data/raw/mls/` (named by
status) and re-run.

## Layout

```
data/raw/mls/         seven MLS status exports (sold, expired, withdrawn, cancelled,
                      temp_off, active_coming_soon, active_pending)
data/raw/land/        residential-land exports (active / failed / sold+pending)
data/raw/commercial_land/  commercial / development land exports
data/raw/income/      residential-income (small multifamily) exports
data/raw/             redfin_fll_neighborhoods.tsv (filtered Redfin neighborhood data)
data/processed/       cleaned data + normalized tables + JSON bundles
config/               deal_dashboard.yml — the control panel (thresholds + data maps)
analysis/             the pipeline; config.py (loads the YAML), refresh.py (front door),
                      normalize_ppsf, mls_normalize, land_analysis, income_analysis, build_*
outputs/              charts (PNG) + the Excel workbook
dashboard/            self-contained interactive dashboard
REPORT.md             written analysis
```

## Honest limitations

- **Lot geography** is now *classified* (barrier-island / finger-isle point-lot /
  Intracoastal-canal / downtown / mainland-inland) from the waterfront flag + subdivision +
  MLS area — indicative, not surveyed. True point/corner/canal/ocean-access still needs the
  MLS *Waterfront Description / Lot Description / Dock* fields.
- **No dates / days-on-market** in the MLS export; those come from the Redfin layer at the
  neighborhood level. Adding *List/Close Date* columns would enable per-home time adjustment.
- **Vacant land** is now comp-backed where sales exist (the land layer); elsewhere land
  value is still *implied* from lot size. The land export is a multi-county South Florida
  pull, so genuine Fort Lauderdale land comps are thin — treat the FLL land figures as
  directional and the wider set as context.
- **Multifamily** is a price-comp layer only ($/unit, $/sqft) — cap rate and GRM need a
  rent roll, which the export doesn't carry.
- **Condo-level** flags are coarse (floor / view / renovation unobserved). Trust the
  neighborhood aggregates over individual condo call-outs.

These are neighborhood benchmarks and screening signals — **not per-home appraisals.**
