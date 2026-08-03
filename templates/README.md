# Input template

`property_data_template.csv` shows the exact columns the residential analysis expects, with
three example rows. To analyze your own set of properties:

1. Replace the example rows with your data (keep the header row).
2. Save one file per status into `data/raw/mls/` — e.g. your closed sales as
   `data/raw/mls/sold.csv`, live listings as `data/raw/mls/active_pending.csv`.
   (Closed sales need the **Sale Price** column filled; live listings can leave it blank.)
3. Run `python analysis/refresh.py`.

Column notes:
- **Type of Property**: Single Family, Condo, or Townhouse.
- **Pool YN / Waterfront Property (Y/N)**: `Yes` or `No`.
- **SqFt LA** = living area square footage; **Lot SqFt** = lot size (0 for condos is fine).
- **Subdivision/Complex** becomes the neighborhood — keep it consistent.

If your export uses different column names, don't rename them by hand — map them once in
`config/deal_dashboard.yml` under `assets.residential.columns`. Full walkthrough in
[`../docs/RECREATE.md`](../docs/RECREATE.md).
