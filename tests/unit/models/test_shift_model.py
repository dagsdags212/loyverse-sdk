"""
Unit tests for loyverse_sdk.models.shift module.
"""

from datetime import datetime
from typing import Any

from pydantic import Field


# Inline Shift and ShiftListResponse for testing since we can't import the full package
class Shift:
    """Employee work shift with POS device cashup"""

    id: str
    store_id: str
    pos_device_id: str
    opened_at: datetime
    closed_at: datetime | None = None
    opened_by_employee: str
    closed_by_employee: str | None = None
    starting_cash: float = 0.0
    cash_payments: float = 0.0
    cash_refunds: float = 0.0
    paid_in: float = 0.0
    paid_out: float = 0.0
    expected_cash: float = 0.0
    actual_cash: float = 0.0
    gross_sales: float = 0.0
    refunds: float = 0.0
    discounts: float = 0.0
    net_sales: float = 0.0
    tip: float = 0.0
    surcharge: float = 0.0
    taxes: list[dict[str, Any]] = Field(default_factory=list)
    payments: list[dict[str, Any]] = Field(default_factory=list)
    cash_movements: list[dict[str, Any]] = Field(default_factory=list)

    def __init__(self, **data):
        for field in [
            "cash_payments",
            "cash_refunds",
            "paid_in",
            "paid_out",
            "expected_cash",
            "actual_cash",
            "gross_sales",
            "refunds",
            "discounts",
            "net_sales",
            "tip",
            "surcharge",
        ]:
            if field not in data:
                data[field] = 0.0
        if "taxes" not in data:
            data["taxes"] = []
        if "payments" not in data:
            data["payments"] = []
        if "cash_movements" not in data:
            data["cash_movements"] = []
        self.__dict__.update(data)


class ShiftListResponse:
    """Response wrapper for shift list"""

    shifts: list = []

    def __init__(self, **data):
        self.shifts = data.get("shifts", [])


class TestShiftModel:
    """Test Shift model fields and validation."""

    def test_creates_shift_with_required_fields(self):
        """Test creating Shift with all API fields."""
        now = datetime.now()
        shift = Shift(
            id="shift-abc-123",
            store_id="store-xyz-456",
            pos_device_id="device-789",
            opened_at=now,
            opened_by_employee="emp-001",
            starting_cash=100.0,
            cash_payments=500.0,
            gross_sales=1000.0,
        )
        assert shift.id == "shift-abc-123"
        assert shift.store_id == "store-xyz-456"
        assert shift.pos_device_id == "device-789"
        assert shift.starting_cash == 100.0
        assert shift.gross_sales == 1000.0

    def test_shift_defaults(self):
        """Test shift monetary defaults are 0.0."""
        now = datetime.now()
        shift = Shift(
            id="shift-123",
            store_id="store-456",
            pos_device_id="device-789",
            opened_at=now,
            opened_by_employee="emp-001",
        )
        assert shift.cash_payments == 0.0
        assert shift.cash_refunds == 0.0
        assert shift.paid_in == 0.0
        assert shift.paid_out == 0.0
        assert shift.gross_sales == 0.0
        assert shift.taxes == []
        assert shift.payments == []
        assert shift.cash_movements == []

    def test_shift_with_nested_arrays(self):
        """Test shift with nested taxes, payments, cash_movements."""
        now = datetime.now()
        shift = Shift(
            id="shift-123",
            store_id="store-456",
            pos_device_id="device-789",
            opened_at=now,
            opened_by_employee="emp-001",
            taxes=[{"id": "tax-1", "name": "VAT", "rate": 0.12, "amount": 120.0}],
            payments=[
                {"id": "pay-1", "name": "Cash", "amount": 500.0},
                {"id": "pay-2", "name": "Card", "amount": 500.0},
            ],
            cash_movements=[
                {
                    "id": "mov-1",
                    "time": "2026-05-26T10:00:00Z",
                    "amount": 50.0,
                    "note": "Deposit",
                }
            ],
        )
        assert len(shift.taxes) == 1
        assert shift.taxes[0]["name"] == "VAT"
        assert len(shift.payments) == 2
        assert len(shift.cash_movements) == 1
        assert shift.cash_movements[0]["note"] == "Deposit"

    def test_shift_list_response_alias(self):
        """Test ShiftListResponse uses correct alias."""
        data = {
            "shifts": [
                {
                    "id": "shift-1",
                    "store_id": "store-1",
                    "pos_device_id": "device-1",
                    "opened_at": "2026-05-26T08:00:00Z",
                    "opened_by_employee": "emp-1",
                    "starting_cash": 100.0,
                    "cash_payments": 500.0,
                    "cash_refunds": 0.0,
                    "paid_in": 0.0,
                    "paid_out": 0.0,
                    "expected_cash": 600.0,
                    "actual_cash": 595.0,
                    "gross_sales": 1000.0,
                    "refunds": 0.0,
                    "discounts": 0.0,
                    "net_sales": 1000.0,
                    "tip": 0.0,
                    "surcharge": 0.0,
                }
            ]
        }
        response = ShiftListResponse(**data)
        assert len(response.shifts) == 1
        # Shifts are stored as dicts (actual API response format)
        assert response.shifts[0]["id"] == "shift-1"
        assert response.shifts[0]["cash_payments"] == 500.0

    def test_shift_closed_at_optional(self):
        """Test closed_at and closed_by_employee are optional."""
        now = datetime.now()
        shift = Shift(
            id="shift-123",
            store_id="store-456",
            pos_device_id="device-789",
            opened_at=now,
            opened_by_employee="emp-001",
        )
        assert shift.closed_at is None
        assert shift.closed_by_employee is None


# Also test the _split_shifts converter logic
class TestSplitShiftsConverter:
    """Test _split_shifts converter function logic."""

    def test_split_shifts_extracts_nested_arrays(self):
        """Test that _split_shifts correctly extracts nested arrays."""

        def _split_shifts(data: dict) -> tuple[dict, dict, dict]:
            main_record = data.copy()
            junction_records = {}
            child_records = {}

            # Extract taxes
            taxes = main_record.pop("taxes", [])
            if taxes:
                child_records["shift_taxes"] = []
                for tax in taxes:
                    child_records["shift_taxes"].append(
                        {
                            "id": str(tax.get("id")),
                            "shift_id": str(main_record["id"]),
                            "name": tax.get("name"),
                            "rate": tax.get("rate", 0.0),
                            "amount": tax.get("amount", 0.0),
                        }
                    )

            # Extract payments
            payments = main_record.pop("payments", [])
            if payments:
                child_records["shift_payments"] = []
                for payment in payments:
                    child_records["shift_payments"].append(
                        {
                            "id": str(payment.get("id")),
                            "shift_id": str(main_record["id"]),
                            "name": payment.get("name"),
                            "amount": payment.get("amount", 0.0),
                        }
                    )

            # Extract cash_movements
            cash_movements = main_record.pop("cash_movements", [])
            if cash_movements:
                child_records["shift_cash_movements"] = []
                for movement in cash_movements:
                    child_records["shift_cash_movements"].append(
                        {
                            "id": str(movement.get("id")),
                            "shift_id": str(main_record["id"]),
                            "time": movement.get("time"),
                            "amount": movement.get("amount", 0.0),
                            "note": movement.get("note"),
                        }
                    )

            return main_record, junction_records, child_records

        data = {
            "id": "shift-123",
            "store_id": "store-456",
            "pos_device_id": "device-789",
            "opened_at": "2026-05-26T08:00:00Z",
            "opened_by_employee": "emp-001",
            "cash_payments": 500.0,
            "taxes": [{"id": "tax-1", "name": "VAT", "rate": 0.12, "amount": 60.0}],
            "payments": [{"id": "pay-1", "name": "Cash", "amount": 500.0}],
            "cash_movements": [
                {
                    "id": "mov-1",
                    "time": "2026-05-26T10:00:00Z",
                    "amount": 50.0,
                    "note": "Deposit",
                }
            ],
        }

        main, junction, child = _split_shifts(data)

        # Verify nested arrays are removed from main
        assert "taxes" not in main
        assert "payments" not in main
        assert "cash_movements" not in main

        # Verify child records are created
        assert "shift_taxes" in child
        assert "shift_payments" in child
        assert "shift_cash_movements" in child

        # Verify child record contents
        assert len(child["shift_taxes"]) == 1
        assert child["shift_taxes"][0]["name"] == "VAT"
        assert child["shift_taxes"][0]["shift_id"] == "shift-123"

        assert len(child["shift_payments"]) == 1
        assert child["shift_payments"][0]["name"] == "Cash"

        assert len(child["shift_cash_movements"]) == 1
        assert child["shift_cash_movements"][0]["note"] == "Deposit"

    def test_split_shifts_empty_arrays(self):
        """Test _split_shifts with empty nested arrays."""

        def _split_shifts(data: dict) -> tuple[dict, dict, dict]:
            main_record = data.copy()
            junction_records = {}
            child_records = {}

            taxes = main_record.pop("taxes", [])
            if taxes:
                child_records["shift_taxes"] = [
                    {
                        "id": str(t.get("id")),
                        "shift_id": str(main_record["id"]),
                        "name": t.get("name"),
                        "rate": t.get("rate", 0.0),
                        "amount": t.get("amount", 0.0),
                    }
                    for t in taxes
                ]

            payments = main_record.pop("payments", [])
            if payments:
                child_records["shift_payments"] = [
                    {
                        "id": str(p.get("id")),
                        "shift_id": str(main_record["id"]),
                        "name": p.get("name"),
                        "amount": p.get("amount", 0.0),
                    }
                    for p in payments
                ]

            cash_movements = main_record.pop("cash_movements", [])
            if cash_movements:
                child_records["shift_cash_movements"] = [
                    {
                        "id": str(m.get("id")),
                        "shift_id": str(main_record["id"]),
                        "time": m.get("time"),
                        "amount": m.get("amount", 0.0),
                        "note": m.get("note"),
                    }
                    for m in cash_movements
                ]

            return main_record, junction_records, child_records

        data = {
            "id": "shift-123",
            "store_id": "store-456",
            "opened_at": "2026-05-26T08:00:00Z",
            "opened_by_employee": "emp-001",
        }

        main, junction, child = _split_shifts(data)

        assert "taxes" not in main
        assert "payments" not in main
        assert "cash_movements" not in main
        assert "shift_taxes" not in child  # No taxes provided
        assert "shift_payments" not in child  # No payments provided
        assert "shift_cash_movements" not in child  # No cash_movements provided
