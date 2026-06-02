"""
Unit tests for loyverse_sdk.db.schema_builder module.

Tests table creation, foreign keys, indexes, and schema initialization.
"""

import pytest
import duckdb
import tempfile
import os
from pathlib import Path

from loyverse_sdk.db.schema_builder import (
    create_duckdb_schema,
    create_indexes,
    CategoryDB,
    StoreDB,
    SupplierDB,
    TaxDB,
    ModifierDB,
    DiscountDB,
    EmployeeDB,
    CustomerDB,
    PosDeviceDB,
    PaymentTypeDB,
    ItemDB,
    VariantDB,
    ReceiptDB,
    MerchantDB,
    ReceiptLineItemDB,
    ModifierOptionDB,
    EmployeeStoreDB,
    ItemTaxDB,
    ItemModifierDB,
    ModifierStoreDB,
    TaxStoreDB,
    DiscountStoreDB,
    PaymentTypeStoreDB,
    VariantStoreDB,
    SyncMetadataDB,
)


@pytest.fixture
def temp_db():
    """Create a temporary DuckDB database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.duckdb")
        yield db_path
        # Cleanup happens automatically with context manager


@pytest.fixture
def db_with_schema(temp_db):
    """Create a database with schema initialized."""
    create_duckdb_schema(temp_db, drop_existing=False)
    return temp_db


class TestSchemaCreation:
    """Test database schema creation."""

    def test_create_schema_creates_all_main_tables(self, temp_db):
        """Test that all 14 main resource tables are created."""
        create_duckdb_schema(temp_db, drop_existing=False)

        conn = duckdb.connect(temp_db)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        # Check main tables exist
        expected_main_tables = [
            "categories",
            "stores",
            "suppliers",
            "taxes",
            "modifiers",
            "discounts",
            "employees",
            "customers",
            "pos_devices",
            "payment_types",
            "items",
            "variants",
            "receipts",
            "merchant",
        ]

        for table in expected_main_tables:
            assert table in table_names, f"Main table '{table}' not found"

        conn.close()

    def test_create_schema_creates_junction_tables(self, temp_db):
        """Test that junction tables for many-to-many relationships are created."""
        create_duckdb_schema(temp_db, drop_existing=False)

        conn = duckdb.connect(temp_db)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        # Check junction tables exist
        expected_junction_tables = [
            "employee_store",
            "item_tax",
            "item_modifier",
            "modifier_store",
            "tax_store",
            "discount_store",
            "payment_type_store",
            "variant_store",
        ]

        for table in expected_junction_tables:
            assert table in table_names, f"Junction table '{table}' not found"

        conn.close()

    def test_create_schema_creates_child_tables(self, temp_db):
        """Test that child tables for nested data are created."""
        create_duckdb_schema(temp_db, drop_existing=False)

        conn = duckdb.connect(temp_db)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        # Check child tables exist
        expected_child_tables = ["receipt_line_items", "modifier_options"]

        for table in expected_child_tables:
            assert table in table_names, f"Child table '{table}' not found"

        conn.close()

    def test_create_schema_creates_metadata_table(self, temp_db):
        """Test that sync_metadata table is created."""
        create_duckdb_schema(temp_db, drop_existing=False)

        conn = duckdb.connect(temp_db)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='main'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "sync_metadata" in table_names, "Metadata table not found"

        conn.close()

    def test_create_schema_with_drop_existing(self, db_with_schema):
        """Test that drop_existing=True recreates all tables."""
        conn = duckdb.connect(db_with_schema)

        # Insert test data
        conn.execute("""
            INSERT INTO categories (id, name, color, created_at, updated_at)
            VALUES ('cat1', 'Test', 'RED', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        count_before = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        assert count_before == 1

        conn.close()

        # Recreate schema with drop_existing=True
        create_duckdb_schema(db_with_schema, drop_existing=True)

        conn = duckdb.connect(db_with_schema)
        count_after = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        assert count_after == 0, "Table should be empty after drop and recreate"

        conn.close()


class TestTableStructure:
    """Test individual table structures and constraints."""

    def test_categories_table_structure(self, db_with_schema):
        """Test categories table has correct columns."""
        conn = duckdb.connect(db_with_schema)

        columns = conn.execute("PRAGMA table_info(categories)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "name",
            "color",
            "created_at",
            "updated_at",
            "deleted_at",
        ]
        for col in expected_columns:
            assert col in column_names, f"Column '{col}' missing from categories"

        conn.close()

    def test_receipts_table_structure(self, db_with_schema):
        """Test receipts table has correct columns and foreign keys."""
        conn = duckdb.connect(db_with_schema)

        columns = conn.execute("PRAGMA table_info(receipts)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "receipt_number",
            "receipt_type",
            "total_money",
            "customer_id",
            "employee_id",
            "store_id",
            "pos_device_id",
        ]

        for col in expected_columns:
            assert col in column_names, f"Column '{col}' missing from receipts"

        conn.close()

    def test_receipt_line_items_table_structure(self, db_with_schema):
        """Test receipt_line_items child table structure."""
        conn = duckdb.connect(db_with_schema)

        columns = conn.execute("PRAGMA table_info(receipt_line_items)").fetchall()
        column_names = [col[1] for col in columns]

        expected_columns = [
            "id",
            "receipt_id",
            "item_id",
            "item_name",
            "quantity",
            "price",
        ]

        for col in expected_columns:
            assert col in column_names, (
                f"Column '{col}' missing from receipt_line_items"
            )

        conn.close()

    def test_junction_table_structure(self, db_with_schema):
        """Test junction table has correct primary key columns."""
        conn = duckdb.connect(db_with_schema)

        # Test item_tax junction table
        columns = conn.execute("PRAGMA table_info(item_tax)").fetchall()
        column_names = [col[1] for col in columns]

        assert "item_id" in column_names
        assert "tax_id" in column_names

        conn.close()


class TestForeignKeys:
    """Test foreign key relationships."""

    def test_receipt_foreign_keys_valid(self, db_with_schema):
        """Test that receipts can reference related tables."""
        conn = duckdb.connect(db_with_schema)

        # Insert required parent records
        conn.execute("""
            INSERT INTO stores (id, name, created_at, updated_at)
            VALUES ('store1', 'Test Store', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        conn.execute("""
            INSERT INTO employees (id, name, created_at, updated_at)
            VALUES ('emp1', 'Test Employee', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        conn.execute("""
            INSERT INTO pos_devices (id, name, store_id)
            VALUES ('dev1', 'Test Device', 'store1')
        """)

        conn.execute("""
            INSERT INTO payment_types (id, name, type, created_at, updated_at)
            VALUES ('pay1', 'Cash', 'CASH', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        # Insert receipt with valid foreign keys
        conn.execute("""
            INSERT INTO receipts (
                receipt_number, receipt_type,
                total_money, employee_id, store_id, pos_device_id
            )
            VALUES (
                '001', 'SALE',
                100.0, 'emp1', 'store1', 'dev1'
            )
        """)

        # Verify insert succeeded
        count = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
        assert count == 1

        conn.close()

    def test_line_items_foreign_key_to_receipt(self, db_with_schema):
        """Test that line items can reference receipts."""
        conn = duckdb.connect(db_with_schema)

        # Insert required parent records
        conn.execute("""
            INSERT INTO stores (id, name, created_at, updated_at)
            VALUES ('store1', 'Test Store', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        conn.execute("""
            INSERT INTO employees (id, name, created_at, updated_at)
            VALUES ('emp1', 'Test Employee', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        conn.execute("""
            INSERT INTO pos_devices (id, name, store_id)
            VALUES ('dev1', 'Test Device', 'store1')
        """)

        conn.execute("""
            INSERT INTO payment_types (id, name, type, created_at, updated_at)
            VALUES ('pay1', 'Cash', 'CASH', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        conn.execute("""
            INSERT INTO receipts (
                receipt_number, receipt_type,
                total_money, employee_id, store_id, pos_device_id
            )
            VALUES (
                '001', 'SALE',
                100.0, 'emp1', 'store1', 'dev1'
            )
        """)

        # Insert parent items record
        conn.execute("""
            INSERT INTO items (id, name, created_at, updated_at)
            VALUES ('item1', 'Test Item', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        # Insert parent variant record
        conn.execute("""
            INSERT INTO variants (id, item_id, sku, cost, default_pricing_type, created_at, updated_at)
            VALUES ('variant1', 'item1', 'SKU001', 0.0, 'DEFAULT', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        # Insert line item
        conn.execute("""
            INSERT INTO receipt_line_items (
                id, receipt_id, item_id, item_name, quantity, price, total_money
            )
            VALUES (
                'line1', '001', 'item1', 'Test Item', 1, 100.0, 100.0
            )
        """)

        # Verify insert succeeded
        count = conn.execute("SELECT COUNT(*) FROM receipt_line_items").fetchone()[0]
        assert count == 1

        conn.close()

    def test_junction_table_foreign_keys(self, db_with_schema):
        """Test junction table foreign key relationships."""
        conn = duckdb.connect(db_with_schema)

        # Insert item
        conn.execute("""
            INSERT INTO items (id, name, created_at, updated_at)
            VALUES ('item1', 'Test Item', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        # Insert tax
        conn.execute("""
            INSERT INTO taxes (id, name, type, rate, created_at, updated_at)
            VALUES ('tax1', 'VAT', 'PERCENT', 10.0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """)

        # Insert junction record
        conn.execute("""
            INSERT INTO item_tax (item_id, tax_id)
            VALUES ('item1', 'tax1')
        """)

        # Verify insert succeeded
        count = conn.execute("SELECT COUNT(*) FROM item_tax").fetchone()[0]
        assert count == 1

        conn.close()


class TestIndexes:
    """Test index creation."""

    def test_create_indexes_succeeds(self, db_with_schema):
        """Test that create_indexes runs without errors."""
        # Should not raise any exceptions
        create_indexes(db_with_schema)

    def test_indexes_exist_on_foreign_keys(self, db_with_schema):
        """Test that indexes are created on foreign key columns."""
        create_indexes(db_with_schema)

        conn = duckdb.connect(db_with_schema)

        # Check for indexes (DuckDB-specific query)
        indexes = conn.execute("""
            SELECT DISTINCT index_name
            FROM duckdb_indexes()
            WHERE index_name LIKE 'idx_%'
        """).fetchall()

        index_names = [idx[0] for idx in indexes]

        # Should have indexes on foreign key columns
        assert len(index_names) > 0, "No indexes created"

        conn.close()
