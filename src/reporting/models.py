from dataclasses import dataclass
from turtle import st

@dataclass(frozen=True)
class QueryLaunch:
    launch_ID: str
    timestamp: str
    query_name: str
    query_version: str
    status: str

@dataclass(frozen=True)
class ResultRecord:
    result_ID: str
    launch_ID: str
    dataset_size: int
    run_index: int
    elapsed_seconds: float

