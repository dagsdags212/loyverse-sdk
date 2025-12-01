from loyverse_api.api.endpoints import LoyverseEndpoint
import pytest


@pytest.fixture
def get_endpoints():
    return [
        "categories",
        "customers",
        "discounts",
        "employees",
        "inventory",
        "items",
        "merchant",
        "modifiers",
        "payment_types",
        "pos_devices",
        "receipts",
        "shifts",
        "stores",
        "suppliers",
        "taxes",
        "webhooks",
        "variants",
    ]


def test_endpoint_reponses(get_endpoints):
    """Ping each endpoint, all must return a valid response"""
    for ep in get_endpoints:
        endpoint = LoyverseEndpoint(endpoint=ep)
        endpoint.fetch_most_recent(1)
