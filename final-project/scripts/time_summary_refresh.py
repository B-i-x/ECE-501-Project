#!/usr/bin/env python3
"""
time_summary_refresh.py

Measure how long it takes to refresh the fact_summary_sys table.

Usage:
    python scripts/time_summary_refresh.py
    python scripts/time_summary_refresh.py --runs 10  # run multiple times for statistics
"""

import sqlite3
import time
import csv
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "nysed.sqlite"
SQL_PATH = ROOT / "sql" / "20_refresh_summary.sql"
OUTDIR = ROOT / "experiments" / "results"
OUTDIR.mkdir(parents=True, exist_ok=True)


def read_sql(path: Path) -> str:
    """Read SQL file content."""
    return path.read_text(encoding="utf-8")


def refresh_summary(con: sqlite3.Connection) -> float:
    """Execute summary refresh and return elapsed time in seconds."""
    sql = read_sql(SQL_PATH)
    t0 = time.perf_counter()
    con.executescript(sql)
    con.commit()
    dt = time.perf_counter() - t0
    return dt


def main():
    parser = argparse.ArgumentParser(description="Time summary table refresh")
    parser.add_argument("--runs", type=int, default=1,
                       help="Number of runs (default: 1, use >1 for statistics)")
    parser.add_argument("--warmup", type=int, default=1,
                       help="Number of warmup runs (default: 1)")
    parser.add_argument("--output", type=str, default=None,
                       help="Output CSV file (default: auto-generated timestamp)")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Make sure you have built the star schema first.")
        return 1

    if not SQL_PATH.exists():
        print(f"ERROR: SQL file not found at {SQL_PATH}")
        return 1

    con = sqlite3.connect(DB_PATH.as_posix())
    con.execute("PRAGMA foreign_keys=ON;")
    con.execute("PRAGMA journal_mode=WAL;")

    # Warmup runs
    if args.warmup > 0:
        print(f"Warming up ({args.warmup} run(s))...")
        for _ in range(args.warmup):
            refresh_summary(con)
        print("Warmup complete.\n")

    # Timed runs
    times = []
    print(f"Running {args.runs} timed refresh(es)...")
    for i in range(args.runs):
        dt = refresh_summary(con)
        times.append(dt)
        print(f"  Run {i+1}/{args.runs}: {dt:.3f}s")

    con.close()

    # Statistics
    times.sort()
    if args.runs == 1:
        print(f"\nSummary refresh time: {times[0]:.3f}s")
    else:
        p50 = times[len(times) // 2]
        p95 = times[int(0.95 * (len(times) - 1))] if len(times) > 1 else times[0]
        p99 = times[int(0.99 * (len(times) - 1))] if len(times) > 1 else times[-1]
        avg = sum(times) / len(times)
        min_time = times[0]
        max_time = times[-1]

        print(f"\nSummary refresh statistics ({args.runs} runs):")
        print(f"   Min:    {min_time:.3f}s")
        print(f"   P50:    {p50:.3f}s")
        print(f"   P95:    {p95:.3f}s")
        print(f"   P99:    {p99:.3f}s")
        print(f"   Max:    {max_time:.3f}s")
        print(f"   Avg:    {avg:.3f}s")

    # Save to CSV if requested or if multiple runs
    if args.output or args.runs > 1:
        if args.output:
            outfile = Path(args.output)
        else:
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            outfile = OUTDIR / f"summary_refresh_timings_{stamp}.csv"

        with open(outfile, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["run", "time_seconds"])
            for i, t in enumerate(times, 1):
                w.writerow([i, f"{t:.6f}"])
        print(f"\nSaved timings to: {outfile}")

    return 0


if __name__ == "__main__":
    exit(main())

