#!/usr/bin/env python3
"""
Run the whole commercial deal-dashboard pipeline end to end.

    python analysis/run_all.py

Reads the BeachesMLS commercial exports in data/raw/, builds the normalized $/SqFt layer and
the assumption-driven income layer, then every deliverable (charts, Excel, interactive
dashboard, report).
"""
import os
import runpy
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("Normalize $/SqFt + attach assumption income", "cre_normalize.py"),
    ("Reprice live inventory", "reprice.py"),
    ("Segments & absorption", "bands.py"),
    ("Prospecting", "prospects.py"),
    ("Comps drill-down", "comps.py"),
    ("Leasing layer + data-derived caps", "cre_leases.py"),
    ("Master ranked submarkets", "master_summary.py"),
    ("Cold-call sheets", "callsheets.py"),
    ("Charts", "build_charts.py"),
    ("Excel workbook", "build_excel.py"),
    ("Interactive dashboard", "build_dashboard.py"),
    ("Neighborhood systems report", "build_neighborhood_report.py"),
    ("Written report", "build_report.py"),
]


def main():
    for i, (label, script) in enumerate(STEPS, 1):
        print(f"\n{'='*68}\n[{i}/{len(STEPS)}] {label}  ({script})\n{'='*68}")
        try:
            runpy.run_path(os.path.join(HERE, script), run_name="__main__")
        except Exception as e:  # noqa: BLE001
            print(f"!! {script} failed: {e}", file=sys.stderr)
            raise
    print("\nAll done. See dashboard/index.html, outputs/, REPORT.md, data/processed/.")


if __name__ == "__main__":
    main()
