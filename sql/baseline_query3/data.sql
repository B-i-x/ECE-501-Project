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
exp_src AS (
    SELECT *
    FROM reportcard_database_23_24."Expenditures per Pupil"
    WHERE YEAR = 2024
      AND DATA_REPORTED_EXP = 'Y'
      AND DATA_REPORTED_ENR = 'Y'
    LIMIT CAST(:n_limit AS INTEGER)
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
