"""
Integration tests for full DuckDB export.

These tests verify end-to-end export functionality with either real API calls
or comprehensive mocks.
"""

import pytest
import os
import tempfile
import duckdb
from datetime import datetime

from loyverse_sdk import LoyverseClient
from loyverse_sdk.db.exporter import DuckDBExporter
from loyverse_sdk.exceptions import ExportError


@pytest.fixture
def temp_db():
    """Create a temporary DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_export.duckdb")
        yield db_path


@pytest.mark.integration
@pytest.mark.asyncio
async def test_export_to_duckdb_creates_database(temp_db):
    """Test that export_to_duckdb creates a new database file."""
    # This test doesn't require a real API token - it just tests schema creation
    client = LoyverseClient(api_token="fake_token_for_testing")

    # Initialize schema only (no data export)
    client.init_duckdb_schema(temp_db)

    # Verify database file was created
    assert os.path.exists(temp_db)

    # Verify tables were created
    conn = duckdb.connect(temp_db)
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
    ).fetchall()
    table_names = [t[0] for t in tables]

    # Check for key tables
    assert "categories" in table_names
    assert "items" in table_names
    assert "receipts" in table_names
    assert "receipt_line_items" in table_names

    conn.close()
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_schema_initialization_with_drop(temp_db):
    """Test that schema can be dropped and recreated."""
    client = LoyverseClient(api_token="fake_token_for_testing")

    # Create schema first time
    client.init_duckdb_schema(temp_db)

    # Add some test data
    conn = duckdb.connect(temp_db)
    conn.execute("""
        INSERT INTO categories (id, name, color, created_at, updated_at)
        VALUES ('test1', 'Test Category', 'RED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
    count_before = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    assert count_before == 1
    conn.close()

    # Recreate schema with drop
    client.init_duckdb_schema(temp_db, drop_existing=True)

    # Verify data was cleared
    conn = duckdb.connect(temp_db)
    count_after = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    assert count_after == 0
    conn.close()

    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_exporter_context_manager(temp_db):
    """Test using DuckDBExporter as context manager."""
    client = LoyverseClient(api_token="fake_token_for_testing")

    with DuckDBExporter(client, temp_db) as exporter:
        exporter.init_schema()

        # Verify database was created
        assert os.path.exists(temp_db)

        # Get table counts (should be 0 for new database)
        counts = exporter.get_table_counts()
        assert "categories" in counts
        assert counts["categories"] == 0

    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_sync_metadata_tracking(temp_db):
    """Test that sync metadata is properly tracked."""
    client = LoyverseClient(api_token="fake_token_for_testing")

    exporter = DuckDBExporter(client, temp_db)
    exporter.init_schema()

    # Manually insert some sync metadata
    with exporter.connection.cursor() as conn:
        conn.execute("""
            INSERT INTO sync_metadata (resource_name, last_sync_at, records_count, sync_type)
            VALUES ('categories', CURRENT_TIMESTAMP, 100, 'full')
        """)

    # Retrieve metadata
    metadata = exporter.get_sync_metadata()

    assert "categories" in metadata
    assert metadata["categories"]["records_count"] == 100
    assert metadata["categories"]["sync_type"] == "full"

    exporter.close()
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_foreign_key_relationships(temp_db):
    """Test that foreign key relationships work correctly."""
    client = LoyverseClient(api_token="fake_token_for_testing")
    client.init_duckdb_schema(temp_db)

    conn = duckdb.connect(temp_db)

    # Insert parent records in correct order
    conn.execute("""
        INSERT INTO categories (id, name, color, created_at, updated_at)
        VALUES ('cat1', 'Beverages', 'BLUE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    conn.execute("""
        INSERT INTO items (id, name, category_id, created_at, updated_at)
        VALUES ('item1', 'Coffee', 'cat1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # Verify relationship via JOIN
    result = conn.execute("""
        SELECT i.name, c.name
        FROM items i
        JOIN categories c ON i.category_id = c.id
        WHERE i.id = 'item1'
    """).fetchone()

    assert result is not None
    assert result[0] == "Coffee"
    assert result[1] == "Beverages"

    conn.close()
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_junction_table_relationships(temp_db):
    """Test that junction tables properly link many-to-many relationships."""
    client = LoyverseClient(api_token="fake_token_for_testing")
    client.init_duckdb_schema(temp_db)

    conn = duckdb.connect(temp_db)

    # Insert parent records
    conn.execute("""
        INSERT INTO items (id, name, created_at, updated_at)
        VALUES ('item1', 'Coffee', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    conn.execute("""
        INSERT INTO taxes (id, name, type, rate, created_at, updated_at)
        VALUES ('tax1', 'VAT', 'PERCENT', 10.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    conn.execute("""
        INSERT INTO taxes (id, name, type, rate, created_at, updated_at)
        VALUES ('tax2', 'Service Tax', 'PERCENT', 5.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # Insert junction records
    conn.execute("INSERT INTO item_tax (item_id, tax_id) VALUES ('item1', 'tax1')")
    conn.execute("INSERT INTO item_tax (item_id, tax_id) VALUES ('item1', 'tax2')")

    # Verify many-to-many relationship via JOIN
    results = conn.execute("""
        SELECT i.name, t.name, t.rate
        FROM items i
        JOIN item_tax it ON i.id = it.item_id
        JOIN taxes t ON it.tax_id = t.id
        WHERE i.id = 'item1'
        ORDER BY t.rate DESC
    """).fetchall()

    assert len(results) == 2
    assert results[0][1] == "VAT"
    assert results[0][2] == 10.0
    assert results[1][1] == "Service Tax"
    assert results[1][2] == 5.0

    conn.close()
    await client.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_child_table_relationships(temp_db):
    """Test that child tables properly reference parent records."""
    client = LoyverseClient(api_token="fake_token_for_testing")
    client.init_duckdb_schema(temp_db)

    conn = duckdb.connect(temp_db)

    # Insert required parent records
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

    # Insert receipt
    conn.execute("""
        INSERT INTO receipts (
            receipt_number, receipt_type,
            total_money, employee_id, store_id, pos_device_id
        )
        VALUES (
            '001', 'SALE',
            150.0, 'emp1', 'store1', 'dev1'
        )
    """)

    # Insert items for the receipt
    conn.execute("""
        INSERT INTO items (id, name, created_at, updated_at)
        VALUES ('item1', 'Item 1', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # Insert variant records for the receipt line items
    conn.execute("""
        INSERT INTO variants (id, item_id, sku, cost, default_pricing_type, created_at, updated_at)
        VALUES ('variant1', 'item1', 'SKU001', 0.0, 'DEFAULT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)
    conn.execute("""
        INSERT INTO variants (id, item_id, sku, cost, default_pricing_type, created_at, updated_at)
        VALUES ('variant2', 'item1', 'SKU002', 0.0, 'DEFAULT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    """)

    # Insert line items
    conn.execute("""
        INSERT INTO receipt_line_items (
            id, receipt_id, item_id, item_name, quantity, price, total_money
        )
        VALUES
            ('line1', '001', 'item1', 'Coffee', 2, 10.0, 20.0),
            ('line2', '001', 'item1', 'Tea', 1, 8.0, 8.0)
    """)

    # Verify parent-child relationship via JOIN
    results = conn.execute("""
        SELECT r.receipt_number, l.item_name, l.quantity, l.price
        FROM receipts r
        JOIN receipt_line_items l ON r.receipt_number = l.receipt_id
        WHERE r.receipt_number = '001'
        ORDER BY l.price DESC
    """).fetchall()

    assert len(results) == 2
    assert results[0][1] == "Coffee"
    assert results[0][2] == 2
    assert results[1][1] == "Tea"
    assert results[1][2] == 1

    conn.close()
    await client.close()
