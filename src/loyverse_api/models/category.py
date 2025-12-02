from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum, unique
from pydantic import BaseModel, Field, field_validator
from loyverse_api.models.common import Pagination


@unique
class CategoryColor(str, Enum):
    GREY = "GREY"
    RED = "RED"
    PINK = "PINK"
    ORANGE = "ORANGE"
    GREEN = "GREEN"
    BLUE = "BLUE"
    PURPLE = "PURPLE"


class BaseCategory(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    color: CategoryColor = CategoryColor.GREY

    @field_validator("color", mode="before")
    def uppercase_color(cls, color: str) -> str:
        """Capitalize the color attribute"""
        return color.upper()


class Category(BaseCategory):
    created_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = None


class CategoryListResponse(Pagination):
    items: list[Category] = Field(alias="categories")


class CreateCategory(BaseCategory):
    name: str
    color: CategoryColor | None = None


class UpdateCategory(BaseCategory):
    id: UUID
    name: str
    color: CategoryColor | None = None
