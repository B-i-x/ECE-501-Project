/* Summary rollup linking attendance + enrollment + ELA/Math rates per (year, school, subgroup) */

DROP TABLE IF EXISTS fact_summary_sys;
CREATE TABLE fact_summary_sys (
  year_key INTEGER NOT NULL,
  district_key INTEGER NOT NULL,
  school_key INTEGER NOT NULL,
  subgroup_key INTEGER NOT NULL,
  n_students INTEGER,
  absence_rate REAL,
  ela_qual_rate REAL,
  math_qual_rate REAL,
  PRIMARY KEY (year_key, school_key, subgroup_key),
  FOREIGN KEY(year_key) REFERENCES dim_year(year_key),
  FOREIGN KEY(district_key) REFERENCES dim_district(district_key),
  FOREIGN KEY(school_key) REFERENCES dim_school(school_key),
  FOREIGN KEY(subgroup_key) REFERENCES dim_subgroup(subgroup_key)
);

WITH assess AS (
  SELECT
    fa.year_key, fa.school_key, fa.subgroup_key,
    MAX(CASE WHEN ds.subject_id='ELA'  THEN fa.qual_rate END)  AS ela_qual_rate,
    MAX(CASE WHEN ds.subject_id='Math' THEN fa.qual_rate END)  AS math_qual_rate
  FROM fact_assessment fa
  JOIN dim_subject ds ON ds.subject_key = fa.subject_key
  GROUP BY fa.year_key, fa.school_key, fa.subgroup_key
),
att AS (
  SELECT year_key, school_key, subgroup_key,
         AVG(absence_rate) AS absence_rate,
         SUM(enrollment)   AS n_students
  FROM fact_attendance
  GROUP BY year_key, school_key, subgroup_key
)
INSERT OR REPLACE INTO fact_summary_sys(
  year_key, district_key, school_key, subgroup_key,
  n_students, absence_rate, ela_qual_rate, math_qual_rate
)
SELECT
  a.year_key,
  sch.district_key,
  a.school_key,
  a.subgroup_key,
  a.n_students,
  a.absence_rate,
  z.ela_qual_rate,
  z.math_qual_rate
FROM att a
LEFT JOIN assess z
  ON z.year_key=a.year_key AND z.school_key=a.school_key AND z.subgroup_key=a.subgroup_key
JOIN dim_school sch ON sch.school_key=a.school_key;
