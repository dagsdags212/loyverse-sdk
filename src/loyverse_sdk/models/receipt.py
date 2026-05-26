from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, field_serializer
from pydantic import NonNegativeFloat, NonNegativeInt
from loyverse_sdk.models.common import Base, Pagination, BaseListQuery


class PaymentType(Base):
    name: str
    type: str = "CASH"
    stores: list[UUID]

    @field_validator("type", mode="before")
    def uppercase_type(cls, value: str) -> str:
        return value.upper()


class PaymentTypeListReponse(Pagination):
    items: list[PaymentType] = Field(alias="payment_types")


class PaymentTypeListQuery(BaseListQuery):
    payment_type_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.payment_type_ids is not None:
            params["payment_type_ids"] = self.payment_type_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params


class LineItem(BaseModel):
    id: UUID
    item_id: UUID
    variant_id: UUID
    name: str
    sku: str
    cost: NonNegativeFloat
    quantity: NonNegativeInt
    price: NonNegativeFloat

    def serialize(self, json: bool = True) -> str:
        if json:
            return dict(
                id=str(self.item_id),
                item_name=self.name,
                quantity=self.quantity,
                price=self.price,
            )
        return f"{self.quantity}x{self.name}@{self.price}"

    def total_cost(self, precision: int = 2) -> float:
        precision = precision if precision >= 0 else 2
        return round(self.quantity * self.price, precision)

    def net_profit(self, precision: int = 2) -> float:
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
                id=item["id"],
                item_id=item["item_id"],
                variant_id=item["variant_id"],
                name=item["item_name"],
                sku=item["sku"],
                cost=item["cost"],
                price=item["price"],
                quantity=item["quantity"],
            )
            for item in values
        ]

    @field_serializer("line_items", mode="plain")
    def serialize_line_items(self, value: list[LineItem]) -> str:
        return [li.serialize(json=True) for li in value]

    @field_validator("payment_type_id", mode="before")
    def extract_payment_type_id(cls, value) -> UUID:
        if isinstance(value, list):
            return UUID(value[0]["payment_type_id"])
        return value

    @field_serializer(
        "customer_id",
        "employee_id",
        "store_id",
        "pos_device_id",
        "payment_type_id",
        mode="plain",
    )
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class ReceiptListResponse(Pagination):
    items: list[Receipt] = Field(alias="receipts")


class ReceiptListQuery(BaseListQuery):
    receipt_numbers: str | None = None
    since_receipt_number: str | None = None
    before_receipt_number: str | None = None
    store_id: str | None = None
    order: str | None = None

    def to_params(self) -> dict:
        params = super().to_params()
        if self.receipt_numbers is not None:
            params["receipt_numbers"] = self.receipt_numbers
        if self.since_receipt_number is not None:
            params["since_receipt_number"] = self.since_receipt_number
        if self.before_receipt_number is not None:
            params["before_receipt_number"] = self.before_receipt_number
        if self.store_id is not None:
            params["store_id"] = self.store_id
        if self.order is not None:
            params["order"] = self.order
        return params
