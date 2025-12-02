from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field
from loyverse_api.models.common import Pagination


class PosDevice(BaseModel):
    id: UUID
    name: str
    store_id: UUID
    activated: bool = True
    deleted_at: datetime | None = None


class PosDeviceListResponse(Pagination):
    items: list[PosDevice] = Field(alias="pos_devices")
