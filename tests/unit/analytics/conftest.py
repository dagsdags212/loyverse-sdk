"""
Shared fixtures for analytics tests.

Creates an in-memory DuckDB database pre-populated with a small set of
representative data so analytics queries can be verified deterministically.
"""

import pytest
import duckdb
from datetime import datetime


@pytest.fixture
def db():
    """In-memory DuckDB with fixture data."""
    conn = duckdb.connect(":memory:")

    # Create schema
    conn.execute("""
        CREATE TABLE categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE stores (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            address TEXT, city TEXT, state TEXT, postal_code TEXT,
            country TEXT, phone_number TEXT, description TEXT,
            created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE items (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            handle TEXT, reference_id TEXT, description TEXT,
            track_stock BOOLEAN DEFAULT FALSE,
            sold_by_weight BOOLEAN DEFAULT FALSE,
            is_composite BOOLEAN DEFAULT FALSE,
            use_production BOOLEAN DEFAULT FALSE,
            category_id TEXT, primary_supplier_id TEXT,
            form TEXT DEFAULT 'SQUARE', color TEXT DEFAULT 'GREY',
            image_url TEXT, option1_name TEXT, option2_name TEXT, option3_name TEXT,
            created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT, phone_number TEXT,
            is_owner BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT, phone_number TEXT,
            address TEXT, city TEXT, region TEXT,
            postal_code TEXT, country_code TEXT, note TEXT,
            customer_code TEXT, first_visit TIMESTAMP, last_visit TIMESTAMP,
            total_visits INTEGER DEFAULT 0, total_spent DOUBLE DEFAULT 0.0,
            total_points DOUBLE DEFAULT 0.0, permanent_deletion_at TIMESTAMP,
            created_at TIMESTAMP NOT NULL, updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE payment_types (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'CASH',
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE receipts (
            id TEXT,
            receipt_number TEXT PRIMARY KEY,
            note TEXT, receipt_type TEXT NOT NULL,
            refund_for TEXT, order_id TEXT,
            created_at TIMESTAMP, updated_at TIMESTAMP, deleted_at TIMESTAMP,
            source TEXT, receipt_date TIMESTAMP, cancelled_at TIMESTAMP,
            total_money DOUBLE NOT NULL,
            total_tax DOUBLE DEFAULT 0.0,
            points_earned DOUBLE DEFAULT 0.0,
            points_deducted DOUBLE DEFAULT 0.0,
            points_balance DOUBLE DEFAULT 0.0,
            total_discount DOUBLE DEFAULT 0.0,
            customer_id TEXT, employee_id TEXT, store_id TEXT, pos_device_id TEXT,
            dining_option TEXT, tip DOUBLE DEFAULT 0.0, surcharge DOUBLE DEFAULT 0.0
        )
    """)
    conn.execute("""
        CREATE TABLE receipt_line_items (
            id TEXT PRIMARY KEY,
            receipt_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            variant_id TEXT,
            item_name TEXT NOT NULL,
            variant_name TEXT, sku TEXT,
            quantity DOUBLE NOT NULL,
            price DOUBLE NOT NULL,
            gross_total_money DOUBLE DEFAULT 0.0,
            total_money DOUBLE NOT NULL,
            cost DOUBLE, cost_total DOUBLE,
            line_note TEXT, total_discount DOUBLE DEFAULT 0.0
        )
    """)
    conn.execute("""
        CREATE TABLE variants (
            id TEXT PRIMARY KEY,
            item_id TEXT NOT NULL,
            sku TEXT NOT NULL,
            reference_variant_id TEXT,
            option1_value TEXT, option2_value TEXT, option3_value TEXT,
            barcode TEXT,
            cost DOUBLE NOT NULL DEFAULT 0.0,
            purchase_cost DOUBLE,
            default_pricing_type TEXT NOT NULL DEFAULT 'VARIABLE',
            default_price DOUBLE,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL,
            deleted_at TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE inventory (
            variant_id TEXT NOT NULL,
            store_id TEXT NOT NULL,
            in_stock INTEGER NOT NULL DEFAULT 0,
            updated_at TIMESTAMP NOT NULL,
            PRIMARY KEY (variant_id, store_id)
        )
    """)
    conn.execute("""
        CREATE TABLE variant_store (
            variant_id TEXT NOT NULL,
            store_id TEXT NOT NULL,
            optimal_stock DOUBLE,
            low_stock_threshold DOUBLE,
            PRIMARY KEY (variant_id, store_id)
        )
    """)

    # Seed data
    now = datetime(2026, 5, 1)
    conn.execute(
        "INSERT INTO categories VALUES ('cat-svc', 'Service', 'BLUE', '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO categories VALUES ('cat-soap', 'Soaps', 'GREEN', '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO stores VALUES ('store1', 'Main Store', NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO items VALUES ('item-wash', 'Wash', NULL, NULL, NULL, FALSE, FALSE, FALSE, FALSE, 'cat-svc', NULL, 'SQUARE', 'GREY', NULL, NULL, NULL, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO items VALUES ('item-dry', 'Dry', NULL, NULL, NULL, FALSE, FALSE, FALSE, FALSE, 'cat-svc', NULL, 'SQUARE', 'GREY', NULL, NULL, NULL, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO items VALUES ('item-det', 'Detergent', NULL, NULL, NULL, FALSE, FALSE, FALSE, FALSE, 'cat-soap', NULL, 'SQUARE', 'GREY', NULL, NULL, NULL, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO employees VALUES ('emp1', 'Alice', NULL, NULL, FALSE, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO employees VALUES ('emp2', 'Bob', NULL, NULL, FALSE, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO customers VALUES ('cust1', 'John Doe', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-04-01', '2026-05-15', 3, 750.0, 0.0, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO customers VALUES ('cust2', 'Jane Smith', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-05-15', '2026-05-15', 1, 200.0, 0.0, NULL, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO customers VALUES ('cust3', 'Bob Wilson', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '2026-03-01', '2026-04-01', 1, 300.0, 0.0, NULL, '2026-01-01', '2026-01-01', NULL)"
    )

    # Variants (one per item for simplicity)
    conn.execute(
        "INSERT INTO variants VALUES ('var-wash', 'item-wash', 'SKU-WASH', NULL, NULL, NULL, NULL, NULL, 30.0, 35.0, 'FIXED', 100.0, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO variants VALUES ('var-dry', 'item-dry', 'SKU-DRY', NULL, NULL, NULL, NULL, NULL, 40.0, 45.0, 'FIXED', 125.0, '2026-01-01', '2026-01-01', NULL)"
    )
    conn.execute(
        "INSERT INTO variants VALUES ('var-det', 'item-det', 'SKU-DET', NULL, NULL, NULL, NULL, NULL, 10.0, 12.0, 'FIXED', 25.0, '2026-01-01', '2026-01-01', NULL)"
    )

    # Inventory — stock on hand per variant/store
    conn.execute(
        "INSERT INTO inventory VALUES ('var-wash', 'store1', 10, '2026-05-01')"
    )
    conn.execute(
        "INSERT INTO inventory VALUES ('var-dry', 'store1', 5, '2026-05-01')"
    )
    conn.execute(
        "INSERT INTO inventory VALUES ('var-det', 'store1', 3, '2026-05-01')"
    )

    # Variant-store thresholds
    conn.execute(
        "INSERT INTO variant_store VALUES ('var-det', 'store1', 20, 5)"
    )

    # Receipts over 3 days
    dates = [
        (datetime(2026, 5, 1, 9, 0), "SALE"),
        (datetime(2026, 5, 1, 12, 0), "SALE"),
        (datetime(2026, 5, 1, 15, 0), "SALE"),
        (datetime(2026, 5, 2, 10, 0), "SALE"),
        (datetime(2026, 5, 2, 14, 0), "SALE"),
        (datetime(2026, 5, 3, 9, 0), "SALE"),
        (datetime(2026, 5, 3, 16, 0), "REFUND"),
    ]
    for i, (dt, rtype) in enumerate(dates):
        num = f"RCPT-{i + 1:04d}"
        total = 250.0 if rtype == "SALE" else -100.0
        tip = 10.0 if rtype == "SALE" and i % 2 == 0 else 0.0
        discount = 25.0 if i == 0 else 0.0
        cancelled = None
        cust = f"cust{i % 3 + 1}" if rtype == "SALE" else None
        emp = "emp1" if i % 2 == 0 else "emp2"
        conn.execute(
            """INSERT INTO receipts
               (id, receipt_number, receipt_type, created_at, receipt_date,
                total_money, total_discount, customer_id, employee_id,
                store_id, tip, surcharge)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                f"id-{num}",
                num,
                rtype,
                dt,
                dt,
                total,
                discount,
                cust,
                emp,
                "store1",
                tip,
                0.0,
            ],
        )

    # Line items — (id, receipt_id, item_id, item_name, qty, price, total_money, variant_id, cost, cost_total)
    line_items = [
        ("L1", "RCPT-0001", "item-wash", "Wash", 1.0, 100.0, 100.0, "var-wash", 30.0, 30.0),
        ("L2", "RCPT-0001", "item-dry", "Dry", 1.0, 125.0, 125.0, "var-dry", 40.0, 40.0),
        ("L3", "RCPT-0001", "item-det", "Detergent", 1.0, 25.0, 25.0, "var-det", 10.0, 10.0),
        ("L4", "RCPT-0002", "item-wash", "Wash", 2.0, 100.0, 200.0, "var-wash", 30.0, 60.0),
        ("L5", "RCPT-0002", "item-det", "Detergent", 1.0, 50.0, 50.0, "var-det", 10.0, 10.0),
        ("L6", "RCPT-0003", "item-dry", "Dry", 1.0, 125.0, 125.0, "var-dry", 40.0, 40.0),
        ("L7", "RCPT-0003", "item-wash", "Wash", 1.0, 100.0, 100.0, "var-wash", 30.0, 30.0),
        ("L8", "RCPT-0003", "item-det", "Detergent", 1.0, 25.0, 25.0, "var-det", 10.0, 10.0),
        ("L9", "RCPT-0004", "item-dry", "Dry", 1.0, 125.0, 125.0, "var-dry", 40.0, 40.0),
        ("L10", "RCPT-0004", "item-det", "Detergent", 2.0, 25.0, 50.0, "var-det", 10.0, 20.0),
        ("L11", "RCPT-0005", "item-wash", "Wash", 1.0, 100.0, 100.0, "var-wash", 30.0, 30.0),
        ("L12", "RCPT-0005", "item-dry", "Dry", 1.0, 125.0, 125.0, "var-dry", 40.0, 40.0),
        ("L13", "RCPT-0006", "item-wash", "Wash", 3.0, 100.0, 300.0, "var-wash", 30.0, 90.0),
        ("L14", "RCPT-0007", "item-dry", "Dry", 1.0, 100.0, -100.0, "var-dry", 40.0, -40.0),
    ]
    for item in line_items:
        conn.execute(
            """INSERT INTO receipt_line_items
               (id, receipt_id, item_id, item_name, quantity, price,
                total_money, variant_id, cost, cost_total)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [item[0], item[1], item[2], item[3], item[4], item[5],
             item[6], item[7], item[8], item[9]],
        )

    # Verify data integrity
    receipts = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]
    lines = conn.execute("SELECT COUNT(*) FROM receipt_line_items").fetchone()[0]
    assert receipts == 7, f"Expected 7 receipts, got {receipts}"
    assert lines == 14, f"Expected 14 line items, got {lines}"

    yield conn
    conn.close()
