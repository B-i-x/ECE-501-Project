# tools/accdb_to_sqlite.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from collections import Counter
from typing import Optional, List

import pandas as pd
import pyodbc

from app.datasets import DataLink
from ingest.downloader import fetch_accdb_from_datalink
from app import AppConfig


def _ensure_dirs(baseline_dir: str) -> None:
    Path(baseline_dir).mkdir(parents=True, exist_ok=True)


def _access_driver() -> Optional[str]:
    # e.g. "Microsoft Access Driver (*.mdb, *.accdb)"
    for d in reversed(pyodbc.drivers()):
        if "Access Driver" in d:
            return d
    return None


def _wanted_table(row) -> bool:
    name = (row.table_name or "").strip()
    if not name:
        return False
    if name.startswith("MSys") or name.startswith("~"):
        return False
    t = (row.table_type or "").upper()
    return t in {"TABLE", "VIEW", "SYSTEM TABLE"}


def _copy_table_chunked(table: str, src_conn, dst_conn, chunksize: int = 100_000) -> int:
    sql = f"SELECT * FROM [{table}]"
    total = 0
    first = True
    try:
        for chunk in pd.read_sql(sql, src_conn, chunksize=chunksize):
            total += len(chunk)
            chunk.to_sql(table, dst_conn, if_exists="replace" if first else "append", index=False)
            first = False
        if first:
            df = pd.read_sql(sql, src_conn)
            total = len(df)
            df.to_sql(table, dst_conn, if_exists="replace", index=False)
        return total
    except Exception as e:
        raise RuntimeError(str(e))

def get_datalink_sqlite_path(dl: DataLink) -> Path:
    """
    Get the expected SQLite file path for the given DataLink.
    """
    out_name = dl.folder_name + ".db"
    sqlite_path = Path(AppConfig.baseline_dir) / out_name
    return sqlite_path

def convert_datalink_to_sqlite(
    dl: DataLink,
    verbose: bool = True,
) -> Path:
    """
    Convert the single Access .accdb in data/ny_edu_data/<folder_name>/ into a SQLite DB
    written to AppConfig.baseline_dir. Returns the SQLite path.

    Rules:
      - The dataset folder must contain exactly one .accdb file.
      - Output file name defaults to the accdb stem + ".db" unless sqlite_name is provided.
    """
    sqlite_path = get_datalink_sqlite_path(dl)
    # Early exit if the desired SQLite already exists
    if sqlite_path.exists():
        if verbose:
            print(f"SQLite for {dl.folder_name} already exists. Skipping conversion.")
        return sqlite_path


    dataset_root = Path(AppConfig.ny_edu_data) / dl.folder_name
    if not dataset_root.exists():
        print(f"Dataset folder not found: {dataset_root}, going to download...")
        fetch_accdb_from_datalink(dl)

    accdbs: List[Path] = [p for p in dataset_root.glob("*.accdb") if p.is_file()]
    mdbs: List[Path] = [p for p in dataset_root.glob("*.mdb") if p.is_file()]
    candidates: List[Path] = accdbs + mdbs

    if len(candidates) == 0:
        raise FileNotFoundError(f"No .accdb or .mdb files found in {dataset_root}")
    if len(candidates) > 1:
        raise RuntimeError(f"Expected exactly one .accdb or .mdb in {dataset_root} but found {len(candidates)}: {candidates}")

    accdb_path = candidates[0]

    _ensure_dirs(AppConfig.baseline_dir)

    driver = _access_driver()
    if not driver:
        raise RuntimeError(
            "ODBC Access driver not found. Install the Microsoft Access Database Engine redistributable."
        )

    if verbose:
        print(f"Input ACCDB: {accdb_path}")
        print(f"Output SQLite: {sqlite_path}")

    src_conn = pyodbc.connect(f"DRIVER={{{driver}}};DBQ={accdb_path};", autocommit=False)
    dst_conn = sqlite3.connect(str(sqlite_path))
    # speed-friendly pragmas that keep integrity reasonable
    dst_conn.execute("PRAGMA journal_mode=WAL;")
    dst_conn.execute("PRAGMA synchronous=NORMAL;")
    dst_conn.execute("PRAGMA temp_store=MEMORY;")

    try:
        cur = src_conn.cursor()
        rows = list(cur.tables())
        objs = [r for r in rows if _wanted_table(r)]

        # Deduplicate by name
        seen = set()
        tables: List[str] = []
        for r in objs:
            nm = r.table_name
            if nm not in seen:
                seen.add(nm)
                tables.append(nm)

        if verbose:
            counts = Counter((r.table_type or "UNKNOWN").upper() for r in objs)
            print("Discovered objects:", counts)
            print(f"Will attempt to copy {len(tables)} objects:")
            for nm in tables:
                print(" -", nm)

        copied, skipped = [], []

        for t in tables:
            try:
                nrows = _copy_table_chunked(t, src_conn, dst_conn, chunksize=100_000)
                copied.append((t, nrows))
                if verbose:
                    print(f"✔ Copied: {t} ({nrows} rows)")
            except Exception as e:
                skipped.append((t, str(e)))
                if verbose:
                    print(f"✖ Skipped: {t} -> {e}")

        dst_conn.commit()

        if verbose:
            print("\nSummary:")
            print(f"SQLite: {sqlite_path}")
            print(f"Copied: {len(copied)}")
            if skipped:
                print(f"Skipped: {len(skipped)}")
                for name, err in skipped:
                    print(f" - {name}: {err}")

        return sqlite_path
    finally:
        try:
            dst_conn.close()
        except Exception:
            pass
        try:
            src_conn.close()
        except Exception:
            pass

from app.datasets import STUDENT_EDUCATOR_DATABASE_23_24, GRADUATION_RATE_23_24

if __name__ == "__main__":
    convert_datalink_to_sqlite(GRADUATION_RATE_23_24)

    