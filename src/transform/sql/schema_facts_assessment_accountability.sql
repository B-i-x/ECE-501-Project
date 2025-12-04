PRAGMA foreign_keys = ON;

-- Accountability indicators
CREATE TABLE IF NOT EXISTS fact_accountability (
    institution_id    TEXT NOT NULL,
    year_id           INTEGER NOT NULL,
    indicator_id      INTEGER NOT NULL,
    subject_id        INTEGER,
    subgroup_id       INTEGER,

    cohort            TEXT,
    enrollment_cnt    INTEGER,
    absent_cnt        INTEGER,
    absent_rate       REAL,

    core_cohort       INTEGER,
    core_index        REAL,
    core_level        TEXT,
    weighted_cohort   INTEGER,
    weighted_index    REAL,
    weighted_level    TEXT,

    ell_count         INTEGER,
    benchmark         TEXT,
    progress_rate     REAL,
    success_ratio     REAL,
    participation_rate REAL,
    met_95_percent    TEXT,
    level             TEXT,
    overall_status    TEXT,
    made_progress     TEXT,

    override_flag     TEXT,
    data_rep_flag     TEXT,
    partial_data_flag TEXT,
    count_zero_flag   TEXT,
    made_progress_flag TEXT,

    PRIMARY KEY (
        institution_id,
        year_id,
        indicator_id,
        COALESCE(subject_id, 0),
        COALESCE(subgroup_id, 0),
        COALESCE(cohort, '')
    ),

    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (indicator_id)   REFERENCES dim_indicator(indicator_id),
    FOREIGN KEY (subject_id)     REFERENCES dim_subject(subject_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);

CREATE INDEX IF NOT EXISTS idx_acc_inst_year
    ON fact_accountability(institution_id, year_id);

-- Assessments (EM ELA/MATH/SCIENCE, NYSAA, NYSESLAT, Regents, Total Cohort Regents)
CREATE TABLE IF NOT EXISTS fact_assessment (
    institution_id    TEXT NOT NULL,
    year_id           INTEGER NOT NULL,
    subject_id        INTEGER NOT NULL,
    subgroup_id       INTEGER NOT NULL,
    cohort            TEXT,

    total_count       INTEGER,
    not_tested        INTEGER,
    pct_not_tested    REAL,
    num_tested        INTEGER,
    pct_tested        REAL,

    level1_count      INTEGER,
    level1_pct        REAL,
    level2_count      INTEGER,
    level2_pct        REAL,
    level3_count      INTEGER,
    level3_pct        REAL,
    level4_count      INTEGER,
    level4_pct        REAL,
    level5_count      INTEGER,
    level5_pct        REAL,

    num_prof          INTEGER,
    per_prof          REAL,

    total_scale_scores REAL,
    mean_score        REAL,

    total_exempt      INTEGER,
    num_exempt_ntest  INTEGER,
    pct_exempt_ntest  REAL,
    num_exempt_test   INTEGER,
    pct_exempt_test   REAL,

    PRIMARY KEY (
        institution_id,
        year_id,
        subject_id,
        subgroup_id,
        COALESCE(cohort, '')
    ),

    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (subject_id)     REFERENCES dim_subject(subject_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);

CREATE INDEX IF NOT EXISTS idx_assess_inst_year
    ON fact_assessment(institution_id, year_id);

CREATE INDEX IF NOT EXISTS idx_assess_subject
    ON fact_assessment(subject_id);
