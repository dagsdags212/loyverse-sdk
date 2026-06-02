from unittest import mock

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_run_async():
    with mock.patch("loyverse_sdk.cli.commands.create.run_async") as m:
        m.side_effect = lambda fn: None
        yield m


class TestCreateCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(app, ["api", "create", "merchant"])
        assert result.exit_code == 1
        assert "Cannot create" in result.stdout

    def test_rejects_missing_required_fields(self):
        result = runner.invoke(app, ["api", "create", "categories"])
        assert result.exit_code == 1
        assert "Missing required fields" in result.stdout
        assert "--name" in result.stdout

    def test_accepts_required_fields(self, mock_run_async):
        result = runner.invoke(app, ["api", "create", "categories", "--name", "Drinks"])
        assert result.exit_code == 0

    def test_rejects_categories_without_name(self):
        result = runner.invoke(app, ["api", "create", "categories", "--color", "GREEN"])
        assert result.exit_code == 1
        assert "Missing required fields" in result.stdout

    def test_accepts_taxes_with_required_fields(self, mock_run_async):
        result = runner.invoke(
            app,
            [
                "api",
                "create",
                "taxes",
                "--type",
                "INCLUDED",
                "--name",
                "VAT",
                "--rate",
                "12",
            ],
        )
        assert result.exit_code == 0

    def test_creatable_includes_expected(self):
        from loyverse_sdk.cli._metadata import get_creatable_resources

        resources = get_creatable_resources()
        assert "categories" in resources
        assert "customers" in resources
        assert "items" in resources
        assert "merchant" not in resources
