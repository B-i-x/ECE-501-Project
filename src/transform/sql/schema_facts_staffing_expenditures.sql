PRAGMA foreign_keys = ON;

-- Staff counts
CREATE TABLE IF NOT EXISTS fact_staff_counts (
    institution_id   TEXT NOT NULL,
    year_id          INTEGER NOT NULL,

    num_principals   REAL,
    num_teachers     REAL,
    num_counselors   REAL,
    num_social       REAL,
    per_attend       REAL,
    per_turn_all     REAL,
    per_turn_five_yrs REAL,

    PRIMARY KEY (institution_id, year_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id)
);

-- Teacher and principal experience
CREATE TABLE IF NOT EXISTS fact_teacher_experience (
    institution_id      TEXT NOT NULL,
    year_id             INTEGER NOT NULL,

    num_teachers_total  REAL,
    num_teachers_inexp  REAL,
    per_teachers_inexp  REAL,

    tot_teach_low       INTEGER,
    num_teach_low       INTEGER,
    per_teach_low       REAL,
    tot_teach_high      INTEGER,
    num_teach_high      INTEGER,
    per_teach_high      REAL,

    num_principals      REAL,
    num_principals_inexp REAL,
    per_principals_inexp REAL,
    tot_princ_low       INTEGER,
    num_princ_low       REAL,
    per_princ_low       REAL,
    tot_princ_high      INTEGER,
    num_princ_high      REAL,
    per_princ_high      REAL,

    teach_data_rep_flag TEXT,
    princ_data_rep_flag TEXT,

    PRIMARY KEY (institution_id, year_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id)
);

-- Teachers teaching out of certification
CREATE TABLE IF NOT EXISTS fact_teacher_out_of_cert (
    institution_id        TEXT NOT NULL,
    year_id               INTEGER NOT NULL,

    num_teach_oc          REAL,
    num_out_cert          REAL,
    per_out_cert          REAL,
    tot_out_cert_low      INTEGER,
    num_out_cert_low      REAL,
    per_out_cert_low      REAL,
    tot_out_cert_high     INTEGER,
    num_out_cert_high     REAL,
    per_out_cert_high     REAL,
    data_rep_flag         TEXT,

    PRIMARY KEY (institution_id, year_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id)
);

-- Expenditures
CREATE TABLE IF NOT EXISTS fact_expenditures (
    institution_id       TEXT NOT NULL,
    year_id              INTEGER NOT NULL,

    pupil_count_tot      REAL,
    federal_exp          REAL,
    per_federal_exp      REAL,
    state_local_exp      REAL,
    per_state_local_exp  REAL,
    fed_state_local_exp  REAL,
    per_fed_state_local_exp REAL,

    data_reported_enr    TEXT,
    data_reported_exp    TEXT,

    PRIMARY KEY (institution_id, year_id),
    FOREIGN KEY (institution_id) REFERENCES dim_institution(institution_id),
    FOREIGN KEY (year_id)        REFERENCES dim_year(year_id)
);
