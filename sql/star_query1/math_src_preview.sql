SELECT
    fa.year_key,
    fa.school_key,
    fa.tested,
    fa.n_qual
FROM fact_assessment AS fa
JOIN dim_subject  AS subj ON fa.subject_key  = subj.subject_key
JOIN dim_subgroup AS sg   ON fa.subgroup_key = sg.subgroup_key
WHERE fa.year_key        = 2024        -- change to 2024 when that data exists
  AND subj.subject_name  = 'Mathematics'
  AND sg.subgroup_name   = 'All Students'
LIMIT CAST(:n_limit AS INTEGER);