#!/usr/bin/env python3
import sqlite3, pathlib, json

DB = pathlib.Path("db/nysed.sqlite")
QUERIES = {
    "absence_vs_prof": """
        SELECT * FROM v_absence_vs_proficiency LIMIT 10;
    """,
}

con = sqlite3.connect(DB.as_posix())
cur = con.cursor()
plans = {}
for name, q in QUERIES.items():
    cur.execute("EXPLAIN QUERY PLAN " + q)
    plans[name] = cur.fetchall()

out = pathlib.Path("design") / "explain_plans.json"
out.write_text(json.dumps(plans, indent=2))
print(f"wrote {out}")
con.close()
