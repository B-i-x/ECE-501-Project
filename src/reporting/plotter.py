# plots.py
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
            subtitle = "latest launch"
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
            subtitle = f"{len(launch_ids)} launches"

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

        # Runs grouped by dataset_size
        num_runs = len(rows)
        by_size = defaultdict(list)
        for ds, sec in rows:
            by_size[int(ds)].append(float(sec))

        if not by_size:
            raise ValueError("No QueryResult rows with elapsed_seconds found for the selection.")

        sizes = sorted(by_size.keys())
        p50s, p95s = [], []
        for ds in sizes:
            vals = sorted(by_size[ds])
            p50s.append(statistics.median(vals))
            p95s.append(_nearest_rank_percentile(vals, 95))

        # Plot
        fig, ax = plt.subplots()
        ax.plot(sizes, p50s, marker="o", label="P50")
        ax.plot(sizes, p95s, marker="o", label="P95")
        ax.set_xlabel("Dataset size (rows)")
        ax.set_ylabel("Elapsed time (s)")
        ax.set_title(f"{query_name} v{query_version} — Runs:{num_runs}")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend()

        fig.savefig(f"{AppConfig.graphs}/{query_name}-v{query_version}.png", dpi=144, bbox_inches="tight")

        return fig, ax
    finally:
        con.close()

def plot_query_percentiles_cli() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query_name", help="Name of the query")
    parser.add_argument("query_version", help="Version of the query")
    parser.add_argument(
        "latest_only",
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

    # whatever you want to do with the figure
    fig.show()

if __name__ == "__main__":
    # Example usage
    fig, ax = plot_query_percentiles("baseline_query1", "1.0", latest_only=False)
    plt.show()