from uuid import uuid4, UUID
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator
import pytz
from loyverse_sdk.core.config import config


class Base(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = Field(default=None, exclude=True)

    @field_validator("created_at", "updated_at", "deleted_at", mode="after")
    def utc_to_local(cls, value: datetime | None) -> datetime:
        if value:
            _tz = config.TIMEZONE if config.TIMEZONE else "Asia/Manila"
            local_tz = pytz.timezone(_tz)
            local_dt = value.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_dt


class Pagination(BaseModel):
    next_cursor: str | None = Field(default=None, alias="cursor")
