"""Convenience helpers for common receipt-fetching workflows.

These wrap :class:`~loyverse_sdk.client.LoyverseClient` receipt endpoints to
cover frequent tasks (latest receipt, today's receipts, receipts since a date)
without the caller having to build query objects or drive pagination manually.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, cast

from loyverse_sdk.core.console import console
from loyverse_sdk.exceptions import ConfigurationError, ResourceNotFoundError
from loyverse_sdk.models.receipt import (
    Receipt,
    ReceiptListQuery,
    ReceiptListResponse,
)

if TYPE_CHECKING:
    from loyverse_sdk.client import LoyverseClient


async def fetch_latest_receipt(
    client: LoyverseClient, *, debug: bool = False
) -> Receipt:
    """Return the most recently issued receipt.

    Args:
        client: LoyverseClient instance.
        debug: Enable debug logging.

    Returns:
        The most recent receipt.

    Raises:
        ResourceNotFoundError: If no receipts exist in the system.
    """
    response = cast(
        ReceiptListResponse,
        await client.receipts.list(ReceiptListQuery(limit=1)),
    )
    if not response.items:
        raise ResourceNotFoundError(
            "No receipts found in the system", resource_type="receipts"
        )

    if debug:
        console.log("Fetched latest receipt")

    return response.items[0]


async def fetch_latest_receipts(
    client: LoyverseClient, n: int, *, debug: bool = False
) -> list[Receipt]:
    """Return the ``n`` most recently issued receipts.

    Args:
        client: LoyverseClient instance.
        n: Number of receipts to fetch.
        debug: Enable debug logging.

    Returns:
        List of the most recent receipts (up to ``n`` items).

    Raises:
        ResourceNotFoundError: If no receipts exist in the system.
        ConfigurationError: If ``n`` is less than 1.
    """
    if n < 1:
        raise ConfigurationError(f"Invalid value for n: {n}. Must be at least 1.")

    records: list[Receipt] = []
    cursor: str | None = None
    while len(records) < n:
        response = cast(
            ReceiptListResponse,
            await client.receipts.list(ReceiptListQuery(cursor=cursor)),
        )
        records.extend(response.items)
        cursor = response.next_cursor
        if not cursor:
            # No more pages — stop even if fewer than n receipts exist.
            break

    if not records:
        raise ResourceNotFoundError(
            "No receipts found in the system", resource_type="receipts"
        )

    if debug:
        console.log(f"Fetched {len(records[:n])} receipts")

    return records[:n]


async def fetch_receipts_today(
    client: LoyverseClient, *, debug: bool = False
) -> list[Receipt]:
    """Return all receipts issued on or after the start of the current day."""
    today = datetime.today()
    created_at_min = datetime(today.year, today.month, today.day)

    if debug:
        console.log(f"Retrieving receipts issued on or after {created_at_min}")

    records = [
        record
        async for record in client.receipts.iter_all(
            ReceiptListQuery(created_at_min=created_at_min)
        )
    ]

    if debug:
        console.log(f"Fetched {len(records)} receipts")

    return records


async def fetch_receipts_since(
    client: LoyverseClient, dt: datetime | date, *, debug: bool = False
) -> list[Receipt]:
    """Return all receipts issued on or after the given date.

    Args:
        client: LoyverseClient instance.
        dt: Date/datetime to fetch receipts from (inclusive).
        debug: Enable debug logging.

    Returns:
        List of receipts issued on or after the specified date.

    Raises:
        ConfigurationError: If ``dt`` is a future date or not a date/datetime.
    """
    # Normalize to a datetime first so the future-date check is type-safe
    # (comparing a bare ``date`` against ``datetime`` raises TypeError).
    if isinstance(dt, datetime):
        created_at_min = dt
    elif isinstance(dt, date):
        created_at_min = datetime(dt.year, dt.month, dt.day)
    else:
        raise ConfigurationError(
            f"Invalid datetime object: expected datetime or date, "
            f"got {type(dt).__name__}"
        )

    if created_at_min > datetime.today():
        raise ConfigurationError(
            f"Cannot fetch receipts from future date: {dt}. "
            "Please provide a date that is today or earlier."
        )

    if debug:
        console.log(f"Retrieving receipts issued on or after {created_at_min}")

    records = [
        record
        async for record in client.receipts.iter_all(
            ReceiptListQuery(created_at_min=created_at_min)
        )
    ]

    if debug:
        console.log(f"Fetched {len(records)} receipts")

    return records
