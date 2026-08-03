"""Styled Excel output for both workbooks."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Mapping, Sequence

import pandas as pd

log = logging.getLogger(__name__)

NAVY = "#1F3A5F"
MONEY_COLS = {"Just/Market Value", "Median Value", "Total Value", "Sale Price"}
INT_COLS = {"Bldg SqFt", "# Bldgs", "Units", "LLC Owned", "Absentee", "Parcels", "Frontage (ft)"}
MIN_WIDTH, MAX_WIDTH = 10, 42


def _sheet_names(names: Sequence[str]) -> dict[str, str]:
    """Excel caps tab names at 31 chars and forbids duplicates."""
    used: set[str] = set()
    out: dict[str, str] = {}
    for name in names:
        base = str(name)[:31] or "Sheet"
        candidate, n = base, 2
        while candidate.lower() in used:
            suffix = f"~{n}"
            candidate = base[: 31 - len(suffix)] + suffix
            n += 1
        used.add(candidate.lower())
        out[name] = candidate
    return out


def _width(series: pd.Series, header: str) -> int:
    sample = series.head(500).astype("string").fillna("")
    widest = sample.str.len().max()  # NA on an empty column
    longest = 0 if pd.isna(widest) else int(widest)
    return max(MIN_WIDTH, min(MAX_WIDTH, max(longest, len(header)) + 2))


def write_workbook(
    path: str | Path,
    sheets: Mapping[str, pd.DataFrame],
    *,
    title: str = "",
    notes: Sequence[str] = (),
) -> Path:
    """Write tabs with a navy header row, frozen panes, autofilter and formats."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tabs = _sheet_names(list(sheets.keys()))

    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        book = writer.book
        f_title = book.add_format({"bold": True, "font_size": 12, "font_name": "Calibri"})
        f_head = book.add_format(
            {
                "bg_color": NAVY,
                "font_color": "white",
                "bold": True,
                "font_name": "Calibri",
                "border": 1,
                "text_wrap": True,
                "valign": "vcenter",
            }
        )
        f_money = book.add_format({"num_format": "$#,##0", "font_name": "Calibri"})
        f_int = book.add_format({"num_format": "#,##0", "font_name": "Calibri"})
        f_text = book.add_format({"font_name": "Calibri"})

        for name, frame in sheets.items():
            tab = tabs[name]
            frame.to_excel(writer, sheet_name=tab, index=False, startrow=1)
            sheet = writer.sheets[tab]

            heading = f"{title} — {name}" if title else str(name)
            sheet.write(0, 0, f"{heading}  ({len(frame):,} rows)", f_title)

            for col, header in enumerate(frame.columns):
                sheet.write(1, col, str(header), f_head)
                fmt = f_money if header in MONEY_COLS else f_int if header in INT_COLS else f_text
                sheet.set_column(col, col, _width(frame[header], str(header)), fmt)

            sheet.freeze_panes(2, 0)
            if len(frame.columns):
                sheet.autofilter(1, 0, max(len(frame) + 1, 2), len(frame.columns) - 1)
            sheet.set_row(1, 30)

        if notes:
            sheet = book.add_worksheet("Read Me")
            sheet.set_column(0, 0, 110)
            sheet.write(0, 0, title or "Read Me", f_title)
            wrap = book.add_format({"font_name": "Calibri", "text_wrap": True, "valign": "top"})
            for i, line in enumerate(notes, start=2):
                sheet.write(i, 0, line, wrap)

    log.info("wrote %s (%d tabs)", path, len(sheets))
    return path


def summary_table(
    sheets: Mapping[str, pd.DataFrame], groups: Mapping[str, str] | None = None
) -> pd.DataFrame:
    """Per-tab counts for the Summary sheet.

    ``groups`` supplies each tab's asset group from the config, so a class that
    came back empty still shows its group instead of a blank.
    """
    rows = []
    for name, frame in sheets.items():
        group = (groups or {}).get(name, "")
        if not group and "Group" in frame.columns and len(frame):
            group = str(frame["Group"].iloc[0])
        entity = int((frame["Entity"] == "Y").sum()) if "Entity" in frame.columns else 0
        absentee = int((frame["Absentee"] == "Y").sum()) if "Absentee" in frame.columns else 0
        value = frame["Just/Market Value"] if "Just/Market Value" in frame.columns else None
        rows.append(
            {
                "Asset Class": name,
                "Group": group,
                "Parcels": len(frame),
                "LLC/Entity": entity,
                "LLC/Entity %": round(100 * entity / len(frame), 1) if len(frame) else 0.0,
                "Absentee": absentee,
                "Absentee %": round(100 * absentee / len(frame), 1) if len(frame) else 0.0,
                "Total Value": float(pd.to_numeric(value, errors="coerce").sum()) if value is not None else 0.0,
            }
        )
    return pd.DataFrame(rows)


PROVENANCE_NOTES = (
    "Source: county property appraiser parcel/ownership records and state business-entity "
    "filings, joined to the county hydrography layer. All rows are current owners of record.",
    "Off-market by design: no MLS or listing feed is used anywhere in this pipeline, so no "
    "owner is included or excluded based on whether their property is listed.",
    "Waterfront is measured, not assumed: a parcel qualifies only when its boundary runs along "
    "mapped water for at least the configured minimum frontage. Spot-check on satellite before dialing.",
    "Absentee = owner's mailing city is outside the market. 'Unknown' means the record has no mailing city.",
    "Entity flag is a name-pattern match on the owner of record; the Sunbiz columns are the "
    "authoritative manager / registered-agent detail where they are populated.",
    "Before cold-calling: scrub numbers against the National DNC Registry and any state list, and "
    "mind state telemarketing rules (in Florida, the 2021 mini-TCPA call-window and consent rules). "
    "Public ownership data is fine for research and mail; live calling has its own rules. Not legal advice.",
)
