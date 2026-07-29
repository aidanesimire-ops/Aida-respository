# Data to add — the exact columns that level this up

Your model is already sharp, but a few extra fields — most of them just **checkboxes on the
same MLS export you already pull** — unlock the biggest gains. Ranked by impact. After you
add columns, map them in `config/deal_dashboard.yml` (the `columns:` block for that asset)
and run `python analysis/refresh.py`.

---

## 1. Dates & price history  ⭐ biggest single win

Add these to the **residential MLS export** (they're standard fields, almost certainly
available in your export tool):

| Add this column | Unlocks |
|---|---|
| **List Date** / **Close Date** | True days-on-market per home; real absorption; seasonality; appreciation straight from the MLS |
| **DOM / CDOM** (days on market) | Listing-level time-on-market instead of a neighborhood proxy |
| **Original List Price** | Total price cut from first ask to sale |
| **Price change count / last change date** | **Motivated-seller signal** — "3rd cut in 60 days" is the best prospecting flag there is |

Also tightens the model: with dates we time-adjust comps to today, which should pull the
accuracy figure (currently ±16% median) meaningfully tighter.

## 2. Waterfront specifics  ⭐ luxury value driver

Waterfront is your #1 price driver and today it's just yes/no. Add the MLS
**Waterfront Description / Dock** fields:

- **Ocean access** (fixed-bridge vs. no-fixed-bridge) — huge for boat owners
- **Water frontage** (linear feet), **dock/slip length & depth**
- **Seawall year / condition**
- **Water type** (ocean / Intracoastal / canal / point lot)

## 3. Rent roll for multifamily  ⭐ turns screening into underwriting

The income export has no income. Add **actual/pro-forma rents, operating expenses, and unit
mix** and the Multifamily view gains **cap rate, GRM, DSCR, and price-per-door vs. income** —
real underwriting instead of price comps.

## 4. Condition & renovation

The single biggest unobserved variable in the price model. Even a coarse field helps:

- **Condition (1–5)** or **Renovated (Y/N + year)**
- **Interior features / updates** the MLS already tags

## 5. Condo health  (post-Surfside, this moves value)

- **HOA / maintenance fee**, **special assessments**, **reserve funding**
- **40-year / milestone recert status (SB-4-D)**

## 6. Public enrichment (no MLS needed — run `analysis/enrich_public.py`)

Ready to go; it geocodes every address and appends, given open internet access:

- **FEMA flood zone + base flood elevation** — coastal FLL, moves value and insurance cost
- **Broward County (BCPA) assessed value, tax, prior sale date/price** — a second valuation
  anchor, tax burden, and the true owner basis (spot long-hold = motivated owners)

## 7. Geocoding → map view

Latitude/longitude (or run the geocoder) enables distance-to-water/beach, spatial comps, and
a heat map on the dashboard.

---

### Priority order

1. **Re-pull the MLS export with dates / DOM / price-history + waterfront-description columns**
   — cheapest, highest impact, mostly checkboxes.
2. **Rent roll on multifamily.**
3. **Run `enrich_public.py`** on a machine with normal internet for flood + assessed value.

Once the columns exist, mapping them is a config edit — no code — and `refresh.py` rebuilds
everything against them.
