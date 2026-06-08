from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer

from loyverse_sdk.models.common import BaseListQuery, Pagination


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


class PosDeviceListQuery(BaseListQuery):
    store_id: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.store_id is not None:
            params["store_id"] = self.store_id
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
