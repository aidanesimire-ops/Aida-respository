# Waterfront Property List Engine

Off-market ownership call sheets for waterfront acquisition targeting, built from public
records. Point it at a county's parcel GIS service, get two styled workbooks:

| Workbook | What's in it |
|---|---|
| `Waterfront_Ownership_Lists_<market>.xlsx` | Every parcel **with measured water frontage**, one tab per asset class, plus a Summary and QA tabs |
| `Beach_Condo_Owners_<market>.xlsx` | Barrier-island condos at the **unit level**, plus a By-Building index for prioritizing towers |

Every row carries folio, situs address, owner(s), mailing address, absentee flag,
entity/LLC flag and type, use code and description, value, building sqft, waterfront type
and water body — and, after the enrichment pass, the entity's managers and registered agent.

**Off-market by design.** Every row comes from public ownership records (property appraiser +
state business filings). No MLS or listing feed is used anywhere in the pipeline, so no owner
is included or excluded based on whether their property is listed.

---

## Quick start

```bash
pip install -r requirements.txt

# 1. See the output shape immediately — synthetic data, no network
python -m waterfront_engine.cli demo --out-dir demo_output

# 2. Confirm the field map against the live layer (do this first on any market)
python -m waterfront_engine.cli verify-fields --market configs/fort_lauderdale.py

# 3. Run it
python -m waterfront_engine.cli run --market configs/fort_lauderdale.py
```

`run` executes six stages in order — `fetch, classify, waterfront, flags, enrich, workbooks`.
Each writes a GeoPackage to `data/`, so you can rerun any stage alone:

```bash
# re-cut the classes without re-downloading 195k parcels
python -m waterfront_engine.cli run --stages classify,waterfront,flags,workbooks

# build the workbooks now, do the slow entity pass later
python -m waterfront_engine.cli run --no-sunbiz
```

Entity resolution is the slow stage (one polite Sunbiz hit per distinct entity owner, cached
to `data/sunbiz_cache.json` so a rerun is free). At volume, skip the scraping entirely and
match against the free bulk corporate data file instead:

```bash
python -m waterfront_engine.cli run --bulk-entities data/sunbiz_entities.csv
```

…where that CSV has an `entity_name` column plus whichever of `managers`, `registered_agent`,
`status`, `document_number` you have.

---

## Asset classes

Standard Florida DOR land-use codes, shared by all 67 FL counties:

| Group | Class | DOR codes |
|---|---|---|
| Residential | Single-Family | `01` |
| Residential | Multi-Family | `03`, `08` |
| Land | Vacant Land | `00`, `10`, `40` |
| Office | Office | `17`, `18`, `19` *(medical stripped out)* |
| Commercial | Commercial | `11`–`16`, `21`–`38` |
| Hospitality | Hospitality | `39` |
| Specialty | Marina | `20` |
| Specialty | Medical | `73`, `74` + medical-keyword offices pulled out of `17`/`18`/`19` |

Medical and Office are mutually exclusive by construction: a `19` parcel whose description
matches the medical keyword pattern lands on the Medical tab and is removed from Office. The
`QA — Multi-Class Folios` tab lists any folio that still ended up on two tabs.

---

## How "waterfront" is decided

1. Hydrography is projected to the market's foot-based CRS and buffered by `water_buffer_ft`.
2. A parcel qualifies when at least `min_frontage_ft` of its **boundary** falls inside that
   buffer — length along the water, not mere intersection.
3. The water body contributing the most frontage is what gets written to `Water Body` /
   `Waterfront Type`.

**Keep `min_frontage_ft` above `2 × water_buffer_ft`.** A parcel that touches water at a single
corner picks up roughly one buffer width along each of its two edges, so a threshold below that
lets corner clips onto your call sheet. The engine logs a warning if the config violates this.
Fort Lauderdale ships at 15 ft buffer / 40 ft minimum frontage — above the corner-clip ceiling
of 30 ft, and below the width of the narrowest genuine canal lot.

`Frontage (ft)` is that measured length, so it reads long by up to about two buffer widths
(the buffer wraps the lot corners). It's a sorting number, not a survey.

---

## Porting to a new market

Everything market-specific lives in one config file. Copy `configs/_template.py`, then:

1. **Find the parcel REST service** — search `"<county> ArcGIS REST parcels"` or the county
   property appraiser's GIS. Set `parcel_service` / `parcel_layer`.
2. **Fix the field map** — run `verify-fields`. It reports every configured `f_*` name that
   doesn't exist on the layer and suggests candidates from the real schema. This is the single
   most common cause of a run that "works" but produces empty owner columns.
3. **Use codes** — any Florida market copies `ASSET_CLASSES` from `configs/fort_lauderdale.py`
   verbatim. Out of state, rebuild the code lists from that assessor's scheme; the class
   structure stays the same. If the county stores 4-digit detail codes (`0100`), set
   `"code_match": "prefix"`.
4. **Water** — point `water_layer` at the county hydrography layer, or set `water_path` to a
   local file (NHD works where the county has nothing). Set `proj_crs` to the local State
   Plane / UTM zone **in feet** so the thresholds mean what they say.
5. **Entity resolution** — Florida is built in. Elsewhere, export the state's business filings
   and use `--bulk-entities`, or write a class with a `lookup(name) -> dict` method and pass it
   to `pipeline.enrich_stage`.
6. **Condos** — confirm the local condominium use code, that situs addresses carry unit
   numbers, and set `beach_lon_threshold` (or `boundary_path` to a drawn barrier-island
   polygon, which is more precise).

One config file per market, one shared script set. New market = new config, same run.

---

## QA before dialing

The pipeline does the mechanical checks itself and writes them into the output:

- `run_report_<market>.json` — parcels classified vs. waterfront vs. enriched, per class.
- `QA — Use Code Census` tab — every use code with counts and a sample description. This is
  where you catch a code that should have moved buckets (marina `20`, medical in `19`,
  hotels `39`).
- `QA — Multi-Class Folios` tab — appears only if a folio landed on two tabs.
- Log warnings for: unmapped fields, a frontage threshold that admits corner clips, condo rows
  whose situs address carries no unit number, non-polygon parcel geometry.

Still on you, because no script can do it:

- Eyeball 8–10 waterfront hits and 8–10 beach condos on satellite; tune `water_buffer_ft`,
  `min_frontage_ft`, and `beach_lon_threshold`.
- Spot-check 5 Sunbiz matches against the real detail pages. The HTML parser targets Sunbiz's
  `div.detailSection` layout and degrades quietly if the markup drifts.

## Compliance

Public ownership data is fine for research and mail. Live telemarketing is a separate regime:
scrub against the National DNC Registry and any state list, and mind state rules (in Florida,
the 2021 mini-TCPA call-window and consent requirements). Run the program by your counsel.
Not legal advice. Every workbook carries a `Read Me` tab restating provenance and this note.

---

## Layout

```
waterfront_engine/
  config.py     market config objects + validation
  arcgis.py     paged REST client, WHERE building (numeric vs string use codes)
  classify.py   use-code + keyword split into asset classes
  spatial.py    frontage measurement, beach filter
  flags.py      entity type + absentee flags
  sunbiz.py     live Sunbiz lookup, disk cache, bulk-file matcher
  condos.py     unit/building parsing, by-building index
  columns.py    output column layout
  excel.py      styled workbook writer
  pipeline.py   stage orchestration
  demo.py       synthetic fixture + offline run
  cli.py        command line
configs/        one file per market
tests/          63 tests, all offline
```

Run the tests with `python -m pytest tests -q`.

### Data sources (Fort Lauderdale)

- Parcels: City of Fort Lauderdale GIS, `GeneralPurpose/gisdata` MapServer layer 94
  (BCPA-sourced owner/value/sqft, clipped to city limits).
- Water: same service, layer 104.
- Owner cross-check: Broward County Property Appraiser (`bcpa.net`).
- Entities: Florida Division of Corporations — `search.sunbiz.org`, or the free bulk corporate
  data file from `dos.fl.gov/sunbiz/other-services/data-downloads/corporate-data-file/`.
