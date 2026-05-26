"""
Unit tests for all ListQuery model classes.

Covers BaseListQuery validation (date ranges, limit bounds) and
endpoint-specific query model field serialization via to_params().
"""

from datetime import datetime, timedelta
import pytest
from pydantic import ValidationError

from loyverse_sdk.models.common import BaseListQuery
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
    StoreListQuery,
    SupplierListQuery,
    TaxListQuery,
    VariantListQuery,
    WebhookListQuery,
)
from loyverse_sdk.models.webhook import WebhookType, WebhookStatus
from loyverse_sdk.core.config import config


# =============================================================================
# BaseListQuery tests
# =============================================================================


class TestBaseListQueryDefaults:
    """Default values and types for BaseListQuery fields."""

    def test_default_limit_from_config(self):
        q = BaseListQuery()
        assert q.limit == config.PAGE_LIMIT

    def test_default_cursor_none(self):
        q = BaseListQuery()
        assert q.cursor is None

    def test_default_date_filters_none(self):
        q = BaseListQuery()
        assert q.created_at_min is None
        assert q.created_at_max is None
        assert q.updated_at_min is None
        assert q.updated_at_max is None


class TestBaseListQueryDateValidation:
    """Date range validators on BaseListQuery."""

    def test_created_at_min_less_than_max_passes(self):
        q = BaseListQuery(
            created_at_min=datetime(2024, 1, 1),
            created_at_max=datetime(2024, 12, 31),
        )
        assert q.created_at_min < q.created_at_max

    def test_created_at_min_greater_than_max_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            BaseListQuery(
                created_at_min=datetime(2024, 12, 31),
                created_at_max=datetime(2024, 1, 1),
            )
        assert "created_at_min must be <= created_at_max" in str(exc_info.value)

    def test_updated_at_min_less_than_max_passes(self):
        q = BaseListQuery(
            updated_at_min=datetime(2024, 1, 1),
            updated_at_max=datetime(2024, 12, 31),
        )
        assert q.updated_at_min < q.updated_at_max

    def test_updated_at_min_greater_than_max_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            BaseListQuery(
                updated_at_min=datetime(2024, 12, 31),
                updated_at_max=datetime(2024, 1, 1),
            )
        assert "updated_at_min must be <= updated_at_max" in str(exc_info.value)

    def test_equal_dates_pass(self):
        same = datetime(2024, 6, 15)
        q = BaseListQuery(created_at_min=same, created_at_max=same)
        assert q.created_at_min == q.created_at_max

    def test_one_date_none_passes(self):
        q = BaseListQuery(created_at_min=datetime(2024, 1, 1))
        assert q.created_at_max is None


class TestBaseListQueryLimitValidation:
    """Limit bound validator on BaseListQuery."""

    def test_limit_within_bounds(self):
        q = BaseListQuery(limit=100)
        assert q.limit == 100

    def test_limit_at_lower_bound(self):
        q = BaseListQuery(limit=1)
        assert q.limit == 1

    def test_limit_at_upper_bound(self):
        q = BaseListQuery(limit=250)
        assert q.limit == 250

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            BaseListQuery(limit=0)
        assert "limit must be between 1 and 250" in str(exc_info.value)

    def test_limit_negative_raises(self):
        with pytest.raises(ValidationError):
            BaseListQuery(limit=-1)

    def test_limit_above_250_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            BaseListQuery(limit=251)
        assert "limit must be between 1 and 250" in str(exc_info.value)


class TestBaseListQueryToParams:
    """to_params() serialization on BaseListQuery."""

    def test_empty_query_returns_only_limit(self):
        q = BaseListQuery()
        params = q.to_params()
        assert params == {"limit": config.PAGE_LIMIT}

    def test_cursor_included_when_set(self):
        q = BaseListQuery(cursor="next-page-token")
        params = q.to_params()
        assert "cursor" in params
        assert params["cursor"] == "next-page-token"

    def test_explicit_limit_in_params(self):
        q = BaseListQuery(limit=50)
        params = q.to_params()
        assert params["limit"] == 50

    def test_created_at_min_serialized(self):
        dt = datetime(2024, 3, 15, 10, 30, 0)
        q = BaseListQuery(created_at_min=dt)
        params = q.to_params()
        assert "created_at_min" in params
        assert "2024-03-15" in params["created_at_min"]

    def test_updated_at_max_serialized(self):
        dt = datetime(2024, 12, 31, 23, 59, 59)
        q = BaseListQuery(updated_at_max=dt)
        params = q.to_params()
        assert "updated_at_max" in params
        assert "2024-12-31" in params["updated_at_max"]

    def test_only_non_null_fields_included(self):
        q = BaseListQuery(cursor="token", limit=50)
        params = q.to_params()
        assert "limit" in params
        assert "cursor" in params
        assert "created_at_min" not in params
        assert "created_at_max" not in params


# =============================================================================
# CategoryListQuery
# =============================================================================


class TestCategoryListQuery:
    def test_default_show_deleted_false(self):
        q = CategoryListQuery()
        assert q.show_deleted is False

    def test_category_ids_passed_to_params(self):
        q = CategoryListQuery(category_ids="id1,id2")
        assert q.to_params()["category_ids"] == "id1,id2"

    def test_show_deleted_true_serialized_lowercase(self):
        q = CategoryListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_show_deleted_false_not_in_params(self):
        q = CategoryListQuery(show_deleted=False)
        params = q.to_params()
        assert "show_deleted" not in params

    def test_combined_params(self):
        q = CategoryListQuery(category_ids="c1,c2", limit=25, cursor="tok")
        params = q.to_params()
        assert params["category_ids"] == "c1,c2"
        assert params["limit"] == 25
        assert params["cursor"] == "tok"


# =============================================================================
# CustomerListQuery
# =============================================================================


class TestCustomerListQuery:
    def test_customer_ids_passed_to_params(self):
        q = CustomerListQuery(customer_ids="cust-1,cust-2")
        assert q.to_params()["customer_ids"] == "cust-1,cust-2"

    def test_email_passed_to_params(self):
        q = CustomerListQuery(email="john@example.com")
        assert q.to_params()["email"] == "john@example.com"

    def test_email_with_date_filter(self):
        q = CustomerListQuery(
            email="jane@example.com",
            created_at_min=datetime(2024, 1, 1),
            created_at_max=datetime(2024, 12, 31),
        )
        params = q.to_params()
        assert params["email"] == "jane@example.com"
        assert "created_at_min" in params
        assert "created_at_max" in params


# =============================================================================
# DiscountListQuery
# =============================================================================


class TestDiscountListQuery:
    def test_discount_ids_passed_to_params(self):
        q = DiscountListQuery(discount_ids="disc-1,disc-2")
        assert q.to_params()["discount_ids"] == "disc-1,disc-2"

    def test_show_deleted_true_serialized(self):
        q = DiscountListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_date_filters_included(self):
        q = DiscountListQuery(
            updated_at_min=datetime(2024, 1, 1),
            updated_at_max=datetime(2024, 6, 30),
        )
        params = q.to_params()
        assert "updated_at_min" in params
        assert "updated_at_max" in params


# =============================================================================
# EmployeeListQuery
# =============================================================================


class TestEmployeeListQuery:
    def test_employee_ids_passed_to_params(self):
        q = EmployeeListQuery(employee_ids="emp-1,emp-2")
        assert q.to_params()["employee_ids"] == "emp-1,emp-2"

    def test_show_deleted_default_false(self):
        q = EmployeeListQuery()
        assert q.show_deleted is False

    def test_show_deleted_true_serialized(self):
        q = EmployeeListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"


# =============================================================================
# InventoryListQuery
# =============================================================================


class TestInventoryListQuery:
    def test_store_ids_passed_to_params(self):
        q = InventoryListQuery(store_ids="store-1,store-2")
        assert q.to_params()["store_ids"] == "store-1,store-2"

    def test_variant_ids_passed_to_params(self):
        q = InventoryListQuery(variant_ids="var-1,var-2")
        assert q.to_params()["variant_ids"] == "var-1,var-2"

    def test_combined_filters(self):
        q = InventoryListQuery(
            store_ids="store-abc",
            variant_ids="var-xyz",
            limit=100,
        )
        params = q.to_params()
        assert params["store_ids"] == "store-abc"
        assert params["variant_ids"] == "var-xyz"
        assert params["limit"] == 100

    def test_no_date_filters_for_inventory(self):
        """Inventory has updated_at but not created_at."""
        q = InventoryListQuery(updated_at_min=datetime(2024, 1, 1))
        params = q.to_params()
        assert "updated_at_min" in params


# =============================================================================
# ItemListQuery
# =============================================================================


class TestItemListQuery:
    def test_item_ids_passed_to_params(self):
        q = ItemListQuery(item_ids="item-1,item-2")
        assert q.to_params()["item_ids"] == "item-1,item-2"

    def test_store_id_passed_to_params(self):
        q = ItemListQuery(store_id="store-single")
        assert q.to_params()["store_id"] == "store-single"

    def test_category_id_passed_to_params(self):
        q = ItemListQuery(category_id="cat-123")
        assert q.to_params()["category_id"] == "cat-123"

    def test_show_deleted_true_serialized(self):
        q = ItemListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_all_filters_combined(self):
        q = ItemListQuery(
            store_id="store-1",
            category_id="cat-1",
            show_deleted=True,
            limit=50,
        )
        params = q.to_params()
        assert params["store_id"] == "store-1"
        assert params["category_id"] == "cat-1"
        assert params["show_deleted"] == "true"
        assert params["limit"] == 50


# =============================================================================
# ModifierListQuery
# =============================================================================


class TestModifierListQuery:
    def test_modifier_ids_passed_to_params(self):
        q = ModifierListQuery(modifier_ids="mod-1,mod-2")
        assert q.to_params()["modifier_ids"] == "mod-1,mod-2"

    def test_show_deleted_true_serialized(self):
        q = ModifierListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_default_show_deleted_false(self):
        q = ModifierListQuery()
        assert q.show_deleted is False


# =============================================================================
# PaymentTypeListQuery
# =============================================================================


class TestPaymentTypeListQuery:
    def test_payment_type_ids_passed_to_params(self):
        q = PaymentTypeListQuery(payment_type_ids="pt-1,pt-2")
        assert q.to_params()["payment_type_ids"] == "pt-1,pt-2"

    def test_show_deleted_true_serialized(self):
        q = PaymentTypeListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"


# =============================================================================
# PosDeviceListQuery
# =============================================================================


class TestPosDeviceListQuery:
    def test_store_id_passed_to_params(self):
        q = PosDeviceListQuery(store_id="store-abc")
        assert q.to_params()["store_id"] == "store-abc"

    def test_show_deleted_true_serialized(self):
        q = PosDeviceListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"


# =============================================================================
# ReceiptListQuery
# =============================================================================


class TestReceiptListQuery:
    def test_receipt_numbers_passed_to_params(self):
        q = ReceiptListQuery(receipt_numbers="8-100,8-200")
        assert q.to_params()["receipt_numbers"] == "8-100,8-200"

    def test_since_receipt_number_passed_to_params(self):
        q = ReceiptListQuery(since_receipt_number="8-500")
        assert q.to_params()["since_receipt_number"] == "8-500"

    def test_before_receipt_number_passed_to_params(self):
        q = ReceiptListQuery(before_receipt_number="8-1000")
        assert q.to_params()["before_receipt_number"] == "8-1000"

    def test_store_id_passed_to_params(self):
        q = ReceiptListQuery(store_id="store-xyz")
        assert q.to_params()["store_id"] == "store-xyz"

    def test_order_passed_to_params(self):
        q = ReceiptListQuery(order="created_at_asc")
        assert q.to_params()["order"] == "created_at_asc"

    def test_order_desc_passed_to_params(self):
        q = ReceiptListQuery(order="created_at_desc")
        assert q.to_params()["order"] == "created_at_desc"

    def test_date_filters_included(self):
        q = ReceiptListQuery(
            created_at_min=datetime(2024, 1, 1),
            created_at_max=datetime(2024, 3, 31),
        )
        params = q.to_params()
        assert "created_at_min" in params
        assert "created_at_max" in params


# =============================================================================
# StoreListQuery
# =============================================================================


class TestStoreListQuery:
    def test_store_ids_passed_to_params(self):
        q = StoreListQuery(store_ids="store-1,store-2")
        assert q.to_params()["store_ids"] == "store-1,store-2"

    def test_show_deleted_true_serialized(self):
        q = StoreListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_date_filters_included(self):
        q = StoreListQuery(
            created_at_min=datetime(2024, 1, 1),
            created_at_max=datetime(2024, 12, 31),
        )
        params = q.to_params()
        assert "created_at_min" in params
        assert "created_at_max" in params


# =============================================================================
# SupplierListQuery
# =============================================================================


class TestSupplierListQuery:
    def test_suppliers_ids_passed_to_params(self):
        q = SupplierListQuery(suppliers_ids="sup-1,sup-2")
        assert q.to_params()["suppliers_ids"] == "sup-1,sup-2"

    def test_show_deleted_true_serialized(self):
        q = SupplierListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_pagination_params_included(self):
        q = SupplierListQuery(limit=50, cursor="next-token")
        params = q.to_params()
        assert params["limit"] == 50
        assert params["cursor"] == "next-token"


# =============================================================================
# TaxListQuery
# =============================================================================


class TestTaxListQuery:
    def test_tax_ids_passed_to_params(self):
        q = TaxListQuery(tax_ids="tax-1,tax-2")
        assert q.to_params()["tax_ids"] == "tax-1,tax-2"

    def test_show_deleted_true_serialized(self):
        q = TaxListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_date_filters_included(self):
        q = TaxListQuery(
            updated_at_min=datetime(2024, 1, 1),
            updated_at_max=datetime(2024, 6, 30),
        )
        params = q.to_params()
        assert "updated_at_min" in params
        assert "updated_at_max" in params


# =============================================================================
# WebhookListQuery
# =============================================================================


class TestWebhookListQuery:
    def test_id_passed_to_params(self):
        q = WebhookListQuery(id="webhook-abc")
        assert q.to_params()["id"] == "webhook-abc"

    def test_merchant_id_passed_to_params(self):
        q = WebhookListQuery(merchant_id="merchant-123")
        # API uses 'merchant_it' (typo in original spec)
        assert q.to_params()["merchant_it"] == "merchant-123"

    def test_url_passed_to_params(self):
        q = WebhookListQuery(url="https://example.com/hook")
        assert q.to_params()["url"] == "https://example.com/hook"

    def test_type_enum_value_passed(self):
        q = WebhookListQuery(type=WebhookType.ITEMS_UPDATE)
        assert q.to_params()["type"] == "items.update"

    def test_status_enum_value_passed(self):
        q = WebhookListQuery(status=WebhookStatus.DISABLED)
        assert q.to_params()["status"] == "DISABLED"

    def test_multiple_filters_combined(self):
        q = WebhookListQuery(
            type=WebhookType.INVENTORY_LEVELS_UPDATE,
            status=WebhookStatus.ENABLED,
        )
        params = q.to_params()
        assert params["type"] == "inventory_levels.update"
        assert params["status"] == "ENABLED"

    def test_date_filters_included(self):
        q = WebhookListQuery(
            created_at_min=datetime(2024, 1, 1),
            updated_at_max=datetime(2024, 12, 31),
        )
        params = q.to_params()
        assert "created_at_min" in params
        assert "updated_at_max" in params


# =============================================================================
# VariantListQuery
# =============================================================================


class TestVariantListQuery:
    def test_variants_ids_passed_to_params(self):
        q = VariantListQuery(variants_ids="var-1,var-2")
        assert q.to_params()["variants_ids"] == "var-1,var-2"

    def test_item_ids_passed_to_params(self):
        q = VariantListQuery(item_ids="item-1,item-2")
        # API uses 'items_ids'
        assert q.to_params()["items_ids"] == "item-1,item-2"

    def test_sku_passed_to_params(self):
        q = VariantListQuery(sku="SKU-12345")
        assert q.to_params()["sku"] == "SKU-12345"

    def test_show_deleted_true_serialized(self):
        q = VariantListQuery(show_deleted=True)
        assert q.to_params()["show_deleted"] == "true"

    def test_all_filters_combined(self):
        q = VariantListQuery(
            item_ids="item-abc",
            sku="SKU-XYZ",
            show_deleted=True,
            limit=100,
        )
        params = q.to_params()
        assert params["items_ids"] == "item-abc"
        assert params["sku"] == "SKU-XYZ"
        assert params["show_deleted"] == "true"
        assert params["limit"] == 100


# =============================================================================
# Integration: Query model used with endpoint list() method
# =============================================================================


class TestQueryModelUsageWithEndpoints:
    """Smoke test: query models serialize correctly for endpoint use."""

    def test_category_list_query_serializes(self):
        q = CategoryListQuery(category_ids="c1,c2", show_deleted=True)
        p = q.to_params()
        assert "category_ids" in p
        assert "show_deleted" in p
        assert p["show_deleted"] == "true"

    def test_inventory_list_query_serializes(self):
        q = InventoryListQuery(
            store_ids="s1",
            variant_ids="v1,v2",
            updated_at_min=datetime(2024, 1, 1),
        )
        p = q.to_params()
        assert p["store_ids"] == "s1"
        assert p["variant_ids"] == "v1,v2"
        assert "updated_at_min" in p

    def test_receipt_list_query_serializes(self):
        q = ReceiptListQuery(
            store_id="store-1",
            order="created_at_desc",
            created_at_min=datetime(2024, 1, 1),
        )
        p = q.to_params()
        assert p["store_id"] == "store-1"
        assert p["order"] == "created_at_desc"

    def test_webhook_list_query_serializes(self):
        q = WebhookListQuery(
            type=WebhookType.RECEIPTS_UPDATE,
            status=WebhookStatus.ENABLED,
        )
        p = q.to_params()
        assert p["type"] == "receipts.update"
        assert p["status"] == "ENABLED"

    def test_base_list_query_date_validator_still_applies(self):
        """BaseListQuery validators still fire for subclasses."""
        with pytest.raises(ValidationError):
            ItemListQuery(
                created_at_min=datetime(2024, 12, 31),
                created_at_max=datetime(2024, 1, 1),
            )
