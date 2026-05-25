from datetime import datetime
from pydantic import BaseModel, Field, field_validator, field_serializer


class Inventory(BaseModel):
    """Inventory item stock levels per variant per store"""

    variant_id: str
    store_id: str
    in_stock: int = 0
    updated_at: datetime

    @field_validator("updated_at", mode="after")
    def utc_to_local(cls, value: datetime) -> datetime:
        if value:
            import pytz
            from loyverse_sdk.core.config import config

            _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
            local_tz = pytz.timezone(_tz)
            local_dt = value.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_dt
        return value

    @field_serializer("variant_id", "store_id", mode="plain")
    def serialize_str(self, value: str) -> str:
        return value


class InventoryListResponse(BaseModel):
    inventory: list[Inventory]
