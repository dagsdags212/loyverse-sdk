"""
DuckDB schema builder for Loyverse data export.

This module defines SQLModel table definitions for all Loyverse resources optimized for DuckDB.
All UUID fields are stored as TEXT for DuckDB compatibility.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
import duckdb

from loyverse_sdk.core.console import console


# ============================================================================
# MAIN RESOURCE TABLES
# ============================================================================


class CategoryDB(SQLModel, table=True):
    """Product categories"""

    __tablename__ = "categories"

    id: str = Field(primary_key=True)
    name: str
    color: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class StoreDB(SQLModel, table=True):
    """Business locations/stores"""

    __tablename__ = "stores"

    id: str = Field(primary_key=True)
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    phone_number: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class SupplierDB(SQLModel, table=True):
    """Vendors/suppliers"""

    __tablename__ = "suppliers"

    id: str = Field(primary_key=True)
    name: str
    contact: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class TaxDB(SQLModel, table=True):
    """Tax configurations"""

    __tablename__ = "taxes"

    id: str = Field(primary_key=True)
    name: str
    type: str
    rate: float
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ModifierDB(SQLModel, table=True):
    """Item modifiers (e.g., size, toppings)"""

    __tablename__ = "modifiers"

    id: str = Field(primary_key=True)
    name: str
    position: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class DiscountDB(SQLModel, table=True):
    """Discount rules"""

    __tablename__ = "discounts"

    id: str = Field(primary_key=True)
    type: str
    name: str
    discount_amount: Optional[float] = None
    discount_percent: Optional[float] = None
    restricted_access: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class EmployeeDB(SQLModel, table=True):
    """Employees/staff"""

    __tablename__ = "employees"

    id: str = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    is_owner: bool = False
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class CustomerDB(SQLModel, table=True):
    """Customers"""

    __tablename__ = "customers"

    id: str = Field(primary_key=True)
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    country_code: Optional[str] = None
    note: Optional[str] = None
    customer_code: Optional[str] = None
    first_visit: Optional[datetime] = None
    last_visit: Optional[datetime] = None
    total_visits: int = 0
    total_spent: float = 0.0
    total_points: float = 0.0
    permanent_deletion_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class PosDeviceDB(SQLModel, table=True):
    """Point of sale devices"""

    __tablename__ = "pos_devices"

    id: str = Field(primary_key=True)
    name: str
    store_id: str = Field(foreign_key="stores.id")
    activated: bool = True
    deleted_at: Optional[datetime] = None


class PaymentTypeDB(SQLModel, table=True):
    """Payment methods"""

    __tablename__ = "payment_types"

    id: str = Field(primary_key=True)
    name: str
    type: str = "CASH"
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class ItemDB(SQLModel, table=True):
    """Inventory items/products"""

    __tablename__ = "items"

    id: str = Field(primary_key=True)
    name: str
    handle: Optional[str] = None
    reference_id: Optional[str] = None
    description: Optional[str] = None
    track_stock: bool = False
    sold_by_weight: bool = False
    is_composite: bool = False
    use_production: bool = False
    category_id: Optional[str] = Field(default=None, foreign_key="categories.id")
    primary_supplier_id: Optional[str] = Field(default=None, foreign_key="suppliers.id")
    form: str = "SQUARE"
    color: str = "GREY"
    image_url: Optional[str] = None
    option1_name: Optional[str] = None
    option2_name: Optional[str] = None
    option3_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class VariantDB(SQLModel, table=True):
    """Product variants"""

    __tablename__ = "variants"

    id: str = Field(primary_key=True)
    item_id: str = Field(foreign_key="items.id")
    sku: str
    reference_variant_id: Optional[str] = None
    option1_value: Optional[str] = None
    option2_value: Optional[str] = None
    option3_value: Optional[str] = None
    barcode: Optional[str] = None
    cost: float = 0.0
    purchase_cost: Optional[float] = None
    default_pricing_type: str = "VARIABLE"
    default_price: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class WebhookDB(SQLModel, table=True):
    """Webhook registrations"""

    __tablename__ = "webhooks"

    id: str = Field(primary_key=True)
    merchant_id: str
    url: str
    type: str
    status: str = "ENABLED"
    created_at: datetime
    updated_at: datetime


class ReceiptDB(SQLModel, table=True):
    """Sales receipts/transactions"""

    __tablename__ = "receipts"

    id: Optional[str] = None
    receipt_number: str = Field(primary_key=True)
    note: Optional[str] = None
    receipt_type: str
    refund_for: Optional[str] = None
    order_id: Optional[str] = None
    receipt_date: datetime
    source: Optional[str] = None
    total_money: float
    total_tax: float = 0.0
    points_earned: float = 0.0
    points_deducted: float = 0.0
    points_balance: float = 0.0
    total_discount: float = 0.0
    customer_id: Optional[str] = Field(default=None, foreign_key="customers.id")
    employee_id: Optional[str] = Field(default=None, foreign_key="employees.id")
    store_id: Optional[str] = Field(default=None, foreign_key="stores.id")
    pos_device_id: Optional[str] = Field(default=None, foreign_key="pos_devices.id")
    dining_option: Optional[str] = None
    surcharge: float = 0.0
    tip: float = 0.0
    cancelled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class MerchantDB(SQLModel, table=True):
    """Merchant/business account information"""

    __tablename__ = "merchant"

    id: str = Field(primary_key=True)
    business_name: str
    email: Optional[str] = None
    country: Optional[str] = None
    currency: str
    created_at: datetime


class InventoryDB(SQLModel, table=True):
    """Inventory item stock levels per variant per store"""

    __tablename__ = "inventory"

    variant_id: str = Field(primary_key=True)
    store_id: str = Field(primary_key=True)
    in_stock: int = 0
    updated_at: datetime


class ShiftDB(SQLModel, table=True):
    """Employee work shifts with POS device cashup"""

    __tablename__ = "shifts"

    id: str = Field(primary_key=True)
    store_id: str
    pos_device_id: str
    opened_at: datetime
    closed_at: datetime | None = None
    opened_by_employee: str
    closed_by_employee: str | None = None
    starting_cash: float = 0.0
    cash_payments: float = 0.0
    cash_refunds: float = 0.0
    paid_in: float = 0.0
    paid_out: float = 0.0
    expected_cash: float = 0.0
    actual_cash: float = 0.0
    gross_sales: float = 0.0
    refunds: float = 0.0
    discounts: float = 0.0
    net_sales: float = 0.0
    tip: float = 0.0
    surcharge: float = 0.0
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None


class ShiftTaxDB(SQLModel, table=True):
    """Shift tax breakdown (child of shifts)"""

    __tablename__ = "shift_taxes"

    id: str = Field(primary_key=True)
    shift_id: str = Field(foreign_key="shifts.id")
    name: str
    rate: float
    amount: float


class ShiftPaymentDB(SQLModel, table=True):
    """Shift payment type breakdown (child of shifts)"""

    __tablename__ = "shift_payments"

    id: str = Field(primary_key=True)
    shift_id: str = Field(foreign_key="shifts.id")
    name: str
    amount: float


class ShiftCashMovementDB(SQLModel, table=True):
    """Shift cash movements (child of shifts)"""

    __tablename__ = "shift_cash_movements"

    id: str = Field(primary_key=True)
    shift_id: str = Field(foreign_key="shifts.id")
    time: datetime
    amount: float
    note: str | None = None


# ============================================================================
# JUNCTION TABLES (Many-to-Many Relationships)
# ============================================================================


class EmployeeStoreDB(SQLModel, table=True):
    """Links employees to stores they work at"""

    __tablename__ = "employee_store"

    employee_id: str = Field(foreign_key="employees.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)


class ItemTaxDB(SQLModel, table=True):
    """Links items to taxes"""

    __tablename__ = "item_tax"

    item_id: str = Field(foreign_key="items.id", primary_key=True)
    tax_id: str = Field(foreign_key="taxes.id", primary_key=True)


class ItemModifierDB(SQLModel, table=True):
    """Links items to modifiers"""

    __tablename__ = "item_modifier"

    item_id: str = Field(foreign_key="items.id", primary_key=True)
    modifier_id: str = Field(foreign_key="modifiers.id", primary_key=True)


class ModifierStoreDB(SQLModel, table=True):
    """Links modifiers to stores"""

    __tablename__ = "modifier_store"

    modifier_id: str = Field(foreign_key="modifiers.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)


class TaxStoreDB(SQLModel, table=True):
    """Links taxes to stores"""

    __tablename__ = "tax_store"

    tax_id: str = Field(foreign_key="taxes.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)


class DiscountStoreDB(SQLModel, table=True):
    """Links discounts to stores"""

    __tablename__ = "discount_store"

    discount_id: str = Field(foreign_key="discounts.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)


class PaymentTypeStoreDB(SQLModel, table=True):
    """Links payment types to stores"""

    __tablename__ = "payment_type_store"

    payment_type_id: str = Field(foreign_key="payment_types.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)


class VariantStoreDB(SQLModel, table=True):
    """Links variants to stores with additional store-specific data"""

    __tablename__ = "variant_store"

    variant_id: str = Field(foreign_key="variants.id", primary_key=True)
    store_id: str = Field(foreign_key="stores.id", primary_key=True)
    available_for_sale: bool = True
    optimal_stock: Optional[float] = None
    low_stock_threshold: Optional[float] = None


# ============================================================================
# CHILD TABLES (One-to-Many Relationships)
# ============================================================================


class ReceiptLineItemDB(SQLModel, table=True):
    """Line items within receipts"""

    __tablename__ = "receipt_line_items"

    id: str = Field(primary_key=True)
    receipt_id: str = Field(foreign_key="receipts.receipt_number")
    item_id: str = Field(foreign_key="items.id")
    variant_id: Optional[str] = Field(default=None, foreign_key="variants.id")
    item_name: str
    variant_name: Optional[str] = None
    sku: Optional[str] = None
    quantity: float
    price: float
    gross_total_money: float = 0.0
    total_money: float
    cost: Optional[float] = None
    cost_total: Optional[float] = None
    line_note: Optional[str] = None
    total_discount: float = 0.0


class ModifierOptionDB(SQLModel, table=True):
    """Options within modifiers"""

    __tablename__ = "modifier_options"

    id: str = Field(primary_key=True)
    modifier_id: str = Field(foreign_key="modifiers.id")
    name: str
    price: float = 0.0
    position: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


# ============================================================================
# METADATA TABLE
# ============================================================================


class SyncMetadataDB(SQLModel, table=True):
    """Tracks sync state for each resource"""

    __tablename__ = "sync_metadata"

    resource_name: str = Field(primary_key=True)
    last_sync_at: datetime
    records_count: int
    sync_type: str  # 'full' or 'incremental'


# ============================================================================
# SCHEMA CREATION FUNCTIONS
# ============================================================================


def create_duckdb_schema(db_path: str, drop_existing: bool = False) -> None:
    """
    Create all tables in the DuckDB database.

    Args:
        db_path: Path to DuckDB database file
        drop_existing: If True, drops all tables before creating

    Example:
        create_duckdb_schema("loyverse.duckdb")
    """
    conn = duckdb.connect(db_path)

    try:
        if drop_existing:
            # Drop all tables in reverse dependency order
            tables = [
                "sync_metadata",
                "modifier_options",
                "receipt_line_items",
                "shift_cash_movements",
                "shift_payments",
                "shift_taxes",
                "variant_store",
                "payment_type_store",
                "discount_store",
                "tax_store",
                "modifier_store",
                "item_modifier",
                "item_tax",
                "employee_store",
                "inventory",
                "shifts",
                "merchant",
                "webhooks",
                "receipts",
                "variants",
                "items",
                "payment_types",
                "pos_devices",
                "customers",
                "employees",
                "discounts",
                "modifiers",
                "taxes",
                "suppliers",
                "stores",
                "categories",
            ]
            for table in tables:
                conn.execute(f"DROP TABLE IF EXISTS {table}")

        # Create tables using SQLModel metadata
        # Note: SQLModel.metadata.create_all() requires SQLAlchemy engine,
        # so we'll create tables directly with SQL for DuckDB

        # Main tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                color TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS stores (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT,
                city TEXT,
                state TEXT,
                postal_code TEXT,
                country TEXT,
                phone_number TEXT,
                description TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                contact TEXT,
                email TEXT,
                phone_number TEXT,
                website TEXT,
                address_1 TEXT,
                address_2 TEXT,
                city TEXT,
                region TEXT,
                postal_code TEXT,
                country_code TEXT,
                note TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS taxes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                rate DOUBLE NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS modifiers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                position INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS discounts (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                discount_amount DOUBLE,
                discount_percent DOUBLE,
                restricted_access BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone_number TEXT,
                is_owner BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                phone_number TEXT,
                address TEXT,
                city TEXT,
                region TEXT,
                postal_code TEXT,
                country_code TEXT,
                note TEXT,
                customer_code TEXT,
                first_visit TIMESTAMP,
                last_visit TIMESTAMP,
                total_visits INTEGER NOT NULL DEFAULT 0,
                total_spent DOUBLE NOT NULL DEFAULT 0.0,
                total_points DOUBLE NOT NULL DEFAULT 0.0,
                permanent_deletion_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS pos_devices (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                store_id TEXT NOT NULL,
                activated BOOLEAN NOT NULL DEFAULT TRUE,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_types (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL DEFAULT 'CASH',
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                handle TEXT,
                reference_id TEXT,
                description TEXT,
                track_stock BOOLEAN NOT NULL DEFAULT FALSE,
                sold_by_weight BOOLEAN NOT NULL DEFAULT FALSE,
                is_composite BOOLEAN NOT NULL DEFAULT FALSE,
                use_production BOOLEAN NOT NULL DEFAULT FALSE,
                category_id TEXT,
                primary_supplier_id TEXT,
                form TEXT NOT NULL DEFAULT 'SQUARE',
                color TEXT NOT NULL DEFAULT 'GREY',
                image_url TEXT,
                option1_name TEXT,
                option2_name TEXT,
                option3_name TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS variants (
                id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                sku TEXT NOT NULL,
                reference_variant_id TEXT,
                option1_value TEXT,
                option2_value TEXT,
                option3_value TEXT,
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
            CREATE TABLE IF NOT EXISTS receipts (
                id TEXT,
                receipt_number TEXT PRIMARY KEY,
                note TEXT,
                receipt_type TEXT NOT NULL,
                refund_for TEXT,
                order_id TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                deleted_at TIMESTAMP,
                source TEXT,
                receipt_date TIMESTAMP,
                cancelled_at TIMESTAMP,
                total_money DOUBLE NOT NULL,
                total_tax DOUBLE NOT NULL DEFAULT 0.0,
                points_earned DOUBLE NOT NULL DEFAULT 0.0,
                points_deducted DOUBLE NOT NULL DEFAULT 0.0,
                points_balance DOUBLE NOT NULL DEFAULT 0.0,
                total_discount DOUBLE NOT NULL DEFAULT 0.0,
                customer_id TEXT,
                employee_id TEXT,
                store_id TEXT,
                pos_device_id TEXT,
                dining_option TEXT,
                tip DOUBLE NOT NULL DEFAULT 0.0,
                surcharge DOUBLE NOT NULL DEFAULT 0.0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS merchant (
                id TEXT PRIMARY KEY,
                business_name TEXT NOT NULL,
                email TEXT,
                country TEXT,
                currency TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                variant_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                in_stock INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP NOT NULL,
                PRIMARY KEY (variant_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                merchant_id TEXT NOT NULL,
                url TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'ENABLED',
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id TEXT PRIMARY KEY,
                store_id TEXT NOT NULL,
                pos_device_id TEXT NOT NULL,
                opened_at TIMESTAMP NOT NULL,
                closed_at TIMESTAMP,
                opened_by_employee TEXT NOT NULL,
                closed_by_employee TEXT,
                starting_cash DOUBLE NOT NULL DEFAULT 0.0,
                cash_payments DOUBLE NOT NULL DEFAULT 0.0,
                cash_refunds DOUBLE NOT NULL DEFAULT 0.0,
                paid_in DOUBLE NOT NULL DEFAULT 0.0,
                paid_out DOUBLE NOT NULL DEFAULT 0.0,
                expected_cash DOUBLE NOT NULL DEFAULT 0.0,
                actual_cash DOUBLE NOT NULL DEFAULT 0.0,
                gross_sales DOUBLE NOT NULL DEFAULT 0.0,
                refunds DOUBLE NOT NULL DEFAULT 0.0,
                discounts DOUBLE NOT NULL DEFAULT 0.0,
                net_sales DOUBLE NOT NULL DEFAULT 0.0,
                tip DOUBLE NOT NULL DEFAULT 0.0,
                surcharge DOUBLE NOT NULL DEFAULT 0.0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shift_taxes (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                name TEXT NOT NULL,
                rate DOUBLE NOT NULL,
                amount DOUBLE NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shift_payments (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                name TEXT NOT NULL,
                amount DOUBLE NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS shift_cash_movements (
                id TEXT PRIMARY KEY,
                shift_id TEXT NOT NULL,
                time TIMESTAMP NOT NULL,
                amount DOUBLE NOT NULL,
                note TEXT
            )
        """)

        # Junction tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employee_store (
                employee_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                PRIMARY KEY (employee_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS item_tax (
                item_id TEXT NOT NULL,
                tax_id TEXT NOT NULL,
                PRIMARY KEY (item_id, tax_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS item_modifier (
                item_id TEXT NOT NULL,
                modifier_id TEXT NOT NULL,
                PRIMARY KEY (item_id, modifier_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS modifier_store (
                modifier_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                PRIMARY KEY (modifier_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS tax_store (
                tax_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                PRIMARY KEY (tax_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS discount_store (
                discount_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                PRIMARY KEY (discount_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS payment_type_store (
                payment_type_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                PRIMARY KEY (payment_type_id, store_id)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS variant_store (
                variant_id TEXT NOT NULL,
                store_id TEXT NOT NULL,
                available_for_sale BOOLEAN NOT NULL DEFAULT TRUE,
                optimal_stock DOUBLE,
                low_stock_threshold DOUBLE,
                PRIMARY KEY (variant_id, store_id)
            )
        """)

        # Child tables
        conn.execute("""
            CREATE TABLE IF NOT EXISTS receipt_line_items (
                id TEXT PRIMARY KEY,
                receipt_id TEXT NOT NULL,
                item_id TEXT NOT NULL,
                variant_id TEXT,
                item_name TEXT NOT NULL,
                variant_name TEXT,
                sku TEXT,
                quantity DOUBLE NOT NULL,
                price DOUBLE NOT NULL,
                gross_total_money DOUBLE NOT NULL DEFAULT 0.0,
                total_money DOUBLE NOT NULL,
                cost DOUBLE,
                cost_total DOUBLE,
                line_note TEXT,
                total_discount DOUBLE NOT NULL DEFAULT 0.0
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS modifier_options (
                id TEXT PRIMARY KEY,
                modifier_id TEXT NOT NULL,
                name TEXT NOT NULL,
                price DOUBLE NOT NULL DEFAULT 0.0,
                position INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                deleted_at TIMESTAMP
            )
        """)

        # Metadata table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sync_metadata (
                resource_name TEXT PRIMARY KEY,
                last_sync_at TIMESTAMP NOT NULL,
                records_count INTEGER NOT NULL,
                sync_type TEXT NOT NULL
            )
        """)

        console.log(f"[green]✓[/green] Created DuckDB schema at {db_path}")

    finally:
        conn.close()


def create_indexes(db_path: str) -> None:
    """
    Create indexes on foreign keys and frequently queried columns.

    Args:
        db_path: Path to DuckDB database file

    Example:
        create_indexes("loyverse.duckdb")
    """
    conn = duckdb.connect(db_path)

    try:
        # Indexes on receipts table (most queried)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_customer ON receipts(customer_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_employee ON receipts(employee_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_store ON receipts(store_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(receipt_date)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_type ON receipts(receipt_type)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_created ON receipts(created_at)"
        )

        # Indexes on line items
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_line_items_receipt ON receipt_line_items(receipt_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_line_items_item ON receipt_line_items(item_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_line_items_variant ON receipt_line_items(variant_id)"
        )

        # Indexes on items
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_category ON items(category_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_supplier ON items(primary_supplier_id)"
        )

        # Indexes on variants
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_variants_item ON variants(item_id)"
        )

        # Indexes on POS devices
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_devices_store ON pos_devices(store_id)"
        )

        # Indexes on deleted_at for filtering active records
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_categories_deleted ON categories(deleted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_customers_deleted ON customers(deleted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_employees_deleted ON employees(deleted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_items_deleted ON items(deleted_at)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_receipts_deleted ON receipts(deleted_at)"
        )

        console.log(f"[green]✓[/green] Created indexes in {db_path}")

    finally:
        conn.close()
