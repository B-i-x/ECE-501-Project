# src/transform/__init__.py
from pathlib import Path
import sqlite3
from webbrowser import get

from app import AppConfig
from transform.setup import (
    apply_schema,
    bootstrap_static_dimensions,
)
from transform.ingest import (
    populate_dim_year_from_baseline,
    populate_dim_institution_from_boces_and_grouping,
    ingest_enrollment_and_demographics,
    ingest_student_educator,
    ingest_grad_rate,
    ingest_reportcard,
)

from load.convert_to_sqlite import (
    get_datalink_sqlite_path,
)

def main():
    """
    Transform bad schema to star schema
    """


    # Create star DB and schema
    star_db_path = AppConfig.star_schema + "/star_schema.db"
    Path(star_db_path).parent.mkdir(parents=True, exist_ok=True)
    conn_star = sqlite3.connect(star_db_path)
    apply_schema(conn_star)
    bootstrap_static_dimensions(conn_star)

    from app.datasets import ENROLLMENT_23_24, GRADUATION_RATE_23_24, REPORT_CARD_23_24, STUDENT_EDUCATOR_DATABASE_23_24
    # Populate dim_year and dim_institution using all baseline dbs
    enrollment_db = get_datalink_sqlite_path(ENROLLMENT_23_24)
    grad_rate_db = get_datalink_sqlite_path(GRADUATION_RATE_23_24)
    reportcard_db = get_datalink_sqlite_path(REPORT_CARD_23_24)
    studed_db = get_datalink_sqlite_path(STUDENT_EDUCATOR_DATABASE_23_24)
    baseline_paths = [
        get_datalink_sqlite_path(ENROLLMENT_23_24),
        get_datalink_sqlite_path(GRADUATION_RATE_23_24),
        get_datalink_sqlite_path(REPORT_CARD_23_24),
        get_datalink_sqlite_path(STUDENT_EDUCATOR_DATABASE_23_24),
    ]
    populate_dim_year_from_baseline(conn_star, baseline_paths)
    populate_dim_institution_from_boces_and_grouping(conn_star, baseline_paths)

    # Ingest facts
    ingest_enrollment_and_demographics(conn_star, enrollment_db)
    ingest_student_educator(conn_star, studed_db)
    ingest_grad_rate(conn_star, grad_rate_db)
    ingest_reportcard(conn_star, reportcard_db)

    conn_star.close()