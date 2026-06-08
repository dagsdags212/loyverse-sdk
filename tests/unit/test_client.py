"""Unit tests for LoyverseClient DuckDB export routing methods.

These drive the client's export convenience methods end-to-end against a temp
DuckDB file with mocked endpoints (no network, no real API). They pin down a
regression where ``export_resource_to_duckdb`` referenced a ``show_progress``
name that was never a parameter (NameError on call).
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import Mock

import pytest
import pytest_asyncio

from loyverse_sdk import LoyverseClient


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "client.duckdb")


@pytest_asyncio.fixture
async def client():
    c = LoyverseClient(api_token="fake-token-for-testing")
    yield c
    await c.close()


def _category_endpoint():
    async def mock_iter(*args, **kwargs):
        yield Mock(
            model_dump=lambda: {
                "id": "cat1",
                "name": "Category 1",
                "color": "RED",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None,
            }
        )

    endpoint = Mock()
    endpoint.iter_all = mock_iter
    return endpoint


class TestExportRouting:
    @pytest.mark.asyncio
    async def test_export_resource_to_duckdb_returns_count(self, client, temp_db):
        # Regression: this method used `show_progress` without declaring it.
        client.categories = _category_endpoint()
        client.init_duckdb_schema(temp_db)

        count = await client.export_resource_to_duckdb(
            "categories", temp_db, show_progress=False
        )

        assert count == 1
        assert os.path.exists(temp_db)

    @pytest.mark.asyncio
    async def test_export_to_duckdb_returns_counts(self, client, temp_db):
        client.categories = _category_endpoint()

        counts = await client.export_to_duckdb(
            db_path=temp_db, resources=["categories"], show_progress=False
        )

        assert counts == {"categories": 1}

    @pytest.mark.asyncio
    async def test_sync_to_duckdb_returns_counts(self, client, temp_db):
        client.categories = _category_endpoint()

        counts = await client.sync_to_duckdb(
            db_path=temp_db, resources=["categories"], show_progress=False
        )

        assert counts == {"categories": 1}
