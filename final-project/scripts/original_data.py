#!/usr/bin/env python3
import sqlite3
import argparse
import time
from textwrap import dedent

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="C:/Users/alexr/Documents/Fall 2025/ECE 501/ECE-501-Project/data/sqlite/src2024.db")
    ap.add_argument("--enr", default="C:/Users/alexr/Documents/Fall 2025/ECE 501/ECE-501-Project/data/sqlite/enrollment2024.db")
    ap.add_argument("--preview", type=int, default=5)
    args = ap.parse_args()

    print("[INFO] Connecting to in-memory workspace")
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-64000;")
    conn.row_factory = None  # tuples for speed and simple printing

    # Attach databases
    run(conn, f"ATTACH '{args.src}' AS src;", "Attach src")
    run(conn, f"ATTACH '{args.enr}' AS enr;", "Attach enr")

    run(conn, dedent("""
        SELECT COUNT(*) AS n FROM src."Annual EM MATH";
    """), "Count rows in Annual EM MATH")
    n1 = scalar(conn, "SELECT COUNT(*) AS n FROM src.\"Annual EM MATH\";")
    print(f"[DEBUG] Annual EM MATH rows: {n1}")


    # Step: Print distinct subgroup names with actual values
    print("\n[INFO] Listing distinct SUBGROUP_NAME values in Annual EM MATH:")
    subgroups = run(conn, dedent("""
        SELECT DISTINCT TRIM(SUBGROUP_NAME) AS subgroup
        FROM src."Annual EM MATH"
        ORDER BY subgroup;
    """), "Subgroup list", preview=100, fetch_all=True)

    print(f"[DEBUG] Total distinct subgroups: {len(subgroups)}\n")
    for sg in subgroups:
        print(" -", sg[0])



    run(conn, dedent("""
        SELECT DISTINCT ASSESSMENT_NAME
        FROM src."Annual EM MATH"
        ORDER BY 1
        LIMIT 50;
    """), "Distinct assessments in Annual EM MATH")
    n1 = scalar(conn, "SELECT COUNT(DISTINCT ASSESSMENT_NAME) FROM src.\"Annual EM MATH\";")
    print(f"[DEBUG] Distinct assessments in Annual EM MATH: {n1}")


    # Step 1. Build math_overall view for All Students, grades 3 to 8
    run(conn, dedent("""
      DROP VIEW IF EXISTS math_overall;
      CREATE TEMP VIEW math_overall AS
      SELECT
        m.ENTITY_CD AS entity_cd,
        CAST(m.YEAR AS INTEGER) AS year,
        SUM(CAST(m.NUM_PROF AS INTEGER)) AS num_prof,
        SUM(CAST(m.NUM_TESTED AS INTEGER)) AS num_tested
      FROM src."Annual EM MATH" m
      WHERE m.ASSESSMENT_NAME LIKE 'Grade %'
        AND m.SUBGROUP_NAME = 'All Students'
      GROUP BY m.ENTITY_CD, CAST(m.YEAR AS INTEGER);
    """), "Create view math_overall")

    n1 = scalar(conn, "SELECT COUNT(*) FROM math_overall;")
    print(f"[DEBUG] math_overall rows: {n1}")
    run(conn, "SELECT * FROM math_overall ORDER BY entity_cd, year LIMIT ?;", "Preview math_overall", args.preview, params=[args.preview])

    # Step 2. Outcome view math_outcome with proficiency rate
    run(conn, dedent("""
      DROP VIEW IF EXISTS math_outcome;
      CREATE TEMP VIEW math_outcome AS
      SELECT
        entity_cd,
        year,
        CASE WHEN num_tested > 0 THEN 1.0 * num_prof / num_tested ELSE NULL END AS math_prof_rate
      FROM math_overall;
    """), "Create view math_outcome")

    n2 = scalar(conn, "SELECT COUNT(*) FROM math_outcome;")
    print(f"[DEBUG] math_outcome rows: {n2}")
    run(conn, "SELECT * FROM math_outcome ORDER BY entity_cd, year LIMIT ?;", "Preview math_outcome", args.preview, params=[args.preview])

    # Step 3. Demographic slice
    run(conn, dedent("""
      DROP VIEW IF EXISTS demo;
      CREATE TEMP VIEW demo AS
      SELECT
        d.ENTITY_CD AS entity_cd,
        CAST(d.YEAR AS INTEGER) AS year,
        CAST(d.PER_ELL AS REAL)   AS per_ell,
        CAST(d.PER_SWD AS REAL)   AS per_swd,
        CAST(d.PER_ECDIS AS REAL) AS per_ecdis,
        CAST(d.PER_BLACK AS REAL) AS per_black,
        CAST(d.PER_HISP AS REAL)  AS per_hisp,
        CAST(d.PER_ASIAN AS REAL) AS per_asian,
        CAST(d.PER_WHITE AS REAL) AS per_white
      FROM enr."Demographic Factors" d;
    """), "Create view demo")

    n3 = scalar(conn, "SELECT COUNT(*) FROM demo;")
    print(f"[DEBUG] demo rows: {n3}")
    run(conn, "SELECT * FROM demo ORDER BY entity_cd, year LIMIT ?;", "Preview demo", args.preview, params=[args.preview])

    # Step 4. Join pairs of demo with outcome
    run(conn, dedent("""
      DROP VIEW IF EXISTS pairs;
      CREATE TEMP VIEW pairs AS
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
      JOIN demo d ON d.entity_cd = o.entity_cd AND d.year = o.year;
    """), "Create view pairs")

    n4 = scalar(conn, "SELECT COUNT(*) FROM pairs;")
    print(f"[DEBUG] pairs rows: {n4}")
    run(conn, "SELECT * FROM pairs ORDER BY entity_cd, year LIMIT ?;", "Preview pairs", args.preview, params=[args.preview])

    # Step 5. Correlations per school for each subgroup percentage vs math_prof_rate
    fields = ["per_ell", "per_swd", "per_ecdis", "per_black", "per_hisp", "per_asian", "per_white"]

    # Build individual temp tables for each correlation so we can inspect easily
    for f in fields:
        run(conn, f"DROP TABLE IF EXISTS corr_{f};", f"Drop corr_{f}")
        sql = f"CREATE TEMP TABLE corr_{f} AS {corr_sql(f)};"
        run(conn, sql, f"Create corr_{f}")
        cnt = scalar(conn, f"SELECT COUNT(*) FROM corr_{f};")
        print(f"[DEBUG] corr_{f} rows: {cnt}")
        run(conn, f"SELECT * FROM corr_{f} ORDER BY entity_cd LIMIT ?;", f"Preview corr_{f}", args.preview, params=[args.preview])

    # Step 6. Join all correlations into one summary
    run(conn, dedent("""
      DROP TABLE IF EXISTS corr_summary;
      CREATE TEMP TABLE corr_summary AS
      SELECT
        e.entity_cd,
        e.r_per_ell,
        s.r_per_swd,
        ec.r_per_ecdis,
        b.r_per_black,
        h.r_per_hisp,
        a.r_per_asian,
        w.r_per_white
      FROM corr_per_ell e
      LEFT JOIN corr_per_swd s   ON s.entity_cd = e.entity_cd
      LEFT JOIN corr_per_ecdis ec ON ec.entity_cd = e.entity_cd
      LEFT JOIN corr_per_black b  ON b.entity_cd = e.entity_cd
      LEFT JOIN corr_per_hisp h   ON h.entity_cd = e.entity_cd
      LEFT JOIN corr_per_asian a  ON a.entity_cd = e.entity_cd
      LEFT JOIN corr_per_white w  ON w.entity_cd = e.entity_cd;
    """).replace("corr_per_", "corr_"), "Create corr_summary")

    nsum = scalar(conn, "SELECT COUNT(*) FROM corr_summary;")
    print(f"[DEBUG] corr_summary rows: {nsum}")
    run(conn, "SELECT * FROM corr_summary ORDER BY entity_cd LIMIT ?;", "Preview corr_summary", args.preview, params=[args.preview])

    # Optional: show top magnitude correlations for a quick sanity check
    run(conn, dedent("""
      SELECT entity_cd, r_per_ell
      FROM corr_summary
      WHERE r_per_ell IS NOT NULL
      ORDER BY ABS(r_per_ell) DESC
      LIMIT 10;
    """), "Top 10 by |r_per_ell|", args.preview)

    print("[INFO] Done")

if __name__ == "__main__":
    main()
