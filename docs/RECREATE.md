# Recreate this analysis for other properties / a new market

Two ways to reuse everything you see here. Pick the one that fits.

---

## A. Analyze a single property right now (no setup)

Open the workbook → **Property Analyzer** tab. Pick a neighborhood from the dropdown,
type the size, beds, and Waterfront Y/N (and an asking price if you have one). It instantly
estimates value, the should-be $/sqft, rent & gross yield, and replacement cost. Use it for
every property you're evaluating — nothing to install.

---

## B. Rebuild the whole book on a NEW set of properties or a new market

The whole system is data-driven: drop in fresh exports, run one command, and every tab,
report and dashboard rebuilds. Four steps.

### 1. Get your data into CSVs
Export from your MLS (or fill the template at
[`templates/property_data_template.csv`](../templates/property_data_template.csv)). For the
main residential analysis you need these columns (names can differ — you map them in step 3):

`Area, Address, Subdivision/Complex, List Price, Sale Price, #Beds, #FBaths, #HBaths,
SqFt LA, Type of Property, Year Built, #Garage Spaces, Pool YN, Waterfront Property (Y/N),
Lot SqFt`

Export one file per status and name them by status:

```
data/raw/mls/sold.csv               (closed sales — the comps; needs Sale Price)
data/raw/mls/active_pending.csv     (live / under-contract inventory)
data/raw/mls/active_coming_soon.csv
data/raw/mls/expired.csv
data/raw/mls/withdrawn.csv
data/raw/mls/cancelled.csv
data/raw/mls/temp_off.csv
```

Other asset classes are optional and go in their own folders (same idea):
`data/raw/land/`, `data/raw/commercial_land/`, `data/raw/income/`, `data/raw/lease/`.

### 2. Name your market
Open [`config/deal_dashboard.yml`](../config/deal_dashboard.yml) and set:

```yaml
market:
  name: Your City Here
```

### 3. (Only if your columns are named differently) map them
In the same config file, under `assets.residential.columns`, put YOUR column name on the
right of each field. Example if your export calls square footage "LivingArea":

```yaml
    columns:
      sqft: LivingArea
```

Leave any line you don't need to change — it falls back to the default.

### 4. Rebuild everything
```bash
python analysis/refresh.py --check   # confirms it found your files & columns (fix any ⚠ it lists)
python analysis/refresh.py           # rebuilds the workbook, dashboard, report and data
node analysis/render_pdf.cjs         # renders the per-neighborhood PDF reports
```

Then open `outputs/Fort_Lauderdale_PPSF_Normalized.xlsx` (it keeps the filename; the contents
are your new market) and `dashboard/index.html`.

---

### Tips
- **Thresholds and brackets** (price bands, comp minimums, sqft bands, cost & rent
  benchmarks) all live in `config/deal_dashboard.yml`. Edit and re-run `refresh.py`.
- **Not sure a column mapped?** `python analysis/refresh.py --check` prints, per asset, the
  files it found, the row counts, the status breakdown, and any column it couldn't find.
- **Smaller dataset?** Lower `min_report_sold` / `min_nbhd_sold` in the config so thinner
  neighborhoods still appear.
- Everything is also packaged as the **deal-dashboard skill**, so you can spin this up on a
  brand-new market from scratch and it will guide the setup.
