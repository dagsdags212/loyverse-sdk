# Flat-File Export

When you just need data in a file — for a spreadsheet, a BI tool, or a data
pipeline — the SDK can write query results straight to **CSV** or **Parquet**
without standing up a database. Any list of Pydantic model instances from any
endpoint can be exported in a single call (see [[Models]] and [[Endpoints]]).

## Features

- **CSV** — comma-delimited, headers from model fields, UTF-8 encoded
- **Parquet** — columnar, Snappy-compressed, type-preserving
- **Zero configuration** — uses Polars (already a dependency); nothing extra to install
- **Any model** — works with any list of model instances from any endpoint

## Client convenience methods

The simplest path is to call directly on your [[Client]]:

```python
client.export_to_csv(data, "output.csv")
client.export_to_parquet(data, "output.parquet")
```

Both accept a list of Pydantic model instances and a file path (`str` or
`pathlib.Path`). Polars is imported lazily, so the flat-file dependency only loads
when you actually export.

## Fetch, then export

Combine a query model ([[Query-Models]]) with `iter_all()` to pull a result set
and write it to disk.

**Customers in a date range → CSV:**

```python
import asyncio
from datetime import datetime
from loyverse_sdk import LoyverseClient
from loyverse_sdk.models import CustomerListQuery

async def main():
    client = LoyverseClient()

    query = CustomerListQuery(
        created_at_min=datetime(2024, 1, 1),
        created_at_max=datetime(2024, 6, 30),
    )

    customers = [c async for c in client.customers.iter_all(query)]
    print(f"Found {len(customers)} customers in H1 2024")

    client.export_to_csv(customers, "customers_h1_2024.csv")

    await client.close()

asyncio.run(main())
```

**Entire item catalog → Parquet:**

```python
items = [i async for i in client.items.iter_all()]
client.export_to_parquet(items, "items_catalog.parquet")
print(f"Exported {len(items)} items to Parquet")
```

## Standalone functions

You don't need a client to export — the module functions work with any list of
models you already have:

```python
from loyverse_sdk.exporters import export_csv, export_parquet

export_csv(models, "data.csv")
export_parquet(models, "data.parquet")
```

## The FlatFileExporter class

For full control, instantiate the exporter directly:

```python
from loyverse_sdk.exporters import FlatFileExporter

exporter = FlatFileExporter()
exporter.export_csv(models, "output.csv")
exporter.export_parquet(models, "output.parquet")
```

## Filtering before export

Push as much filtering as possible into the query ([[Query-Models]]), then refine
client-side for anything the API can't express:

```python
from datetime import datetime, timedelta
from loyverse_sdk.models import ReceiptListQuery, CustomerListQuery

# Receipts from the last 7 days, newest first
last_week = datetime.now() - timedelta(days=7)
query = ReceiptListQuery(created_at_min=last_week, sort_order="desc")
receipts = [r async for r in client.receipts.iter_all(query)]
client.export_to_csv(receipts, "receipts_last_week.csv")

# Customers by email domain (client-side filter after the API query)
response = await client.customers.list(CustomerListQuery(limit=250))
gmail = [c for c in response.items if c.email and c.email.endswith("@gmail.com")]
client.export_to_csv(gmail, "gmail_customers.csv")
```

## Flat-file vs. DuckDB

Both exporters consume the same model instances — you can query once and write to
either (or both).

| Feature | Flat-file (CSV/Parquet) | [[DuckDB-Export]] |
|---|---|---|
| Setup | Zero — works instantly | Requires `duckdb` |
| Output | Standalone files (`.csv`, `.parquet`) | Database file (`.duckdb`) |
| Schema | Column headers from model fields | Relational, with FK constraints |
| Use case | Quick exports, spreadsheets | SQL analytics, BI tools |
| Performance | File I/O (good for batches) | Columnar storage + indexes |
| Incremental | Manual (overwrite files) | UPSERT via date-range filtering |

```python
# Query once, export everywhere
response = await client.customers.list(query)

client.export_to_csv(response.items, "customers.csv")
client.export_to_parquet(response.items, "customers.parquet")
await client.export_to_duckdb("loyverse.duckdb", resources=["customers"])
```

## See also

- [[DuckDB-Export]] — relational warehouse for SQL analytics
- [[Endpoints]] — fetch the data you want to export
- [[Query-Models]] — filter and paginate before exporting
- [[Models]] — the model instances the exporters accept
- [[Analytics]] — computed metrics instead of raw records
