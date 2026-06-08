from typing import Self
from uuid import UUID

from pydantic import Field, field_serializer, model_validator

from loyverse_sdk.models.common import Base, BaseListQuery, Pagination


class Item(Base):
    name: str = Field(alias="item_name")
    handle: str | None = None
    reference_id: UUID | None = None
    description: str | None = None
    track_stock: bool = False
    sold_by_weight: bool = False
    is_composite: bool = False
    use_production: bool = False
    category_id: UUID | None = None
    components: list = Field(default_factory=list)
    primary_supplier_id: UUID | None = None
    tax_ids: list[UUID] | None = Field(default_factory=list)
    modifier_ids: list[UUID] | None = Field(default_factory=list)
    form: str = Field(default="SQUARE")
    color: str = Field(default="GREY")
    image_url: str | None = None
    option1_name: str | None = Field(default=None)
    option2_name: str | None = Field(default=None)
    option3_name: str | None = Field(default=None)
    variants: list[dict] | None = None

    @model_validator(mode="after")
    def set_default_handle(self) -> Self:
        if self.handle is None:
            self.handle = self.name
        return self

    @field_serializer(
        "reference_id", "category_id", "primary_supplier_id", mode="plain"
    )
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value

    @field_serializer("tax_ids", "modifier_ids", mode="plain")
    def serialize_uuid_lists(self, value: list[UUID]) -> list[str]:
        return [str(id) for id in value]


class ItemListResponse(Pagination):
    items: list[Item] = Field(alias="items")


class ItemListQuery(BaseListQuery):
    item_ids: str | None = None
    store_id: str | None = None
    category_id: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.item_ids is not None:
            params["item_ids"] = self.item_ids
        if self.store_id is not None:
            params["store_id"] = self.store_id
        if self.category_id is not None:
            params["category_id"] = self.category_id
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
