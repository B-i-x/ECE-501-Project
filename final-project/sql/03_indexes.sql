PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA temp_store = MEMORY;

-- Star indexes (idempotent)
CREATE INDEX IF NOT EXISTS ix_enroll_school_year   ON fact_enrollment(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_enroll_subgroup      ON fact_enrollment(subgroup_key);

CREATE INDEX IF NOT EXISTS ix_att_school_year      ON fact_attendance(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_att_subgroup         ON fact_attendance(subgroup_key);

CREATE INDEX IF NOT EXISTS ix_assess_school_year   ON fact_assessment(school_key, year_key);
CREATE INDEX IF NOT EXISTS ix_assess_subject_grade ON fact_assessment(subject_key, grade_key);
CREATE INDEX IF NOT EXISTS ix_assess_subgroup      ON fact_assessment(subgroup_key);

-- Helpful dimension indexes (if not already unique)
CREATE UNIQUE INDEX IF NOT EXISTS ux_district_nat  ON dim_district(district_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_school_nat    ON dim_school(school_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_year_key      ON dim_year(year_key);
CREATE UNIQUE INDEX IF NOT EXISTS ux_subject_id    ON dim_subject(subject_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_grade_id      ON dim_grade(grade_id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_subgroup_id   ON dim_subgroup(subgroup_id);
