from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Discount, DiscountListQuery, DiscountListResponse


class DiscountsEndpoint(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "discounts"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Discount)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Discount)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Discount)

    async def list(self, query: DiscountListQuery | None = None):
        query = query or DiscountListQuery()
        return await super().list(model=DiscountListResponse, **query.to_params())

    async def iter_all(self, query: DiscountListQuery | None = None):
        query = query or DiscountListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Discount.model_validate(item)
