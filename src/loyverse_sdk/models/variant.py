from uuid import UUID
from pydantic import Field, NonNegativeFloat, field_serializer
from loyverse_sdk.models.common import Base, Pagination, BaseListQuery


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

    @field_serializer("item_id", mode="plain")
    def serialize_item_uuid(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class VariantListResponse(Pagination):
    items: list[Variant] = Field(alias="variants")


class VariantListQuery(BaseListQuery):
    variants_ids: str | None = None
    item_ids: str | None = None
    sku: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.variants_ids is not None:
            params["variants_ids"] = self.variants_ids
        if self.item_ids is not None:
            params["items_ids"] = self.item_ids
        if self.sku is not None:
            params["sku"] = self.sku
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
