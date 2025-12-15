PRAGMA foreign_keys=ON;

-- ========== DIMENSIONS ==========
CREATE TABLE IF NOT EXISTS dim_district (
  district_key INTEGER PRIMARY KEY,
  district_id  TEXT UNIQUE NOT NULL,
  district_name TEXT,
  county_name   TEXT,
  nrc_code      TEXT,
  nrc_desc      TEXT
);

CREATE TABLE IF NOT EXISTS dim_school (
  school_key   INTEGER PRIMARY KEY,
  school_id    TEXT UNIQUE NOT NULL,
  district_key INTEGER NOT NULL REFERENCES dim_district(district_key),
  school_name  TEXT
);

CREATE TABLE IF NOT EXISTS dim_year (
  year_key INTEGER PRIMARY KEY,        -- e.g., 2024 (reporting year)
  school_year_label TEXT               -- e.g., 2023-24 (optional)
);

CREATE TABLE IF NOT EXISTS dim_subject (
  subject_key INTEGER PRIMARY KEY,
  subject_id  TEXT UNIQUE NOT NULL,    -- 'ELA','Math'
  subject_name TEXT
);

CREATE TABLE IF NOT EXISTS dim_grade (
  grade_key INTEGER PRIMARY KEY,
  grade_id  TEXT UNIQUE NOT NULL       -- '3'..'8','All'
);

CREATE TABLE IF NOT EXISTS dim_subgroup (
  subgroup_key  INTEGER PRIMARY KEY,
  subgroup_id   TEXT UNIQUE NOT NULL,  -- canonical code: F,M,SWD,ELL,ED,Asian,...
  subgroup_name TEXT
);

-- ========== FACTS ==========
-- fact_enrollment: year x school x subgroup
CREATE TABLE IF NOT EXISTS fact_enrollment (
  year_key     INTEGER NOT NULL REFERENCES dim_year(year_key),
  school_key   INTEGER NOT NULL REFERENCES dim_school(school_key),
  subgroup_key INTEGER NOT NULL REFERENCES dim_subgroup(subgroup_key),
  n_students   INTEGER,
  PRIMARY KEY (year_key, school_key, subgroup_key)
);

-- fact_attendance: year x school x subgroup
CREATE TABLE IF NOT EXISTS fact_attendance (
  year_key     INTEGER NOT NULL REFERENCES dim_year(year_key),
  school_key   INTEGER NOT NULL REFERENCES dim_school(school_key),
  subgroup_key INTEGER NOT NULL REFERENCES dim_subgroup(subgroup_key),
  absent_count INTEGER,
  absence_rate REAL,     -- 0..1
  enrollment   INTEGER,  -- copy-through for QA/joins
  data_rep_flag TEXT,
  partial_data_flag TEXT,
  count_zero_flag TEXT,
  PRIMARY KEY (year_key, school_key, subgroup_key)
);

-- fact_assessment: year x school x subject x grade x subgroup
CREATE TABLE IF NOT EXISTS fact_assessment (
  year_key     INTEGER NOT NULL REFERENCES dim_year(year_key),
  school_key   INTEGER NOT NULL REFERENCES dim_school(school_key),
  subject_key  INTEGER NOT NULL REFERENCES dim_subject(subject_key),
  grade_key    INTEGER NOT NULL REFERENCES dim_grade(grade_key),
  subgroup_key INTEGER NOT NULL REFERENCES dim_subgroup(subgroup_key),
  tested       INTEGER,
  n_qual       INTEGER,
  qual_rate    REAL,     -- 0..1
  PRIMARY KEY (year_key, school_key, subject_key, grade_key, subgroup_key)
);

-- fact_expenditures: year x school (school-level expenditure data)
CREATE TABLE IF NOT EXISTS fact_expenditures (
  year_key           INTEGER NOT NULL REFERENCES dim_year(year_key),
  school_key         INTEGER NOT NULL REFERENCES dim_school(school_key),
  per_pupil_expenditure REAL,  -- dollars per pupil
  data_reported_exp  TEXT,     -- 'Y' if expenditure data reported
  data_reported_enr  TEXT,     -- 'Y' if enrollment data reported
  PRIMARY KEY (year_key, school_key)
);

-- summary table created by 20_refresh_summary.sql

-- ========== INDEXES (idempotent) ==========
CREATE UNIQUE INDEX IF NOT EXISTS ux_district_id ON dim_district(district_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_school_id   ON dim_school(school_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_year_key    ON dim_year(year_key);
CREATE UNIQUE INDEX IF NOT EXISTS ux_subject_id  ON dim_subject(subject_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_grade_id    ON dim_grade(grade_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_subgroup_id ON dim_subgroup(subgroup_id);

CREATE INDEX IF NOT EXISTS ix_enroll_school_year   ON fact_enrollment(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_enroll_subgroup      ON fact_enrollment(subgroup_key);
CREATE INDEX IF NOT EXISTS ix_att_school_year      ON fact_attendance(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_att_subgroup         ON fact_attendance(subgroup_key);
CREATE INDEX IF NOT EXISTS ix_assess_school_year   ON fact_assessment(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_assess_subject_grade ON fact_assessment(subject_key, grade_key);
CREATE INDEX IF NOT EXISTS ix_assess_subgroup      ON fact_assessment(subgroup_key);

CREATE INDEX IF NOT EXISTS ix_expend_school_year   ON fact_expenditures(school_key, year_key);
