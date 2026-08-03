# 451 White Horse Pike, Atco, NJ 08004

Lease and sale comp analysis for a single-tenant net lease acquisition.
Waterford Township, Camden County. ±4,400 SF former bank branch on ±3.13 AC
with a 3-lane drive-thru, leased to Holistic Solutions (cannabis dispensary).

Offered at **$1,600,000 / 8.25% cap** on $132,000 NOI.

## Files

| File | What it is |
|---|---|
| `analysis.html` | The acquisition case at $1,100,000 — comps, re-rent economics, backfill strategy, land monetization, cap rate positioning, returns, risk register, offer strategy |
| `offer_case_1100k.py` | Returns on the $1.1M basis, payback, downside yields and the negotiation ladder |
| `land_upside_model.py` | Outparcel ground lease and EV charging licence sizing, and value created |
| `underwriting_model.py` | Reversion scenario model and unlevered IRR by purchase price |
| `sensitivity_model.py` | Renewal-probability sensitivity and the re-rent matrix by tenant type |

Both scripts are dependency-free — `python3 underwriting_model.py`.

## Position: offering $1,100,000

The analysis supports the offer. At $1.1M the going-in cap is **12.00%** ($250/SF),
expected unlevered IRR is **12.0%**, and **no modelled scenario loses money** — the
worst case (tenant fails, building goes dark, liquidate land and shell) still
returns **+6.2%**. At the $1.6M ask that same scenario returns −1.4%.

The offer sits at the market-rent capitalization value of $1,106,000, meaning the
building is bought at its plain conventional-use worth and the cannabis premium,
the renewal option and the excess land are unpaid-for upside.

Practical ceiling **$1,250,000** (9.3% expected). Above $1.3M the margin of safety
is gone.

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
- Four independent value checks converge on **$1.11M–$1.43M**, indicating a
  value around **$1.30M** — so $1.1M is roughly 15% inside value and 31% inside
  the ask.
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
