"""Fort Lauderdale, FL — the reference market.

Parcels: City of Fort Lauderdale GIS, GeneralPurpose/gisdata layer 94 (BCPA-sourced
owner / value / sqft attributes, already clipped to city limits).
Water:   same service, layer 104 (canals, ICW/estuary, lakes).

The f_* names below are the layer's own attribute names. Verify them before the
first run — they are the single most common reason a port produces empty columns:

    python -m waterfront_engine.cli verify-fields --market configs/fort_lauderdale.py
"""

MARKET = {
    "name": "Fort Lauderdale, FL",
    "parcel_service": "https://gis.fortlauderdale.gov/arcgis/rest/services/GeneralPurpose/gisdata/MapServer",
    "parcel_layer": 94,
    "water_layer": 104,
    "proj_crs": 2236,  # NAD83 / Florida East (US survey feet) — buffers are in feet
    # Barrier island ("the beach") = parcels east of this longitude. Quick
    # approximation; swap in a drawn polygon via CONDO_DELIVERABLE['boundary_path']
    # once you have one.
    "beach_lon_threshold": -80.11,
    "beach_side": "east",
    # Waterfront test: buffer mapped water, then require this much parcel boundary
    # inside the buffer. Keep min_frontage_ft > 2 x water_buffer_ft — a parcel that
    # only clips water at one corner picks up about one buffer width on each of its
    # two edges, so a threshold below that lets corner clips through. Keep it under
    # the narrowest genuine waterfront lot width in the market (canal lots here run
    # 50 ft and up).
    "water_buffer_ft": 15.0,
    "min_frontage_ft": 40.0,
    "water_name_field": "NAME",
    "water_type_field": "TYPE",
    # Uncomment once you have eyeballed the water layer, to drop drainage ditches:
    # "water_type_exclude": r"Ditch|Retention|Swale",
    # -- field map (layer 94) ------------------------------------------------
    "f_folio": "FOLIO",  # VERIFY: confirm the folio/parcel-id attribute name
    "f_owner1": "OWNERNME1",
    "f_owner2": "OWNERNME2",
    "f_owners": "OWNERS",
    "f_mail": "PSTLADDRESS",
    "f_mailcity": "PSTLCITY",
    "f_situs": "SITEADDRESS",
    "f_use": "USECD",
    "f_usedesc": "USEDSCRP",
    "f_usedetail": "DORUSEDETAILS",
    "f_value": "CNTASSDVAL",
    "f_sqft": "CNTYGISSQFT",
    "f_bldgs": "BLDGNUMOF",
    "home_city": "FORT LAUDERDALE",
    "home_city_aliases": ("FT LAUDERDALE", "FT. LAUDERDALE", "FTLAUDERDALE"),
    "code_match": "exact",
}

# Standard Florida DOR land-use codes — shared by all 67 FL counties, so any
# Florida market runs with this block unchanged. Out of state, rebuild the code
# lists from that assessor's scheme; the class structure stays the same.
MEDICAL_KW = (
    r"(?:MEDIC|DENTAL|CLINIC|HEALTH|SURG|PHYSICIAN|HOSPITAL|NURS|REHAB|ORTHO|"
    r"DIALYSIS|IMAGING|URGENT|CARE CTR|CARE CENTER)"
)

ASSET_CLASSES = {
    "single_family": {"label": "Single-Family", "group": "Residential", "codes": ["01"]},
    "multifamily": {"label": "Multi-Family", "group": "Residential", "codes": ["03", "08"]},
    "vacant_land": {"label": "Vacant Land", "group": "Land", "codes": ["00", "10", "40"]},
    "office": {
        "label": "Office",
        "group": "Office",
        "codes": ["17", "18", "19"],
        "exclude_kw": MEDICAL_KW,  # medical offices move to the Specialty/Medical tab
    },
    "commercial": {
        "label": "Commercial",
        "group": "Commercial",
        "codes": [
            "11", "12", "13", "14", "15", "16",
            "21", "22", "23", "24", "25", "26", "27", "28", "29",
            "30", "31", "32", "33", "34", "35", "36", "37", "38",
        ],
    },
    "hospitality": {"label": "Hospitality", "group": "Hospitality", "codes": ["39"]},
    "specialty_marina": {"label": "Marina", "group": "Specialty", "codes": ["20"]},
    "specialty_medical": {
        "label": "Medical",
        "group": "Specialty",
        "codes": ["73", "74"],
        "include_kw_from": ["17", "18", "19"],
        "include_kw": MEDICAL_KW,
    },
}

# Workbook 2 — off-market beach condo owners, unit level.
CONDO_DELIVERABLE = {
    "label": "Beach Condo Owners",
    "codes": ["04"],  # condominium; add "05" for co-ops
    "beach_only": True,
    # "boundary_path": "data/barrier_island.geojson",
}
