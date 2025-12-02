from uuid import UUID
from datetime import datetime
from typing import Iterable, Tuple, Literal
from pydantic import BaseModel, Field
from pydantic import NonNegativeFloat
from loyverse_api.models.common import Base, Pagination


class CashMovement(BaseModel):
    type: Literal["PAY_IN", "PAY_OUT"]
    money_amount: NonNegativeFloat
    comment: str | None = None
    employee_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)


class Shift(Base):
    store_id: UUID
    pos_device_id: UUID
    opened_at: datetime
    closed_at: datetime
    opened_by_employee: UUID
    closed_by_employee: UUID
    starting_cash: NonNegativeFloat | None = None
    cash_payments: NonNegativeFloat | None = None
    cash_refunds: NonNegativeFloat | None = None
    paid_in: NonNegativeFloat | None = None
    paid_out: NonNegativeFloat | None = None
    expected_cash: NonNegativeFloat
    actual_cash: NonNegativeFloat
    gross_sales: NonNegativeFloat
    refunds: NonNegativeFloat = 0.0
    discounts: NonNegativeFloat = 0.0
    net_sales: NonNegativeFloat
    tip: NonNegativeFloat = 0.0
    surcharge: NonNegativeFloat = 0.0
    taxes: Iterable[Tuple[UUID, NonNegativeFloat] | None] = []
    payments: Iterable[Tuple[UUID, NonNegativeFloat] | None] = []
    cash_movements: Iterable[CashMovement] = []


class ShiftListResponse(Pagination):
    items: list[Shift] = Field(alias="shifts")
