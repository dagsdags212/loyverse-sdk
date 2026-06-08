from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    CreateMixin,
    ListMixin,
    PaginationMixin,
    RetrieveMixin,
    UpdateMixin,
)
from loyverse_sdk.models import Item, ItemListQuery, ItemListResponse


class ItemsEndpoint(
    BaseEndpoint, ListMixin, RetrieveMixin, PaginationMixin, CreateMixin, UpdateMixin
):
    path = "items"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Item)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Item)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Item)

    async def list(self, query: ItemListQuery | None = None):
        query = query or ItemListQuery()
        return await super().list(model=ItemListResponse, **query.to_params())

    async def iter_all(self, query: ItemListQuery | None = None):
        query = query or ItemListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Item.model_validate(item)
