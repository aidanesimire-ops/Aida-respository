# How to use your deal dashboard

Plain-English guide: what to open for each job, and how to put it to work in your
marketing. Two main tools — the **dashboard** (`dashboard/index.html`, open in a browser)
and the **workbook** (`outputs/Fort_Lauderdale_PPSF_Normalized.xlsx`, open the **Index** tab).

---

## Pick the job, open the right place

| When you're… | Open this | What you get |
|---|---|---|
| **Talking to a homeowner** about their area | Dashboard → **Marketing** card · Excel → **Marketing Kit** | A copy-ready market snapshot, talking points, and a shareable stat for that neighborhood |
| **Pricing a listing** (CMA) | Dashboard → **Repricing** · Excel → **High-Ticket Underwriting** / **Repriced Inventory** | What comps support vs. current asking, a suggested list, and the CMA line to say it |
| **Prospecting for listings** | Dashboard → **Seller prospects** · Excel → **Seller Prospects** / **Overpriced Actives** · Marketing → **prospect lines** | Owners who tried and couldn't + overpriced actives, each with a ready outreach line |
| **Finding a deal for a buyer** | Dashboard → **Underpriced** · Excel → **Underpriced + Why** | Live listings below comp-supported value, ranked by dollar opportunity, with reasons |
| **Judging if a market is hot or cold** | Dashboard → **Absorption** · Excel → **Absorption** | Months of supply by price band and neighborhood (seller's vs buyer's) |
| **Underwriting luxury (≥$1M)** | Dashboard → **High-ticket bands** · Excel → **Band x Neighborhood** | How each price band behaves *within* each neighborhood — what sold vs what's asked |
| **Running the numbers on a buy** | Dashboard → **Deal scenario** · Excel → **Scenario** tab | Financing + rate/appreciation what-ifs → price, DOM, cash-to-close, returns |
| **Land / lots / docks** | Dashboard → **Land & docks** · Excel → **Land Comps** | Land $/sqft by neighborhood, geography, zoning, dock & commercial-land comps |
| **Small multifamily** | Dashboard → **Multifamily** · Excel → **Multifamily** | $/unit and $/sqft comps by neighborhood and building size |
| **Backing up your pricing claims** | Dashboard KPI **Model accuracy** · Excel → **Model Accuracy** | The out-of-sample accuracy figure — your "data-backed pricing" proof |
| **Understanding any term** | Excel → **Glossary** | Every metric in plain English — read it once |
| **Analyzing a specific property** | Dashboard → **Property Analyzer** · Excel → **Property Analyzer** | Type in neighborhood/size/beds/waterfront → estimated value, should-be $/sqft, rent/yield, replacement cost — with your asking benchmarked against the estimate |
| **Checking how fresh the data is** | Dashboard header **"Data as of…"** · Excel → **Data** tab | The newest export date, every source, and its file/row counts — the vintage behind every number |
| **Running this on a new dataset/market** | [`docs/RECREATE.md`](docs/RECREATE.md) + [`templates/`](templates/) | Drop in new CSVs, run one command, everything rebuilds |

---

## Using it in your marketing

The **Marketing** card (dashboard) and **Marketing Kit** tab (Excel) are built to be pasted,
not just read. For any neighborhood you get:

- **Market snapshot** — a short paragraph for a listing email, a CMA cover note, a farming
  postcard, or a social caption. *Example:* “Rio Vista ranks #9 of 74 Fort Lauderdale
  neighborhoods by normalized value, at about $706/sqft… waterfront trades around
  $1,124/sqft… up ~111% since 2020.”
- **Talking points** — bullet facts to drop into a listing presentation or a call.
- **Shareable stat** — one punchy line (with an emoji) for Instagram / a story / a text.
- **CMA line** — the sentence that frames your price: “Recent comparable sales support about
  $X/sqft… priced to the comps, not to hope.”
- **Buyer opportunities** — specific under-priced listings you can forward to a buyer.

There's also a **citywide Market Pulse** paragraph and **stat cards** for a monthly
market-update email or reel, and a **prospect outreach line** for every failed/overpriced
listing — the exact message to open a listing-appointment conversation.

> Everything is a **data-backed screening signal**, not an appraisal. Confirm specifics
> (condition, exact comps) before you publish a number with someone's address on it.

---

## Tuning it to your read of the market

- **Live, in the browser** — the dashboard's **Live assumptions** panel (verdict cutoff,
  minimum comps, absorption boundaries) recomputes every verdict and market label instantly.
  Use it to be stricter or looser without touching anything.
- **Structural, then rebuild** — thresholds, price bands, and which data you feed live in
  `config/deal_dashboard.yml`. Edit it and run `python analysis/refresh.py`.

## Getting fresh data in

Drop new MLS exports into the folders under `data/raw/`, then:

```bash
python analysis/refresh.py --check   # confirms it read your files & columns
python analysis/refresh.py           # rebuilds the dashboard, workbook, and report
```

Everything is **built to grow with your data.** Each refresh re-reads whatever is on disk
and re-stamps the **"Data as of…"** line (dashboard header, Excel **Data** tab, and Index),
so the vintage always tracks your latest export — add lease exports to `data/raw/lease/` and
the rent/yield numbers switch from sourced benchmarks to real comps automatically.

To sharpen accuracy and unlock more, see **[docs/DATA_TO_ADD.md](docs/DATA_TO_ADD.md)** —
the exact columns to add to your next export and what each one turns on.
