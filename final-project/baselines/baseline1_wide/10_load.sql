-- baselines/baseline1_wide/10_load.sql
-- Populate wide_report_card from staging (st_attendance_em_num, st_assessment_em_num, st_org)

DELETE FROM wide_report_card;

INSERT INTO wide_report_card (
  year, district_id, district_name, school_id, school_name,
  subject, grade, subgroup,
  n_students, absent_count, absence_rate,
  tested, n_prof, prof_rate,
  data_rep_flag, partial_data_flag, count_zero_flag
)
SELECT
  a.year_key                                  AS year,
  o.district_id, o.district_name,
  a.school_id, o.school_name,
  t.subject, t.grade,
  a.subgroup_raw                               AS subgroup,
  a.enrollment, a.absent_count, a.absent_rate,
  t.tested, t.n_qual, t.qual_rate,
  a.DATA_REP_FLAG, a.PARTIAL_DATA_FLAG, a.COUNT_ZERO_NON_DISPLAY_FLAG
FROM st_attendance_em_num a
LEFT JOIN st_assessment_em_num t
  USING (year_key, school_id, subgroup_raw)
LEFT JOIN st_org o
  ON o.school_id = a.school_id;

-- Optional: also include rows present in assessment but missing in attendance
INSERT INTO wide_report_card (
  year, district_id, district_name, school_id, school_name,
  subject, grade, subgroup,
  n_students, absent_count, absence_rate,
  tested, n_prof, prof_rate,
  data_rep_flag, partial_data_flag, count_zero_flag
)
SELECT
  t.year_key,
  o.district_id, o.district_name,
  t.school_id, o.school_name,
  t.subject, t.grade,
  t.subgroup_raw,
  NULL, NULL, NULL,
  t.tested, t.n_qual, t.qual_rate,
  NULL, NULL, NULL
FROM st_assessment_em_num t
LEFT JOIN st_org o
  ON o.school_id = t.school_id
LEFT JOIN st_attendance_em_num a
  USING (year_key, school_id, subgroup_raw)
WHERE a.school_id IS NULL;
