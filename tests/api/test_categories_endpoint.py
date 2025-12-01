from datetime import datetime
from typing import Iterable
from loyverse_api.api import LoyverseEndpoint, LoyverseEndpoints
import pytest


@pytest.fixture
def endpoint() -> LoyverseEndpoint:
    """Instantiate endpoint"""
    endpoint = LoyverseEndpoints.CATEGORIES
    return endpoint


@pytest.fixture
def record_id() -> str:
    """Example id from the dataset"""
    return "6f4cb227-09cd-4e13-8d3d-441a392f77b5"


@pytest.fixture
def expected_keys() -> list[str]:
    """List of keys expected to be contains by the JSON data"""
    return [
        "id",
        "handle",
        "name",
        "description",
        "track_stock",
        "sold_by_weight",
        "is_composite",
        "use_production",
        "category_id",
        "components",
        "primary_supplier_id",
        "tax_ids",
        "modified_ids",
        "variants"
    ]


def test_endpoint(endpoint, expected_keys):
    """Sends a GET request to the endpoint.
    Expects JSON data containg specified key names."""
    data, cursor = endpoint.get()
    assert isinstance(data, Iterable)
    assert len(data) > 0

    for key in expected_keys:
        assert key in data[0]


def test_fetch_after_dt(endpoint):
    """Expects an iterable of objects created AFTER the specified datetime"""
    start = datetime(2025, 7, 15)
    records = endpoint.fetch_after_dt(start)

    for record in records:
        assert record.created_at.timestamp() >= start.timestamp()


def test_fetch_before_dt(endpoint):
    """Expects an iterable of objects created BEFORE the specified datetime"""
    end = datetime(2025, 5, 30)
    records = endpoint.fetch_before_dt(end)

    for record in records:
        assert record.created_at.timestamp() <= end.timestamp()


def test_fetch_between_dt(endpoint):
    """Expects an iterable of objects created WITHIN the specified datetimes"""
    start = datetime(2025, 1, 1)
    end = datetime(2025, 12, 31)

    records = endpoint.fetch_between_dt(start, end)

    for record in records:
        assert start.timestamp() <= record.created_at.timestamp() <= end.timestamp()


def test_fetch_by_id(endpoint, record_id):
    """Expect a Receipt object with matching attribute values"""
    r = endpoint.fetch_by_id(record_id)

    assert r.name == "Wash"
    assert isinstance(r.amount, float)
    for attrib in (r.track_stock, r.sold_by_weight, r.is_composite, r.use_production):
        assert isinstance(attrib, bool)
