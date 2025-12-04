PRAGMA foreign_keys = ON;

-- Detailed graduation outcomes
CREATE TABLE IF NOT EXISTS fact_grad_outcomes (
    institution_id      TEXT NOT NULL,
    year_id             INTEGER NOT NULL,
    aggregation_index   INTEGER,
    aggregation_type    TEXT,
    aggregation_code    TEXT,
    aggregation_name    TEXT,
    membership_code     TEXT,
    membership_desc     TEXT,
    subgroup_id         INTEGER NOT NULL,

    enroll_cnt          INTEGER,
    grad_cnt            INTEGER,
    grad_pct            REAL,
    local_cnt           INTEGER,
    local_pct           REAL,
    reg_cnt             INTEGER,
    reg_pct             REAL,
    reg_adv_cnt         INTEGER,
    reg_adv_pct         REAL,
    non_diploma_cred_cnt INTEGER,
    non_diploma_cred_pct REAL,
    still_enr_cnt       INTEGER,
    still_enr_pct       REAL,
    ged_cnt             INTEGER,
    ged_pct             REAL,
    dropout_cnt         INTEGER,
    dropout_pct         REAL,

    PRIMARY KEY (
        institution_id,
        year_id,
        COALESCE(aggregation_type, ''),
        COALESCE(aggregation_code, ''),
        COALESCE(membership_code, ''),
        subgroup_id
    ),

    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);

CREATE INDEX IF NOT EXISTS idx_grad_inst_year
    ON fact_grad_outcomes(institution_id, year_id);

-- HS grad rate (ACC HS Graduation Rate table)
CREATE TABLE IF NOT EXISTS fact_grad_rate_hs (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,
    subgroup_id      INTEGER NOT NULL,
    cohort           TEXT NOT NULL,

    cohort_count     INTEGER,
    grad_count       INTEGER,
    grad_rate        REAL,
    cohort_level     TEXT,
    override_flag    TEXT,
    wt_perf_flag     TEXT,

    PRIMARY KEY (institution_id, year_id, subgroup_id, cohort),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);

-- Postsecondary enrollment
CREATE TABLE IF NOT EXISTS fact_postsecondary_enrollment (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,
    membership_desc  TEXT NOT NULL,
    subgroup_id      INTEGER NOT NULL,

    total_grad_count INTEGER,
    nys_pub_2yr_cnt  INTEGER,
    per_nys_pub_2yr  REAL,
    nys_pub_4yr_cnt  INTEGER,
    per_nys_pub_4yr  REAL,
    nys_pvt_2yr_cnt  INTEGER,
    per_nys_pvt_2yr  REAL,
    nys_pvt_4yr_cnt  INTEGER,
    per_nys_pvt_4yr  REAL,
    out_2yr_cnt      INTEGER,
    per_out_2yr      REAL,
    out_4yr_cnt      INTEGER,
    per_out_4yr      REAL,
    tot_2yr_cnt      INTEGER,
    per_tot_2yr      REAL,
    tot_4yr_cnt      INTEGER,
    per_tot_4yr      REAL,
    tot_enroll_cnt   INTEGER,
    per_tot_enroll   REAL,

    PRIMARY KEY (institution_id, year_id, membership_desc, subgroup_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id),
    FOREIGN KEY (subgroup_id)    REFERENCES dim_subgroup(subgroup_id)
);
