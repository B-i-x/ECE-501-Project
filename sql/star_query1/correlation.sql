WITH math_school AS (
    SELECT
        fa.school_key,
        SUM(fa.n_qual) AS total_qual,
        SUM(fa.tested) AS total_tested,
        CASE
            WHEN SUM(fa.tested) > 0
            THEN 100.0 * SUM(fa.n_qual) / SUM(fa.tested)
            ELSE NULL
        END AS math_prof_rate
    FROM fact_assessment AS fa
    JOIN dim_subject  AS subj ON fa.subject_key  = subj.subject_key
    JOIN dim_subgroup AS sg   ON fa.subgroup_key = sg.subgroup_key
    WHERE fa.year_key        = 2024       -- change to 2024 later
      AND subj.subject_name  = 'Mathematics'
      AND sg.subgroup_name   = 'All Students'
    GROUP BY fa.school_key
    LIMIT CAST(:n_limit AS INTEGER)
),
enroll_src AS (
    SELECT
        fe.school_key,
        fe.subgroup_key,
        fe.n_students
    FROM fact_enrollment AS fe
    WHERE fe.year_key = 2024       -- change to 2024 later
    LIMIT CAST(:n_limit AS INTEGER)
),
enroll_with_names AS (
    SELECT
        e.school_key,
        sg.subgroup_name,
        e.n_students
    FROM enroll_src AS e
    JOIN dim_subgroup AS sg ON e.subgroup_key = sg.subgroup_key
),
school_totals AS (
    SELECT
        school_key,
        SUM(n_students) AS total_students
    FROM enroll_with_names
    GROUP BY school_key
),
composition AS (
    SELECT
        e.school_key,
        e.subgroup_name,
        e.n_students,
        t.total_students,
        CASE
            WHEN t.total_students > 0
            THEN 1.0 * e.n_students / t.total_students
            ELSE NULL
        END AS subgroup_share
    FROM enroll_with_names AS e
    JOIN school_totals AS t
      ON e.school_key = t.school_key
),
pairs AS (
    SELECT
        c.subgroup_name,
        c.subgroup_share,
        m.math_prof_rate
    FROM composition AS c
    JOIN math_school AS m
      ON c.school_key = m.school_key
    WHERE c.subgroup_share IS NOT NULL
      AND m.math_prof_rate IS NOT NULL
)

SELECT
    subgroup_name,
    (
        AVG(subgroup_share * math_prof_rate)
        - AVG(subgroup_share) * AVG(math_prof_rate)
    )
    /
    (
        SQRT(
            AVG(subgroup_share * subgroup_share)
            - AVG(subgroup_share) * AVG(subgroup_share)
        )
        *
        SQRT(
            AVG(math_prof_rate * math_prof_rate)
            - AVG(math_prof_rate) * AVG(math_prof_rate)
        )
    ) AS correlation
FROM pairs
GROUP BY subgroup_name
HAVING COUNT(*) > 1
ORDER BY correlation DESC;
