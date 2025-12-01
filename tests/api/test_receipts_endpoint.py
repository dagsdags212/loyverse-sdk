from uuid import UUID
from datetime import datetime, timedelta
from typing import Iterable
from loyverse_api.api import LoyverseEndpoint, LoyverseEndpoints
import pytest


@pytest.fixture
def endpoint() -> LoyverseEndpoint:
    """Instantiate endpoint"""
    endpoint = LoyverseEndpoints.RECEIPTS
    endpoint.set_limit(250)
    return endpoint


@pytest.fixture
def record_id() -> str:
    """Example id from the dataset"""
    return "8-4181"


@pytest.fixture
def expected_keys() -> list[str]:
    """List of keys expected to be contains by the JSON data"""
    return [
        "receipt_number",
        "customer_id",
        "employee_id",
        "store_id",
        "pos_device_id",
        "line_items",
        "total_money",
        "total_discount",
        "payments",
    ]


def test_endpoint(endpoint, expected_keys):
    """Sends a GET request to the endpoint.
    Expects JSON data containg specified key names."""
    data, cursor = endpoint.get()
    assert isinstance(data, Iterable)
    assert len(data) > 0

    for key in expected_keys:
        assert key in data[0]
        if key.endswith("id"):
            UUID(data[0][key])
        if key == "line_items":
            assert isinstance(data[0][key], Iterable)


def test_fetch_after_dt(endpoint):
    """Expects an iterable of objects created AFTER the specified datetime"""
    start = datetime.now(tz=None) - timedelta(days=2)
    records = endpoint.fetch_after_dt(start)

    for record in records:
        assert record.created_at.timestamp() >= start.timestamp()


def test_fetch_before_dt(endpoint):
    """Expects an iterable of objects created BEFORE the specified datetime"""
    end = datetime(2025, 2, 1)
    records = endpoint.fetch_before_dt(end)

    for record in records:
        assert record.created_at.timestamp() <= end.timestamp()


def test_fetch_between_dt(endpoint):
    """Expects an iterable of objects created WITHIN the specified datetimes"""
    start = datetime.now(tz=None) - timedelta(days=5)
    end = datetime.now(tz=None) - timedelta(days=3)

    records = endpoint.fetch_between_dt(start, end)

    for record in records:
        assert start.timestamp() <= record.created_at.timestamp() <= end.timestamp()


def test_fetch_by_id(endpoint, record_id):
    """Expect a Receipt object with matching attribute values"""
    r = endpoint.fetch_by_id(record_id)

    assert r.customer_id == UUID("4c969d4e-333f-4f54-b6bf-4626cf368f34")
    assert r.employee_id == UUID("a563ec77-a6ca-4f60-97e7-64d80232c293")
    assert len(r.line_items.split(",")) == 5
