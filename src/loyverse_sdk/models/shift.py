from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from loyverse_sdk.models.common import BaseListQuery


class ShiftListQuery(BaseListQuery):
    """Query parameters for GET /shifts."""

    pass


class Shift(BaseModel):
    """Employee work shift with POS device cashup"""

    id: str
    store_id: str
    pos_device_id: str
    opened_at: datetime
    closed_at: datetime | None = None
    opened_by_employee: str
    closed_by_employee: str | None = None
    starting_cash: float = 0.0
    cash_payments: float = 0.0
    cash_refunds: float = 0.0
    paid_in: float = 0.0
    paid_out: float = 0.0
    expected_cash: float = 0.0
    actual_cash: float = 0.0
    gross_sales: float = 0.0
    refunds: float = 0.0
    discounts: float = 0.0
    net_sales: float = 0.0
    tip: float = 0.0
    surcharge: float = 0.0
    taxes: list[dict[str, Any]] = Field(default_factory=list)
    payments: list[dict[str, Any]] = Field(default_factory=list)
    cash_movements: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("opened_at", "closed_at", mode="after")
    def utc_to_local(cls, value: datetime | None) -> datetime | None:
        if value:
            import pytz

            from loyverse_sdk.core.config import config

            _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
            local_tz = pytz.timezone(_tz)
            local_dt = value.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_dt
        return value


class ShiftListResponse(BaseModel):
    shifts: list[Shift] = Field(alias="shifts")
