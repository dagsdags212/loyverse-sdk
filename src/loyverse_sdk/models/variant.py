from uuid import UUID
from pydantic import Field, NonNegativeFloat, field_serializer
from loyverse_sdk.models.common import Base, Pagination


class Variant(Base):
    id: UUID = Field(alias="variant_id")
    item_id: UUID
    sku: str = Field(max_length=40)
    reference_variant_id: str | None = Field(default=None, max_length=128)
    option1_value: str | None = Field(default=None, max_length=20)
    option2_value: str | None = Field(default=None, max_length=20)
    option3_value: str | None = Field(default=None, max_length=20)
    barcode: str | None = Field(default=None, max_length=20)
    cost: NonNegativeFloat = 0.0
    purchase_cost: NonNegativeFloat | None = 0.0
    default_pricing_type: str = "VARIABLE"
    default_price: NonNegativeFloat | None = None
    stores: list

    @field_serializer("id", mode="plain")
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class VariantListResponse(Pagination):
    items: list[Variant] = Field(alias="variants")
