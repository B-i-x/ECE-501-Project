#!/usr/bin/env python3
"""
Cross-platform extractor for NYSED SRC databases (.mdb/.accdb) -> CSVs.

- Windows: uses pyodbc with Microsoft Access ODBC driver (no WSL).
  Requires "Microsoft Access Database Engine" and `pip install pyodbc`.
- macOS/Linux: uses mdbtools (mdb-tables, mdb-export).

It auto-detects table names across years:
  - Attendance: "Attendance and Suspensions" or "ACC EM Chronic Absenteeism"
  - ELA: union ELA3..ELA8 Subgroup Results (older) OR fallback to "Annual ... ELA"
  - Math: union Math3..Math8 Subgroup Results (older) OR fallback to "Annual ... Math"
  - Orgs: "BOCES and N/RC" (variant patterns handled)

Outputs per year:
  data_work/SRCYYYY/acc_em_chronic_absenteeism.csv
  data_work/SRCYYYY/annual_em_ela.csv
  data_work/SRCYYYY/annual_em_math.csv
  data_work/SRCYYYY/boces_n_rc.csv
"""
import sys, os, re, csv, pathlib, platform, subprocess
from typing import List, Optional

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC_ROOT = REPO / "data_raw"
OUT_ROOT = REPO / "data_work"

ATTENDANCE_PAT = re.compile(r"(ACC.*Chronic|Chronic.*Abs|Attendance.*Suspensions)", re.I)
ELA_UNION_PAT  = re.compile(r"^ELA[3-8]\s+Subgroup\s+Results$", re.I)
MATH_UNION_PAT = re.compile(r"^Math[3-8]\s+Subgroup\s+Results$", re.I)
ELA_ANNUAL_PATS  = [re.compile(p, re.I) for p in [
    r"Annual\s+E\.?/?M\.?\s+ELA", r"Annual.*ELA", r"ELA.*Annual"
]]
MATH_ANNUAL_PATS = [re.compile(p, re.I) for p in [
    r"Annual\s+E\.?/?M\.?\s+Math", r"Annual.*Math", r"Math.*Annual"
]]
ORG_PAT        = re.compile(r"(BOCES.*N.?/?.?RC|N.?RC|BOCES.*NRC)", re.I)

def list_src_files() -> List[pathlib.Path]:
    patterns = ["SRC*/*.mdb", "SRC*/*.accdb", "SRC*/*/*.mdb", "SRC*/*/*.accdb"]
    files: List[pathlib.Path] = []
    for pat in patterns:
        files += list(SRC_ROOT.glob(pat))
    return sorted(files)

# ---------- Windows (pyodbc) ----------
def _win_available() -> bool:
    return platform.system().lower().startswith("win")

def _pyodbc_conn_str(db: pathlib.Path) -> str:
    drv = os.environ.get("ACCESS_ODBC_DRIVER", "Microsoft Access Driver (*.mdb, *.accdb)")
    return f"Driver={{{drv}}};DBQ={db};"

def _win_list_tables(conn) -> List[str]:
    cur = conn.cursor()
    tables = []
    for row in cur.tables():
        if str(row.table_type).upper() == "TABLE":
            tables.append(row.table_name)
    return tables

def _win_query_to_csv(conn, table: str, out_csv: pathlib.Path):
    cur = conn.cursor()
    sql = f"SELECT * FROM [{table}]"
    rs = cur.execute(sql)
    cols = [c[0] for c in rs.description]
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in rs:
            w.writerow(list(row))

def _win_union_to_csv(conn, tables: List[str], out_csv: pathlib.Path) -> bool:
    if not tables:
        return False
    cur = conn.cursor()
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    first = True
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for t in tables:
            rs = cur.execute(f"SELECT * FROM [{t}]")
            cols = [c[0] for c in rs.description]
            if first:
                w.writerow(cols); first = False
            for row in rs:
                w.writerow(list(row))
    return True

# ---------- macOS/Linux (mdbtools) ----------
def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def _nix_list_tables(db: pathlib.Path) -> List[str]:
    try:
        out = _run(["mdb-tables", "-1", str(db)]).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mdb-tables failed on {db}: {e.stderr.strip()}")
    return [line.strip() for line in out.splitlines() if line.strip()]

def _nix_export_table(db: pathlib.Path, table: str, out_csv: pathlib.Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    try:
        text = _run(["mdb-export", "-D", "%Y-%m-%d", str(db), table]).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"mdb-export failed on {db} / {table}: {e.stderr.strip()}")
    out_csv.write_text(text, encoding="utf-8")

def _nix_union_tables(db: pathlib.Path, tables: List[str], out_csv: pathlib.Path) -> bool:
    if not tables:
        return False
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    first = True
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        for t in tables:
            text = _run(["mdb-export", "-D", "%Y-%m-%d", str(db), t]).stdout
            lines = text.splitlines()
            if not lines: 
                continue
            if first:
                f.write("\n".join(lines) + "\n")
                first = False
            else:
                # append without header
                f.write("\n".join(lines[1:]) + "\n")
    return True

# ---------- shared matching helpers ----------
def _first_match(tables: List[str], regex: re.Pattern) -> Optional[str]:
    for t in tables:
        if regex.search(t):
            return t
    return None

def _first_match_any(tables: List[str], regexes: List[re.Pattern]) -> Optional[str]:
    for rgx in regexes:
        m = _first_match(tables, rgx)
        if m: return m
    return None

def process_one(db: pathlib.Path):
    year_base = db.parent.name
    out_dir = OUT_ROOT / year_base
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f">> Extracting from: {db}")

    if _win_available():
        import pyodbc
        try:
            conn = pyodbc.connect(_pyodbc_conn_str(db), autocommit=True)
        except pyodbc.Error as e:
            print(f"ERROR: cannot open {db}: {e}")
            return
        tables = _win_list_tables(conn)

        # Attendance
        att = _first_match(tables, ATTENDANCE_PAT)
        if att:
            print(f"   - {att} -> acc_em_chronic_absenteeism.csv")
            _win_query_to_csv(conn, att, out_dir / "acc_em_chronic_absenteeism.csv")
        else:
            print("WARN: attendance not found")

        # ELA
        elas = [t for t in tables if ELA_UNION_PAT.search(t)]
        if elas and _win_union_to_csv(conn, elas, out_dir / "annual_em_ela.csv"):
            print(f"   - union({len(elas)} ELA tables) -> annual_em_ela.csv")
        else:
            ela = _first_match_any(tables, ELA_ANNUAL_PATS)
            if ela:
                print(f"   - {ela} -> annual_em_ela.csv")
                _win_query_to_csv(conn, ela, out_dir / "annual_em_ela.csv")
            else:
                print("WARN: ELA not found")

        # Math
        maths = [t for t in tables if MATH_UNION_PAT.search(t)]
        if maths and _win_union_to_csv(conn, maths, out_dir / "annual_em_math.csv"):
            print(f"   - union({len(maths)} Math tables) -> annual_em_math.csv")
        else:
            math = _first_match_any(tables, MATH_ANNUAL_PATS)
            if math:
                print(f"   - {math} -> annual_em_math.csv")
                _win_query_to_csv(conn, math, out_dir / "annual_em_math.csv")
            else:
                print("WARN: Math not found")

        # Org
        org = _first_match(tables, ORG_PAT)
        if org:
            print(f"   - {org} -> boces_n_rc.csv")
            _win_query_to_csv(conn, org, out_dir / "boces_n_rc.csv")
        else:
            print("WARN: org not found")

        conn.close()
    else:
        # macOS/Linux via mdbtools
        tables = _nix_list_tables(db)

        # Attendance
        att = _first_match(tables, ATTENDANCE_PAT)
        if att:
            print(f"   - {att} -> acc_em_chronic_absenteeism.csv")
            _nix_export_table(db, att, out_dir / "acc_em_chronic_absenteeism.csv")
        else:
            print("WARN: attendance not found")

        # ELA
        elas = [t for t in tables if ELA_UNION_PAT.search(t)]
        wrote = False
        if elas:
            wrote = _nix_union_tables(db, elas, out_dir / "annual_em_ela.csv")
            if wrote:
                print(f"   - union({len(elas)} ELA tables) -> annual_em_ela.csv")
        if not wrote:
            ela = _first_match_any(tables, ELA_ANNUAL_PATS)
            if ela:
                print(f"   - {ela} -> annual_em_ela.csv")
                _nix_export_table(db, ela, out_dir / "annual_em_ela.csv")
            else:
                print("WARN: ELA not found")

        # Math
        maths = [t for t in tables if MATH_UNION_PAT.search(t)]
        wrote = False
        if maths:
            wrote = _nix_union_tables(db, maths, out_dir / "annual_em_math.csv")
            if wrote:
                print(f"   - union({len(maths)} Math tables) -> annual_em_math.csv")
        if not wrote:
            math = _first_match_any(tables, MATH_ANNUAL_PATS)
            if math:
                print(f"   - {math} -> annual_em_math.csv")
                _nix_export_table(db, math, out_dir / "annual_em_math.csv")
            else:
                print("WARN: Math not found")

        # Org
        org = _first_match(tables, ORG_PAT)
        if org:
            print(f"   - {org} -> boces_n_rc.csv")
            _nix_export_table(db, org, out_dir / "boces_n_rc.csv")
        else:
            print("WARN: org not found")

def main():
    files = list_src_files()
    if not files:
        print(f"No .mdb/.accdb under {SRC_ROOT}")
        sys.exit(1)
    for db in files:
        process_one(db)
    print(f"✅ OK: CSVs written under {OUT_ROOT}/SRCYYYY/*.csv")

if __name__ == "__main__":
    main()
