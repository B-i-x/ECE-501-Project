#!/usr/bin/env python3
import sys
import argparse
import statistics
import time
from typing import List, Optional, Dict
from types import ModuleType

import sqlite3

from execute.sql import run_sql, debug_sql, load_sql_sequence
from app.queries import QuerySpec
from load.convert_to_sqlite import convert_datalink_to_sqlite, get_datalink_sqlite_path
from ingest.downloader import fetch_accdb_from_datalink
from app import AppConfig
from reporting.models import QueryLaunch, ResultRecord, DataReportingModel, create_result_record, create_launch_from_query
from reporting.setup import get_database_connection
from reporting.operations import create_query_launch, insert_new_result_record
# ---------- Runner API ----------

def run_queryspec(
    spec: QuerySpec,
    runs: int,
    dataset_limits: List[int],
    timeout_s: Optional[int] = 300,
    num_lines_to_preview: int = 5,
) -> DataReportingModel:
    data_reporting_conn = get_database_connection()
    launch = create_query_launch(data_reporting_conn, create_launch_from_query(spec))

    results = []
    print(f"\n[RUN] {spec.name} v{spec.version}  folder={spec.sql_folder}  runs={runs}  timeout={timeout_s}s")

    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA temp_store=MEMORY;")
    conn.execute("PRAGMA cache_size=-64000;")
    conn.execute("PRAGMA journal_mode=OFF;")
    conn.execute("PRAGMA synchronous=OFF;")
    conn.row_factory = None

    for dataset in spec.dependant_datasets:
        dataset_sqlite_path = get_datalink_sqlite_path(dataset)  # Ensure dataset is materialized

        if not dataset_sqlite_path.exists():
            print(f"Dataset SQLite not found for {dataset.folder_name}, going to download and convert...")
            fetch_accdb_from_datalink(dataset)
            dataset_sqlite_path = convert_datalink_to_sqlite(dataset, verbose=True)

        run_sql(
            conn,
            f"ATTACH DATABASE '{dataset_sqlite_path.as_posix()}' AS '{dataset.folder_name}';")

    # Load SQL texts and keep filenames in the same order for logging
    sql_texts = load_sql_sequence(spec.sql_folder, spec.sql_file_sequence)
    sql_filenames = list(spec.sql_file_sequence)

    latencies = []
    for limit in dataset_limits:
        print(f"\n[INFO] Dataset limit: {limit:,}")
        latencies = []
        for r in range(1, runs + 1):
            t0 = time.perf_counter()
            for i, (fname, sql) in enumerate(zip(sql_filenames, sql_texts), start=1):
                desc = (
                    f"{spec.name} rows={limit:,} run {r}/{runs} "
                    f"part {i}/{len(sql_texts)} [{fname}]"
                )
                run_sql(
                    conn,
                    sql,
                    desc=desc,
                    params={"n_limit": int(limit)},
                    preview=num_lines_to_preview,
                    timeout_s=timeout_s,
                )

            elapsed = time.perf_counter() - t0
            #this is the end of a result and should be stored as a result record   
            rec = create_result_record(
                launch_ID=launch.launch_ID,
                dataset_size=limit,
                run_index=r,
                elapsed_seconds=elapsed,
            )
            results.append(rec)

            latencies.append(elapsed)
            print(f"[RESULT] {spec.name} rows={limit:,} run {r}/{runs} time={elapsed:.3f}s")
            conn.execute("PRAGMA optimize;")
            conn.execute("PRAGMA shrink_memory;")

    for r in results:
        insert_new_result_record(data_reporting_conn, r)

    latencies.sort()
    p50 = statistics.median(latencies)
    from math import ceil
    idx = max(0, min(len(latencies) - 1, ceil(0.95 * len(latencies)) - 1))
    p95 = latencies[idx]
    print(f"[SUMMARY] {spec.name} rows={limit:,} P50={p50:.3f}s P95={p95:.3f}s over {runs} runs")

    data_reporting_conn.close()
    # last_result = {"name": spec.name, "version": spec.version, "runs": runs, "p50": p50, "p95": p95}
    return DataReportingModel(query_launch=launch, result_records=results)


import app.queries as QUERIES_MODULE
from types import ModuleType

def get_query_specs_by_name(mod: ModuleType) -> Dict[str, QuerySpec]:
    """Return {spec.name: QuerySpec} mapping, so you do not need the variable name."""
    return {
        obj.name: obj
        for _, obj in vars(mod).items()
        if isinstance(obj, QuerySpec)
    }

def run_queryspecs() -> Dict[str, DataReportingModel]:
    exec_config = AppConfig.load_execution_config()
    all_query_specs = get_query_specs_by_name(QUERIES_MODULE)
    results = {}
    for spec_name in exec_config.queries_to_run:
        if spec_name not in all_query_specs:
            raise ValueError(f"Query name '{spec_name}' not found in app.queries Check your execution_config.yaml.")
        spec = all_query_specs[spec_name]
        print(f"\n[INFO] Running {spec.name} with dataset limits: {exec_config.dataset_partitions_per_query[spec.name]}")
        data = run_queryspec(
            spec,
            runs=exec_config.runs_per_query,
            dataset_limits=exec_config.dataset_partitions_per_query[spec.name],
            timeout_s=exec_config.timeout_seconds,
            num_lines_to_preview=5,
        )
        results[spec.name] = data
    return results


def cli_run_queryspec() -> None:
    """
    CLI entry point to run a single QuerySpec by name and version.

    Example:
        run-queryspec baseline_query2 2.0
        run-queryspec baseline_query2 2.0 --runs 5 --dataset-limits 10000,50000
    """
    parser = argparse.ArgumentParser(
        description="Run a single QuerySpec by name and version."
    )
    parser.add_argument(
        "query_name",
        help="Name of the query spec (matches QuerySpec.name)",
    )
    parser.add_argument(
        "version",
        help="Version string to match (matches QuerySpec.version)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Number of runs (defaults to runs_per_query from execution_config).",
    )
    parser.add_argument(
        "--dataset-limits",
        type=str,
        default=None,
        help=(
            "Comma-separated dataset sizes, e.g. '10000,50000'. "
            "Defaults to dataset_partitions_per_query[query_name] from execution_config."
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Timeout in seconds (defaults to timeout_seconds from execution_config).",
    )
    parser.add_argument(
        "--preview",
        type=int,
        default=5,
        help="Number of rows to preview per SQL file (default: 5).",
    )

    args = parser.parse_args()

    # Load execution config for defaults
    exec_config = AppConfig.load_execution_config()

    # Collect all QuerySpec objects from the module
    all_specs = [
        obj
        for _, obj in vars(QUERIES_MODULE).items()
        if isinstance(obj, QuerySpec)
    ]

    # Filter by query_name
    matching_name = [spec for spec in all_specs if spec.name == args.query_name]
    if not matching_name:
        available_names = sorted({spec.name for spec in all_specs})
        parser.error(
            f"Unknown query_name '{args.query_name}'. "
            f"Available query names: {', '.join(available_names)}"
        )

    # Filter by version
    spec = None
    for candidate in matching_name:
        if str(candidate.version) == str(args.version):
            spec = candidate
            break

    if spec is None:
        available_versions = sorted({str(s.version) for s in matching_name})
        parser.error(
            f"No QuerySpec found for name='{args.query_name}' "
            f"with version='{args.version}'. "
            f"Available versions for this name: {', '.join(available_versions)}"
        )

    # Resolve dataset limits
    if args.dataset_limits:
        dataset_limits = [int(x) for x in args.dataset_limits.split(",") if x.strip()]
    else:
        dataset_limits = exec_config.dataset_partitions_per_query.get(
            spec.name, [0]
        )

    # Resolve runs and timeout
    runs = args.runs if args.runs is not None else exec_config.runs_per_query
    timeout_s = args.timeout if args.timeout is not None else exec_config.timeout_seconds

    # Run the query spec
    print(
        f"[INFO] Running {spec.name} v{spec.version} "
        f"with dataset limits {dataset_limits} for {runs} runs"
    )
    _ = run_queryspec(
        spec,
        runs=runs,
        dataset_limits=dataset_limits,
        timeout_s=timeout_s,
        num_lines_to_preview=args.preview,
    )

    print(f"[DONE] {spec.name} v{spec.version} completed.")
    sys.exit(0)



# ---------- Script entry ----------
from app.queries import BASELINE_QUERY_1

def main():
    exec_config = AppConfig.load_execution_config()
    # print(exec_config.dataset_partitions_per_query)
    if BASELINE_QUERY_1.name in exec_config.dataset_partitions_per_query:
        print(f"\n[INFO] Running {BASELINE_QUERY_1.name} with dataset limits: {exec_config.dataset_partitions_per_query[BASELINE_QUERY_1.name]}")
        #this is 1 query launch
        data = run_queryspec(
            BASELINE_QUERY_1,
            runs=exec_config.runs_per_query,
            dataset_limits=exec_config.dataset_partitions_per_query[BASELINE_QUERY_1.name],
            timeout_s=exec_config.timeout_seconds,
            num_lines_to_preview=5,
            )

    # with open("results.csv", "w", newline="") as f:
    #     w = csv.writer(f)
    #     w.writerow(["query_name", "version", "runs", "P50_seconds", "P95_seconds"])
    #     w.writerow([res["name"], res["version"], res["runs"], f"{res['p50']:.6f}", f"{res['p95']:.6f}"])

    # print(f"\n[INFO] Results saved to results.csv")

if __name__ == "__main__":
    main()
