from datetime import datetime, date
from loyverse_sdk import LoyverseClient
from loyverse_sdk.core.console import console
from loyverse_sdk.exceptions import APIError
from loyverse_sdk.models.receipt import Receipt


async def fetch_latest_receipt(
    client: LoyverseClient,
    *,
    debug: bool = False
) -> Receipt:
    """Returns the latest issued receipt."""

    records = await client.receipts.list(limit=1)
    if len(records.items) == 0:
        raise APIError(status_code=400, payload={"detail": "failed to retrieve latest receipt"})

    return records.items[0]


async def fetch_latest_receipts(
    client: LoyverseClient,
    n: int,
    *,
    debug: bool = False
) -> Receipt:
    """Returns the latest issued receipt."""

    records = []
    cursor = None
    while len(records) < n:
        if cursor:
            next_records = await client.receipts.list(cursor=cursor)
        else:
            next_records = await client.receipts.list()

        records.extend(next_records.items)
        cursor = next_records.next_cursor

    if len(records) == 0:
        raise APIError(status_code=400, payload={"detail": "failed to retrieve latest receipts"})

    return records[:n]


async def fetch_receipts_today(
    client: LoyverseClient,
    *,
    debug: bool = False
) -> list[Receipt]:
    """Returns a list of receipts issue on or after the current date."""

    today = datetime.today()
    created_at_min = datetime(today.year, today.month, today.day)

    if debug:
        console.log(f"Retrieving receipts issued no later than {created_at_min}")

    records = []
    async for record in client.receipts.iter_all(created_at_min=created_at_min):
        records.append(record)

    if debug:
        console.log(f"Fetched {len(records)} records")

    return records


async def fetch_receipts_since(
    client: LoyverseClient,
    dt: datetime,
    *,
    debug: bool = False
) -> list[Receipt]:
    """Returns a list of receipts issue on or after the current date."""

    assert dt <= datetime.today(), "`dt` cannot be a future date"

    if isinstance(dt, (datetime, date)):
        dt = datetime(dt.year, dt.month, dt.day)
    else:
        raise ValueError("Invalid datetime object")

    if debug:
        console.log(f"Retrieving receipts issued no later than {dt}")

    records = []
    async for record in client.receipts.iter_all(created_at_min=dt):
        records.append(record)

    if debug:
        console.log(f"Fetched {len(records)} records")

    return records
