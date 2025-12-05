from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Customer, CustomerListResponse


class CustomersEndpoint(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "customers"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Customer)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Customer)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Customer)

    async def list(self, limit: int = config.PAGE_LIMIT, cursor: str | None = None):
        return await super().list(
            limit=limit, cursor=cursor, model=CustomerListResponse
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Customer.model_validate(item)
