# 451 White Horse Pike, Atco, NJ 08004

Lease and sale comp analysis for a single-tenant net lease acquisition.
Waterford Township, Camden County. ±4,400 SF former bank branch on ±3.13 AC
with a 3-lane drive-thru, leased to Holistic Solutions (cannabis dispensary).

Offered at **$1,600,000 / 8.25% cap** on $132,000 NOI.

## Files

| File | What it is |
|---|---|
| **`451 White Horse Pike - IC Deck.pdf`** | **THE presentation document, and the complete analysis. 19 landscape slides in four parts plus two appendices, built to take a reader from cold to an approved offer.**<br>Part 1 decision · Part 2 asset and price · Part 3 return · Part 4 risk and execution · Appendix A price sensitivity · Appendix B site quality. |
| **`451 White Horse Pike - Acquisition Model.xlsx`** | **Live 14-tab model, 898 formulas. Change the offer price on `Assumptions` and everything recalculates.** |
| `analysis.html` | The same analysis as a web page |
| `deck.html` | Source for the IC deck |
| `build_model.py` | Rebuilds the workbook from scratch |
| **`ONE_MODEL.py`** | **The single source of truth. One 10-year hold, four cases. Every figure in the deck comes from here.** |
| **`METRICS.py`** | **The full standard metric set: cap rates, IRR, cash-on-cash, DSCR, debt yield, equity multiples, payback, yield on cost.** |
| `growth_case_model.py` | Ten-year floor / base / growth cases, levered and unlevered, plus the value bridge |
| `comp_adjustment_grid.py` | Lease comp adjustment grid, exclusions with reasons, and the sale comp schedule |
| `broker_comparison.py` | Ask-to-offer bridge, combined broker/our comp set, and the size-vs-rent regression |
| `financing_stress_tests.py` | Loan sizing, DSCR, levered IRR, tenant-health coverage, sensitivity and exit analysis |
| `price_ladder.py` | Re-runs all four cases at every price on the negotiating ladder (Appendix A) |
| `consistency_gate.py` | Gate: asserts the deck PDF carries every canonical figure and no superseded one |
| `audit_consistency.py` | Recomputes every headline figure independently and cross-checks it against the workbook and the PDF |
| `offer_case_1100k.py` | Returns on the $1.1M basis, payback, downside yields and the negotiation ladder |
| `land_upside_model.py` | Outparcel ground lease and EV charging licence sizing, and value created |
| `underwriting_model.py` | Reversion scenario model and unlevered IRR by purchase price |
| `sensitivity_model.py` | Renewal-probability sensitivity and the re-rent matrix by tenant type |

The `.py` models are dependency-free (`python3 underwriting_model.py`); `build_model.py` needs `openpyxl`.

### Workbook tabs

`Executive Summary` · `Assumptions` · `Reversion Scenarios` · `Returns` · `Valuation` ·
`Re-Rent Analysis` · `Re-Leasing Options` · `Land Upside` · `Growth Plan` · `Financing` · `Stress Tests` ·
`Lease Comps` · `Sale Comps` · `Risks & Diligence`

898 formulas, zero errors; every headline figure independently verified against
`audit_consistency.py`. Blue cells are inputs; the yellow cell on `Assumptions` is the
master lever (our offer price).

## Us vs the broker, side by side

The $500,000 gap between their ask and our offer decomposes to one argument:

| Step | Amount |
|---|---|
| Their ask — $132,000 contract rent ÷ 8.25% | $1,600,000 |
| 1. Use market rent ($22.00/SF), not their tenant's rent | (426,700) |
| 2. Widen the yield 8.25% → 8.75% for flat rent, 6.5 yrs, personal guarantees | (67,000) |
| 3. Negotiating margin | (6,300) |
| **Our offer** | **$1,100,000** |

**85% of the gap is a single question: is $30.00/SF a market rent?** Negotiate the rent,
not the cap rate.

Slides 6–8 present this as schedules rather than prose: a **16-row lease comp
schedule** (every comp, both sides, with size, rent/SF, annual, drive-thru, source
and status), an **adjustment grid** in appraisal format, and a **sale comp schedule**.

| # | Comparable | City | SF | Rent/SF | Size | Loc | Term | Adjusted |
|---|---|---|---|---|---|---|---|---|
| 1 | 501 Delsea Drive | Sewell | 1,373 | $39.33 | −30% | −10% | — | **$24.78** |
| 2 | 340 S White Horse Pike | Berlin | 1,750 | $27.43 | −20% | — | — | **$21.94** |
| 3 | 341 N WHP (Avis Budget) | Lawnside | 3,300 | $27.96 | −10% | −10% | −5% | **$21.52** |
| | *Indicated range* | | | | | | | *$21.52–$24.78* |
| | **Concluded — we use** | | | | | | | **$22.00** |

On the comps, four of the broker's seven are build-to-suit deals where rent repays land
*and* construction — which is why 7 Brew reads as $303.92/SF on a 510 SF kiosk. Fitting
the size-vs-rent curve on second-generation buildings only (both comp sets combined,
R² 0.89) puts **4,400 SF at $25.74/SF**. His own best comp — Avis Budget, same road,
signed June 2025 — adjusts to **$21.52**. We underwrite **$22.00** throughout, the
conservative end; at $25.74 the floor is simply higher than presented.

## Returns — the buyer's view

Slide 9 carries the decision in four rows, ordered by likelihood, with a range bar
showing that **every outcome lands between 6.1% and 18.3%**. Slide 10 is labelled
*backup detail* and carries the full metric set plus a plain-English glossary
(cap rate, IRR, cash-on-cash, equity multiple, DSCR) so no term trips the reader up.

| Outcome | What has to happen | Return | Cash back | Likelihood |
|---|---|---|---|---|
| **Renewal** | Tenant takes its option at $154,000 | **14.95%** | $3,061,865 (2.78×) | Likeliest |
| **Growth** | Land let from yr 3 *and* quality re-let | **18.33%** | $3,999,438 (3.64×) | If we execute |
| Base | Tenant leaves, re-let at market, no land | 8.40% | $1,928,561 (1.75×) | Realistic |
| Floor | Tenant fails, weak re-let, no land | 6.13% | $1,634,677 (1.49×) | Downside |

## Full metric set — all from one model

**One 10-year hold at $1,100,000. Four cases. Every number below is from `ONE_MODEL.py`.**

| Metric | Floor | Base | Renewal | Growth |
|---|---|---|---|---|
| Exit NOI | $81,180 | $99,220 | $154,000 | $208,240 |
| Exit cap rate | 9.00% | 8.75% | 9.25% | 8.00% |
| Sale price, yr 10 | $902,000 | $1,133,943 | $1,664,865 | $2,603,000 |
| **Unlevered IRR** | **6.13%** | **8.40%** | **14.95%** | **18.33%** |
| Equity multiple | 1.49x | 1.75x | 2.78x | 3.64x |
| **Levered IRR** (55% LTV) | **−1.08%** | **6.29%** | **19.40%** | **24.43%** |
| Levered equity multiple | 0.94x | 1.53x | 3.82x | 5.71x |
| Yield on cost | 7.4% | 9.0% | 14.0% | 16.7% |

**Acquisition:** $1,100,000 · $250.00/SF · NOI $132,000 · **going-in cap 12.00%** ·
cap on market rent 8.80% · cap at their ask 8.25%

**Debt (55% LTV, 10%, 25-yr):** loan $605,000 · equity $495,000 · constant 10.90% ·
debt service $65,972 · **DSCR 2.00x** · **debt yield 21.8%** · break-even 50% of rent

**Cash-on-cash yr 1:** unlevered 12.00% (= the cap rate) · **levered 13.34%** ·
payback 8.3 yrs unlevered / 7.5 yrs levered

**Caveat, stated plainly:** in the floor case *with* debt the levered IRR is −1.08% and
the equity multiple 0.94x — you get back slightly less than you put in. Unlevered that
case still returns 6.13% and 1.49x. Buy for cash or hold leverage to 35–40% and every
case is positive. At their $1.6M ask the floor case is −39.93% levered.

## Position: offering $1,100,000

The analysis supports the offer. At $1.1M the **going-in cap rate is 12.00%** ($250/SF),
and **no modelled case loses money on an unlevered basis** — the 10-year unlevered IRR
runs from **6.13%** (floor: tenant fails, weak re-let) to **18.33%** (growth: land let
and quality re-let), with the likeliest single outcome — the tenant renewing — at
**14.95%**. At the $1.6M ask the same four cases run 0.31% to 12.25%.

The offer sits at the market-rent capitalization value of $1,106,000, meaning the
building is bought at its plain conventional-use worth and the cannabis premium,
the renewal option and the excess land are unpaid-for upside.

Practical ceiling **$1,250,000** — base-case 10-yr unlevered IRR ~6%, renewal ~12.3%,
and the point at which leverage stops adding return. Above $1,300,000 we would be paying
more than the indicated value of $1,252,500.

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
- **The listing agent's comps confirm our rent, not his price.** Five of the seven
  he sent are build-to-suit deals where rent repays land *and* construction
  (7 Brew reads as $303.92/SF on a 510 SF kiosk; ALDI as $12.96/SF on 19,054 SF)
  — not comparable to re-letting a second-generation box. The two genuine
  lettings, adjusted for size, location and term, indicate **$21.52 and $21.94**,
  confirming the $22 base case. His build-to-suit pad rents ($155,000 for 7 Brew,
  $157,659 for Wendy's) are, however, strong evidence for the outparcel: a ground
  lease typically runs 40–55% of a BTS rent, so the pad estimate rose from
  $55,000 to **$80,000** base.
- **Land upside, excluded from every return figure:** ±2.48 developable acres
  (site coverage is only 3.2%). An outparcel ground lease plus a third-party EV
  fast-charging licence adds **$100,000/yr** of NOI and about **$1.10M** of
  value net of cost — taking yield on cost to 21.1%. With a pad in place, even a
  dark building re-let at $18/SF still yields 16.3%.
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
