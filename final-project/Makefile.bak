PY ?= python
SQLITE ?= sqlite3
DB := db/nysed.sqlite

.PHONY: help build extract import refresh bench checks indexes views exports vacuum tests

help:
	@echo "Targets:"
	@echo "  make build    - extract+import SRC .mdb/.accdb, build star schema, seed, load, indexes, summary"
	@echo "  make extract  - export needed tables from .mdb/.accdb to data_work/SRCYYYY/*.csv"
	@echo "  make import   - import CSVs into raw SQLite tables (acc_em_chronic_absenteeism, annual_em_ela, annual_em_math, boces_n_rc)"
	@echo "  make refresh  - refresh materialized summary only"
	@echo "  make bench    - run timing experiments"
	@echo "  make checks   - run QA checks"
	@echo "  make indexes  - apply index & PRAGMA tuning"
	@echo "  make views    - (re)create convenience views"
	@echo "  make exports  - export CSVs for figures"
	@echo "  make vacuum   - VACUUM/ANALYZE/optimize"
	@echo "  make tests    - run simple SQL sanity tests"

build: extract import
	$(PY) etl/run_sql.py
	$(SQLITE) $(DB) < sql/03_indexes.sql
	@echo "Build complete."

extract:
	scripts/extract_src.sh

import:
	scripts/import_csv_to_sqlite.sh

refresh:
	$(SQLITE) $(DB) < sql/20_refresh_summary.sql
	@echo "Summary refreshed."

bench:
	$(PY) experiments/time_queries.py

checks:
	scripts/checks.sh

indexes:
	$(SQLITE) $(DB) < sql/03_indexes.sql

views:
	$(SQLITE) $(DB) < sql/30_views.sql

exports:
	$(SQLITE) -header -csv $(DB) < sql/40_exports.sql > figs/abs_vs_prof.csv
	@echo "Exported figs/abs_vs_prof.csv"

vacuum:
	scripts/vacuum_analyze.sh

tests:
	$(SQLITE) $(DB) < tests/test_fk_violations.sql
	$(SQLITE) $(DB) < tests/test_rates_range.sql
	$(SQLITE) $(DB) < tests/test_rowcounts.sql
