# NYSED Educational Data Warehouse — ECE 501 Final Project

This project builds a **SQLite data warehouse** from the **New York State Education Department (NYSED) Report Card Databases (2015–2024)**.  
It integrates multiple Access databases into a unified **star schema** that supports analysis of **enrollment composition**, **attendance**, and **academic achievement** (Grades 3–8 ELA and Math).

---

## Project Objectives

- Extract and standardize NYSED annual report card datasets (.mdb/.accdb)
- Build a **reproducible star schema** using SQLite
- Enable cross-year analysis of subgroups, attendance, and proficiency
- Compare baseline designs (wide vs normalized) for performance
- Validate data quality and consistency across years

---

## Project Structure (as of 10-27-2025)

```
final-project/
├── 68fecfeb5787c7dcef34728b/        # Linked Overleaf project (mid-semester report)
│   └── mid-sem-report/
│       ├── main.tex
│       ├── figs/, docs/, sql/ ...
│       └── mid-JuleenAdams...pdf
│
├── baselines/                       # Reference schemas for comparison
│   ├── baseline1_wide/
│   └── baseline2_normalized/
│
├── data_raw/                        # Original NYSED Report Card databases (.mdb/.accdb)
├── data_work/                       # Extracted CSVs (intermediate, not tracked)
├── db/                              # SQLite output files (not tracked)
│
├── docs/                            # Documentation and supporting files
│   ├── ERD.dbml, ERD_export.sql
│   ├── data_dictionary.md
│   ├── BUILD.md, WORKFLOW.md
│   ├── experiments_plan.md
│   └── queries_baselines.md
│
├── design/                          # Design notes and index/plan analysis
│   ├── index_plan.md
│   └── queries/
│
├── etl/                             # ETL modules (Python)
│   ├── extract_report_card.py
│   ├── clean_standardize.py
│   ├── map_subgroups.csv
│   └── run_sql.py
│
├── experiments/                     # Benchmark and correctness testing
│   ├── config.py
│   ├── time_queries.py
│   ├── sizeup_test.py
│   ├── correctness_check.py
│   └── load_sample_year.py
│
├── scripts/                         # Cross-platform pipeline scripts
│   ├── extract_src.py / extract_src.sh
│   ├── fixcsv_headers.py / fixcsv_headers.sh
│   ├── import_csv_to_sqlite.py / import_csv_to_sqlite.sh
│   ├── run_pipeline.py              # One-command ETL pipeline (primary workflow)
│   ├── build_star.sh, checks.sh
│   ├── refresh_summary.sh, bench.sh
│   └── vacuum_analyze.sh
│
├── sql/                             # SQL definitions for schema + pipeline
│   ├── 00_schema.sql → 12_load_assessment.sql
│   ├── 20_refresh_summary.sql
│   ├── 30_views.sql → 99_checks.sql
│   └── analysis, cleanup, and staging SQL
│
├── tests/                           # SQL QA checks
│   ├── test_fk_violations.sql
│   ├── test_rates_range.sql
│   └── test_rowcounts.sql
│
├── figs/                            # Generated diagrams and figures
├── environment.yml                  # Conda environment (cross-platform)
├── Makefile                         # Optional (Mac/Linux convenience)
└── README.md                        # (this file)
```

---

## Star Schema Overview

| Table | Key | Description |
|--------|-----|-------------|
| **dim_year** | `year_key` | Reporting year (2015–2024) |
| **dim_district** | `district_key` | District identifiers & metadata |
| **dim_school** | `school_key` | School identifiers linked to districts |
| **dim_subject** | `subject_key` | ELA, Math |
| **dim_grade** | `grade_key` | Grades 3–8 and “All” category |
| **dim_subgroup** | `subgroup_key` | Demographic / program subgroups |

| Fact Table | Grain | Metrics |
|-------------|--------|----------|
| **fact_enrollment** | year × school × subgroup | student counts |
| **fact_attendance** | year × school × subgroup | absences, rates |
| **fact_assessment** | year × school × subject × grade × subgroup | proficiency metrics |

Materialized views in `20_refresh_summary.sql` combine key indicators for analysis and visualization.

---

## Workflow

See [`docs/WORKFLOW.md`](docs/WORKFLOW.md) for full details.  
Below is a summary of the pipeline from raw data to database.

### 1. Environment Setup
```bash
conda env create -f environment.yml
conda activate ece501-final
```

**Windows**
- Install [Microsoft Access Database Engine 2016 Redistributable](https://www.microsoft.com/en-us/download/details.aspx?id=54920)
- Verify the ODBC driver `Microsoft Access Driver (*.mdb, *.accdb)` is available.

**macOS**
```bash
brew install mdbtools
```

**Linux**
```bash
sudo apt update
sudo apt install mdbtools
```

---

### 2. Place Data
Download NYSED Report Card databases from  
<https://data.nysed.gov/downloads.php>

Store `.mdb` and `.accdb` files under `data_raw/SRCYYYY/` for each year.

---

### 3. Run the Cross-Platform ETL Pipeline
```bash
python scripts/run_pipeline.py
```

This script executes:
1. `extract_src.py` – Extracts and merges Access tables into CSVs  
2. `fixcsv_headers.py` – Cleans and standardizes header formats  
3. `import_csv_to_sqlite.py` – Loads cleaned CSVs into SQLite staging tables  
4. SQL stages to build facts, dimensions, and summaries

---

### 4. Validate the Build
```bash
python scripts/build.py --check
```
Or, to run SQL QA scripts:
```bash
sqlite3 db/nysed.sqlite < tests/test_fk_violations.sql
```

---

### **Alternative Workflow for macOS/Linux Users**

If you are on **macOS or Linux** and have `make` installed, you can use the Makefile as a **shortcut** to run the same steps as the Python workflow.
It’s not additional — it’s an *alternative* way to run Steps 3–4 from the main workflow.

| **Purpose**                        | **Python Command**                                                     | **Make Equivalent** | **Includes `fixcsv_headers.py`?** |
| ---------------------------------- | ---------------------------------------------------------------------- | ------------------- | --------------------------------- |
| Extract and normalize CSVs         | `python scripts/extract_src.py` and `python scripts/fixcsv_headers.py` | `make extract`      | Yes                             |
| Import CSVs into SQLite            | `python scripts/import_csv_to_sqlite.py`                               | `make import`       | —                                 |
| Build schema, facts, and summaries | `python scripts/run_pipeline.py`                                       | `make build`        | Yes (calls full pipeline)           |
| Validate database build            | `python scripts/build.py --check`                                      | `make checks`       | —                                 |
| Run benchmarks                     | `python scripts/time_queries.py`                                       | `make bench`        | —                                 |

> **Note:**
>
> * `make extract` automatically runs both CSV extraction and header normalization.
> * `make build` executes the full end-to-end pipeline (equivalent to `python scripts/run_pipeline.py`).
> * Windows users should use the Python workflow directly.

---

## Documentation and Reports

- Overleaf mid-semester report: `68fecfeb5787c7dcef34728b/mid-sem-report`
- ER Diagram: `docs/ERD.dbml` → export as `figs/star-schema.png`
- Data Dictionary: `docs/data_dictionary.md`
- Experiments Plan: `docs/experiments_plan.md`
- Workflow instructions: `docs/WORKFLOW.md`

---

## Authors

Group 5 — ECE 501: Data Management Systems  
University of Arizona — Fall 2025  
Contributors: Juleen Adams, Alex Romero, Kama Svoboda
