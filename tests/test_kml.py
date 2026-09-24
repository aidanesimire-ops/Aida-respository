import xml.etree.ElementTree as ET

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from waterfront_engine.kml import write_kml

KML_NS = "{http://www.opengis.net/kml/2.2}"


@pytest.fixture
def layers():
    geo = gpd.GeoDataFrame(
        geometry=[box(-80.12, 26.12, -80.119, 26.121), box(-80.13, 26.13, -80.129, 26.131)],
        crs="EPSG:4326",
    )
    sheet = pd.DataFrame(
        {
            "Folio": ["A1", "A2"],
            "Situs Address": ["700 SE CANAL DR", "710 SE CANAL DR"],
            "Owner 1": ["SMITH JOHN", "CANALSIDE HOLDINGS LLC"],
            "Mailing City": ["FORT LAUDERDALE", "NEW YORK"],
            "Absentee": ["N", "Y"],
            "Entity": ["N", "Y"],
            "Just/Market Value": [1_450_000, 2_100_000],
            "Water Body": ["Demo Canal", "Demo Canal"],
        }
    )
    return {"Single-Family": (geo, sheet, "Residential")}


def parse(path):
    return ET.parse(path).getroot()


def test_write_kml_makes_one_folder_per_layer(tmp_path, layers):
    path = write_kml(tmp_path / "out.kml", layers, document_name="Test Market")
    root = parse(path)

    doc = root.find(f"{KML_NS}Document")
    assert doc.find(f"{KML_NS}name").text == "Test Market"
    folders = doc.findall(f"{KML_NS}Folder")
    assert len(folders) == 1
    assert folders[0].find(f"{KML_NS}name").text == "Single-Family (2)"
    assert len(folders[0].findall(f"{KML_NS}Placemark")) == 2


def test_placemarks_are_points_at_centroids_by_default(tmp_path, layers):
    path = write_kml(tmp_path / "out.kml", layers, document_name="Test")
    placemark = parse(path).iter(f"{KML_NS}Placemark").__next__()

    point = placemark.find(f"{KML_NS}Point")
    assert point is not None
    assert placemark.find(f"{KML_NS}Polygon") is None
    lon, lat, _ = point.find(f"{KML_NS}coordinates").text.split(",")
    assert float(lon) == pytest.approx(-80.1195, abs=1e-3)
    assert float(lat) == pytest.approx(26.1205, abs=1e-3)


def test_polygon_mode_draws_outlines(tmp_path, layers):
    path = write_kml(tmp_path / "out.kml", layers, document_name="Test", polygons=True)
    placemark = parse(path).iter(f"{KML_NS}Placemark").__next__()
    assert placemark.find(f"{KML_NS}Polygon") is not None
    assert placemark.find(f"{KML_NS}Point") is None


def test_balloon_carries_dial_sheet_fields(tmp_path, layers):
    path = write_kml(tmp_path / "out.kml", layers, document_name="Test")
    text = path.read_text()
    assert "CANALSIDE HOLDINGS LLC" in text
    assert "$2,100,000" in text, "value should be formatted for a human reading the pin"
    assert "Demo Canal" in text
    assert "<name>700 SE CANAL DR</name>" in text


def test_xml_special_characters_are_escaped(tmp_path):
    geo = gpd.GeoDataFrame(geometry=[box(-80.12, 26.12, -80.119, 26.121)], crs="EPSG:4326")
    sheet = pd.DataFrame({"Situs Address": ["A & B <TEST>"], "Owner 1": ["SMITH & SONS"]})
    path = write_kml(
        tmp_path / "out.kml", {"L": (geo, sheet, "Residential")}, document_name="A & B"
    )
    root = parse(path)  # would raise if the XML were malformed
    assert root.iter(f"{KML_NS}Placemark").__next__().find(f"{KML_NS}name").text == "A & B <TEST>"


def test_empty_layer_is_skipped(tmp_path):
    empty = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    path = write_kml(
        tmp_path / "out.kml",
        {"Nothing": (empty, pd.DataFrame(), "Land")},
        document_name="Test",
    )
    assert parse(path).find(f"{KML_NS}Document").findall(f"{KML_NS}Folder") == []


def test_blank_fields_are_left_out_of_the_balloon(tmp_path):
    geo = gpd.GeoDataFrame(geometry=[box(-80.12, 26.12, -80.119, 26.121)], crs="EPSG:4326")
    sheet = pd.DataFrame({"Situs Address": ["X"], "Owner 2": [None], "Managers/Members": [""]})
    path = write_kml(tmp_path / "o.kml", {"L": (geo, sheet, "Land")}, document_name="T")
    text = path.read_text()
    assert "Owner 2" not in text
    assert "Managers/Members" not in text
