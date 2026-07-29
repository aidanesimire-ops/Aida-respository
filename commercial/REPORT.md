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


**Rents anchored to real lease comps.** From **244** lease listings we derive a median asking rent $/SqFt per asset type — so the assumption isn't a pure guess where we have data:


| Asset type | Assumed rent | Market rent (lease comps) | n |
|---|---|---|---|
| Office | $34 | $17 | 41 |
| Retail | $23 | $28 | 59 |
| Industrial | $12 | $19 | 24 |
| Mixed Use | $16 | $20 | 24 |
| Restaurant | $33 | $23 | 7 |
| Special Purpose | $22 | $7 | 4 |
| Commercial (other) | $22 | $26 | 80 |

*In the dashboard, 'Use market rents' swaps these in with one click.*


**Multifamily $/unit.** Unit counts were parsed from addresses (e.g. "Unit#1-28") for **30 of 90** multifamily comps, enabling a per-door metric where available (units aren't a field in the export).

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

*Scope: 56 of 96 live for-sale listings have a usable building size; the rest (and 115 live lease listings) can't be priced and are excluded.*

Of the **56** priced live listings: **20 underpriced**, 10 fair, **26 overpriced** — on the income lens (asking vs value at assumed rents/cap). Below value = a higher implied cap = a buy. Note these flags **move as you change assumptions**.


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


## Market context — researched benchmarks

External Broward / Fort Lauderdale benchmarks, 2024–2025 (some Q1 2026); curated 2026-07-29 — the market backdrop to talk to, and to sanity-check the assumptions against. Verify before quoting a specific deal.


| Asset class | Market cap | Rent | Sale $/SF | Vacancy |
|---|---|---|---|---|
| Multifamily | 4.7–5.4% (A ~4.74% · B ~4.92% · C ~5.38%); ~5.6% blended, Yardi ~6.3% | priced per unit; ~$359,437/unit avg (2025 YTD) | ~$300–450/SF on value-add product; per-unit is the metric | ~7.9% (buildings 50+ units, Q3 2025) |
| Office | ~6.75–8.0% | $41.60/SF full-service overall (record high); Class A $46.74/SF; medical ~$34–36/SF | closed $196–442/SF (Plantation Place ~$196; Las Olas Centre trophy $442) | ~12.3% (Broward, Q4 2025) |
| Retail | ~6.0–6.1% | $27.59/SF NNN Broward; Fort Lauderdale ~$36/SF; prime Las Olas/Downtown $50–75/SF | closed ~$391/SF (RK Centers, Riverbend, Dec 2025); listings avg ~$630/SF | ~3.8–3.9% (very tight) |
| Industrial | ~6.0–6.3% (South FL) | ~$16/SF NNN (Fort Lauderdale ~$16.22); small-bay/flex $18–30/SF NNN | ~$150–300/SF (well-located Broward warehouse) | ~4.0–5.5% (rising on new supply) |
| Hotel | ~7.8% | ADR $129 (summer trough) to ~$240 peak; per key ~$273,831 | priced per key (~$274K/key), not per SF | occupancy ~55% (summer) to 72–85% (peak/annual, destination-wide) |
| Mixed Use | ~6.0–6.75% (blends retail/MF) | ground-floor retail $27–75/SF NNN + residential above | varies with the residential/retail split | tracks its retail (sub-4%) and MF (~8%) components |

**Costs & Florida realities (headline):**

- Construction (hard): MF garden $170–200/SF, mid-rise $200–275/SF, industrial $156–234/SF; +10–15% of construction cost HVHZ premium; soft costs 15–30% of hard costs.

- Value-add rehab: MF light $15,000–25,000/unit, heavy $45,000–65,000+/unit; office TI ~$122/SF (Class A $135–150 · Class B $90–120).

- Land: commercial ~$944/SF (avg parcel ~6,700 SF); ~$4.04M/acre; per-buildable-unit ~$38,000/unit (2125 S Andrews 'The Era', 400 units, 2024) to ~$420,000/unit (900 Intracoastal 'Sage', 44 units, 2024).

- Waterfront: direct/unobstructed water access sells ~30–50% above comparable dry-lot; priced per linear foot of frontage, adjusted for depth, bridge clearance, seawall/dock; seawall ~$500–1,000/linear foot.

- Insurance: ~$1,430/unit/yr (+53% YoY, 2024) — insurance ~7% of opex but ~17% of expense growth since 2019 → compresses NOI, expands caps; FL values −6.8%.

- Incentives: by-right MF on commercial/industrial if ≥40% units ≤120% AMI; density = highest in jurisdiction, height = highest within 1 mi; 75–100% property-tax exemption on affordable units; Broward 30 tracts / Fort Lauderdale 10 — prime: Flagler Village, 13th St/Progresso, Sistrunk.


### Neighborhood playbook (talking points by area)

- **Area 3600 → 17th Street Causeway / Harbor Beach / SE** (High): The marine & yachting-services heart of the market — and increasingly a waterfront redevelopment target. *Recent:* The Quay (1515 SE 17th) — Related/BH/PEBB bought the ~7-acre waterfront marina/retail site for $48.5M (2024) and won approval for a 521-unit tower (40% workforce, Live Local). F3 Marina automated drystack completed. **Play:** Waterfront/marina redevelopment; dockage value; Live Local density on the water.
- **Area 3810 → Sistrunk / Progresso / Northwest** (Med): A CRA-driven, largely opportunity-zone corridor where public subsidy is catalyzing affordable/workforce and mixed-use redevelopment. *Recent:* The Aldridge & The Laramore — ~$42M, 72-unit mixed-use with retail at 1204 Sistrunk. NPF-CRA plan runs to 2035 with construction/façade incentives. **Play:** Low basis vs downtown; land assembly on the OZ + CRA-incentive angle; Flagler Village spillover.
- **Area 3380 → Wilton Manors** (High): A walkable, affluent arts-and-entertainment node (Wilton Drive) drawing its first mid-rise projects. *Recent:* Stiles bought the Shoppes of Wilton Manors (78,600 SF) for $27.6M (Dec 2024), pursuing an 82-unit rezoning; Kaplan's Generation proposes ~190 units. **Play:** Retail redevelopment; constrained supply; strong restaurant/retail demand.
- **Area 3370 → Oakland Park** (High): One of Broward's fastest-emerging urban-infill submarkets, led by public placemaking. *Recent:* Culinary Arts District (NE 12th Ave) restaurant/distillery corridor; new City Hall mixed-use (2025); 6-acre Horizon redevelopment of the old City Hall site. **Play:** Infill mixed-use, older-industrial repositioning; CRA incentives; attractive basis.
- **Area 3500 → Downtown / Flagler Village** (High): The region's most active development submarket — a former warehouse district now dense with high-rise multifamily, creative office and ground-floor retail. *Recent:* FAT Village — Hines/Urban Street ~$500M, ~600 units + the region's first mass-timber office, topping off 2025, delivery mid-2026. Gallery at Flagler Village (263 units) queued. Class A office asking low-$40s/SF. **Play:** Development & land assembly; Live Local density bonuses; office repositioning.
- **Area 3800 → Downtown / Flagler Village** (High): The region's most active development submarket — a former warehouse district now dense with high-rise multifamily, creative office and ground-floor retail. *Recent:* FAT Village — Hines/Urban Street ~$500M, ~600 units + the region's first mass-timber office, topping off 2025, delivery mid-2026. Gallery at Flagler Village (263 units) queued. Class A office asking low-$40s/SF. **Play:** Development & land assembly; Live Local density bonuses; office repositioning.
- **Area 3470 → Las Olas** (High): Broward's premier office / CBD address — law, finance and wealth-management tenancy. *Recent:* 2025 delivered the two largest office trades in a decade: Las Olas Centre I & II $208M (~$442/SF, Bradford Allen) and Bank of America Plaza at 401 E Las Olas ~$220M (Lone Star/Highline/Square2). **Play:** Trophy office, repositioning, ground-floor retail at $50–75/SF.
- **Area 3460 → Sistrunk / Progresso / Northwest** (Med): A CRA-driven, largely opportunity-zone corridor where public subsidy is catalyzing affordable/workforce and mixed-use redevelopment. *Recent:* The Aldridge & The Laramore — ~$42M, 72-unit mixed-use with retail at 1204 Sistrunk. NPF-CRA plan runs to 2035 with construction/façade incentives. **Play:** Low basis vs downtown; land assembly on the OZ + CRA-incentive angle; Flagler Village spillover.
- **Area 3160 → Fort Lauderdale Beach** (Med): The barrier-island beach market — hospitality, beachfront retail and boutique commercial/condo, where waterfront and ocean views drive a clear premium. *Recent:* Hotel product trades ~$274K/key with a beachfront ADR premium; retail/mixed commercial along the A1A / Ocean Blvd corridor. **Play:** Hospitality & beachfront retail; premium land; tourism demand.

*Sources: CBRE (Calum Weaver), Colliers, JLL, Matthews, Cushman & Wakefield, Yardi, The Real Deal, Florida YIMBY, RSMeans/Turner/RLB, LandSearch, Holland & Knight, and others — full list on the dashboard's Market context card and the Excel **Market** tab.*


## Honest limitations

- **No income in the source** — NOI/cap/returns are only as good as your assumptions. The tool makes them explicit and adjustable rather than hiding a guess.

- **Thin closed-sale counts** in some submarkets/types; normalized $/SqFt pools across the market, and low-count cells should be read as indicative.

- **Mixed asset classes and lease vs. sale**; lease listings (different rate bases) are excluded from the $/SqFt sale analysis.

- **Area = MLS area code**, not a named neighborhood; and **units are unknown**, so multifamily is analyzed on $/SqFt, not $/unit.

- These are **screening signals, not appraisals** — verify rent rolls, T-12s and cap-ex before underwriting any specific deal.

