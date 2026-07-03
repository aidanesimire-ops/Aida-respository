# The Cove (Deerfield Beach, FL) — Boundary Source Notes

**Boundary name:** The Cove – GIS-Informed Planning Boundary
**Neighborhood:** The Cove · **City:** Deerfield Beach · **County:** Broward · **State:** Florida
**Created:** 2026-07-03
**Boundary type:** Interpretive planning boundary (GIS-informed)
**Official status:** ⚠️ **Unofficial** — no official City/County GIS polygon for "The Cove" was found.

> **Disclaimer.** This is a **planning / discussion** boundary, not a legal or surveyed
> boundary. It is defensible enough to bring to City of Deerfield Beach planning/CRA staff,
> a city manager, or a planning consultant to discuss neighborhood-scale topics
> (redevelopment, walkability, the US-1 edge, waterfront connectivity, the Cove commercial
> node) — but it should be replaced by an official city/county polygon if one is adopted.

---

## 1. Was an official "The Cove" polygon found?

**No.** The Cove is a real, well-known neighborhood, but no public GIS layer publishes it as
a discrete polygon. Specifically:

| Candidate "official polygon" type | Found? | Detail |
|---|---|---|
| Named-place / neighborhood polygon (City GIS) | ❌ No | Not present in the city GIS resources surfaced. |
| Subdivision / plat polygon | ❌ Not confirmed | Not verified in this session (BCPA parcels not reachable — see §4). |
| CRA area | ❌ No | The Cove was not identified as a CRA district. |
| Census-designated place / tract | ❌ No | No CDP named "The Cove"; census tracts do not match the neighborhood. |
| Zoning / land-use district | ❌ No | Zoning is by parcel/district, not by neighborhood name. |
| Civic-association boundary | ⚠️ Exists, not GIS | A **Cove Club Civic Association, Inc.** (FL Sunbiz) and a neighborhood org site exist, but publish **no downloadable GIS boundary**. |

**Conclusion:** the boundary here is **interpretive**, built to the widely-documented
definition of the neighborhood and snapped to real linear features (roads/waterway).

---

## 2. Documented neighborhood definition (corroboration)

Independent, public descriptions consistently define The Cove the same way, which matches the
four-edge assumption used here:

> *"The Cove neighborhood in Deerfield Beach stretches from the Intracoastal Waterway to US-1
> and from Hillsboro Blvd. to the border of Lighthouse Point to the South."*
> — neighborhood real-estate guides (homes.com; By The Sea Realty)

- 1,000+ homes, many waterfront single-family on protected finger canals and the Intracoastal.
- Commercial node: **The Cove Shopping Center**, ~1574–1584 SE 3rd Ct, Deerfield Beach, FL 33441.

---

## 3. Which source was used for each boundary edge

| Edge | Feature followed | Source basis | Certainty |
|---|---|---|---|
| **North** | Hillsboro Boulevard | Road alignment (scaffold aligned to Hillsboro Blvd; snap to OSM/city road centerline via pipeline) | **High** — unambiguous major road |
| **West** | US-1 / Federal Highway | Road alignment (scaffold aligned to US-1; snap to OSM/city centerline) | **High** — unambiguous major road |
| **East** | Intracoastal Waterway / canal waterfront | Waterfront line (scaffold smoothed; true finger-canal edge needs OSM water + BCPA parcel snap) | **Medium-High** — waterfront is real, but the smoothed line does not yet trace individual canals |
| **South** | Transition toward Lighthouse Point | **Interpretive** — best candidates are the Deerfield Beach/Lighthouse Point municipal line or a canal near the SE corner | **Lower / interpretive** — see §6 |

The **south edge is the least certain** and is explicitly interpretive. It should be validated
against the official Deerfield Beach ↔ Lighthouse Point municipal boundary (Broward County
municipal-boundaries layer) and/or a defining canal.

---

## 4. Every public GIS source checked (this session)

| # | Source | URL | Usable geometry obtained here? |
|---|---|---|---|
| 1 | City of Deerfield Beach GIS hub | https://www.deerfield-beach.com/763/GIS | ❌ Blocked (see §5) |
| 2 | City of Deerfield Beach Planning & Zoning ArcGIS web app | https://www.arcgis.com/apps/webappviewer/index.html?id=b21bd16e76fa4a0a857a63091fbd314d | ❌ Blocked; app confirmed to exist |
| 3 | DFB_Zoning ArcGIS layer (last updated Apr 22, 2025) | (ArcGIS Online item) | ❌ Blocked |
| 4 | Broward County GIS / GeoHub (municipal boundaries, parcels, roads, waterways) | https://gis.broward.org/ · Broward Open Data | ❌ Blocked |
| 5 | Broward County Property Appraiser (parcels/subdivisions) | https://bcpa.net/ | ❌ Blocked |
| 6 | OpenStreetMap / Overpass (roads, waterways, canals, coastline) | https://overpass-api.de · https://nominatim.openstreetmap.org | ❌ Blocked |
| 7 | Public neighborhood descriptions (corroboration) | homes.com, By The Sea Realty, etc. | ✅ Text only (no geometry) |

---

## 5. Limitations (important)

- **Network egress was blocked in the session that produced these files.** Every GIS/OSM data
  endpoint above returned **HTTP 403** at the environment's policy proxy (confirmed for
  `gis.broward.org`, `services1.arcgis.com`, `overpass-api.de`, `nominatim.openstreetmap.org`,
  `data.deerfield-beach.com`). Per policy, this was **not** routed around. Therefore **no live
  ArcGIS/OSM geometry was downloaded**, and the edges were **not** programmatically snapped to
  official layers in this session.
- The boundary was instead built from the provided **street-respecting scaffold** plus the
  documented neighborhood definition, then cleaned/validated/simplified with `shapely`.
- The **eastern waterfront is a smoothed line**, not a canal-by-canal trace. The Cove's finger
  canals ("isles") create a jagged real edge that requires OSM water polygons and/or BCPA
  waterfront parcels to capture — done by the pipeline (§7) where network is available.
- To produce a **truly GIS-snapped** boundary, run `build_the_cove_boundary.py` in an
  environment with open network access (your local machine or a session whose egress policy
  permits ArcGIS Online, Broward GIS, and OSM/Overpass).

---

## 6. Assumptions made

1. The Cove = the area bounded by Hillsboro Blvd (N), US-1/Federal Hwy (W), the
   Intracoastal/canal waterfront (E), and the Lighthouse Point transition (S) — per §2.
2. The **north/west edges follow road centerlines** (Hillsboro Blvd, US-1). A future refinement
   could use the road right-of-way edge or the back-of-parcel line instead of the centerline.
3. The **east edge follows the waterfront**; the smoothed line will be replaced by the
   OSM/parcel water edge in the pipeline. Waterfront detail is deliberately preserved
   (not over-simplified) because the water interface is central to the neighborhood's planning
   logic.
4. The **south edge is interpretive.** It approximates the municipal transition toward
   Lighthouse Point; the defensible official feature is the Deerfield Beach/Lighthouse Point
   municipal boundary (and/or a defining canal), which must be confirmed against the Broward
   municipal-boundaries layer.

---

## 7. How the final boundary differs from the scaffold

- Scaffold input: **170** vertices → cleaned/validated → **lightly simplified** (Douglas–Peucker,
  topology-preserving, ~0.9 m tolerance) → **59** vertices in the exported ring.
- The dense **colinear north edge** (45 points at one latitude along Hillsboro Blvd) collapsed to
  a clean straight segment; the **curved SW corner** (US-1 sweep) and the **east/south curves**
  were preserved for smooth rendering.
- Geometry is **valid, simple (no self-intersections), and closed**.
- Approx. area: **813.7 acres ≈ 1.27 sq mi** — consistent with a ~1,000-home waterfront
  neighborhood (sanity check passed).
- When `build_the_cove_boundary.py` is run with network access, the edges will move from the
  scaffold alignment onto the **actual** Hillsboro Blvd / US-1 centerlines, the **actual**
  Intracoastal/canal water edge, and the **actual** municipal/canal south transition.

---

## 8. Recommended next steps for official validation

1. **City of Deerfield Beach Planning & Zoning / GIS staff** — ask whether an adopted neighborhood
   or planning-area boundary for "The Cove" exists internally, and request the layer if so.
2. **Broward County GIS / GeoHub** — pull the municipal-boundaries layer to lock the south edge
   (Deerfield Beach ↔ Lighthouse Point line) and the roads/waterways centerlines.
3. **Broward County Property Appraiser (bcpa.net)** — use waterfront parcels to trace the true
   finger-canal east edge and any subdivision lines along the south.
4. **The Cove / Cove Club Civic Association** — confirm the community's own understood extent.
5. Run `build_the_cove_boundary.py` (open-network environment) to regenerate the snapped
   geometry, then re-review.

---

## 9. Files in this deliverable

| File | Purpose |
|---|---|
| `the_cove_deerfield_beach_gis_boundary.kml` | Google My Maps import — red outline, transparent red fill, commercial-core placemark, edge reference points. |
| `the_cove_deerfield_beach_gis_boundary.geojson` | Valid FeatureCollection (polygon + commercial core + 6 reference points) with full properties. |
| `boundary_reference_points.csv` | Named edge anchor points + commercial core. |
| `generate_boundary_files.py` | Offline generator (no network) that produced the files above from the scaffold. |
| `build_the_cove_boundary.py` | **Live GIS/OSM pipeline** — snaps edges to real ArcGIS/OSM geometry (run where egress is open). |
| `preview_qa.svg` | Schematic shape check (no basemap). |
| `source_notes.md` | This file. |
