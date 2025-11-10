from dataclasses import dataclass
import time

@dataclass
class QueryLaunch:
    launch_ID: str
    timestamp: str
    query_name: str
    query_version: str

@dataclass
class ResultRecord:
    result_ID: str
    launch_ID: str
    dataset_size: int
    run_index: int
    elapsed_seconds: float

@dataclass
class DataReportingModel:
    query_launch: QueryLaunch
    result_records: list[ResultRecord]

from app.queries import QuerySpec
def create_launch_from_query(query: QuerySpec) -> QueryLaunch:
    return QueryLaunch(
        launch_ID="",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        query_name=query.name,
        query_version=query.version,
    )

def create_result_record(
    launch_ID: str,
    dataset_size: int,
    run_index: int,
    elapsed_seconds: float,
) -> ResultRecord:
    return ResultRecord(
        result_ID="",
        launch_ID=launch_ID,
        dataset_size=dataset_size,
        run_index=run_index,
        elapsed_seconds=elapsed_seconds,
    )