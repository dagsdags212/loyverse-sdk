from uuid import uuid4, UUID
from datetime import datetime
import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Receipt


class TestReceiptModel:
    """Simulates ingesting and instatiating data from /receipts"""

    def generate_valid_payload(self):
        payload = dict(
            receipt_number="8-1234",
            note="an example receipt",
            receipt_type="SALE",
            refund_for=None,
            order=None,
            source=None,
            total_money=300,
            total_tax=30,
            line_items=[
                dict(item_name=f"item{i}", quantity=i, price=i * 100) for i in range(3)
            ],
            points_earned=10,
            points_deducted=0,
            points_balance=50,
            total_discount=0,
            surcharge=0,
            tip=15,
            customer_id=uuid4(),
            employee_id=uuid4(),
            store_id=uuid4(),
            pos_device_id=uuid4(),
            payments=uuid4(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            cancelled_at=None,
            deleted_at=None,
        )
        return payload

    def test_valid_payload(self):
        payload = self.generate_valid_payload()
        r = Receipt(**payload)

        assert r.receipt_type in ["SALE", "REFUND"]
        if r.receipt_type == "REFUND":
            assert r.receipt_type is not None

        if r.customer_id:
            assert isinstance(r.customer_id, UUID)
        assert r.employee_id and isinstance(r.employee_id, UUID)
        assert r.store_id and isinstance(r.store_id, UUID)
        assert r.pos_device_id and isinstance(r.pos_device_id, UUID)

        assert r.total_amount >= 0
        assert r.total_tax >= 0
        assert r.total_discount >= 0
        assert r.points_earned >= 0
        assert r.points_deducted >= 0
        assert r.points_balance >= 0
        assert r.tip >= 0

    def test_missing_required_values(self):
        payload = self.generate_valid_payload()
        del payload["receipt_number"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["total_money"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["employee_id"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["store_id"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["pos_device_id"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["payments"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["line_items"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

        payload = self.generate_valid_payload()
        del payload["points_balance"]

        with pytest.raises(ValidationError):
            Receipt(**payload)

    def test_default_handle(self):
        payload = dict(
            receipt_number="8-1234",
            line_items=[
                dict(item_name=f"item{i}", quantity=i, price=i * 100) for i in range(3)
            ],
            total_money=200,
            points_balance=100,
            employee_id=uuid4(),
            store_id=uuid4(),
            pos_device_id=uuid4(),
            payments=uuid4(),
        )
        r = Receipt(**payload)

        assert r.note is None
        assert r.receipt_type == "SALE"
        assert r.refund_for is None
        assert r.order is None
        assert r.source is None
        assert r.total_tax == 0
        assert r.points_earned == 0
        assert r.points_deducted == 0
        assert r.total_discount == 0
        assert r.surcharge == 0
        assert r.tip == 0
        assert r.cancelled_at is None
