WITH math_src AS (
    SELECT
        fa.school_key,
        fa.tested,
        fa.n_qual
    FROM fact_assessment AS fa
    JOIN dim_subject  AS subj ON fa.subject_key  = subj.subject_key
    JOIN dim_subgroup AS sg   ON fa.subgroup_key = sg.subgroup_key
    WHERE fa.year_key       = 2024
      AND subj.subject_name = 'Mathematics'     -- adjust if your math label differs
      AND sg.subgroup_name  = 'All Students'
    LIMIT CAST(:n_limit AS INTEGER)
),
math_school AS (
    SELECT
        school_key,
        SUM(n_qual)  AS total_prof,
        SUM(tested)  AS total_tested,
        CASE
            WHEN SUM(tested) > 0
            THEN 100.0 * SUM(n_qual) / SUM(tested)
            ELSE NULL
        END AS math_prof_rate
    FROM math_src
    GROUP BY school_key
),
exp_src AS (
    SELECT
        e.ENTITY_CD,
        e.ENTITY_NAME,
        e.YEAR,
        e.PER_FED_STATE_LOCAL_EXP
    FROM reportcard_database_23_24."Expenditures per Pupil" AS e
    WHERE e.YEAR = 2024
      AND e.DATA_REPORTED_EXP = 'Y'
      AND e.DATA_REPORTED_ENR = 'Y'
    LIMIT CAST(:n_limit AS INTEGER)
),
pairs AS (
    SELECT
        e.PER_FED_STATE_LOCAL_EXP AS per_pupil_expenditure,
        m.math_prof_rate          AS math_prof_rate
    FROM exp_src      AS e
    JOIN dim_school   AS s ON e.ENTITY_CD = s.school_id   -- adjust if school_id maps to INSTITUTION_ID instead
    JOIN math_school  AS m ON s.school_key = m.school_key
    WHERE e.ENTITY_NAME NOT LIKE '% SD'
      AND e.PER_FED_STATE_LOCAL_EXP IS NOT NULL
      AND e.PER_FED_STATE_LOCAL_EXP > 0
      AND m.math_prof_rate IS NOT NULL
      AND m.math_prof_rate > 0
)

SELECT
    (AVG(per_pupil_expenditure * math_prof_rate)
     - AVG(per_pupil_expenditure) * AVG(math_prof_rate))
    /
    (SQRT(AVG(per_pupil_expenditure * per_pupil_expenditure)
          - AVG(per_pupil_expenditure) * AVG(per_pupil_expenditure))
     *
     SQRT(AVG(math_prof_rate * math_prof_rate)
          - AVG(math_prof_rate) * AVG(math_prof_rate))
    ) AS correlation
FROM pairs;
