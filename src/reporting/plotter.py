import sqlite3
from typing import List, Tuple
from collections import defaultdict
import statistics
import math
import matplotlib.pyplot as plt
import os
import argparse

from app import AppConfig
from reporting.setup import get_database_connection  # uses AppConfig.result_db_path


def _nearest_rank_percentile(sorted_values: List[float], p: int) -> float:
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


def _compute_query_percentiles(
    cur: sqlite3.Cursor,
    query_name: str,
    query_version: str,
    *,
    latest_only: bool,
) -> Tuple[List[int], List[float], List[float], int]:
    """
    Return (sizes, p50s, p95s, num_runs) for a given query name and version.
    """
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
        launch_ids = [row[0]]
    else:
        launch_ids = [
            r[0]
            for r in cur.execute(
                """
                SELECT launch_ID
                FROM QueryLaunch
                WHERE query_name = ? AND query_version = ?
                ORDER BY datetime(timestamp) ASC;
                """,
                (query_name, query_version),
            ).fetchall()
        ]
        if not launch_ids:
            raise ValueError(f"No launches found for {query_name} v{query_version}")

    # Fetch all results for those launches
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
    by_size = defaultdict(list)
    for ds, sec in rows:
        by_size[int(ds)].append(float(sec))

    if not by_size:
        raise ValueError(
            "No QueryResult rows with elapsed_seconds found for the selection."
        )

    sizes = sorted(by_size.keys())
    p50s, p95s = [], []
    for ds in sizes:
        vals = sorted(by_size[ds])
        p50s.append(statistics.median(vals))
        p95s.append(_nearest_rank_percentile(vals, 95))

    return sizes, p50s, p95s, num_runs


def plot_query_percentiles(
    query_name: str,
    query_version: str,
    *,
    latest_only: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot P50 and P95 elapsed_seconds vs dataset_size for a given query name and version.

    latest_only=True -> uses the most recent launch for that query/version.
    latest_only=False -> aggregates all launches for that query/version together.
    """
    try:
        os.mkdir(AppConfig.graphs)
    except FileExistsError:
        pass
    except FileNotFoundError:
        print("Error: Data directory does not exist.")

    con: sqlite3.Connection = get_database_connection()
    try:
        cur = con.cursor()

        sizes, p50s, p95s, num_runs = _compute_query_percentiles(
            cur, query_name, query_version, latest_only=latest_only
        )

        fig, ax = plt.subplots()
        ax.plot(sizes, p50s, marker="o", label="P50")
        ax.plot(sizes, p95s, marker="o", label="P95")
        ax.set_xlabel("Dataset size (rows)")
        ax.set_ylabel("Elapsed time (s)")
        ax.set_title(f"{query_name} v{query_version} - Runs:{num_runs}")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

        fig.savefig(
            f"{AppConfig.graphs}/{query_name}-v{query_version}.png",
            dpi=144,
            bbox_inches="tight",
        )

        return fig, ax
    finally:
        con.close()


def plot_two_query_percentiles(
    query1_name: str,
    query1_version: str,
    query2_name: str,
    query2_version: str,
    *,
    latest_only: bool = True,
) -> Tuple[plt.Figure, plt.Axes]:
    """
    Plot P50 and P95 elapsed_seconds vs dataset_size for two queries on the same figure.

    latest_only=True  -> use the most recent launch for each query/version.
    latest_only=False -> aggregate all launches for each query/version together.
    """
    try:
        os.mkdir(AppConfig.graphs)
    except FileExistsError:
        pass
    except FileNotFoundError:
        print("Error: Data directory does not exist.")

    con: sqlite3.Connection = get_database_connection()
    try:
        cur = con.cursor()

        s1, p50_1, p95_1, n1 = _compute_query_percentiles(
            cur, query1_name, query1_version, latest_only=latest_only
        )
        s2, p50_2, p95_2, n2 = _compute_query_percentiles(
            cur, query2_name, query2_version, latest_only=latest_only
        )

        fig, ax = plt.subplots()

        # Query 1
        ax.plot(
            s1,
            p50_1,
            marker="o",
            linestyle="-",
            label=f"{query1_name} v{query1_version} P50",
        )
        ax.plot(
            s1,
            p95_1,
            marker="o",
            linestyle="--",
            label=f"{query1_name} v{query1_version} P95",
        )

        # Query 2
        ax.plot(
            s2,
            p50_2,
            marker="s",
            linestyle="-",
            label=f"{query2_name} v{query2_version} P50",
        )
        ax.plot(
            s2,
            p95_2,
            marker="s",
            linestyle="--",
            label=f"{query2_name} v{query2_version} P95",
        )

        ax.set_xlabel("Dataset size (rows)")
        ax.set_ylabel("Elapsed time (s)")

        mode = "latest launch" if latest_only else "all launches"
        ax.set_title(
            f"{query1_name} v{query1_version} (runs: {n1}) vs "
            f"{query2_name} v{query2_version} (runs: {n2})\n{mode}"
        )

        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

        fig.savefig(
            f"{AppConfig.graphs}/{query1_name}-v{query1_version}__vs__"
            f"{query2_name}-v{query2_version}.png",
            dpi=144,
            bbox_inches="tight",
        )

        return fig, ax
    finally:
        con.close()


def plot_query_percentiles_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query_name", help="Name of the query")
    parser.add_argument("query_version", help="Version of the query")
    parser.add_argument(
        "latest_only",
        action="store_false",
        help="Use all data instead of only the latest",
    )

    args = parser.parse_args()

    fig = None
    if args.latest_only:
        print("Plotting all launches...")
        fig, ax = plot_query_percentiles(
            query_name=args.query_name,
            query_version=args.query_version,
            latest_only=False,
        )
    else:
        print("Plotting latest launch only...")
        fig, ax = plot_query_percentiles(
            query_name=args.query_name,
            query_version=args.query_version,
            latest_only=True,
        )

    fig.show()

def plot_two_query_percentiles_cli() -> None:
    parser = argparse.ArgumentParser(
        description="Compare percentile plots for two queries on the same figure."
    )
    parser.add_argument("query1_name", help="Name of the first query")
    parser.add_argument("query1_version", help="Version of the first query")
    parser.add_argument("query2_name", help="Name of the second query")
    parser.add_argument("query2_version", help="Version of the second query")
    parser.add_argument(
        "--all-launches",
        action="store_true",
        help="Use all launches instead of only the latest for each query",
    )

    args = parser.parse_args()

    latest_only = not args.all_launches
    mode = "latest launch only" if latest_only else "all launches"
    print(f"Plotting two queries using {mode}...")

    fig, ax = plot_two_query_percentiles(
        query1_name=args.query1_name,
        query1_version=args.query1_version,
        query2_name=args.query2_name,
        query2_version=args.query2_version,
        latest_only=latest_only,
    )

    fig.show()


if __name__ == "__main__":
    # Example usage
    fig, ax = plot_query_percentiles("baseline_query1", "1.0", latest_only=False)
    plt.show()
    # Example for comparing two queries:
    # fig, ax = plot_two_query_percentiles("baseline_query1", "1.0", "optimized_query1", "1.0", latest_only=True)
    # plt.show()
