# Fort Lauderdale Deal Dashboard — repo guide for Claude

This repository builds a comp-based real-estate **market-intelligence "deal dashboard"**
for Fort Lauderdale (extensible to any market): a per-home hedonic model that normalizes
price-per-square-foot by neighborhood, repricing of live inventory vs. comps, luxury
underwriting, absorption, seller/teardown screens, leasing & yield, costs/build-vs-buy,
micro-segmentation, a live financing scenario model, an interactive HTML dashboard, and a
self-contained multi-tab Excel workbook.

## Use the `deal-dashboard` skill

For ANY work in this repo — pricing/normalization, repricing or underwriting listings,
ranking neighborhoods, finding under/over-priced inventory, leasing/yield, build-vs-buy,
segmentation, refreshing outputs, or recreating the dashboard for a new market/asset class —
**use the `deal-dashboard` skill** (`.claude/skills/deal-dashboard/`). Invoke it explicitly
with `/deal-dashboard` or just describe the task; it carries the full playbook, the config
schema, and the methodology.

## The one command

```bash
python analysis/refresh.py          # discover data + rebuild EVERYTHING (the front door)
python analysis/refresh.py --check  # validate data & column maps only, no rebuild
```

`refresh.py` runs the whole 25-step pipeline. Nothing is hard-coded — thresholds, price
bands, data sources and cost/lease benchmarks live in `config/deal_dashboard.yml`.

## Where things are

- `analysis/` — the pipeline (config.py, refresh.py, manifest.py, mls_normalize.py, the
  analysis modules, and build_excel / build_dashboard / build_report / build_neighborhood_reports).
- `config/deal_dashboard.yml` — the single control panel (thresholds + data maps + costs).
- `data/raw/…` — drop new MLS / land / income / lease CSV exports here; re-run refresh.py.
- `data/processed/` — cleaned tables + `*_bundle.json` + `manifest.json` (the "data as of" vintage).
- `outputs/Fort_Lauderdale_PPSF_Normalized.xlsx` — the self-contained workbook. Opens on a
  visual **Dashboard** tab (KPIs, job→tab navigator, key charts), with a full **Index** and
  every data tab in the one file.
- `dashboard/index.html` — the same dashboard as an interactive web page.

## Conventions

- Add more data over time by dropping exports into `data/raw/…` and re-running `refresh.py`;
  the manifest re-stamps the "data as of" date everywhere. Adding a new asset class = clone
  one `assets:` block in the config and point a module at it.
- Keep the skill copy in `.claude/skills/deal-dashboard/scripts/` in sync when you change an
  `analysis/` script (the skill is the portable, reusable version).
- Everything is a data-backed **screening signal, not a per-home appraisal** — keep that framing.
