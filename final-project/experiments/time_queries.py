import sqlite3, time, csv
from pathlib import Path
from datetime import datetime
from config import DBS, QUERIES, QUERIES_WIDE

OUTDIR = Path("experiments/results")
OUTDIR.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTFILE = OUTDIR / f"timings_{STAMP}.csv"

RUNS = 5  # run each query multiple times; report P50/P95 in your writeup

def run_and_time(conn, sql):
    # warm-up run (don’t time)
    conn.execute(sql).fetchall()
    # timed runs
    times = []
    for _ in range(RUNS):
        t0 = time.perf_counter()
        conn.execute(sql).fetchall()
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()
    p50 = times[len(times)//2]
    p95 = times[int(0.95*(len(times)-1))]
    return p50, p95

def main():
    rows = []
    for schema, dbpath in DBS.items():
        qset = QUERIES if schema == "star" else QUERIES_WIDE
        with sqlite3.connect(dbpath) as conn:
            conn.execute("PRAGMA foreign_keys=ON;")
            for name, sql in qset.items():
                try:
                    p50, p95 = run_and_time(conn, sql)
                    rows.append([schema, name, f"{p50:.2f}", f"{p95:.2f}"])
                    print(f"[{schema}] {name}: P50={p50:.2f} ms  P95={p95:.2f} ms")
                except Exception as e:
                    rows.append([schema, name, "ERROR", str(e)])
                    print(f"[{schema}] {name}: ERROR {e}")

    with open(OUTFILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["schema", "query_name", "p50_ms", "p95_ms"])
        w.writerows(rows)
    print(f"Saved: {OUTFILE}")

if __name__ == "__main__":
    main()
