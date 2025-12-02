from typing import Self
from uuid import UUID
from pydantic import Field, model_validator
from loyverse_api.models.common import Base, Pagination


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
    components: list = Field(default_factory=list, exclude=True)
    primary_supplier_id: UUID | None = None
    tax_ids: list[UUID] | None = Field(default_factory=list, exclude=True)
    modifier_ids: list[UUID] | None = Field(default_factory=list, exclude=True)
    form: str = Field(default="SQUARE", exclude=True)
    color: str = Field(default="GREY", exclude=True)
    image_url: str | None = None
    option1_name: str | None = Field(default=None, exclude=True)
    option2_name: str | None = Field(default=None, exclude=True)
    option3_name: str | None = Field(default=None, exclude=True)
    variants: list[dict] | None = None

    @model_validator(mode="after")
    def set_default_handle(self) -> Self:
        """Sets handle to the value of the item name if not provided"""
        if self.handle is None:
            self.handle = self.name
        return self


class ItemListResponse(Pagination):
    items: list[Item] = Field(alias="items")
