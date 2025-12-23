from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Receipt, ReceiptListResponse


class ReceiptsEndpoint(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "receipts"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=Receipt)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Receipt)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=Receipt)

    async def list(
        self, *,
        limit: int = config.PAGE_LIMIT,
        cursor: str | None = None,
        **kwargs,
    ):
        return await super().list(
            limit=limit,
            cursor=cursor,
            model=ReceiptListResponse,
            **kwargs
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield Receipt.model_validate(item)
