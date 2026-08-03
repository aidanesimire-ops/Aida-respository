"""Synthetic fixture + offline end-to-end run.

No network: this builds a small make-believe city (a canal, a row of waterfront
lots, some inland lots, a beachfront condo tower and a mainland one), pushes it
through every stage, and writes both workbooks. It is how the pipeline is tested
and the fastest way to see the output shape before pointing at a live county.
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd
from pyproj import Transformer
from shapely.geometry import box

from .config import MarketConfig, load_config

log = logging.getLogger(__name__)

# Mainland canal block and a barrier island east of the -80.11 threshold.
MAINLAND = (-80.135, 26.120)
BEACH = (-80.105, 26.120)


class DemoResolver:
    """Stand-in for Sunbiz so the enrichment columns are exercised offline."""

    def lookup(self, name: str) -> dict[str, str]:
        return {
            "Sunbiz_Entity": str(name).title(),
            "Sunbiz_Status": "ACTIVE (SYNTHETIC)",
            "Sunbiz_DocNumber": "L00000000000",
            "Registered_Agent": "SYNTHETIC AGENT | 100 MAIN ST | FORT LAUDERDALE, FL",
            "Managers_Members": "SYNTHETIC, MANAGER, MGR | 100 MAIN ST",
            "Sunbiz_Principal_Address": "100 MAIN ST | FORT LAUDERDALE, FL",
            "Sunbiz_URL": "https://search.sunbiz.org/",
        }


def _rows() -> list[dict[str, object]]:
    """Attribute rows; geometry is attached by :func:`build_fixture`."""
    owners = [
        ("SMITH JOHN A", "SMITH MARY", "FORT LAUDERDALE"),
        ("CANALSIDE HOLDINGS LLC", "", "NEW YORK"),
        ("BLUE WATER PROPERTIES LLC", "", "FT LAUDERDALE"),
        ("GARCIA LUIS", "GARCIA ANA", "CHICAGO"),
        ("OCEAN VENTURES LP", "", "BOSTON"),
        ("JONES ROBERT TR", "", "FORT LAUDERDALE"),
        ("MARINA GROUP INC", "", "MIAMI"),
        ("WILLIAMS SUSAN", "", ""),
    ]
    specs = [
        # (use code, description, detail, value, sqft, buildings)
        ("01", "SINGLE FAMILY", "SINGLE FAMILY RESIDENTIAL", 1_450_000, 3200, 1),
        ("01", "SINGLE FAMILY", "SINGLE FAMILY RESIDENTIAL", 2_100_000, 4100, 1),
        ("03", "MULTI-FAMILY", "MULTIFAMILY 10 UNITS OR MORE", 6_400_000, 18000, 2),
        ("08", "MULTI-FAMILY", "MULTIFAMILY LESS THAN 10 UNITS", 1_900_000, 7400, 1),
        ("00", "VACANT RESIDENTIAL", "VACANT LAND", 850_000, 0, 0),
        ("10", "VACANT COMMERCIAL", "VACANT LAND", 1_250_000, 0, 0),
        ("17", "OFFICE", "OFFICE BUILDING ONE STORY", 3_300_000, 12000, 1),
        ("19", "OFFICE", "PROFESSIONAL SERVICES MEDICAL PLAZA", 5_100_000, 22000, 1),
        ("11", "STORES", "RETAIL STORE ONE STORY", 2_750_000, 9000, 1),
        ("39", "HOTEL/MOTEL", "HOTEL OR MOTEL", 24_000_000, 88000, 3),
        ("20", "MARINA", "MARINAS MARINE TERMINALS PIERS", 11_500_000, 6000, 4),
        ("73", "MEDICAL", "HOSPITAL PRIVATE", 18_000_000, 54000, 2),
    ]
    rows = []
    for i, (use, desc, detail, value, sqft, bldgs) in enumerate(specs):
        owner1, owner2, city = owners[i % len(owners)]
        rows.append(
            {
                "FOLIO": f"5042{i:08d}",
                "OWNERNME1": owner1,
                "OWNERNME2": owner2,
                "OWNERS": f"{owner1} {('& ' + owner2) if owner2 else ''}".strip(),
                "PSTLADDRESS": f"{100 + i} MAILING WAY",
                "PSTLCITY": city,
                "SITEADDRESS": f"{700 + i * 10} SE CANAL DR",
                "USECD": use,
                "USEDSCRP": desc,
                "DORUSEDETAILS": detail,
                "CNTASSDVAL": value,
                "CNTYGISSQFT": sqft,
                "BLDGNUMOF": bldgs,
            }
        )
    return rows


def _condo_rows(prefix: str, building: str, count: int, beach: bool) -> list[dict[str, object]]:
    owners = [
        ("KOWALSKI ANNA", "", "TORONTO"),
        ("SEA BREEZE INVESTMENTS LLC", "", "NEW YORK"),
        ("PATEL RAJ", "PATEL MEENA", "FORT LAUDERDALE"),
        ("NORTHSTAR CAPITAL LLC", "", "CHICAGO"),
    ]
    rows = []
    for i in range(count):
        owner1, owner2, city = owners[i % len(owners)]
        unit = f"{(i // 4) + 5}{'ABCD'[i % 4]}"
        rows.append(
            {
                "FOLIO": f"{prefix}{i:06d}",
                "OWNERNME1": owner1,
                "OWNERNME2": owner2,
                "OWNERS": f"{owner1} {('& ' + owner2) if owner2 else ''}".strip(),
                "PSTLADDRESS": f"{200 + i} MAILING WAY",
                "PSTLCITY": city,
                "SITEADDRESS": f"{building} # {unit}",
                "USECD": "04",
                "USEDSCRP": "CONDOMINIUM",
                "DORUSEDETAILS": "RESIDENTIAL CONDOMINIUM UNIT",
                "CNTASSDVAL": 700_000 + i * 45_000 + (400_000 if beach else 0),
                "CNTYGISSQFT": 1400 + i * 60,
                "BLDGNUMOF": 1,
            }
        )
    return rows


def build_fixture() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Return ``(parcels, water)`` in EPSG:4326.

    Layout, in feet from the mainland anchor:

    * canal   : 1200 x 60 strip along y = 0..60
    * lots  0-5 : sit on the canal edge          -> waterfront
    * lot     6 : 10 ft off the canal            -> waterfront (buffer bridges it)
    * lot     7 : 60 ft off the canal            -> not waterfront
    * lots  8-11: 400 ft inland                  -> not waterfront
    * corner lot: touches the canal at one corner-> rejected by the frontage rule
    """
    to_ft = Transformer.from_crs(4326, 2236, always_xy=True)
    mx, my = to_ft.transform(*MAINLAND)
    bx, by = to_ft.transform(*BEACH)

    canal = box(mx, my, mx + 1200, my + 60)
    water = gpd.GeoDataFrame(
        {"NAME": ["Demo Canal", "Demo Intracoastal"], "TYPE": ["Canal", "Estuary"]},
        geometry=[canal, box(bx - 400, by - 200, bx - 250, by + 900)],
        crs=2236,
    )

    rows = _rows()
    geoms = []
    for i in range(len(rows)):
        x0 = mx + (i % 6) * 110
        if i < 6:  # on the canal edge
            y0 = my + 60
        elif i == 6:  # 10 ft gap — inside the 15 ft buffer
            y0 = my + 70
        elif i == 7:  # 60 ft gap — outside it
            y0 = my + 120
        else:  # well inland
            y0 = my + 400 + (i - 8) * 130
        geoms.append(box(x0, y0, x0 + 100, y0 + 120))

    # Corner clip: shares exactly one point with the canal's east end.
    rows.append(
        {
            "FOLIO": "5042CORNER01",
            "OWNERNME1": "CORNER CLIP TEST LLC",
            "OWNERNME2": "",
            "OWNERS": "CORNER CLIP TEST LLC",
            "PSTLADDRESS": "999 MAILING WAY",
            "PSTLCITY": "DENVER",
            "SITEADDRESS": "999 SE CANAL DR",
            "USECD": "01",
            "USEDSCRP": "SINGLE FAMILY",
            "DORUSEDETAILS": "SINGLE FAMILY RESIDENTIAL",
            "CNTASSDVAL": 900_000,
            "CNTYGISSQFT": 2100,
            "BLDGNUMOF": 1,
        }
    )
    geoms.append(box(mx + 1200, my - 100, mx + 1300, my))

    condo_rows = _condo_rows("704200", "4300 N OCEAN BLVD", 8, beach=True)
    condo_rows += _condo_rows("704300", "1500 W BROWARD BLVD", 4, beach=False)
    for i, row in enumerate(condo_rows):
        beach_tower = str(row["SITEADDRESS"]).startswith("4300")
        ax, ay = (bx, by) if beach_tower else (mx, my)
        x0 = ax + (i % 2) * 40
        y0 = ay + 300 + (i // 2) * 40
        geoms.append(box(x0, y0, x0 + 35, y0 + 35))
    rows += condo_rows

    parcels = gpd.GeoDataFrame(rows, geometry=geoms, crs=2236)
    return parcels.to_crs(4326), water.to_crs(4326)


def seed_fixture(cfg: MarketConfig) -> None:
    """Write the fixture into the config's data dir as if fetch had run."""
    from .pipeline import PARCELS_FILE, WATER_FILE, _save

    parcels, water = build_fixture()
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    _save(parcels, cfg.stage_path(PARCELS_FILE))
    _save(water, cfg.stage_path(WATER_FILE))
    log.info("fixture: %d parcels, %d water features", len(parcels), len(water))


SYNTHETIC_WARNING = (
    "*** SYNTHETIC DEMO DATA — DO NOT CALL ANYONE FROM THIS WORKBOOK. ***",
    "Every parcel, owner name, mailing address and entity filing in this file was invented by "
    "waterfront_engine/demo.py to exercise the pipeline offline. None of it describes a real "
    "property or a real person. Real output comes from `cli run` against the live county layer.",
)


def run_demo(out_dir: Path, market_path: str = "configs/fort_lauderdale.py") -> dict[str, Path]:
    """Full offline run against the real market config, on fixture data.

    The market name is stamped SYNTHETIC DEMO so it carries into the workbook
    filenames and title rows — a fixture call sheet that reads as genuine is
    worse than no call sheet.
    """
    import dataclasses

    from . import pipeline

    out_dir = Path(out_dir)
    cfg = load_config(market_path, data_dir=out_dir / "data", out_dir=out_dir)
    cfg.market = dataclasses.replace(cfg.market, name=f"{cfg.market.name} SYNTHETIC DEMO")

    seed_fixture(cfg)
    pipeline.classify_stage(cfg)
    pipeline.waterfront_stage(cfg)
    pipeline.flags_stage(cfg)
    pipeline.enrich_stage(cfg, DemoResolver())

    paths = {"ownership_workbook": pipeline.build_ownership_workbook(cfg, SYNTHETIC_WARNING)}
    condo = pipeline.build_condo_workbook(cfg, SYNTHETIC_WARNING)
    if condo:
        paths["condo_workbook"] = condo
    paths["run_report"] = pipeline.write_run_report(cfg, {"data_source": "SYNTHETIC FIXTURE"})
    return paths
