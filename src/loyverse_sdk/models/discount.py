from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, field_serializer, model_validator

from loyverse_sdk.models.common import Base, BaseListQuery, Pagination


class DiscountType(StrEnum):
    FIXED_PERCENT = "FIXED_PERCENT"
    FIXED_AMOUNT = "FIXED_AMOUNT"
    VARIABLE_PERCENT = "VARIABLE_PERCENT"
    VARIABLE_AMOUNT = "VARIABLE_AMOUNT"
    DISCOUNT_BY_POINTS = "DISCOUNT_BY_POINTS"


class Discount(Base):
    type: DiscountType
    name: str
    discount_amount: float | None = Field(default=None, ge=0.0)
    discount_percent: float | None = Field(default=None, ge=0.0, le=100.0)
    stores: list[UUID]
    restricted_access: bool = False

    @model_validator(mode="after")
    def validate_discount_amount(self) -> Self:
        if self.type == DiscountType.FIXED_AMOUNT:
            if self.discount_amount is None:
                raise ValueError("discount_amount required but not provided")
        if self.type != DiscountType.FIXED_AMOUNT:
            self.discount_amount = None
        return self

    @model_validator(mode="after")
    def validate_discount_percent(self) -> Self:
        if self.type == DiscountType.FIXED_PERCENT:
            if self.discount_percent is None:
                raise ValueError("discount_percent required but not provided")
        if self.type != DiscountType.FIXED_PERCENT:
            self.discount_percent = None
        return self

    @field_serializer("stores", mode="plain")
    def serialize_store_uuids(self, value: list[UUID]) -> list[str]:
        return [str(id) for id in value]

    def list_valid_discount_types(self) -> list:
        return list(DiscountType)


class DiscountListResponse(Pagination):
    items: list[Discount] = Field(alias="discounts")


class DiscountListQuery(BaseListQuery):
    discount_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.discount_ids is not None:
            params["discount_ids"] = self.discount_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
