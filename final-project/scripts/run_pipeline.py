#!/usr/bin/env python3
"""
End-to-end pipeline for NYSED SRC → star schema (cross-platform).

Steps (enabled by default; toggle with --skip-* flags):
  1) extract  : Access (.mdb/.accdb) → CSV (default: SRC2024 only; use --all-years in extract_src.py for all years)
  2) fixcsv   : normalize CSV headers (first line only)
  3) import   : CSVs → raw SQLite tables (default: SRC2024 only; use --all-years to import all years)
  4) map_subgroups : load subgroup mapping CSV into map_subgroups table
  5) staging  : build persistent st_* tables
  6) star     : create star schema (dims + facts empty)
  7) load     : populate facts (enrollment, attendance, assessment)
  8) indexes  : create indexes for performance
  9) checks   : run QA tests (if present)

Requires:
  - Python 3.x
  - Windows extraction: Microsoft Access Database Engine + `pip install pyodbc`
  - macOS/Linux extraction: mdbtools (mdb-tables, mdb-export)

Usage:
  python scripts/run_pipeline.py                # do everything
  python scripts/run_pipeline.py --skip-extract # if CSVs already exist
  python scripts/run_pipeline.py --only staging,star,load  # run just these steps
"""

import argparse
import os
import sys
import subprocess
import time
import pathlib
import sqlite3
from typing import List, Sequence

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB   = ROOT / "db" / "star_schema.db"

SQL_DIR = ROOT / "sql"
TESTS_DIR = ROOT / "tests"

SQL_STAGING = SQL_DIR / "09_staging_persistent.sql"
SQL_SCHEMA  = SQL_DIR / "00_schema.sql"
SQL_LOADS   = [SQL_DIR / "10_load_enrollment.sql",
               SQL_DIR / "11_load_attendance.sql",
               SQL_DIR / "12_load_assessment.sql"]
SQL_INDEXES = SQL_DIR / "03_indexes.sql"

TEST_FILES  = [TESTS_DIR / "test_fk_violations.sql",
               TESTS_DIR / "test_rates_range.sql",
               TESTS_DIR / "test_rowcounts.sql"]

EXTRACT_PY  = ROOT / "scripts" / "extract_src.py"
FIXCSV_PY   = ROOT / "scripts" / "fixcsv_headers.py"
IMPORT_PY   = ROOT / "scripts" / "import_csv_to_sqlite.py"
LOAD_MAP_SUBGROUPS_PY = ROOT / "scripts" / "load_map_subgroups.py"

def run_subprocess(cmd: Sequence[str], cwd: pathlib.Path | None = None) -> int:
    """Run a child process and stream output."""
    print(f"$ {' '.join(cmd)}")
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
    return proc.wait()

def run_python(script: pathlib.Path, args: Sequence[str] = ()) -> None:
    if not script.exists():
        raise FileNotFoundError(f"Missing script: {script}")
    rc = run_subprocess([sys.executable, str(script), *args], cwd=ROOT)
    if rc != 0:
        raise RuntimeError(f"{script.name} failed with exit code {rc}")

def read_sql(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")

def run_sql_file(con: sqlite3.Connection, path: pathlib.Path, label: str | None = None) -> None:
    if not path.exists():
        print(f"(!) Skipping missing SQL file: {path}")
        return
    t0 = time.perf_counter()
    print(f"==> {label or path.name}")
    sql = read_sql(path)
    con.executescript(sql)
    con.commit()
    dt = time.perf_counter() - t0
    print(f"    OK ({dt:0.2f}s)")

def run_tests(con: sqlite3.Connection, files: List[pathlib.Path]) -> None:
    for f in files:
        if not f.exists():
            print(f"(!) Skipping missing test file: {f}")
            continue
        print(f"==> TEST: {f.name}")
        # Execute each statement and print rows (works for simple SELECT assertions)
        sql = read_sql(f)
        cur = con.cursor()
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            try:
                cur.execute(stmt)
                rows = cur.fetchall()
                if rows:
                    for r in rows:
                        print("   ", "|".join(str(x) for x in r))
            except sqlite3.Error as e:
                print(f"   ERROR running statement: {stmt[:120]}... -> {e}")
        print("    OK")

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="NYSED pipeline runner")
    p.add_argument("--db", default=str(DB), help="Path to SQLite DB (default: db/star_schema.db)")
    # inclusive step control
    p.add_argument("--skip-extract", action="store_true")
    p.add_argument("--skip-fixcsv",  action="store_true")
    p.add_argument("--skip-import",  action="store_true")
    p.add_argument("--skip-map-subgroups", action="store_true")
    p.add_argument("--skip-staging", action="store_true")
    p.add_argument("--skip-star",    action="store_true")
    p.add_argument("--skip-load",    action="store_true")
    p.add_argument("--skip-indexes", action="store_true")
    p.add_argument("--skip-checks",  action="store_true")
    p.add_argument("--only", type=str, default="", 
                   help="Comma-separated subset of steps to run (e.g., 'staging,star,load'). Overrides skip flags.")
    return p.parse_args()

def should_run(step: str, args: argparse.Namespace, plan_only: set[str] | None) -> bool:
    if plan_only is not None:
        return step in plan_only
    flag_name = f"skip_{step}"
    return not getattr(args, flag_name, False)

def main() -> None:
    args = parse_args()
    db_path = pathlib.Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    plan_only = None
    if args.only:
        plan_only = {s.strip() for s in args.only.split(",") if s.strip()}

    steps = ["extract", "fixcsv", "import", "map_subgroups", "staging", "star", "load", "indexes", "checks"]
    print("Pipeline plan:", " -> ".join(s for s in steps if should_run(s, args, plan_only)))
    print()

    t_total = time.perf_counter()

    # 1) Extract
    if should_run("extract", args, plan_only):
        t0 = time.perf_counter()
        if not EXTRACT_PY.exists():
            raise FileNotFoundError(f"Missing {EXTRACT_PY}.")
        print("=== STEP 1/9: EXTRACT (.mdb/.accdb -> CSV)")
        run_python(EXTRACT_PY)
        print(f"=== EXTRACT done in {time.perf_counter()-t0:0.2f}s\n")

    # 2) Fix headers
    if should_run("fixcsv", args, plan_only):
        t0 = time.perf_counter()
        if not FIXCSV_PY.exists():
            raise FileNotFoundError(f"Missing {FIXCSV_PY}.")
        print("=== STEP 2/9: FIXCSV (normalize headers)")
        run_python(FIXCSV_PY)
        print(f"=== FIXCSV done in {time.perf_counter()-t0:0.2f}s\n")

    # 3) Import CSV -> raw tables
    if should_run("import", args, plan_only):
        t0 = time.perf_counter()
        if not IMPORT_PY.exists():
            raise FileNotFoundError(f"Missing {IMPORT_PY}.")
        print("=== STEP 3/9: IMPORT (CSVs -> raw tables)")
        run_python(IMPORT_PY)
        print(f"=== IMPORT done in {time.perf_counter()-t0:0.2f}s\n")

    # Open DB for SQL phases
    con = sqlite3.connect(db_path.as_posix())
    con.execute("PRAGMA foreign_keys=ON;")

    # 4) Load map_subgroups
    if should_run("map_subgroups", args, plan_only):
        t0 = time.perf_counter()
        if not LOAD_MAP_SUBGROUPS_PY.exists():
            print(f"(!) Skipping missing script: {LOAD_MAP_SUBGROUPS_PY}")
        else:
            print("=== STEP 4/9: MAP_SUBGROUPS (load subgroup mapping)")
            run_python(LOAD_MAP_SUBGROUPS_PY)
            print(f"=== MAP_SUBGROUPS done in {time.perf_counter()-t0:0.2f}s\n")

    # 5) Staging
    if should_run("staging", args, plan_only):
        print("=== STEP 5/9: STAGING (build persistent st_* tables)")
        run_sql_file(con, SQL_STAGING, label="09_staging_persistent.sql")
        print()

    # 6) Star schema
    if should_run("star", args, plan_only):
        print("=== STEP 6/9: STAR (create dims/facts)")
        run_sql_file(con, SQL_SCHEMA, label="00_schema.sql")
        print()

    # 7) Loads
    if should_run("load", args, plan_only):
        print("=== STEP 7/9: LOAD (facts)")
        for f in SQL_LOADS:
            run_sql_file(con, f)
        print()

    # 8) Indexes
    if should_run("indexes", args, plan_only):
        print("=== STEP 8/9: INDEXES (create indexes)")
        run_sql_file(con, SQL_INDEXES, label="03_indexes.sql")
        print()

    # 9) Checks
    if should_run("checks", args, plan_only):
        print("=== STEP 9/9: CHECKS (QA tests)")
        run_tests(con, TEST_FILES)
        print()

    con.close()
    print(f"Pipeline complete in {time.perf_counter()-t_total:0.2f}s")
    print(f"DB: {db_path}")

if __name__ == "__main__":
    main()
