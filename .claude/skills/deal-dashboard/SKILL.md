---
name: deal-dashboard
description: >-
  Build a comp-based real-estate market-intelligence "deal dashboard" from listing and
  sales data (MLS exports, Redfin/Zillow pulls, or any property CSV): a per-home hedonic
  model that normalizes price-per-square-foot by neighborhood against size, waterfront,
  age, type and time; repricing live inventory vs. comps; luxury underwriting by price
  band and neighborhood; absorption / months-of-supply; seller-prospect and teardown
  screens; a live financing/capital-markets scenario model; an interactive HTML dashboard;
  a multi-tab Excel workbook. USE THIS SKILL whenever the user wants to normalize or clean
  $/sqft, reprice or "underwrite" listings, rank neighborhoods, find under/over-priced
  inventory, model how rate/assumption changes move price, DOM, $psf and returns, or
  recreate this deal dashboard for a new market or asset class. This is market pricing
  intelligence from comps, NOT a development pro forma — for construction loans, LP/GP
  waterfalls, or sell-out models use the real-estate-underwriting skill.
---

# Deal Dashboard — comp-based real-estate market intelligence

This skill recreates a full market-pricing suite from raw listing/sales data. It turns
confounded, apples-to-oranges price-per-square-foot into **clean, comparable $/sqft by
neighborhood**, then layers on repricing, luxury-band underwriting, absorption, prospecting
screens, a financing scenario model, and two deliverables: a **self-contained interactive
HTML dashboard** and a **formatted Excel workbook**.

The reference implementation (Fort Lauderdale residential) is bundled in `scripts/`. It is
a *working template*, not a black box — you adapt the small data-loading layer to a new
market's columns and everything downstream flows.

## When to use this

Trigger this skill when the user wants any of:

- **Normalize / clean $/sqft** so neighborhoods are comparable (remove size, waterfront,
  age, type, time confounders).
- **Reprice live inventory** — "what should this be listed at?" vs. recent comps.
- **Rank neighborhoods** most-to-least expensive with metrics and suggested repricing.
- **Find mispriced inventory** — under- or over-priced listings, with reasons.
- **Luxury / high-ticket underwriting** — behavior of each price band *within* each
  neighborhood; a band can be hot in one area and soft in another.
- **Absorption** — months of supply by band and neighborhood.
- **Prospecting** — owners whose listings failed, overpriced actives, teardown/land plays.
- **A financing / capital-markets scenario tool** — set down payment, rate, a rate shift,
  price/DOM elasticities, cash-buyer share, appreciation, hold, and watch price, $/sqft,
  DOM, monthly P&I, cash-to-close, equity multiple and annualized return recompute.
- **"Recreate my deal dashboard for another market / asset class."**

**When NOT to use:** ground-up development pro formas, construction-loan draw schedules,
LP/GP promote waterfalls, entitlement or condo sell-out models, going-concern hotel
valuation — those are the **real-estate-underwriting** skill. This skill is about pricing
an *existing* market from comparable sales and live listings.

## The two-layer data architecture

The strongest version of this analysis cross-validates two independent estimates:

| Layer | Typical source | Gives you |
|---|---|---|
| **Primary** | Per-listing export (MLS, or any CSV with address / price / sqft / beds / baths / type / neighborhood / status) | Per-home hedonic normalized $/sqft, waterfront & new-construction premiums, real list-to-sale discounts, live repricing & mispricing flags |
| **Context** | A neighborhood aggregate tracker (e.g. Redfin Data Center, public & free) with dates | Appreciation index, days-on-market, and the "since 20XX" time shift the per-listing export usually lacks |

If the two are built from different data and agree (the reference achieves r = 0.93), that
agreement is your main validation that the normalization is sound. If you only have one
layer, the pipeline still runs — you just lose the cross-check and the time series.

## Quickstart

```bash
pip install -r requirements.txt
python scripts/refresh.py         # discover data + rebuild everything (the front door)
python scripts/refresh.py --check # validate data & column maps only, no rebuild
```

`refresh.py` reports the files, row counts and status breakdown it found for each asset
class and validates the column maps against the real export headers before building —
catching a renamed column instead of silently dropping it. `run_all.py` still runs the
raw pipeline if you want it.

## Dynamic — config-driven, nothing hard-coded

`config/deal_dashboard.yml` (loaded by `config.py`, whose built-in defaults reproduce the
reference behaviour exactly) is the single control panel:

- **`thresholds`** — comp minimums, price bands, high-ticket floor, verdict cutoffs,
  absorption boundaries, age/size bounds. Every module reads these via `from config import
  CFG` (`CFG.thr("high_ticket")`, `CFG.full_bands()`, …). Change a value, run `refresh.py`,
  and the whole pipeline rebuilds against it.
- **`assets`** — each asset class declares its `folder`, `status_from` (filename vs a
  status column), `status_map`, and a `columns` map (canonical field → the raw column name
  in *this* export). The loaders reference `CFG.cols("residential")["address"]`, so
  onboarding a differently-named export is a config edit, not code. Deleting any line falls
  back to the default — you only keep what you change.

The **dashboard also ships a "Live assumptions" panel** (verdict cutoff, min comps,
absorption boundaries) that recomputes every verdict, flag and market label **in the
browser** with no rebuild — seeded from the same config values and persisted to
localStorage. The split is deliberate: structural choices (price bands, hedonic premiums,
new data) go through config + `refresh.py`; day-to-day screening what-ifs are live.

When you adapt this skill, keep that architecture: read tunables from `CFG`, never
re-hard-code them, and seed any new live control from the config default.

`run_all.py` runs 16 stages in dependency order and writes everything to `data/processed/`,
`outputs/` and `dashboard/`. Re-run any time fresh data arrives.

**Path resolution:** each script computes `ROOT` as the parent of `scripts/` and reads/writes
`data/`, `outputs/`, `dashboard/` under it — so drop your `data/raw/` alongside `scripts/`, or
copy the scripts into a project and edit the `ROOT =` line at the top of each. Working from a
dedicated project directory (as in the reference repo) is the least-friction setup.

**Expected input layout** (adapt paths in the loaders):
```
data/raw/mls/            per-status listing exports (sold, expired, withdrawn,
                         cancelled, temp_off, active_coming_soon, active_pending)
data/raw/                neighborhood aggregate tracker (optional context layer)
data/processed/          cleaned tables + JSON bundles (generated)
outputs/                 charts (PNG) + the Excel workbook (generated)
dashboard/               index.html — the interactive dashboard (generated)
```

## Pipeline stages (what each script produces)

Each analysis module writes a `*_bundle.json` to `data/processed/`; the three builders
(`build_excel`, `build_dashboard`, `build_report`) consume those bundles. This decoupling
is deliberate — you can re-run one analysis without rebuilding everything, and the
deliverables never touch raw data.

| Script | Produces | Purpose |
|---|---|---|
| `normalize_ppsf.py` | `analysis_bundle.json` | Context-layer (Redfin) neighborhood hedonic, market index, time series |
| `mls_normalize.py` | `mls_bundle.json`, `mls_all_valued.csv` | **Core** per-home hedonic: normalized $/sqft, premiums, geography, land value, per-listing valuations, profiles |
| `land_analysis.py` | `land_bundle.json` | Vacant-land + dock + commercial-land comps: land $/sqft by neighborhood, lot geography, zoning/density, size gradient, implied-vs-actual |
| `income_analysis.py` | `income_bundle.json` | Small-multifamily $/unit & $/sqft comps by neighborhood and unit tier, live repricing |
| `street_underwrite.py` | `street_bundle.json` | Street-by-street value + live listings underwritten vs their own street's comps |
| `high_ticket.py` | `high_ticket_bundle.json` | ≥ $1M underwriting; band × neighborhood matrix |
| `underpriced.py` | `underpriced_bundle.json` | Underpriced opportunities with generated reasons |
| `absorption.py` | `absorption_bundle.json` | Months of supply by band and band × neighborhood |
| `seller_prospects.py` | `seller_bundle.json` | Failed-listing owners + overpriced actives to call |
| `teardown.py` | `teardown_bundle.json` | Land plays (lot is most of the value) |
| `comps.py` | `comps_bundle.json`, `comps_flat.csv` | The actual comps behind each ≥ $1M valuation |
| `reprice.py` | `reprice_bundle.json` | Reprice live inventory vs recent sold comps |
| `time_analysis.py` | `time_bundle.json` | 20XX → now shifts from the context layer |
| `master_summary.py` | `master_bundle.json` | Master ranked neighborhood sheet + suggested repricing |
| `backtest.py` | `backtest_bundle.json` | Out-of-sample accuracy (k-fold CV): median error in $ and %, by band/type — the credibility figure |
| `marketing.py` | `marketing_bundle.json` | Copy-ready content: per-neighborhood snapshot, shareable stat, CMA line, talking points, buyer opps, prospect outreach lines |
| `build_charts.py` | `outputs/*.png` | Matplotlib charts |
| `build_excel.py` | `outputs/*.xlsx` | Multi-tab workbook (Index, Key Conclusions, Master, **Scenario**, …) |
| `build_dashboard.py` | `dashboard/index.html` | Self-contained interactive dashboard |
| `build_report.py` | `REPORT.md` | Written analysis |

## Multiple asset classes (same pattern, one dashboard)

The improved-residential hedonic is the flagship, but the same export style (one file per
status, `St` column = CS/PS/A/X/C/W/T) drops in for other asset classes, each as its own
comp layer that shares the neighborhood canonicalizer:

- **Vacant land & docks** (`land_analysis.py`) — land $/sqft by neighborhood, lot geography
  (waterfront/corner/cul-de-sac/size), zoning/density, boat-dock/dockominium sales, and
  commercial/development parcels. This turns the hedonic's *implied* land value into real
  comps and cross-checks the two. Watch for **multi-market exports**: a "land" pull often
  spans a whole region, so isolate the target market (neighborhoods present in the improved
  layer) for the headline and label the rest as context — don't let rural acreage drag the
  citywide median.
- **Small multifamily / income** (`income_analysis.py`) — **price-per-unit** and **$/sqft**
  by neighborhood and unit tier (duplex/triplex/quad), with live listings repriced against
  recent closings. Recover missing unit counts from the income style code (I02/I03/I04).
  No rent roll in a single-line export, so **cap rate & GRM are out of scope** here — say so.

Each writes a `*_bundle.json` the builders pick up; each is guarded so a missing layer just
drops its dashboard card / Excel tab. To add a **new** asset class, clone the closest of the
two modules, remap the loader columns (`references/data_schema.md`), and register it in
`run_all.py`, `build_dashboard.py` and `build_excel.py` next to the others.

## The core model (read `references/methodology.md` before changing it)

```
log(sale $/sqft) ~ living area + beds + baths + waterfront + pool
                 + age + new construction + property type + NEIGHBORHOOD
```

**Normalized $/sqft** = the model's price for ONE *standardized* home (dry-lot, no pool,
citywide-median size and age) placed in each neighborhood, so only location varies.
Waterfront, pool, age and new-construction are reported separately as premiums. A second
structure-vs-land model implies land $/sqft. Duan smearing corrects the log-retransformation
bias. `references/methodology.md` has the full derivation, the absorption definition, and
the **comp-backed gating philosophy** that keeps thin luxury/condo/pre-construction data
from producing false signals — read it before touching the stats.

## The financing / capital-markets scenario model

Both the dashboard (`#scenario` card) and the Excel **Scenario** tab implement the same
live model. Inputs: purchase price, size, down payment, mortgage rate, amortization, a
**rate shift (bps)**, **price sensitivity (%/+100bps)** dampened by **cash-buyer share**,
**DOM sensitivity**, appreciation, hold, selling costs. Outputs: adjusted price, $/sqft,
projected DOM, monthly P&I, cash-to-close, exit value, equity multiple, annualized return,
plus a −200…+200 bps sensitivity table.

The elasticities are **inputs, not constants** — that is what makes the tool recreate for
any market or asset class. The Excel version is fully formula-driven off yellow input cells
(with cached values so it displays before recalc). The math is mirrored in
`scripts/build_dashboard.py` (`scenAt`/`scCalc`) and `scripts/build_excel.py`
(`scenario_sheet`/`_scen_compute`) — keep the two in sync if you edit the formula.

## Adapting to a new market or asset class

The only thing that is market-specific is the **data-loading layer**. Read
`references/data_schema.md` for the field-by-field mapping. The short version:

1. **Map your columns** to what `mls_normalize.load_clean()` expects (address, list/sale
   price, sqft, beds, baths, property type, year built, lot size, waterfront flag,
   neighborhood/subdivision, status). Most exports need only a rename dict.
2. **Set the status buckets** — which files/values mean sold vs active vs failed. Absorption
   and failure-rate math depend on this.
3. **Decide the confounders that matter for your asset class.** Residential cares about
   waterfront and pool; for another asset class swap those hedonic terms (e.g. office →
   floor, class, build-out; industrial → clear height, dock doors). The regression is just
   a formula string — change the right-hand side.
4. **Re-point the high-ticket threshold and price bands** in `high_ticket.py` to your
   market's luxury cutoffs.
5. **Drop the context layer** if you have no time-stamped aggregate — the pipeline degrades
   gracefully (guarded `FileNotFoundError`s throughout).

Then run `python scripts/run_all.py` and inspect `dashboard/index.html`.

## Guardrails that make the output defensible

The reference model is deliberately **tiered by confidence**: reliable for mid-market
single-family, degrading for $10M+ trophy homes, pre-construction towers and thin condo
buildings. Rather than emit a confident-but-wrong number there, it flags low-confidence
("Insufficient comps", "Condo — verify"), bounds gaps, and gates deal flags on a minimum
comp count. Preserve this. A dashboard that cries "underpriced!" on a $30M pre-construction
penthouse with no comps destroys trust in the 200 solid mid-market calls next to it. See
the "Comp-backed gating" section of `references/methodology.md`.

## Make it usable & marketing-ready

Two things turn the analysis into something the user actually operates:

- **`marketing.py` → a Marketing Kit** (dashboard card with copy-to-clipboard buttons +
  Excel "Marketing Kit" tab). It renders the numbers as *paste-ready prose* — a
  market-snapshot paragraph, a shareable one-liner, the CMA/pricing sentence, talking
  points, live buyer opportunities, and a per-prospect outreach message. This is where the
  model earns its keep for an agent. Keep the copy defensible and labeled as screening
  signal, never an appraisal.
- **`backtest.py` → out-of-sample accuracy.** A k-fold CV that reports median error in real
  $ and %, plus % within ±10/±20%, by band and type. It's the honest credibility figure
  ("priced within ±X% out-of-sample") *and* a map of where the model is strong (mid-market)
  vs. thin (trophy/condo). Surface it as a KPI, don't bury it.

Also ship a plain-English **how-to** (a "Start here" card mapping each job → the right
section, and a `USER_GUIDE.md`) and a **`DATA_TO_ADD.md`** that names the exact columns to
add next and what each unlocks — so the user knows both how to use it and how to grow it.

## Outputs to hand the user

- `dashboard/index.html` — open in a browser. Self-contained (all data/CSS/JS inlined, no
  network). Sticky section nav, light/dark theme, the scenario model, and every table.
- `outputs/*.xlsx` — the workbook. Point them at the **Index** tab (linked table of
  contents) and the **Scenario** tab (their editable deal model).
- `REPORT.md` — the written narrative.
- `outputs/*.png` — charts for slides/emails.
