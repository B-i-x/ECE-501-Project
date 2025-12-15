-- =======================
-- Data Quality & QA Checks
-- Run: sqlite3 db/nysed.sqlite < sql/99_checks.sql
-- =======================

-- 0) Basic metadata
SELECT 'sqlite_version' AS k, sqlite_version() AS v;

-- 1) Orphan fact keys (FK integrity)
SELECT 'orphan school_key in fact_enrollment' AS "check", COUNT(*) n_bad
FROM fact_enrollment fe
LEFT JOIN dim_school s USING (school_key)
WHERE s.school_key IS NULL;

SELECT 'orphan school_key in fact_attendance' AS "check", COUNT(*) n_bad
FROM fact_attendance fa
LEFT JOIN dim_school s USING (school_key)
WHERE s.school_key IS NULL;

SELECT 'orphan school_key in fact_assessment' AS "check", COUNT(*) n_bad
FROM fact_assessment fa
LEFT JOIN dim_school s USING (school_key)
WHERE s.school_key IS NULL;

-- 2) Rates within [0,1]
SELECT 'bad absence_rate (not 0..1)' AS "check", COUNT(*) n_bad
FROM fact_attendance WHERE absence_rate IS NOT NULL AND (absence_rate<0 OR absence_rate>1);

SELECT 'bad qual_rate (not 0..1)' AS "check", COUNT(*) n_bad
FROM fact_assessment WHERE qual_rate IS NOT NULL AND (qual_rate<0 OR qual_rate>1);

-- 3) Nulls on required columns (grain keys)
SELECT 'NULLs in enrollment grain keys' AS "check", COUNT(*) n_bad
FROM fact_enrollment WHERE year_key IS NULL OR school_key IS NULL OR subgroup_key IS NULL;

SELECT 'NULLs in attendance grain keys' AS "check", COUNT(*) n_bad
FROM fact_attendance WHERE year_key IS NULL OR school_key IS NULL OR subgroup_key IS NULL;

SELECT 'NULLs in assessment grain keys' AS "check", COUNT(*) n_bad
FROM fact_assessment
WHERE year_key IS NULL OR school_key IS NULL OR subject_key IS NULL OR grade_key IS NULL OR subgroup_key IS NULL;

-- 4) Duplicate natural keys in dims
SELECT 'dup district_id' AS "check", district_id, COUNT(*) c
FROM dim_district GROUP BY district_id HAVING c>1;

SELECT 'dup school_id' AS "check", school_id, COUNT(*) c
FROM dim_school GROUP BY school_id HAVING c>1;

SELECT 'dup subgroup_id' AS "check", subgroup_id, COUNT(*) c
FROM dim_subgroup GROUP BY subgroup_id HAVING c>1;

-- 5) Consistency checks between counts and rates
-- qual_rate should roughly equal n_qual/tested (within tolerance)
WITH diffs AS (
  SELECT
    year_key, school_key, subject_key, grade_key, subgroup_key,
    tested, n_qual, qual_rate,
    CASE
      WHEN tested IS NOT NULL AND tested>0 AND n_qual IS NOT NULL AND qual_rate IS NOT NULL
      THEN ABS(qual_rate - (1.0*n_qual)/tested)
      ELSE NULL
    END AS delta
  FROM fact_assessment
)
SELECT 'qual_rate vs n_qual/tested | delta>0.02' AS "check", COUNT(*) n_bad
FROM diffs WHERE delta IS NOT NULL AND delta>0.02;

-- 6) Rowcount sanity by year (quick glance)
SELECT 'enrollment rows by year' AS "check", y.year_key, COUNT(*) n
FROM fact_enrollment fe JOIN dim_year y USING (year_key)
GROUP BY y.year_key ORDER BY y.year_key;

SELECT 'attendance rows by year' AS "check", y.year_key, COUNT(*) n
FROM fact_attendance fa JOIN dim_year y USING (year_key)
GROUP BY y.year_key ORDER BY y.year_key;

SELECT 'assessment rows by year' AS "check", y.year_key, COUNT(*) n
FROM fact_assessment fa JOIN dim_year y USING (year_key)
GROUP BY y.year_key ORDER BY y.year_key;

-- 7) Schools without a district (should be none)
SELECT 'schools missing district' AS "check", COUNT(*) n_bad
FROM dim_school s LEFT JOIN dim_district d ON d.district_key=s.district_key
WHERE d.district_key IS NULL;

-- 9) Expenditures data quality
SELECT 'expenditures with NULL per_pupil_expenditure' AS "check", COUNT(*) n_bad
FROM fact_expenditures WHERE per_pupil_expenditure IS NULL;

SELECT 'expenditures rows by year' AS "check", y.year_key, COUNT(*) n
FROM fact_expenditures fe JOIN dim_year y USING (year_key)
GROUP BY y.year_key ORDER BY y.year_key;

-- 8) Summary coverage (should cover existing school-year-subgroup combos)
WITH base AS (
  SELECT year_key, school_key, subgroup_key FROM fact_attendance
  UNION
  SELECT year_key, school_key, subgroup_key FROM fact_enrollment
),
miss AS (
  SELECT b.year_key, b.school_key, b.subgroup_key
  FROM base b
  LEFT JOIN fact_summary_sys fs
    ON fs.year_key=b.year_key AND fs.school_key=b.school_key AND fs.subgroup_key=b.subgroup_key
  WHERE fs.school_key IS NULL
)
SELECT 'missing rows in summary vs base' AS "check", COUNT(*) n_missing FROM miss;
