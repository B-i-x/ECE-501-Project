CREATE TABLE dim_district (
  district_key integer PRIMARY KEY,
  district_id TEXT UNIQUE NOT NULL,
  district_name TEXT,
  county_name TEXT,
  nrc_code TEXT,
  nrc_desc TEXT
);

CREATE TABLE dim_school (
  school_key integer PRIMARY KEY,
  school_id TEXT UNIQUE NOT NULL,
  district_key integer NOT NULL,
  school_name TEXT
);

CREATE TABLE dim_year (
  year_key integer PRIMARY KEY,
  school_year_label TEXT
);

CREATE TABLE dim_subject (
  subject_key integer PRIMARY KEY,
  subject_id TEXT UNIQUE NOT NULL,
  subject_name TEXT
);

CREATE TABLE dim_grade (
  grade_key integer PRIMARY KEY,
  grade_id TEXT UNIQUE NOT NULL
);

CREATE TABLE dim_subgroup (
  subgroup_key integer PRIMARY KEY,
  subgroup_id TEXT UNIQUE NOT NULL,
  subgroup_name TEXT
);

CREATE TABLE fact_enrollment (
  year_key integer NOT NULL,
  school_key integer NOT NULL,
  subgroup_key integer NOT NULL,
  n_students integer,
  PRIMARY KEY (year_key, school_key, subgroup_key)
);

CREATE TABLE fact_attendance (
  year_key integer NOT NULL,
  school_key integer NOT NULL,
  subgroup_key integer NOT NULL,
  absent_count integer,
  absence_rate real,
  enrollment integer,
  data_rep_flag TEXT,
  partial_data_flag TEXT,
  count_zero_flag TEXT,
  PRIMARY KEY (year_key, school_key, subgroup_key)
);

CREATE TABLE fact_assessment (
  year_key integer NOT NULL,
  school_key integer NOT NULL,
  subject_key integer NOT NULL,
  grade_key integer NOT NULL,
  subgroup_key integer NOT NULL,
  tested integer,
  n_qual integer,
  qual_rate real,
  PRIMARY KEY (year_key, school_key, subject_key, grade_key, subgroup_key)
);

ALTER TABLE dim_school ADD FOREIGN KEY (district_key) REFERENCES dim_district (district_key);

ALTER TABLE fact_enrollment ADD FOREIGN KEY (year_key) REFERENCES dim_year (year_key);

ALTER TABLE fact_enrollment ADD FOREIGN KEY (school_key) REFERENCES dim_school (school_key);

ALTER TABLE fact_enrollment ADD FOREIGN KEY (subgroup_key) REFERENCES dim_subgroup (subgroup_key);

ALTER TABLE fact_attendance ADD FOREIGN KEY (year_key) REFERENCES dim_year (year_key);

ALTER TABLE fact_attendance ADD FOREIGN KEY (school_key) REFERENCES dim_school (school_key);

ALTER TABLE fact_attendance ADD FOREIGN KEY (subgroup_key) REFERENCES dim_subgroup (subgroup_key);

ALTER TABLE fact_assessment ADD FOREIGN KEY (year_key) REFERENCES dim_year (year_key);

ALTER TABLE fact_assessment ADD FOREIGN KEY (school_key) REFERENCES dim_school (school_key);

ALTER TABLE fact_assessment ADD FOREIGN KEY (subject_key) REFERENCES dim_subject (subject_key);

ALTER TABLE fact_assessment ADD FOREIGN KEY (grade_key) REFERENCES dim_grade (grade_key);

ALTER TABLE fact_assessment ADD FOREIGN KEY (subgroup_key) REFERENCES dim_subgroup (subgroup_key);
