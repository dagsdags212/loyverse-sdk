"""
Shared SQL fragments for analytics queries.

Provides reusable parameterized SQL clauses for date-range filtering,
store filtering, and safe query execution against DuckDB.
"""

from datetime import datetime
from typing import Optional

import duckdb
import polars as pl


def date_filter(
    column: str,
    date_start: Optional[datetime | str] = None,
    date_end: Optional[datetime | str] = None,
    days: Optional[int] = None,
) -> tuple[str, list]:
    """Build a parameterized date-range WHERE clause.

    If ``days`` is given, it takes precedence and adds a clause
    using ``CURRENT_DATE - days`` (value is embedded, not parameterised,
    because DuckDB does not support ``?`` inside INTERVAL expressions).

    Returns a tuple of ``(sql_clause, params)`` where ``sql_clause``
    includes the leading ``AND`` when non-empty.
    """
    if days is not None:
        return (f" AND {column} >= CURRENT_DATE - ({days} - 1)", [])

    clauses: list[str] = []
    params: list = []

    if date_start is not None:
        clauses.append(f"{column} >= ?")
        params.append(date_start)
    if date_end is not None:
        clauses.append(f"{column} <= ?")
        params.append(date_end)

    if not clauses:
        return ("", [])

    return (" AND " + " AND ".join(clauses), params)


def store_filter(store_id: Optional[str] = None) -> tuple[str, list]:
    """Build an optional store-id filter clause."""
    if store_id is None:
        return ("", [])
    return (" AND store_id = ?", [store_id])


def _query(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: Optional[list] = None,
) -> pl.DataFrame:
    """Execute a parameterized SQL query and return a Polars DataFrame."""
    result = conn.execute(sql, params or [])
    rows = result.fetchall()
    columns = [desc[0] for desc in result.description]
    return pl.DataFrame(rows, schema=columns, orient="row")


def _scalar(
    conn: duckdb.DuckDBPyConnection, sql: str, params: Optional[list] = None
) -> float | int | None:
    """Execute a SQL query returning a single scalar value."""
    result = conn.execute(sql, params or []).fetchone()
    if result is None:
        return None
    return result[0]
