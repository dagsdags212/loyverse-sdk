from uuid import uuid4, UUID
from datetime import datetime
from zoneinfo import ZoneInfo
from pydantic import BaseModel, Field, field_validator
from loyverse_api.core.config import config


class Base(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = Field(default=None, exclude=True)

    @field_validator("created_at", "updated_at", "deleted_at", mode="after")
    def update_timezone(cls, value: datetime | None) -> datetime:
        if value:
            return value.replace(tzinfo=ZoneInfo(config.timezone))
