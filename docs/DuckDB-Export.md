# DuckDB Export

The SDK can export all of your Loyverse data into a local
[DuckDB](https://duckdb.org/) database — a relational warehouse you can query
with plain SQL or hand to the [[Analytics]] engine. No server, no infrastructure:
just a single `.duckdb` file on disk.

## Why DuckDB?

DuckDB is an analytics-focused embedded database, ideal for POS data:

- **Fast analytical queries** over large datasets
- **Local data warehousing** with no server to run
- **Familiar SQL** with a relational, foreign-keyed schema
- **Integration** with Python, R, and BI tools (Metabase, Superset, Tableau)
- **Efficient storage** via columnar compression

## Features

- 17 main resource tables (categories, items, receipts, etc.)
- Relational schema with foreign keys and indexes
- Junction tables for many-to-many relationships
- Child tables for nested data (line items, modifier options)
- Full and incremental exports with date-range filtering
- Streaming export for memory efficiency
- UPSERT semantics (`INSERT OR REPLACE`) to prevent duplicates
- Progress tracking via a callback

## Quick start

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()

    counts = await client.export_to_duckdb("loyverse.duckdb")
    print(f"Exported {sum(counts.values())} total records")
    # {'categories': 15, 'customers': 1250, 'receipts': 45000, ...}

    await client.close()

asyncio.run(main())
```

> The `export_to_duckdb()` method always performs a **full** export. The
> `loyverse export` CLI command, by contrast, syncs **incrementally by default**
> (fetching only records changed since the last run) — pass `--force` for a full
> re-export. See [[CLI]].

### Querying the warehouse

```python
import duckdb

conn = duckdb.connect("loyverse.duckdb")

result = conn.execute("""
    SELECT c.name,
           COUNT(DISTINCT r.id) AS receipt_count,
           SUM(r.total_amount)  AS total_spent
    FROM customers c
    JOIN receipts r ON c.id = r.customer_id
    WHERE r.receipt_type = 'SALE'
    GROUP BY c.id, c.name
    ORDER BY total_spent DESC
    LIMIT 10
""").fetchall()

conn.close()
```

For pre-built metrics over this same database, use [[Analytics]] instead of
hand-writing SQL.

## Export methods

### Full export with options

Export all or selected resources with filtering, batching, and progress:

```python
from datetime import datetime, timedelta

counts = await client.export_to_duckdb(
    db_path="loyverse.duckdb",
    resources=["receipts", "customers", "items"],        # specific resources
    created_at_min=datetime(2024, 1, 1),                  # start date
    created_at_max=datetime(2024, 12, 31),               # end date
    updated_at_min=datetime.now() - timedelta(days=7),   # updated after
    batch_size=1000,                                      # records per batch
    progress_callback=lambda res, curr, total: print(f"{res}: {curr}"),
    create_indexes=True,                                  # build indexes after load
)
# {'receipts': 5000, 'customers': 1200, 'items': 350}
```

### Single-resource export

Export one resource with fine-grained control:

```python
count = await client.export_resource_to_duckdb(
    resource_name="receipts",
    db_path="loyverse.duckdb",
    created_at_min=datetime.now() - timedelta(days=30),
)
print(f"Exported {count} receipts")
```

### Schema initialization

Create the schema without loading any data:

```python
# Empty database with full schema
client.init_duckdb_schema("loyverse.duckdb")

# Reset an existing database
client.init_duckdb_schema("loyverse.duckdb", drop_existing=True)
```

## Progress tracking

Pass a callback to follow long exports batch by batch:

```python
def progress(resource_name: str, current: int, total: int):
    print(f"Exporting {resource_name}: {current:,} records processed...")

counts = await client.export_to_duckdb("loyverse.duckdb", progress_callback=progress)
```

## Incremental updates

Export only records that changed in a window. Existing rows are updated and new
rows inserted (UPSERT), so repeated runs stay consistent:

```python
yesterday = datetime.now() - timedelta(days=1)
counts = await client.export_to_duckdb("loyverse.duckdb", updated_at_min=yesterday)
```

## Selective export

Limit the export to the resources you actually need:

```python
counts = await client.export_to_duckdb(
    "loyverse.duckdb",
    resources=["receipts", "customers", "items", "categories"],
)
```

## Database schema

**Main tables (17):** `categories`, `stores`, `suppliers`, `taxes`, `modifiers`,
`discounts`, `employees`, `customers`, `pos_devices`, `payment_types`, `items`,
`variants`, `receipts`, `inventory`, `merchant`, `webhooks`, `shifts`.

**Junction tables (8):** `employee_store`, `item_tax`, `item_modifier`,
`modifier_store`, `tax_store`, `discount_store`, `payment_type_store`,
`variant_store`.

**Child tables (5):** `receipt_line_items` (line items per receipt),
`modifier_options` (options within modifiers), and `shift_taxes`,
`shift_payments`, `shift_cash_movements` (per-shift detail).

**Metadata:** `sync_metadata` tracks export history and per-resource record
counts — this is what the CLI reads to decide what an incremental sync needs to
fetch.

## Example queries

**Daily revenue:**

```sql
SELECT DATE(receipt_date) AS date,
       COUNT(*)           AS receipt_count,
       SUM(total_amount)  AS revenue
FROM receipts
WHERE receipt_type = 'SALE'
  AND receipt_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(receipt_date)
ORDER BY date DESC;
```

**Best-selling items:**

```sql
SELECT i.name,
       SUM(l.quantity)            AS units_sold,
       SUM(l.quantity * l.price)  AS revenue
FROM items i
JOIN receipt_line_items l ON i.id = l.item_id
JOIN receipts r           ON l.receipt_id = r.id
WHERE r.receipt_type = 'SALE'
GROUP BY i.id, i.name
ORDER BY units_sold DESC
LIMIT 10;
```

**Customer lifetime value:**

```sql
SELECT c.name,
       c.total_visits,
       c.total_spent,
       c.total_spent / NULLIF(c.total_visits, 0) AS avg_per_visit
FROM customers c
WHERE c.total_visits > 0
ORDER BY c.total_spent DESC
LIMIT 20;
```

**Inventory by category:**

```sql
SELECT cat.name                  AS category,
       COUNT(DISTINCT i.id)      AS item_count,
       COUNT(DISTINCT v.id)      AS variant_count
FROM categories cat
LEFT JOIN items i    ON cat.id = i.category_id
LEFT JOIN variants v ON i.id = v.item_id
GROUP BY cat.id, cat.name
ORDER BY item_count DESC;
```

## Performance tips

1. **Batch size** — default is 1000 records per transaction. Raise it on
   capable machines: `export_to_duckdb("loyverse.duckdb", batch_size=5000)`.
2. **Indexes** — built automatically after load. Skip them for a faster initial
   import: `export_to_duckdb("loyverse.duckdb", create_indexes=False)`.
3. **Memory** — DuckDB runs with a 4 GB memory limit by default, comfortable for
   datasets with millions of records.
4. **Incremental updates** — export only changed records to minimize transfer:
   `export_to_duckdb("loyverse.duckdb", created_at_min=yesterday)`.

## Use cases

- **Business intelligence** — connect Metabase, Superset, or Tableau
- **Custom reports** — write SQL for specific business questions
- **Data science** — analyze sales, customer behavior, and inventory trends
- **Backup** — keep a local copy of all POS data
- **Data warehouse** — centralize data for cross-system analytics
- **Migration** — export data for moving to another system

## See also

- [[Analytics]] — pre-built metrics that read this warehouse
- [[CLI]] — `loyverse export` (incremental by default; `--force` for full)
- [[Flat-File-Export]] — write query results to CSV/Parquet instead
- [[Endpoints]] — the API resources that populate these tables
- [[Error-Handling]] — `ExportError` when an export or sync fails
