#!/usr/bin/env bash
set -euo pipefail
# Requires: mdbtools (brew install mdbtools)
# Purpose: Export core tables (attendance, ELA, Math, org) from each SRC*.mdb/accdb
#          into CSVs under data_work/SRCYYYY/

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC_ROOT="${ROOT}/data_raw"
OUT_ROOT="${ROOT}/data_work"

# ----------------- ELA -----------------
# Try older per-grade union first
export_union_matches "$DB" '^ELA[3-8][[:space:]]+Subgroup[[:space:]]+Results$' "${OUT_DIR}/annual_em_ela.csv" || true

# If union didn't produce a non-empty file, try multiple Annual patterns
if [ ! -s "${OUT_DIR}/annual_em_ela.csv" ]; then
export_first_match "$DB" 'Annual[[:space:]]+E.?/?M.?[[:space:]]+ELA' "${OUT_DIR}/annual_em_ela.csv" || \
export_first_match "$DB" 'Annual.*ELA'                             "${OUT_DIR}/annual_em_ela.csv" || \
export_first_match "$DB" 'ELA.*Annual'                             "${OUT_DIR}/annual_em_ela.csv" || true
fi

# ----------------- Math -----------------
export_union_matches "$DB" '^Math[3-8][[:space:]]+Subgroup[[:space:]]+Results$' "${OUT_DIR}/annual_em_math.csv" || true

if [ ! -s "${OUT_DIR}/annual_em_math.csv" ]; then
export_first_match "$DB" 'Annual[[:space:]]+E.?/?M.?[[:space:]]+Math' "${OUT_DIR}/annual_em_math.csv" || \
export_first_match "$DB" 'Annual.*Math'                              "${OUT_DIR}/annual_em_math.csv" || \
export_first_match "$DB" 'Math.*Annual'                              "${OUT_DIR}/annual_em_math.csv" || true
fi


# -------------------------------------------
shopt -s nullglob
found=0
for DB in "${SRC_ROOT}"/SRC*/**/*.mdb "${SRC_ROOT}"/SRC*/**/*.accdb "${SRC_ROOT}"/SRC*/*.{mdb,accdb}; do
  [ -e "$DB" ] || continue
  found=1
  YEAR_DIR="$(dirname "$DB")"
  YEAR_BASE="$(basename "$YEAR_DIR")"
  OUT_DIR="${OUT_ROOT}/${YEAR_BASE}"
  mkdir -p "${OUT_DIR}"

  echo ">> Extracting from: $DB"
    {
      # Attendance (older: "Attendance and Suspensions"; newer: "ACC EM Chronic Absenteeism")
	  export_first_match "$DB" 'ACC.*Chronic|Chronic.*Abs|Attendance.*Suspensions' \
		"${OUT_DIR}/acc_em_chronic_absenteeism.csv"
	
	  # ELA (older: per-grade tables; newer: single "Annual EM ELA")
	  export_union_matches "$DB" '^ELA[3-8] Subgroup Results' "${OUT_DIR}/annual_em_ela.csv" \
		|| export_first_match "$DB" 'Annual.*ELA' "${OUT_DIR}/annual_em_ela.csv"
	
	  # Math (older: per-grade tables; newer: single "Annual EM Math")
	  export_union_matches "$DB" '^Math[3-8] Subgroup Results' "${OUT_DIR}/annual_em_math.csv" \
		|| export_first_match "$DB" 'Annual.*Math' "${OUT_DIR}/annual_em_math.csv"
	
	  # Org (same across years)
	  export_first_match "$DB" 'BOCES.*N.?/?.?RC|N.?RC|BOCES.*NRC' \
		"${OUT_DIR}/boces_n_rc.csv"
    
  } || {
    echo "WARN: extraction encountered an error for $DB (continuing)"
  }
done

if [ "$found" -eq 0 ]; then
  echo "No .mdb/.accdb found under ${SRC_ROOT}/SRC*/"
  exit 1
fi

echo "OK: CSVs written under ${OUT_ROOT}/SRCYYYY/*.csv"
