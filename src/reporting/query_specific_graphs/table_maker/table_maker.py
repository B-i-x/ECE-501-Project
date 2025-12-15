#!/usr/bin/env python3
import argparse
import csv
import math
import sqlite3
import statistics
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from reporting.setup import get_database_connection  # uses AppConfig.result_db_path


DEFAULT_DATASET_SIZES = [10000, 50000, 100000, 200000, 300000, 400000, 500000]


@dataclass(frozen=True)
class QuerySpec:
    name: str
    version: str


@dataclass(frozen=True)
class ComparisonSpec:
    label: str
    baseline: QuerySpec
    star: QuerySpec


COMPARISONS: List[ComparisonSpec] = [
    ComparisonSpec(
        label="query1",
        baseline=QuerySpec("baseline_query1", "1.1"),
        star=QuerySpec("star_query1", "2.0"),
    ),
    ComparisonSpec(
        label="query2",
        baseline=QuerySpec("baseline_query2", "2.2"),
        star=QuerySpec("star_query2", "1.0"),
    ),
    ComparisonSpec(
        label="query3",
        baseline=QuerySpec("baseline_query3", "1.0"),
        star=QuerySpec("star_query3", "0.0"),
    ),
]


def nearest_rank_percentile(sorted_values: List[float], p: int) -> float:
    """Excel-style nearest-rank percentile on a sorted list."""
    if not sorted_values:
        return float("nan")
    if p <= 0:
        return sorted_values[0]
    if p >= 100:
        return sorted_values[-1]
    k = math.ceil(p / 100.0 * len(sorted_values)) - 1
    k = max(0, min(len(sorted_values) - 1, k))
    return sorted_values[k]


def get_launch_ids(
    cur: sqlite3.Cursor, query_name: str, query_version: str, latest_only: bool
) -> List[int]:
    if latest_only:
        row = cur.execute(
            """
            SELECT launch_ID
            FROM QueryLaunch
            WHERE query_name = ? AND query_version = ?
            ORDER BY datetime(timestamp) DESC
            LIMIT 1;
            """,
            (query_name, query_version),
        ).fetchone()
        if not row:
            raise ValueError(f"No launches found for {query_name} v{query_version}")
        return [int(row[0])]

    rows = cur.execute(
        """
        SELECT launch_ID
        FROM QueryLaunch
        WHERE query_name = ? AND query_version = ?
        ORDER BY datetime(timestamp) ASC;
        """,
        (query_name, query_version),
    ).fetchall()

    launch_ids = [int(r[0]) for r in rows]
    if not launch_ids:
        raise ValueError(f"No launches found for {query_name} v{query_version}")
    return launch_ids


def compute_percentiles_for_query(
    cur: sqlite3.Cursor,
    query_name: str,
    query_version: str,
    *,
    latest_only: bool,
) -> Tuple[Dict[int, Tuple[float, float]], int]:
    """
    Returns:
      - per_size: {dataset_size: (p50, p95)}
      - num_runs: total number of QueryResult rows included
    """
    launch_ids = get_launch_ids(cur, query_name, query_version, latest_only=latest_only)

    placeholders = ",".join("?" * len(launch_ids))
    rows = cur.execute(
        f"""
        SELECT dataset_size, elapsed_seconds
        FROM QueryResult
        WHERE launch_ID IN ({placeholders})
          AND elapsed_seconds IS NOT NULL;
        """,
        launch_ids,
    ).fetchall()

    num_runs = len(rows)
    by_size: Dict[int, List[float]] = defaultdict(list)
    for ds, sec in rows:
        by_size[int(ds)].append(float(sec))

    per_size: Dict[int, Tuple[float, float]] = {}
    for ds, vals in by_size.items():
        vals_sorted = sorted(vals)
        p50 = statistics.median(vals_sorted)
        p95 = nearest_rank_percentile(vals_sorted, 95)
        per_size[ds] = (p50, p95)

    return per_size, num_runs


def fmt_float(x: Optional[float]) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return f"{x:.6f}"


def export_csv(out_path: str, dataset_sizes: List[int], latest_only: bool) -> None:
    con = get_database_connection()
    try:
        cur = con.cursor()

        with open(out_path, "w", newline="") as f:
            w = csv.writer(f)

            w.writerow(
                [
                    "comparison",
                    "dataset_size",
                    "baseline_name",
                    "baseline_version",
                    "baseline_p50_s",
                    "baseline_p95_s",
                    "baseline_num_runs",
                    "star_name",
                    "star_version",
                    "star_p50_s",
                    "star_p95_s",
                    "star_num_runs",
                ]
            )

            for comp in COMPARISONS:
                base_map, base_runs = compute_percentiles_for_query(
                    cur,
                    comp.baseline.name,
                    comp.baseline.version,
                    latest_only=latest_only,
                )
                star_map, star_runs = compute_percentiles_for_query(
                    cur,
                    comp.star.name,
                    comp.star.version,
                    latest_only=latest_only,
                )

                for ds in dataset_sizes:
                    base_p50, base_p95 = base_map.get(ds, (float("nan"), float("nan")))
                    star_p50, star_p95 = star_map.get(ds, (float("nan"), float("nan")))

                    w.writerow(
                        [
                            comp.label,
                            ds,
                            comp.baseline.name,
                            comp.baseline.version,
                            fmt_float(base_p50),
                            fmt_float(base_p95),
                            base_runs,
                            comp.star.name,
                            comp.star.version,
                            fmt_float(star_p50),
                            fmt_float(star_p95),
                            star_runs,
                        ]
                    )

        print(f"Wrote {out_path}")
        mode = "latest launch only" if latest_only else "all launches"
        print(f"Mode: {mode}")
        print(f"Dataset sizes: {dataset_sizes}")

    finally:
        con.close()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Export P50/P95 results for baseline vs star query comparisons to CSV."
    )
    p.add_argument(
        "--out",
        default="results_table_data.csv",
        help="Output CSV path (default: results_table_data.csv)",
    )
    p.add_argument(
        "--all-launches",
        action="store_true",
        help="Aggregate over all launches instead of only the latest launch per query/version",
    )
    p.add_argument(
        "--sizes",
        default=",".join(str(x) for x in DEFAULT_DATASET_SIZES),
        help="Comma-separated dataset sizes to include",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    sizes = [int(s.strip()) for s in args.sizes.split(",") if s.strip()]
    latest_only = not args.all_launches
    export_csv(args.out, sizes, latest_only=latest_only)


if __name__ == "__main__":
    main()
