"""
Unit tests for loyverse_sdk.endpoints.inventory module.
"""

import pytest
import inspect
from unittest.mock import AsyncMock, MagicMock
from loyverse_sdk.endpoints.inventory import InventoryEndpoint
from loyverse_sdk.endpoints.mixins import RetrieveMixin


class TestInventoryEndpoint:
    """Test InventoryEndpoint structure and behavior."""

    def test_no_retrieve_method(self):
        """Inventory endpoint should NOT expose retrieve() — no GET /inventory/{id}."""
        client = MagicMock()
        client.request = AsyncMock()
        endpoint = InventoryEndpoint(client)

        # Verify RetrieveMixin is not in the class MRO
        assert RetrieveMixin not in type(endpoint).__mro__, (
            "RetrieveMixin should not be in InventoryEndpoint MRO"
        )

    def test_list_signature_has_filter_params(self):
        """list() should accept store_id and variant_ids filter params."""
        sig = inspect.signature(InventoryEndpoint.list)
        assert "store_id" in sig.parameters, (
            "store_id parameter missing from InventoryEndpoint.list()"
        )
        assert "variant_ids" in sig.parameters, (
            "variant_ids parameter missing from InventoryEndpoint.list()"
        )

    @pytest.mark.asyncio
    async def test_list_forwards_store_id_filter(self):
        """list(store_id=...) should pass store_id as query param to API."""
        client = MagicMock()
        client.request = AsyncMock(
            return_value={
                "inventory_levels": [],
                "cursor": None,
            }
        )
        endpoint = InventoryEndpoint(client)

        await endpoint.list(store_id="store-abc")

        call_args = client.request.call_args
        # Verify the API call was made with correct params
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "inventory"
        assert "store_id" in str(call_args[1].get("params", {}))

    @pytest.mark.asyncio
    async def test_list_forwards_variant_ids_filter(self):
        """list(variant_ids=...) should pass variant_ids as query param to API."""
        client = MagicMock()
        client.request = AsyncMock(
            return_value={
                "inventory_levels": [],
                "cursor": None,
            }
        )
        endpoint = InventoryEndpoint(client)

        await endpoint.list(variant_ids="var-1,var-2")

        call_args = client.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "inventory"
        assert "variant_ids" in str(call_args[1].get("params", {}))

    @pytest.mark.asyncio
    async def test_list_no_filters_works(self):
        """list() without filters should still work."""
        client = MagicMock()
        client.request = AsyncMock(
            return_value={
                "inventory_levels": [],
                "cursor": None,
            }
        )
        endpoint = InventoryEndpoint(client)

        await endpoint.list()

        call_args = client.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "inventory"
