import pandas as pd
import pytest

from waterfront_engine.classify import (
    class_mask,
    match_codes,
    normalize_use,
    overlap_report,
    split_asset_classes,
    use_code_census,
)
from waterfront_engine.config import load_config
from waterfront_engine.flags import absentee_flag, add_flags, callable_entities, entity_type

CONFIG = "configs/fort_lauderdale.py"


@pytest.fixture(scope="module")
def cfg():
    return load_config(CONFIG)


def frame(rows):
    return pd.DataFrame(rows)


# -- use codes -----------------------------------------------------------
def test_normalize_use_pads_and_strips():
    got = normalize_use(pd.Series(["1", "01", " 3 ", "1.0", "0100", None]))
    assert list(got) == ["01", "01", "03", "01", "0100", ""]


def test_match_codes_handles_unpadded_source_values():
    use = pd.Series(["1", "01", "3", "39"])
    assert list(match_codes(use, ["01"])) == [True, True, False, False]


def test_match_codes_prefix_mode_catches_detail_codes():
    use = pd.Series(["0100", "0110", "0300"])
    assert list(match_codes(use, ["01"], match="prefix")) == [True, True, False]


# -- asset class split ---------------------------------------------------
def test_medical_office_moves_to_specialty(cfg):
    df = frame(
        [
            {"USECD": "19", "USEDSCRP": "OFFICE", "DORUSEDETAILS": "MEDICAL PLAZA"},
            {"USECD": "19", "USEDSCRP": "OFFICE", "DORUSEDETAILS": "PROFESSIONAL SERVICES"},
            {"USECD": "73", "USEDSCRP": "MEDICAL", "DORUSEDETAILS": "HOSPITAL"},
        ]
    )
    office = class_mask(df, cfg.asset_classes["office"], cfg.market)
    medical = class_mask(df, cfg.asset_classes["specialty_medical"], cfg.market)

    assert list(office) == [False, True, False]
    assert list(medical) == [True, False, True]
    # and no parcel lands in both
    assert not (office & medical).any()


def test_split_tags_group_and_class(cfg):
    df = frame([{"USECD": "20", "USEDSCRP": "MARINA", "DORUSEDETAILS": ""}])
    buckets = split_asset_classes(df, cfg.asset_classes, cfg.market)
    marina = buckets["specialty_marina"]
    assert len(marina) == 1
    assert marina["Asset_Class"].iloc[0] == "Marina"
    assert marina["Asset_Group"].iloc[0] == "Specialty"
    assert buckets["commercial"].empty


def test_every_configured_class_is_reachable(cfg):
    """Each class must claim at least one row of its own primary codes."""
    rows = [
        {"FOLIO": f"F{i}", "USECD": code, "USEDSCRP": "", "DORUSEDETAILS": ""}
        for i, code in enumerate(cfg.all_source_codes)
    ]
    buckets = split_asset_classes(frame(rows), cfg.asset_classes, cfg.market)
    empty = [k for k, v in buckets.items() if v.empty]
    assert empty == []


def test_overlap_report_flags_shared_folios(cfg):
    buckets = {
        "office": frame([{"FOLIO": "A1"}, {"FOLIO": "A2"}]),
        "specialty_medical": frame([{"FOLIO": "A1"}]),
    }
    classes = {k: cfg.asset_classes[k] for k in buckets}
    report = overlap_report(buckets, classes, cfg.market)
    assert list(report["Folio"]) == ["A1"]
    assert report["Count"].iloc[0] == 2


def test_use_code_census_counts(cfg):
    df = frame([{"USECD": c, "USEDSCRP": "X"} for c in ["01", "1", "39"]])
    census = use_code_census(df, cfg.market)
    counts = dict(zip(census["DOR Use"], census["Parcels"]))
    assert counts == {"01": 2, "39": 1}


# -- flags ---------------------------------------------------------------
@pytest.mark.parametrize(
    "name,expected",
    [
        ("CANALSIDE HOLDINGS LLC", "LLC"),
        ("OCEAN VENTURES L.P.", "LP"),
        ("SMITH FAMILY TRUST", "TRUST"),
        ("JONES ROBERT TR", "TRUST"),
        ("BAY REALTY INC", "INC"),
        ("CITY OF FORT LAUDERDALE", "GOVERNMENT"),
        ("SMITH JOHN A", ""),
        ("LANDON MARIA", ""),  # 'LAND' must not match inside a person's name
        ("COLE PATRICIA", ""),  # nor 'CO' inside COLE
        (None, ""),
    ],
)
def test_entity_type(name, expected):
    assert entity_type(name) == expected


@pytest.mark.parametrize(
    "city,expected",
    [("FORT LAUDERDALE", "N"), ("ft lauderdale", "N"), ("NEW YORK", "Y"), ("", "Unknown"), (None, "Unknown")],
)
def test_absentee_flag(city, expected, cfg):
    assert absentee_flag(city, cfg.market.local_cities) == expected


def test_add_flags_and_callable_entities(cfg):
    df = frame(
        [
            {"OWNERNME1": "BLUE WATER PROPERTIES LLC", "PSTLCITY": "NEW YORK"},
            {"OWNERNME1": "SMITH JOHN", "PSTLCITY": "FORT LAUDERDALE"},
            {"OWNERNME1": "CITY OF FORT LAUDERDALE", "PSTLCITY": "FORT LAUDERDALE"},
        ]
    )
    out = add_flags(df, cfg.market)
    assert list(out["Entity_YN"]) == ["Y", "N", "Y"]
    assert list(out["Absentee_YN"]) == ["Y", "N", "N"]
    # city-owned parcels are entities but not cold-call targets
    assert list(callable_entities(out)) == [True, False, False]
