"""
Unit tests for loyverse_sdk.models.inventory module.
"""

from datetime import datetime

from loyverse_sdk.models.inventory import Inventory, InventoryListResponse


class TestInventoryModel:
    """Test Inventory model fields and validation."""

    def test_creates_inventory_with_required_fields(self):
        """Test creating Inventory with all API fields."""
        now = datetime.now()
        inv = Inventory(
            variant_id="var-abc-123",
            store_id="store-xyz-456",
            in_stock=100,
            updated_at=now,
        )
        assert inv.variant_id == "var-abc-123"
        assert inv.store_id == "store-xyz-456"
        assert inv.in_stock == 100
        # updated_at is converted to local timezone, check it exists
        assert inv.updated_at is not None

    def test_in_stock_default_zero(self):
        """Test in_stock defaults to 0."""
        now = datetime.now()
        inv = Inventory(
            variant_id="var-123",
            store_id="store-456",
            updated_at=now,
        )
        assert inv.in_stock == 0

    def test_inventory_list_response_alias(self):
        """Test InventoryListResponse uses correct alias."""
        data = {
            "inventory_levels": [
                {
                    "variant_id": "var-1",
                    "store_id": "store-1",
                    "in_stock": 50,
                    "updated_at": "2026-05-26T10:00:00Z",
                }
            ]
        }
        response = InventoryListResponse.model_validate(data)
        assert len(response.items) == 1
        assert response.items[0].variant_id == "var-1"

    def test_inventory_list_response_multiple_items(self):
        """Test InventoryListResponse with multiple items."""
        data = {
            "inventory_levels": [
                {
                    "variant_id": "var-1",
                    "store_id": "store-1",
                    "in_stock": 10,
                    "updated_at": "2026-05-26T10:00:00Z",
                },
                {
                    "variant_id": "var-2",
                    "store_id": "store-1",
                    "in_stock": 20,
                    "updated_at": "2026-05-26T11:00:00Z",
                },
            ]
        }
        response = InventoryListResponse.model_validate(data)
        assert len(response.items) == 2
        assert response.items[0].in_stock == 10
        assert response.items[1].in_stock == 20

    def test_list_response_with_cursor(self):
        """Test InventoryListResponse exposes next_cursor from cursor field."""
        data = {
            "inventory_levels": [
                {
                    "variant_id": "var-1",
                    "store_id": "store-1",
                    "in_stock": 50,
                    "updated_at": "2026-05-26T10:00:00Z",
                }
            ],
            "cursor": "next-page-token",
        }
        response = InventoryListResponse.model_validate(data)
        assert response.next_cursor == "next-page-token"

    def test_list_response_without_cursor(self):
        """Test InventoryListResponse defaults next_cursor to None."""
        data = {
            "inventory_levels": [
                {
                    "variant_id": "var-1",
                    "store_id": "store-1",
                    "in_stock": 50,
                    "updated_at": "2026-05-26T10:00:00Z",
                }
            ]
        }
        response = InventoryListResponse.model_validate(data)
        assert response.next_cursor is None

    def test_inventory_list_response_inherits_pagination(self):
        """Test InventoryListResponse inherits from Pagination base."""
        from loyverse_sdk.models.common import Pagination

        assert issubclass(InventoryListResponse, Pagination)
