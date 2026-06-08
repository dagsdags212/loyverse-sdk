# Query Models

Every list endpoint accepts an optional **query model** — a Pydantic object that
filters, paginates, and validates a list request before any HTTP call is made.
Because the fields are typed, your IDE autocompletes the filters available for
each resource, and invalid input is caught up front rather than by the API.

Query models are used with `list()` and `iter_all()` on any endpoint (see
[[Endpoints]]); the records they return are documented in [[Models]].

## Importing

Every query model lives in `loyverse_sdk.models`:

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
    ShiftListQuery,
    StoreListQuery,
    SupplierListQuery,
    TaxListQuery,
    VariantListQuery,
    WebhookListQuery,
)
```

## The common pattern

All query models share the same shape, so once you know one you know them all:

```python
# Pass a query model with filters
query = FooListQuery(limit=50, some_filter="value")
response = await client.foo.list(query)

# Or stream every matching record with iter_all()
async for item in client.foo.iter_all(FooListQuery(some_filter="value")):
    print(item.name)

# Omit the query entirely to use defaults (limit from config, no filters)
response = await client.foo.list()
```

## Pagination

The Loyverse API is cursor-paginated. A `list()` response exposes a
`next_cursor`; pass it back via `cursor` to fetch the following page:

```python
query = CustomerListQuery(limit=50)
response = await client.customers.list(query)

if response.next_cursor:
    next_page = await client.customers.list(
        CustomerListQuery(cursor=response.next_cursor, limit=50)
    )
```

If you don't want to manage cursors yourself, use `iter_all()` — it follows the
cursor automatically and yields one record at a time. See
[[Endpoints]] for the difference between streaming and paging.

## Date-range filtering

Every query model inherits four date filters from the shared base. Pass `datetime`
objects; the SDK serializes them to the format the API expects:

```python
from datetime import datetime, timedelta

# Records updated in the last 7 days
recent = datetime.now() - timedelta(days=7)
query = CustomerListQuery(updated_at_min=recent)

async for customer in client.customers.iter_all(query):
    print(customer.name)
```

| Field | Filters by |
|---|---|
| `created_at_min` / `created_at_max` | creation timestamp |
| `updated_at_min` / `updated_at_max` | last-update timestamp |

## Endpoint-specific filters

Each query model adds the filters its endpoint supports on top of the common
fields:

```python
# Inventory: restrict to specific stores and variants (comma-separated IDs)
query = InventoryListQuery(store_ids="store-1,store-2", variant_ids="var-1,var-2")
response = await client.inventory.list(query)

# Receipts: filter by store, date range, and sort order
query = ReceiptListQuery(
    store_id="store-abc",
    created_at_min=datetime(2024, 1, 1),
    created_at_max=datetime(2024, 12, 31),
    sort_order="desc",
)
async for receipt in client.receipts.iter_all(query):
    print(receipt.receipt_number)

# Items: filter by category and include soft-deleted records
query = ItemListQuery(category_id="cat-123", show_deleted=True)
async for item in client.items.iter_all(query):
    print(item.name)

# Webhooks: filter by type and status using the provided enums
from loyverse_sdk.models import WebhookListQuery, WebhookType, WebhookStatus

query = WebhookListQuery(
    type=WebhookType.RECEIPTS_UPDATE,
    status=WebhookStatus.ENABLED,
)
async for webhook in client.webhooks.iter_all(query):
    print(webhook.url)
```

`WebhookType` covers `INVENTORY_LEVELS_UPDATE`, `ITEMS_UPDATE`,
`CUSTOMERS_UPDATE`, `RECEIPTS_UPDATE`, and `SHIFTS_CREATE`; `WebhookStatus` is
`ENABLED` or `DISABLED`.

## Validation

Query models validate their inputs the moment you construct them. Two rules apply
to every model:

- `created_at_min` must be `<= created_at_max` (and likewise for `updated_at_*`)
- `limit` must be between **1 and 250**

Breaking a rule raises a `ValidationError` with a descriptive message and the
offending field — no request is sent. See [[Error-Handling]] for how to catch it:

```python
from loyverse_sdk.exceptions import ValidationError

try:
    ReceiptListQuery(created_at_min=datetime(2024, 6, 1),
                     created_at_max=datetime(2024, 1, 1))
except ValidationError as e:
    print(e)  # created_at_min must be <= created_at_max
```

## See also

- [[Endpoints]] — where query models are passed to `list()` and `iter_all()`
- [[Models]] — the response models these queries return
- [[Error-Handling]] — `ValidationError` and the input rules above
- [[Flat-File-Export]] — fetch with a query, then write the results to disk
- [[Client]] — construct the client the endpoints hang off
