"""Unit tests for loyverse_sdk.helpers receipt convenience functions.

These exercise the helper wrappers against a mocked receipts endpoint. They
also pin down two previously-latent bugs:

* ``fetch_latest_receipts`` must stop when pagination is exhausted instead of
  looping forever when fewer than ``n`` receipts exist.
* ``fetch_receipts_since`` must accept a bare ``date`` without raising
  ``TypeError`` from a ``date``/``datetime`` comparison.
"""

from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from loyverse_sdk.exceptions import ConfigurationError, ResourceNotFoundError
from loyverse_sdk.helpers import (
    fetch_latest_receipt,
    fetch_latest_receipts,
    fetch_receipts_since,
    fetch_receipts_today,
)


def _page(items, next_cursor=None):
    """Build a stand-in for ReceiptListResponse."""
    page = Mock()
    page.items = items
    page.next_cursor = next_cursor
    return page


def _client_with_iter(records):
    """Build a mock client whose receipts.iter_all yields *records*."""

    async def fake_iter_all(query=None):
        for r in records:
            yield r

    client = Mock()
    client.receipts.iter_all = fake_iter_all
    return client


class TestFetchLatestReceipt:
    @pytest.mark.asyncio
    async def test_returns_first_item(self):
        receipt = Mock()
        client = Mock()
        client.receipts.list = AsyncMock(return_value=_page([receipt]))

        result = await fetch_latest_receipt(client)

        assert result is receipt

    @pytest.mark.asyncio
    async def test_raises_when_no_receipts(self):
        client = Mock()
        client.receipts.list = AsyncMock(return_value=_page([]))

        with pytest.raises(ResourceNotFoundError):
            await fetch_latest_receipt(client)


class TestFetchLatestReceipts:
    @pytest.mark.asyncio
    async def test_rejects_non_positive_n(self):
        client = Mock()
        with pytest.raises(ConfigurationError):
            await fetch_latest_receipts(client, 0)

    @pytest.mark.asyncio
    async def test_stops_when_pagination_exhausted(self):
        # Only two receipts exist but caller asked for ten — must not loop forever.
        client = Mock()
        client.receipts.list = AsyncMock(
            return_value=_page([Mock(), Mock()], next_cursor=None)
        )

        result = await fetch_latest_receipts(client, 10)

        assert len(result) == 2
        assert client.receipts.list.await_count == 1

    @pytest.mark.asyncio
    async def test_paginates_until_target_reached(self):
        client = Mock()
        client.receipts.list = AsyncMock(
            side_effect=[
                _page([Mock(), Mock()], next_cursor="c1"),
                _page([Mock(), Mock()], next_cursor="c2"),
            ]
        )

        result = await fetch_latest_receipts(client, 3)

        assert len(result) == 3
        assert client.receipts.list.await_count == 2

    @pytest.mark.asyncio
    async def test_raises_when_no_receipts(self):
        client = Mock()
        client.receipts.list = AsyncMock(return_value=_page([], next_cursor=None))

        with pytest.raises(ResourceNotFoundError):
            await fetch_latest_receipts(client, 5)


class TestFetchReceiptsToday:
    @pytest.mark.asyncio
    async def test_collects_iter_all(self):
        records = [Mock(), Mock(), Mock()]
        client = _client_with_iter(records)

        result = await fetch_receipts_today(client)

        assert result == records


class TestFetchReceiptsSince:
    @pytest.mark.asyncio
    async def test_accepts_bare_date(self):
        # Regression: a bare date previously raised TypeError on the future check.
        records = [Mock()]
        client = _client_with_iter(records)

        result = await fetch_receipts_since(client, date(2020, 1, 1))

        assert result == records

    @pytest.mark.asyncio
    async def test_accepts_datetime(self):
        records = [Mock(), Mock()]
        client = _client_with_iter(records)

        result = await fetch_receipts_since(client, datetime(2020, 1, 1))

        assert result == records

    @pytest.mark.asyncio
    async def test_rejects_future_date(self):
        client = Mock()
        future = datetime.today() + timedelta(days=2)

        with pytest.raises(ConfigurationError):
            await fetch_receipts_since(client, future)

    @pytest.mark.asyncio
    async def test_rejects_invalid_type(self):
        client = Mock()
        with pytest.raises(ConfigurationError):
            await fetch_receipts_since(client, "2020-01-01")  # type: ignore[arg-type]
