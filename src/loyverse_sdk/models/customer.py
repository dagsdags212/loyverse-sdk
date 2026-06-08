import re
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytz
from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)

from loyverse_sdk.core.config import config
from loyverse_sdk.models.common import BaseListQuery, Pagination


class Customer(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str | None = None
    phone_number: str | None = None
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
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)

    @field_validator("name", "email", "phone_number", mode="before")
    def sanitize_strings(cls, value: str | None) -> str | None:
        if value:
            return re.sub(r"\s+", " ", value).strip()

    @field_validator("name", mode="before")
    def titlecase(cls, value: str | None) -> str | None:
        if value:
            return value.title()

    @field_serializer("id", mode="plain")
    def serialize_uuid(self, value: UUID, _info: object = None) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value

    @model_validator(mode="after")
    def validate_timestamps(self) -> "Customer":
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        if self.created_at or self.updated_at or self.deleted_at:
            _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
            local_tz = pytz.timezone(_tz)

            if self.created_at and self.created_at.tzinfo is None:
                self.created_at = self.created_at.replace(tzinfo=pytz.utc).astimezone(
                    local_tz
                )
            if self.updated_at and self.updated_at.tzinfo is None:
                self.updated_at = self.updated_at.replace(tzinfo=pytz.utc).astimezone(
                    local_tz
                )
            if self.deleted_at and self.deleted_at.tzinfo is None:
                self.deleted_at = self.deleted_at.replace(tzinfo=pytz.utc).astimezone(
                    local_tz
                )

        return self

    @field_validator("created_at", "updated_at", "deleted_at", mode="before")
    @classmethod
    def parse_timestamps(cls, value):
        if value is None or value == "" or value == "null":
            return None
        return value

    def __repr__(self) -> str:
        return f"Customer(name={self.name},email={self.email},phone_number={self.phone_number})"

    def tenure(self) -> timedelta | None:
        if self.first_visit and self.last_visit:
            return self.last_visit - self.first_visit


class CustomerListResponse(Pagination):
    items: list[Customer] = Field(alias="customers")


class CustomerListQuery(BaseListQuery):
    customer_ids: str | None = None
    email: str | None = None

    def to_params(self) -> dict:
        params = super().to_params()
        if self.customer_ids is not None:
            params["customer_ids"] = self.customer_ids
        if self.email is not None:
            params["email"] = self.email
        return params
