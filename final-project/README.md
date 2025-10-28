# NYSED Educational Data Warehouse — ECE 501 Final Project

This project builds a **SQLite star schema** on top of the **New York State Education Department (NYSED) Report Card Databases** (2015–2024).  
The goal is to quantify how **enrollment mix (student subgroups)** and **attendance** relate to **academic achievement** in Grades 3–8 **ELA and Math** across New York schools and districts.

---

## Objectives

- Integrate NYSED annual Report Card databases into a unified SQLite warehouse.
- Design a **star schema** for reproducible, performant educational analytics.
- Support cross-year analysis of subgroup composition, attendance, and proficiency.
- Provide scripts for extraction, cleaning, loading, and validation.
- Compare baselines (wide vs normalized) and measure query performance.

---

## Project Structure

```
final-project/
├── data_raw/                     # Raw downloaded .mdb/.accdb files (NYSED SRC2015–SRC2024)
├── data_work/                    # Intermediate CSVs extracted from Access DBs
├── db/
│   └── nysed.sqlite              # SQLite database (generated)
│
├── sql/                          # SQL pipeline: schema → seed → load → refresh → QA
│   ├── 00_schema.sql             # Star schema (dimensions + facts + indexes)
│   ├── 01_seed_dims.sql          # Populate subjects, grades, and years
│   ├── 02_upsert_orgs.sql        # Populate districts and schools from staging
│   ├── 09_staging.sql            # Build staging tables from raw normalized tables
│   ├── 10_load_enrollment.sql    # Load enrollment facts
│   ├── 11_load_attendance.sql    # Load attendance facts
│   ├── 12_load_assessment.sql    # Load assessment facts (ELA + Math)
│   ├── 20_refresh_summary.sql    # Create materialized summary views for analysis
│   └── 99_checks.sql             # Quality-assurance (FKs, ranges, rowcounts)
│
├── scripts/                      # Utility shell scripts for data processing
│   ├── extract_src.sh            # Extracts key tables from .mdb/.accdb using mdbtools
│   ├── import_csv_to_sqlite.sh   # Imports CSVs into SQLite normalized tables
│   ├── build_star.sh             # Optional: orchestrates SQL build manually
│   ├── refresh_summary.sh        # Optional: refreshes summary
│   ├── bench.sh                  # Optional: runs timing tests
│   └── vacuum_analyze.sh         # Optional: vacuum/optimize step
│
├── etl/                          # Python ETL scripts
│   ├── extract_report_card.py    # Optional future automation
│   ├── clean_standardize.py      # Cleans CSVs, normalizes subgroup labels
│   ├── run_sql.py                # Runs sequential SQL pipeline
│   └── map_subgroups.csv         # Maps raw subgroup names → canonical IDs
│
├── baselines/                    # For comparison with alternative schemas
│   ├── baseline1_wide/           # Denormalized (flat) schema
│   └── baseline2_normalized/     # Partially normalized schema
│
├── design/
│   ├── index_plan.md             # Documentation of indexing and PRAGMA tuning
│   ├── queries/                  # Benchmark queries
│   └── explain_plans.json        # Query plan capture (optional)
│
├── experiments/                  # Scripts for timing and correctness tests
│   ├── config.py
│   ├── time_queries.py
│   ├── sizeup_test.py
│   └── correctness_check.py
│
├── docs/
│   ├── ERD.dbml                  # Source for ER diagram (open in dbdiagram.io)
│   ├── ERD.png                   # Exported ER diagram image
│   ├── data_dictionary.md        # Column-level documentation
│   ├── index_plan.md             # Index rationale and performance notes
│   └── experiments_plan.md       # Plan for baseline and design experiments
│
├── figs/                         # Output CSVs and plots
│
├── Makefile                      # Main orchestration for build, refresh, QA, and bench
├── environment.yml               # Conda environment dependencies
└── README.md                     # Project overview (this file)
```

---

## Star Schema Overview

### Dimensions
| Table | Key | Description |
|--------|-----|-------------|
| dim_year | year_key | Reporting year (e.g., 2024) |
| dim_district | district_key | District identifiers and attributes |
| dim_school | school_key | School identifiers linked to districts |
| dim_subject | subject_key | Academic subject (ELA, Math) |
| dim_grade | grade_key | Grades 3–8 and “All” category |
| dim_subgroup | subgroup_key | Student subgroups (gender, race/ethnicity, program, etc.) |

### Facts
| Table | Grain | Metrics |
|--------|--------|---------|
| fact_enrollment | Year × School × Subgroup | Student counts |
| fact_attendance | Year × School × Subgroup | Absence counts, rates, and flags |
| fact_assessment | Year × School × Subject × Grade × Subgroup | Tested counts, proficiency counts, proficiency rates |

A materialized summary table in 20_refresh_summary.sql precomputes key aggregates (e.g., chronic absence vs. proficiency).

---

## Makefile Targets

| Command | Description |
|----------|--------------|
| make extract | Extracts key tables from .mdb/.accdb files using mdbtools |
| make import | Imports all CSVs into normalized raw tables in db/nysed.sqlite |
| make build | Runs full pipeline (extract → import → staging → load → index → summary) |
| make refresh | Refreshes materialized summary views |
| make checks | Executes QA checks (rates in range, FKs, rowcounts) |
| make bench | Runs benchmark query timing |
| make indexes | Applies index and PRAGMA tuning |
| make exports | Exports summary CSVs to figs/ |
| make vacuum | Runs VACUUM and ANALYZE for optimization |
| make tests | Executes simple SQL test scripts in tests/ |

---

## How to Work with the Project

### Setting up
1. Download NYSED Report Card databases (2015–2024) from data.nysed.gov.  
2. Place each year’s .mdb or .accdb inside:
   ```
   data_raw/SRC2016/
   data_raw/SRC2017/
   ...
   data_raw/SRC2024/
   ```

### Building the Database
After downloads complete:
```bash
make build
```
This will:
- Extract 4 key tables per year  
- Import them into normalized staging tables  
- Build all dimensions and facts  
- Generate db/nysed.sqlite

### Quality Assurance
Run:
```bash
make checks
```
to validate foreign keys, rate ranges, and row counts.

### ER Diagram
Open docs/ERD.dbml in dbdiagram.io to visualize the schema.  
Export to PNG and include in reports or presentations.

---

## Deliverables

- **Mid-Progress Report:** schema design, ETL progress, and partial QA results  
- **Final Report:** experiments on performance, completeness, and analytical findings  
- **ER Diagram:** in docs/ERD.dbml and docs/ERD.png  
- **SQLite Database:** generated as db/nysed.sqlite (excluded from Git)

---

_Developed by Group 5 — ECE 501: Data Management Systems_  
_University of Arizona, Fall 2025_
