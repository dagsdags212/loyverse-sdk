import os

import pytest
from dotenv import load_dotenv

from loyverse_sdk.client import LoyverseClient

load_dotenv()


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "tests/integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


@pytest.fixture(autouse=True)
def skip_if_no_token():
    if not os.getenv("LOYVERSE_API_TOKEN"):
        pytest.skip("Skipping integration tests: LOYVERSE_API_TOKEN not set")


@pytest.fixture
def client():
    api_token = os.getenv("LOYVERSE_API_TOKEN")
    if not api_token:
        pytest.skip("No API token provided for integration tests")
    return LoyverseClient(api_token=api_token)
