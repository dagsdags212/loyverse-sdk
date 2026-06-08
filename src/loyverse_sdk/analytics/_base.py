"""
Shared SQL fragments for analytics queries.

Provides reusable parameterized SQL clauses for date-range filtering,
store filtering, and safe query execution against DuckDB.
"""

import json
from datetime import datetime
from io import StringIO
from typing import Literal

import duckdb
import polars as pl

Format = Literal["dataframe", "json", "csv"]


def date_filter(
    column: str,
    date_start: datetime | str | None = None,
    date_end: datetime | str | None = None,
    days: int | None = None,
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


def store_filter(store_id: str | None = None) -> tuple[str, list]:
    """Build an optional store-id filter clause."""
    if store_id is None:
        return ("", [])
    return (" AND store_id = ?", [store_id])


def _serialize(df: pl.DataFrame, fmt: Format) -> pl.DataFrame | str:
    if fmt == "dataframe":
        return df
    if fmt == "json":
        return json.dumps(df.to_dicts(), default=str)
    buf = StringIO()
    df.write_csv(buf)
    return buf.getvalue()


def _scalar_to_output(
    value: float | int | None,
    fmt: Format,
    label: str = "value",
) -> float | int | None | str:
    if fmt == "dataframe":
        return value
    if fmt == "json":
        return json.dumps({label: value})
    return f"{label}\n{value}\n"


def _dict_to_output(
    result: dict,
    fmt: Format,
) -> dict | str:
    if fmt == "dataframe":
        return result
    if fmt == "json":
        return json.dumps(result, default=str)
    flat: dict = {}
    for k, v in result.items():
        if isinstance(v, pl.DataFrame):
            flat[k] = v.to_dicts()
        else:
            flat[k] = v
    return json.dumps(flat, default=str)


def _query(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | None = None,
    fmt: Format = "dataframe",
) -> pl.DataFrame | str:
    """Execute a parameterized SQL query and return a Polars DataFrame."""
    result = conn.execute(sql, params or [])
    rows = result.fetchall()
    columns = [desc[0] for desc in result.description]
    df = pl.DataFrame(rows, schema=columns, orient="row")
    return _serialize(df, fmt)


def _scalar(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list | None = None,
    fmt: Format = "dataframe",
) -> float | int | None | str:
    """Execute a SQL query returning a single scalar value."""
    result = conn.execute(sql, params or []).fetchone()
    if result is None:
        return None if fmt == "dataframe" else _scalar_to_output(None, fmt)
    return result[0] if fmt == "dataframe" else _scalar_to_output(result[0], fmt)
