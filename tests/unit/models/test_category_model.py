from datetime import datetime
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Category


class TestCategoryModel:
    """Simulates ingesting and instatiating data from /categories"""

    def test_valid_payload(self):
        payload = dict(
            id=uuid4(),
            name="Soaps and Detergent",
            color="BLUE",
        )
        record = Category(**payload)

        assert isinstance(record.id, UUID)
        assert record.name == "Soaps and Detergent"
        assert record.color == "BLUE"
        assert isinstance(record.created_at, datetime)
        assert record.deleted_at is None

    def test_missing_required_values(self):
        payload = dict(id=uuid4(), color="GRAY")
        with pytest.raises(ValidationError):
            Category(**payload)

    def test_defaults(self):
        payload = dict(name="Soaps and Detergent")
        record = Category(**payload)

        assert record.color == "GREY"
        assert isinstance(record.id, UUID)
        assert isinstance(record.created_at, datetime)
