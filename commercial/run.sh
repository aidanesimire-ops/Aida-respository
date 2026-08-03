#!/usr/bin/env bash
# One-command runner: rebuild the whole workbook + dashboard from the CSVs in data/raw/.
#
#   1. Put your MLS export CSV(s) in  data/raw/  (delete the old ones first).
#   2. From this folder run:   ./run.sh        (or:  bash run.sh )
#   3. Open  outputs/Commercial_Deal_Dashboard.xlsx  and  dashboard/index.html
#
set -e
cd "$(dirname "$0")"
echo "Installing dependencies (first run only)…"
python3 -m pip install -q -r requirements.txt
echo "Running the full analysis on the data in data/raw/ …"
python3 analysis/run_all.py
echo ""
echo "Done. Open:"
echo "  outputs/Commercial_Deal_Dashboard.xlsx   (the workbook — start on the 'Guide' and 'Start Here' tabs)"
echo "  dashboard/index.html                     (the interactive dashboard)"
echo "  outputs/Cold_Call_Sheets.pdf / Neighborhood_Report.pdf   (printable)"
