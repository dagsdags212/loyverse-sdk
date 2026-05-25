from uuid import uuid4, UUID
from datetime import datetime
import pytest
from pydantic import ValidationError

from loyverse_sdk.models import PaymentType


class TestPaymentTypeModel:
    """Simulates ingesting and instatiating data from /payment_types"""

    def generate_valid_payload(self):
        payload = dict(
            id=uuid4(),
            name="Cash",
            type="CASH",
            stores=[uuid4()],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
        )
        return payload

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = PaymentType(**payload)

        assert r.id is not None
        assert isinstance(r.id, UUID)
        assert r.name is not None
        assert r.type is not None
        assert r.type.isupper()

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["name"]

        with pytest.raises(ValidationError):
            PaymentType(**payload)

        payload = self.generate_valid_payload()
        del payload["stores"]

        with pytest.raises(ValidationError):
            PaymentType(**payload)

    def test_default_handle(self):
        payload = dict(name="Cash", stores=[uuid4()])
        r = PaymentType(**payload)

        assert r.name == "Cash"
        assert r.type == "CASH"
