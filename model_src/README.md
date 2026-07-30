# Assemblage Underwriting Model — developer guide

A programmatic institutional real-estate underwriting model. Python generates a fully
formulated, self-recalculating Excel workbook; there is **one input surface** and a
**machine-readable input/output contract** so it can be driven from, or plugged into,
other systems. Built as a reusable template for covered-land / assemblage plays.

```
model_src/                      python engine (openpyxl)
  build_model.py                orchestrator → ../Shahidi_Assemblage_Model.xlsx
  mblib.py                      sheet wrapper, styles, number formats, cell registry
  tab_assumptions.py            THE control surface (GLOBAL_SECTIONS + per-asset _blocks)
  tab_*.py                      one module per tab (asset tabs, income, scenarios, …)
  data.py / configs.py          per-asset facts + assumption dicts
  export_inputs.py              → ../model_inputs.json  (the input contract)
  validate.py                   headless recalc (formulas engine) — 0-error gate
../Shahidi_Assemblage_Model.xlsx   the deliverable (13 tabs)
../model_inputs.json            generated input contract (integration surface)
../MODEL_AUDIT.md               math/formula review + data-gap register
```

## Build & validate

```bash
cd model_src
python3 build_model.py                                  # writes ../Shahidi_Assemblage_Model.xlsx
python3 validate.py ../Shahidi_Assemblage_Model.xlsx    # must print "formula errors: 0"
python3 export_inputs.py                                # regenerate ../model_inputs.json
```

`validate.py` recalculates every formula with the `formulas` package (no Excel/LibreOffice
needed) and fails on any `#REF`/`#DIV0`/`#NUM`. Treat a non-zero error count as a broken build.

## The contract (how another system plugs in)

**Inputs — `model_inputs.json`.** Generated from the model source, so it never drifts.
Structure:

- `global[]` — the global driver sections (valuation, financing, acquisition costs, prior-sale
  basis, assemblage premium, land/redevelopment). Each driver: `key, label, value, unit,
  type, confidence, drives`.
- `assets{}` — per asset: `control_tab_inputs[]` (price/rents/occupancy/opex/caps/debt),
  `detail_inputs{}` (growth, TI/LC, reserves, closing), and `verified_facts{}` where public.
- `office_owner_roster[]` — the fractured-condo buy-out map (owner, SF, basis, date).
- `market_research{}` — the mid-2026 comp set.
- `outputs{}` — the key **named cells** the model produces (price, NOI, IRRs, DSCR, premium,
  buy-out, residual, …), keyed by tab, with plain-English meaning.

Every ratio is a decimal (`0.065` = 6.5%). Confidence is `VERIFIED | REPORTED | MODELED |
ESTIMATED` (see `conventions.confidence`).

**Outputs.** Every meaningful cell is *named* (openpyxl defined-name via the `mblib` registry).
`registry.json` (written by `build_model.py`) maps `sheet → name → cell coord`, so a consumer
can read a specific result without scraping the grid. The `outputs{}` block in the JSON lists
the headline names.

## Fill in real data as you get it  ← the easy path

`overrides.json` is the fill-in-the-blanks surface. It ships pre-populated with every input we
**don't have solid data for yet, or that's modeled and worth confirming** — each with its
current value and a `status` telling you what it is and where to source the real number:

```jsonc
{ "assets": { "sunrise": {
    "price": { "value": 8500000, "status": "⚠️ REPORTED ~$8.5M — VERIFY at BCPA / broker" } } },
  "global": {
    "RATE":  { "value": 0.065,   "status": "🔶 MODELED — replace with a lender term sheet" } } }
```

Put a confirmed number in any `value` field, then `python3 build_model.py` — it flows through
every tab. Leave a field alone and the model keeps its current assumption; nothing breaks.
`build_model.py` calls `apply_overrides()` **before** building, so `overrides.json` always wins
over the coded defaults. Regenerating `overrides.template.json` (via `export_inputs.py`) never
touches your `overrides.json`. `global` patches by driver name; `assets.<asset>` patches by
input key — both keys are listed in `model_inputs.json`.

## Change a default in code

The **Assumptions** tab is also a live control surface — every blue cell drives the model by
cross-sheet link, so editing a blue cell and reopening recalculates the workbook. To move a
*default* in code:

- **Global drivers** live in `tab_assumptions.GLOBAL_SECTIONS` (data, not code) — the workbook
  builder, `export_inputs.py`, and `apply_overrides()` all read it.
- **Per-asset headline inputs** come from `tab_assumptions._blocks()`, sourced from `data.SH`,
  `configs.PUBLIX_CFG` / `KARLUEN_CFG`, `tab_office.A`, `tab_land.A` (Publix leaseback terms too).
- **Prior-sale basis** (what each owner paid) is a single source of truth in the global
  `PRIOR SALE / SELLER BASIS` section, linked by both the HBU history and the Exec scorecard.

Edit the value, rebuild, re-export, re-validate. (For a one-off real value, prefer `overrides.json`.)

## Repoint at a NEW assemblage (template use)

1. Reset `GLOBAL_SECTIONS` (caps, hold, financing, premium, land ladder) and the prior-sale block.
2. Reset each asset's `data.py` / `configs.py` dict (price, rents, occupancy, opex, caps, debt).
   Retail/office/land archetypes already differ — copy the closest for a new asset.
3. Replace the office owner roster and each asset's tenant rows with the real ones.
4. Add/drop an asset via the component lists in `tab_hbu` / `tab_exec` / `tab_assemblage`.
5. Rebuild → validate (0 errors) → export JSON → confirm ⚠️ REPORTED figures at the county.

Or, for incremental real data on the current deal, just edit `overrides.json` and rebuild.
See `../MODEL_AUDIT.md` for what is verified vs. modeled and the outstanding data gaps.

## Tabs

Grouped by reading section (tab colours match): **SEE** `Start Here · Executive Summary` · **MAKE**
`Deal Book · Partner Returns` · **PLAY** `Review Board · Capital Stack` · **CHANGE** `Assumptions` ·
**MATH** `Income Valuation · Scenarios · Assemblage · Highest & Best Use` · **ASSETS** `Shahidi · Publix &
Starbucks · Sunrise Plaza · Office Condo · Land` · **SOURCES** `Notes & Sources`.

- **Start Here** — the reading map: the deal in three lines, the four numbers that matter, and which tab
  answers which question. The front door for anyone opening the workbook.
- **Partner Returns** — the LP/GP equity waterfall (8% pref, 70/30 promote) on the consolidated levered
  cash flow: LP vs GP IRR/multiple, the promote earned, and the LP's downside cushion.
- **Deal Book** — the acquisition & execution package: deal-at-a-glance, per-owner acquisition
  strategy (basis / structure / motivation / approach / contingency), whole-deal Sources & Uses to
  control all five, financing & returns, a risk register, and an execution timeline. Numbers are
  live-linked; deal intel is editable (`ACQ_STRATEGY` / `RISKS` / `TIMELINE` in `tab_dealbook.py`).
- **Review Board** — interactive, closed-form sensitivity grids + driver tornado; every grid is
  anchored to the actual consolidated reversion so the base reproduces the headline multiple.
- **Capital Stack** — sandbox to flex leverage/rates/equity: the stack (senior/mezz/equity) at
  each deal price, DSCR/debt-yield/LTC, GP/LP split, and affordability (max price + assemblage
  capacity from the equity you have). Blue cells are a sandbox and don't disturb the model.
- **Income Valuation** — consolidated cash flows; the single source of truth for portfolio returns
  (one IRR on combined cash flows — never averaged asset IRRs).

## Formatting discipline

Blue-on-yellow = input · Black = formula · Green = verified fact / cross-sheet link ·
Gold-on-navy = header / total / KPI. Accounting formats (negatives in parens, zero as dash),
gridlines off, freeze panes, `fullCalcOnLoad = True` so Excel recalculates on open.

## Confidence flags

- ✅ **Shahidi & Publix** — BCPA / Sunbiz / recorded-deed verified.
- ⚠️ **Sunrise Plaza, Office Condo, Land** — reported (LoopNet / Sunbiz / press); BCPA/Clerk were
  egress-blocked in the build environment. Verify folios at bcpa.net before close.
- 🔶 **All rents / cap rates / financing** — modeled from mid-2026 market research.
