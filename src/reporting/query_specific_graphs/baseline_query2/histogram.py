import matplotlib.pyplot as plt
import sqlite3
import numpy as np
from scipy.stats import pearsonr
from execute.sql import create_sqlite_conn_for_spec
from app.queries import QuerySpec

ATTENDANCE_MATH_SQL = """
WITH math_school AS (
    SELECT
        ENTITY_CD,
        YEAR,
        SUM(CAST(NUM_PROF AS REAL))    AS total_prof,
        SUM(CAST(TOTAL_COUNT AS REAL)) AS total_tested,
        CASE
            WHEN SUM(CAST(TOTAL_COUNT AS REAL)) > 0
            THEN 100.0 * SUM(CAST(NUM_PROF AS REAL))
                       / SUM(CAST(TOTAL_COUNT AS REAL))
            ELSE NULL
        END AS math_prof_rate
    FROM reportcard_database_23_24."Annual EM MATH"
    WHERE YEAR = 2024
      AND SUBGROUP_NAME = 'All Students'
    GROUP BY ENTITY_CD, YEAR
)
SELECT
    a.ENTITY_CD,
    a.ENTITY_NAME,
    a.ATTENDANCE_RATE,
    m.math_prof_rate
FROM student_educator_database_23_24.Attendance AS a
JOIN math_school AS m
  ON a.ENTITY_CD = m.ENTITY_CD
 AND a.YEAR      = m.YEAR
WHERE a.YEAR = 2024
  AND a.ENTITY_NAME NOT LIKE '% SD'
  AND m.math_prof_rate IS NOT NULL
  AND m.math_prof_rate > 0
  AND a.ATTENDANCE_RATE IS NOT NULL
  AND a.ATTENDANCE_RATE > 0;
"""



def fetch_attendance_math_points(conn: sqlite3.Connection):
    """
    Returns list of (entity_cd, entity_name, attendance_rate, math_prof_rate).
    """
    cur = conn.cursor()
    cur.execute(ATTENDANCE_MATH_SQL)
    rows = cur.fetchall()
    cur.close()

    n = len(rows)
    print(f"Number of schools in dataset: {n}")

    return rows

import matplotlib.pyplot as plt

def plot_attendance_vs_math_from_spec(spec: QuerySpec):
    # Build the attached in memory connection
    conn = create_sqlite_conn_for_spec(spec)
    rows = fetch_attendance_math_points(conn)
    conn.close()

    attendance = [r[2] for r in rows]
    math_prof  = [r[3] for r in rows]


    corr, p_value = pearsonr(attendance, math_prof)
    print("Correlation:", corr)
    print("p-value:", p_value)

    plt.figure(figsize=(7, 5))
    # 2D histogram: x = attendance, y = math proficiency
    plt.hist2d(attendance, math_prof, bins=[100, 100])
    plt.colorbar(label="Number of schools")

    plt.xlabel("Attendance rate (%)")
    plt.ylabel("Math proficiency rate (%)")
    plt.title(f"{spec.name} v{spec.version} - Attendance vs Math Proficiency (2024)")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    from app.queries import BASELINE_QUERY_2_V1  # or whichever spec you want
    plot_attendance_vs_math_from_spec(BASELINE_QUERY_2_V1)