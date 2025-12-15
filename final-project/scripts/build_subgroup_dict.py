#!/usr/bin/env python3
"""
build_subgroup_dict.py

Scan staging tables for distinct subgroup_raw values and
build/merge a canonical subgroup mapping CSV at etl/map_subgroups.csv.

Usage:
    python scripts/build_subgroup_dict.py
"""

import sqlite3
import csv
from pathlib import Path
import sys


DB_PATH = Path("db") / "nysed.sqlite"
OUT_CSV = Path("etl") / "map_subgroups.csv"


def table_exists(cur, name: str) -> bool:
    cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
        (name,),
    )
    return cur.fetchone() is not None


def load_existing_mapping(path: Path):
    """Load existing map_subgroups.csv if present."""
    mapping = {}
    if not path.exists():
        return mapping

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_label = row.get("raw_label")
            if raw_label is None:
                continue
            mapping[raw_label.strip()] = {
                "subgroup_id": row.get("subgroup_id", "").strip(),
                "subgroup_name": row.get("subgroup_name", "").strip(),
            }
    return mapping


def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Make sure you ran the import / staging steps first.")
        sys.exit(1)

    con = sqlite3.connect(DB_PATH.as_posix())
    cur = con.cursor()

    # Ensure staging tables exist
    required_tables = ["st_attendance_em_num", "st_assessment_em_num"]
    missing = [t for t in required_tables if not table_exists(cur, t)]
    if missing:
        print("ERROR: Missing staging tables:", ", ".join(missing))
        print("You probably need to run:")
        print("  sqlite3 db/nysed.sqlite < sql/09_staging_persistent.sql")
        con.close()
        sys.exit(1)

    # Collect distinct raw subgroup labels from both staging tables
    query = """
    SELECT DISTINCT TRIM(subgroup_raw) AS subgroup_raw
    FROM st_attendance_em_num
    WHERE subgroup_raw IS NOT NULL AND TRIM(subgroup_raw) <> ''
    UNION
    SELECT DISTINCT TRIM(subgroup_raw) AS subgroup_raw
    FROM st_assessment_em_num
    WHERE subgroup_raw IS NOT NULL AND TRIM(subgroup_raw) <> ''
    ORDER BY 1;
    """

    cur.execute(query)
    rows = cur.fetchall()
    con.close()

    raw_values = [r[0] for r in rows if r[0] is not None]

    print(f"Found {len(raw_values)} distinct subgroup_raw values in staging.")

    # Load existing mapping if present
    existing = load_existing_mapping(OUT_CSV)
    if existing:
        print(f"Loaded {len(existing)} existing mappings from {OUT_CSV}")

    # Merge: keep existing mappings, add new raw_labels with blanks
    merged = []
    for raw in raw_values:
        raw_stripped = raw.strip()
        if raw_stripped in existing:
            entry = existing[raw_stripped]
            subgroup_id = entry.get("subgroup_id", "")
            subgroup_name = entry.get("subgroup_name", "")
        else:
            subgroup_id = ""
            subgroup_name = ""
        merged.append(
            {
                "raw_label": raw_stripped,
                "subgroup_id": subgroup_id,
                "subgroup_name": subgroup_name,
            }
        )

    # Also preserve any existing raw_labels that no longer appear (optional)
    for raw, entry in existing.items():
        if raw not in {m["raw_label"] for m in merged}:
            merged.append(
                {
                    "raw_label": raw,
                    "subgroup_id": entry.get("subgroup_id", ""),
                    "subgroup_name": entry.get("subgroup_name", ""),
                }
            )

    # Sort by raw_label for readability
    merged.sort(key=lambda r: r["raw_label"].lower())

    # Ensure etl/ directory exists
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Write CSV
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["raw_label", "subgroup_id", "subgroup_name"],
        )
        writer.writeheader()
        writer.writerows(merged)

    print(f"Wrote {len(merged)} rows to {OUT_CSV}")
    print("Next step: open this file and fill in subgroup_id and subgroup_name.")
    print("Example:")
    print("  raw_label,subgroup_id,subgroup_name")
    print("  Female,F,Female")
    print("  Economically Disadvantaged,ED,Economically Disadvantaged")


if __name__ == "__main__":
    main()
