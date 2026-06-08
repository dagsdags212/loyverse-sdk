from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Customer


class TestCustomerModel:
    """Simulates ingesting and instatiating data from /customers"""

    payload = dict(
        id=uuid4(),
        name="John Doe",
        email="john.doe@email.com",
        phone_number="+639102231956",
        address="123 Umali Drive",
        city="Los Banos",
        region="Laguna",
        country_code="PH",
        customer_code="8-1942",
        note="",
        first_visit=datetime.now(),
        last_visit=datetime.now(),
        total_visits=1,
        total_spent=3000.0,
        total_points=100.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        deleted_at=None,
        permanent_deletion_at=None,
    )

    def test_valid_payload(self):
        r = Customer(**self.payload)

        assert r.id is not None
        assert isinstance(r.id, UUID)
        assert r.name is not None
        assert isinstance(r.name, str)
        assert r.email == "john.doe@email.com"
        assert isinstance(r.first_visit, datetime)
        assert isinstance(r.last_visit, datetime)
        assert isinstance(r.total_visits, int)
        assert isinstance(r.total_spent, float)
        assert isinstance(r.total_points, float)

    def test_missing_required_values(self):
        payload = self.payload
        del payload["name"]

        with pytest.raises(ValidationError):
            Customer(**payload)

    def test_defaults(self):
        payload = dict(name="John Doe")
        r = Customer(**payload)

        assert isinstance(r.id, UUID)
        assert r.email is None
        assert r.phone_number is None
        assert r.address is None
