from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_serializer
from loyverse_sdk.models.common import Pagination


class PosDevice(BaseModel):
    id: UUID
    name: str
    store_id: UUID
    activated: bool = True
    deleted_at: datetime | None = None

    @field_serializer("id", mode="plain")
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class PosDeviceListResponse(Pagination):
    items: list[PosDevice] = Field(alias="pos_devices")
