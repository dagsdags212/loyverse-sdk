from datetime import datetime, date
from loyverse_sdk import LoyverseClient
from loyverse_sdk.core.console import console
from loyverse_sdk.exceptions import ResourceNotFoundError, ConfigurationError
from loyverse_sdk.models.receipt import Receipt


async def fetch_latest_receipt(
    client: LoyverseClient, *, debug: bool = False
) -> Receipt:
    """
    Returns the latest issued receipt.

    Args:
        client: LoyverseClient instance
        debug: Enable debug logging

    Returns:
        The most recent receipt

    Raises:
        ResourceNotFoundError: If no receipts exist in the system
    """
    records = await client.receipts.list(limit=1)
    if len(records.items) == 0:
        raise ResourceNotFoundError(
            "No receipts found in the system", resource_type="receipts"
        )

    return records.items[0]


async def fetch_latest_receipts(
    client: LoyverseClient, n: int, *, debug: bool = False
) -> list[Receipt]:
    """
    Returns the N latest issued receipts.

    Args:
        client: LoyverseClient instance
        n: Number of receipts to fetch
        debug: Enable debug logging

    Returns:
        List of the most recent receipts (up to n items)

    Raises:
        ResourceNotFoundError: If no receipts exist in the system
        ConfigurationError: If n is less than 1
    """
    if n < 1:
        raise ConfigurationError(f"Invalid value for n: {n}. Must be at least 1.")

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
        raise ResourceNotFoundError(
            "No receipts found in the system", resource_type="receipts"
        )

    return records[:n]


async def fetch_receipts_today(
    client: LoyverseClient, *, debug: bool = False
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
    client: LoyverseClient, dt: datetime | date, *, debug: bool = False
) -> list[Receipt]:
    """
    Returns a list of receipts issued on or after the given date.

    Args:
        client: LoyverseClient instance
        dt: Date/datetime to fetch receipts from (inclusive)
        debug: Enable debug logging

    Returns:
        List of receipts issued on or after the specified date

    Raises:
        ConfigurationError: If dt is a future date or invalid datetime
    """
    # Validate date is not in the future
    if dt > datetime.today():
        raise ConfigurationError(
            f"Cannot fetch receipts from future date: {dt}. "
            "Please provide a date that is today or earlier."
        )

    # Convert to datetime with time set to beginning of day
    if isinstance(dt, date) and not isinstance(dt, datetime):
        dt = datetime(dt.year, dt.month, dt.day)
    elif not isinstance(dt, datetime):
        raise ConfigurationError(
            f"Invalid datetime object: expected datetime or date, got {type(dt).__name__}"
        )

    if debug:
        console.log(f"Retrieving receipts issued on or after {dt}")

    records = []
    async for record in client.receipts.iter_all(created_at_min=dt):
        records.append(record)

    if debug:
        console.log(f"Fetched {len(records)} records")

    return records
