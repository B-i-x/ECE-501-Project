# Rerunning the Pipeline

This document explains how to rerun the pipeline to ensure you're using only data from specific source folders (e.g., SRC2024).

## Quick Rerun (SRC2024 Only)

To rerun with only SRC2024 data:

### 1. Delete Generated Files

Delete the following to start fresh:

```bash
# Delete the database (removes all star schema and staging tables)
rm -f db/nysed.sqlite db/nysed.sqlite-shm db/nysed.sqlite-wal

# Delete intermediate CSVs (optional - only if you want to re-extract)
rm -rf data_work/SRC2024
```

**Note**: If you only want to rebuild the star schema from existing CSVs, you can skip deleting `data_work/SRC2024/`.

### 2. Run the Pipeline

**Option A: Full pipeline (extract → star schema)**
```bash
python scripts/run_pipeline.py
```

**Option B: Skip extraction (if CSVs already exist)**
```bash
python scripts/run_pipeline.py --skip-extract --skip-fixcsv
```

**Option C: Manual step-by-step**
```bash
# 1. Extract (if needed)
python scripts/extract_src.py

# 2. Fix CSV headers (if needed)
python scripts/fixcsv_headers.py

# 3. Import CSVs (defaults to SRC2024 only)
python scripts/import_csv_to_sqlite.py

# 4. Load map_subgroups (if you've updated the CSV)
python scripts/load_map_subgroups.py

# 5. Build star schema
python etl/run_sql.py
# Note: sql/03_indexes.sql is already included in etl/run_sql.py, so the line below is optional/redundant
# sqlite3 db/nysed.sqlite < sql/03_indexes.sql
```

## What Gets Deleted vs. Preserved

### Files to Delete for Clean Rerun:
- `db/nysed.sqlite*` - Database file and WAL files
- `data_work/SRC2024/` - Intermediate CSVs (optional, only if re-extracting)

### Files to Keep:
- `data_raw/SRC2024/` - Original source files (never delete)
- `etl/map_subgroups.csv` - Subgroup mapping dictionary
- All SQL scripts in `sql/`
- All Python scripts in `scripts/`

## Partial Rerun (Rebuild Star Schema Only)

If you've updated `map_subgroups.csv` or modified SQL scripts, you can rebuild just the star schema:

```bash
# 1. Load updated subgroup mappings
python scripts/load_map_subgroups.py

# 2. Rebuild staging and star schema
sqlite3 db/nysed.sqlite < sql/09_staging_persistent.sql
python etl/run_sql.py
```

## Troubleshooting

**Problem**: Database locked or WAL file issues
```bash
# Close any connections, then:
rm -f db/nysed.sqlite-shm db/nysed.sqlite-wal
```

**Problem**: Want to verify what data is in the database
```bash
sqlite3 db/nysed.sqlite "SELECT DISTINCT year_key FROM dim_year ORDER BY year_key;"
sqlite3 db/nysed.sqlite "SELECT COUNT(*) FROM fact_enrollment;"
```

