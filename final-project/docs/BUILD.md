# Build steps (from raw to figures)

1) Put original NYSED files in `data_raw/`
   - e.g., `enrollment_2024.csv`, `attendance_2024.csv`, `assessment_2024.csv`
2) Clean & standardize:
   python etl/clean_standardize.py

3) Build star schema + load + summary:
   python etl/run_sql.py
   sqlite3 db/nysed.sqlite < sql/03_indexes.sql

4) Run QA checks:
   scripts/checks.sh

5) Export analysis tables (optional):
   sqlite3 -header -csv db/nysed.sqlite < sql/40_exports.sql > figs/abs_vs_prof.csv

6) Vacuum/Analyze (optional):
   scripts/vacuum_analyze.sh
