WITH math_src AS (
    SELECT
        fa.school_key,
        fa.tested,
        fa.n_qual
    FROM fact_assessment AS fa
    JOIN dim_subject  AS subj ON fa.subject_key  = subj.subject_key
    JOIN dim_subgroup AS sg   ON fa.subgroup_key = sg.subgroup_key
    WHERE fa.year_key        = 2024        -- change to 2024 later
      AND subj.subject_name  = 'Mathematics'
      AND sg.subgroup_name   = 'All Students'
    LIMIT CAST(:n_limit AS INTEGER)
)
SELECT
    school_key,
    SUM(n_qual) AS total_qual,
    SUM(tested) AS total_tested,
    CASE
        WHEN SUM(tested) > 0
        THEN 100.0 * SUM(n_qual) / SUM(tested)
        ELSE NULL
    END AS math_prof_rate
FROM math_src
GROUP BY school_key
LIMIT CAST(:n_limit AS INTEGER);
