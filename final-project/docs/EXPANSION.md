# Expanding to Multiple Years

This document explains how to expand the pipeline to process data from multiple SRC* folders (e.g., SRC2015 through SRC2024).

## Current Setup (SRC2024 Only)

By default, the pipeline processes only data from `data_work/SRC2024/`:

- **Import script**: `scripts/import_csv_to_sqlite.py` defaults to SRC2024 only
- **Staging script**: `sql/09_staging_persistent.sql` processes all data in imported tables (no YEAR filter)

## Expanding to All Years

### Step 1: Extract Data from All Years

Ensure you have extracted CSVs for all desired years:

```bash
# Extract from all SRC* folders in data_raw/
python scripts/extract_src.py

# This creates:
#   data_work/SRC2015/*.csv
#   data_work/SRC2016/*.csv
#   ...
#   data_work/SRC2024/*.csv
```

### Step 2: Import All Years

**Python script:**
```bash
python scripts/import_csv_to_sqlite.py --all-years
```

**Shell script:**
```bash
ALL_YEARS=1 scripts/import_csv_to_sqlite.sh
```

**Makefile:**
```bash
make import  # (if Makefile is updated to support --all-years)
```

This will import CSVs from all `SRC*` folders into the raw SQLite tables, unioning across years.

### Step 3: Rebuild Star Schema

The staging script (`sql/09_staging_persistent.sql`) already processes all data in the imported tables, so no changes are needed:

```bash
# Rebuild staging and star schema with all years
sqlite3 db/nysed.sqlite < sql/09_staging_persistent.sql
python etl/run_sql.py
sqlite3 db/nysed.sqlite < sql/03_indexes.sql
```

Or use the full pipeline (skip extract/fixcsv if already done):
```bash
python scripts/run_pipeline.py --skip-extract --skip-fixcsv --all-years
```

**Note**: You'll need to update `run_pipeline.py` to pass `--all-years` to the import step, or modify it to support this flag.

### Step 4: Verify Multi-Year Data

```bash
# Check which years are in the database
sqlite3 db/nysed.sqlite "SELECT DISTINCT year_key FROM dim_year ORDER BY year_key;"

# Check row counts by year
sqlite3 db/nysed.sqlite "SELECT year_key, COUNT(*) FROM fact_enrollment GROUP BY year_key ORDER BY year_key;"
```

## Important Notes

### Year Column vs. Folder Name

**Critical**: The `YEAR` column in the data may not match the folder name. For example:
- `data_work/SRC2024/` may contain data with `YEAR='2023'` (reporting year)
- The folder name indicates the **release year**, not necessarily the **data year**

The staging script (`09_staging_persistent.sql`) does **not** filter by YEAR column - it processes all data that was imported. Filtering happens at import time based on which folders you choose to import.

### Staging Script Behavior

The staging script processes **all rows** in the imported raw tables:
- `st_years` contains all distinct YEAR values from imported data
- `st_attendance_em_num` contains all attendance records
- `st_assessment_em_num` contains all assessment records
- `st_org` contains all organization records

If you want to filter to specific years in the staging script, you would add `WHERE YEAR IN ('2023', '2024')` clauses, but this is generally not recommended since the folder-based filtering at import time is more reliable.

### Performance Considerations

- Importing all years will create larger raw tables
- Star schema build time will increase
- Consider adding indexes (already in `sql/03_indexes.sql`)
- May want to run `VACUUM ANALYZE` after loading all years

### Rolling Back to Single Year

To go back to SRC2024 only:

1. Delete the database: `rm -f db/nysed.sqlite*`
2. Re-import with default (SRC2024 only): `python scripts/import_csv_to_sqlite.py`
3. Rebuild star schema: `python etl/run_sql.py`

## Future Enhancements

Potential improvements for multi-year support:

1. **Year range filtering**: Add `--years 2020,2021,2022` flag to import specific years
2. **Incremental loading**: Add logic to append new years without re-importing all data
3. **Year validation**: Add checks to ensure YEAR column values are reasonable
4. **Partitioning**: Consider partitioning fact tables by year for better performance

