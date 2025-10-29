# NYSED Pipeline Workflow (Cross-Platform, WIP)

## 0) Repository layout (key paths)
```
final-project/
  data_raw/              # SRCYYYY/*.mdb|*.accdb  (NOT in git)
  data_work/             # extracted CSVs         (NOT in git)
  db/nysed.sqlite        # output DB              (NOT in git)
  scripts/
    run_pipeline.py
    extract_src.py
    fixcsv_headers.py
    import_csv_to_sqlite.py
  sql/
    09_staging_persistent.sql
    00_schema.sql
    10_load_enrollment.sql
    11_load_attendance.sql
    12_load_assessment.sql
  tests/
    test_fk_violations.sql
    test_rates_range.sql
    test_rowcounts.sql
  docs/
    WORKFLOW.md
```

## 1) Environment setup

### All platforms (Conda)
```bash
conda env create -f environment.yml
conda activate ece501-final
```

### Windows
- Install [Microsoft Access Database Engine 2016 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=54920)
- Verify the ODBC driver exists: `Microsoft Access Driver (*.mdb, *.accdb)`

### macOS
```bash
brew install mdbtools
```

### Linux
```bash
sudo apt update
sudo apt install mdbtools
```

## 2) Data placement

```
final-project/data_raw/SRC2015/*.mdb|*.accdb
...
final-project/data_raw/SRC2024/*.mdb|*.accdb
```

Download all NYSED Report Card databases from https://data.nysed.gov/downloads.php
Unzip into appropriate directories.

## 3) One-command run
```bash
python final-project/scripts/run_pipeline.py
```

## 4) Verifying run
```bash
sqlite3 final-project/db/nysed.sqlite "SELECT count(*) FROM fact_enrollment;"
```
