#!/usr/bin/env python3
import sqlite3
import argparse
import time
from textwrap import dedent
import csv


def run(conn, sql, desc="", preview=5, fetch_all=False, params=None):
    t0 = time.time()
    cur = conn.cursor()

    stripped = sql.lstrip()
    first_token = stripped.split(None, 1)[0].upper() if stripped else ""
    is_select_like = first_token in ("SELECT", "WITH")  # treat CTE as SELECT too

    try:
        if is_select_like:
            cur.execute(sql, params or [])
        else:
            cur.executescript(sql)
    except sqlite3.Error as e:
        print(f"[ERROR] {desc}: {e}")
        raise

    elapsed = time.time() - t0
    if is_select_like:
        rows = cur.fetchall() if fetch_all else cur.fetchmany(preview)
        print(f"[OK] {desc} in {elapsed:.3f}s. Preview {len(rows)} row(s):")
        for r in rows:
            print(r)
        return rows
    else:
        print(f"[OK] {desc} in {elapsed:.3f}s.")
        return None


def scalar(conn, sql, params=None):
    cur = conn.execute(sql, params or [])
    r = cur.fetchone()
    return r[0] if r and r[0] is not None else 0

def corr_sql(x_col):
    # Pearson correlation of x_col in pairs view vs math_prof_rate, per school
    return dedent(f"""
    WITH stats AS (
      SELECT
        ENTITY_CD,
        COUNT(*) AS n,
        SUM({x_col}) AS sumx,
        SUM(math_prof_rate) AS sumy,
        SUM({x_col} * math_prof_rate) AS sumxy,
        SUM({x_col} * {x_col}) AS sumx2,
        SUM(math_prof_rate * math_prof_rate) AS sumy2
      FROM pairs
      WHERE {x_col} IS NOT NULL AND math_prof_rate IS NOT NULL
      GROUP BY ENTITY_CD
    )
    SELECT
      s.ENTITY_CD,
      CASE
        WHEN (s.n * s.sumx2 - s.sumx * s.sumx) <= 0
          OR (s.n * s.sumy2 - s.sumy * s.sumy) <= 0
          THEN NULL
        ELSE (s.n * s.sumxy - s.sumx * s.sumy)
             / sqrt( (s.n * s.sumx2 - s.sumx * s.sumx)
                   * (s.n * s.sumy2 - s.sumy * s.sumy) )
      END AS r_{x_col}
    FROM stats s
    """).strip()
def main():
  import time, statistics

  def nearest_rank_percentile(values, p):
    # values must be non-empty, already sorted
    # p in [0, 100], returns nearest-rank percentile (Excel-style)
    if not values:
        return None
    if p <= 0:
        return values[0]
    if p >= 100:
        return values[-1]
    k = int((p/100.0) * len(values))
    # nearest-rank: rank = ceil(p*N); convert to 0-based index
    from math import ceil
    idx = max(0, min(len(values)-1, ceil(p/100.0 * len(values)) - 1))
    return values[idx]

  ap = argparse.ArgumentParser()
  ap.add_argument("--src", default="C:/Users/alexr/Documents/Fall 2025/ECE 501/ECE-501-Project/data/sqlite/src2024.db")
  ap.add_argument("--enr", default="C:/Users/alexr/Documents/Fall 2025/ECE 501/ECE-501-Project/data/sqlite/enrollment2024.db")
  ap.add_argument("--year", type=int, default=2024)
  ap.add_argument("--preview", type=int, default=5)
  ap.add_argument("--runs", type=int, default=15, help="Repeated runs per input size")
  args = ap.parse_args()
  year = int(args.year)

  overall_t0 = time.time()

  print("[INFO] Connecting to in-memory workspace")
  conn = sqlite3.connect(":memory:")
  conn.execute("PRAGMA temp_store=MEMORY;")
  conn.execute("PRAGMA cache_size=-64000;")
  conn.execute("PRAGMA journal_mode=OFF;")
  conn.execute("PRAGMA synchronous=OFF;")
  conn.row_factory = None

  run(conn, f"ATTACH '{args.src}' AS src;", "Attach src")
  run(conn, f"ATTACH '{args.enr}' AS enr;", "Attach enr")

  # Static demo slice
  run(conn, """
    DROP VIEW IF EXISTS demo;
    CREATE TEMP VIEW demo AS
    SELECT
      d.ENTITY_CD AS entity_cd,
      CAST(d.YEAR AS INTEGER) AS year,
      CAST(d.PER_ELL   AS REAL) AS per_ell,
      CAST(d.PER_SWD   AS REAL) AS per_swd,
      CAST(d.PER_ECDIS AS REAL) AS per_ecdis,
      CAST(d.PER_BLACK AS REAL) AS per_black,
      CAST(d.PER_HISP  AS REAL) AS per_hisp,
      CAST(d.PER_ASIAN AS REAL) AS per_asian,
      CAST(d.PER_WHITE AS REAL) AS per_white
    FROM enr."Demographic Factors" d;
  """, "Create view demo")

  # Input sizes and total available rows
  sizes = [10_000, 50_000, 100_000, 200_000, 400_000, 600_000]  
  total_rows = scalar(conn, 'SELECT COUNT(*) FROM src."Annual EM MATH";')
  print(f"[INFO] Available rows in src.\"Annual EM MATH\": {total_rows}")

  summary = []  # list of dicts per size

  for n in sizes:
    n_eff = min(n, total_rows)
    print(f"\n[INFO] Benchmarking on first {n_eff} rows with {args.runs} runs")

    latencies = []

    for r in range(1, args.runs + 1):
      # Reset temp objects each run to avoid reuse artifacts
      run(conn, """
        DROP VIEW IF EXISTS pairs_year;
        DROP VIEW IF EXISTS math_outcome;
        DROP VIEW IF EXISTS math_overall;
        DROP TABLE IF EXISTS math_src;
      """, f"Reset temp objects (run {r}/{args.runs})")

      t0 = time.time()

      # Limit source to first N rows
      run(conn, f"""
        CREATE TEMP TABLE math_src AS
        SELECT *
        FROM src."Annual EM MATH"
        LIMIT {n_eff};
      """, f"Create math_src ({n_eff} rows) [run {r}]")

      # Outcome: All Students, any MATH assessment, by school and year
      run(conn, """
        CREATE TEMP VIEW math_overall AS
        SELECT
          m.ENTITY_CD AS entity_cd,
          CAST(m.YEAR AS INTEGER) AS year,
          SUM(CAST(NULLIF(REPLACE(m.NUM_PROF,   ',', ''), '') AS INTEGER)) AS num_prof,
          SUM(CAST(NULLIF(REPLACE(m.NUM_TESTED, ',', ''), '') AS INTEGER)) AS num_tested
        FROM math_src m
        WHERE TRIM(UPPER(m.SUBGROUP_NAME)) LIKE 'ALL STUDENTS%'
          AND UPPER(m.ASSESSMENT_NAME) LIKE '%MATH%'
        GROUP BY m.ENTITY_CD, CAST(m.YEAR AS INTEGER);
      """, f"Create view math_overall [run {r}]")

      run(conn, """
        CREATE TEMP VIEW math_outcome AS
        SELECT
          entity_cd,
          year,
          CASE WHEN num_tested > 0 THEN 1.0 * num_prof / num_tested END AS math_prof_rate
        FROM math_overall;
      """, f"Create view math_outcome [run {r}]")

      # Cross-sectional pairs for chosen year
      run(conn, f"""
        CREATE TEMP VIEW pairs_year AS
        SELECT
          o.entity_cd,
          o.year,
          o.math_prof_rate,
          d.per_ell,
          d.per_swd,
          d.per_ecdis,
          d.per_black,
          d.per_hisp,
          d.per_asian,
          d.per_white
        FROM math_outcome o
        JOIN demo d
          ON d.entity_cd = o.entity_cd AND d.year = o.year
        WHERE o.year = {year}
          AND o.math_prof_rate IS NOT NULL;
      """, f"Create view pairs_year for {year} [run {r}]")

      # Correlations
      corr_sql = """
      WITH base AS (
        SELECT
          math_prof_rate,
          per_ell, per_swd, per_ecdis, per_black, per_hisp, per_asian, per_white
        FROM pairs_year
        WHERE math_prof_rate IS NOT NULL
      ),
      stats AS (
        SELECT
          COUNT(*) AS n,
          SUM(math_prof_rate) AS sumy,
          SUM(math_prof_rate * math_prof_rate) AS sumy2
        FROM base
      ),
      s_ell AS (
        SELECT 'per_ell' AS var, COUNT(*) n,
                SUM(per_ell) sumx, SUM(per_ell*per_ell) sumx2,
                SUM(per_ell*math_prof_rate) sumxy
        FROM base WHERE per_ell IS NOT NULL
      ),
      s_swd AS (
        SELECT 'per_swd', COUNT(*), SUM(per_swd), SUM(per_swd*per_swd), SUM(per_swd*math_prof_rate)
        FROM base WHERE per_swd IS NOT NULL
      ),
      s_ecdis AS (
        SELECT 'per_ecdis', COUNT(*), SUM(per_ecdis), SUM(per_ecdis*per_ecdis), SUM(per_ecdis*math_prof_rate)
        FROM base WHERE per_ecdis IS NOT NULL
      ),
      s_black AS (
        SELECT 'per_black', COUNT(*), SUM(per_black), SUM(per_black*per_black), SUM(per_black*math_prof_rate)
        FROM base WHERE per_black IS NOT NULL
      ),
      s_hisp AS (
        SELECT 'per_hisp', COUNT(*), SUM(per_hisp), SUM(per_hisp*per_hisp), SUM(per_hisp*math_prof_rate)
        FROM base WHERE per_hisp IS NOT NULL
      ),
      s_asian AS (
        SELECT 'per_asian', COUNT(*), SUM(per_asian), SUM(per_asian*per_asian), SUM(per_asian*math_prof_rate)
        FROM base WHERE per_asian IS NOT NULL
      ),
      s_white AS (
        SELECT 'per_white', COUNT(*), SUM(per_white), SUM(per_white*per_white), SUM(per_white*math_prof_rate)
        FROM base WHERE per_white IS NOT NULL
      ),
      allstats AS (
        SELECT * FROM s_ell
        UNION ALL SELECT * FROM s_swd
        UNION ALL SELECT * FROM s_ecdis
        UNION ALL SELECT * FROM s_black
        UNION ALL SELECT * FROM s_hisp
        UNION ALL SELECT * FROM s_asian
        UNION ALL SELECT * FROM s_white
      )
      SELECT
        a.var,
        a.n,
        CASE
          WHEN (a.n * a.sumx2 - a.sumx * a.sumx) <= 0
            OR (s.n * s.sumy2 - s.sumy * s.sumy) <= 0
            THEN NULL
          ELSE (a.n * a.sumxy - a.sumx * s.sumy)
                / sqrt( (a.n * a.sumx2 - a.sumx * a.sumx)
                      * (s.n * s.sumy2 - s.sumy * s.sumy) )
        END AS r,
        CASE
          WHEN (a.n * a.sumx2 - a.sumx * a.sumx) = 0
            THEN NULL
          ELSE (a.n * a.sumxy - a.sumx * s.sumy)
                / (a.n * a.sumx2 - a.sumx * a.sumx)
        END AS slope
      FROM allstats a
      CROSS JOIN stats s
      ORDER BY ABS(r) DESC;
      """
      run(conn, corr_sql, f"Correlations for {year} on {n_eff} rows [run {r}]", fetch_all=True)

      elapsed = time.time() - t0
      latencies.append(elapsed)
      print(f"[RESULT] Rows={n_eff} Run={r}/{args.runs} Time={elapsed:.3f}s")

      # Light cleanup and hint to engine
      conn.execute("PRAGMA optimize;")
      conn.execute("PRAGMA shrink_memory;")

    latencies.sort()
    p50 = statistics.median(latencies)
    p95 = nearest_rank_percentile(latencies, 95)
    summary.append({"rows": n_eff, "runs": args.runs, "p50": p50, "p95": p95})

    print(f"[SUMMARY] Rows={n_eff} P50={p50:.3f}s P95={p95:.3f}s")

  total_time = time.time() - overall_t0
  output_path = r"final-project\\experiments\\original_data\\query1\results.csv"  # <-- replace with your actual path

  print("\n[FINAL SUMMARY]")
  for row in summary:
      print(f"  {row['rows']:>7,d} rows | runs={row['runs']:2d} | P50={row['p50']:.3f}s | P95={row['p95']:.3f}s")

  # Save to CSV
  with open(output_path, mode="w", newline="") as f:
      writer = csv.writer(f)
      writer.writerow(["rows", "runs", "P50_seconds", "P95_seconds", "total_wall_time_seconds"])
      for row in summary:
          writer.writerow([row["rows"], row["runs"], f"{row['p50']:.6f}", f"{row['p95']:.6f}", f"{total_time:.6f}"])

  print(f"\n[INFO] Results saved to {output_path}")
  print(f"[INFO] Done. Total wall time: {total_time:.2f}s")



if __name__ == "__main__":
    main()