import sqlite3
import time
from pathlib import Path
from typing import List, Optional
# ---------- Debug + timeout helpers ----------

def debug_sql(sql: str, params: Optional[dict] = None) -> str:
    if not params:
        return sql
    def _esc(v):
        if v is None: return "NULL"
        if isinstance(v, (int, float)): return str(v)
        s = str(v).replace("'", "''")
        return f"'{s}'"
    out = sql
    for k in sorted(params.keys(), key=len, reverse=True):
        out = out.replace(f":{k}", _esc(params[k]))
    return out


def run_sql(
    conn: sqlite3.Connection,
    sql_text: str,
    desc: str = "",
    params: Optional[dict] = None,
    preview: int = 5,
    timeout_s: Optional[int] = None,
):
    start = time.perf_counter()
    if timeout_s and timeout_s > 0:
        def _ph():
            return 1 if time.perf_counter() - start > timeout_s else 0
        conn.set_progress_handler(_ph, 1000)
    else:
        conn.set_progress_handler(None, 0)

    sql = sql_text.strip()
    print("\n===", desc or "(unnamed)")
    # print(debug_sql(sql, params))

    # Single vs multi statement (allow one trailing semicolon)
    sql_no_trailing = sql[:-1] if sql.endswith(";") else sql
    is_single_stmt = ";" not in sql_no_trailing

    t0 = time.perf_counter()
    cur = conn.cursor()
    try:
        if is_single_stmt:
            cur.execute(sql, params or {})
            # preview only for read statements
            first = sql.split(None, 1)[0].upper() if sql else ""
            if first in ("SELECT", "WITH", "PRAGMA"):
                rows = cur.fetchmany(preview)
                elapsed = time.perf_counter() - t0
                print(f"[OK] {desc} in {elapsed:.3f}s. Preview {len(rows)} row(s):")
                for r in rows:
                    print(r)
                return rows
            else:
                elapsed = time.perf_counter() - t0
                print(f"[OK] {desc} in {elapsed:.3f}s.")
                return None
        else:
            if params:
                print("[WARN] Parameters ignored for multi-statement script. Split the SQL if you need params.")
            cur.executescript(sql)
            elapsed = time.perf_counter() - t0
            print(f"[OK] {desc} in {elapsed:.3f}s.")
            return None
    except sqlite3.Error as e:
        elapsed = time.perf_counter() - t0
        print(f"[ERROR] {desc} after {elapsed:.3f}s -> {e}")
        raise
    finally:
        conn.set_progress_handler(None, 0)


# ---------- SQL loading ----------

def load_sql_sequence(folder: Path, file_list: List[str]) -> List[str]:
    sql_texts = []
    for fname in file_list:
        p = folder / fname
        if not p.exists():
            raise FileNotFoundError(f"SQL file not found: {p}")
        sql_texts.append(p.read_text(encoding="utf-8"))
    return sql_texts

from load.convert_to_sqlite import convert_datalink_to_sqlite, get_datalink_sqlite_path
from ingest.downloader import fetch_accdb_from_datalink
from app.queries import QuerySpec

def create_sqlite_conn_for_spec(spec: QuerySpec) -> sqlite3.Connection:
    """
    Create an in-memory SQLite connection and attach all dependant_datasets
    for the given QuerySpec. This is basically the setup part of run_queryspec,
    but without timing / reporting.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-64000;")
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")
    conn.row_factory = None

    for dataset in spec.dependant_datasets:
        dataset_sqlite_path = get_datalink_sqlite_path(dataset)

        if not dataset_sqlite_path.exists():
            print(f"Dataset SQLite not found for {dataset.folder_name}, going to download and convert...")
            fetch_accdb_from_datalink(dataset)
            dataset_sqlite_path = convert_datalink_to_sqlite(dataset, verbose=True)

        run_sql(
            conn,
            f"ATTACH DATABASE '{dataset_sqlite_path.as_posix()}' AS '{dataset.folder_name}';",
        )

    return conn