-- Query 1 Star Schema: Calculate demographic percentages from assessment data
-- This replaces demo_view.sql which used baseline "Demographic Factors" table
-- Calculates PER_ELL, PER_SWD, PER_ECDIS, PER_BLACK, PER_HISP, PER_ASIAN, PER_WHITE
-- as percentages of total tested students per school/year
-- Note: Uses assessment data because enrollment data only has "All Students" subgroup

DROP VIEW IF EXISTS demo;
CREATE TEMP VIEW demo AS
WITH total_tested AS (
  -- Get total tested students (All Students subgroup) per school/year
  SELECT
    s.school_id AS entity_cd,
    y.year_key AS year,
    SUM(fa.tested) AS total_students
  FROM fact_assessment fa
  JOIN dim_school s ON s.school_key = fa.school_key
  JOIN dim_year y ON y.year_key = fa.year_key
  JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
  WHERE UPPER(TRIM(sg.subgroup_name)) LIKE 'ALL STUDENTS%'
  GROUP BY s.school_id, y.year_key
),
subgroup_tested AS (
  -- Get tested counts for each demographic subgroup per school/year
  SELECT
    s.school_id AS entity_cd,
    y.year_key AS year,
    sg.subgroup_id,
    SUM(fa.tested) AS subgroup_students
  FROM fact_assessment fa
  JOIN dim_school s ON s.school_key = fa.school_key
  JOIN dim_year y ON y.year_key = fa.year_key
  JOIN dim_subgroup sg ON sg.subgroup_key = fa.subgroup_key
  WHERE sg.subgroup_id IN ('ELL', 'SWD', 'ED', 'Black', 'Hispanic', 'Asian_NHPI', 'White')
  GROUP BY s.school_id, y.year_key, sg.subgroup_id
)
SELECT
  t.entity_cd,
  t.year,
  -- PER_ELL: English Language Learners
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'ELL' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_ell,
  -- PER_SWD: Students with Disabilities
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'SWD' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_swd,
  -- PER_ECDIS: Economically Disadvantaged
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'ED' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_ecdis,
  -- PER_BLACK: Black students
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'Black' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_black,
  -- PER_HISP: Hispanic students
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'Hispanic' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_hisp,
  -- PER_ASIAN: Asian or Native Hawaiian/Other Pacific Islander students
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'Asian_NHPI' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_asian,
  -- PER_WHITE: White students
  CASE WHEN t.total_students > 0
    THEN 100.0 * COALESCE(MAX(CASE WHEN se.subgroup_id = 'White' THEN se.subgroup_students END), 0) / t.total_students
    ELSE NULL
  END AS per_white
FROM total_tested t
LEFT JOIN subgroup_tested se ON se.entity_cd = t.entity_cd AND se.year = t.year
GROUP BY t.entity_cd, t.year, t.total_students;

