"""Unit tests for the endpoint CRUD/pagination mixins.

These build a throwaway endpoint composed of ``BaseEndpoint`` and the mixins,
backed by a mock client whose ``request`` is an ``AsyncMock``, so every HTTP
verb wrapper and the cursor-pagination generator are exercised directly.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.exceptions import PaginationError, ValidationError


class Widget(BaseModel):
    id: str
    name: str


class WidgetEndpoint(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "widgets"


def make_endpoint(return_value=None, *, side_effect=None):
    client = Mock()
    client.request = AsyncMock(return_value=return_value, side_effect=side_effect)
    return WidgetEndpoint(client), client


class TestListMixin:
    @pytest.mark.asyncio
    async def test_list_returns_raw_dict(self):
        ep, client = make_endpoint({"widgets": []})
        result = await ep.list()
        assert result == {"widgets": []}
        client.request.assert_awaited_once_with("GET", "widgets", params={})

    @pytest.mark.asyncio
    async def test_list_with_model_validates(self):
        ep, _ = make_endpoint({"id": "w1", "name": "Widget"})
        result = await ep.list(model=Widget)
        assert isinstance(result, Widget)
        assert result.id == "w1"

    @pytest.mark.asyncio
    async def test_list_with_model_raises_validation_error(self):
        ep, _ = make_endpoint({"id": "w1"})  # missing 'name'
        with pytest.raises(ValidationError):
            await ep.list(model=Widget)


class TestRetrieveMixin:
    @pytest.mark.asyncio
    async def test_retrieve_builds_path_with_id(self):
        ep, client = make_endpoint({"id": "w1", "name": "Widget"})
        await ep.retrieve("w1")
        client.request.assert_awaited_once_with("GET", "widgets/w1")

    @pytest.mark.asyncio
    async def test_retrieve_with_model(self):
        ep, _ = make_endpoint({"id": "w1", "name": "Widget"})
        result = await ep.retrieve("w1", model=Widget)
        assert isinstance(result, Widget)


class TestCreateMixin:
    @pytest.mark.asyncio
    async def test_create_from_dict(self):
        ep, client = make_endpoint({"id": "w1", "name": "Widget"})
        await ep.create({"name": "Widget"})
        client.request.assert_awaited_once_with(
            "POST", "widgets", json={"name": "Widget"}
        )

    @pytest.mark.asyncio
    async def test_create_from_model_dumps_payload(self):
        ep, client = make_endpoint({"id": "w1", "name": "Widget"})
        await ep.create(Widget(id="w1", name="Widget"))
        _, kwargs = client.request.await_args
        assert kwargs["json"] == {"id": "w1", "name": "Widget"}

    @pytest.mark.asyncio
    async def test_create_with_model_validates_response(self):
        ep, _ = make_endpoint({"id": "w1", "name": "Widget"})
        result = await ep.create({"name": "Widget"}, model=Widget)
        assert isinstance(result, Widget)


class TestUpdateMixin:
    @pytest.mark.asyncio
    async def test_update_injects_id_into_payload(self):
        ep, client = make_endpoint({"id": "w1", "name": "New"})
        await ep.update("w1", {"name": "New"})
        _, kwargs = client.request.await_args
        assert kwargs["json"] == {"name": "New", "id": "w1"}


class TestDeleteMixin:
    @pytest.mark.asyncio
    async def test_delete_calls_delete_verb(self):
        ep, client = make_endpoint({})
        await ep.delete("w1")
        client.request.assert_awaited_once_with("DELETE", "widgets/w1")


class TestPaginationMixin:
    @pytest.mark.asyncio
    async def test_iter_all_yields_across_pages(self):
        pages = [
            {"widgets": [{"id": "1"}, {"id": "2"}], "cursor": "c1"},
            {"widgets": [{"id": "3"}], "cursor": None},
        ]
        ep, _ = make_endpoint(side_effect=pages)

        items = [item async for item in ep.iter_all()]

        assert [i["id"] for i in items] == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_iter_all_raises_on_non_dict_response(self):
        ep, _ = make_endpoint(side_effect=[["not", "a", "dict"]])
        with pytest.raises(PaginationError):
            [item async for item in ep.iter_all()]

    @pytest.mark.asyncio
    async def test_iter_all_raises_on_missing_key(self):
        ep, _ = make_endpoint(side_effect=[{"cursor": None}])
        with pytest.raises(PaginationError):
            [item async for item in ep.iter_all()]

    @pytest.mark.asyncio
    async def test_iter_all_raises_on_non_list_records(self):
        ep, _ = make_endpoint(side_effect=[{"widgets": "nope"}])
        with pytest.raises(PaginationError):
            [item async for item in ep.iter_all()]

    @pytest.mark.asyncio
    async def test_iter_all_detects_cursor_loop(self):
        pages = [
            {"widgets": [{"id": "1"}], "cursor": "dup"},
            {"widgets": [{"id": "2"}], "cursor": "dup"},
        ]
        ep, _ = make_endpoint(side_effect=pages)
        with pytest.raises(PaginationError):
            [item async for item in ep.iter_all()]
