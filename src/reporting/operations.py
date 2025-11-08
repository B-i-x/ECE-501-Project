
# ---------- QueryLaunch CRUD ----------
from typing import Optional
import sqlite3

from reporting.models import QueryLaunch, ResultRecord

def create_query_launch(conn: sqlite3.Connection, launch: QueryLaunch) -> QueryLaunch:
    """
    Insert a QueryLaunch. If launch_ID is falsy, it will be auto-assigned.
    Returns the inserted object with launch_ID populated if auto-assigned.
    """
    params = [launch.timestamp, launch.query_name, launch.query_version]

    if launch.launch_ID:  # caller provided an explicit ID
        sql = "INSERT INTO QueryLaunch (launch_ID, timestamp, query_name, query_version) VALUES (?, ?, ?, ?)"
        conn.execute(sql, [launch.launch_ID] + params)
    else:
        sql = "INSERT INTO QueryLaunch (timestamp, query_name, query_version) VALUES (?, ?, ?)"
        cur = conn.execute(sql, params)
        launch.launch_ID = str(cur.lastrowid)

    conn.commit()
    return launch


def read_query_launch(conn: sqlite3.Connection, launch_ID: str) -> Optional[QueryLaunch]:
    """Fetch a QueryLaunch by primary key, or None if not found."""
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT launch_ID, timestamp, query_name, query_version "
        "FROM QueryLaunch WHERE launch_ID = ?", (launch_ID,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return QueryLaunch(
        launch_ID=str(row["launch_ID"]),
        timestamp=row["timestamp"],
        query_name=row["query_name"],
        query_version=row["query_version"],
    )


def update_query_launch(conn: sqlite3.Connection, launch: QueryLaunch) -> int:
    """
    Update a QueryLaunch by primary key.
    Returns number of rows affected.
    """
    if not launch.launch_ID:
        raise ValueError("launch_ID is required for update")
    cur = conn.execute(
        "UPDATE QueryLaunch SET timestamp = ?, query_name = ?, query_version = ? "
        "WHERE launch_ID = ?",
        (launch.timestamp, launch.query_name, launch.query_version, launch.launch_ID),
    )
    conn.commit()
    return cur.rowcount


def delete_query_launch(conn: sqlite3.Connection, launch_ID: str) -> int:
    """Delete a QueryLaunch by primary key. Returns number of rows affected."""
    cur = conn.execute("DELETE FROM QueryLaunch WHERE launch_ID = ?", (launch_ID,))
    conn.commit()
    return cur.rowcount


# ---------- ResultRecord CRUD ----------

def insert_new_result_record(conn: sqlite3.Connection, rec: ResultRecord) -> ResultRecord:
    """
    Insert a ResultRecord. If result_ID is falsy, it will be auto-assigned.
    Returns the inserted object with result_ID populated if auto-assigned.
    """
    cols = ["launch_ID", "dataset_size", "run_index", "elapsed_seconds"]
    params = [rec.launch_ID, rec.dataset_size, rec.run_index, rec.elapsed_seconds]

    if rec.result_ID:  # explicit result id provided
        sql = "INSERT INTO QueryResult (result_ID, launch_ID, dataset_size, run_index, elapsed_seconds) VALUES (?, ?, ?, ?, ?)"
        conn.execute(sql, [rec.result_ID] + params)
    else:
        sql = "INSERT INTO QueryResult (launch_ID, dataset_size, run_index, elapsed_seconds) VALUES (?, ?, ?, ?)"
        cur = conn.execute(sql, params)
        rec.result_ID = str(cur.lastrowid)

    conn.commit()
    return rec


def read_result_record(conn: sqlite3.Connection, result_ID: str) -> Optional[ResultRecord]:
    """Fetch a ResultRecord by primary key, or None if not found."""
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT result_ID, launch_ID, dataset_size, run_index, elapsed_seconds "
        "FROM QueryResult WHERE result_ID = ?", (result_ID,)
    )
    row = cur.fetchone()
    if not row:
        return None
    return ResultRecord(
        result_ID=str(row["result_ID"]),
        launch_ID=str(row["launch_ID"]),
        dataset_size=int(row["dataset_size"]),
        run_index=int(row["run_index"]),
        elapsed_seconds=float(row["elapsed_seconds"]),
    )


def update_result_record(conn: sqlite3.Connection, rec: ResultRecord) -> int:
    """
    Update a ResultRecord by primary key.
    Returns number of rows affected.
    """
    if not rec.result_ID:
        raise ValueError("result_ID is required for update")
    cur = conn.execute(
        "UPDATE QueryResult SET launch_ID = ?, dataset_size = ?, run_index = ?, elapsed_seconds = ? "
        "WHERE result_ID = ?",
        (rec.launch_ID, rec.dataset_size, rec.run_index, rec.elapsed_seconds, rec.result_ID),
    )
    conn.commit()
    return cur.rowcount


def delete_result_record(conn: sqlite3.Connection, result_ID: str) -> int:
    """Delete a ResultRecord by primary key. Returns number of rows affected."""
    cur = conn.execute("DELETE FROM QueryResult WHERE result_ID = ?", (result_ID,))
    conn.commit()
    return cur.rowcount