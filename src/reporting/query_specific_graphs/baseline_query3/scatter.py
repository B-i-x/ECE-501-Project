import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import pearsonr

from execute.sql import create_sqlite_conn_for_spec
from app.queries import QuerySpec

EXPENDITURES_MATH_SQL = """
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
),
exp_src AS (
    SELECT *
    FROM reportcard_database_23_24."Expenditures per Pupil"
    WHERE YEAR = 2024
      AND DATA_REPORTED_EXP = 'Y'
      AND DATA_REPORTED_ENR = 'Y'
)

SELECT
    e.ENTITY_CD,
    e.ENTITY_NAME,
    e.PER_FED_STATE_LOCAL_EXP      AS per_pupil_expenditure,
    m.math_prof_rate               AS math_prof_rate
FROM exp_src AS e
JOIN math_school AS m
  ON e.ENTITY_CD = m.ENTITY_CD
 AND e.YEAR      = m.YEAR
WHERE e.ENTITY_NAME NOT LIKE '% SD'
  AND e.PER_FED_STATE_LOCAL_EXP IS NOT NULL
  AND e.PER_FED_STATE_LOCAL_EXP > 0
  AND m.math_prof_rate IS NOT NULL
  AND m.math_prof_rate > 0;
"""


def fetch_expenditure_math_points(conn: sqlite3.Connection):
    """
    Returns list of (entity_cd, entity_name, per_pupil_exp, math_prof_rate).
    """
    cur = conn.cursor()
    cur.execute(EXPENDITURES_MATH_SQL)
    rows = cur.fetchall()
    cur.close()

    n = len(rows)
    print(f"Number of schools in dataset: {n}")

    return rows


def plot_expenditure_vs_math_from_spec(spec: QuerySpec):
    # Build the attached in-memory connection
    conn = create_sqlite_conn_for_spec(spec)
    rows = fetch_expenditure_math_points(conn)
    conn.close()

    per_pupil = np.array([r[2] for r in rows], dtype=float)
    math_prof = np.array([r[3] for r in rows], dtype=float)

    # Optionally clip extreme expenditure outliers (e.g., top 1%)
    upper_cap = np.percentile(per_pupil, 99)
    mask = per_pupil <= upper_cap
    per_pupil_clipped = per_pupil[mask]
    math_prof_clipped = math_prof[mask]

    print(f"Using {per_pupil_clipped.size} schools after clipping extreme expenditures")

    # Correlation on the clipped data
    corr, p_value = pearsonr(per_pupil_clipped, math_prof_clipped)
    print("Correlation (per-pupil vs math prof):", corr)
    print("p-value:", p_value)

    # Fit a simple linear regression line y = a*x + b
    a, b = np.polyfit(per_pupil_clipped, math_prof_clipped, 1)
    x_line = np.linspace(per_pupil_clipped.min(), per_pupil_clipped.max(), 200)
    y_line = a * x_line + b

    plt.figure(figsize=(8, 6))

    # Scatter plot
    plt.scatter(per_pupil_clipped, math_prof_clipped, alpha=0.4, s=10)
    plt.plot(x_line, y_line, linewidth=2)  # regression line (default color)

    plt.xlabel("Per-pupil expenditure (federal + state + local) ($)")
    plt.ylabel("Math proficiency rate (%)")
    plt.title(
        f"{spec.name} v{spec.version} – Expenditures vs Math Proficiency (2024)\n"
        f"r = {corr:.3f}, p = {p_value:.2e}"
    )
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Replace with the actual QuerySpec you’re using for this query
    from app.queries import BASELINE_QUERY_3  # example placeholder
    plot_expenditure_vs_math_from_spec(BASELINE_QUERY_3)
