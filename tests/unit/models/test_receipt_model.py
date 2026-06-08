from datetime import datetime

import pytest
from pydantic import ValidationError

from loyverse_sdk.models import Receipt


class TestReceiptModel:
    """Simulates ingesting data from /receipts endpoint.

    The Loyverse API returns string IDs, not UUID objects.
    """

    def generate_valid_payload(self):
        """Generate a payload matching the actual Loyverse API response format."""
        return {
            # Primary identifier
            "receipt_number": "8-1234",
            "note": "an example receipt",
            "receipt_type": "SALE",
            "refund_for": None,
            "order_id": None,
            "source": None,
            "dining_option": "Dine in",

            # Financial totals
            "total_money": 300.00,
            "total_tax": 30.00,
            "points_earned": 10.00,
            "points_deducted": 0.00,
            "points_balance": 50.00,
            "total_discount": 0.00,
            "surcharge": 0.00,
            "tip": 15.00,

            # Timestamps
            "receipt_date": datetime.now(),
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "cancelled_at": None,

            # References (API returns strings)
            "customer_id": "c71758a2-79bf-11ea-bde9-1269e7c5a22d",
            "employee_id": "58f53835-7a17-11ea-bde9-1269e7c5a22d",
            "store_id": "42dc2cec-6f40-11ea-bde9-1269e7c5a22d",
            "pos_device_id": "1cce2f2e-8033-4b67-ad2a-b9d1c749ec26",

            # Nested arrays matching API format
            "line_items": [
                {
                    "id": f"item-{i}",
                    "item_id": "d5fe0da6-44b3-4633-9915-e9dc5118cbfc",
                    "variant_id": "706e2626-3329-45f8-98d7-0e1dbcbcb9d9",
                    "item_name": f"Item{i}",
                    "variant_name": None,
                    "sku": f"SKU{i:05d}",
                    "quantity": float(i),
                    "price": float(i * 100),
                    "gross_total_money": float(i * 100),
                    "total_money": float(i * 90),
                    "cost": 10.00,
                    "cost_total": 20.00,
                    "line_note": None,
                    "line_taxes": [],
                    "total_discount": 10.00,
                    "line_discounts": [],
                    "line_modifiers": [],
                }
                for i in range(1, 4)
            ],

            "total_discounts": [
                {
                    "id": "82185d34-97a9-4137-8e1b-e0d1f07a7cd7",
                    "type": "FIXED_PERCENT",
                    "name": "Percent discount",
                    "percentage": 10.0,
                    "money_amount": 10.00,
                }
            ],

            "total_taxes": [
                {
                    "id": "a94d8606-7268-11ea-bde9-1269e7c5a22d",
                    "type": "ADDED",
                    "name": "Added",
                    "rate": 5.545,
                    "money_amount": 30.00,
                }
            ],

            "payments": [
                {
                    "payment_type_id": "42dd2a55-6f40-11ea-bde9-1269e7c5a22d",
                    "name": "Cash",
                    "type": "CASH",
                    "money_amount": 300.00,
                    "paid_at": datetime.now(),
                    "payment_details": None,
                }
            ],
        }

    def test_valid_payload(self):
        """Test that a valid API payload creates a valid Receipt."""
        payload = self.generate_valid_payload()
        r = Receipt(**payload)

        assert r.receipt_number == "8-1234"
        assert r.receipt_type == "SALE"
        assert r.total_money == 300.00
        assert r.total_tax == 30.00

        # Check string IDs are preserved
        assert isinstance(r.customer_id, str)
        assert isinstance(r.employee_id, str)
        assert isinstance(r.store_id, str)
        assert isinstance(r.pos_device_id, str)

        # Check nested arrays
        assert len(r.line_items) == 3
        assert r.line_items[0].item_name == "Item1"

        assert len(r.payments) == 1
        assert r.payments[0].money_amount == 300.00

    def test_missing_required_values(self):
        """Test that missing required fields raise ValidationError."""
        payload = self.generate_valid_payload()

        # receipt_number is required
        del payload["receipt_number"]
        with pytest.raises(ValidationError):
            Receipt(**payload)

        # total_money is required
        payload = self.generate_valid_payload()
        del payload["total_money"]
        with pytest.raises(ValidationError):
            Receipt(**payload)

    def test_default_handle(self):
        """Test that missing optional fields get correct defaults."""
        # Minimal payload with only required fields
        payload = {
            "receipt_number": "8-1234",
            "receipt_type": "SALE",
            "total_money": 200.00,
            "points_balance": 100.00,
            "line_items": [
                {
                    "id": "item-1",
                    "item_id": "d5fe0da6-44b3-4633-9915-e9dc5118cbfc",
                    "item_name": "Coffee",
                    "quantity": 1.0,
                    "price": 200.00,
                    "total_money": 200.00,
                }
            ],
            "payments": [
                {
                    "payment_type_id": "42dd2a55-6f40-11ea-bde9-1269e7c5a22d",
                    "name": "Cash",
                    "type": "CASH",
                    "money_amount": 200.00,
                }
            ],
        }
        r = Receipt(**payload)

        # Check the receipt_number is correctly set
        assert r.receipt_number == "8-1234"

        # Check optional string fields default to None
        assert r.note is None
        assert r.refund_for is None
        assert r.order_id is None
        assert r.source is None
        assert r.dining_option is None

        # Financial fields default to 0
        assert r.total_tax == 0.0
        assert r.points_earned == 0.0
        assert r.points_deducted == 0.0
        assert r.total_discount == 0.0
        assert r.surcharge == 0.0
        assert r.tip == 0.0

        # Reference IDs default to None
        assert r.cancelled_at is None
        assert r.customer_id is None
        assert r.employee_id is None
        assert r.store_id is None
        assert r.pos_device_id is None

        # Empty arrays for nested data
        assert r.total_discounts == []
        assert r.total_taxes == []

        # Note: created_at and updated_at are set by Base.validate_timestamps
        # since None values trigger the default factory
        assert r.created_at is not None
        assert r.updated_at is not None
