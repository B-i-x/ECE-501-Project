PRAGMA foreign_keys = ON;

-- Enrollment by grade
CREATE TABLE IF NOT EXISTS fact_enrollment (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,
    grade_id         INTEGER NOT NULL,
    program_type     TEXT,                 -- 'HALF', 'FULL', or NULL
    enrollment_cnt   INTEGER NOT NULL,

    PRIMARY KEY (institution_id, year_id, grade_id, COALESCE(program_type, '')),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (grade_id)       REFERENCES dim_grade(grade_id)
);

CREATE INDEX IF NOT EXISTS idx_enrollment_inst_year
    ON fact_enrollment(institution_id, year_id);

CREATE INDEX IF NOT EXISTS idx_enrollment_grade
    ON fact_enrollment(grade_id);

-- Demographic factors
CREATE TABLE IF NOT EXISTS fact_demographics (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,
    subgroup_id      INTEGER NOT NULL,
    count_value      INTEGER NOT NULL,
    pct_value        REAL NOT NULL,

    PRIMARY KEY (institution_id, year_id, subgroup_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);

CREATE INDEX IF NOT EXISTS idx_demo_inst_year
    ON fact_demographics(institution_id, year_id);

-- Generic student metrics like attendance, suspensions, etc
CREATE TABLE IF NOT EXISTS fact_student_metrics (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,
    metric_code      TEXT NOT NULL,
    metric_value_num REAL,
    metric_value_txt TEXT,

    PRIMARY KEY (institution_id, year_id, metric_code),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id)
);

CREATE INDEX IF NOT EXISTS idx_student_metrics_inst_year
    ON fact_student_metrics(institution_id, year_id);

-- Class type dimension
CREATE TABLE IF NOT EXISTS dim_class_type (
    class_type_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    class_desc       TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_class_type_desc
    ON dim_class_type(class_desc);

-- Average class size
CREATE TABLE IF NOT EXISTS fact_class_size (
    institution_id      TEXT NOT NULL,
    year_id             INTEGER NOT NULL,
    class_type_id       INTEGER NOT NULL,
    average_class_size  REAL NOT NULL,
    data_reported       TEXT,

    PRIMARY KEY (institution_id, year_id, class_type_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (class_type_id)  REFERENCES dim_class_type(class_type_id)
);
