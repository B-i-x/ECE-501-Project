#!/usr/bin/env python3
"""
load_map_subgroups.py

Load etl/map_subgroups.csv into the map_subgroups table in the database.

Usage:
    python scripts/load_map_subgroups.py
"""

import sqlite3
import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "nysed.sqlite"
CSV_PATH = ROOT / "etl" / "map_subgroups.csv"


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Make sure you have run the import step first:")
        print("  python scripts/import_csv_to_sqlite.py")
        sys.exit(1)

    if not CSV_PATH.exists():
        print(f"ERROR: CSV file not found at {CSV_PATH}")
        print("Make sure etl/map_subgroups.csv exists.")
        sys.exit(1)

    con = sqlite3.connect(DB_PATH.as_posix())
    cur = con.cursor()

    # Ensure map_subgroups table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS map_subgroups (
            raw_label   TEXT PRIMARY KEY,
            subgroup_id TEXT,
            subgroup_name TEXT
        );
    """)

    # Clear existing data (optional - comment out if you want to preserve existing)
    cur.execute("DELETE FROM map_subgroups;")

    # Load CSV
    with CSV_PATH.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            raw_label = row.get("raw_label", "").strip()
            subgroup_id = row.get("subgroup_id", "").strip()
            subgroup_name = row.get("subgroup_name", "").strip()
            
            if raw_label:  # Skip empty raw_labels
                rows.append((raw_label, subgroup_id, subgroup_name))

    if rows:
        cur.executemany(
            "INSERT OR REPLACE INTO map_subgroups (raw_label, subgroup_id, subgroup_name) VALUES (?, ?, ?);",
            rows
        )
        con.commit()
        print(f"✅ Loaded {len(rows)} rows from {CSV_PATH} into map_subgroups table")
    else:
        print(f"WARNING: No valid rows found in {CSV_PATH}")

    # Verify
    cur.execute("SELECT COUNT(*) FROM map_subgroups;")
    count = cur.fetchone()[0]
    print(f"   Total rows in map_subgroups: {count}")

    con.close()


if __name__ == "__main__":
    main()

