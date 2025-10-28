#!/usr/bin/env python3
import sqlite3
import csv
import time
from pathlib import Path
from config import DB_PATH, QUERIES   # you probably already have this defined

OUTPUT_FILE = Path("experiments/query_plans.csv")

def capture_explain_plan(conn, name, sql):
    cursor = conn.execute(f"EXPLAIN QUERY PLAN {sql}")
    plan_rows = cursor.fetchall()
    plan_text = " | ".join([r[3] for r in plan_rows])  # column 3 = description
    return plan_text

def main():
    with sqlite3.connect(DB_PATH) as conn, open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["query_name", "plan_text"])

        for name, sql in QUERIES.items():
            try:
                plan_text = capture_explain_plan(conn, name, sql)
                writer.writerow([name, plan_text])
                print(f"[OK] {name}")
            except Exception as e:
                print(f"[FAIL] {name}: {e}")
                writer.writerow([name, f"ERROR: {e}"])

if __name__ == "__main__":
    main()

