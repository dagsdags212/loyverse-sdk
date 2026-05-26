from pydantic import Field
from loyverse_sdk.models.common import Base, Pagination, BaseListQuery


class Store(Base):
    name: str = Field(max_length=40)
    address: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=64)
    state: str | None = Field(default=None, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=2)
    phone_number: str | None = Field(default=None, max_length=15)
    description: str | None = Field(default=None, max_length=128)


class StoreListResponse(Pagination):
    items: list[Store] = Field(alias="stores")


class StoreListQuery(BaseListQuery):
    store_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.store_ids is not None:
            params["store_ids"] = self.store_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
