-- baselines/baseline2_normalized/10_load.sql
-- Seed baseline-2 dims & load facts from staging

-- Years
INSERT OR IGNORE INTO b2_year(year)
SELECT DISTINCT year_key FROM st_years;

-- Districts & Schools
INSERT OR IGNORE INTO b2_district(district_id, district_name, county_name, nrc_code, nrc_desc)
SELECT DISTINCT district_id, district_name, COUNTY_NAME, NEEDS_INDEX, NEEDS_INDEX_DESCRIPTION
FROM st_org
WHERE district_id IS NOT NULL;

INSERT OR IGNORE INTO b2_school(school_id, district_id, school_name)
SELECT DISTINCT school_id, district_id, school_name
FROM st_org
WHERE school_id IS NOT NULL;

-- Subjects & Grades from assessment staging
INSERT OR IGNORE INTO b2_subject(subject_id, subject_name)
SELECT DISTINCT subject,
       CASE subject WHEN 'ELA' THEN 'English Language Arts'
                    WHEN 'Math' THEN 'Mathematics'
                    ELSE subject END
FROM st_assessment_em_num;

INSERT OR IGNORE INTO b2_grade(grade_id)
SELECT DISTINCT grade FROM st_assessment_em_num;

-- Subgroups (canonicalize via map_subgroups if present)
INSERT OR IGNORE INTO b2_subgroup(subgroup_id, subgroup_name)
SELECT DISTINCT
  COALESCE(ms.subgroup_id, x.subgroup_raw)      AS subgroup_id,
  COALESCE(ms.subgroup_name, x.subgroup_raw)    AS subgroup_name
FROM (
  SELECT subgroup_raw FROM st_attendance_em_num
  UNION
  SELECT subgroup_raw FROM st_assessment_em_num
) x
LEFT JOIN map_subgroups ms
  ON ms.raw_label = x.subgroup_raw;

-- ENROLLMENT (derive from attendance staging's enrollment)
INSERT OR REPLACE INTO b2_enrollment(year, school_id, subgroup_id, n_students)
SELECT
  a.year_key,
  a.school_id,
  COALESCE(ms.subgroup_id, a.subgroup_raw) AS subgroup_id,
  a.enrollment
FROM st_attendance_em_num a
LEFT JOIN map_subgroups ms ON ms.raw_label = a.subgroup_raw
WHERE a.enrollment IS NOT NULL;

-- ATTENDANCE
INSERT OR REPLACE INTO b2_attendance(
  year, school_id, subgroup_id,
  absent_count, absence_rate, enrollment,
  data_rep_flag, partial_data_flag, count_zero_flag
)
SELECT
  a.year_key,
  a.school_id,
  COALESCE(ms.subgroup_id, a.subgroup_raw) AS subgroup_id,
  a.absent_count,
  a.absent_rate,
  a.enrollment,
  a.DATA_REP_FLAG,
  a.PARTIAL_DATA_FLAG,
  a.COUNT_ZERO_NON_DISPLAY_FLAG
FROM st_attendance_em_num a
LEFT JOIN map_subgroups ms ON ms.raw_label = a.subgroup_raw;

-- ASSESSMENT (ELA + Math)
INSERT OR REPLACE INTO b2_assessment(
  year, school_id, subject_id, grade_id, subgroup_id,
  tested, n_prof, prof_rate
)
SELECT
  t.year_key,
  t.school_id,
  t.subject,
  t.grade,
  COALESCE(ms.subgroup_id, t.subgroup_raw) AS subgroup_id,
  t.tested,
  t.n_qual,
  t.qual_rate
FROM st_assessment_em_num t
LEFT JOIN map_subgroups ms ON ms.raw_label = t.subgroup_raw;
