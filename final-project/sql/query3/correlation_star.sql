-- Query 3 Correlation: Expenditures vs Math Proficiency (Star Schema Version)

WITH math_school AS (
    SELECT
        s.school_id AS ENTITY_CD,
        y.year_key AS YEAR,
        AVG(fa.qual_rate) * 100.0 AS math_prof_rate
    FROM fact_assessment fa
    JOIN dim_school s ON s.school_key = fa.school_key
    JOIN dim_year y ON y.year_key = fa.year_key
    JOIN dim_subject subj ON subj.subject_key = fa.subject_key
    JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
    WHERE y.year_key = 2024
      AND subj.subject_id = 'Math'
      AND UPPER(TRIM(sg.subgroup_name)) LIKE 'ALL STUDENTS%'
    GROUP BY s.school_id, y.year_key
),
exp_school AS (
    SELECT
        s.school_id AS ENTITY_CD,
        s.school_name AS ENTITY_NAME,
        y.year_key AS YEAR,
        fe.per_pupil_expenditure AS per_pupil_expenditure
    FROM fact_expenditures fe
    JOIN dim_school s ON s.school_key = fe.school_key
    JOIN dim_year y ON y.year_key = fe.year_key
    WHERE y.year_key = 2024
      AND fe.data_reported_exp = 'Y'
      AND fe.data_reported_enr = 'Y'
      AND fe.per_pupil_expenditure IS NOT NULL
      AND fe.per_pupil_expenditure > 0
),
pairs AS (
    SELECT
        e.per_pupil_expenditure,
        m.math_prof_rate
    FROM exp_school AS e
    JOIN math_school AS m
      ON e.ENTITY_CD = m.ENTITY_CD
     AND e.YEAR = m.YEAR
    WHERE e.ENTITY_NAME NOT LIKE '% SD'
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

