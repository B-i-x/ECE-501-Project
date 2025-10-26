import sqlite3, os, pathlib

BASE = pathlib.Path(__file__).resolve().parents[1]
DB_DIR = BASE / "data"
DB_DIR.mkdir(exist_ok=True)
DB = DB_DIR / "nysed.db"

with sqlite3.connect(DB) as conn:
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript((BASE/"sql/schema.sql").read_text())
print(f"Initialized {DB}")
