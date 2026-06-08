import random
from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Discount
from loyverse_sdk.models.discount import DiscountType


class TestDiscountModel:
    """Simulates ingesting and instatiating data from /discounts"""

    def generate_valid_payload(self):
        payload = dict(
            id=uuid4(),
            name=f"Discount {random.randint(1, 10)}",
            type=random.choice(list(DiscountType)),
            discount_amount=random.random() * 100,
            discount_percent=random.random(),
            stores=[uuid4() for _ in range(2)],
            restricted_access=random.choice([True, False]),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            deleted_at=None,
        )
        return payload

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = Discount(**payload)

        assert r.type in DiscountType
        if r.type == DiscountType.FIXED_AMOUNT:
            assert r.discount_percent is None
            assert r.discount_amount >= 0.0
        if r.type == DiscountType.FIXED_PERCENT:
            assert r.discount_amount is None
            assert 0.0 <= r.discount_percent <= 1.0

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["name"]

        with pytest.raises(ValidationError):
            Discount(**payload)

        payload = self.generate_valid_payload()
        del payload["stores"]

        with pytest.raises(ValidationError):
            Discount(**payload)

        payload = self.generate_valid_payload()
        del payload["type"]

        with pytest.raises(ValidationError):
            Discount(**payload)

        payload = self.generate_valid_payload()
        payload["type"] = DiscountType.FIXED_AMOUNT
        payload["discount_amount"] = None

        with pytest.raises(ValidationError):
            Discount(**payload)

        payload = self.generate_valid_payload()
        payload["type"] = DiscountType.FIXED_PERCENT
        payload["discount_percent"] = None

        with pytest.raises(ValidationError):
            Discount(**payload)

    def test_fixed_amount_discount_without_value(self):
        payload = dict(
            name="Fixed amount", type=DiscountType.FIXED_AMOUNT, stores=[uuid4()]
        )

        with pytest.raises(ValueError):
            Discount(**payload)

    def test_fixed_percent_discount_without_value(self):
        payload = dict(
            name="Fixed percent", type=DiscountType.FIXED_PERCENT, stores=[uuid4()]
        )

        with pytest.raises(ValueError):
            Discount(**payload)
