from typing import List
from uuid import UUID
from pydantic import Field
from loyverse_sdk.models.common import Base, Pagination, BaseListQuery


class ModifierOption(Base):
    name: str
    price: float = Field(default=0.0, ge=0.0)
    position: int


class Modifier(Base):
    name: str
    position: int
    stores: List[UUID]
    modifier_options: List[ModifierOption] = Field(default_factory=list)


class ModifierListResponse(Pagination):
    items: list[Modifier] = Field(alias="modifiers")


class ModifierListQuery(BaseListQuery):
    modifier_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.modifier_ids is not None:
            params["modifier_ids"] = self.modifier_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
