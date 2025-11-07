# queries.py
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Iterable
import yaml

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

from app.datasets import ENROLLMENT_23_24, REPORT_CARD_23_24
BASELINE_QUERY_1 = QuerySpec(
    name="baseline_query1",
    sql_folder=Path("sql/baseline_query1"),
    sql_file_sequence=[
        "part1.sql", 
        "part2.sql", 
        "part3.sql"],
    version="1.0",
    dependant_datasets=[ENROLLMENT_23_24, REPORT_CARD_23_24],
)