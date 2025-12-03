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
  AND a.ENTITY_NAME NOT LIKE '% SD';