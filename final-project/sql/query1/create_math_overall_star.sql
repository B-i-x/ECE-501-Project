-- Query 1 Star Schema: Aggregate math proficiency by school/year
-- This replaces create_math_overall.sql

CREATE TEMP VIEW math_overall AS
SELECT
  m.ENTITY_CD AS entity_cd,
  CAST(m.YEAR AS INTEGER) AS year,
  SUM(CAST(m.NUM_PROF AS INTEGER)) AS num_prof,
  SUM(CAST(m.NUM_TESTED AS INTEGER)) AS num_tested
FROM math_src m
WHERE TRIM(UPPER(m.SUBGROUP_NAME)) LIKE 'ALL STUDENTS%'
  AND UPPER(m.ASSESSMENT_NAME) LIKE '%MATH%'
GROUP BY m.ENTITY_CD, CAST(m.YEAR AS INTEGER);

