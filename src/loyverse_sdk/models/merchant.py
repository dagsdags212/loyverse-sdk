from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from pydantic import ValidationError


class Merchant(BaseModel):
    id: UUID
    business_name: str
    email: str | None = None
    country: str | None
    currency: str
    created_at: datetime = Field(default_factory=datetime.now)

    @field_validator("country", mode="before")
    def validate_country_code(cls, country: str) -> str:
        """Checks if the passed country conforms to ISO 3166-1-alpha-2 format"""
        if len(country) != 2:
            raise ValidationError("country must be a two-character code")
        return country.upper()

    @field_validator("currency", mode="after")
    def extract_currency_code(cls, currency: dict) -> str:
        """Extracts the code key from the currency object"""
        currency_code = currency.get("code")
        if currency_code is None:
            raise ValidationError("code field does not exist in currency object")
        return currency_code

