#!/usr/bin/env python3
import argparse
import csv
import statistics
import time
from pathlib import Path
from typing import Dict, List, Optional

import sqlite3
import yaml

from app import AppConfig  # pip install pyyaml


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
    echo: bool = True,
):
    # Install a per-statement timeout via progress handler
    start = time.perf_counter()
    if timeout_s is not None and timeout_s > 0:
        def _ph():
            if time.perf_counter() - start > timeout_s:
                return 1  # abort this statement
            return 0
        conn.set_progress_handler(_ph, 1000)
    else:
        conn.set_progress_handler(None, 0)

    sql = sql_text.strip()
    if echo:
        print("\n===", desc or "(unnamed)")
        print(debug_sql(sql, params))

    t0 = time.perf_counter()
    cur = conn.cursor()
    # Detect single-statement SELECT/CTE vs multi-statement scripts
    first = sql.split(None, 1)[0].upper() if sql else ""
    is_select_like = first in ("SELECT", "WITH", "PRAGMA")
    try:
        if is_select_like and ";" not in sql.rstrip().rstrip(";"):
            cur.execute(sql, params or {})
            rows = cur.fetchmany(preview)
            elapsed = time.perf_counter() - t0
            print(f"[OK] {desc} in {elapsed:.3f}s. Preview {len(rows)} row(s):")
            for r in rows:
                print(r)
            return rows
        else:
            # Use executescript for multi-statement files. Params cannot be bound here.
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


# ---------- Config + SQL loading ----------

def load_config(path: Path) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if not isinstance(cfg, dict) or "query_config" not in cfg:
        raise ValueError("Invalid config. Expected top-level key 'query_config'.")
    return cfg["query_config"]

def load_sql_sequence(folder: Path, file_list: List[str]) -> List[str]:
    sql_texts = []
    for fname in file_list:
        p = folder / fname
        if not p.exists():
            raise FileNotFoundError(f"SQL file not found: {p}")
        sql_texts.append(p.read_text(encoding="utf-8"))
    return sql_texts


# ---------- Runner ----------

def main():

    qcfg = load_config(AppConfig.query_config)

    # Single connection used across all sequences unless a script ATTACHes others
    print(f"[INFO] Connecting to SQLite at {args.db}")
    conn = sqlite3.connect(args.db)
    conn.row_factory = None
    # Speed-focused pragmas. Adjust if you need full durability.
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-64000;")
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")

    results_rows = []
    overall_t0 = time.time()

    # Preserve YAML order
    for name, entry in qcfg.items():
        execute = bool(entry.get("execute", False))
        if not execute:
            print(f"[SKIP] {name} execute=false")
            continue

        sql_folder = base_dir / Path(entry["sql_folder"])
        sequence = entry.get("sql_file_sequence", [])
        num_runs = int(entry.get("num_runs", 1))
        timeout = entry.get("timeout", None)
        timeout_s = int(timeout) if timeout is not None else None
        version = str(entry.get("version", ""))

        print(f"\n[RUN] {name} v{version}  folder={sql_folder}  runs={num_runs}  timeout={timeout_s}s")
        sql_texts = load_sql_sequence(sql_folder, sequence)

        latencies = []
        for r in range(1, num_runs + 1):
            # optional per-run reset hook if you include a reset.sql as first file
            t0 = time.perf_counter()
            for i, sql in enumerate(sql_texts, start=1):
                desc = f"{name} run {r}/{num_runs} part {i}/{len(sql_texts)}"
                run_sql(conn, sql, desc=desc, params=None, preview=args.preview, timeout_s=timeout_s, echo=args.echo)
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            print(f"[RESULT] {name} run {r}/{num_runs} time={elapsed:.3f}s")
            conn.execute("PRAGMA optimize;")
            conn.execute("PRAGMA shrink_memory;")

        latencies.sort()
        p50 = statistics.median(latencies)
        from math import ceil
        idx = max(0, min(len(latencies) - 1, ceil(0.95 * len(latencies)) - 1))
        p95 = latencies[idx]
        print(f"[SUMMARY] {name} P50={p50:.3f}s P95={p95:.3f}s over {num_runs} runs")

        results_rows.append([name, version, num_runs, f"{p50:.6f}", f"{p95:.6f}"])

    total_time = time.time() - overall_t0
    with open(args.out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["query_name", "version", "runs", "P50_seconds", "P95_seconds", "total_wall_time_seconds"])
        for row in results_rows:
            w.writerow(row + [f"{total_time:.6f}"])

    print(f"\n[INFO] Results saved to {args.out}")
    print(f"[INFO] Done. Total wall time: {total_time:.2f}s")


if __name__ == "__main__":
    main()
