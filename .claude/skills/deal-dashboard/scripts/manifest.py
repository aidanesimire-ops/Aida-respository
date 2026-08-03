#!/usr/bin/env python3
"""
Data manifest — what data is loaded, and how fresh it is.

Scans the raw-data folders declared in the config and records, per asset class, how
many files and rows are present and the newest file date, plus an overall "data as of"
date (the most recent export). Surfaced as a "Data as of…" stamp on the dashboard and an
Excel "Data" tab, so you always know the vintage — and so adding more exports over time
shows up immediately after a refresh.

Output: data/processed/manifest.json
"""
from __future__ import annotations
import glob
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from config import CFG

ROOT = os.path.dirname(HERE)
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(PROC, exist_ok=True)


def _rows(path):
    try:
        with open(path, "rb") as f:
            return max(0, sum(1 for _ in f) - 1)   # minus header
    except OSError:
        return 0


def _date(ts):
    return time.strftime("%Y-%m-%d", time.localtime(ts)) if ts else None


def main():
    sources = []
    latest = 0.0
    for name, spec in CFG.as_dict()["assets"].items():
        folder = CFG.folder(name)
        files = sorted(glob.glob(os.path.join(folder, "*.csv")))
        if not files:
            continue
        rows = sum(_rows(f) for f in files)
        mt = max(os.path.getmtime(f) for f in files)
        latest = max(latest, mt)
        sources.append({"source": name, "folder": spec["folder"], "files": len(files),
                        "rows": int(rows), "updated": _date(mt)})
    # redfin context tsv, if present
    for tsv in glob.glob(os.path.join(ROOT, "data", "raw", "*.tsv")):
        mt = os.path.getmtime(tsv)
        latest = max(latest, mt)
        sources.append({"source": "redfin (context)", "folder": "data/raw",
                        "files": 1, "rows": _rows(tsv), "updated": _date(mt)})

    manifest = {
        "market": CFG.market["name"],
        "data_as_of": _date(latest),
        "n_sources": len(sources),
        "total_rows": int(sum(s["rows"] for s in sources)),
        "sources": sorted(sources, key=lambda s: -s["rows"]),
        "note": "Vintage = newest export in each folder. Add more CSVs to data/raw/… and "
                "re-run analysis/refresh.py to update everything; this stamp moves with your "
                "latest data.",
    }
    with open(os.path.join(PROC, "manifest.json"), "w") as f:
        json.dump(manifest, f, separators=(",", ":"))
    print(f"Manifest: data as of {manifest['data_as_of']} · {manifest['n_sources']} sources · "
          f"{manifest['total_rows']:,} rows")


if __name__ == "__main__":
    main()
