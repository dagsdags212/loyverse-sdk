# Helpers

`loyverse_sdk` ships convenience functions that wrap common receipt-fetching
workflows so you don't have to build query models or drive pagination by hand.
They are coroutines that take a [[Client]] and return `Receipt`
objects (see [[Models]]).

```python
from loyverse_sdk import (
    fetch_latest_receipt,
    fetch_latest_receipts,
    fetch_receipts_today,
    fetch_receipts_since,
)
# (also available as `from loyverse_sdk.helpers import ...`)
```

## Functions

### `fetch_latest_receipt(client, *, debug=False) -> Receipt`

Return the single most recently issued receipt.

```python
receipt = await fetch_latest_receipt(client)
print(receipt.receipt_number, receipt.total_money)
```

Raises `ResourceNotFoundError` if no receipts exist.

### `fetch_latest_receipts(client, n, *, debug=False) -> list[Receipt]`

Return the `n` most recent receipts, paginating as needed. If fewer than `n`
exist, it returns everything available (it does not loop forever).

```python
last_ten = await fetch_latest_receipts(client, 10)
```

Raises `ConfigurationError` if `n < 1`, or `ResourceNotFoundError` if there are
no receipts.

### `fetch_receipts_today(client, *, debug=False) -> list[Receipt]`

Return every receipt issued since the start of the current day.

```python
todays = await fetch_receipts_today(client)
print(f"{len(todays)} receipts so far today")
```

### `fetch_receipts_since(client, dt, *, debug=False) -> list[Receipt]`

Return every receipt issued on or after `dt` (a `date` or `datetime`).

```python
from datetime import date

since_jan = await fetch_receipts_since(client, date(2024, 1, 1))
```

Raises `ConfigurationError` if `dt` is in the future or is not a `date`/`datetime`.

## Notes

- Pass `debug=True` to log progress to the console.
- These are thin wrappers over `client.receipts` — for custom filters (store,
  date ranges, sort order) use [[Query-Models]] with
  `client.receipts.list()` / `iter_all()` directly (see [[Endpoints]]).

## See also

- [[Endpoints]] — the underlying receipts endpoint
- [[Query-Models]] — build precise receipt queries
- [[Error-Handling]] — the exceptions these functions raise
