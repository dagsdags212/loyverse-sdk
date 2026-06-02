from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.endpoints.mixins import (
    ListMixin,
    RetrieveMixin,
    PaginationMixin,
)
from loyverse_sdk.models import Shift, ShiftListQuery, ShiftListResponse


class ShiftsEndpoint(BaseEndpoint, ListMixin, RetrieveMixin, PaginationMixin):
    path = "shifts"

    async def list(self, query: ShiftListQuery | None = None):
        query = query or ShiftListQuery()
        return await super().list(model=ShiftListResponse, **query.to_params())

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=Shift)

    async def iter_all(self, query: ShiftListQuery | None = None):
        query = query or ShiftListQuery()
        async for item in super().iter_all(**query.to_params()):
            yield Shift.model_validate(item)
