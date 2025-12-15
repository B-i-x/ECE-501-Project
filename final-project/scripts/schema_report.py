#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec  3 17:36:02 2025

Simple SQLite schema reporter.

Usage:
    python schema_report.py /path/to/output/sqlite

- Scans the given directory for any .db, .sqlite, or .sqlite3 files.
- Prints each database name.
- Under it, prints each table and the columns in that table.
"""

import sys
import sqlite3
from pathlib import Path

def list_sqlite_files(folder: Path):
    if not folder.exists() or not folder.is_dir():
        print(f"Error: {folder} is not a valid directory")
        sys.exit(1)
    for f in folder.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
            yield f

def print_schema(db_path: Path):
    print(f"\n=== Database: {db_path} ===")
    try:
        conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name;
        """)
        tables = cur.fetchall()

        if not tables:
            print("  (no user tables found)")
            return

        for (table,) in tables:
            print(f"\n  [Table] {table}")
            cur.execute(f'PRAGMA table_info("{table}")')
            columns = cur.fetchall()
            if not columns:
                print("    (no columns found)")
            else:
                print("    columns:")
                for col in columns:
                    cid, name, col_type, notnull, default, pk = col
                    pk_str = "PRIMARY KEY" if pk else ""
                    nn_str = "NOT NULL" if notnull else ""
                    default_str = f"DEFAULT {default}" if default is not None else ""
                    print(f"      - {name} {col_type} {pk_str} {nn_str} {default_str}")
    except Exception as e:
        print(f"  Error reading database: {e}")
    finally:
        try:
            conn.close()
        except:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python schema_report.py /path/to/output/sqlite")
        sys.exit(1)

    folder = Path(sys.argv[1]).resolve()
    db_files = list(list_sqlite_files(folder))

    if not db_files:
        print("No SQLite files found in the specified directory.")
        sys.exit(0)

    for db in db_files:
        print_schema(db)

if __name__ == "__main__":
    main()