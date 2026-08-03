# 451 White Horse Pike, Atco, NJ 08004

Lease and sale comp analysis for a single-tenant net lease acquisition.
Waterford Township, Camden County. ±4,400 SF former bank branch on ±3.13 AC
with a 3-lane drive-thru, leased to Holistic Solutions (cannabis dispensary).

Offered at **$1,600,000 / 8.25% cap** on $132,000 NOI.

## Files

| File | What it is |
|---|---|
| **`451 White Horse Pike - Acquisition Analysis.pdf`** | **9-page report. Page 1 is a standalone executive summary; §1–10 carry the full detail.** |
| **`451 White Horse Pike - Acquisition Model.xlsx`** | **Live 11-tab model. Change the offer price on `Assumptions` and everything recalculates.** |
| `analysis.html` | The same analysis as a web page |
| `analysis-print.html` | Print source for the PDF |
| `build_model.py` | Rebuilds the workbook from scratch |
| `financing_stress_tests.py` | Loan sizing, DSCR, levered IRR, tenant-health coverage, sensitivity and exit analysis |
| `audit_consistency.py` | Recomputes every headline figure independently and cross-checks it against the workbook and the PDF |
| `offer_case_1100k.py` | Returns on the $1.1M basis, payback, downside yields and the negotiation ladder |
| `land_upside_model.py` | Outparcel ground lease and EV charging licence sizing, and value created |
| `underwriting_model.py` | Reversion scenario model and unlevered IRR by purchase price |
| `sensitivity_model.py` | Renewal-probability sensitivity and the re-rent matrix by tenant type |

The `.py` models are dependency-free (`python3 underwriting_model.py`); `build_model.py` needs `openpyxl`.

### Workbook tabs

`Executive Summary` · `Assumptions` · `Reversion Scenarios` · `Returns` · `Valuation` ·
`Re-Rent Analysis` · `Re-Leasing Options` · `Land Upside` · `Financing` · `Stress Tests` ·
`Lease Comps` · `Sale Comps` · `Risks & Diligence`

853 formulas, zero errors; every headline figure independently verified against
`audit_consistency.py`. Blue cells are inputs; the yellow cell on `Assumptions` is the
master lever (our offer price).

## Position: offering $1,100,000

The analysis supports the offer. At $1.1M the going-in cap is **12.00%** ($250/SF),
expected unlevered IRR is **12.0%**, and **no modelled scenario loses money** — the
worst case (tenant fails, building goes dark, liquidate land and shell) still
returns **+6.2%**. At the $1.6M ask that same scenario returns −1.4%.

The offer sits at the market-rent capitalization value of $1,106,000, meaning the
building is bought at its plain conventional-use worth and the cannabis premium,
the renewal option and the excess land are unpaid-for upside.

Practical ceiling **$1,250,000** (9.3% expected). Above $1,300,000 we would be
paying more than the property is worth.

## Headline findings

- In-place rent is **$30.00/SF NNN, flat for the full 10-year base term**.
  Conventional market rent for this box is **$20–24/SF NNN** — the lease
  carries roughly a 36% cannabis premium that expires with the tenant.
- Re-rent range to a conventional user: **$88,000–$106,000/yr**
  (a 20–33% roll-down) after 9–18 months of downtime and $150k–$250k of
  landlord capital.
- Best backfills in order: credit union / community bank (turnkey — vault and
  drive-thru already in place), then urgent care / veterinary, then a QSR pad
  on the ±2.5 acres of excess land.
- Expected unlevered IRR at the $1.6M ask is **4.3%**. Even assuming a 90%
  renewal probability it only reaches 7.5%.
- Four independent value methods produce a weighted indication of **$1,252,500**
  (in-place income 40%, assessor 20%, county $/SF 15%, market-rent floor 25%) —
  so $1.1M is **12% inside value and 31% inside the ask**.
- **Re-leasing options and timing:** six paths back to full rent. Fastest and
  cheapest is a bank or credit union (~10 months, ~$22k landlord cost — the vault
  and drive-thru are already there); deepest demand is medical/urgent care
  (~17 months, ~$264k); cannabis carries the longest regulatory lag (~24 months).
- **The corner matters.** Two frontages on Route 30 and Cooper Folly Road give
  signage on two streets, secondary-road access, drive-thru circulation that a
  mid-block parcel cannot support, and a physically realistic second pad.
- **Objective is one re-tenanting, not churn.** Target a 10–15 year NNN lease
  with escalations (medical or bank/credit union) and then hold passively.
  Short conventional retail deals roll every five years and are the outcome to
  avoid; demising the box for a QSR trades one covenant for two.
- **Leverage:** at $1.1M, 55% LTV private debt at 10% gives **2.00x DSCR,
  13.3% cash-on-cash and a 14.85% levered IRR** — leverage adds 285 bps. At the
  $1.6M ask, DSCR falls to 1.38x and the levered return is **−3.32%**.
  **$1,250,000 is almost exactly the leverage-neutral point**, independently
  confirming the ceiling the valuation work produced.
- **Tenant health is the honest risk.** Gross occupancy cost is $193,400
  ($43.95/SF). The store needs roughly **$2.15M of annual sales** to keep
  occupancy under 9%. Getting the tenant's actual sales is the single
  highest-value diligence item.
- **Robustness:** the conclusion does not depend on the 40% renewal assumption —
  even at 20% the offer returns 10.50%. Market rent would have to fall to ~$18/SF,
  below every conventional comp on the corridor, before the basis stopped being
  covered by the building alone.
- **Exit:** re-letting to a non-cannabis covenant removes the financing
  constraint, widening the buyer pool from cash-only cannabis specialists to the
  whole institutional net-lease market — worth roughly 75–125 bps of exit cap.
- **Land upside, excluded from every return figure:** ±2.48 developable acres
  (site coverage is only 3.2%). An outparcel ground lease plus a third-party EV
  fast-charging licence conservatively adds **$75,000/yr** of NOI and about
  **$661,000** of value net of cost — taking yield on cost to 18.8%. With a pad
  in place, even a dark building re-let at $18/SF still yields 14.0%.
  Gating item: confirm whether the lease demises the entire 3.13 AC to the
  tenant, which would block development without their consent.

## Basis and caveats

Deal terms are from the Matthews offering memorandum. Assessment, GLA, zoning
and prior use are from public tax-assessor records. Comparables were assembled
from public listing platforms, brokerage transaction announcements and
published Q1 2026 net lease research — **predominantly asking rates and
marketed cap rates, not verified closed transactions.** Re-run against CoStar,
Crexi and Camden County deed records before submitting an offer. Operating
expense, TI, downtime and leasing-commission figures are analyst estimates and
reversion probabilities are judgmental. Not an appraisal.
