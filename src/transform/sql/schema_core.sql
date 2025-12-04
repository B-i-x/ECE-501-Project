PRAGMA foreign_keys = ON;

-- Dimension: institution (schools, districts, etc)
CREATE TABLE IF NOT EXISTS dim_institution (
    institution_id      TEXT PRIMARY KEY,
    entity_cd           TEXT UNIQUE NOT NULL,
    entity_name         TEXT NOT NULL,

    district_cd         TEXT,
    district_name       TEXT,
    boces_cd            TEXT,
    boces_name          TEXT,
    county_cd           TEXT,
    county_name         TEXT,
    nrc_code            TEXT,
    nrc_desc            TEXT,
    nyc_ind             TEXT,

    needs_index         TEXT,
    needs_index_desc    TEXT,

    group_code          INTEGER,
    group_name          TEXT,
    school_type         TEXT
);

CREATE INDEX IF NOT EXISTS idx_dim_institution_entity_cd
    ON dim_institution(entity_cd);

CREATE INDEX IF NOT EXISTS idx_dim_institution_district
    ON dim_institution(district_cd);

-- Dimension: year
CREATE TABLE IF NOT EXISTS dim_year (
    year_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    report_year    INTEGER NOT NULL,
    school_year    TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_year_report
    ON dim_year(report_year);

-- Dimension: subgroup
CREATE TABLE IF NOT EXISTS dim_subgroup (
    subgroup_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    subgroup_code  TEXT,
    subgroup_name  TEXT NOT NULL,
    subgroup_type  TEXT NOT NULL DEFAULT 'Unknown'
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_subgroup_code_name
    ON dim_subgroup(subgroup_code, subgroup_name);

-- Dimension: subject / assessment
CREATE TABLE IF NOT EXISTS dim_subject (
    subject_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_code     TEXT NOT NULL,
    subject_name     TEXT NOT NULL,
    assessment_name  TEXT,
    grade_span       TEXT,
    is_hs            INTEGER NOT NULL DEFAULT 0
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_subject_code
    ON dim_subject(subject_code);

-- Dimension: indicator (for accountability)
CREATE TABLE IF NOT EXISTS dim_indicator (
    indicator_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator_code  TEXT NOT NULL,
    indicator_name  TEXT NOT NULL,
    domain          TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_indicator_code
    ON dim_indicator(indicator_code);

-- Dimension: grade
CREATE TABLE IF NOT EXISTS dim_grade (
    grade_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    grade_code      TEXT NOT NULL,
    grade_label     TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_dim_grade_code
    ON dim_grade(grade_code);
