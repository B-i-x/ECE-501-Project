#!/usr/bin/env python3
import argparse
import csv
from pdb import run
import statistics
import time
from pathlib import Path
from typing import List, Optional

import sqlite3

from app.queries import QuerySpec
from load.convert_to_sqlite import convert_datalink_to_sqlite, get_datalink_sqlite_path
from ingest.downloader import fetch_accdb_from_datalink
from app import AppConfig
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
    if timeout_s is not None and timeout_s > 0:
        def _ph():
            if time.perf_counter() - start > timeout_s:
                return 1
            return 0
        conn.set_progress_handler(_ph, 1000)
    else:
        conn.set_progress_handler(None, 0)

    sql = sql_text.strip()
    # Always print SQL for debugging
    print("\n===", desc or "(unnamed)")
    print(debug_sql(sql, params))

    t0 = time.perf_counter()
    cur = conn.cursor()
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


# ---------- Runner API ----------

def run_queryspec(
    spec: QuerySpec,
    runs: int,
    dataset_limits: List[int],
    timeout_s: Optional[int] = 300,
    num_lines_to_preview: int = 5,
):
    print(f"\n[RUN] {spec.name} v{spec.version}  folder={spec.sql_folder}  runs={runs}  timeout={timeout_s}s")

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-64000;")
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")
    conn.row_factory = None

    for dataset in spec.dependant_datasets:
        dataset_sqlite_path = get_datalink_sqlite_path(dataset)  # Ensure dataset is materialized
        
        if not dataset_sqlite_path.exists():
            print(f"Dataset SQLite not found for {dataset.folder_name}, going to download and convert...")
            fetch_accdb_from_datalink(dataset)
            dataset_sqlite_path = convert_datalink_to_sqlite(dataset, verbose=True)
        
        run_sql(
            conn,
            f"ATTACH DATABASE '{dataset_sqlite_path.as_posix()}' AS '{dataset.folder_name}';")


    sql_texts = load_sql_sequence(spec.sql_folder, spec.sql_file_sequence)

    latencies = []
    last_result = None
    for limit in dataset_limits:
        print(f"\n[INFO] Dataset limit: {limit:,}")
        latencies = []
        for r in range(1, runs + 1):
            t0 = time.perf_counter()
            for i, sql in enumerate(sql_texts, start=1):
                desc = f"{spec.name} rows={limit:,} run {r}/{runs} part {i}/{len(sql_texts)}"
                run_sql(conn, sql, desc=desc,
                        params={"n_limit": int(limit)},  # <-- pass the dataset limit here
                        preview=num_lines_to_preview,
                        timeout_s=timeout_s)
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            print(f"[RESULT] {spec.name} rows={limit:,} run {r}/{runs} time={elapsed:.3f}s")
            conn.execute("PRAGMA optimize;")
            conn.execute("PRAGMA shrink_memory;")

    latencies.sort()
    p50 = statistics.median(latencies)
    from math import ceil
    idx = max(0, min(len(latencies) - 1, ceil(0.95 * len(latencies)) - 1))
    p95 = latencies[idx]
    print(f"[SUMMARY] {spec.name} rows={limit:,} P50={p50:.3f}s P95={p95:.3f}s over {runs} runs")

    last_result = {"name": spec.name, "version": spec.version, "runs": runs, "p50": p50, "p95": p95}
    return last_result


# ---------- Script entry ----------
from app.queries import BASELINE_QUERY_1

def main():
    exec_config = AppConfig.load_execution_config()
    # Run a single QuerySpec as a test
    # print(exec_config.dataset_partitions_per_query)
    if BASELINE_QUERY_1.name in exec_config.dataset_partitions_per_query:
        print(f"\n[INFO] Running {BASELINE_QUERY_1.name} with dataset limits: {exec_config.dataset_partitions_per_query[BASELINE_QUERY_1.name]}")
        res = run_queryspec(
            BASELINE_QUERY_1,
            runs=exec_config.runs_per_query,
            dataset_limits=exec_config.dataset_partitions_per_query[BASELINE_QUERY_1.name],
            timeout_s=exec_config.timeout_seconds,
            num_lines_to_preview=5,
            )

    # with open("results.csv", "w", newline="") as f:
    #     w = csv.writer(f)
    #     w.writerow(["query_name", "version", "runs", "P50_seconds", "P95_seconds"])
    #     w.writerow([res["name"], res["version"], res["runs"], f"{res['p50']:.6f}", f"{res['p95']:.6f}"])

    # print(f"\n[INFO] Results saved to results.csv")

if __name__ == "__main__":
    main()
