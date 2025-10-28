# Workflow Cross-Platform

## macOS/Linux (needs mdbtools):
python3 scripts/extract_src.py

macOS/Linux extraction needs mdbtools:
```shell
brew install mdbtools (mac) or apt-get install mdbtools (Linux)
```

## Windows (no WSL; needs Access Database Engine + pyodbc):
py -3 scripts\extract_src.py


### Windows prerequisites

Install “Microsoft Access Database Engine (2016 or 2010)”.
```powershell
pip install pyodbc
```

If your driver name differs, set an env var:
```powershell
setx ACCESS_ODBC_DRIVER "Microsoft Access Driver (*.mdb, *.accdb)"
```




## 1) Extract: Access (.mdb/.accdb) -> CSV (auto-detects table names)
python scripts/extract_src.py

## 2) Normalize CSV headers (first line only; safe)
python scripts/fixcsv_headers.py

## 3) Import all CSVs into the 4 raw tables (union across years)
python scripts/import_csv_to_sqlite.py

## 4) Build staging tables (persistent st_* tables)
sqlite3 db/nysed.sqlite < sql/09_staging_persistent.sql

## 5) Build star schema + load facts
sqlite3 db/nysed.sqlite < sql/00_schema.sql
sqlite3 db/nysed.sqlite < sql/10_load_enrollment.sql
sqlite3 db/nysed.sqlite < sql/11_load_attendance.sql
sqlite3 db/nysed.sqlite < sql/12_load_assessment.sql

## 6) Quick checks
sqlite3 db/nysed.sqlite "SELECT 'enrollment', COUNT(*) FROM fact_enrollment;"
sqlite3 db/nysed.sqlite "SELECT 'attendance', COUNT(*) FROM fact_attendance;"
sqlite3 db/nysed.sqlite "SELECT 'assessment', COUNT(*) FROM fact_assessment;"



# (optional) clean extracted CSVs
rm -rf data_work/*

# run everything end-to-end
python scripts/run_pipeline.py

# run a subset (example: after CSVs are ready)
python scripts/run_pipeline.py --only fixcsv,import,staging,star,load,checks

# skip extract if you already have CSVs
python scripts/run_pipeline.py --skip-extract
