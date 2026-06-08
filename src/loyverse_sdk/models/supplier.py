from pydantic import Field

from loyverse_sdk.models.common import Base, BaseListQuery, Pagination


class Supplier(Base):
    name: str = Field(max_length=40)
    contact: str | None = Field(max_length=64)
    email: str | None = Field(default=None, max_length=64)
    phone_number: str | None = Field(default=None, max_length=15)
    website: str | None = None
    address_1: str | None = Field(default=None, max_length=192)
    address_2: str | None = Field(default=None, max_length=192)
    city: str | None = Field(default=None, max_length=64)
    region: str | None = Field(default=None, max_length=64)
    postal_code: str | None = Field(default=None, max_length=20)
    country_code: str | None = Field(default=None, max_length=2)
    note: str | None = Field(default=None, max_length=500)


class SupplierListResponse(Pagination):
    items: list[Supplier] = Field(alias="suppliers")


class SupplierListQuery(BaseListQuery):
    suppliers_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.suppliers_ids is not None:
            params["suppliers_ids"] = self.suppliers_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
