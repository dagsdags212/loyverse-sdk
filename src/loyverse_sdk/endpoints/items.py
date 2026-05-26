from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    RetrieveMixin,
    PaginationMixin,
    CreateMixin,
    UpdateMixin,
)
from loyverse_sdk.models import Item, ItemListResponse


class ItemsEndpoint(
    BaseEndpoint, ListMixin, RetrieveMixin, PaginationMixin, CreateMixin, UpdateMixin
):
    path = "items"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Item)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Item)

    # TODO: upload single image using /items/{item_id}/image endpoint
    # TODO: delete single image using /items/{item_id}/image endpoint

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Item)

    async def list(self, limit: int = 100, cursor: str | None = None):
        return await super().list(limit=limit, cursor=cursor, model=ItemListResponse)

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Item.model_validate(item)
