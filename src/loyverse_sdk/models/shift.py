from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, field_serializer
from loyverse_sdk.models.common import Pagination


class Shift(BaseModel):
    """Employee shift/work period"""

    id: UUID = Field(default_factory=uuid4)
    employee_id: UUID
    start_time: datetime
    end_time: datetime | None = None
    opening_amount: Decimal = Field(default=Decimal("0"))
    closing_amount: Decimal = Field(default=Decimal("0"))
    cash_sales: Decimal = Field(default=Decimal("0"))
    card_sales: Decimal = Field(default=Decimal("0"))
    returned_amount: Decimal = Field(default=Decimal("0"))
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None

    @field_serializer(
        "id",
        "employee_id",
        "opening_amount",
        "closing_amount",
        "cash_sales",
        "card_sales",
        "returned_amount",
        mode="plain",
    )
    def serialize_fields(self, value):
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, Decimal):
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


class ShiftListResponse(Pagination):
    items: list[Shift] = Field(alias="shifts")
