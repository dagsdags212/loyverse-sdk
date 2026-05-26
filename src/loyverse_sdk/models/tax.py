from typing import List
from uuid import UUID
from pydantic import Field
from loyverse_sdk.models.common import Base, Pagination, BaseListQuery


class Tax(Base):
    name: str = Field(max_length=40)
    type: str
    rate: float = Field(ge=0.0, le=100.0)
    stores: List[UUID]


class TaxListResponse(Pagination):
    items: list[Tax] = Field(alias="taxes")


class TaxListQuery(BaseListQuery):
    tax_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.tax_ids is not None:
            params["tax_ids"] = self.tax_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
