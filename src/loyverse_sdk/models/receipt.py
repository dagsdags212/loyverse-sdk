from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator

from loyverse_sdk.models.common import Base, BaseListQuery, Pagination

# =============================================================================
# Payment Type
# =============================================================================


class PaymentType(Base):
    """Payment type model for POS transactions."""

    # Override Base fields - API uses string IDs
    id: str | None = Field(default=None)
    name: str
    type: str = "CASH"
    stores: list[UUID] = Field(default_factory=list)

    @field_validator("type", mode="before")
    def uppercase_type(cls, value: str) -> str:
        return value.upper()


class PaymentTypeListResponse(Pagination):
    items: list[PaymentType] = Field(alias="payment_types")


class PaymentTypeListQuery(BaseListQuery):
    payment_type_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.payment_type_ids is not None:
            params["payment_type_ids"] = self.payment_type_ids
        if self.show_deleted is not None:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params


# =============================================================================
# Line Item Nested Models
# =============================================================================


class LineItemTax(BaseModel):
    """Tax applied to a line item."""

    money_amount: float
    id: str
    type: str
    name: str
    rate: float | None = None


class LineItemDiscount(BaseModel):
    """Discount applied to a line item."""

    id: str
    type: str
    name: str
    money_amount: float
    percentage: float | None = None


class LineItemModifier(BaseModel):
    """Modifier applied to a line item (e.g., toppings)."""

    id: str
    modifier_option_id: str | None = None
    name: str
    option: str | None = None
    price: float | None = None
    money_amount: float = 0.0


class LineItem(BaseModel):
    """Line item within a receipt."""

    id: str
    item_id: str
    variant_id: str | None = None
    item_name: str
    variant_name: str | None = None
    sku: str | None = None
    quantity: float
    price: float
    gross_total_money: float = 0.0
    total_money: float
    cost: float | None = None
    cost_total: float | None = None
    line_note: str | None = None
    line_taxes: list[LineItemTax] = Field(default_factory=list)
    total_discount: float = 0.0
    line_discounts: list[LineItemDiscount] = Field(default_factory=list)
    line_modifiers: list[LineItemModifier] = Field(default_factory=list)


# =============================================================================
# Receipt Nested Models
# =============================================================================


class TotalDiscount(BaseModel):
    """Discount applied to entire receipt."""

    id: str
    type: str
    name: str
    percentage: float | None = None
    money_amount: float


class TotalTax(BaseModel):
    """Tax applied to entire receipt."""

    id: str
    type: str
    name: str
    rate: float | None = None
    money_amount: float


class PaymentDetail(BaseModel):
    """Additional payment details (e.g., card info)."""

    authorization_code: str | None = None
    reference_id: int | str | None = None
    entry_method: str | None = None
    card_company: str | None = None
    card_number: str | None = None


class Payment(BaseModel):
    """Payment for a receipt."""

    payment_type_id: str
    name: str
    type: str
    money_amount: float
    paid_at: datetime | None = None
    payment_details: PaymentDetail | None = None


# =============================================================================
# Receipt
# =============================================================================


class Receipt(Base):
    """Loyverse receipt model."""

    # Primary identifier - field name in API JSON
    receipt_number: str
    note: str | None = None
    receipt_type: str
    refund_for: str | None = None
    order_id: str | None = None
    # Override Base defaults to allow None
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    source: str | None = None
    receipt_date: datetime | None = None
    cancelled_at: datetime | None = None

    # Financial totals
    total_money: float
    total_tax: float = 0.0
    points_earned: float = 0.0
    points_deducted: float = 0.0
    points_balance: float = 0.0
    total_discount: float = 0.0
    tip: float = 0.0
    surcharge: float = 0.0

    # References
    customer_id: str | None = None
    employee_id: str | None = None
    store_id: str | None = None
    pos_device_id: str | None = None
    dining_option: str | None = None

    # Nested arrays
    total_discounts: list[TotalDiscount] = Field(default_factory=list)
    total_taxes: list[TotalTax] = Field(default_factory=list)
    line_items: list[LineItem] = Field(default_factory=list)
    payments: list[Payment] = Field(default_factory=list)

    @field_validator("receipt_type", mode="before")
    def uppercase_receipt_type(cls, value: str | None) -> str | None:
        if value:
            return value.upper()
        return value

    @field_serializer(
        "customer_id", "employee_id", "store_id", "pos_device_id", mode="plain"
    )
    def serialize_uuids(self, value: str | None) -> str | None:
        return value


class ReceiptListResponse(Pagination):
    items: list[Receipt] = Field(alias="receipts")


class ReceiptListQuery(BaseListQuery):
    """Query parameters for GET /receipts."""

    receipt_numbers: str | None = None
    since_receipt_number: str | None = None
    before_receipt_number: str | None = None
    store_id: str | None = None
    sort_order: str | None = None  # 'asc' or 'desc' for sorting results
    order_id: str | None = None  # Filter by order reference

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
        if self.sort_order is not None:
            params["order"] = self.sort_order
        if self.order_id is not None:
            params["order"] = self.order_id
        return params
