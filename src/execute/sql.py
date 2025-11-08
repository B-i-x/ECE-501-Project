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