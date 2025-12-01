from uuid import UUID
from pydantic import Field, field_validator
from loyverse_api.models.base import Base


class Item(Base):
    handle: str
    reference_id: UUID | None = None
    name: str = Field(alias="item_name")
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

    @field_validator("handle", mode="before")
    def titlecase_handle(cls, value: str) -> str:
        """Convert item handle to titlecase"""
        return value.title()
