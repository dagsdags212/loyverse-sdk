# Loyverse SDK

Asynchronous Python SDK for the [Loyverse API](https://developer.loyverse.com/docs/), a point-of-sale (POS) system for managing business transactions, inventory, and customer data.

## Overview

The SDK provides:
- **Async/await** interface using `httpx` for non-blocking API calls
- **Type-safe** request/response models using Pydantic
- **Automatic pagination** with cursor-based iteration via `iter_all()`
- **Full CRUD operations** for supported endpoints
- **16 endpoints**: categories, customers, discounts, devices, employees, inventory, items, merchant, modifiers, receipts, shifts, stores, suppliers, taxes, webhooks, variants

### Codebase Structure

**`src/loyverse_sdk/`** contains:
- `client.py` - Main `LoyverseClient` class with endpoint access
- `endpoints/` - Endpoint classes using mixin pattern for CRUD operations
- `models/` - Pydantic models for request/response validation
- `auth.py` - Token-based authentication
- `core/` - Configuration, logging, and utilities

## Installation

```bash
# Install from PyPI - recommended (default)
uv pip install loyverse_sdk

# Add as a project dependency - recommended for uv projects
up add loyverse_sdk 

# Install from GitHub
uv pip install git+https://github.com/dagsdags212/loyverse_sdk.git
```

## Setup

Set your API token as an environment variable:

```bash
export LOYVERSE_API_TOKEN=your_api_token
```

Or create a `.env` file in your project root:

```env
LOYVERSE_API_TOKEN=your_api_token
```

## Quick Start

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()

    # List customers (uses default limit from config)
    response = await client.customers.list()
    print(f"Found {len(response.items)} customers")

    await client.close()

asyncio.run(main())
```

## Usage Examples

### Customers Endpoint

The customers endpoint manages customer data from your POS system.

**List customers with a query model:**

```python
from loyverse_sdk.models import CustomerListQuery

# Use a query model to filter and paginate
query = CustomerListQuery(limit=50, email="jane@example.com")
response = await client.customers.list(query)

for customer in response.items:
    print(f"{customer.name} - {customer.email}")

# Next page using cursor from response
if response.next_cursor:
    next_query = CustomerListQuery(cursor=response.next_cursor, limit=50)
    next_page = await client.customers.list(next_query)
```

**Retrieve a single customer:**

```python
customer = await client.customers.retrieve(id="customer-uuid-here")
print(customer.name)
print(customer.phone_number)
print(customer.address)
```

**Create a new customer:**

```python
new_customer = await client.customers.create({
    "name": "Jane Smith",
    "email": "jane@example.com",
    "phone_number": "+1234567890",
    "address": "123 Main St",
    "city": "San Francisco",
    "postal_code": "94102",
    "customer_code": "CUST001"
})

print(f"Created customer: {new_customer.id}")
```

**Update an existing customer:**

```python
updated = await client.customers.update(
    id=customer.id,
    payload={"email": "newemail@example.com", "note": "VIP customer"}
)

print(f"Updated {updated.name}")
```

**Delete a customer:**

```python
result = await client.customers.delete(id=customer.id)
print(result)  # {'deleted_object_ids': ['customer-uuid']}
```

**Iterate through all customers:**

```python
async for customer in client.customers.iter_all():
    print(f"{customer.name} - Last visit: {customer.last_visit}")
```

**Filter customers by date and attributes using a query model:**

```python
from datetime import datetime, timedelta
from loyverse_sdk.models import CustomerListQuery

# Get customers created in the last 30 days
start_date = datetime.now() - timedelta(days=30)
query = CustomerListQuery(created_at_min=start_date)

async for customer in client.customers.iter_all(query):
    tenure = customer.tenure()
    print(f"{customer.name} - Customer for {tenure.days} days")

# Filter by multiple criteria
query = CustomerListQuery(
    email="john@example.com",
    created_at_min=datetime(2024, 1, 1),
    created_at_max=datetime(2024, 12, 31),
)
response = await client.customers.list(query)
```

### Other Endpoints

All endpoints follow the same pattern. Available endpoints:

```python
client.categories   # Item categories
client.customers    # Customer records
client.discounts    # Discount rules
client.devices      # POS devices
client.employees    # Staff members
client.inventory    # Stock levels
client.items        # Inventory items
client.merchant     # Merchant info
client.modifiers    # Item modifiers
client.receipts     # Transaction receipts
client.shifts       # Employee shifts
client.stores       # Store locations
client.suppliers    # Supplier records
client.taxes        # Tax configurations
client.variants     # Item variants
client.webhooks     # Webhook subscriptions
```

Each endpoint supports operations based on the [Loyverse API capabilities](https://developer.loyverse.com/docs/).

## Query Models

All list endpoints accept an optional query model to filter, paginate, and sort results. Query models are Pydantic models with typed fields — your IDE will autocomplete available filters.

**Import from `loyverse_sdk.models`:**

```python
from loyverse_sdk.models import (
    CategoryListQuery,
    CustomerListQuery,
    DiscountListQuery,
    EmployeeListQuery,
    InventoryListQuery,
    ItemListQuery,
    ModifierListQuery,
    PaymentTypeListQuery,
    PosDeviceListQuery,
    ReceiptListQuery,
    StoreListQuery,
    SupplierListQuery,
    TaxListQuery,
    WebhookListQuery,
    VariantListQuery,
)
```

**Common pattern for all list/iter_all calls:**

```python
# Pass query model with filters
query = FooListQuery(limit=50, some_filter="value")
response = await client.foo.list(query)

# Or iterate with a query model
async for item in client.foo.iter_all(FooListQuery(some_filter="value")):
    print(item.name)

# Omit query to use defaults (limit=250, no filters)
response = await client.foo.list()
```

**Pagination:**

```python
# Use cursor from previous response to get next page
next_query = FooListQuery(cursor=response.next_cursor, limit=50)
next_page = await client.foo.list(next_query)
```

**Date range filtering:**

```python
from datetime import datetime, timedelta

# Records updated in the last 7 days
recent = datetime.now() - timedelta(days=7)
query = FooListQuery(updated_at_min=recent)

async for item in client.foo.iter_all(query):
    print(item.name)
```

**Endpoint-specific filters:**

Each query model exposes the filters supported by its endpoint. Examples:

```python
# Inventory: filter by store and variants
query = InventoryListQuery(store_ids="store-1,store-2", variant_ids="var-1,var-2")
response = await client.inventory.list(query)

# Receipts: filter by store, date range, and sort order
query = ReceiptListQuery(
    store_id="store-abc",
    created_at_min=datetime(2024, 1, 1),
    created_at_max=datetime(2024, 12, 31),
    order="created_at_desc",
)
async for receipt in client.receipts.iter_all(query):
    print(receipt.id)

# Items: filter by category and include deleted items
query = ItemListQuery(category_id="cat-123", show_deleted=True)
async for item in client.items.iter_all(query):
    print(item.name)

# Webhooks: filter by type and status
from loyverse_sdk.models import WebhookListQuery, WebhookType, WebhookStatus

query = WebhookListQuery(type=WebhookType.RECEIPTS_UPDATE, status=WebhookStatus.ENABLED)
async for webhook in client.webhooks.iter_all(query):
    print(webhook.url)
```

**Validation:** Query models validate their inputs — e.g., `created_at_min` must be less than or equal to `created_at_max`, and `limit` must be between 1 and 250. Invalid queries raise `ValidationError` with a descriptive message.

## DuckDB Export

The SDK includes powerful export functionality to save all your Loyverse data to a local DuckDB database for analytics, reporting, and data warehousing.

### Why DuckDB?

DuckDB is an analytics-focused database perfect for:
- **Fast analytical queries** on large datasets
- **Local data warehousing** without server infrastructure
- **SQL analytics** with familiar syntax
- **Integration** with Python, R, and BI tools
- **Efficient storage** with columnar compression

### Features

- ✅ **15 main resource tables** (categories, items, receipts, etc.)
- ✅ **Relational schema** with foreign keys and indexes
- ✅ **Junction tables** for many-to-many relationships
- ✅ **Child tables** for nested data (line items, modifier options)
- ✅ **Full and incremental exports** with date range filtering
- ✅ **Streaming export** for memory efficiency
- ✅ **UPSERT support** (INSERT OR REPLACE) to prevent duplicates
- ✅ **Progress tracking** with callback support

### Quick Start

**Full export:**

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()

    # Export all data to DuckDB
    counts = await client.export_to_duckdb("loyverse.duckdb")

    print(f"Exported {sum(counts.values())} total records")
    # Output: {'categories': 15, 'customers': 1250, 'receipts': 45000, ...}

    await client.close()

asyncio.run(main())
```

**Query exported data:**

```python
import duckdb

conn = duckdb.connect("loyverse.duckdb")

# Top 10 customers by total spent
result = conn.execute("""
    SELECT
        c.name,
        COUNT(DISTINCT r.id) as receipt_count,
        SUM(r.total_amount) as total_spent
    FROM customers c
    JOIN receipts r ON c.id = r.customer_id
    WHERE r.receipt_type = 'SALE'
    GROUP BY c.id, c.name
    ORDER BY total_spent DESC
    LIMIT 10
""").fetchall()

conn.close()
```

### Export Methods

#### 1. Full Export with Options

Export all or selected resources with comprehensive filtering:

```python
from datetime import datetime, timedelta

client = LoyverseClient()

# Export with all options
counts = await client.export_to_duckdb(
    db_path="loyverse.duckdb",
    resources=["receipts", "customers", "items"],  # Optional: specific resources
    created_at_min=datetime(2024, 1, 1),           # Optional: start date
    created_at_max=datetime(2024, 12, 31),         # Optional: end date
    updated_at_min=datetime.now() - timedelta(days=7),  # Optional: updated after
    batch_size=1000,                                # Optional: records per batch
    progress_callback=lambda res, curr, total: print(f"{res}: {curr}"),  # Optional
    create_indexes=True                             # Optional: create indexes after
)

print(f"Exported: {counts}")
# Returns: {'receipts': 5000, 'customers': 1200, 'items': 350}

await client.close()
```

#### 2. Single Resource Export

Export one resource with fine-grained control:

```python
client = LoyverseClient()

# Export only receipts from last 30 days
count = await client.export_resource_to_duckdb(
    resource_name="receipts",
    db_path="loyverse.duckdb",
    created_at_min=datetime.now() - timedelta(days=30)
)

print(f"Exported {count} receipts")

await client.close()
```

#### 3. Schema Initialization

Create database schema without exporting data:

```python
client = LoyverseClient()

# Initialize empty database with schema
client.init_duckdb_schema("loyverse.duckdb")

# Or reset existing database
client.init_duckdb_schema("loyverse.duckdb", drop_existing=True)
```

### Advanced Usage

**Progress tracking:**

```python
def progress_callback(resource_name: str, current: int, total: int):
    """Called for each batch of records."""
    print(f"Exporting {resource_name}: {current:,} records processed...")

counts = await client.export_to_duckdb(
    "loyverse.duckdb",
    progress_callback=progress_callback
)
```

**Incremental updates:**

```python
# Export only records updated in last 24 hours
yesterday = datetime.now() - timedelta(days=1)

counts = await client.export_to_duckdb(
    "loyverse.duckdb",
    updated_at_min=yesterday
)

# UPSERT semantics: existing records are updated, new ones inserted
```

**Selective export:**

```python
# Export only what you need
counts = await client.export_to_duckdb(
    "loyverse.duckdb",
    resources=[
        "receipts",      # Transaction data
        "customers",     # Customer profiles
        "items",         # Product catalog
        "categories"     # Item categories
    ]
)
```

### Database Schema

The exported database includes:

**Main Tables (15):**
- `categories` - Item categories
- `stores` - Store locations
- `suppliers` - Supplier records
- `taxes` - Tax configurations
- `modifiers` - Item modifiers
- `discounts` - Discount rules
- `employees` - Staff members
- `customers` - Customer records
- `pos_devices` - POS devices
- `payment_types` - Payment methods
- `items` - Inventory items
- `variants` - Item variants
- `receipts` - Transaction receipts
- `inventory` - Stock levels
- `merchant` - Merchant info

**Junction Tables (8):**
- `employee_store` - Employee-to-store assignments
- `item_tax` - Item-to-tax relationships
- `item_modifier` - Item-to-modifier relationships
- `modifier_store` - Modifier-to-store assignments
- `tax_store` - Tax-to-store assignments
- `discount_store` - Discount-to-store assignments
- `payment_type_store` - Payment type availability by store
- `variant_store` - Variant inventory by store

**Child Tables (2):**
- `receipt_line_items` - Individual line items per receipt
- `modifier_options` - Options within modifiers

**Metadata:**
- `sync_metadata` - Tracks export history and record counts

### Example Queries

**Daily revenue:**

```sql
SELECT
    DATE(receipt_date) as date,
    COUNT(*) as receipt_count,
    SUM(total_amount) as revenue
FROM receipts
WHERE receipt_type = 'SALE'
  AND receipt_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(receipt_date)
ORDER BY date DESC;
```

**Best-selling items:**

```sql
SELECT
    i.name,
    SUM(l.quantity) as units_sold,
    SUM(l.quantity * l.price) as revenue
FROM items i
JOIN receipt_line_items l ON i.id = l.item_id
JOIN receipts r ON l.receipt_id = r.id
WHERE r.receipt_type = 'SALE'
GROUP BY i.id, i.name
ORDER BY units_sold DESC
LIMIT 10;
```

**Customer lifetime value:**

```sql
SELECT
    c.name,
    c.total_visits,
    c.total_spent,
    c.total_spent / NULLIF(c.total_visits, 0) as avg_per_visit
FROM customers c
WHERE c.total_visits > 0
ORDER BY c.total_spent DESC
LIMIT 20;
```

**Inventory by category:**

```sql
SELECT
    cat.name as category,
    COUNT(DISTINCT i.id) as item_count,
    COUNT(DISTINCT v.id) as variant_count
FROM categories cat
LEFT JOIN items i ON cat.id = i.category_id
LEFT JOIN variants v ON i.id = v.item_id
GROUP BY cat.id, cat.name
ORDER BY item_count DESC;
```

### Performance Tips

1. **Batch size**: Default is 1000 records per transaction. Increase for faster exports on powerful machines:
   ```python
   counts = await client.export_to_duckdb("loyverse.duckdb", batch_size=5000)
   ```

2. **Indexes**: Created automatically after export. Disable for faster initial load:
   ```python
   counts = await client.export_to_duckdb("loyverse.duckdb", create_indexes=False)
   ```

3. **Memory**: DuckDB is configured with 4GB memory limit by default. Efficient for datasets with millions of records.

4. **Incremental updates**: Export only changed records to minimize transfer time:
   ```python
   # Daily sync: export only yesterday's data
   yesterday = datetime.now() - timedelta(days=1)
   counts = await client.export_to_duckdb("loyverse.duckdb", created_at_min=yesterday)
   ```

### Use Cases

- **Business Intelligence**: Connect DuckDB to Metabase, Superset, or Tableau
- **Custom Reports**: Write SQL queries for specific business questions
- **Data Science**: Analyze sales patterns, customer behavior, inventory trends
- **Backup**: Maintain local copy of all POS data
- **Data Warehouse**: Centralize data for cross-system analytics
- **Migration**: Export data for migration to other systems

### Complete Example

See `examples/duckdb_export.py` for comprehensive examples including:
- Full and selective exports
- Date range filtering
- Progress tracking
- Querying exported data
- Incremental updates

```bash
python examples/duckdb_export.py
```
