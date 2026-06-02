from datetime import datetime
import pytest
from pydantic import ValidationError

from loyverse_sdk.models import PaymentType


class TestPaymentTypeModel:
    """Simulates ingesting data from /payment_types endpoint.

    The Loyverse API returns string IDs, not UUID objects.
    """

    def generate_valid_payload(self):
        return {
            "id": "42dd2a55-6f40-11ea-bde9-1269e7c5a22d",
            "name": "Cash",
            "type": "CASH",
            "stores": ["42dc2cec-6f40-11ea-bde9-1269e7c5a22d"],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "deleted_at": None,
        }

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = PaymentType(**payload)

        assert r.id is not None
        assert isinstance(r.id, str)
        assert r.name == "Cash"
        assert r.type == "CASH"
        assert len(r.stores) == 1

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["name"]

        with pytest.raises(ValidationError):
            PaymentType(**payload)

        # stores is optional (has default_factory=list)

    def test_default_handle(self):
        # Minimal payload with only required fields
        payload = {
            "name": "Cash",
        }
        r = PaymentType(**payload)

        assert r.name == "Cash"
        assert r.type == "CASH"  # Default value
        assert r.stores == []  # Default empty list
