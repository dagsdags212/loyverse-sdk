"""
Unit tests for loyverse_sdk.endpoints.inventory module.

Tests endpoint structure, method contracts, and filter parameter forwarding
without real API calls.
"""

import pytest
import inspect
from unittest.mock import AsyncMock, MagicMock
from loyverse_sdk.endpoints.inventory import InventoryEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    RetrieveMixin,
    PaginationMixin,
)
from loyverse_sdk.endpoints.base import BaseEndpoint


class TestInventoryEndpointStructure:
    """Test InventoryEndpoint class structure and MRO."""

    def test_inherits_correct_mixins(self):
        """InventoryEndpoint should inherit ListMixin and PaginationMixin but NOT RetrieveMixin."""
        mro = InventoryEndpoint.__mro__
        assert BaseEndpoint in mro, "Should inherit BaseEndpoint"
        assert ListMixin in mro, "Should inherit ListMixin"
        assert PaginationMixin in mro, "Should inherit PaginationMixin"
        assert RetrieveMixin not in mro, "Should NOT inherit RetrieveMixin"

    def test_no_retrieve_method(self):
        """InventoryEndpoint should NOT have a retrieve() method."""
        client = MagicMock()
        client.request = AsyncMock()
        endpoint = InventoryEndpoint(client)

        with pytest.raises(AttributeError):
            endpoint.retrieve("some-id")

    def test_path_is_inventory(self):
        """Endpoint path should be 'inventory'."""
        client = MagicMock()
        client.request = AsyncMock()
        endpoint = InventoryEndpoint(client)
        assert endpoint.path == "inventory"

    def test_items_key_is_inventory_levels(self):
        """Items key should be 'inventory_levels' for pagination."""
        client = MagicMock()
        client.request = AsyncMock()
        endpoint = InventoryEndpoint(client)
        assert endpoint.items_key == "inventory_levels"


class TestInventoryEndpointListSignature:
    """Test the list() method signature uses a query model."""

    def test_list_accepts_query_param(self):
        """list() should accept an optional query parameter."""
        sig = inspect.signature(InventoryEndpoint.list)
        assert "query" in sig.parameters
        param = sig.parameters["query"]
        assert param.default is None, "query should default to None"


class TestInventoryEndpointHasIterAll:
    """Test that iter_all is available (from PaginationMixin)."""

    def test_iter_all_exists(self):
        """iter_all should be callable."""
        client = MagicMock()
        client.request = AsyncMock()
        endpoint = InventoryEndpoint(client)
        assert callable(endpoint.iter_all)

    def test_iter_all_is_async_generator(self):
        """iter_all should be an async generator function."""
        assert inspect.isasyncgenfunction(InventoryEndpoint.iter_all)


class TestInventoryEndpointFilterForwarding:
    """Test filter parameter forwarding via query model."""

    @pytest.mark.asyncio
    async def test_list_forwards_store_id_filter(self):
        """list(store_ids=...) should pass store_ids as query param to API."""
        from loyverse_sdk.models import InventoryListQuery

        client = MagicMock()
        client.request = AsyncMock(
            return_value={
                "inventory_levels": [],
                "cursor": None,
            }
        )
        endpoint = InventoryEndpoint(client)

        query = InventoryListQuery(store_ids="store-abc")
        await endpoint.list(query)

        call_args = client.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "inventory"
        assert "store_ids" in str(call_args[1].get("params", {}))

    @pytest.mark.asyncio
    async def test_list_forwards_variant_ids_filter(self):
        """list(variant_ids=...) should pass variant_ids as query param to API."""
        from loyverse_sdk.models import InventoryListQuery

        client = MagicMock()
        client.request = AsyncMock(
            return_value={
                "inventory_levels": [],
                "cursor": None,
            }
        )
        endpoint = InventoryEndpoint(client)

        query = InventoryListQuery(variant_ids="var-1,var-2")
        await endpoint.list(query)

        call_args = client.request.call_args
        assert call_args[0][0] == "GET"
        assert call_args[0][1] == "inventory"
        assert "variant_ids" in str(call_args[1].get("params", {}))

    @pytest.mark.asyncio
    async def test_list_no_filters_works(self):
        """list() without query should default to InventoryListQuery()."""
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
