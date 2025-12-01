from datetime import datetime, timedelta
from uuid import UUID
from typing import Iterable
from loyverse_api.api import LoyverseEndpoints
import pytest


@pytest.fixture
def endpoint():
    """Instantiate endpoint"""
    return LoyverseEndpoints.EMPLOYEES


@pytest.fixture
def expected_keys() -> list[str]:
    """List of keys expected to be contains by the JSON data"""
    return [
        "id",
        "name",
        "phone_number",
        "stores",
        "is_owner",
        "created_at",
        "updated_at",
        "deleted_at",
    ]


@pytest.fixture
def record_id() -> UUID:
    """Example id from the dataset"""
    return UUID("b0bf616d-e297-4643-a73f-a2eb5c44176b")


def test_endpoint(endpoint, expected_keys):
    """Sends a GET request to the endpoint.
    Expects JSON data containing specified key names."""
    data, cursor = endpoint.get()
    assert isinstance(data, Iterable)
    assert len(data) > 0

    for key in expected_keys:
        assert key in data[0]


def test_fetch_after_dt(endpoint):
    """Expects an iterable objects created AFTER the specified datetime"""
    start = datetime.now(tz=None) - timedelta(days=7)
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
    start = datetime.now(tz=None) - timedelta(days=60)
    end = datetime.now(tz=None) - timedelta(days=30)

    records = endpoint.fetch_between_dt(start, end)

    for record in records:
        assert start.timestamp() <= record.created_at.timestamp() <= end.timestamp()


def test_fetch_by_id(endpoint, record_id):
    """Expect an object with matching id and other attributes"""
    r = endpoint.fetch_by_id(record_id)

    assert r.name == "Hannah"
    assert r.is_owner is True
