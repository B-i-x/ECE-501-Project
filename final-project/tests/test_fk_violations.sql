SELECT 'orphan enrollment.school_key', COUNT(*)
FROM fact_enrollment fe LEFT JOIN dim_school s USING(school_key)
WHERE s.school_key IS NULL;
