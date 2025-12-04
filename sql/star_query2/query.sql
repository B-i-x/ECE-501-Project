WITH math_src AS (
    SELECT
        fa.school_key,
        fa.tested,
        fa.n_qual
    FROM fact_assessment AS fa
    JOIN dim_subject  AS subj ON fa.subject_key  = subj.subject_key
    JOIN dim_subgroup AS sg   ON fa.subgroup_key = sg.subgroup_key
    WHERE fa.year_key       = 2024                
      AND subj.subject_name = 'Mathematics'        
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
att_src AS (
    SELECT
        fa.school_key,
        fa.absence_rate,
        fa.enrollment
    FROM fact_attendance AS fa
    JOIN dim_subgroup AS sg ON fa.subgroup_key = sg.subgroup_key
    WHERE fa.year_key      = 2024
      AND sg.subgroup_name = 'All Students'
    LIMIT CAST(:n_limit AS INTEGER)
),
att_school AS (
    SELECT
        school_key,
        CASE
            WHEN SUM(enrollment) > 0
            THEN SUM(absence_rate * enrollment) / SUM(enrollment)
            ELSE NULL
        END AS absence_rate,
        CASE
            WHEN SUM(enrollment) > 0
            THEN 100.0 - (SUM(absence_rate * enrollment) / SUM(enrollment))
            ELSE NULL
        END AS attendance_rate
    FROM att_src
    GROUP BY school_key
),
pairs AS (
    SELECT
        a.school_key,
        a.attendance_rate,
        m.math_prof_rate
    FROM att_school AS a
    JOIN math_school AS m
      ON a.school_key = m.school_key
    WHERE a.attendance_rate IS NOT NULL11
      AND a.attendance_rate > 0
      AND m.math_prof_rate IS NOT NULL
      AND m.math_prof_rate > 0
)
SELECT
    s.school_id,
    s.school_name,
    p.attendance_rate,
    p.math_prof_rate
FROM pairs AS p
JOIN dim_school AS s
  ON s.school_key = p.school_key
ORDER BY s.school_id
LIMIT CAST(:n_limit AS INTEGER);