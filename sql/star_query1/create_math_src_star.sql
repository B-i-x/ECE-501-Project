CREATE TEMP VIEW math_src AS
SELECT
  s.school_id      AS ENTITY_CD,
  y.year_key       AS YEAR,
  sg.subgroup_name AS SUBGROUP_NAME,
  'MATH'           AS ASSESSMENT_NAME,
  fa.tested        AS NUM_TESTED,
  fa.n_qual        AS NUM_PROF
FROM fact_assessment fa
JOIN dim_school   s   ON s.school_key   = fa.school_key
JOIN dim_year     y   ON y.year_key     = fa.year_key
JOIN dim_subject  subj ON subj.subject_key = fa.subject_key
JOIN dim_subgroup sg   ON sg.subgroup_key  = fa.subgroup_key
WHERE subj.subject_id = 'Math'
  AND UPPER(TRIM(sg.subgroup_name)) LIKE 'ALL STUDENTS%';