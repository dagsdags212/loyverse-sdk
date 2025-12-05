from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Supplier, SupplierListResponse


class SuppliersEndpoint(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "suppliers"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Supplier)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Supplier)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Supplier)

    async def list(self, limit: int = config.PAGE_LIMIT, cursor: str | None = None):
        return await super().list(
            limit=limit, cursor=cursor, model=SupplierListResponse
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Supplier.model_validate(item)
