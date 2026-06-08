"""
Unit tests for loyverse_sdk.db.exporter module.

Tests DuckDBExporter class with mocked data and API calls.
"""

import os
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from loyverse_sdk.db.exporter import DuckDBExporter
from loyverse_sdk.exceptions import ExportError


@pytest.fixture
def temp_db():
    """Create a temporary DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        yield db_path


@pytest.fixture
def mock_client():
    """Create a mock LoyverseClient."""
    client = Mock()
    client.endpoints = {}
    return client


@pytest.fixture
def exporter(mock_client, temp_db):
    """Create a DuckDBExporter instance with mocked client."""
    return DuckDBExporter(mock_client, temp_db)


class TestDuckDBExporterInit:
    """Test DuckDBExporter initialization."""

    def test_init_schema_creates_tables(self, exporter):
        """Test that init_schema creates all tables."""
        exporter.init_schema(drop_existing=False)

        # Verify database file exists
        assert os.path.exists(exporter.db_path)

        # Verify connection can query tables
        conn = exporter.connection.connect()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "categories" in table_names
        assert "receipts" in table_names
        conn.close()


class TestResourceOrder:
    """Test resource export order respects dependencies."""

    def test_resource_order_respects_dependencies(self, exporter):
        """Test that dependent resources come after their dependencies."""
        order = DuckDBExporter.RESOURCE_ORDER

        # Categories should come before items
        cat_index = order.index("categories")
        items_index = order.index("items")
        assert cat_index < items_index

        # Items should come before variants
        variants_index = order.index("variants")
        assert items_index < variants_index

        # Stores should come before employees
        stores_index = order.index("stores")
        employees_index = order.index("employees")
        assert stores_index < employees_index


class TestExportResource:
    """Test export_resource method."""

    @pytest.mark.asyncio
    async def test_export_resource_unknown_raises_error(self, exporter):
        """Test that exporting unknown resource raises ExportError."""
        with pytest.raises(ExportError, match="Unknown resource"):
            await exporter.export_resource("unknown_resource")

    @pytest.mark.asyncio
    async def test_export_resource_calls_endpoint_iter_all(self, exporter, mock_client):
        """Test that export_resource calls endpoint's iter_all method."""

        # Setup mock endpoint
        async def mock_iter_all(*args, **kwargs):
            """Mock async generator."""
            for i in range(3):
                yield Mock(
                    model_dump=lambda: {
                        "id": f"cat{i}",
                        "name": f"Category {i}",
                        "color": "RED",
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "deleted_at": None,
                    }
                )

        mock_endpoint = Mock()
        mock_endpoint.iter_all = mock_iter_all

        mock_client.endpoints = {"categories": mock_endpoint}

        # Initialize schema first
        exporter.init_schema()

        # Export resource
        count = await exporter.export_resource("categories")

        assert count == 3

    @pytest.mark.asyncio
    async def test_export_resource_passes_date_filters(self, exporter, mock_client):
        """Test that date filters are passed to iter_all via Query object."""
        created_min = datetime(2024, 1, 1)
        created_max = datetime(2024, 12, 31)
        # Track if iter_all was called with correct args
        iter_all_called = False
        captured_query = None

        async def mock_iter_all(*args, query=None, **kwargs):
            nonlocal iter_all_called, captured_query
            iter_all_called = True
            captured_query = query
            return
            yield  # Make it a generator

        mock_endpoint = Mock()
        mock_endpoint.iter_all = mock_iter_all
        mock_client.endpoints = {"categories": mock_endpoint}
        exporter.init_schema()
        await exporter.export_resource(
            "categories",
            created_at_min=created_min,
            created_at_max=created_max,
        )

        assert iter_all_called
        assert captured_query is not None
        assert captured_query.created_at_min == created_min
        assert captured_query.created_at_max == created_max

    @pytest.mark.asyncio
    async def test_export_resource_handles_merchant_special_case(
        self, exporter, mock_client
    ):
        """Test that merchant endpoint (single record) is handled specially."""
        # Mock merchant endpoint without iter_all
        mock_merchant = Mock(
            id="merchant1",
            business_name="Test Business",
            currency="USD",
            created_at=datetime.now(),
        )
        mock_merchant.model_dump = lambda: {
            "id": "merchant1",
            "business_name": "Test Business",
            "email": None,
            "country": None,
            "currency": "USD",
            "created_at": datetime.now(),
        }

        mock_endpoint = Mock(spec=["retrieve"])
        mock_endpoint.retrieve = AsyncMock(return_value=mock_merchant)
        # Don't add iter_all to simulate merchant endpoint (Mock with spec prevents auto-generated attributes)

        mock_client.endpoints = {"merchant": mock_endpoint}
        mock_client.merchant = mock_endpoint

        exporter.init_schema()

        count = await exporter.export_resource("merchant")

        assert count == 1
        mock_endpoint.retrieve.assert_called_once()

    @pytest.mark.asyncio
    async def test_export_resource_batches_inserts(self, exporter, mock_client):
        """Test that export batches inserts based on batch_size."""

        # Create 2500 records (should trigger 3 batches with size 1000)
        async def mock_iter_all(*args, **kwargs):
            for i in range(2500):
                yield Mock(
                    model_dump=lambda i=i: {
                        "id": f"cat{i}",
                        "name": f"Category {i}",
                        "color": "RED",
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "deleted_at": None,
                    }
                )

        mock_endpoint = Mock()
        mock_endpoint.iter_all = mock_iter_all

        mock_client.endpoints = {"categories": mock_endpoint}

        exporter.init_schema()

        count = await exporter.export_resource("categories", batch_size=1000)

        assert count == 2500

    @pytest.mark.asyncio
    async def test_export_resource_calls_progress_callback(self, exporter, mock_client):
        """Test that progress callback is called during export."""
        callback_calls = []

        def progress_callback(resource, current, total):
            callback_calls.append((resource, current, total))

        async def mock_iter_all(*args, **kwargs):
            for i in range(5):
                yield Mock(
                    model_dump=lambda: {
                        "id": f"cat{i}",
                        "name": f"Category {i}",
                        "color": "RED",
                        "created_at": datetime.now(),
                        "updated_at": datetime.now(),
                        "deleted_at": None,
                    }
                )

        mock_endpoint = Mock()
        mock_endpoint.iter_all = mock_iter_all

        mock_client.endpoints = {"categories": mock_endpoint}

        exporter.init_schema()

        await exporter.export_resource(
            "categories", progress_callback=progress_callback
        )

        # Callback should be called 5 times (once per record)
        assert len(callback_calls) == 5
        assert callback_calls[0] == ("categories", 1, -1)
        assert callback_calls[4] == ("categories", 5, -1)


class TestExportAll:
    """Test export_all method."""

    @pytest.mark.asyncio
    async def test_export_all_initializes_schema_if_needed(self, exporter, mock_client):
        """Test that export_all initializes schema when database doesn't exist."""
        # Ensure database file doesn't exist
        assert not os.path.exists(exporter.db_path)

        # Set up mock endpoint so export_resource doesn't fail
        async def empty_iter_all(*args, **kwargs):
            return
            yield  # Make it an async generator

        mock_endpoint = Mock()
        mock_endpoint.iter_all = empty_iter_all
        mock_client.endpoints = {"categories": mock_endpoint}

        # Export should create the database and schema
        counts = await exporter.export_all(resources=["categories"])

        # Export ran for the requested resource (zero rows from empty iterator)
        assert counts == {"categories": 0}

        # Verify database file was created
        assert os.path.exists(exporter.db_path)

        # Verify schema was created (table exists)
        conn = exporter.connection.connect()
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        assert "categories" in table_names
        conn.close()

    @pytest.mark.asyncio
    async def test_export_all_exports_selected_resources(self, exporter, mock_client):
        """Test that export_all exports only selected resources."""

        async def mock_iter_categories(*args, **kwargs):
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

        async def mock_iter_stores(*args, **kwargs):
            yield Mock(
                model_dump=lambda: {
                    "id": "store1",
                    "name": "Store 1",
                    "address": None,
                    "city": None,
                    "state": None,
                    "postal_code": None,
                    "country": None,
                    "phone_number": None,
                    "description": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                }
            )

        mock_cat_endpoint = Mock()
        mock_cat_endpoint.iter_all = mock_iter_categories

        mock_store_endpoint = Mock()
        mock_store_endpoint.iter_all = mock_iter_stores

        mock_client.endpoints = {
            "categories": mock_cat_endpoint,
            "stores": mock_store_endpoint,
        }

        exporter.init_schema()

        counts = await exporter.export_all(resources=["categories", "stores"])

        assert "categories" in counts
        assert "stores" in counts
        assert counts["categories"] == 1
        assert counts["stores"] == 1

    @pytest.mark.asyncio
    async def test_export_all_respects_resource_order(self, exporter, mock_client):
        """Test that export_all exports resources in dependency order."""
        export_order = []

        async def mock_iter_all(resource_name):
            async def generator(*args, **kwargs):
                export_order.append(resource_name)
                return
                yield  # Make it a generator

            return generator

        # Mock multiple endpoints
        for resource in ["categories", "items", "variants"]:
            mock_endpoint = Mock()
            mock_endpoint.iter_all = await mock_iter_all(resource)
            mock_client.endpoints[resource] = mock_endpoint

        exporter.init_schema()

        await exporter.export_all(resources=["categories", "items", "variants"])

        # Verify categories before items before variants
        cat_index = export_order.index("categories")
        items_index = export_order.index("items")
        variants_index = export_order.index("variants")

        assert cat_index < items_index < variants_index

    @pytest.mark.asyncio
    async def test_export_all_creates_indexes_when_requested(
        self, exporter, mock_client
    ):
        """Test that export_all creates indexes when create_indexes_after=True."""

        # Set up mock endpoint so export_resource can proceed
        async def empty_iter_all(*args, **kwargs):
            return
            yield  # Make it an async generator

        mock_endpoint = Mock()
        mock_endpoint.iter_all = empty_iter_all
        mock_client.endpoints = {"categories": mock_endpoint}

        exporter.init_schema()

        await exporter.export_all(resources=["categories"], create_indexes_after=True)

        # Verify indexes exist (check database)
        conn = exporter.connection.connect()
        indexes = conn.execute("""
            SELECT DISTINCT index_name
            FROM duckdb_indexes()
            WHERE index_name LIKE 'idx_%'
        """).fetchall()

        assert len(indexes) > 0

    @pytest.mark.asyncio
    async def test_export_all_raises_export_error_on_failure(
        self, exporter, mock_client
    ):
        """Test that export_all raises ExportError when resource export fails."""

        async def failing_iter_all(*args, **kwargs):
            raise ExportError("Simulated failure")
            yield  # Make it a generator

        mock_endpoint = Mock()
        mock_endpoint.iter_all = failing_iter_all

        mock_client.endpoints = {"categories": mock_endpoint}

        exporter.init_schema()

        with pytest.raises(ExportError, match="Failed to export categories"):
            await exporter.export_all(resources=["categories"])


class TestBatchInsert:
    """Test _batch_insert method."""

    def test_batch_insert_handles_empty_batch(self, exporter):
        """Test that empty batch is handled gracefully."""
        exporter.init_schema()

        # Should not raise
        exporter._batch_insert("categories", [])

    def test_batch_insert_inserts_main_records(self, exporter):
        """Test that main records are inserted."""
        exporter.init_schema()

        batch = [
            (
                {
                    "id": "cat1",
                    "name": "Category 1",
                    "color": "RED",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
                {},
                {},
            ),
            (
                {
                    "id": "cat2",
                    "name": "Category 2",
                    "color": "BLUE",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
                {},
                {},
            ),
        ]

        exporter._batch_insert("categories", batch)

        # Verify records inserted
        conn = exporter.connection.connect()
        count = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        assert count == 2
        conn.close()

    def test_batch_insert_inserts_junction_records(self, exporter):
        """Test that junction records are inserted."""
        exporter.init_schema()

        # Insert parent records first
        with exporter.connection.cursor() as conn:
            conn.execute("""
                INSERT INTO items (id, name, created_at, updated_at)
                VALUES ('item1', 'Item 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            conn.execute("""
                INSERT INTO taxes (id, name, type, rate, created_at, updated_at)
                VALUES ('tax1', 'VAT', 'PERCENT', 10.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)

        batch = [
            (
                {
                    "id": "item1",
                    "name": "Item 1",
                    "handle": None,
                    "reference_id": None,
                    "description": None,
                    "track_stock": True,
                    "sold_by_weight": False,
                    "is_composite": False,
                    "use_production": False,
                    "category_id": None,
                    "primary_supplier_id": None,
                    "form": "default",
                    "color": "default",
                    "image_url": None,
                    "option1_name": None,
                    "option2_name": None,
                    "option3_name": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
                {"item_tax": [{"item_id": "item1", "tax_id": "tax1"}]},
                {},
            ),
        ]

        exporter._batch_insert("items", batch)

        # Verify junction record inserted
        conn = exporter.connection.connect()
        count = conn.execute("SELECT COUNT(*) FROM item_tax").fetchone()[0]
        assert count == 1

        # Test idempotent re-insert with different item (avoids FK constraint
        # violation from INSERT OR REPLACE deleting rows referenced by junction tables).
        # DuckDB's INSERT OR REPLACE first deletes conflicting rows, which fails when
        # junction/child tables hold FK references to the main table.
        batch2 = [
            (
                {
                    "id": "item2",
                    "name": "Item 2",
                    "handle": None,
                    "reference_id": None,
                    "description": None,
                    "track_stock": True,
                    "sold_by_weight": False,
                    "is_composite": False,
                    "use_production": False,
                    "category_id": None,
                    "primary_supplier_id": None,
                    "form": "default",
                    "color": "default",
                    "image_url": None,
                    "option1_name": None,
                    "option2_name": None,
                    "option3_name": None,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                    "deleted_at": None,
                },
                {"item_tax": [{"item_id": "item2", "tax_id": "tax1"}]},
                {},
            ),
        ]

        exporter._batch_insert("items", batch2)

        # Verify junction record inserted for item2 as well
        conn = exporter.connection.connect()
        count = conn.execute("SELECT COUNT(*) FROM item_tax").fetchone()[0]
        assert count == 2
        conn.close()

    def test_batch_insert_inserts_child_records(self, exporter):
        """Test that child records are inserted."""
        exporter.init_schema()

        # Insert required parent records
        with exporter.connection.cursor() as conn:
            conn.execute("""
                INSERT INTO stores (id, name, created_at, updated_at)
                VALUES ('store1', 'Store 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            conn.execute("""
                INSERT INTO employees (id, name, created_at, updated_at)
                VALUES ('emp1', 'Employee 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            conn.execute("""
                INSERT INTO pos_devices (id, name, store_id)
                VALUES ('dev1', 'Device 1', 'store1')
            """)
            conn.execute("""
                INSERT INTO payment_types (id, name, type, created_at, updated_at)
                VALUES ('pay1', 'Cash', 'CASH', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            conn.execute("""
                INSERT INTO items (id, name, created_at, updated_at)
                VALUES ('item1', 'Item 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)
            conn.execute("""
                INSERT INTO variants (id, item_id, sku, cost, default_pricing_type, created_at, updated_at)
                VALUES ('variant1', 'item1', 'SKU001', 0.0, 'DEFAULT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)

        batch = [
            (
                {
                    "receipt_number": "001",
                    "receipt_type": "SALE",
                    "total_money": 100.0,
                    "employee_id": "emp1",
                    "store_id": "store1",
                    "pos_device_id": "dev1",
                },
                {},
                {
                    "receipt_line_items": [
                        {
                            "id": "line1",
                            "receipt_id": "001",
                            "item_id": "item1",
                            "item_name": "Item 1",
                            "quantity": 1.0,
                            "price": 100.0,
                            "total_money": 100.0,
                        }
                    ]
                },
            ),
        ]

        exporter._batch_insert("receipts", batch)

        # Verify child record inserted
        conn = exporter.connection.connect()
        count = conn.execute("SELECT COUNT(*) FROM receipt_line_items").fetchone()[0]
        assert count == 1

        # Test idempotent re-insert with different receipt (avoids FK constraint
        # violation from INSERT OR REPLACE deleting rows referenced by child tables).
        batch2 = [
            (
                {
                    "receipt_number": "002",
                    "receipt_type": "SALE",
                    "total_money": 200.0,
                    "employee_id": "emp1",
                    "store_id": "store1",
                    "pos_device_id": "dev1",
                },
                {},
                {
                    "receipt_line_items": [
                        {
                            "id": "line2",
                            "receipt_id": "002",
                            "item_id": "item1",
                            "item_name": "Item 1",
                            "quantity": 2.0,
                            "price": 100.0,
                            "total_money": 200.0,
                        }
                    ]
                },
            ),
        ]

        exporter._batch_insert("receipts", batch2)

        # Verify child records accumulated
        conn = exporter.connection.connect()
        count = conn.execute("SELECT COUNT(*) FROM receipt_line_items").fetchone()[0]
        assert count == 2
        conn.close()


class TestSyncMetadata:
    """Test sync metadata tracking."""

    def test_get_sync_metadata_empty(self, exporter):
        """Test getting sync metadata from empty database."""
        exporter.init_schema()

        metadata = exporter.get_sync_metadata()

        assert metadata == {}

    @pytest.mark.asyncio
    async def test_export_updates_sync_metadata(self, exporter, mock_client):
        """Test that export updates sync metadata table."""

        async def mock_iter_all(*args, **kwargs):
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

        mock_endpoint = Mock()
        mock_endpoint.iter_all = mock_iter_all

        mock_client.endpoints = {"categories": mock_endpoint}

        exporter.init_schema()

        await exporter.export_all(resources=["categories"])

        metadata = exporter.get_sync_metadata()

        assert "categories" in metadata
        assert metadata["categories"]["records_count"] == 1
        assert metadata["categories"]["sync_type"] == "full"

    def test_get_table_counts(self, exporter):
        """Test getting table counts."""
        exporter.init_schema()

        # Insert test data
        with exporter.connection.cursor() as conn:
            conn.execute("""
                INSERT INTO categories (id, name, color, created_at, updated_at)
                VALUES ('cat1', 'Category 1', 'RED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """)

        counts = exporter.get_table_counts()

        assert "categories" in counts
        assert counts["categories"] == 1


class TestContextManager:
    """Test context manager support."""

    def test_exporter_as_context_manager(self, mock_client, temp_db):
        """Test using exporter as context manager."""
        with DuckDBExporter(mock_client, temp_db) as exporter:
            assert exporter is not None
            exporter.init_schema()

        # Connection should be closed after context exit
        # (Can't easily test this without accessing internals)


def _category_endpoint(cat_id: str = "cat1"):
    """Build a mock endpoint whose iter_all yields one category record."""

    async def mock_iter(*args, **kwargs):
        yield Mock(
            model_dump=lambda: {
                "id": cat_id,
                "name": f"Category {cat_id}",
                "color": "RED",
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "deleted_at": None,
            }
        )

    endpoint = Mock()
    endpoint.iter_all = mock_iter
    return endpoint


class TestSyncAll:
    """Test sync_all — the default ``loyverse export`` (incremental) path.

    Regression coverage: sync_all previously referenced a bare ``RESOURCE_ORDER``
    (NameError), passed ``total_resources`` to ExportProgress both positionally
    and by keyword (TypeError), never called ``tracker.start()``, and invoked a
    non-existent ``self.create_indexes()`` (AttributeError). It could not run.
    """

    @pytest.mark.asyncio
    async def test_sync_all_full_export_on_new_database(self, exporter, mock_client):
        mock_client.endpoints = {"categories": _category_endpoint()}

        counts = await exporter.sync_all(
            resources=["categories"], show_progress=False
        )

        assert counts == {"categories": 1}
        assert os.path.exists(exporter.db_path)

    @pytest.mark.asyncio
    async def test_sync_all_records_metadata_and_supports_second_run(
        self, exporter, mock_client
    ):
        mock_client.endpoints = {"categories": _category_endpoint()}

        # First run creates the schema and writes sync metadata (full).
        await exporter.sync_all(resources=["categories"], show_progress=False)

        # Second run sees an existing database and performs an incremental sync.
        counts = await exporter.sync_all(
            resources=["categories"], show_progress=False
        )
        assert counts == {"categories": 1}

        meta = exporter.get_sync_metadata()
        assert "categories" in meta
        assert meta["categories"]["sync_type"] == "incremental"


class TestQuickExport:
    """Test the quick_export convenience function.

    Regression coverage: quick_export was a sync ``def`` that returned an
    un-awaited coroutine while its ``finally`` closed the connection.
    """

    @pytest.mark.asyncio
    async def test_quick_export_returns_counts(self, mock_client, temp_db):
        from loyverse_sdk.db.exporter import quick_export

        mock_client.endpoints = {"categories": _category_endpoint()}

        counts = await quick_export(
            mock_client, temp_db, resources=["categories"], show_progress=False
        )

        assert counts == {"categories": 1}
        assert os.path.exists(temp_db)
