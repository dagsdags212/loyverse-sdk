import asyncio
from unittest import mock

from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


def _make_fake_run_async(mocker):
    mock_client = mocker.MagicMock()
    mock_client.categories.update = mocker.AsyncMock(
        return_value=mocker.MagicMock(model_dump=lambda: {})
    )

    def fake_run_async(fn):
        asyncio.run(fn(mock_client))

    return fake_run_async


class TestUpdateCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(
            app, ["api", "update", "employees", "some-id", "--name", "New"]
        )
        assert result.exit_code == 1
        assert "Cannot update" in result.stdout

    def test_rejects_no_fields(self):
        result = runner.invoke(app, ["api", "update", "categories", "some-id"])
        assert result.exit_code == 1
        assert "No update fields provided" in result.stdout

    def test_prompts_confirmation_and_cancels(self, mocker):
        fake = _make_fake_run_async(mocker)
        with mock.patch("loyverse_sdk.cli.commands.update.run_async", fake):
            result = runner.invoke(
                app,
                ["api", "update", "categories", "abc-123", "--name", "NewName"],
                input="n\n",
            )
        assert result.exit_code == 0
        assert "Proceed with update" in result.stdout
        assert "Cancelled" in result.stdout

    def test_skips_confirmation_with_yes(self, mocker):
        fake = _make_fake_run_async(mocker)
        with mock.patch("loyverse_sdk.cli.commands.update.run_async", fake):
            result = runner.invoke(
                app,
                [
                    "api",
                    "update",
                    "categories",
                    "abc-123",
                    "--name",
                    "NewName",
                    "--yes",
                ],
            )
        assert result.exit_code == 0

    def test_updatable_includes_expected(self):
        from loyverse_sdk.cli._metadata import get_updatable_resources

        resources = get_updatable_resources()
        assert "categories" in resources
        assert "items" in resources
        assert "modifiers" in resources
