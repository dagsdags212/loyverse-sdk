from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, field_serializer
from pydantic import NonNegativeFloat, NonNegativeInt
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


class LineItem(BaseModel):
    """A single line item purchased by a client"""

    id: UUID
    item_id: UUID
    variant_id: UUID
    name: str
    sku: str
    cost: NonNegativeFloat
    quantity: NonNegativeInt
    price: NonNegativeFloat

    def serialize(self) -> str:
        return f"{self.quantity}x{self.name}@{self.price}"

    def total_cost(self, precision: int = 2) -> float:
        """Computes the total cost of a line item.""" 
        precision = precision if precision >= 0 else 2
        return round(self.quantity * self.price, precision)

    def net_profit(self, precision: int = 2) -> float:
        """Compute the net profit gained from selling the item."""
        precision = precision if precision >= 0 else 2
        profit = self.total_cost(precision) - self.cost
        return round(profit, precision)

    @field_serializer("id", "item_id", "variant_id", mode="plain")
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class Receipt(Base):
    id: str = Field(alias="receipt_number")
    note: str | None = None
    receipt_type: str
    refund_for: str | None = None
    order: str | None = None
    receipt_date: datetime
    source: str | None = None
    total_amount: NonNegativeFloat = Field(alias="total_money")
    total_tax: NonNegativeFloat = 0.0
    points_earned: NonNegativeFloat = 0.0
    points_deducted: NonNegativeFloat = 0.0
    points_balance: NonNegativeFloat
    total_discount: NonNegativeFloat = 0.0
    line_items: list[LineItem]
    customer_id: UUID | None = None
    employee_id: UUID
    store_id: UUID
    pos_device_id: UUID
    total_discounts: list[dict] = []
    total_taxes: list[dict] = []
    surcharge: NonNegativeFloat = 0.0
    tip: NonNegativeFloat = 0.0
    payment_type_id: UUID | str = Field(alias="payments")
    cancelled_at: datetime | None = None

    @field_validator("line_items", mode="before")
    def serialize_items(cls, values) -> list[LineItem]:
        return [
            LineItem(
                id=item['id'],
                item_id=item['item_id'],
                variant_id=item['variant_id'],
                name=item['item_name'],
                sku=item['sku'],
                cost=item['cost'],
                price=item['price'],
                quantity=item['quantity']
            ) for item in values
        ]

    @field_serializer("line_items", mode="plain")
    def serialize_line_items(self, value: list[LineItem]) -> str:
        return ','.join([li.serialize() for li in value])

    @field_validator("payment_type_id", mode="before")
    def extract_payment_type_id(cls, value) -> UUID:
        if isinstance(value, list):
            return UUID(value[0]["payment_type_id"])
        return value

    @field_serializer(
        "customer_id", "employee_id", "store_id",
        "pos_device_id", "payment_type_id", mode="plain")
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class ReceiptListResponse(Pagination):
    items: list[Receipt] = Field(alias="receipts")
