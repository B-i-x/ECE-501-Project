import sqlite3, pathlib

DB = pathlib.Path("db/nysed.sqlite")

ORDER = [
  "00_schema.sql",
  "09_staging_persistent.sql",  # build persistent staging from imported raw tables
  "01_seed_dims.sql",           # can now pull distinct years from staging
  "02_upsert_orgs.sql",         # populate dim_district and dim_school from st_org
  "10_load_enrollment.sql",
  "11_load_attendance.sql",
  "12_load_assessment.sql",
  "13_load_expenditures.sql",  # load expenditures fact table
  "20_refresh_summary.sql",
  "03_indexes.sql",             # indexes are idempotent (safe to reapply)
  "99_checks.sql"               # QA at the end
]

def exec_script(con, path):
  with open(path, "r", encoding="utf-8") as f:
    con.executescript(f.read())

DB.parent.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB.as_posix())
con.execute("PRAGMA foreign_keys=ON;")
con.execute("PRAGMA journal_mode=WAL;")
con.execute("PRAGMA synchronous=NORMAL;")

for name in ORDER:
  p = pathlib.Path("sql") / name
  if p.exists():
    exec_script(con, p.as_posix())
  else:
    print(f"[skip] {p}")

con.commit()
con.close()
print("OK: star schema built & summary refreshed")
