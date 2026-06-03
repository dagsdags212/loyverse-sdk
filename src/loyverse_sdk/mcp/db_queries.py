"""Local DuckDB query path for MCP CRUD tools.

Provides a read-through cache: when a local DuckDB database is available and
fresh (receipt records exist within the last 2 days), CRUD tools query it
directly instead of hitting the Loyverse API.
"""

import json
from datetime import timedelta
from pathlib import Path

import duckdb


def _serialize_row(row: tuple, columns: list[str]) -> dict:
    result: dict = {}
    for i, col in enumerate(columns):
        val = row[i]
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        elif isinstance(val, int) and len(str(val)) > 10:
            val = str(val)
        result[col] = val
    return result


def is_db_fresh(db_path: str) -> bool:
    """Return True if a receipt was created within the last 2 days."""
    if not Path(db_path).exists():
        return False
    try:
        conn = duckdb.connect(db_path, read_only=True)
        count = conn.execute(
            "SELECT COUNT(*) FROM receipts "
            "WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '2 days'"
        ).fetchone()
        conn.close()
        return count is not None and count[0] > 0
    except Exception:
        return False


def list_from_db(
    db_path: str,
    table: str,
    limit: int = 50,
    created_at_min: str | None = None,
    created_at_max: str | None = None,
    updated_at_min: str | None = None,
    updated_at_max: str | None = None,
) -> str | None:
    """Query a table from DuckDB and return JSON matching the API envelope.

    Returns None if the database doesn't exist or the query fails.
    Filters on created_at/updated_at date ranges; excludes soft-deleted rows.
    """
    if not Path(db_path).exists():
        return None
    try:
        conn = duckdb.connect(db_path, read_only=True)
        conditions: list[str] = []
        params: list = []

        if created_at_min:
            conditions.append("created_at >= ?")
            params.append(created_at_min)
        if created_at_max:
            conditions.append("created_at <= ?")
            params.append(created_at_max)
        if updated_at_min:
            conditions.append("updated_at >= ?")
            params.append(updated_at_min)
        if updated_at_max:
            conditions.append("updated_at <= ?")
            params.append(updated_at_max)
        conditions.append("deleted_at IS NULL")

        where = " AND ".join(conditions)
        sql = f'SELECT * FROM "{table}" WHERE {where} ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        result = conn.execute(sql, params)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()

        items = [_serialize_row(row, columns) for row in rows]
        conn.close()

        return json.dumps({"items": items, "count": len(items), "next_cursor": None}, default=str)
    except Exception:
        return None


def get_from_db(
    db_path: str,
    table: str,
    resource_id: str,
) -> str | None:
    """Retrieve a single row by ID from DuckDB.

    Returns None if not found or DB unavailable.
    """
    if not Path(db_path).exists():
        return None
    try:
        conn = duckdb.connect(db_path, read_only=True)
        sql = f'SELECT * FROM "{table}" WHERE id = ? AND deleted_at IS NULL'
        result = conn.execute(sql, [resource_id])
        columns = [desc[0] for desc in result.description]
        row = result.fetchone()
        conn.close()

        if row is None:
            return None

        item = _serialize_row(row, columns)
        return json.dumps(item, default=str)
    except Exception:
        return None
