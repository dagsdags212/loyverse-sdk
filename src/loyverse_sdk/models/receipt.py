from uuid import UUID
from datetime import datetime
from pydantic import Field, field_validator
from pydantic import NonNegativeFloat
from loyverse_sdk.models.common import Base, Pagination


class PaymentType(Base):
    name: str
    type: str = "CASH"
    stores: list[UUID]

    @field_validator("type", mode="before")
    def uppercase_type(cls, value: str) -> str:
        return value.upper()


class PaymentTypeListReponse(Pagination):
    items: list[PaymentType] = Field(alias="payment_types")


class Receipt(Base):
    id: str = Field(alias="receipt_number")
    note: str | None = Field(default=None, exclude=True)
    receipt_type: str
    refund_for: str | None = None
    order: str | None = None
    source: str | None = None
    total_amount: NonNegativeFloat = Field(alias="total_money", ge=0.0)
    total_tax: NonNegativeFloat = 0.0
    line_items: str
    points_earned: NonNegativeFloat = 0.0
    points_deducted: NonNegativeFloat = 0.0
    points_balance: NonNegativeFloat
    total_discount: NonNegativeFloat = 0.0
    surcharge: NonNegativeFloat = 0.0
    tip: NonNegativeFloat = 0.0
    customer_id: UUID | None = None
    employee_id: UUID
    store_id: UUID
    pos_device_id: UUID
    payment_type_id: UUID = Field(alias="payments")
    cancelled_at: datetime | None = None

    @field_validator("line_items", mode="before")
    def serialize_items(cls, values) -> str:
        orders = []
        for item in values:
            orders.append(
                f"{item['quantity']}x{item['item_name']}@{item['price']}/unit"
            )

        return ",".join(orders)

    @field_validator("payment_type_id", mode="before")
    def extract_payment_type_id(cls, value) -> UUID:
        if isinstance(value, list):
            return UUID(value[0]["payment_type_id"])
        return value


class ReceiptListResponse(Pagination):
    items: list[Receipt] = Field(alias="receipts")
