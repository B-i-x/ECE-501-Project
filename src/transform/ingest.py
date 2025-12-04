import sqlite3
from typing import Iterable, Dict, Any, Optional
from pathlib import Path

from transform.lookup import (
    get_or_create_year_id,
    get_or_create_grade_id,
    get_or_create_institution_id,
    get_or_create_subgroup_id,
    get_or_create_subject_id,
    get_or_create_indicator_id,
)

def populate_dim_year_from_baseline(conn_star: sqlite3.Connection, baseline_dbs: Iterable[Path]) -> None:
    seen_years = set()
    for db_path in baseline_dbs:
        src = sqlite3.connect(db_path)
        cur = src.cursor()
        # Try to detect columns called YEAR or report_school_year
        for table_name, col in [
            ("BEDS Day Enrollment", "YEAR"),
            ("Demographic Factors", "YEAR"),
            ("Attendance", "YEAR"),
            ("Average Class Size", "YEAR"),
            ("Free Reduced Price Lunch", "YEAR"),
            ("Instructional_Modalities", "YEAR"),
        ]:
            try:
                cur.execute(f"SELECT DISTINCT CAST({col} AS INTEGER) FROM '{table_name}'")
                for (year,) in cur.fetchall():
                    if year and year not in seen_years:
                        get_or_create_year_id(conn_star, year)
                        seen_years.add(year)
            except sqlite3.Error:
                continue

        # Grad rate db special year column
        try:
            cur.execute("SELECT DISTINCT report_school_year FROM GRAD_RATE_AND_OUTCOMES_2024")
            for (school_year_str,) in cur.fetchall():
                if school_year_str and "-" in school_year_str:
                    end_year = int(school_year_str.split("-")[-1]) + 2000
                    if end_year not in seen_years:
                        get_or_create_year_id(conn_star, end_year, school_year_str)
                        seen_years.add(end_year)
        except sqlite3.Error:
            pass

        src.close()


def populate_dim_institution_from_boces_and_grouping(
    conn_star: sqlite3.Connection,
    baseline_dbs: Iterable[Path],
) -> None:
    for db_path in baseline_dbs:
        src = sqlite3.connect(db_path)
        cur = src.cursor()

        # BOCES and N/RC tables
        try:
            cur.execute("SELECT DISTINCT ENTITY_CD, SCHOOL_NAME, DISTRICT_CD, DISTRICT_NAME, "
                        "BOCES_CD, BOCES_NAME, COUNTY_CD, COUNTY_NAME, NEEDS_INDEX, NEEDS_INDEX_DESCRIPTION "
                        "FROM 'BOCES and N/RC'")
            for row in cur.fetchall():
                entity_cd, school_name, district_cd, district_name, boces_cd, boces_name, county_cd, county_name, needs_idx, needs_desc = row
                if not entity_cd:
                    continue
                defaults = {
                    "district_cd": district_cd,
                    "district_name": district_name,
                    "boces_cd": boces_cd,
                    "boces_name": boces_name,
                    "county_cd": county_cd,
                    "county_name": county_name,
                    "needs_index": needs_idx,
                    "needs_index_desc": needs_desc,
                }
                get_or_create_institution_id(conn_star, entity_cd, school_name or "", defaults)
        except sqlite3.Error:
            pass

        # Institution Grouping tables
        try:
            cur.execute("SELECT DISTINCT INSTITUTION_ID, ENTITY_CD, ENTITY_NAME, GROUP_CODE, GROUP_NAME "
                        "FROM 'Institution Grouping'")
            for inst_id, entity_cd, entity_name, group_code, group_name in cur.fetchall():
                if not entity_cd:
                    continue
                defaults = {
                    "group_code": group_code,
                    "group_name": group_name,
                }
                # Ensure we use the INSTITUTION_ID if present
                cur_star = conn_star.cursor()
                cur_star.execute(
                    "SELECT institution_id FROM dim_institution WHERE entity_cd = ?",
                    (entity_cd,),
                )
                row = cur_star.fetchone()
                if row:
                    # update institution_id only if blank
                    continue
                # create using institution_id from source
                cur_star.execute(
                    """
                    INSERT OR IGNORE INTO dim_institution (
                        institution_id, entity_cd, entity_name, group_code, group_name
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (inst_id or entity_cd, entity_cd, entity_name or "", group_code, group_name),
                )
                conn_star.commit()
        except sqlite3.Error:
            pass

        src.close()

def ingest_enrollment_and_demographics(
    conn_star: sqlite3.Connection,
    enrollment_db: Path,
) -> None:
    src = sqlite3.connect(enrollment_db)
    cur = src.cursor()

    cur_star = conn_star.cursor()

    # BEDS Day Enrollment -> fact_enrollment
    try:
        cur.execute("SELECT ENTITY_CD, ENTITY_NAME, CAST(YEAR AS INTEGER), "
                    "PK, PKHALF, PKFULL, KHALF, KFULL, "
                    "\"1\", \"2\", \"3\", \"4\", \"5\", \"6\", \"7\", \"8\", \"9\", \"10\", \"11\", \"12\", "
                    "UGE, UGS "
                    "FROM 'BEDS Day Enrollment'")
        for row in cur.fetchall():
            (
                entity_cd, entity_name, year,
                pk, pk_half, pk_full, k_half, k_full,
                g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12,
                uge, ugs,
            ) = row

            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)

            # Helper to insert a grade
            def insert_grade(grade_code: str, program_type: Optional[str], value: Optional[float]) -> None:
                if value is None:
                    return
                grade_id = get_or_create_grade_id(conn_star, grade_code)
                cur_star.execute(
                    """
                    INSERT OR REPLACE INTO fact_enrollment (
                        institution_id, year_id, grade_id, program_type, enrollment_cnt
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (institution_id, year_id, grade_id, program_type, int(value)),
                )

            insert_grade("PK", "HALF", pk_half)
            insert_grade("PK", "FULL", pk_full)
            insert_grade("K", "HALF", k_half)
            insert_grade("K", "FULL", k_full)

            # grades 1-12
            grade_values = [g1, g2, g3, g4, g5, g6, g7, g8, g9, g10, g11, g12]
            for i, val in enumerate(grade_values, start=1):
                insert_grade(str(i), None, val)

            insert_grade("UGE", None, uge)
            insert_grade("UGS", None, ugs)

        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting BEDS Day Enrollment:", e)

    # Demographic Factors -> fact_demographics
    try:
        cur.execute("SELECT * FROM 'Demographic Factors'")
        col_names = [d[0] for d in cur.description]

        # Map column pairs NUM_x / PER_x to subgroup names
        pairs = []
        for col in col_names:
            if col.startswith("NUM_"):
                suffix = col[4:]
                per_col = "PER_" + suffix
                if per_col in col_names:
                    pairs.append((suffix, col, per_col))

        for row in cur.fetchall():
            row_dict = dict(zip(col_names, row))
            entity_cd = row_dict["ENTITY_CD"]
            entity_name = row_dict["ENTITY_NAME"]
            year = int(row_dict["YEAR"])
            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)

            for suffix, num_col, per_col in pairs:
                num_val = row_dict[num_col]
                per_val = row_dict[per_col]
                if num_val is None and per_val is None:
                    continue
                subgroup_name = suffix
                subgroup_type = "Demographic"
                subgroup_id = get_or_create_subgroup_id(conn_star, subgroup_name, None, subgroup_type)
                cur_star.execute(
                    """
                    INSERT OR REPLACE INTO fact_demographics (
                        institution_id, year_id, subgroup_id, count_value, pct_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        institution_id,
                        year_id,
                        subgroup_id,
                        int(num_val) if num_val is not None else 0,
                        float(per_val) if per_val is not None else 0.0,
                    ),
                )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Demographic Factors:", e)

    src.close()

def ingest_student_educator(
    conn_star: sqlite3.Connection,
    studed_db: Path,
) -> None:
    src = sqlite3.connect(studed_db)
    cur = src.cursor()
    cur_star = conn_star.cursor()

    # Attendance -> fact_student_metrics metric_code ATT_RATE
    try:
        cur.execute("SELECT ENTITY_CD, ENTITY_NAME, CAST(YEAR AS INTEGER), ATTENDANCE_RATE, DATA_REPORTED "
                    "FROM Attendance")
        for entity_cd, entity_name, year, rate, data_rep in cur.fetchall():
            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)
            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_student_metrics (
                    institution_id, year_id, metric_code, metric_value_num, metric_value_txt
                ) VALUES (?, ?, 'ATT_RATE', ?, ?)
                """,
                (institution_id, year_id, rate, data_rep),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Attendance:", e)

    # Suspensions
    try:
        cur.execute("SELECT ENTITY_CD, ENTITY_NAME, CAST(YEAR AS INTEGER), "
                    "NUM_SUSPENSIONS, PER_SUSPENSIONS, DATA_REPORTED "
                    "FROM Suspensions")
        for entity_cd, entity_name, year, num_susp, per_susp, data_rep in cur.fetchall():
            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)
            cur_star.executemany(
                """
                INSERT OR REPLACE INTO fact_student_metrics (
                    institution_id, year_id, metric_code, metric_value_num, metric_value_txt
                ) VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (institution_id, year_id, "NUM_SUSP", num_susp, data_rep),
                    (institution_id, year_id, "PER_SUSP", per_susp, data_rep),
                ],
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Suspensions:", e)

    # Free Reduced Price Lunch
    try:
        cur.execute("SELECT ENTITY_CD, ENTITY_NAME, CAST(YEAR AS INTEGER), "
                    "NUM_FREE_LUNCH, PER_FREE_LUNCH, NUM_REDUCED_LUNCH, PER_REDUCED_LUNCH "
                    "FROM 'Free Reduced Price Lunch'")
        for entity_cd, entity_name, year, nf, pf, nr, pr in cur.fetchall():
            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)
            metrics = [
                ("NUM_FREE_LUNCH", nf),
                ("PER_FREE_LUNCH", pf),
                ("NUM_REDUCED_LUNCH", nr),
                ("PER_REDUCED_LUNCH", pr),
            ]
            for code, val in metrics:
                cur_star.execute(
                    """
                    INSERT OR REPLACE INTO fact_student_metrics (
                        institution_id, year_id, metric_code, metric_value_num, metric_value_txt
                    ) VALUES (?, ?, ?, ?, NULL)
                    """,
                    (institution_id, year_id, code, val),
                )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Free Reduced Price Lunch:", e)

    # Average Class Size -> dim_class_type + fact_class_size
    try:
        cur.execute("SELECT ENTITY_CD, ENTITY_NAME, CAST(YEAR AS INTEGER), "
                    "CLASS_DESCRIPTION, AVERAGE_CLASS_SIZE, DATA_REPORTED "
                    "FROM 'Average Class Size'")
        for entity_cd, entity_name, year, class_desc, avg_size, data_rep in cur.fetchall():
            institution_id = get_or_create_institution_id(conn_star, entity_cd, entity_name or "")
            year_id = get_or_create_year_id(conn_star, year)

            cur_star.execute(
                "SELECT class_type_id FROM dim_class_type WHERE class_desc = ?",
                (class_desc,),
            )
            row = cur_star.fetchone()
            if row:
                class_type_id = row[0]
            else:
                cur_star.execute(
                    "INSERT INTO dim_class_type (class_desc) VALUES (?)",
                    (class_desc,),
                )
                class_type_id = cur_star.lastrowid

            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_class_size (
                    institution_id, year_id, class_type_id, average_class_size, data_reported
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (institution_id, year_id, class_type_id, avg_size, data_rep),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Average Class Size:", e)

    # Staff
    try:
        cur.execute("SELECT ENTITY_CD, SCHOOL_NAME, CAST(YEAR AS INTEGER), "
                    "NUM_PRINC, NUM_TEACH, NUM_COUNSELORS, NUM_SOCIAL, "
                    "PER_ATTEND, PER_TURN_ALL, PER_TURN_FIVE_YRS "
                    "FROM Staff")
        for entity_cd, school_name, year, n_princ, n_teach, n_coun, n_soc, per_att, per_turn_all, per_turn_5 in cur.fetchall():
            institution_id = get_or_create_institution_id(conn_star, entity_cd, school_name or "")
            year_id = get_or_create_year_id(conn_star, year)
            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_staff_counts (
                    institution_id, year_id, num_principals, num_teachers,
                    num_counselors, num_social, per_attend, per_turn_all, per_turn_five_yrs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    year_id,
                    n_princ,
                    n_teach,
                    n_coun,
                    n_soc,
                    per_att,
                    per_turn_all,
                    per_turn_5,
                ),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Staff:", e)

    src.close()

def ingest_grad_rate(
    conn_star: sqlite3.Connection,
    grad_db: Path,
) -> None:
    src = sqlite3.connect(grad_db)
    cur = src.cursor()
    cur_star = conn_star.cursor()

    try:
        cur.execute("SELECT * FROM GRAD_RATE_AND_OUTCOMES_2024")
        cols = [d[0] for d in cur.description]

        for row in cur.fetchall():
            rec = dict(zip(cols, row))

            school_year_str = rec["report_school_year"]
            if school_year_str and "-" in school_year_str:
                end_year = int(school_year_str.split("-")[-1]) + 2000
            else:
                # fallback
                end_year = 2024
            year_id = get_or_create_year_id(conn_star, end_year, school_year_str)

            institution_id = get_or_create_institution_id(
                conn_star,
                rec["INSTITUTION_ID"],
                rec.get("aggregation_name") or rec.get("lea_name") or "",
                {"entity_cd": rec["INSTITUTION_ID"]},
            )

            subgroup_code = rec["subgroup_code"]
            subgroup_name = rec["subgroup_name"]
            subgroup_id = get_or_create_subgroup_id(conn_star, subgroup_name, subgroup_code)

            def to_int(val: Any) -> Optional[int]:
                if val in (None, "", "s"):
                    return None
                try:
                    return int(val)
                except ValueError:
                    return None

            def to_float(val: Any) -> Optional[float]:
                if val in (None, "", "s"):
                    return None
                try:
                    return float(val)
                except ValueError:
                    return None

            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_grad_outcomes (
                    institution_id, year_id,
                    aggregation_index, aggregation_type, aggregation_code, aggregation_name,
                    membership_code, membership_desc, subgroup_id,
                    enroll_cnt, grad_cnt, grad_pct,
                    local_cnt, local_pct, reg_cnt, reg_pct, reg_adv_cnt, reg_adv_pct,
                    non_diploma_cred_cnt, non_diploma_cred_pct,
                    still_enr_cnt, still_enr_pct,
                    ged_cnt, ged_pct,
                    dropout_cnt, dropout_pct
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    year_id,
                    rec["aggregation_index"],
                    rec["aggregation_type"],
                    rec["aggregation_code"],
                    rec["aggregation_name"],
                    rec["membership_code"],
                    rec["membership_desc"],
                    subgroup_id,
                    to_int(rec["enroll_cnt"]),
                    to_int(rec["grad_cnt"]),
                    to_float(rec["grad_pct"]),
                    to_int(rec["local_cnt"]),
                    to_float(rec["local_pct"]),
                    to_int(rec["reg_cnt"]),
                    to_float(rec["reg_pct"]),
                    to_int(rec["reg_adv_cnt"]),
                    to_float(rec["reg_adv_pct"]),
                    to_int(rec["non_diploma_credential_cnt"]),
                    to_float(rec["non_diploma_credential_pct"]),
                    to_int(rec["still_enr_cnt"]),
                    to_float(rec["still_enr_pct"]),
                    to_int(rec["ged_cnt"]),
                    to_float(rec["ged_pct"]),
                    to_int(rec["dropout_cnt"]),
                    to_float(rec["dropout_pct"]),
                ),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting GRAD_RATE_AND_OUTCOMES_2024:", e)

    src.close()

def ingest_reportcard(
    conn_star: sqlite3.Connection,
    reportcard_db: Path,
) -> None:
    src = sqlite3.connect(reportcard_db)
    cur = src.cursor()
    cur_star = conn_star.cursor()

    # Expenditures per Pupil -> fact_expenditures
    try:
        cur.execute("SELECT INSTITUTION_ID, ENTITY_CD, ENTITY_NAME, YEAR, "
                    "PUPIL_COUNT_TOT, FEDERAL_EXP, PER_FEDERAL_EXP, "
                    "STATE_LOCAL_EXP, PER_STATE_LOCAL_EXP, FED_STATE_LOCAL_EXP, "
                    "PER_FED_STATE_LOCAL_EXP, DATA_REPORTED_ENR, DATA_REPORTED_EXP "
                    "FROM 'Expenditures per Pupil'")
        for row in cur.fetchall():
            (
                inst_id, entity_cd, entity_name, year,
                pupil_count_tot, federal_exp, per_federal_exp,
                state_local_exp, per_state_local_exp, fed_state_local_exp,
                per_fed_state_local_exp, data_rep_enr, data_rep_exp,
            ) = row

            institution_id = get_or_create_institution_id(
                conn_star,
                entity_cd or inst_id,
                entity_name or "",
                {"institution_id": inst_id or entity_cd},
            )
            year_id = get_or_create_year_id(conn_star, int(year))

            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_expenditures (
                    institution_id, year_id,
                    pupil_count_tot, federal_exp, per_federal_exp,
                    state_local_exp, per_state_local_exp,
                    fed_state_local_exp, per_fed_state_local_exp,
                    data_reported_enr, data_reported_exp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    year_id,
                    pupil_count_tot,
                    federal_exp,
                    per_federal_exp,
                    state_local_exp,
                    per_state_local_exp,
                    fed_state_local_exp,
                    per_fed_state_local_exp,
                    data_rep_enr,
                    data_rep_exp,
                ),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Expenditures per Pupil:", e)

    # Inexperienced Teachers and Principals -> fact_teacher_experience
    try:
        cur.execute("SELECT INSTITUTION_ID, ENTITY_CD, ENTITY_NAME, YEAR, "
                    "NUM_TEACH, NUM_TEACH_INEXP, PER_TEACH_INEXP, "
                    "TOT_TEACH_LOW, NUM_TEACH_LOW, PER_TEACH_LOW, "
                    "TOT_TEACH_HIGH, NUM_TEACH_HIGH, PER_TEACH_HIGH, "
                    "NUM_PRINC, NUM_PRINC_INEXP, PER_PRINC_INEXP, "
                    "TOT_PRINC_LOW, NUM_PRINC_LOW, PER_PRINC_LOW, "
                    "TOT_PRINC_HIGH, NUM_PRINC_HIGH, PER_PRINC_HIGH, "
                    "TEACH_DATA_REP_FLAG, PRIN_DATA_REP_FLAG "
                    "FROM 'Inexperienced Teachers and Principals'")
        for row in cur.fetchall():
            (
                inst_id, entity_cd, entity_name, year,
                num_teach, num_teach_inexp, per_teach_inexp,
                tot_teach_low, num_teach_low, per_teach_low,
                tot_teach_high, num_teach_high, per_teach_high,
                num_princ, num_princ_inexp, per_princ_inexp,
                tot_princ_low, num_princ_low, per_princ_low,
                tot_princ_high, num_princ_high, per_princ_high,
                teach_flag, princ_flag,
            ) = row

            institution_id = get_or_create_institution_id(
                conn_star,
                entity_cd or inst_id,
                entity_name or "",
                {"institution_id": inst_id or entity_cd},
            )
            year_id = get_or_create_year_id(conn_star, int(year))

            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_teacher_experience (
                    institution_id, year_id,
                    num_teachers_total, num_teachers_inexp, per_teachers_inexp,
                    tot_teach_low, num_teach_low, per_teach_low,
                    tot_teach_high, num_teach_high, per_teach_high,
                    num_principals, num_principals_inexp, per_principals_inexp,
                    tot_princ_low, num_princ_low, per_princ_low,
                    tot_princ_high, num_princ_high, per_princ_high,
                    teach_data_rep_flag, princ_data_rep_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    year_id,
                    num_teach,
                    num_teach_inexp,
                    per_teach_inexp,
                    tot_teach_low,
                    num_teach_low,
                    per_teach_low,
                    tot_teach_high,
                    num_teach_high,
                    per_teach_high,
                    num_princ,
                    num_princ_inexp,
                    per_princ_inexp,
                    tot_princ_low,
                    num_princ_low,
                    per_princ_low,
                    tot_princ_high,
                    num_princ_high,
                    per_princ_high,
                    teach_flag,
                    princ_flag,
                ),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Inexperienced Teachers and Principals:", e)

    # Teachers Teaching Out of Certification -> fact_teacher_out_of_cert
    try:
        cur.execute("SELECT INSTITUTION_ID, ENTITY_CD, ENTITY_NAME, YEAR, "
                    "NUM_TEACH_OC, NUM_OUT_CERT, PER_OUT_CERT, "
                    "TOT_OUT_CERT_LOW, NUM_OUT_CERT_LOW, PER_OUT_CERT_LOW, "
                    "TOT_OUT_CERT_HIGH, NUM_OUT_CERT_HIGH, PER_OUT_CERT_HIGH, "
                    "OUT_OF_CERT_DATA_REP_FLAG "
                    "FROM 'Teachers Teaching Out of Certification'")
        for row in cur.fetchall():
            (
                inst_id, entity_cd, entity_name, year,
                num_teach_oc, num_out_cert, per_out_cert,
                tot_low, num_low, per_low,
                tot_high, num_high, per_high,
                flag,
            ) = row

            institution_id = get_or_create_institution_id(
                conn_star,
                entity_cd or inst_id,
                entity_name or "",
                {"institution_id": inst_id or entity_cd},
            )
            year_id = get_or_create_year_id(conn_star, int(year))

            cur_star.execute(
                """
                INSERT OR REPLACE INTO fact_teacher_out_of_cert (
                    institution_id, year_id,
                    num_teach_oc, num_out_cert, per_out_cert,
                    tot_out_cert_low, num_out_cert_low, per_out_cert_low,
                    tot_out_cert_high, num_out_cert_high, per_out_cert_high,
                    data_rep_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    year_id,
                    num_teach_oc,
                    num_out_cert,
                    per_out_cert,
                    tot_low,
                    num_low,
                    per_low,
                    tot_high,
                    num_high,
                    per_high,
                    flag,
                ),
            )
        conn_star.commit()
    except sqlite3.Error as e:
        print("Error ingesting Teachers Out of Certification:", e)

    # You would continue in this function with the same pattern for:
    # - Chronic Absenteeism tables -> fact_accountability
    # - Core and Weighted Performance -> fact_accountability
    # - ELP tables -> fact_accountability
    # - Participation Rate tables -> fact_accountability
    # - Accountability Levels / Status / Status by Subgroup -> fact_accountability
    # - Annual EM ELA/MATH/SCI -> fact_assessment
    # - Annual NYSAA -> fact_assessment
    # - Annual NYSESLAT -> fact_assessment
    # - Annual Regents Exams -> fact_assessment
    # - Total Cohort Regents Exams -> fact_assessment
    # - Postsecondary Enrollment -> fact_postsecondary_enrollment

    src.close()
