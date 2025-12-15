/* fact_assessment: EM ELA/Math by grade + subgroup (proportions) */

-- seed subjects & grades (idempotent)
INSERT OR IGNORE INTO dim_subject(subject_id, subject_name)
VALUES ('ELA','English Language Arts'), ('Math','Mathematics');

INSERT OR IGNORE INTO dim_grade(grade_id)
VALUES ('3'),('4'),('5'),('6'),('7'),('8'),('All');

-- seed subgroups from observed labels (fallback if map_subgroups not populated)
INSERT OR IGNORE INTO dim_subgroup(subgroup_id, subgroup_name)
SELECT DISTINCT COALESCE(m.subgroup_id, r.subgroup_raw),
       COALESCE(m.subgroup_name, r.subgroup_raw)
FROM (SELECT DISTINCT subgroup_raw FROM st_assessment_em_num) r
LEFT JOIN map_subgroups m ON m.raw_label = r.subgroup_raw;

INSERT OR REPLACE INTO fact_assessment(
  year_key, school_key, subject_key, grade_key, subgroup_key, tested, n_qual, qual_rate
)
SELECT
  y.year_key,
  s.school_key,
  sub.subject_key,
  gkey.grade_key,
  sg.subgroup_key,
  a.tested,
  a.n_qual,
  a.qual_rate
FROM st_assessment_em_num a
JOIN dim_year y     ON y.year_key = a.year_key
JOIN dim_school s   ON s.school_id = a.school_id
JOIN dim_subject sub ON sub.subject_id = a.subject
JOIN dim_grade gkey  ON gkey.grade_id = a.grade
LEFT JOIN map_subgroups m ON m.raw_label = a.subgroup_raw
JOIN dim_subgroup sg ON sg.subgroup_id = COALESCE(m.subgroup_id, a.subgroup_raw);
