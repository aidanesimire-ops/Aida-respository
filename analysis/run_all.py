#!/usr/bin/env python3
"""
Run the whole Fort Lauderdale PPSF pipeline end to end.

    python analysis/run_all.py

Order matters: the Redfin layer is built first (the MLS talking points borrow its
appreciation & days-on-market), then the per-home MLS layer, then every deliverable.
"""
import runpy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ("Redfin neighborhood normalization", "normalize_ppsf.py"),
    ("MLS per-home hedonic + profiles", "mls_normalize.py"),
    ("Street-by-street underwriting", "street_underwrite.py"),
    ("High-ticket underwriting (>=$1M)", "high_ticket.py"),
    ("Underpriced opportunities + reasons", "underpriced.py"),
    ("Absorption / months-of-supply", "absorption.py"),
    ("Seller / listing-prospect engine", "seller_prospects.py"),
    ("Teardown / land-play screen", "teardown.py"),
    ("Comps drill-down", "comps.py"),
    ("Reprice live inventory", "reprice.py"),
    ("Time analysis (2020 -> now)", "time_analysis.py"),
    ("Master ranked neighborhood summary", "master_summary.py"),
    ("Charts", "build_charts.py"),
    ("Excel workbook", "build_excel.py"),
    ("Interactive dashboard", "build_dashboard.py"),
    ("Written report", "build_report.py"),
]


def main():
    for i, (label, script) in enumerate(STEPS, 1):
        print(f"\n{'='*70}\n[{i}/{len(STEPS)}] {label}  ({script})\n{'='*70}")
        try:
            runpy.run_path(os.path.join(HERE, script), run_name="__main__")
        except Exception as e:  # noqa: BLE001
            print(f"!! {script} failed: {e}", file=sys.stderr)
            raise
    print("\nAll done. See outputs/, dashboard/, data/processed/, and REPORT.md.")


if __name__ == "__main__":
    main()
