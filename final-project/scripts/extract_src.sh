#!/usr/bin/env bash
set -euo pipefail

# Requires: mdbtools (brew install mdbtools)
# Exports the 4 needed tables from each .mdb/.accdb under data_raw/SRC*/

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_ROOT="${ROOT}/data_raw"
OUT_ROOT="${ROOT}/data_work"

# Tables we care about (exact Access table names)
declare -a TABLES=(
  "ACC EM Chronic Absenteeism"
  "Annual EM ELA"
  "Annual EM Math"
  "BOCES and N/RC"
)

shopt -s nullglob
found=0
for DB in "${SRC_ROOT}"/SRC*/**/*.mdb "${SRC_ROOT}"/SRC*/**/*.accdb "${SRC_ROOT}"/SRC*/*.{mdb,accdb}; do
  [ -e "$DB" ] || continue
  found=1
  YEAR_DIR="$(dirname "$DB")"
  YEAR_BASE="$(basename "$YEAR_DIR")"    # e.g., SRC2024
  OUT_DIR="${OUT_ROOT}/${YEAR_BASE}"
  mkdir -p "${OUT_DIR}"

  echo ">> Extracting from: $DB"
  for TBL in "${TABLES[@]}"; do
    SAFE_NAME="$(echo "$TBL" | tr '[:upper:]' '[:lower:]' | tr ' /' '__' | tr -cd '[:alnum:]_')"
    CSV="${OUT_DIR}/${SAFE_NAME}.csv"
    echo "   - $TBL  ->  ${CSV}"
    # mdb-export prints CSV to stdout
    # -D sets date format; we also add header
    if ! mdb-export -D "%Y-%m-%d" "$DB" "$TBL" > "$CSV"; then
      echo "WARN: failed to export table '$TBL' from '$DB' (skipping)"
      rm -f "$CSV" || true
    fi
  done
done

if [ "$found" -eq 0 ]; then
  echo "No .mdb/.accdb found under ${SRC_ROOT}/SRC*/"
  exit 1
fi

echo "OK: CSVs written under ${OUT_ROOT}/SRCYYYY/*.csv"
