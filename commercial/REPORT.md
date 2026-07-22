# Commercial Deal Dashboard — Fort Lauderdale

Market intelligence on **984 commercial listings** (331 valid sale comps, 69 closed; 521 lease listings) from user-provided BeachesMLS exports (com_active.csv, com_cancelled.csv, com_closed_pending_rented.csv).

> **The source has no income data.** These MLS exports carry price, size, asset type, age, zoning and location — but **no NOI, rent, cap rate or unit counts**. So the factual layer here is **price-per-SqFt**, and every income figure (NOI, cap rate, value, returns) is **derived from editable industry-norm assumptions** you can tune live in the dashboard. Treat this as pricing & screening intelligence, not appraisal.

## Two layers

**1. Factual — normalized $/SqFt.** A hedonic strips size, age, asset type and the closed-vs-listed gap out of raw pricing so areas and property types are comparable:

```
log($/SqFt) ~ log(sqft) + age + closed + C(asset_type) + C(submarket)
```

Fit R² = **0.585** (n=125); closed sales price about **-26%** vs live asks. Market-wide normalized **$182/SqFt**.

**2. Assumption-driven — the income view.** For each asset class we assume a market rent ($/SqFt/yr), vacancy, expense ratio and cap rate, then derive `NOI = SqFt × rent × (1−vacancy) × (1−opex)`, an implied cap at the asking price, and a value at the market cap. **Every one of those is a live control** — the whole point is to dial them to your read and watch value, cap and returns move.

### Default assumptions by asset class

| Asset type | Rent $/SqFt | Vacancy | Opex % EGI | Market cap | Median $/SqFt | # |
|---|---|---|---|---|---|---|
| Multifamily | $18 | 6% | 42% | 5.50% | $177 | 90 |
| Office | $34 | 15% | 45% | 8.00% | $197 | 29 |
| Retail | $23 | 8% | 22% | 6.75% | $247 | 25 |
| Industrial | $12 | 5% | 15% | 6.25% | $150 | 34 |
| Mixed Use | $16 | 10% | 35% | 6.75% | $136 | 33 |
| Hotel | $100 | 30% | 62% | 8.50% | $347 | 11 |
| Restaurant | $33 | 10% | 20% | 6.50% | $365 | 8 |
| Flex | $20 | 8% | 20% | 7.00% | $345 | 3 |
| Special Purpose | $22 | 15% | 30% | 7.50% | $319 | 2 |
| Commercial (other) | $22 | 12% | 30% | 7.00% | $195 | 96 |

*Defaults are calibrated so a typically-priced building of each type prices near its market cap, and are realistic South-Florida gross rents — starting points, not gospel.*

## Submarkets, ranked (normalized $/SqFt)

| Submarket | Norm $/SqFt | vs city | Median price | Top type | Mo supply | Stance |
|---|---|---|---|---|---|---|
| Area 3600 | $268 | +47% | $1.80M | Retail | 18 | Neutral |
| Area 3810 | $253 | +39% | $3.45M | Multifamily | — | Neutral |
| Area 3380 | $242 | +33% | $2.10M | Commercial (other) | 18 | Neutral |
| Area 3370 | $186 | +2% | $1.70M | Multifamily | 8 | Neutral |
| Area 3500 | $173 | -5% | $1.33M | Commercial (other) | 4 | Neutral |
| Area 3800 | $170 | -6% | $1.07M | Commercial (other) | 28 | Neutral |
| Area 3470 | $153 | -16% | $1.90M | Multifamily | 22 | Neutral |
| Area 3460 | $126 | -31% | $1.40M | Multifamily | — | Neutral |
| Area 3160 | $99 | -46% | $732K | Commercial (other) | 4 | Neutral |

## Repricing live inventory (at default assumptions)

Of **56** live listings: **20 underpriced**, 10 fair, **26 overpriced** — on the income lens (asking vs value at assumed rents/cap). Below value = a higher implied cap = a buy. Note these flags **move as you change assumptions**.


**Top underpriced (income basis, default assumptions):**

| Address | Submarket | Type | Asking | Value | Gap | Why |
|---|---|---|---|---|---|---|
| 1313 S Andrews Avenue | Area 3800 | Commercial (other) | $2.35M | $5.40M | -56% | implied cap 16.08% vs 7.00% market (given assumed rents); 36% under comp $/sqft; asking ~56% below assumption value ($5.40M) |
| 1225 SE 2nd Avenue | Area 3800 | Office | $2.00M | $4.33M | -54% | implied cap 17.36% vs 8.00% market (given assumed rents); asking ~54% below assumption value ($4.33M) |
| 701 W Las Olas Boulevard | Area 3470 | Commercial (other) | $1.90M | $3.99M | -52% | implied cap 14.70% vs 7.00% market (given assumed rents); 34% under comp $/sqft; asking ~52% below assumption value ($3.99M) |
| 1518-1522 NE 4th Ave | Area 3370 | Retail | $750K | $1.53M | -51% | implied cap 13.75% vs 6.75% market (given assumed rents); 42% under comp $/sqft; asking ~51% below assumption value ($1.53M) |
| 2001-2007 NW 21st Ave | Area 3560 | Mixed Use | $800K | $1.54M | -48% | implied cap 13.03% vs 6.75% market (given assumed rents); 59% under comp $/sqft; asking ~48% below assumption value ($1.54M) |
| 355 NW 32nd St Unit#1-6 | Area 3720 | Multifamily | $1.30M | $2.46M | -47% | implied cap 10.42% vs 5.50% market (given assumed rents); 55% under comp $/sqft; asking ~47% below assumption value ($2.46M) |
| 423 SE 19th St | Area 3800 | Office | $799K | $1.36M | -41% | implied cap 13.61% vs 8.00% market (given assumed rents); 10% under comp $/sqft; asking ~41% below assumption value ($1.36M) |
| 1026 NW 9th Ave | Area 3424 | Retail | $1.05M | $1.65M | -36% | implied cap 10.61% vs 6.75% market (given assumed rents); 25% under comp $/sqft; asking ~36% below assumption value ($1.65M) |

## Absorption

Months of supply = live / (closed per month); closed assumed to span 18 months (no dates in export — set CRE_SOLD_MONTHS).


## Prospecting

- **206** failed listings (expired / cancelled / withdrawn) — motivated owners, with the $/SqFt overpricing that likely stalled the deal.

- **25** overpriced actives to reset or re-trade.


## Underwriting a deal (live model)

The dashboard's **Underwrite a deal** card and the Excel **Scenario** tab build NOI from the assumptions and run a full levered return. Seeded example — a Multifamily deal at $1.80M / 13,402 SqFt ($134/SqFt), assumed rent $18/SqFt, 60% LTV @ 6.75%:

- Derived NOI **$132K** → going-in cap **7.31%**, DSCR **1.47×**, debt yield **12.2%**.

- Year-1 cash-on-cash **6.1%**, 5-yr levered IRR **22.5%**, equity multiple **2.57×** (exit at 5.75% cap).

*Change the rent, cap, LTV, rate or hold and it all recomputes — this single seeded number is just a starting point.*


## Honest limitations

- **No income in the source** — NOI/cap/returns are only as good as your assumptions. The tool makes them explicit and adjustable rather than hiding a guess.

- **Thin closed-sale counts** in some submarkets/types; normalized $/SqFt pools across the market, and low-count cells should be read as indicative.

- **Mixed asset classes and lease vs. sale**; lease listings (different rate bases) are excluded from the $/SqFt sale analysis.

- **Area = MLS area code**, not a named neighborhood; and **units are unknown**, so multifamily is analyzed on $/SqFt, not $/unit.

- These are **screening signals, not appraisals** — verify rent rolls, T-12s and cap-ex before underwriting any specific deal.

