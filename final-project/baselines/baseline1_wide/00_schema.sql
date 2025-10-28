-- baseline1_schema.sql  (Wide, denormalized; minimal constraints, no indexes)
DROP TABLE IF EXISTS wide_report_card;

CREATE TABLE wide_report_card (
  -- grain: Year × School × Subject × Grade × Subgroup
  year                  INTEGER,          -- e.g., 2024
  district_id           TEXT,
  district_name         TEXT,
  school_id             TEXT,
  school_name           TEXT,
  subject               TEXT,             -- 'ELA' | 'Math'
  grade                 TEXT,             -- '3'..'8' | 'All'
  subgroup              TEXT,             -- raw/canonical label

  -- enrollment / attendance (from Chronic Absenteeism)
  n_students            INTEGER,
  absent_count          INTEGER,
  absence_rate          REAL,             -- 0..1

  -- assessment (from EM ELA / EM Math)
  tested                INTEGER,
  n_prof                INTEGER,
  prof_rate             REAL,             -- 0..1

  -- optional provenance/flags
  data_rep_flag         TEXT,
  partial_data_flag     TEXT,
  count_zero_flag       TEXT
);

/* Optional (commented) PK to enforce uniqueness; baseline can stay without it
-- ALTER TABLE wide_report_card
-- ADD CONSTRAINT pk_wide PRIMARY KEY (year, school_id, subject, grade, subgroup);
*/

-- Optional: demonstration of how to populate it from staging
-- (keep commented until staging exists)
-- INSERT INTO wide_report_card (
--   year, district_id, district_name, school_id, school_name,
--   subject, grade, subgroup,
--   n_students, absent_count, absence_rate,
--   tested, n_prof, prof_rate,
--   data_rep_flag, partial_data_flag, count_zero_flag
-- )
-- SELECT
--   a.year_key,
--   o.district_id, o.district_name,
--   a.school_id, o.school_name,
--   t.subject, t.grade,
--   a.subgroup_raw,
--   a.enrollment, a.absent_count, a.absent_rate,
--   t.tested, t.n_qual, t.qual_rate,
--   a.DATA_REP_FLAG, a.PARTIAL_DATA_FLAG, a.COUNT_ZERO_NON_DISPLAY_FLAG
-- FROM st_attendance_em_num a
-- LEFT JOIN st_assessment_em_num t
--   USING(year_key, school_id, subgroup_raw)
-- LEFT JOIN st_org o
--   ON o.school_id = a.school_id;