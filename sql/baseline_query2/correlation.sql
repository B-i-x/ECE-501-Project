WITH math_src AS (
    SELECT *
    FROM reportcard_database_23_24."Annual EM MATH"
    WHERE YEAR = 2024
      AND SUBGROUP_NAME = 'All Students'
    LIMIT CAST(:n_limit AS INTEGER)
),
math_school AS (
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
    FROM math_src
    GROUP BY ENTITY_CD, YEAR
),
att_src AS (
    SELECT *
    FROM student_educator_database_23_24.Attendance
    WHERE YEAR = 2024
    LIMIT CAST(:n_limit AS INTEGER)
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
    FROM att_src AS a
    JOIN math_school AS m
      ON a.ENTITY_CD = m.ENTITY_CD
     AND a.YEAR      = m.YEAR
    WHERE a.ENTITY_NAME NOT LIKE '% SD'
      AND m.math_prof_rate IS NOT NULL
);
