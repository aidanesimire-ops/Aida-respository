import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from waterfront_engine.arcgis import code_where
from waterfront_engine.condos import building_index, split_unit
from waterfront_engine.config import load_config
from waterfront_engine.demo import build_fixture
from waterfront_engine.spatial import beach_filter, buffer_water, centroid_lon, waterfront

CONFIG = "configs/fort_lauderdale.py"


@pytest.fixture(scope="module")
def cfg():
    return load_config(CONFIG)


@pytest.fixture(scope="module")
def fixture():
    return build_fixture()


# -- waterfront join -----------------------------------------------------
def test_waterfront_keeps_canal_lots_and_rejects_corner_clip(cfg, fixture):
    parcels, water = fixture
    kept = waterfront(parcels, buffer_water(water, cfg.market), cfg.market)
    folios = set(kept["FOLIO"])

    assert "5042CORNER01" not in folios, "corner-touch parcel must fail the frontage test"
    on_canal = {f"5042{i:08d}" for i in range(6)}
    assert on_canal <= folios, "lots sitting on the canal edge must be waterfront"
    assert "504200000006" in folios, "a 10 ft gap is inside the 15 ft buffer"
    assert "504200000007" not in folios, "a 60 ft gap is outside it"
    assert "504200000008" not in folios, "inland lots are not waterfront"


def test_waterfront_tags_water_body_and_frontage(cfg, fixture):
    parcels, water = fixture
    kept = waterfront(parcels, buffer_water(water, cfg.market), cfg.market)
    row = kept[kept["FOLIO"] == "504200000000"].iloc[0]
    assert row["Water_Body"] == "Demo Canal"
    assert row["Waterfront_Type"] == "Canal"
    assert row["Frontage_Ft"] >= cfg.market.min_frontage_ft
    assert row["Frontage_Ft"] == pytest.approx(100, abs=35), "≈ the 100 ft lot width"


def test_waterfront_empty_input_returns_tagged_empty(cfg, fixture):
    parcels, water = fixture
    empty = parcels.iloc[0:0]
    out = waterfront(empty, buffer_water(water, cfg.market), cfg.market)
    assert out.empty
    assert {"Waterfront_Type", "Water_Body", "Frontage_Ft"} <= set(out.columns)


def test_water_type_exclude_filters(cfg, fixture):
    _, water = fixture
    market = type(cfg.market)(**{**cfg.market.__dict__, "water_type_exclude": r"Canal"})
    remaining = buffer_water(water, market)
    assert list(remaining["TYPE"]) == ["Estuary"]


def test_buffer_water_rejects_empty_layer(cfg, fixture):
    _, water = fixture
    with pytest.raises(ValueError):
        buffer_water(water.iloc[0:0], cfg.market)


# -- beach filter --------------------------------------------------------
def test_beach_filter_splits_on_longitude(cfg, fixture):
    parcels, _ = fixture
    condos = parcels[parcels["USECD"] == "04"]
    kept = beach_filter(condos, cfg.market)
    assert len(kept) == 8
    assert kept["SITEADDRESS"].str.startswith("4300").all()
    assert (centroid_lon(kept, cfg.market) > cfg.market.beach_lon_threshold).all()


def test_beach_filter_polygon_path(cfg, fixture, tmp_path):
    parcels, _ = fixture
    condos = parcels[parcels["USECD"] == "04"].copy()
    island = gpd.GeoDataFrame(
        geometry=[box(-80.11, 26.0, -80.0, 26.3)], crs="EPSG:4326"
    )
    path = tmp_path / "island.geojson"
    island.to_file(path, driver="GeoJSON")

    kept = beach_filter(condos, cfg.market, str(path))
    assert len(kept) == 8
    assert kept["SITEADDRESS"].str.startswith("4300").all()


# -- condo unit parsing --------------------------------------------------
@pytest.mark.parametrize(
    "address,expected",
    [
        ("4300 N OCEAN BLVD # 12B", ("4300 N OCEAN BLVD", "12B")),
        ("4300 N OCEAN BLVD UNIT 5", ("4300 N OCEAN BLVD", "5")),
        ("100 S BIRCH RD APT 1204", ("100 S BIRCH RD", "1204")),
        ("100 S BIRCH RD STE 200", ("100 S BIRCH RD", "200")),
        ("100 S BIRCH RD", ("100 S BIRCH RD", "")),
        ("", ("", "")),
        (None, ("", "")),
    ],
)
def test_split_unit(address, expected):
    assert split_unit(address) == expected


def test_building_index_aggregates():
    units = pd.DataFrame(
        {
            "Folio": ["1", "2", "3", "4"],
            "Building": ["TOWER A", "TOWER A", "TOWER A", "TOWER B"],
            "Entity": ["Y", "N", "Y", "N"],
            "Absentee": ["Y", "Y", "N", "N"],
            "Just/Market Value": [1_000_000, 2_000_000, 3_000_000, 500_000],
        }
    )
    idx = building_index(units).set_index("Building")
    assert idx.loc["TOWER A", "Units"] == 3
    assert idx.loc["TOWER A", "LLC Owned"] == 2
    assert idx.loc["TOWER A", "LLC %"] == pytest.approx(66.7)
    assert idx.loc["TOWER A", "Median Value"] == 2_000_000
    assert list(idx.index) == ["TOWER A", "TOWER B"]  # sorted by unit count


# -- WHERE building ------------------------------------------------------
def test_code_where_quotes_strings_and_pads():
    clause = code_where("USECD", ["01", "3"], field_type="esriFieldTypeString")
    assert clause.startswith("USECD IN (")
    for variant in ("'01'", "'1'", "'03'", "'3'"):
        assert variant in clause


def test_code_where_leaves_numeric_columns_unquoted():
    clause = code_where("USECD", ["01", "39"], field_type="esriFieldTypeSmallInteger")
    assert clause == "USECD IN (1,39)"


def test_code_where_prefix_uses_like():
    clause = code_where("DORUSE", ["01"], field_type="esriFieldTypeString", match="prefix")
    assert clause == "(DORUSE LIKE '01%')"


def test_code_where_prefix_on_numeric_column_is_rejected():
    with pytest.raises(ValueError):
        code_where("USECD", ["01"], field_type="esriFieldTypeInteger", match="prefix")
