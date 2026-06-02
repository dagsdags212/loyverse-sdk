from unittest import mock

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_run_async():
    with mock.patch("loyverse_sdk.cli.commands.get.run_async") as m:
        m.side_effect = lambda fn: None
        yield m


class TestGetCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(app, ["api", "get", "unknown", "some-id"])
        assert result.exit_code == 1
        assert "Unknown resource" in result.stdout

    def test_rejects_invalid_format(self):
        result = runner.invoke(app, ["api", "get", "categories", "some-id", "--format", "xml"])
        assert result.exit_code == 1
        assert "Invalid --format" in result.stdout

    def test_accepts_valid_resource(self, mock_run_async):
        result = runner.invoke(app, ["api", "get", "categories", "abc-123"])
        assert result.exit_code == 0

    def test_accepts_merchant_without_id(self, mock_run_async):
        # merchant doesn't have a list endpoint but supports retrieve
        result = runner.invoke(app, ["api", "get", "merchant", "any"])
        assert result.exit_code == 0

    def test_accepts_table_format(self, mock_run_async):
        result = runner.invoke(
            app, ["api", "get", "categories", "abc-123", "--format", "table"]
        )
        assert result.exit_code == 0
