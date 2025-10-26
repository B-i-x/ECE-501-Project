# ECE 501C Final Project – Enrollment → Attendance → Achievement

**Stack:** Python + SQLite.  
**Goal:** Quantify how enrollment mix (subgroups) and attendance relate to G3–8 ELA/Math achievement (NYSED data).  
**Design:** 3NF core schema + summary (materialized-view-like) table; compare two baselines vs optimized design.

## Layout
- `sql/`         – schema (DDL), indexes, summary refresh SQL
- `baseline1/`   – single-wide-table loader + same queries
- `baseline2/`   – normalized loader + same queries (no indexes)
- `design/`      – indexes, WAL, summary refresh
- `experiments/` – timing harness, size-up generator, correctness checks
- `raw_data/`    – CSVs (not tracked)
- `data/`        – SQLite db files (ignored)
- `figs/`        – plots
- `plans/`       – EXPLAIN plans
- `docs/`        – data dictionary, ERD, report drafts


final-project/
├── baseline1/
│   ├── wide_schema.sql
│   └── queries/
├── baseline2/
│   ├── loader.sql
│   └── queries/
├── design/
│   ├── indexes.sql
│   ├── summary.sql
│   ├── refresh_test.py
│   └── timing_results.csv
├── experiments/
│   ├── time_queries.py
│   ├── load_sample_year.py
│   ├── correctness_check.py
│   └── sizeup_test.py
├── sql/
│   └── schema.sql
├── data/
├── raw_data/
├── docs/
│   ├── data_dictionary.md
│   └── ERD.png
├── figs/
├── plans/
├── requirements.txt
├── environment.yml
└── .gitignore


## Setup
### Option 1: Conda (recommended)
```python
# Create and activate the environment
conda env create -f environment.yml
conda activate ece501-final
```

If you do not yet have an `environment.yml` file, you can create the environment manually:
```python
conda create -n ece501-final python=3.11
conda activate ece501-final
pip install -r requirements.txt
```


### Option 2: Python venv
```python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```


## Quick start
1) `python experiments/init_db.py` to create DB files
2) `python experiments/load_sample_year.py --year 2023`
3) `python experiments/time_queries.py` to produce P50/P95 numbers
