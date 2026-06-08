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
from loyverse_sdk.utils import standardize_datetime_str


class Base(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime | None = Field(default=None)
    updated_at: datetime | None = Field(default=None)
    deleted_at: datetime | None = Field(default=None)

    @model_validator(mode="after")
    def validate_timestamps(self) -> "Base":
        """Ensure timestamps are properly set and converted to local timezone."""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
        local_tz = pytz.timezone(_tz)

        def _to_local(dt: datetime | None) -> datetime | None:
            if dt is None:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=pytz.utc)
            return dt.astimezone(local_tz)

        self.created_at = _to_local(self.created_at)
        self.updated_at = _to_local(self.updated_at)
        self.deleted_at = _to_local(self.deleted_at)

        return self

    @field_validator("created_at", "updated_at", "deleted_at", mode="before")
    @classmethod
    def parse_timestamps(cls, value):
        """Handle API responses with null or empty timestamp values."""
        if value is None or value == "" or value == "null":
            return None
        return value

    @field_serializer("id", mode="plain")
    def serialize_uuid(self, value: UUID) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value


class Pagination(BaseModel):
    next_cursor: str | None = Field(default=None, alias="cursor")


# ---------------------------------------------------------------------------
# List query models
# ---------------------------------------------------------------------------


class BaseListQuery(BaseModel):
    """Base query model for list endpoints.

    Provides standard pagination params plus common date-range filters.
    Unsupported params are silently ignored by the Loyverse API, so every
    endpoint query model can safely inherit from this even if the API
    endpoint doesn't support all of these fields.
    """

    limit: int = Field(default_factory=lambda: config.PAGE_LIMIT)
    cursor: str | None = Field(default=None)
    created_at_min: datetime | None = Field(default=None)
    created_at_max: datetime | None = Field(default=None)
    updated_at_min: datetime | None = Field(default=None)
    updated_at_max: datetime | None = Field(default=None)

    @model_validator(mode="after")
    def validate_date_ranges(self) -> "BaseListQuery":
        if self.created_at_min and self.created_at_max:
            if self.created_at_min > self.created_at_max:
                raise ValueError("created_at_min must be <= created_at_max")
        if self.updated_at_min and self.updated_at_max:
            if self.updated_at_min > self.updated_at_max:
                raise ValueError("updated_at_min must be <= updated_at_max")
        return self

    @model_validator(mode="after")
    def validate_limit(self) -> "BaseListQuery":
        if self.limit is not None and (self.limit < 1 or self.limit > 250):
            raise ValueError("limit must be between 1 and 250")
        return self

    def to_params(self) -> dict:
        """Serialize to a dict suitable for passing as URL query params."""
        params: dict[str, object] = {}
        if self.limit is not None:
            params["limit"] = self.limit
        if self.cursor is not None:
            params["cursor"] = self.cursor
        if self.created_at_min is not None:
            params["created_at_min"] = standardize_datetime_str(self.created_at_min)
        if self.created_at_max is not None:
            params["created_at_max"] = standardize_datetime_str(self.created_at_max)
        if self.updated_at_min is not None:
            params["updated_at_min"] = standardize_datetime_str(self.updated_at_min)
        if self.updated_at_max is not None:
            params["updated_at_max"] = standardize_datetime_str(self.updated_at_max)
        return params
