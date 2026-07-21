# E Sunrise Blvd Assemblage — Underwriting Model

Institutional-grade acquisition underwriting for a five-asset covered-land-play
assemblage on the E Sunrise Blvd hard corner at the Galleria, Fort Lauderdale FL.

**Deliverable:** `../Shahidi_Assemblage_Model.xlsx` — 7 tabs, zero formula errors,
every asset modeled levered **and** unlevered.

## Workbook tabs

| # | Tab | Contents |
|---|---|---|
| 1 | **Executive Summary** | KPI banner, deal thesis, asset scorecard, capital & covered-land math, recommendation — all live green links |
| 2 | **Assemblage** | Covered-land roll-up: control cost, blended cap, land basis, assemblage premium → total acquisition cost, highest-and-best-use (redevelopment residual → hold) |
| 3 | **Shahidi Retail** | 26,272 SF (Galleria Plaza). Tenant rent roll, 10-yr DCF, NPV, reversion, debt, unlev + lev returns, P&L. Reproduces the BuildSpec §8 QA targets |
| 4 | **Publix & Starbucks** | Grocery + pad valued off market rent; income value vs. $25M land basis (the covered-land gap) |
| 5 | **Sunrise Plaza** | 2465–2485 E Sunrise (incl. 2473 Daoud's Fine Jewelry). Restaurant/jeweler value-add lease-up |
| 6 | **Office Condo** | Galleria Corporate Centre (2455). Two-owner lease-position valuation (Main Street Fund 57.4% + International Sunrise) |
| 7 | **Land** | 1040 Bayview covered-land underwrite: 4 valuation approaches, interim income, redevelopment residual (negative → hold) |

## Formatting discipline

- **Blue on yellow** = hardcoded input (the only cells to change)
- **Black** = formula / calculation
- **Green** = BCPA-verified fact or cross-sheet link
- **Gold on navy / dark** = headers, totals, KPI boxes
- Arial, accounting number formats (negatives in parens, zero as dash), gridlines off, freeze panes.

## Confidence flags

- ✅ **Shahidi & Publix** — BCPA / Sunbiz / recorded-deed verified (do not re-verify).
- ⚠️ **Sunrise Plaza, Office Condo, Land** — reported (LoopNet / Sunbiz / press);
  BCPA was blocked in the build environment. Verify folios at bcpa.net before close.
- 🔶 **All rents / cap rates / financing** — modeled from mid-2026 market research.

## Rebuild

```bash
cd model_src
pip install openpyxl
python3 build_model.py            # writes ../Shahidi_Assemblage_Model.xlsx
python3 validate.py ../Shahidi_Assemblage_Model.xlsx   # recalc + error scan (needs `formulas`)
```

Files: `mblib.py` (formatting engine) · `data.py` / `configs.py` (facts + assumptions) ·
`tab_*.py` (per-tab builders) · `build_model.py` (assembles & orders tabs) ·
`validate.py` / `preview.py` (QA).

*Validation uses the `formulas` Python engine (LibreOffice headless is unavailable
in this sandbox). Set `wb.calculation.fullCalcOnLoad = True` so Excel recalculates on open.*
