from datetime import datetime
from enum import StrEnum
from uuid import UUID
from pydantic import BaseModel, Field
from loyverse_sdk.models.common import Pagination, BaseListQuery


class WebhookType(StrEnum):
    INVENTORY_LEVELS_UPDATE = "inventory_levels.update"
    ITEMS_UPDATE = "items.update"
    CUSTOMERS_UPDATE = "customers.update"
    RECEIPTS_UPDATE = "receipts.update"
    SHIFTS_CREATE = "shifts.create"


class WebhookStatus(StrEnum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"


class Webhook(BaseModel):
    id: UUID
    merchant_id: UUID
    url: str
    type: WebhookType
    status: WebhookStatus = WebhookStatus.ENABLED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class WebhookListResponse(Pagination):
    items: list[Webhook] = Field(alias="webhooks")


class WebhookListQuery(BaseListQuery):
    id: str | None = None
    merchant_id: str | None = None
    url: str | None = None
    type: WebhookType | None = None
    status: WebhookStatus | None = None

    def to_params(self) -> dict:
        params = super().to_params()
        if self.id is not None:
            params["id"] = self.id
        if self.merchant_id is not None:
            params["merchant_it"] = self.merchant_id
        if self.url is not None:
            params["url"] = self.url
        if self.type is not None:
            params["type"] = self.type.value
        if self.status is not None:
            params["status"] = self.status.value
        return params
