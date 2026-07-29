# Market realities — costs, waterfront & the ultra-luxury market

The numbers to *know and speak to* when you're selling ultra-luxury Fort Lauderdale, with
sources. These feed the dashboard's **Costs & realities** card, the Excel **Costs &
Realities** tab, and the build-vs-buy math. They're **external market estimates** — ranges,
not appraisals — and they're editable in [`config/deal_dashboard.yml`](../config/deal_dashboard.yml)
under `costs:`. Update them as the market moves and re-run `python analysis/refresh.py`.

## New construction (hard cost, $/sqft)

| Tier | $/sqft |
|---|---|
| Luxury custom | ~$600 |
| High-end custom | ~$900 |
| Ultra-premium waterfront | ~$1,500–$2,000+ |

Full-custom South Florida generally runs **$500–$1,000/sqft**, with ultra-premium waterfront
above **$1,500–$2,000**. Add **~25% soft costs** (design, permits, GC fee, financing) on top
of hard cost. Waterfront lots cost more to build on — elevated foundations, HVHZ hurricane
code, impact glass, and labor demand. Typical custom timeline runs ~18–30 months.

## Renovation (high-end gut, $/sqft)

High-end gut renovation runs **~$150–$300+/sqft**; ultra-luxury finishes (imported stone,
custom cabinetry, smart systems) push **$300–$400+**. Miami-area midpoint ≈ $175/sqft for a
full remodel.

## Waterfront — how it's actually priced

Waterfront is **priced per linear foot of water frontage**, built from sold comparables on
the **same waterbody** over the last 12–24 months — *not* off interior square footage. The
value drivers, in order:

- **Ocean access** — *no fixed bridges* (unlimited vertical clearance for large/sport-fish
  and megayachts) is the single biggest premium.
- **Water depth** and **dockage** (linear feet of dock, draft).
- **Exposure / point lots / wide-water** views.

Supporting infrastructure and its cost:

| Item | Cost |
|---|---|
| Seawall replacement | **$300–$900 / linear foot** (Fort Lauderdale high end; +$2–5k engineering, +$0.8–3k permits) |
| New residential dock | **$35k–$75k** ( ~$43–$85/sqft) |
| Boat lift | **~$1 / lb** (a 24,000-lb lift ≈ $38k) |
| Deep-water pilings | $300–$450 each (8+ ft) |

Fort Lauderdale enforces strict seawall **elevation (NAVD88)** standards — a factor on any
older waterfront property.

## Carrying cost — insurance (luxury waterfront, per year)

| Exposure | Annual premium |
|---|---|
| Canal-front | $8k–$20k |
| Intracoastal | $12k–$30k |
| Direct oceanfront (luxury) | $18k–$50k+ (>$60k on $5M+ estates) |

On a ~$3M canal home, wind + flood together commonly add **$15k–$25k+/yr** to carry; flood
alone in an AE zone runs $4k–$12k depending on elevation and mitigation. Large glass spans and
waterfront infrastructure raise rebuild value, which raises premiums.

## The ultra-luxury market (2025)

- **Depth:** 361 South Florida homes sold above **$10M** in 2025 — the 2nd-highest year ever
  (2021 = 444). Broward logged its first **$70M** sale; the market now transacts **$20M–$50M+**.
- **Price:** modern luxury homes command **~$1,500+/sqft** at **$8M+**.
- **Demand:** driven by wealth migration, tax policy, and **cash / international** buyers.
- **Context:** Fort Lauderdale broadly ran a **buyer's market** in 2025 (~9.8 months of
  inventory) — but finished waterfront trophy product stays scarce and moves on that scarcity.

## Build-vs-buy (replacement cost)

For each house-dominant neighborhood the dashboard computes **all-in replacement cost** =
construction ($/sqft × home size × 1 + soft %) **+ land** (land $/sqft × lot size), and
compares it to finished-product resale (new-construction $/sqft where available). The read:

- **Resale above replacement** → new construction pencils; spec-builder territory.
- **Resale below replacement** → often cheaper to buy finished than to build (most FLL
  neighborhoods, at current construction costs).

Use it to frame a listing ("you're buying ~X% below what it costs to reproduce") or a
land/teardown play.

## Sources

- Sabal Luxury Builder — [Miami luxury cost/sqft (2026)](https://sabalbuilder.com/en/journal/luxury-home-construction-cost-per-square-foot-miami)
- Tri-Town Construction — [Fort Lauderdale build & renovation costs (2025)](https://www.tri-townconstruction.com/blog/cost-to-build-home-fort-lauderdale-2025/)
- Seanote Construction — [Cost to build a house in Florida (2026)](https://seanotefl.com/cost-to-build-a-house-in-florida/)
- Ginger Luxe Real Estate — [Fort Lauderdale waterfront pricing guide](https://gingerluxereal.com/blog/pricing-waterfront-homes-in-fort-lauderdale)
- Sea Me Dive — [South Florida seawall cost (2025)](https://seamedive.net/how-much-does-a-seawall-cost-in-south-florida/)
- Crocker Marine — [dock construction cost guide (2025)](https://crockermarine.com/blog/complete-dock-construction-cost-guide-for-southwest-florida/)
- Josh Dotoli Group — [Fort Lauderdale waterfront insurance costs](https://joshdotoligroup.com/blog/insurance-costs-for-waterfront-homes-in-fort-lauderdale/)
- MillionLuxury — [South Florida luxury market report (2025)](https://www.millionluxury.com/news/south-florida-luxury-real-estate-market-september-2025-report)
- The Real Deal — [Fort Lauderdale luxury market (2025–26)](https://therealdeal.com/miami/2026/05/13/fort-lauderdales-luxury-market-regains-momentum/)

*Figures are estimates gathered from public sources for context and conversation — verify
against current bids and same-waterbody comps before relying on them in a transaction.*
