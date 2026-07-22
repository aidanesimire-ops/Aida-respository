# Fort Lauderdale — Normalized Price/SqFt by Neighborhood

*A per-home statistical normalization of the Fort Lauderdale market, built to give you numbers you can quote to homeowners with confidence.*

## The short version

- **4,535 closed sales** (out of **12,469** total listings across sold, expired, withdrawn, cancelled, temp-off, active and pending) were run through a per-home hedonic model that explains **70%** of price variation.
- The model isolates location from everything else, so every neighborhood gets a clean, comparable **normalized $/sqft**. Citywide that standardized home is **$465/sqft**.
- **What moves price, all else equal:** waterfront **+32%**, new construction **+15%**, a private pool **+10%**, and each decade of age **-3%**.
- The market has appreciated **3.3×** since 2012 (quality-adjusted).
- Independent check: these results correlate **r = 0.93** with a completely separate Redfin-based estimate — two methods, same answer.

## How the normalization works

Raw price-per-square-foot lies to you. A neighborhood can look cheap or expensive purely because its homes are bigger, older, newer, on the water, or a different property type. The model strips all of that out:

```
log(sale $/sqft) ~ living area + beds + baths + waterfront + pool
                  + age + new construction + property type + NEIGHBORHOOD
```
The **neighborhood** term is what we want — each area's price contribution holding everything else constant. **Normalized $/sqft** is then the model's price for one standardized home (a dry-lot, no-pool home of citywide-median size ~1,447 sqft and age ~53 yrs) dropped into each neighborhood. Waterfront, pool, age and new-construction are reported **separately** as premiums so you can add them back for a specific home.

## Is the data real? (Yes — spot-checked against public records)

| Address | In your data | Public record | 
|---|---|---|
| 5 Harborage Isle | $70.0M · 20,000 sqft · 2008 | $70M record sale (Sept 2024), 20,000 sqft ✓ |
| 84 Isla Bahia Dr | $34.0M · 11,714 sqft · 2021 | $34M (Apr 2026), 11,714 sqft, built 2021 ✓ |
| 2406 Laguna Dr | $26.0M · 10,646 sqft · 2021 | $26M (Dec 2025), ~10,700 sqft, Harbor Beach ✓ |

Across all files: **100%** of listings have an address, **~98%** have valid square footage and year built. Before modeling, the pipeline recovers **161 missing square-footage** and **44 bad year-built** values from same-building/subdivision peers, and drops the small remainder that can't be recovered.

> **Public-data note:** Census, FEMA flood zones, and the Broward County Property Appraiser (assessed land vs. building value) would add more context, but this session's network policy blocks those hosts. `analysis/enrich_public.py` is included, ready to pull them (geocode → ACS → FEMA → BCPA) in any environment with open network access.

## What drives value

![Price drivers](outputs/chart_premiums.png)

| Driver | Effect on $/sqft |
|---|---|
| Waterfront (vs dry lot) | **+32%** |
| New construction (≤6 yrs, net of age) | **+15%** |
| Private pool | **+10%** |
| Each extra bathroom | **+6%** |
| Each decade of age | **-3%** |
| Implied land value | **~$42/sqft of lot** |

## Price by lot geography

![Geography](outputs/chart_geography.png)

A derived classification (from the waterfront flag + subdivision name + MLS area — indicative, since the export has no true point/corner/canal field) shows the water tiers clearly:

| Geography | Median $/sqft | Waterfront $/sqft | Sales |
|--|--|--|--|
| Finger-isle waterfront | $902 | $902 | 248 |
| Barrier island / beach | $553 | $642 | 826 |
| Intracoastal / canal waterfront | $462 | $462 | 919 |
| Mainland inland | $411 | — | 2,384 |
| Downtown high-rise | $378 | — | 158 |

Finger-isle (point-lot) waterfront runs about **2.2×** mainland-inland per foot — the single biggest geographic swing in the market.

## Neighborhood value ranking

![Top neighborhoods](outputs/chart_mls_ranking.png)

**Most expensive (normalized):**

| # | Neighborhood | Norm. $/sqft | vs City | Waterfront $/sqft | New premium | Sold |
|--|--|--|--|--|--|--|
| 1 | Lauderdale Beach | $924 | +99% | — | — | 12 |
| 2 | Four Seasons | $876 | +88% | $2,032 | +452% | 17 |
| 3 | Coral Isles | $839 | +80% | $1,275 | — | 15 |
| 4 | Halls | $761 | +64% | — | — | 12 |
| 5 | Idlewyld | $750 | +61% | $1,623 | +88% | 16 |
| 6 | Harbor Beach | $745 | +60% | $1,139 | — | 30 |
| 7 | Nurmi Isles | $745 | +60% | $1,071 | +62% | 17 |
| 8 | Colee Hammock | $739 | +59% | — | +28% | 28 |
| 9 | Rio Vista | $706 | +52% | $1,124 | +2% | 91 |
| 10 | Venice | $705 | +52% | $1,123 | +19% | 12 |
| 11 | Lauderdale Harbors | $699 | +50% | $1,094 | — | 26 |
| 12 | Harbour Heights | $698 | +50% | — | — | 14 |

**Most affordable (normalized):**

| Neighborhood | Norm. $/sqft | vs City | Sold |
|--|--|--|--|
| East Point Towers | $159 | -66% | 25 |
| Gallery One | $172 | -63% | 29 |
| Drake Tower | $210 | -55% | 13 |
| River Reach | $214 | -54% | 54 |
| River Shores | $218 | -53% | 15 |
| River Manor | $223 | -52% | 27 |

## Waterfront vs. dry-lot, by neighborhood

The citywide waterfront premium is one number; on the ground it varies enormously. This is the actual median $/sqft of waterfront vs non-waterfront sales *within* each neighborhood:

| Neighborhood | Waterfront $/sqft | Dry-lot $/sqft | Local water premium |
|--|--|--|--|
| Four Seasons | $2,032 | $1,764 | +15% |
| Idlewyld | $1,623 | $733 | +121% |
| Harbor Beach | $1,139 | $732 | +56% |
| Rio Vista | $1,124 | $759 | +48% |
| Lauderdale Harbors | $1,094 | $564 | +94% |
| Coral Ridge | $1,048 | $714 | +47% |
| Coral Ridge Galt | $927 | $628 | +48% |
| Oceanage | $799 | $781 | +2% |
| Coral Shores | $744 | $495 | +50% |
| Las Olas | $708 | $468 | +51% |

## New construction vs. existing

Citywide, brand-new homes (≤6 yrs) command **+15%** per foot over comparable existing homes, net of the age gradient. Where the local sample supports it:

| Neighborhood | New $/sqft | Existing $/sqft | New premium |
|--|--|--|--|
| Four Seasons | $2,004 | $363 | +452% |
| Idlewyld | $1,425 | $756 | +88% |
| Nurmi Isles | $1,599 | $988 | +62% |
| Wilton Manors | $828 | $551 | +50% |
| Coral Ridge | $1,038 | $704 | +48% |
| Coral Ridge Galt | $974 | $664 | +47% |
| Progresso | $593 | $405 | +46% |
| Poinsettia Heights | $703 | $484 | +45% |

## Market shifts since 2020 (Redfin layer)

The MLS export has no dates, so the trajectory comes from Redfin's monthly neighborhood data. Three metrics tell the whole cycle:

![Market shifts since 2020](outputs/chart_timeline.png)

- **Price:** citywide **$283/sqft in 2020 → $482 now (+70%)**, at new highs.
- **Speed:** days-on-market bottomed at **45 days (2022-05)** during the 2022 frenzy, then climbed back above 100.
- **Leverage:** homes sold *at* asking in mid-2022; buyers now negotiate ~6% off again. **Price is at a high while the market is slow — a genuine divergence.**

![Biggest shifts since 2020](outputs/chart_shifts.png)

**Biggest price gains, 2020 → now** (neighborhoods with ≥40 sales):

| Neighborhood | 2020 $/sqft | Now $/sqft | Change | DOM 2020→now |
|--|--|--|--|--|
| Lauderdale Harbours | $435 | $1,096 | +152% | 167→58 |
| Livermore Estates | $230 | $545 | +137% | 136→87 |
| Beach Way Heights | $275 | $645 | +134% | 84→110 |
| Croissant Park River | $238 | $544 | +128% | 25→292 |
| Bal Harbour | $348 | $782 | +125% | 46→55 |
| Coral Ridge Galt | $310 | $687 | +122% | 94→112 |
| Lauder del Mar | $443 | $956 | +116% | 308→101 |
| Harbor Beach | $394 | $850 | +115% | 192→140 |

**Cooled most from their peak:** Bay Colony (-66%), Las Olas Park (-55%), Birch Oceanfront (-52%), Harbor Beach (-47%), Riviera Isles (-45%).

The interactive dashboard lets you pull any neighborhood's price path against the citywide line and toggle price / days-on-market / discount.

## Live opportunities

Every active & pending listing was scored against its predicted value: **925 overpriced**, **459 fair**, **587 underpriced**. The single-family candidates trading furthest below model (verify condition on site — the model can't see renovations):

| Neighborhood | List | SqFt | Ask $/sqft | Model $/sqft | Gap |
|--|--|--|--|--|--|
| Victoria Park | $950,000 | 2,191 | $434 | $688 | -37% |
| Verena Park | $699,000 | 2,273 | $308 | $487 | -37% |
| Osceola Park | $620,000 | 1,986 | $312 | $492 | -37% |
| Dorsey Park Second | $259,900 | 1,272 | $204 | $319 | -36% |
| Progresso | $499,999 | 1,904 | $263 | $409 | -36% |
| Waverly Place | $600,000 | 2,498 | $240 | $369 | -35% |
| Valentines | $699,900 | 2,107 | $332 | $509 | -35% |
| Dorsey Park Th | $445,900 | 1,442 | $309 | $473 | -35% |

## Using this with homeowners

Each neighborhood has an auto-generated profile (see the **Neighborhood Profiles** sheet and the dashboard). Example:

**Rio Vista** — *$706/sqft normalized · 52% above the citywide average*

- A standardized home here normalizes to $706/sqft — 52% above the citywide average (city $465/sqft).
- Recent closed sales run a median $2,300,000 on about 2,790 sqft ($800/sqft actual).
- Geography: predominantly mainland inland.
- Waterfront homes sell around $1,124/sqft vs $759/sqft dry — about +48% for the water here.
- New construction sells around $815/sqft vs $800 for existing here — a +2% new-build premium.
- On a typical 6,779.0 sqft lot the land alone is worth ~$119/sqft (~$808,735).
- Homes typically close about 7% under asking, after roughly 127 days on market.
- Prices here have compounded about 9%/yr over the last decade.
- 48% of listings here fail to sell — pricing right the first time matters more than in most areas.

## Two methods, one answer

![Cross-validation](outputs/chart_crosscheck.png)

The per-home MLS model and the aggregate Redfin index were built from different data with different methods, yet agree at **r = 0.93** across overlapping neighborhoods. That convergence is the strongest evidence the normalization is right.

## Honest limitations & what would sharpen this

- **Lot geography** (point vs corner vs canal vs ocean-access, no-fixed-bridges) is not in the export — only a Waterfront Y/N flag. Adding the MLS *Waterfront Description / Lot Description / Dock* columns would materially improve the waterfront premium.
- **No dates / days-on-market** in the MLS export — those come from Redfin at the neighborhood level. Adding *List Date / Close Date / DOM* columns would let the model time-adjust per home.
- **Vacant land** isn't in the data (all rows are improved residential); land value here is *implied* from lot size. True land comps need a separate land export.
- **Condo-level** flags are coarse — floor, view and renovation aren't observed, so trust the neighborhood aggregates over individual condo call-outs.

---
*Generated by `analysis/` pipeline. Sources: user-provided Fort Lauderdale MLS exports (per-home) + Redfin Data Center (time/DOM). Neighborhood benchmarks and screening signals — not per-home appraisals.*
