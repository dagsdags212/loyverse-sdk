from unittest import mock

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_run_async():
    with mock.patch("loyverse_sdk.cli.commands.list.run_async") as m:
        m.side_effect = lambda fn: None
        yield m


class TestListCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(app, ["api", "list", "unknown"])
        assert result.exit_code == 1
        assert "Unknown resource" in result.stdout

    def test_rejects_invalid_format(self):
        result = runner.invoke(app, ["api", "list", "categories", "--format", "xml"])
        assert result.exit_code == 1
        assert "Invalid --format" in result.stdout

    def test_accepts_valid_resource(self, mock_run_async):
        result = runner.invoke(app, ["api", "list", "categories"])
        assert result.exit_code == 0

    def test_accepts_all_formats(self, mock_run_async):
        for fmt in ("json", "table", "csv", "parquet"):
            result = runner.invoke(app, ["api", "list", "categories", "--format", fmt])
            assert result.exit_code == 0

    def test_accepts_limit(self, mock_run_async):
        result = runner.invoke(app, ["api", "list", "categories", "--limit", "10"])
        assert result.exit_code == 0

    def test_accepts_date_filters(self, mock_run_async):
        result = runner.invoke(
            app,
            [
                "api",
                "list",
                "receipts",
                "--created-at-min",
                "2024-01-01",
                "--created-at-max",
                "2024-12-31",
            ],
        )
        assert result.exit_code == 0

    def test_list_resources_includes_expected(self):
        """Verify that a list of expected resources exists."""
        from loyverse_sdk.cli._metadata import get_listable_resources

        resources = get_listable_resources()
        assert "customers" in resources
        assert "receipts" in resources
        assert "items" in resources
        assert "categories" in resources
