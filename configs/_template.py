"""Template market config — copy to configs/<market>.py and fill in.

Porting checklist (Part II of the playbook):

1. Find the parcel REST service. Search "<county or city> ArcGIS REST parcels"
   or the county property appraiser's GIS / state open-data hub. Confirm it
   exposes owner name, mailing address, use code and value.
2. Run `verify-fields` and paste the real attribute names into the f_* map:
       python -m waterfront_engine.cli verify-fields --market configs/<market>.py
3. Use codes. Every Florida county uses the same DOR codes, so an FL market can
   copy ASSET_CLASSES from configs/fort_lauderdale.py verbatim. Out of state,
   rebuild the code lists from that assessor's scheme — the class structure
   (SF, MF, land, office, commercial, hospitality, marina, medical) stays.
4. Water: point water_layer at the county hydrography layer, or set water_path
   to a local file (NHD flowlines/waterbodies work when the county has none).
   Set proj_crs to the local State Plane / UTM zone in FEET so the buffer and
   frontage thresholds mean what they say.
5. Entity resolution: FL = Sunbiz (built in). Elsewhere, export that state's
   business filings to CSV and pass --bulk-entities, or write a resolver class
   with a `lookup(name) -> dict` method.
6. Condos: confirm the local condominium use code and that situs addresses
   carry unit numbers, then set beach_lon_threshold (or a barrier-island
   polygon) for the new coastline.
"""

MARKET = {
    "name": "CHANGE ME, ST",
    "parcel_service": "https://<host>/arcgis/rest/services/<folder>/<service>/MapServer",
    "parcel_layer": 0,
    "water_layer": None,  # or an int; set water_path instead for a local file
    # "water_path": "data/nhd_waterbodies.geojson",
    "proj_crs": 2236,  # local State Plane / UTM in FEET
    "beach_lon_threshold": None,  # e.g. -80.11; None disables the beach filter
    "beach_side": "east",
    "water_buffer_ft": 30.0,
    "min_frontage_ft": 15.0,
    "water_name_field": "NAME",
    "water_type_field": "TYPE",
    # -- field map: run verify-fields and fill these in ---------------------
    "f_folio": "FOLIO",
    "f_owner1": "OWNER1",
    "f_owner2": "OWNER2",
    "f_owners": "OWNERS",
    "f_mail": "MAILADDR",
    "f_mailcity": "MAILCITY",
    "f_situs": "SITEADDR",
    "f_use": "USECD",
    "f_usedesc": "USEDSCRP",
    "f_usedetail": None,
    "f_value": "JUSTVALUE",
    "f_sqft": None,
    "f_bldgs": None,
    "home_city": "CHANGE ME",
    "home_city_aliases": (),
    "code_match": "exact",  # "prefix" if the county stores 4-digit detail codes
}

# Copy from configs/fort_lauderdale.py for any Florida market; rebuild the code
# lists from the local assessor's scheme out of state.
ASSET_CLASSES: dict[str, dict] = {}

CONDO_DELIVERABLE = {
    "label": "Beach Condo Owners",
    "codes": ["04"],
    "beach_only": True,
}
