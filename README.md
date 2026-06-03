# Loyverse SDK

Asynchronous Python SDK for the [Loyverse API](https://developer.loyverse.com/docs/), a point-of-sale (POS) system for managing business transactions, inventory, and customer data.

## Overview

The SDK provides:
- **Async/await** interface using `httpx` for non-blocking API calls
- **Type-safe** request/response models using Pydantic
- **Automatic pagination** with cursor-based iteration via `iter_all()`
- **Full CRUD operations** for supported endpoints
- **CLI** — `loyverse` command for listing, creating, updating, deleting, and exporting resources
- **MCP server** — `loyverse-mcp` stdio server exposing 18 read-only tools to LLM clients (Claude Desktop, etc.)
- **Flat-file export** — write query results directly to CSV or Parquet files
- **DuckDB export** — local data warehousing with relational schema
- **16 endpoints**: categories, customers, discounts, devices, employees, inventory, items, merchant, modifiers, receipts, shifts, stores, suppliers, taxes, webhooks, variants

### Codebase Structure

**`src/loyverse_sdk/`** contains:
- `client.py` - Main `LoyverseClient` class with endpoint access
- `cli/` - Typer-based command-line interface with 8 subcommands
- `mcp/` - FastMCP server with 18 read-only tools for LLM clients
- `endpoints/` - Endpoint classes using mixin pattern for CRUD operations
- `models/` - Pydantic models for request/response validation
- `exporters/` - Flat-file exporter for CSV and Parquet output
- `db/` - DuckDB export pipeline for local data warehousing
- `auth.py` - Token-based authentication
- `core/` - Configuration, logging, and utilities

## Installation

```bash
# Core SDK (default)
uv pip install loyverse_sdk

# SDK + MCP server
uv pip install "loyverse_sdk[mcp]"

# Add as a project dependency (uv)
uv add loyverse_sdk

# With MCP extras
uv add "loyverse_sdk[mcp]"

# Install from GitHub
uv pip install git+https://github.com/dagsdags212/loyverse_sdk.git
```

## Setup

Configuration lives in `~/.loyverse`, so the CLI works from any directory:

```
~/.loyverse/
├── .loyverse.env       # API token and settings
└── db/
    └── loyverse.db     # exported DuckDB database(s)
```

The easiest way to set it up is the interactive command, which prompts for the
config directory (default `~/.loyverse`), your API token, and a database name
(default `loyverse.db`):

```bash
loyverse init

# Or supply any value as a flag to skip its prompt (handy for scripts):
loyverse init --config-dir ~/work/loyverse \  # -c  where config + databases live
              --api-token YOUR_TOKEN \         # -t  paste your Loyverse API key
              --db-path mydata.duckdb          # -d  database name (or a path)
```

`init` writes `<config-dir>/.loyverse.env`. If you pick a non-default config
directory, the location is recorded in a small pointer file
(`~/.config/loyverse/config_dir`) so every later command finds it automatically
— no environment variable to export. You can also edit the env file directly:

```env
LOYVERSE_API_TOKEN=your_api_token
LOYVERSE_DB_PATH=loyverse.db                 # optional, defaults to loyverse.db
```

`LOYVERSE_DB_PATH` (and the `--db-path` argument) accept either a bare name —
stored under `<config-dir>/db/` — or an explicit path (absolute or containing a
directory), which is used as-is.

The config directory is resolved in this order: the `LOYVERSE_CONFIG_DIR`
environment variable, then the pointer file written by `init`, then the default
`~/.loyverse`. Environment variables set in your shell still take precedence
over values in the env file.

> **Migrating from an older version:** if a `.env` exists in your working
> directory and `~/.loyverse` does not yet exist, its values are copied into
> `~/.loyverse/.loyverse.env` automatically on first run.

## CLI Usage

The `loyverse` CLI provides quick terminal access to the Loyverse API without writing Python code. The database path (`--db-path`/`-d`) is optional for `export` and `analytics` commands — it defaults to the `LOYVERSE_DB_PATH` env var or `loyverse.db`.

```bash
# List resources with output formats
loyverse list customers --limit 10
loyverse list receipts --created-at-min 2024-01-01 --format table
loyverse list customers --format csv > customers.csv

# Create resources
loyverse create categories --name "Drinks" --color GREEN
loyverse create customers --name "Jane" --email jane@acme.com

# Update and delete
loyverse update categories <ID> --name "New Name"
loyverse delete categories <ID> --yes

# Retrieve a single record
loyverse get customers <ID>
loyverse get receipts <ID> --format table

# Export to DuckDB for analytics (incremental by default; use --force for full)
loyverse export
loyverse export --force
loyverse export mydata.duckdb --resource receipts
loyverse export --created-at-min 2024-01-01

# Analytics queries (no --db-path needed if LOYVERSE_DB_PATH is set)
loyverse analytics revenue --days 30
loyverse analytics revenue --by-month --days 365
loyverse analytics products --top-n 10
loyverse analytics customers --rfm
loyverse analytics time-series --monthly

# List available endpoints
loyverse endpoints
```

## MCP Server

The `loyverse-mcp` server exposes your Loyverse data as MCP tools, letting LLM clients like [Claude Desktop](https://claude.ai/download) query your POS data in natural language — no code required.

### Installation

The MCP server requires the `mcp` extra:

```bash
# Global install
pip install "loyverse_sdk[mcp]"

# uv-managed project
uv add "loyverse_sdk[mcp]"
```

### MCP Client Setup

The `loyverse-mcp` command communicates over stdio. How you reference it depends on your setup:

**Globally installed** — the script is on your PATH:

```json
"command": "loyverse-mcp"
```

**uv-managed project** — use `uv run` (works from anywhere inside the project):

```json
"command": "uv",
"args": ["run", "loyverse-mcp"]
```

**uv-managed project (explicit venv path)** — point directly at the virtualenv:

```json
"command": "/path/to/project/.venv/bin/loyverse-mcp"
```

### Claude Desktop

Add the server to `~/.config/claude/claude_desktop_config.json` (macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "loyverse": {
      "command": "uv",
      "args": ["run", "loyverse-mcp"],
      "env": {
        "LOYVERSE_API_TOKEN": "your_api_token_here",
        "LOYVERSE_DB_PATH": "loyverse.db"
      }
    }
  }
}
```

If you installed globally (`pip install`), replace the command with just `"loyverse-mcp"` and omit `args`.

Restart Claude Desktop. You should see a hammer icon (🔨) in the chat toolbar indicating tools are available.

### Available Tools

The server registers **18 read-only tools**:

| Tool | Description |
|------|-------------|
| `loyverse_list_receipts` | List sales receipts with date, store, and receipt-number filters |
| `loyverse_get_receipt` | Retrieve a single receipt by UUID |
| `loyverse_list_items` | List catalog items, filterable by store, category, or IDs |
| `loyverse_get_item` | Retrieve a single item by UUID |
| `loyverse_list_customers` | List customers, searchable by email or IDs |
| `loyverse_get_customer` | Retrieve a single customer by UUID |
| `loyverse_list_categories` | List all item categories |
| `loyverse_get_category` | Retrieve a single category by UUID |
| `loyverse_list_employees` | List all employees |
| `loyverse_get_employee` | Retrieve a single employee by UUID |
| `loyverse_list_shifts` | List employee work shifts |
| `loyverse_get_shift` | Retrieve a single shift by UUID |
| `loyverse_list_stores` | List all store locations |
| `loyverse_get_store` | Retrieve a single store by UUID |
| `loyverse_list_inventory` | List inventory levels, filterable by store or variant |
| `loyverse_list_payment_types` | List configured payment methods |
| `loyverse_get_payment_type` | Retrieve a single payment type by ID |
| `loyverse_get_merchant` | Retrieve the merchant account profile |

All list tools support cursor-based pagination via `limit` and `cursor` parameters, and most support date-range filtering (`created_at_min`, `created_at_max`, `updated_at_min`, `updated_at_max`).

### Example Prompts

Once connected, you can ask Claude things like:

```
"Show me all receipts from this week"
"Which items are in the Drinks category?"
"How many customers do we have?"
"What payment methods are configured?"
"List all stores and their details"
"Find receipts from store <UUID> in January 2024"
"Get the details for receipt R-1042"
"Show me the current inventory for store <UUID>"
```

Claude will call the appropriate tools, paginate through results as needed, and summarize the data in plain language.

### Running Standalone

You can also run the server directly outside of Claude Desktop (for example, to connect it to another MCP client or to test it):

```bash
LOYVERSE_API_TOKEN=your_token loyverse-mcp
```

To enable analytics tools, set the database path:

```bash
LOYVERSE_API_TOKEN=your_token LOYVERSE_DB_PATH=loyverse.db loyverse-mcp
```

Or as a Python module:

```bash
LOYVERSE_API_TOKEN=your_token python -m loyverse_sdk.mcp
```

The server communicates over stdio using the MCP protocol.

---

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

## Flat-File Export

The SDK can write query results directly to CSV and Parquet files — no database needed. Combine any endpoint query with `client.export_to_csv()` or `client.export_to_parquet()` to save data locally for spreadsheet analysis, BI tools, or data pipelines.

### Features

- ✅ **CSV export** — comma-delimited with headers, double-quote quoting, UTF-8 encoding
- ✅ **Parquet export** — columnar format with Snappy compression, preserves column types
- ✅ **Zero configuration** — uses Polars (already a dependency), no extra installs
- ✅ **Any Pydantic model** — works with any list of model instances from any endpoint
- ✅ **Client convenience** — `client.export_to_csv(data, path)` and `client.export_to_parquet(data, path)`
- ✅ **Standalone functions** — `from loyverse_sdk.exporters import export_csv, export_parquet`

### Quick Start

**Fetch customers between a date range and export to CSV:**

```python
import asyncio
from datetime import datetime
from loyverse_sdk import LoyverseClient
from loyverse_sdk.models import CustomerListQuery

async def main():
    client = LoyverseClient()

    # Filter customers created between two dates
    query = CustomerListQuery(
        created_at_min=datetime(2024, 1, 1),
        created_at_max=datetime(2024, 6, 30),
    )

    # Fetch all matching customers via pagination
    customers = []
    async for customer in client.customers.iter_all(query):
        customers.append(customer)

    print(f"Found {len(customers)} customers in H1 2024")

    # Write results to disk with a single call
    client.export_to_csv(customers, "customers_h1_2024.csv")
    print("Exported to customers_h1_2024.csv")

    await client.close()

asyncio.run(main())
```

**Export all items to Parquet for efficient storage:**

```python
# Stream every item in the catalog via pagination
items = []
async for item in client.items.iter_all(limit=250):
    items.append(item)

# Parquet preserves types and compresses automatically
client.export_to_parquet(items, "items_catalog.parquet")
print(f"Exported {len(items)} items to Parquet")
```

### Export Methods

#### 1. Client Convenience Methods

The simplest path — call directly on your `LoyverseClient` instance:

```python
# Export to CSV
client.export_to_csv(data, "output.csv")

# Export to Parquet
client.export_to_parquet(data, "output.parquet")
```

Both methods accept a list of Pydantic model instances and a file path (`str` or `pathlib.Path`). Polars is imported lazily so flat-file dependencies are only loaded when you actually use them.

#### 2. Standalone Module Functions

Use the exporters directly without a client instance:

```python
from loyverse_sdk.exporters import export_csv, export_parquet

# Export from any script that has model instances
export_csv(models, "data.csv")
export_parquet(models, "data.parquet")
```

#### 3. FlatFileExporter Class

For full control, instantiate the exporter directly:

```python
from loyverse_sdk.exporters import FlatFileExporter

exporter = FlatFileExporter()
exporter.export_csv(models, "output.csv")
exporter.export_parquet(models, "output.parquet")
```

### Filtering Before Export

Combine query models with client-side filtering for precise exports:

```python
from datetime import datetime, timedelta
from loyverse_sdk.models import ReceiptListQuery, CustomerListQuery

# Receipts from last 7 days, sorted newest first
last_week = datetime.now() - timedelta(days=7)
query = ReceiptListQuery(
    created_at_min=last_week,
    order="created_at_desc",
    limit=250,
)

receipts = []
async for receipt in client.receipts.iter_all(query):
    receipts.append(receipt)

client.export_to_csv(receipts, "receipts_last_week.csv")

# Customers by email domain (client-side filter after API query)
query = CustomerListQuery(limit=250)
response = await client.customers.list(query)

gmail_customers = [
    c for c in response.items
    if c.email and c.email.endswith("@gmail.com")
]

client.export_to_csv(gmail_customers, "gmail_customers.csv")
```

### Comparison: Flat-File vs DuckDB Export

| Feature | Flat-File (CSV/Parquet) | DuckDB Export |
|---------|------------------------|---------------|
| Setup | Zero — works instantly | Requires `duckdb` import |
| Output | Standalone files (.csv, .parquet) | Database file (.duckdb) |
| Schema | Column headers from model fields | Relational with FK constraints |
| Use case | Quick exports, spreadsheet analysis | Analytics, SQL queries, BI tools |
| Performance | File I/O (good for batches) | Columnar storage + indexes |
| Incremental | Manual (overwrite files) | UPSERT via date range filtering |

Both exporters work with the same Pydantic model instances — you can query once and export to both formats:

```python
# Query once
response = await client.customers.list(query)

# Export to both formats from the same data
client.export_to_csv(response.items, "customers.csv")
client.export_to_parquet(response.items, "customers.parquet")

# Also export to DuckDB for SQL analytics
await client.export_to_duckdb("loyverse.duckdb", resources=["customers"])
```

### Complete Example

See `examples/export_flat_files.py` for working examples including:
- Customers filtered by date range → CSV
- All items via pagination → Parquet
- Latest receipts → CSV
- Client-side filtering patterns

```bash
python examples/export_flat_files.py
```

## DuckDB Export

The SDK includes powerful export functionality to save all your Loyverse data to a local DuckDB database for analytics, reporting, and data warehousing.

The `loyverse export` CLI command syncs **incrementally by default** — fetching only records updated since the last export. Use `--force`/`-f` for a full re-export. The `export_to_duckdb()` SDK method always performs a full export.

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

See the example scripts for end-to-end workflows:

- `examples/export_flat_files.py` — Flat-file export (CSV + Parquet) with date-range filtering and client-side filtering
- `examples/duckdb_export.py` — DuckDB export with full/selective exports, date ranges, progress tracking, and incremental updates

```bash
python examples/export_flat_files.py
python examples/duckdb_export.py
```
