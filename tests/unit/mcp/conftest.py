"""Shared fixtures for MCP unit tests."""

from unittest.mock import AsyncMock, MagicMock

import polars as pl
import pytest


def _make_list_response(items: list) -> MagicMock:
    """Build a mock list response whose model_dump returns items + next_cursor."""
    resp = MagicMock()
    resp.model_dump.return_value = {"items": items, "next_cursor": None}
    return resp


def _make_item_response(data: dict) -> MagicMock:
    """Build a mock single-item response."""
    obj = MagicMock()
    obj.model_dump.return_value = data
    return obj


def _make_analytics_df(rows: list[dict]) -> MagicMock:
    """Build a mock Polars DataFrame for analytics calls."""
    df = MagicMock(spec=pl.DataFrame)
    df.to_dicts.return_value = rows
    return df


@pytest.fixture
def mock_client():
    """LoyverseClient mock with AsyncMock endpoint methods."""
    client = MagicMock()

    # List methods
    client.receipts.list = AsyncMock(
        return_value=_make_list_response([{"receipt_number": "R-1"}])
    )
    client.items.list = AsyncMock(return_value=_make_list_response([{"id": "item-1"}]))
    client.customers.list = AsyncMock(
        return_value=_make_list_response([{"id": "cust-1"}])
    )
    client.categories.list = AsyncMock(
        return_value=_make_list_response([{"id": "cat-1"}])
    )
    client.employees.list = AsyncMock(
        return_value=_make_list_response([{"id": "emp-1"}])
    )
    client.shifts.list = AsyncMock(return_value=_make_shift_list_response())
    client.stores.list = AsyncMock(
        return_value=_make_list_response([{"id": "store-1"}])
    )
    client.inventory.list = AsyncMock(
        return_value=_make_list_response([{"variant_id": "v-1"}])
    )
    client.payment_types.list = AsyncMock(
        return_value=_make_list_response([{"id": "pt-1"}])
    )

    # Retrieve methods
    client.receipts.retrieve = AsyncMock(
        return_value=_make_item_response({"receipt_number": "R-1"})
    )
    client.items.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "item-1"})
    )
    client.customers.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "cust-1"})
    )
    client.categories.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "cat-1"})
    )
    client.employees.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "emp-1"})
    )
    client.shifts.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "shift-1"})
    )
    client.stores.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "store-1"})
    )
    client.payment_types.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "pt-1"})
    )
    client.merchant.retrieve = AsyncMock(
        return_value=_make_item_response({"id": "merchant-1"})
    )

    return client


def _make_shift_list_response() -> MagicMock:
    resp = MagicMock()
    resp.model_dump.return_value = {"shifts": [{"id": "shift-1"}]}
    return resp


@pytest.fixture
def mock_ctx(mock_client):
    """FastMCP Context mock wired to mock_client via lifespan_state."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {"client": mock_client}
    return ctx


@pytest.fixture
def mock_analytics_engine():
    """Mock AnalyticsEngine with all sub-modules patched."""
    engine = MagicMock()

    engine.revenue.total_revenue_by_month.return_value = _make_analytics_df(
        [
            {
                "month": "2026-05",
                "revenue": 1500.0,
                "tx_count": 6,
                "avg_ticket": 250.0,
            },
        ]
    )
    engine.revenue.daily_revenue.return_value = _make_analytics_df(
        [
            {
                "date": "2026-05-01",
                "revenue": 500.0,
                "tx_count": 2,
                "avg_ticket": 250.0,
            },
        ]
    )
    engine.revenue.revenue_by_store.return_value = _make_analytics_df(
        [
            {
                "store_name": "Main",
                "tx_count": 100,
                "revenue": 20000.0,
                "avg_ticket": 200.0,
            },
        ]
    )
    engine.products.top_items.return_value = _make_analytics_df(
        [
            {"item": "Wash", "total_qty": 50, "total_revenue": 5000.0, "tx_count": 50},
        ]
    )
    engine.products.revenue_by_category.return_value = _make_analytics_df(
        [
            {
                "category": "Service",
                "tx_count": 80,
                "revenue": 16000.0,
                "units_sold": 200,
                "pct_share": 80.0,
            },
        ]
    )
    engine.customers.rfm_analysis.return_value = _make_analytics_df(
        [
            {
                "customer_id": "c1",
                "name": "John",
                "recency_days": 3,
                "frequency": 10,
                "monetary": 2500.0,
                "r_score": 5,
                "f_score": 5,
                "m_score": 5,
                "rfm_cell": 555,
                "segment": "Champions",
            },
        ]
    )
    engine.customers.top_customers.return_value = _make_analytics_df(
        [
            {
                "customer_id": "c1",
                "name": "John",
                "visits": 10,
                "total_spent": 2500.0,
                "avg_ticket": 250.0,
            },
        ]
    )
    engine.employees.revenue_by_employee.return_value = _make_analytics_df(
        [
            {
                "employee": "Alice",
                "tx_count": 100,
                "revenue": 20000.0,
                "avg_ticket": 200.0,
                "total_tips": 500.0,
            },
        ]
    )
    engine.operations.peak_hours.return_value = _make_analytics_df(
        [
            {"hour": 14, "tx_count": 30, "revenue": 6000.0, "pct_of_day": 15.0},
        ]
    )
    engine.operations.peak_days.return_value = _make_analytics_df(
        [
            {
                "day_name": "Saturday",
                "tx_count": 150,
                "revenue": 30000.0,
                "avg_ticket": 200.0,
            },
        ]
    )
    engine.time_series.monthly_summary.return_value = _make_analytics_df(
        [
            {
                "month": "2026-05-01",
                "revenue": 200000.0,
                "tx_count": 900,
                "unique_customers": 400,
                "avg_ticket": 222.0,
                "prev_month_revenue": 195000.0,
                "mom_change_pct": 2.6,
            },
        ]
    )
    engine.close = MagicMock()

    return engine


@pytest.fixture
def mock_ctx_analytics(mock_client, mock_analytics_engine):
    """FastMCP Context mock with both client and analytics engine."""
    ctx = MagicMock()
    ctx.request_context.lifespan_context = {
        "client": mock_client,
        "engine": mock_analytics_engine,
    }
    return ctx
