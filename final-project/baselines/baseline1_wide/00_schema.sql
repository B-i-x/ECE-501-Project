-- single wide denormalized table for Baseline 1
CREATE TABLE IF NOT EXISTS wide(
  year INTEGER,
  district_id TEXT, district_name TEXT,
  school_id TEXT,   school_name TEXT,
  subject TEXT, grade INTEGER,
  subgroup_code TEXT, subgroup_label TEXT,
  tested INTEGER, n_qual INTEGER, qual_rate REAL,
  attendance_indicator REAL, chronic_absent_rate REAL,
  number_students INTEGER, pct_students REAL
);
