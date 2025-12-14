import re
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import Field, field_validator, field_serializer
from loyverse_sdk.models.common import Base, Pagination


class User(Base):
    name: str
    email: str | None = None
    phone_number: str | None = None

    @field_validator("name", "email", "phone_number", mode="before")
    def sanitize_strings(cls, value: str | None) -> str | None:
        """Remove and collapse trailing whitespaces from strings"""
        if value:
            return re.sub(r"\s+", " ", value).strip()

    @field_validator("name", mode="before")
    def titlecase(cls, value: str | None) -> str | None:
        if value:
            return value.title()


class Employee(User):
    stores: list[UUID]
    is_owner: bool = False

    @field_serializer("stores", mode="plain")
    def serialize_store_uuids(self, value: UUID) -> str:
        return [str(id) for id in value]


class EmployeeListResponse(Pagination):
    items: list[Employee] = Field(alias="employees")


class Customer(User):
    address: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    country_code: str | None = None
    note: str | None = None
    customer_code: str | None = None
    first_visit: datetime | None = None
    last_visit: datetime | None = None
    total_visits: int = Field(default=1)
    total_spent: float = Field(default=0.0)
    total_points: float = Field(default=0.0)
    permanent_deletion_at: datetime | None = None

    def __repr__(self) -> str:
        return f"Customer(name={self.name},email={self.email},phone_number={self.phone_number})"

    def tenure(self) -> timedelta | None:
        if self.first_visit and self.last_visit:
            return self.last_visit - self.first_visit


class CustomerListResponse(Pagination):
    items: list[Customer] = Field(alias="customers")
