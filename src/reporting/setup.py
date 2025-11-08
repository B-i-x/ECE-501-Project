#db_setup.py
#Reusable setup for the QueryLaunch / QueryResult SQLite database.

from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Tuple

from app import AppConfig

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS QueryLaunch (
    launch_ID      INTEGER PRIMARY KEY,
    timestamp      TEXT NOT NULL,
    query_name     TEXT NOT NULL,
    status         TEXT NOT NULL,
    query_version  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS QueryResult (
    result_ID        INTEGER PRIMARY KEY,
    launch_ID        INTEGER NOT NULL,
    dataset_size     INTEGER,
    elapsed_seconds  REAL,
    FOREIGN KEY (launch_ID) REFERENCES QueryLaunch(launch_ID)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_QueryResult_launch_ID
ON QueryResult(launch_ID);
""".strip()


def setup_database() -> Tuple[str, bool]:
    """
    Ensure the database exists with the correct schema.
    
    Parameters
    ----------
    db_path : str
        File path for the SQLite DB. If the file does not exist, it will be created.
    
    Returns
    -------
    (db_path, created) : (str, bool)
        db_path is the absolute path to the DB file.
        created is True if the DB file did not exist before this call.
    """
    path = Path(AppConfig.result_db_path).expanduser().resolve()
    created = not path.exists()

    # Connect (this will create the file if it doesn't exist)
    con = sqlite3.connect(str(path))
    try:
        cur = con.cursor()
        # Apply schema (idempotent)
        for stmt in [s.strip() for s in SCHEMA_SQL.split(";") if s.strip()]:
            cur.execute(stmt + ";")
        con.commit()
    finally:
        con.close()

    return (str(path), created)


if __name__ == "__main__":
    location, created = setup_database()
    print(f"Database ready at: {location} (created={created})")