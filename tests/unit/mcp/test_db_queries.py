"""Unit tests for the MCP local DuckDB read-through cache (``db_queries``).

A temporary DuckDB file is populated with a minimal schema mirroring the
columns these functions rely on (``id``, ``created_at``, ``updated_at``,
``deleted_at``), then each query helper is exercised against it.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta

import duckdb
import pytest

from loyverse_sdk.mcp import db_queries


@pytest.fixture
def db_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "cache.duckdb")


def _build_db(path: str, *, fresh: bool = True) -> None:
    """Create a minimal schema with a ``receipts`` and ``categories`` table."""
    conn = duckdb.connect(path)
    conn.execute(
        """
        CREATE TABLE receipts (
            id VARCHAR,
            receipt_number VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE categories (
            id VARCHAR,
            name VARCHAR,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            deleted_at TIMESTAMP
        )
        """
    )

    now = datetime.now()
    recent = now if fresh else now - timedelta(days=10)
    conn.execute(
        "INSERT INTO receipts VALUES (?, ?, ?, ?, ?)",
        ["r-1", "R-1", recent, recent, None],
    )
    # A soft-deleted receipt that must be excluded from list/get results.
    conn.execute(
        "INSERT INTO receipts VALUES (?, ?, ?, ?, ?)",
        ["r-deleted", "R-DEL", recent, recent, now],
    )
    conn.execute(
        "INSERT INTO categories VALUES (?, ?, ?, ?, ?)",
        ["c-1", "Drinks", now - timedelta(days=1), now - timedelta(days=1), None],
    )
    conn.execute(
        "INSERT INTO categories VALUES (?, ?, ?, ?, ?)",
        ["c-2", "Food", now - timedelta(days=5), now - timedelta(days=5), None],
    )
    conn.close()


class TestIsDbFresh:
    def test_missing_file_returns_false(self, db_path):
        assert db_queries.is_db_fresh(db_path) is False

    def test_fresh_db_returns_true(self, db_path):
        _build_db(db_path, fresh=True)
        assert db_queries.is_db_fresh(db_path) is True

    def test_stale_db_returns_false(self, db_path):
        _build_db(db_path, fresh=False)
        assert db_queries.is_db_fresh(db_path) is False

    def test_db_without_receipts_table_returns_false(self, db_path):
        conn = duckdb.connect(db_path)
        conn.execute("CREATE TABLE other (id VARCHAR)")
        conn.close()
        assert db_queries.is_db_fresh(db_path) is False


class TestListFromDb:
    def test_missing_file_returns_none(self, db_path):
        assert db_queries.list_from_db(db_path, "categories") is None

    def test_returns_api_envelope(self, db_path):
        _build_db(db_path)
        result = db_queries.list_from_db(db_path, "categories")
        assert result is not None
        payload = json.loads(result)
        assert set(payload) == {"items", "count", "next_cursor"}
        assert payload["next_cursor"] is None
        assert payload["count"] == 2
        names = {row["name"] for row in payload["items"]}
        assert names == {"Drinks", "Food"}

    def test_excludes_soft_deleted_rows(self, db_path):
        _build_db(db_path)
        payload = json.loads(db_queries.list_from_db(db_path, "receipts"))
        ids = {row["id"] for row in payload["items"]}
        assert ids == {"r-1"}

    def test_respects_limit(self, db_path):
        _build_db(db_path)
        payload = json.loads(db_queries.list_from_db(db_path, "categories", limit=1))
        assert payload["count"] == 1

    def test_orders_by_created_at_desc(self, db_path):
        _build_db(db_path)
        payload = json.loads(db_queries.list_from_db(db_path, "categories"))
        # Drinks is more recent than Food, so it should appear first.
        assert payload["items"][0]["name"] == "Drinks"

    def test_created_at_date_filters(self, db_path):
        _build_db(db_path)
        # Only the older "Food" category falls before this cutoff.
        cutoff = (datetime.now() - timedelta(days=3)).isoformat()
        payload = json.loads(
            db_queries.list_from_db(db_path, "categories", created_at_max=cutoff)
        )
        names = {row["name"] for row in payload["items"]}
        assert names == {"Food"}

    def test_updated_at_date_filters(self, db_path):
        _build_db(db_path)
        cutoff = (datetime.now() - timedelta(days=3)).isoformat()
        payload = json.loads(
            db_queries.list_from_db(db_path, "categories", updated_at_min=cutoff)
        )
        names = {row["name"] for row in payload["items"]}
        assert names == {"Drinks"}

    def test_serialized_timestamps_are_iso_strings(self, db_path):
        _build_db(db_path)
        payload = json.loads(db_queries.list_from_db(db_path, "categories"))
        created = payload["items"][0]["created_at"]
        # isoformat output is parseable back into a datetime.
        assert datetime.fromisoformat(created)

    def test_unknown_table_returns_none(self, db_path):
        _build_db(db_path)
        assert db_queries.list_from_db(db_path, "nonexistent") is None


class TestGetFromDb:
    def test_missing_file_returns_none(self, db_path):
        assert db_queries.get_from_db(db_path, "categories", "c-1") is None

    def test_returns_single_row(self, db_path):
        _build_db(db_path)
        result = db_queries.get_from_db(db_path, "categories", "c-1")
        assert result is not None
        item = json.loads(result)
        assert item["id"] == "c-1"
        assert item["name"] == "Drinks"

    def test_missing_id_returns_none(self, db_path):
        _build_db(db_path)
        assert db_queries.get_from_db(db_path, "categories", "does-not-exist") is None

    def test_soft_deleted_returns_none(self, db_path):
        _build_db(db_path)
        assert db_queries.get_from_db(db_path, "receipts", "r-deleted") is None

    def test_unknown_table_returns_none(self, db_path):
        _build_db(db_path)
        assert db_queries.get_from_db(db_path, "nonexistent", "c-1") is None


class TestSerializeRow:
    def test_serializes_datetime_via_isoformat(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        row = db_queries._serialize_row((dt, "x"), ["created_at", "name"])
        assert row["created_at"] == dt.isoformat()
        assert row["name"] == "x"

    def test_large_int_stringified(self):
        big = 12345678901234  # > 10 digits
        row = db_queries._serialize_row((big,), ["epoch"])
        assert row["epoch"] == str(big)

    def test_small_int_left_as_int(self):
        row = db_queries._serialize_row((42,), ["count"])
        assert row["count"] == 42
