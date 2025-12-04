WITH enroll_src AS (
    SELECT
        fe.school_key,
        fe.subgroup_key,
        fe.n_students
    FROM fact_enrollment AS fe
    WHERE fe.year_key = 2023       -- change to 2024 later
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
)
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
LIMIT CAST(:n_limit AS INTEGER);
