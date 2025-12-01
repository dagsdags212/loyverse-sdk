from uuid import UUID
from datetime import datetime
from pydantic import Field, field_validator
from loyverse_api.models.base import Base


class PaymentType(Base):
    name: str
    type: str
    stores: list[UUID]


class Discount(Base):
    name: str
    type: str | None = None
    discount_amount: float = 0.0
    discount_percent: float | None = Field(default=0.0, ge=0.0, le=100.0)
    stores: list[UUID] = []
    restricted_access: bool = False

    @field_validator("stores", mode="before")
    def serialize_store_ids(cls, values: list[str]) -> str:
        return ",".join(values)


class Receipt(Base):
    id: str = Field(alias="receipt_number")
    note: str | None = Field(default=None, exclude=True)
    receipt_type: str = Field(default="SALE")
    refund_for: str | None = None
    order: str | None = None
    source: str | None = None
    total_amount: float = Field(alias="total_money")
    total_tax: float = 0.0
    line_items: str
    points_earned: float = 0.0
    points_deducted: float = 0.0
    points_balance: float
    total_discount: float = 0.0
    surchage: float = 0.0
    tip: float = 0.0
    customer_id: UUID | None = None
    employee_id: UUID
    store_id: UUID
    pos_device_id: UUID
    payment_type_id: UUID = Field(alias="payments")
    cancelled_at: datetime | None = None

    @field_validator("line_items", mode="before")
    def concat_items(cls, values) -> str:
        orders = []
        for item in values:
            orders.append(
                f"{item['quantity']}x{item['item_name']}@{item['price']}/unit"
            )

        return ",".join(orders)

    @field_validator("payment_type_id", mode="before")
    def extract_payment_type_id(cls, value) -> UUID:
        return UUID(value[0]["payment_type_id"])
