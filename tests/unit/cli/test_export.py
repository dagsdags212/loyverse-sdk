from unittest import mock

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_run_async():
    with mock.patch("loyverse_sdk.cli.commands.export_.run_async") as m:
        m.side_effect = lambda fn: None
        yield m


class TestExportCommandValidation:
    def test_db_path_is_optional(self, mock_run_async):
        # db_path defaults to config.LOYVERSE_DB_PATH when omitted
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0

    def test_accepts_db_path(self, mock_run_async):
        result = runner.invoke(app, ["export", "test.duckdb"])
        assert result.exit_code == 0

    def test_rejects_unknown_resource(self, mock_run_async):
        result = runner.invoke(
            app,
            ["export", "test.duckdb", "--resource", "unknown"],
        )
        assert result.exit_code == 1
        assert "Unknown resource" in result.stdout

    def test_accepts_valid_resource(self, mock_run_async):
        result = runner.invoke(
            app,
            ["export", "test.duckdb", "--resource", "receipts"],
        )
        assert result.exit_code == 0

    def test_accepts_date_filters(self, mock_run_async):
        result = runner.invoke(
            app,
            [
                "export",
                "test.duckdb",
                "--created-at-min",
                "2024-01-01",
                "--created-at-max",
                "2024-12-31",
            ],
        )
        assert result.exit_code == 0

    def test_accepts_batch_size(self, mock_run_async):
        result = runner.invoke(
            app,
            ["export", "test.duckdb", "--batch-size", "500"],
        )
        assert result.exit_code == 0

    def test_accepts_no_indexes(self, mock_run_async):
        result = runner.invoke(
            app,
            ["export", "test.duckdb", "--no-indexes"],
        )
        assert result.exit_code == 0
