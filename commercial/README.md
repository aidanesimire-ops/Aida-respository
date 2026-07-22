# Commercial Deal Dashboard — Fort Lauderdale

Market-pricing intelligence for **commercial real estate** (all asset classes: multifamily,
office, retail, industrial, mixed-use, hotel, …), built from user-provided BeachesMLS
commercial exports. It is the commercial counterpart to the residential PPSF project in the
repo root — same idea, adapted to how commercial is actually priced.

## The core problem this solves

The MLS commercial export gives you **price, size, asset type, age, zoning and location — but
no income** (no NOI, rents, cap rate, occupancy or unit counts). Commercial value is driven by
income, so a pure export can't tell you what anything is *worth*.

So this project runs in **two layers**:

1. **Factual — normalized $/SqFt.** A hedonic removes size, age, asset type and the
   closed-vs-listed gap, giving clean, comparable **$/SqFt by submarket and asset type**.
2. **Assumption-driven — the income view.** Per asset class we attach editable **industry-norm
   assumptions** (market rent $/SqFt, vacancy, expense ratio, cap rate) and derive NOI, implied
   cap, value and full levered returns from them. **Every assumption is a live control** — drag
   it and implied caps, mispricing flags and deal returns recompute in real time.

> This is pricing & screening intelligence, **not** an appraisal. The income numbers are only
> as good as the assumptions — which is exactly why the tool makes them explicit and tunable.

## Deliverables

- **`dashboard/index.html`** — the interactive dashboard (open in a browser; fully self-contained).
  Tune the assumptions at the top and watch everything below move: the $/SqFt map, the live-inventory
  repricing (both a $/SqFt and an income lens), and a full single-deal underwriting model with
  exit-cap and rent sensitivity. **Start here.**
- **`outputs/Commercial_Deal_Dashboard.xlsx`** — a multi-tab workbook. The **Assumptions** tab
  and the formula-driven **Scenario** tab are live (edit the yellow cells).
- **`REPORT.md`** — the written analysis.
- **`outputs/*.png`** — charts for slides/emails.

## Run it

```bash
pip install -r requirements.txt
python analysis/run_all.py
```

Drop fresh BeachesMLS commercial exports in `data/raw/` (see `data/raw/SCHEMA.md`) and re-run.

## Pipeline

| Script | Produces | Purpose |
|---|---|---|
| `cre_common.py` | — | Loader: parse the MLS export, classify asset type & status, compute $/SqFt |
| `cre_assumptions.py` | — | The editable industry-norm assumptions + income derivation |
| `cre_normalize.py` | `cre_*.json/csv` | $/SqFt hedonic by submarket × type; per-listing valuation + assumption income |
| `reprice.py` | `reprice_bundle.json` | Live inventory: $/SqFt & income mispricing, buy list |
| `bands.py` | `segments_bundle.json` | Deal-size bands + absorption by submarket / type |
| `prospects.py` | `prospects_bundle.json` | Failed listings + overpriced actives + failure rate |
| `comps.py` | `comps_bundle.json` | Closed sales behind every number |
| `master_summary.py` | `master_bundle.json` | Master ranked submarket sheet |
| `cre_scenario.py` | — | Single-deal underwriting math (mirrored in the dashboard JS) |
| `build_charts / _excel / _dashboard / _report` | `outputs/`, `dashboard/`, `REPORT.md` | Deliverables |

## Honest limitations

- **No income in the source** — NOI/cap/returns are assumption-driven. Verify rent rolls and
  T-12s before underwriting a real deal.
- **Thin closed-sale counts** in some submarkets/types — read low-count cells as indicative.
- **Area = MLS area code**, not a named neighborhood. **Units are unknown**, so multifamily is
  analyzed on $/SqFt, not $/unit.
- **Lease listings** (different rate bases) are excluded from the $/SqFt sale analysis.
