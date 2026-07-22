# Input data — BeachesMLS / RAPB "Agent Single Line — COM" exports

Drop one or more of these commercial MLS exports as `*.csv` in this folder
(`commercial/data/raw/`). The loader (`analysis/cre_common.py`) reads **every** CSV here that
has the MLS columns, concatenates them, de-dupes by MLS number, and keeps the most-progressed
status per listing. The three exports this was built on:

| File (any name) | Status codes inside | Meaning |
|---|---|---|
| closed/pending/rented pull | `CS`, `PS`, `R` | closed sales, pending, rentals |
| active pull | `A`, `AC` | active + active-contingent (live inventory) |
| off-market pull | `X`, `C`, `W`, `T` | expired / cancelled / withdrawn / temp-off (failed) |

## Columns the loader reads

The export is the fixed BeachesMLS single-line layout. The loader keys off these headers:

| Column | Used as |
|---|---|
| `MLS # Link` | listing id (de-dupe key) |
| `St` | status code → Sold / Active / Pending / UnderContract / Cancelled / Expired / Withdrawn / TempOff / Rented |
| `Area` | submarket (MLS area code, e.g. `3370` → "Area 3370") |
| `Address` | address |
| `Current Price` | asking / current price |
| `Sale Price` | closing price (populated on closed `CS` rows) |
| `Year Built` | → age |
| `Prop Type` | `COM/Sale` vs `COM/Lease` — leases are excluded from the $/SqFt sale analysis |
| `Style of Property` | refines the generic "Commercial" bucket |
| `Type of Property` | **asset class** → Multifamily / Office / Retail / Industrial / Mixed Use / Hotel / Restaurant / Flex / Special Purpose / Commercial (other) |
| `Property SqFt` | building size — the $/SqFt denominator |
| `Waterfront Property (Y/N)` | waterfront flag |
| `#Bays` | loading bays (industrial context) |

## What this data does and doesn't contain

**Contains:** price, building SqFt, asset type, year built, zoning, area, waterfront, status.
So the hard, factual metric is **price per SqFt**.

**Does NOT contain:** NOI, rents, cap rate, occupancy, expenses, or unit counts. Every
income figure in the dashboard (NOI, cap rate, value, returns) is therefore **derived from
editable industry-norm assumptions** — see `analysis/cre_assumptions.py`. Tune them live in
`dashboard/index.html`.

## Using a different / fresh pull

Replace the CSVs here and re-run `python analysis/run_all.py`. If your export uses different
status letters or header names, edit `STATUS_MAP` / the column references at the top of
`analysis/cre_common.py`. To point the income assumptions at your own numbers, edit
`DEFAULTS` in `analysis/cre_assumptions.py` (or just drag the sliders in the dashboard).

## Tunables

- `analysis/cre_common.py`: `PPSF_LO/HI` (plausible $/SqFt band), `MIN_SEG_SOLD`, `PRICE_BANDS`.
- `analysis/cre_normalize.py`: `MIN_GEO`, `MIN_ASSET` (fold thin submarkets/types).
- `analysis/cre_assumptions.py`: `DEFAULTS` (per-type rent/vacancy/opex/cap), `FINANCE`.
- `CRE_SOLD_MONTHS` env var: the window closed sales are assumed to span (absorption).
