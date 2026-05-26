from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from loyverse_sdk.models.common import Pagination, BaseListQuery


class Inventory(BaseModel):
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


class InventoryListResponse(Pagination):
    items: list[Inventory] = Field(alias="inventory_levels")


class InventoryListQuery(BaseListQuery):
    store_ids: str | None = None
    variant_ids: str | None = None

    def to_params(self) -> dict:
        params = super().to_params()
        if self.store_ids is not None:
            params["store_ids"] = self.store_ids
        if self.variant_ids is not None:
            params["variant_ids"] = self.variant_ids
        return params
