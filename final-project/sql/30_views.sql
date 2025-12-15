DROP VIEW IF EXISTS v_assessment_school_year;
CREATE VIEW v_assessment_school_year AS
SELECT
  y.year_key AS year,
  s.school_key, s.school_name,
  d.district_key, d.district_name,
  subj.subject_id, g.grade_id,
  sg.subgroup_id, sg.subgroup_name,
  fa.tested, fa.n_qual, fa.qual_rate
FROM fact_assessment fa
JOIN dim_year y     ON y.year_key=fa.year_key
JOIN dim_school s   ON s.school_key=fa.school_key
JOIN dim_district d ON d.district_key=s.district_key
JOIN dim_subject subj ON subj.subject_key=fa.subject_key
JOIN dim_grade g    ON g.grade_key=fa.grade_key
JOIN dim_subgroup sg ON sg.subgroup_key=fa.subgroup_key;

DROP VIEW IF EXISTS v_absence_vs_proficiency;
CREATE VIEW v_absence_vs_proficiency AS
SELECT
  y.year_key AS year,
  d.district_name, s.school_name,
  sg.subgroup_id,
  fs.absence_rate,
  fs.ela_qual_rate,
  fs.math_qual_rate
FROM fact_summary_sys fs
JOIN dim_year y     ON y.year_key=fs.year_key
JOIN dim_school s   ON s.school_key=fs.school_key
JOIN dim_district d ON d.district_key=fs.district_key
JOIN dim_subgroup sg ON sg.subgroup_key=fs.subgroup_key;

-- Comprehensive summary view with all key metrics
DROP VIEW IF EXISTS v_summary_complete;
CREATE VIEW v_summary_complete AS
SELECT
  y.year_key AS year,
  y.school_year_label,
  d.district_id,
  d.district_name,
  d.county_name,
  s.school_id,
  s.school_name,
  sg.subgroup_id,
  sg.subgroup_name,
  fs.n_students,
  fs.absence_rate,
  ROUND(fs.absence_rate * 100, 2) AS absence_rate_pct,
  fs.ela_qual_rate,
  ROUND(fs.ela_qual_rate * 100, 2) AS ela_qual_rate_pct,
  fs.math_qual_rate,
  ROUND(fs.math_qual_rate * 100, 2) AS math_qual_rate_pct,
  fe.per_pupil_expenditure
FROM fact_summary_sys fs
JOIN dim_year y     ON y.year_key=fs.year_key
JOIN dim_school s   ON s.school_key=fs.school_key
JOIN dim_district d ON d.district_key=fs.district_key
JOIN dim_subgroup sg ON sg.subgroup_key=fs.subgroup_key
LEFT JOIN fact_expenditures fe ON fe.year_key=fs.year_key AND fe.school_key=fs.school_key;
