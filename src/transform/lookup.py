import sqlite3
from typing import Iterable, Dict, Any, Optional

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