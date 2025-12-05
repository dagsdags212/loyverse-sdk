from loyverse_sdk.endpoints.base import BaseEndpoint
from loyverse_sdk.core.config import config
from loyverse_sdk.endpoints.mixins import (
    CrudMixin,
    ListMixin,
    PaginationMixin,
)
from loyverse_sdk.models import PosDevice, PosDeviceListResponse


class PosDevicesEndpoints(BaseEndpoint, CrudMixin, ListMixin, PaginationMixin):
    path = "pos_devices"

    async def create(self, payload: dict):
        return await super().create(payload=payload, model=PosDevice)

    async def retrieve(self, id: str):
        return await super().retrieve(id, model=PosDevice)

    async def update(self, id: str, payload: dict):
        return await super().update(id=id, payload=payload, model=PosDevice)

    async def list(self, limit: int = config.PAGE_LIMIT, cursor: str | None = None):
        return await super().list(
            limit=limit, cursor=cursor, model=PosDeviceListResponse
        )

    async def iter_all(self, **kwargs):
        async for item in super().iter_all(**kwargs):
            yield PosDevice.model_validate(item)
