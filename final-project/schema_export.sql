CREATE TABLE IF NOT EXISTS "acc_em_chronic_absenteeism" ("INSTITUTION_ID" TEXT, "ENTITY_CD" TEXT, "ENTITY_NAME" TEXT, "YEAR" TEXT, "SUBJECT" TEXT, "SUBGROUP_NAME" TEXT, "ENROLLMENT" TEXT, "ABSENT_COUNT" TEXT, "ABSENT_RATE" TEXT, "LEVEL" TEXT, "OVERRIDE" TEXT, "DATA_REP_FLAG" TEXT, "PARTIAL_DATA_FLAG" TEXT, "COUNT_ZERO_NON_DISPLAY_FLAG" TEXT);
CREATE TABLE IF NOT EXISTS "annual_em_ela" ("INSTITUTION_ID" TEXT, "ENTITY_CD" TEXT, "ENTITY_NAME" TEXT, "YEAR" TEXT, "ASSESSMENT_NAME" TEXT, "SUBGROUP_NAME" TEXT, "TOTAL_COUNT" TEXT, "NOT_TESTED" TEXT, "PCT_NOT_TESTED" TEXT, "NUM_TESTED" TEXT, "PCT_TESTED" TEXT, "LEVEL1_COUNT" TEXT, "LEVEL1_pctTESTED" TEXT, "LEVEL2_COUNT" TEXT, "LEVEL2_pctTESTED" TEXT, "LEVEL3_COUNT" TEXT, "LEVEL3_pctTESTED" TEXT, "LEVEL4_COUNT" TEXT, "LEVEL4_pctTESTED" TEXT, "NUM_PROF" TEXT, "PER_PROF" TEXT, "TOTAL_SCALE_SCORES" TEXT, "MEAN_SCORE" TEXT);
CREATE TABLE IF NOT EXISTS "annual_em_math" ("INSTITUTION_ID" TEXT, "ENTITY_CD" TEXT, "ENTITY_NAME" TEXT, "YEAR" TEXT, "ASSESSMENT_NAME" TEXT, "SUBGROUP_NAME" TEXT, "TOTAL_COUNT" TEXT, "NOT_TESTED" TEXT, "PCT_NOT_TESTED" TEXT, "NUM_TESTED" TEXT, "PCT_TESTED" TEXT, "LEVEL1_COUNT" TEXT, "LEVEL1_pctTESTED" TEXT, "LEVEL2_COUNT" TEXT, "LEVEL2_pctTESTED" TEXT, "LEVEL3_COUNT" TEXT, "LEVEL3_pctTESTED" TEXT, "LEVEL4_COUNT" TEXT, "LEVEL4_pctTESTED" TEXT, "LEVEL5_COUNT" TEXT, "LEVEL5_pctTESTED" TEXT, "NUM_PROF" TEXT, "PER_PROF" TEXT, "TOTAL_SCALE_SCORES" TEXT, "MEAN_SCORE" TEXT);
CREATE TABLE IF NOT EXISTS "boces_n_rc" ("INSTITUTION_ID" TEXT, "ENTITY_CD" TEXT, "SCHOOL_NAME" TEXT, "YEAR" TEXT, "DISTRICT_CD" TEXT, "DISTRICT_NAME" TEXT, "BOCES_CD" TEXT, "BOCES_NAME" TEXT, "COUNTY_CD" TEXT, "COUNTY_NAME" TEXT, "NEEDS_INDEX" TEXT, "NEEDS_INDEX_DESCRIPTION" TEXT);
CREATE TABLE map_subgroups (
            raw_label   TEXT PRIMARY KEY,
            subgroup_id TEXT,
            subgroup_name TEXT
        );
CREATE TABLE dim_district (
  district_key INTEGER PRIMARY KEY,
  district_id  TEXT UNIQUE NOT NULL,
  district_name TEXT,
  county_name   TEXT,
  nrc_code      TEXT,
  nrc_desc      TEXT
);
CREATE TABLE dim_school (
  school_key   INTEGER PRIMARY KEY,
  school_id    TEXT UNIQUE NOT NULL,
  district_key INTEGER NOT NULL REFERENCES dim_district(district_key),
  school_name  TEXT
);
CREATE TABLE dim_year (
  year_key INTEGER PRIMARY KEY,        -- e.g., 2024 (reporting year)
  school_year_label TEXT               -- e.g., 2023-24 (optional)
);
CREATE TABLE dim_subject (
  subject_key INTEGER PRIMARY KEY,
  subject_id  TEXT UNIQUE NOT NULL,    -- 'ELA','Math'
  subject_name TEXT
);
CREATE TABLE dim_grade (
  grade_key INTEGER PRIMARY KEY,
  grade_id  TEXT UNIQUE NOT NULL       -- '3'..'8','All'
);
CREATE TABLE dim_subgroup (
  subgroup_key  INTEGER PRIMARY KEY,
  subgroup_id   TEXT UNIQUE NOT NULL,  -- canonical code: F,M,SWD,ELL,ED,Asian,...
  subgroup_name TEXT
);
CREATE TABLE fact_enrollment (
  year_key     INTEGER NOT NULL REFERENCES dim_year(year_key),
  school_key   INTEGER NOT NULL REFERENCES dim_school(school_key),
  subgroup_key INTEGER NOT NULL REFERENCES dim_subgroup(subgroup_key),
  n_students   INTEGER,
  PRIMARY KEY (year_key, school_key, subgroup_key)
);
CREATE TABLE fact_attendance (
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
CREATE TABLE fact_assessment (
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
CREATE UNIQUE INDEX ux_district_id ON dim_district(district_id);
CREATE UNIQUE INDEX ux_school_id   ON dim_school(school_id);
CREATE UNIQUE INDEX ux_year_key    ON dim_year(year_key);
CREATE UNIQUE INDEX ux_subject_id  ON dim_subject(subject_id);
CREATE UNIQUE INDEX ux_grade_id    ON dim_grade(grade_id);
CREATE UNIQUE INDEX ux_subgroup_id ON dim_subgroup(subgroup_id);
CREATE INDEX ix_enroll_school_year   ON fact_enrollment(school_key, year_key);
CREATE INDEX ix_enroll_subgroup      ON fact_enrollment(subgroup_key);
CREATE INDEX ix_att_school_year      ON fact_attendance(school_key, year_key);
CREATE INDEX ix_att_subgroup         ON fact_attendance(subgroup_key);
CREATE INDEX ix_assess_school_year   ON fact_assessment(school_key, year_key);
CREATE INDEX ix_assess_subject_grade ON fact_assessment(subject_key, grade_key);
CREATE INDEX ix_assess_subgroup      ON fact_assessment(subgroup_key);
CREATE UNIQUE INDEX ux_district_nat  ON dim_district(district_id);
CREATE UNIQUE INDEX ux_school_nat    ON dim_school(school_id);
CREATE TABLE st_years(year_key NUM);
CREATE TABLE st_attendance_em_num(
  year_key INT,
  school_id TEXT,
  subgroup_raw,
  enrollment INT,
  absent_count INT,
  absence_rate,
  DATA_REP_FLAG TEXT,
  PARTIAL_DATA_FLAG TEXT,
  COUNT_ZERO_NON_DISPLAY_FLAG TEXT
);
CREATE TABLE st_assessment_em_num(
  year_key NUM,
  school_id TEXT,
  subgroup_raw,
  subject,
  grade,
  tested NUM,
  n_qual,
  qual_rate
);
CREATE TABLE st_org(
  school_id TEXT,
  school_name TEXT,
  district_id TEXT,
  district_name TEXT,
  COUNTY_NAME TEXT,
  needs_index TEXT,
  needs_index_description TEXT
);
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
