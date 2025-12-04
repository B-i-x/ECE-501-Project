# queries.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Iterable

from app.datasets import DataLink

@dataclass(frozen=True)
class QuerySpec:
    name: str
    sql_folder: Path
    sql_file_sequence: List[str]
    version: str
    dependant_datasets: List[DataLink] = None

    def files(self) -> List[Path]:
        return [self.sql_folder / f for f in self.sql_file_sequence]

from app.datasets import ENROLLMENT_23_24, REPORT_CARD_23_24, STUDENT_EDUCATOR_DATABASE_23_24

BASELINE_QUERY_1 = QuerySpec(
    name="baseline_query1",
    sql_folder=Path("sql/baseline_query1"),
    sql_file_sequence = [
        "reset.sql",
        "demo_view.sql",
        "create_math_src.sql",
        "create_math_overall.sql",
        "create_math_outcome.sql",
        "create_pairs_year.sql",
        "correlations.sql",
    ],
    version="1.1",
    dependant_datasets=[ENROLLMENT_23_24, REPORT_CARD_23_24],
)

BASELINE_QUERY_2_V1 = QuerySpec(
    name="baseline_query2",
    sql_folder=Path("sql/baseline_query2"),
    sql_file_sequence = [
        "query.sql",
    ],
    version="1.2",
    dependant_datasets=[REPORT_CARD_23_24,STUDENT_EDUCATOR_DATABASE_23_24],
)

BASELINE_QUERY_2_V2 = QuerySpec(
    name="baseline_query2",
    sql_folder=Path("sql/baseline_query2"),
    sql_file_sequence = [
        "correlation.sql",
    ],
    version="2.2",
    dependant_datasets=[REPORT_CARD_23_24,STUDENT_EDUCATOR_DATABASE_23_24],
)

BASELINE_QUERY_3 = QuerySpec(
    name="baseline_query3",
    sql_folder=Path("sql/baseline_query3"),
    sql_file_sequence = [
        "correlation.sql",
    ],
    version="1.0",
    dependant_datasets=[REPORT_CARD_23_24],
)