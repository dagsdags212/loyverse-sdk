from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, field_serializer
from loyverse_sdk.models.common import Pagination


class Inventory(BaseModel):
    """Inventory item stock levels across warehouses"""

    id: UUID = Field(default_factory=uuid4)
    item_id: UUID
    warehouse_id: UUID
    available: int = 0
    committed: int = 0
    damaged: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    @field_serializer("id", "item_id", "warehouse_id", mode="plain")
    def serialize_uuid(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_validator("created_at", "updated_at", "deleted_at", mode="after")
    def utc_to_local(cls, value: datetime | None) -> datetime | None:
        if value:
            import pytz
            from loyverse_sdk.core.config import config

            _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
            local_tz = pytz.timezone(_tz)
            local_dt = value.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_dt
        return value


class InventoryListResponse(Pagination):
    items: list[Inventory] = Field(alias="inventory")
