import re
from datetime import datetime
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


class Employee(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str | None = None
    phone_number: str | None = None
    stores: list[UUID]
    is_owner: bool = False
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

    @field_serializer("stores", mode="plain")
    def serialize_store_uuids(
        self, value: list[UUID], _info: object = None
    ) -> list[str]:
        return [str(id) for id in value]

    @field_serializer("id", mode="plain")
    def serialize_uuid(self, value: UUID, _info: object = None) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value

    @model_validator(mode="after")
    def validate_timestamps(self) -> "Employee":
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


class EmployeeListResponse(Pagination):
    items: list[Employee] = Field(alias="employees")


class EmployeeListQuery(BaseListQuery):
    employee_ids: str | None = None
    show_deleted: bool = Field(default=False)

    def to_params(self) -> dict:
        params = super().to_params()
        if self.employee_ids is not None:
            params["employee_ids"] = self.employee_ids
        if self.show_deleted is not False:
            params["show_deleted"] = str(self.show_deleted).lower()
        return params
