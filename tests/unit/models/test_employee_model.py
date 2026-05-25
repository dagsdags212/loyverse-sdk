import random
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError
import pytest

from loyverse_sdk.models import Employee


class TestEmployeeModel:
    """Simulates ingesting and instatiating data from /employees"""

    payload = dict(
        id=uuid4(),
        name="John Doe",
        email="john.doe@email.com",
        phone_number="+6381920302375",
        stores=[uuid4()],
        is_owner=random.choice([True, False]),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None,
    )

    def test_valid_payload(self):
        r = Employee(**self.payload)

        assert r.id is not None
        assert isinstance(r.id, UUID)
        assert r.name is not None
        assert isinstance(r.name, str)
        assert r.email == "john.doe@email.com"

    def test_missing_required_values(self):
        payload = self.payload
        del payload["name"]

        with pytest.raises(ValidationError):
            Employee(**payload)

    def test_defaults(self):
        payload = dict(name="John Doe", stores=[uuid4()])
        r = Employee(**payload)

        assert isinstance(r.id, UUID)
        assert r.email is None
        assert r.phone_number is None
        assert r.is_owner is False
