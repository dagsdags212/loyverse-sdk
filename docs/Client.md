# Client

`LoyverseClient` is the entry point to the SDK. It holds your authentication,
manages a shared async HTTP connection, exposes every resource as an attribute,
and provides convenience methods for exporting data.

```python
from loyverse_sdk import LoyverseClient

client = LoyverseClient()
```

## Constructor

```python
LoyverseClient(
    api_token: str | None = None,
    base_url: str = <config default>,
    timeout: float = 15.0,
)
```

| Parameter | Default | Purpose |
|---|---|---|
| `api_token` | `None` | API key. When omitted, it is read from your config/env (see [[Configuration]]). |
| `base_url` | config default | The Loyverse API base URL. |
| `timeout` | `15.0` | Per-request timeout in seconds. |

Passing `api_token=None` (the default) is the common case — the client falls
back to `LOYVERSE_API_TOKEN` from the configuration written by `loyverse init`.
A missing token surfaces as an authentication failure on first use; see
[[Error-Handling]].

## Async lifecycle

The client is asynchronous and wraps a shared `httpx.AsyncClient`. Always
`await client.close()` when you're finished so the underlying connection pool is
released:

```python
import asyncio
from loyverse_sdk import LoyverseClient

async def main():
    client = LoyverseClient()
    try:
        response = await client.customers.list()
        print(len(response.items))
    finally:
        await client.close()

asyncio.run(main())
```

In the [[CLI]] the client's lifecycle is managed for you — each command opens and
closes a client around its work.

## Endpoints

Every resource is reachable as an attribute on the client (`client.customers`,
`client.receipts`, `client.pos_devices`, …). They all share the same
mixin-based CRUD + pagination interface — see [[Endpoints]] for the full list and
the call pattern, and [[Query-Models]] for the filters each one accepts.

The client also exposes a read-only `client.endpoints` mapping (name →
endpoint), which is what [[Endpoints]] iterates over to discover the available
resources.

## Export convenience methods

The client carries shortcuts so you can fetch and persist data without wiring up
the exporters yourself.

**DuckDB** (full details in [[DuckDB-Export]]):

| Method | Purpose |
|---|---|
| `await client.export_to_duckdb(...)` | Full export of all or selected resources |
| `await client.sync_to_duckdb(...)` | Incremental sync of changed records |
| `await client.export_resource_to_duckdb(...)` | Export a single resource |
| `client.init_duckdb_schema(...)` | Create the schema without exporting data |

**Flat files** (full details in [[Flat-File-Export]]):

| Method | Purpose |
|---|---|
| `client.export_to_csv(data, path)` | Write a list of models to CSV |
| `client.export_to_parquet(data, path)` | Write a list of models to Parquet |

Each method is documented in depth on its own page — this page only orients you
to what the client offers.

## See also

- [[Endpoints]] — the resources hanging off the client
- [[Configuration]] — where the token and base URL come from
- [[Error-Handling]] — authentication and network failures
- [[DuckDB-Export]] — the DuckDB convenience methods in detail
- [[Flat-File-Export]] — the CSV and Parquet methods in detail
