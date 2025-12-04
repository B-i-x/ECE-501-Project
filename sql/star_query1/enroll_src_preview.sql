SELECT
    fe.year_key,
    fe.school_key,
    fe.subgroup_key,
    fe.n_students
FROM fact_enrollment AS fe
WHERE fe.year_key = 2024           -- change to 2024 when available
LIMIT CAST(:n_limit AS INTEGER);
