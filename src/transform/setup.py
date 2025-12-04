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

from transform.lookup import (
    get_or_create_year_id,
    get_or_create_grade_id,
    get_or_create_institution_id,
    get_or_create_subgroup_id,
    get_or_create_subject_id,
    get_or_create_indicator_id,
)

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

