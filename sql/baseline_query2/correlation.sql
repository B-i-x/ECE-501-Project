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
    (AVG(attendance_rate * math_prof_rate)
     - AVG(attendance_rate) * AVG(math_prof_rate))
    /
    (SQRT(AVG(attendance_rate * attendance_rate)
          - AVG(attendance_rate) * AVG(attendance_rate))
     *
     SQRT(AVG(math_prof_rate * math_prof_rate)
          - AVG(math_prof_rate) * AVG(math_prof_rate))
    ) AS correlation
FROM (
    SELECT
        a.ATTENDANCE_RATE AS attendance_rate,
        m.math_prof_rate  AS math_prof_rate
    FROM student_educator_database_23_24.Attendance a
    JOIN math_school m
      ON a.ENTITY_CD = m.ENTITY_CD
     AND a.YEAR      = m.YEAR
    WHERE a.YEAR = 2024
      AND a.ENTITY_NAME NOT LIKE '% SD'
      AND m.math_prof_rate IS NOT NULL
);
