#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="${ROOT}/db/nysed.sqlite"
CSV_ROOT="${ROOT}/data_work"

# Normalized SQLite table names we will import into:
#   acc_em_chronic_absenteeism, annual_em_ela, annual_em_math, boces_n_rc
# These correspond to CSVs created in extract step:
#   acc_em_chronic_absenteeism.csv, annual_em_ela.csv, annual_em_math.csv, boces_n_rc.csv

sqlite3 "$DB" <<'SQL'
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

DROP TABLE IF EXISTS acc_em_chronic_absenteeism;
DROP TABLE IF EXISTS annual_em_ela;
DROP TABLE IF EXISTS annual_em_math;
DROP TABLE IF EXISTS boces_n_rc;

-- Create simple raw tables. Column types will be inferred by SQLite on import.
CREATE TABLE acc_em_chronic_absenteeism AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
CREATE TABLE annual_em_ela               AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
CREATE TABLE annual_em_math              AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
CREATE TABLE boces_n_rc                  AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
SQL

# Function to import a CSV into a target table (overwrites schema to match CSV header)
import_csv() {
  local csv="$1"
  local table="$2"
  local db="$3"
  # Create a temp table from header then import
  sqlite3 "$db" <<SQL
.mode csv
.import --skip 0 "$csv" "$table"
SQL
}

# Find the newest SRCYYYY folder (or loop all)
shopt -s nullglob
folders=( "${CSV_ROOT}"/SRC* )
if [ ${#folders[@]} -eq 0 ]; then
  echo "No CSV folders under ${CSV_ROOT}/SRC*/. Run scripts/extract_src.sh first."
  exit 1
fi

# Loop all SRC-year folders and append (UNION ALL-style): we import each year into a temp then INSERT
for FOLDER in "${folders[@]}"; do
  echo ">> Importing CSVs from ${FOLDER}"
  # Build paths (some may be missing if export failed)
  A="${FOLDER}/acc_em_chronic_absenteeism.csv"
  E="${FOLDER}/annual_em_ela.csv"
  M="${FOLDER}/annual_em_math.csv"
  B="${FOLDER}/boces_n_rc.csv"

  # For each file: create a temp table, import; if main table is empty, rename; else append columns aligned by name
  for pair in "A:acc_em_chronic_absenteeism" "E:annual_em_ela" "M:annual_em_math" "B:boces_n_rc"; do
    key="${pair%%:*}"
    tbl="${pair##*:}"
    f=""
    case "$key" in
      A) f="$A";;
      E) f="$E";;
      M) f="$M";;
      B) f="$B";;
    esac
    [ -f "$f" ] || { echo "   - skip missing $f"; continue; }
    echo "   - importing $f -> $tbl"
    sqlite3 "$DB" <<SQL
.mode csv
.import --skip 0 "$f" __tmp_${tbl}
-- On first folder, target table is empty (created with 0 rows). We need to align columns and append.
-- Create aligned insert after discovering common columns by PRAGMA table_info (done in SQL below).
SQL

    # Build a column list intersection using sqlite PRAGMA via a shell call
    common_cols=$(sqlite3 "$DB" "
      WITH
      src AS (SELECT name FROM pragma_table_info('__tmp_${tbl}') ORDER BY cid),
      dst AS (SELECT name FROM pragma_table_info('${tbl}')        ORDER BY cid)
      SELECT group_concat(src.name, ',')
      FROM src JOIN dst USING(name);
    ")
    if [ -z "$common_cols" ]; then
      # First time: replace empty shell table with imported temp
      sqlite3 "$DB" "DROP TABLE ${tbl}; ALTER TABLE __tmp_${tbl} RENAME TO ${tbl};"
    else
      # Append matching columns
      sqlite3 "$DB" "INSERT INTO ${tbl} (${common_cols}) SELECT ${common_cols} FROM __tmp_${tbl}; DROP TABLE __tmp_${tbl};"
    fi
  done
done

echo "OK: Imported raw tables into ${DB}: acc_em_chronic_absenteeism, annual_em_ela, annual_em_math, boces_n_rc"
