#!/usr/bin/env bash
# Build the Fort Lauderdale waterfront lists on your own computer.
#
#   bash run_fort_lauderdale.sh
#
# Needs Python 3.10+ and an internet connection. Everything lands in ./output.
# Safe to re-run: finished stages are cached in ./data and reused.

set -uo pipefail

MARKET="configs/fort_lauderdale.py"
OUT="output"
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die() { printf '\n\033[31m%s\033[0m\n' "$*" >&2; exit 1; }

cd "$(dirname "$0")" || die "could not enter the script's directory"

# --- python ------------------------------------------------------------
PY=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 && \
     "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    PY="$candidate"; break
  fi
done
[ -n "$PY" ] || die "Python 3.10+ not found. Install it from https://www.python.org/downloads/ and run this again."

say "1/5  Setting up (one-time, a few minutes)"
[ -d .venv ] || "$PY" -m venv .venv || die "could not create the virtual environment"
# shellcheck disable=SC1091
source .venv/bin/activate || die "could not activate the virtual environment"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt || die "dependency install failed — send me the output above"

say "2/5  Checking the county's data is reachable"
python - <<'PYEOF' || die "Cannot reach gis.fortlauderdale.gov. Check your internet connection, or a VPN/firewall may be blocking it."
import sys, requests
try:
    r = requests.get(
        "https://gis.fortlauderdale.gov/arcgis/rest/services/GeneralPurpose/gisdata/MapServer/94",
        params={"f": "json"}, timeout=45)
    r.raise_for_status()
    print("    reachable:", r.json().get("name", "layer 94"))
except Exception as exc:
    print("   ", exc, file=sys.stderr); sys.exit(1)
PYEOF

say "3/5  Verifying the field map against the live layer"
mkdir -p "$OUT"
if ! python -m waterfront_engine.cli verify-fields --market "$MARKET" --json "$OUT/fields.json"; then
  cat <<'MSG'

  ^^ Some configured field names do not exist on the county layer (see UNMAPPED above).
     The run would produce empty columns, so it stopped here.
     Send me output/fields.json and I will correct the config.
MSG
  exit 1
fi

say "4/5  Pulling parcels and finding waterfront (several minutes, ~195k parcels)"
python -m waterfront_engine.cli run --market "$MARKET" --out-dir "$OUT" --no-sunbiz \
  || die "the run failed — send me the output above"

say "5/5  Looking up LLC owners on Sunbiz (slow — Ctrl-C is safe, progress is cached)"
python -m waterfront_engine.cli run --market "$MARKET" --out-dir "$OUT" --stages enrich,workbooks \
  || echo "  Sunbiz pass did not finish. The workbooks in $OUT are still complete apart from the manager columns."

say "Done. Your files:"
ls -1 "$OUT"/*.xlsx "$OUT"/*.kml 2>/dev/null | sed 's/^/  /'
echo
echo "  .xlsx  open in Excel — one tab per asset class"
echo "  .kml   open in Google Earth — one folder per asset class"
command -v open >/dev/null 2>&1 && open "$OUT" 2>/dev/null
