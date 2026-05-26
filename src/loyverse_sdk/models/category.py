from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum, unique
from pydantic import BaseModel, Field, field_validator, field_serializer
from loyverse_sdk.models.common import Pagination, BaseListQuery


@unique
class CategoryColor(str, Enum):
    GREY = "GREY"
    RED = "RED"
    PINK = "PINK"
    ORANGE = "ORANGE"
    GREEN = "GREEN"
    BLUE = "BLUE"
    PURPLE = "PURPLE"
    LIME = "LIME"


class BaseCategory(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    color: CategoryColor = CategoryColor.GREY

    @field_validator("color", mode="before")
    def uppercase_color(cls, color: str) -> str:
        return color.upper()

    @field_serializer("id", mode="plain")
    def serialize_uuids(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class Category(BaseCategory):
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None


class CategoryListResponse(Pagination):
    items: list[Category] = Field(alias="categories")


class CategoryListQuery(BaseListQuery):
    """Query parameters for GET /categories."""

    category_ids: str | None = Field(default=None)
    show_deleted: bool = Field(default=False)
    limit: int = Field(default=50)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.category_ids is not None:
            params["category_ids"] = self.category_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params


class CreateCategory(BaseCategory):
    name: str
    color: CategoryColor | None = None


class UpdateCategory(BaseCategory):
    id: UUID
    name: str
    color: CategoryColor | None = None
