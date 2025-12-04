from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Dict, Any, Optional

# Static variables pointing to SQL files
SCHEMA_CORE_SQL = "schema_core.sql"
SCHEMA_FACTS_ENROLLMENT_DEMOGRAPHICS_SQL = "schema_facts_enrollment_demographics.sql"
SCHEMA_FACTS_GRAD_POSTSECONDARY_SQL = "schema_facts_grad_postsecondary.sql"
SCHEMA_FACTS_ASSESSMENT_ACCOUNTABILITY_SQL = "schema_facts_assessment_accountability.sql"
SCHEMA_FACTS_STAFFING_EXPENDITURES_SQL = "schema_facts_staffing_expenditures.sql"

SQL_DIR = Path(__file__).resolve().parent / "sql"


from app.datasets import DataLink

def read_sql_file(filename: str) -> str:
    path = SQL_DIR / filename
    with path.open("r", encoding="utf8") as f:
        return f.read()


def apply_schema(conn: sqlite3.Connection) -> None:
    scripts = [
        SCHEMA_CORE_SQL,
        SCHEMA_FACTS_ENROLLMENT_DEMOGRAPHICS_SQL,
        SCHEMA_FACTS_GRAD_POSTSECONDARY_SQL,
        SCHEMA_FACTS_ASSESSMENT_ACCOUNTABILITY_SQL,
        SCHEMA_FACTS_STAFFING_EXPENDITURES_SQL,
    ]
    cur = conn.cursor()
    for fname in scripts:
        sql = read_sql_file(fname)
        cur.executescript(sql)
    conn.commit()

def get_or_create_year_id(conn: sqlite3.Connection, year: int, school_year: Optional[str] = None) -> int:
    if school_year is None:
        school_year = f"{year-1}-{str(year)[-2:]}"
    cur = conn.cursor()
    cur.execute("SELECT year_id FROM dim_year WHERE report_year = ?", (year,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_year (report_year, school_year) VALUES (?, ?)",
        (year, school_year),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_grade_id(conn: sqlite3.Connection, grade_code: str, grade_label: Optional[str] = None) -> int:
    if grade_label is None:
        grade_label = grade_code
    cur = conn.cursor()
    cur.execute("SELECT grade_id FROM dim_grade WHERE grade_code = ?", (grade_code,))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_grade (grade_code, grade_label) VALUES (?, ?)",
        (grade_code, grade_label),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_institution_id(
    conn: sqlite3.Connection,
    entity_cd: str,
    entity_name: str,
    defaults: Optional[Dict[str, Any]] = None,
) -> str:
    cur = conn.cursor()
    cur.execute(
        "SELECT institution_id FROM dim_institution WHERE entity_cd = ?",
        (entity_cd,),
    )
    row = cur.fetchone()
    if row:
        return row[0]

    # Use ENTITY_CD as institution_id if no other ID is available
    institution_id = entity_cd
    cols = ["institution_id", "entity_cd", "entity_name"]
    vals = [institution_id, entity_cd, entity_name]

    if defaults:
        for k, v in defaults.items():
            cols.append(k)
            vals.append(v)

    sql = f"INSERT INTO dim_institution ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))})"
    cur.execute(sql, vals)
    conn.commit()
    return institution_id


def get_or_create_subgroup_id(
    conn: sqlite3.Connection,
    subgroup_name: str,
    subgroup_code: Optional[str] = None,
    subgroup_type: str = "Unknown",
) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT subgroup_id FROM dim_subgroup WHERE subgroup_name = ? AND IFNULL(subgroup_code,'') = IFNULL(?, '')",
        (subgroup_name, subgroup_code),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_subgroup (subgroup_code, subgroup_name, subgroup_type) VALUES (?, ?, ?)",
        (subgroup_code, subgroup_name, subgroup_type),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_subject_id(
    conn: sqlite3.Connection,
    subject_code: str,
    subject_name: str,
    assessment_name: Optional[str] = None,
    grade_span: Optional[str] = None,
    is_hs: int = 0,
) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT subject_id FROM dim_subject WHERE subject_code = ?",
        (subject_code,),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_subject (subject_code, subject_name, assessment_name, grade_span, is_hs) "
        "VALUES (?, ?, ?, ?, ?)",
        (subject_code, subject_name, assessment_name, grade_span, is_hs),
    )
    conn.commit()
    return cur.lastrowid


def get_or_create_indicator_id(
    conn: sqlite3.Connection,
    indicator_code: str,
    indicator_name: str,
    domain: str,
) -> int:
    cur = conn.cursor()
    cur.execute(
        "SELECT indicator_id FROM dim_indicator WHERE indicator_code = ?",
        (indicator_code,),
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute(
        "INSERT INTO dim_indicator (indicator_code, indicator_name, domain) VALUES (?, ?, ?)",
        (indicator_code, indicator_name, domain),
    )
    conn.commit()
    return cur.lastrowid

def bootstrap_static_dimensions(conn: sqlite3.Connection) -> None:
    # Grades PK, K, 1-12, UGE, UGS
    grade_codes = ["PK", "K"] + [str(i) for i in range(1, 13)] + ["UGE", "UGS"]
    for code in grade_codes:
        get_or_create_grade_id(conn, code)

    # Some common subjects - extend as needed
    subjects = [
        ("EM_ELA", "English Language Arts (3-8)", "Annual EM ELA", "3-8", 0),
        ("EM_MATH", "Mathematics (3-8)", "Annual EM MATH", "3-8", 0),
        ("EM_SCI", "Science (3-8)", "Annual EM SCIENCE", "3-8", 0),
        ("NYSAA_ELA", "NYSAA ELA", "Annual NYSAA", "3-8", 0),
        ("NYSAA_MATH", "NYSAA Math", "Annual NYSAA", "3-8", 0),
        ("NYSAA_SCI", "NYSAA Science", "Annual NYSAA", "3-8", 0),
        ("NYSESLAT", "NYSESLAT", "Annual NYSESLAT", "K-12", 0),
        ("REGENTS", "Regents Exam", "Annual Regents Exams", "HS", 1),
        ("COHORT_REGENTS", "Cohort Regents", "Total Cohort Regents", "HS", 1),
    ]
    for code, name, assess, span, is_hs in subjects:
        get_or_create_subject_id(conn, code, name, assess, span, is_hs)

    # Common indicators - extend as needed
    indicators = [
        ("CA_EM", "Chronic Absenteeism EM", "Accountability"),
        ("CA_HS", "Chronic Absenteeism HS", "Accountability"),
        ("PERF_CORE_EM", "Core Performance EM", "Accountability"),
        ("PERF_CORE_HS", "Core Performance HS", "Accountability"),
        ("PERF_WEIGHTED_EM", "Weighted Performance EM", "Accountability"),
        ("PERF_WEIGHTED_HS", "Weighted Performance HS", "Accountability"),
        ("ELP_EM", "English Learner Progress EM", "Accountability"),
        ("ELP_HS", "English Learner Progress HS", "Accountability"),
        ("PART_EM", "Participation EM", "Accountability"),
        ("PART_HS", "Participation HS", "Accountability"),
        ("ACC_LEVEL", "Accountability Level", "Accountability"),
        ("ACC_STATUS", "Accountability Status", "Accountability"),
        ("ACC_STATUS_SUB", "Accountability Status by Subgroup", "Accountability"),
        ("GRAD_RATE_HS", "Graduation Rate HS", "Graduation"),
    ]
    for code, name, domain in indicators:
        get_or_create_indicator_id(conn, code, name, domain)

