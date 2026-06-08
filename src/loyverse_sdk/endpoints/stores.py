from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    PaginationMixin,
    RetrieveMixin,
)
from loyverse_sdk.models import Store, StoreListQuery, StoreListResponse


class StoresEndpoint(BaseEndpoint, RetrieveMixin, ListMixin, PaginationMixin):
    path = "stores"

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Store)

    async def list(self, query: StoreListQuery | None = None):
        query = query or StoreListQuery()
        return await super().list(model=StoreListResponse, **query.to_params())

    async def iter_all(self, query: StoreListQuery | None = None):
        query = query or StoreListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Store.model_validate(item)
