-- baseline2_schema.sql  (Normalized on natural keys; no indexes)

DROP TABLE IF EXISTS b2_district;
DROP TABLE IF EXISTS b2_school;
DROP TABLE IF EXISTS b2_year;
DROP TABLE IF EXISTS b2_subject;
DROP TABLE IF EXISTS b2_grade;
DROP TABLE IF EXISTS b2_subgroup;
DROP TABLE IF EXISTS b2_enrollment;
DROP TABLE IF EXISTS b2_attendance;
DROP TABLE IF EXISTS b2_assessment;

-- Dimensions (natural keys)
CREATE TABLE b2_district (
  district_id     TEXT PRIMARY KEY,
  district_name   TEXT,
  county_name     TEXT,
  nrc_code        TEXT,
  nrc_desc        TEXT
);

CREATE TABLE b2_school (
  school_id     TEXT PRIMARY KEY,
  district_id   TEXT NOT NULL REFERENCES b2_district(district_id),
  school_name   TEXT
);

CREATE TABLE b2_year (
  year          INTEGER PRIMARY KEY
);

CREATE TABLE b2_subject (
  subject_id    TEXT PRIMARY KEY,   -- 'ELA' | 'Math'
  subject_name  TEXT
);

CREATE TABLE b2_grade (
  grade_id      TEXT PRIMARY KEY     -- '3'..'8' | 'All'
);

CREATE TABLE b2_subgroup (
  subgroup_id    TEXT PRIMARY KEY,   -- canonical code or raw label
  subgroup_name  TEXT
);

-- Facts (natural-key FKs; NO indexes)
CREATE TABLE b2_enrollment (
  year          INTEGER NOT NULL REFERENCES b2_year(year),
  school_id     TEXT    NOT NULL REFERENCES b2_school(school_id),
  subgroup_id   TEXT    NOT NULL REFERENCES b2_subgroup(subgroup_id),
  n_students    INTEGER,
  PRIMARY KEY (year, school_id, subgroup_id)
);

CREATE TABLE b2_attendance (
  year          INTEGER NOT NULL REFERENCES b2_year(year),
  school_id     TEXT    NOT NULL REFERENCES b2_school(school_id),
  subgroup_id   TEXT    NOT NULL REFERENCES b2_subgroup(subgroup_id),
  absent_count  INTEGER,
  absence_rate  REAL,           -- 0..1
  enrollment    INTEGER,
  data_rep_flag TEXT,
  partial_data_flag TEXT,
  count_zero_flag TEXT,
  PRIMARY KEY (year, school_id, subgroup_id)
);

CREATE TABLE b2_assessment (
  year          INTEGER NOT NULL REFERENCES b2_year(year),
  school_id     TEXT    NOT NULL REFERENCES b2_school(school_id),
  subject_id    TEXT    NOT NULL REFERENCES b2_subject(subject_id),
  grade_id      TEXT    NOT NULL REFERENCES b2_grade(grade_id),
  subgroup_id   TEXT    NOT NULL REFERENCES b2_subgroup(subgroup_id),
  tested        INTEGER,
  n_prof        INTEGER,
  prof_rate     REAL,          -- 0..1
  PRIMARY KEY (year, school_id, subject_id, grade_id, subgroup_id)
);
