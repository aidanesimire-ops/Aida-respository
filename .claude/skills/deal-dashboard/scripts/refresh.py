#!/usr/bin/env python3
"""
One-command rebuild of the entire deal dashboard.

    python analysis/refresh.py           # discover data, then rebuild everything
    python analysis/refresh.py --check   # discovery + column validation only, no build

This is the front door for the dynamic model: drop new CSV exports into the folders
declared in `config/deal_dashboard.yml`, adjust any thresholds there, and run this.
It first reports what data it found for each asset class and validates that your
column maps match the actual export headers (so a renamed column is caught before it
silently drops data), then runs the full pipeline and points you at the outputs.
"""
from __future__ import annotations
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG, ROOT  # noqa: E402
import run_all  # noqa: E402


def _rel(p):
    return os.path.relpath(p, ROOT)


def discover():
    """Report files, row counts and status breakdown per asset; flag column mismatches."""
    print("=" * 74)
    print(f"  {CFG.market['name']} — deal dashboard refresh")
    print(f"  config: {_rel(os.path.join(ROOT, 'config', 'deal_dashboard.yml'))}"
          if os.path.exists(os.path.join(ROOT, "config", "deal_dashboard.yml"))
          else "  config: built-in defaults (no YAML found)")
    print("=" * 74)
    any_problem = False
    for name, spec in CFG.as_dict()["assets"].items():
        folder = CFG.folder(name)
        files = sorted(glob.glob(os.path.join(folder, "*.csv")))
        if not files:
            print(f"\n• {name:16s} — no CSVs in {_rel(folder)}  (skipped)")
            continue
        # validate column map against the first file's header
        header = list(pd.read_csv(files[0], nrows=0).columns)
        missing = [c for c in spec["columns"].values() if c not in header]
        # row counts + status distribution
        total, statuses = 0, {}
        for f in files:
            df = pd.read_csv(f)
            total += len(df)
            if spec.get("status_from") == "column":
                col = spec["status_column"]
                if col in df.columns:
                    mapped = df[col].map(spec["status_map"])
                    for k, v in mapped.value_counts().items():
                        statuses[k] = statuses.get(k, 0) + int(v)
            else:  # status from filename stem
                key = os.path.splitext(os.path.basename(f))[0]
                bucket = spec["status_map"].get(key)
                if bucket:
                    statuses[bucket] = statuses.get(bucket, 0) + len(df)
        st = " · ".join(f"{k} {v:,}" for k, v in sorted(statuses.items(), key=lambda x: -x[1]))
        print(f"\n• {name:16s} — {len(files)} file(s), {total:,} rows  [{_rel(folder)}]")
        print(f"    status: {st or '(no rows matched the status map)'}")
        if missing:
            any_problem = True
            print(f"    ⚠ column map misses {len(missing)} column(s) not in the export header:")
            print(f"      {missing}")
            print(f"      → fix the `{name}.columns` block in the config, or the export.")
    print()
    return not any_problem


def main():
    check_only = "--check" in sys.argv
    ok = discover()
    if check_only:
        print("Check-only run complete." + ("" if ok else "  Resolve the ⚠ items above."))
        return
    if not ok:
        print("Proceeding despite column warnings above — affected fields may be blank.\n")
    print("Building the full pipeline …\n")
    run_all.main()
    print("\n" + "=" * 74)
    print("  Rebuilt. Outputs:")
    print("    • dashboard/index.html                          (interactive dashboard)")
    print("    • outputs/Fort_Lauderdale_PPSF_Normalized.xlsx   (workbook — Index tab)")
    print("    • REPORT.md                                      (written analysis)")
    print("    • data/processed/*_bundle.json                   (data bundles)")
    print("=" * 74)


if __name__ == "__main__":
    main()
