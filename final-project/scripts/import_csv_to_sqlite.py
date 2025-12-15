#!/usr/bin/env python3
"""
Import CSVs under data_work/SRCYYYY/ into SQLite raw tables:
  acc_em_chronic_absenteeism, annual_em_ela, annual_em_math, boces_n_rc, expenditures_per_pupil

By default, imports only SRC2024. Use --all-years to import all SRC* folders.
Union across years by aligning on common column names.
Works on Windows/macOS/Linux with Python's sqlite3.
"""
import sqlite3, csv, pathlib, argparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB   = ROOT / "db" / "nysed.db"
CSV_ROOT = ROOT / "data_work"

TABLES = [
    "acc_em_chronic_absenteeism",
    "annual_em_ela",
    "annual_em_math",
    "boces_n_rc",
    "expenditures_per_pupil",
]

def ensure_empty_shells(con: sqlite3.Connection):
    cur = con.cursor()
    cur.executescript("""
    PRAGMA journal_mode=WAL;
    PRAGMA foreign_keys=ON;

    DROP TABLE IF EXISTS acc_em_chronic_absenteeism;
    DROP TABLE IF EXISTS annual_em_ela;
    DROP TABLE IF EXISTS annual_em_math;
    DROP TABLE IF EXISTS boces_n_rc;
    DROP TABLE IF EXISTS expenditures_per_pupil;

    CREATE TABLE acc_em_chronic_absenteeism AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
    CREATE TABLE annual_em_ela               AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
    CREATE TABLE annual_em_math              AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
    CREATE TABLE boces_n_rc                  AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
    CREATE TABLE expenditures_per_pupil      AS SELECT * FROM (SELECT 1 AS dummy) WHERE 0;
    """)
    con.commit()

def read_header(csv_path: pathlib.Path):
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        row = next(reader, None)
        return row or []

def create_temp_from_csv(con: sqlite3.Connection, csv_path: pathlib.Path, temp_name: str):
    headers = read_header(csv_path)
    if not headers:
        return False
    # simple TEXT columns; types not needed for staging/raw
    cols_sql = ", ".join([f'"{h}" TEXT' for h in headers])
    con.execute(f'DROP TABLE IF EXISTS "{temp_name}"')
    con.execute(f'CREATE TABLE "{temp_name}" ({cols_sql})')

    # bulk insert
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = [tuple(r.get(h, None) for h in headers) for r in reader]
    if rows:
        placeholders = ", ".join(["?"] * len(headers))
        con.executemany(f'INSERT INTO "{temp_name}" VALUES ({placeholders})', rows)
    con.commit()
    return True

def common_cols(con: sqlite3.Connection, temp_name: str, target: str):
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info('{temp_name}')")
    src_cols = [r[1] for r in cur.fetchall()]
    cur.execute(f"PRAGMA table_info('{target}')")
    dst_cols = [r[1] for r in cur.fetchall()]
    return [c for c in src_cols if c in dst_cols]

def import_one_file(con: sqlite3.Connection, csv_path: pathlib.Path, target: str):
    tmp = f"__tmp_{target}"
    if not create_temp_from_csv(con, csv_path, tmp):
        print(f"   - skip empty {csv_path.name}")
        return
    cols = common_cols(con, tmp, target)
    if not cols:
        # first time: replace shell with temp
        con.execute(f'DROP TABLE "{target}"')
        con.execute(f'ALTER TABLE "{tmp}" RENAME TO "{target}"')
    else:
        col_list = ", ".join([f'"{c}"' for c in cols])
        con.execute(f'INSERT INTO "{target}" ({col_list}) SELECT {col_list} FROM "{tmp}"')
        con.execute(f'DROP TABLE "{tmp}"')
    con.commit()

def main():
    parser = argparse.ArgumentParser(description="Import CSVs into SQLite raw tables")
    parser.add_argument("--all-years", action="store_true",
                       help="Import all SRC* folders (default: only SRC2024)")
    args = parser.parse_args()

    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB.as_posix())
    ensure_empty_shells(con)

    if args.all_years:
        year_dirs = sorted(p for p in CSV_ROOT.glob("SRC*") if p.is_dir())
        print(f"Importing from all year folders: {[d.name for d in year_dirs]}")
    else:
        year_dirs = [CSV_ROOT / "SRC2024"]
        print(f"Importing from SRC2024 only (use --all-years to import all years)")

    if not year_dirs or not any(d.exists() for d in year_dirs):
        print(f"No CSV folders found. Expected: {[str(d) for d in year_dirs]}")
        print(f"Run extract + fixcsv first.")
        return

    for d in year_dirs:
        if not d.exists():
            print(f"   - skip missing {d.name}")
            continue
        print(f">> Importing CSVs from {d}")
        pairs = [
            (d / "acc_em_chronic_absenteeism.csv", "acc_em_chronic_absenteeism"),
            (d / "annual_em_ela.csv", "annual_em_ela"),
            (d / "annual_em_math.csv", "annual_em_math"),
            (d / "boces_n_rc.csv", "boces_n_rc"),
            (d / "expenditures_per_pupil.csv", "expenditures_per_pupil"),
        ]
        for path, table in pairs:
            if path.exists():
                print(f"   - {path.name} -> {table}")
                import_one_file(con, path, table)
            else:
                print(f"   - skip missing {path.name}")
    con.close()
    print(f"✅ OK: Imported raw tables into {DB}")

if __name__ == "__main__":
    main()
