"""Unit tests for MCP tool functions.

Each test verifies that the tool calls the correct endpoint method on the
LoyverseClient and returns a valid JSON string.
"""

import json

import pytest

from loyverse_sdk.mcp.tools import (
    GetCategoryInput,
    GetCustomerInput,
    GetEmployeeInput,
    GetItemInput,
    GetPaymentTypeInput,
    GetReceiptInput,
    GetShiftInput,
    GetStoreInput,
    ListCustomersInput,
    ListInventoryInput,
    ListItemsInput,
    ListPaymentTypesInput,
    ListReceiptsInput,
    _AnalyticsInput,
    _BaseListInput,
    loyverse_analytics_daily_revenue,
    loyverse_analytics_monthly_summary,
    loyverse_analytics_peak_days,
    loyverse_analytics_peak_hours,
    loyverse_analytics_revenue_by_category,
    loyverse_analytics_revenue_by_employee,
    loyverse_analytics_revenue_by_store,
    loyverse_analytics_rfm_analysis,
    loyverse_analytics_top_customers,
    loyverse_analytics_top_items,
    loyverse_analytics_total_revenue,
    loyverse_analytics_unique_customers,
    loyverse_get_category,
    loyverse_get_customer,
    loyverse_get_employee,
    loyverse_get_item,
    loyverse_get_merchant,
    loyverse_get_payment_type,
    loyverse_get_receipt,
    loyverse_get_shift,
    loyverse_get_store,
    loyverse_list_categories,
    loyverse_list_customers,
    loyverse_list_employees,
    loyverse_list_inventory,
    loyverse_list_items,
    loyverse_list_payment_types,
    loyverse_list_receipts,
    loyverse_list_shifts,
    loyverse_list_stores,
)


def _is_json(value: str) -> bool:
    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


# ---------------------------------------------------------------------------
# List tool tests
# ---------------------------------------------------------------------------


class TestListReceipts:
    @pytest.mark.asyncio
    async def test_calls_receipts_list(self, mock_client, mock_ctx):
        result = await loyverse_list_receipts(ListReceiptsInput(), mock_ctx)
        mock_client.receipts.list.assert_called_once()
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_returns_count(self, mock_client, mock_ctx):
        result = await loyverse_list_receipts(ListReceiptsInput(), mock_ctx)
        data = json.loads(result)
        assert "count" in data
        assert data["count"] == 1

    @pytest.mark.asyncio
    async def test_passes_store_id_filter(self, mock_client, mock_ctx):
        await loyverse_list_receipts(ListReceiptsInput(store_id="store-123"), mock_ctx)
        call_kwargs = mock_client.receipts.list.call_args
        query = call_kwargs[0][0]
        assert query.store_id == "store-123"


class TestListItems:
    @pytest.mark.asyncio
    async def test_calls_items_list(self, mock_client, mock_ctx):
        result = await loyverse_list_items(ListItemsInput(), mock_ctx)
        mock_client.items.list.assert_called_once()
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_passes_category_filter(self, mock_client, mock_ctx):
        await loyverse_list_items(ListItemsInput(category_id="cat-abc"), mock_ctx)
        query = mock_client.items.list.call_args[0][0]
        assert query.category_id == "cat-abc"


class TestListCustomers:
    @pytest.mark.asyncio
    async def test_calls_customers_list(self, mock_client, mock_ctx):
        result = await loyverse_list_customers(ListCustomersInput(), mock_ctx)
        mock_client.customers.list.assert_called_once()
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_passes_email_filter(self, mock_client, mock_ctx):
        await loyverse_list_customers(
            ListCustomersInput(email="user@example.com"), mock_ctx
        )
        query = mock_client.customers.list.call_args[0][0]
        assert query.email == "user@example.com"


class TestListCategories:
    @pytest.mark.asyncio
    async def test_calls_categories_list(self, mock_client, mock_ctx):
        result = await loyverse_list_categories(_BaseListInput(), mock_ctx)
        mock_client.categories.list.assert_called_once()
        assert _is_json(result)


class TestListEmployees:
    @pytest.mark.asyncio
    async def test_calls_employees_list(self, mock_client, mock_ctx):
        result = await loyverse_list_employees(_BaseListInput(), mock_ctx)
        mock_client.employees.list.assert_called_once()
        assert _is_json(result)


class TestListShifts:
    @pytest.mark.asyncio
    async def test_calls_shifts_list(self, mock_client, mock_ctx):
        result = await loyverse_list_shifts(_BaseListInput(), mock_ctx)
        mock_client.shifts.list.assert_called_once()
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_normalizes_shifts_key_to_items(self, mock_client, mock_ctx):
        result = await loyverse_list_shifts(_BaseListInput(), mock_ctx)
        data = json.loads(result)
        assert "items" in data


class TestListStores:
    @pytest.mark.asyncio
    async def test_calls_stores_list(self, mock_client, mock_ctx):
        result = await loyverse_list_stores(_BaseListInput(), mock_ctx)
        mock_client.stores.list.assert_called_once()
        assert _is_json(result)


class TestListInventory:
    @pytest.mark.asyncio
    async def test_calls_inventory_list(self, mock_client, mock_ctx):
        result = await loyverse_list_inventory(ListInventoryInput(), mock_ctx)
        mock_client.inventory.list.assert_called_once()
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_passes_store_ids_filter(self, mock_client, mock_ctx):
        await loyverse_list_inventory(
            ListInventoryInput(store_ids="store-1,store-2"), mock_ctx
        )
        query = mock_client.inventory.list.call_args[0][0]
        assert query.store_ids == "store-1,store-2"


class TestListPaymentTypes:
    @pytest.mark.asyncio
    async def test_calls_payment_types_list(self, mock_client, mock_ctx):
        result = await loyverse_list_payment_types(ListPaymentTypesInput(), mock_ctx)
        mock_client.payment_types.list.assert_called_once()
        assert _is_json(result)


# ---------------------------------------------------------------------------
# Retrieve tool tests
# ---------------------------------------------------------------------------


class TestGetReceipt:
    @pytest.mark.asyncio
    async def test_calls_receipts_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_receipt(GetReceiptInput(receipt_id="r-1"), mock_ctx)
        mock_client.receipts.retrieve.assert_called_once_with("r-1")
        assert _is_json(result)


class TestGetItem:
    @pytest.mark.asyncio
    async def test_calls_items_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_item(GetItemInput(item_id="i-1"), mock_ctx)
        mock_client.items.retrieve.assert_called_once_with("i-1")
        assert _is_json(result)


class TestGetCustomer:
    @pytest.mark.asyncio
    async def test_calls_customers_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_customer(
            GetCustomerInput(customer_id="c-1"), mock_ctx
        )
        mock_client.customers.retrieve.assert_called_once_with("c-1")
        assert _is_json(result)


class TestGetCategory:
    @pytest.mark.asyncio
    async def test_calls_categories_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_category(
            GetCategoryInput(category_id="cat-1"), mock_ctx
        )
        mock_client.categories.retrieve.assert_called_once_with("cat-1")
        assert _is_json(result)


class TestGetEmployee:
    @pytest.mark.asyncio
    async def test_calls_employees_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_employee(
            GetEmployeeInput(employee_id="e-1"), mock_ctx
        )
        mock_client.employees.retrieve.assert_called_once_with("e-1")
        assert _is_json(result)


class TestGetShift:
    @pytest.mark.asyncio
    async def test_calls_shifts_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_shift(GetShiftInput(shift_id="s-1"), mock_ctx)
        mock_client.shifts.retrieve.assert_called_once_with("s-1")
        assert _is_json(result)


class TestGetStore:
    @pytest.mark.asyncio
    async def test_calls_stores_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_store(GetStoreInput(store_id="st-1"), mock_ctx)
        mock_client.stores.retrieve.assert_called_once_with("st-1")
        assert _is_json(result)


class TestGetPaymentType:
    @pytest.mark.asyncio
    async def test_calls_payment_types_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_payment_type(
            GetPaymentTypeInput(payment_type_id="pt-1"), mock_ctx
        )
        mock_client.payment_types.retrieve.assert_called_once_with("pt-1")
        assert _is_json(result)


class TestGetMerchant:
    @pytest.mark.asyncio
    async def test_calls_merchant_retrieve(self, mock_client, mock_ctx):
        result = await loyverse_get_merchant(mock_ctx)
        mock_client.merchant.retrieve.assert_called_once()
        assert _is_json(result)


# ---------------------------------------------------------------------------
# Error handling tests
# ---------------------------------------------------------------------------


class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_sdk_error_returns_error_string(self, mock_client, mock_ctx):
        from unittest.mock import AsyncMock

        from loyverse_sdk.exceptions import NotFoundError

        mock_client.receipts.retrieve = AsyncMock(
            side_effect=NotFoundError(
                {"message": "not found"}, endpoint="receipts/bad-id"
            )
        )
        result = await loyverse_get_receipt(
            GetReceiptInput(receipt_id="bad-id"), mock_ctx
        )
        assert result.startswith("Error:")

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_error_string(self, mock_client, mock_ctx):
        from unittest.mock import AsyncMock

        mock_client.items.list = AsyncMock(side_effect=RuntimeError("unexpected"))
        result = await loyverse_list_items(ListItemsInput(), mock_ctx)
        assert result.startswith("Error:")


# ---------------------------------------------------------------------------
# Analytics tool tests
# ---------------------------------------------------------------------------


class TestAnalyticsDailyRevenue:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_daily_revenue(
            _AnalyticsInput(days=7), mock_ctx_analytics
        )
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_contains_revenue_field(self, mock_ctx_analytics):
        result = await loyverse_analytics_daily_revenue(
            _AnalyticsInput(days=7), mock_ctx_analytics
        )
        data = json.loads(result)
        assert data[0]["revenue"] == 500.0


class TestAnalyticsRevenueByStore:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_revenue_by_store(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsTotalRevenue:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_total_revenue(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)

    @pytest.mark.asyncio
    async def test_by_month_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_total_revenue(
            _AnalyticsInput(days=30, by_month=True), mock_ctx_analytics
        )
        assert _is_json(result)
        data = json.loads(result)
        assert data[0]["month"] == "2026-05"
        assert data[0]["revenue"] == 1500.0


class TestAnalyticsTopItems:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_top_items(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsRevenueByCategory:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_revenue_by_category(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsRFM:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_rfm_analysis(mock_ctx_analytics)
        assert _is_json(result)


class TestAnalyticsTopCustomers:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_top_customers(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsUniqueCustomers:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_unique_customers(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsRevenueByEmployee:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_revenue_by_employee(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsPeakHours:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_peak_hours(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsPeakDays:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_peak_days(
            _AnalyticsInput(days=30), mock_ctx_analytics
        )
        assert _is_json(result)


class TestAnalyticsMonthlySummary:
    @pytest.mark.asyncio
    async def test_returns_json(self, mock_ctx_analytics):
        result = await loyverse_analytics_monthly_summary(mock_ctx_analytics)
        assert _is_json(result)


class TestAnalyticsErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_engine_returns_error(self, mock_ctx):
        result = await loyverse_analytics_daily_revenue(
            _AnalyticsInput(days=7), mock_ctx
        )
        assert result.startswith("Error:")
