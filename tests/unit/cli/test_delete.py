import asyncio
from unittest import mock

from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


def _make_fake_run_async(mocker, endpoint_retrieve_return=None):
    """Create a run_async mock that executes the inner function with a
    fully mocked client.  All endpoint methods are AsyncMock so 'await'
    works correctly."""
    mock_client = mocker.MagicMock()

    async def _mock_retrieve(id):
        if endpoint_retrieve_return is not None:
            return endpoint_retrieve_return
        return {"id": id, "name": "Test"}

    async def _mock_delete(id):
        return {"deleted": True}

    mock_client.categories.retrieve = _mock_retrieve
    mock_client.categories.delete = _mock_delete

    def fake_run_async(fn):
        asyncio.run(fn(mock_client))

    return fake_run_async


class TestDeleteCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(app, ["api", "delete", "employees", "some-id"])
        assert result.exit_code == 1
        assert "Cannot delete" in result.stdout

    def test_prompts_confirmation_and_cancels(self, mocker):
        fake = _make_fake_run_async(
            mocker, endpoint_retrieve_return={"id": "abc-123", "name": "Test"}
        )
        with mock.patch("loyverse_sdk.cli.commands.delete.run_async", fake):
            result = runner.invoke(
                app, ["api", "delete", "categories", "abc-123"], input="n\n"
            )
        assert result.exit_code == 0
        assert "Cancelled" in result.stdout

    def test_skips_confirmation_with_yes(self, mocker):
        fake = _make_fake_run_async(mocker)
        with mock.patch("loyverse_sdk.cli.commands.delete.run_async", fake):
            result = runner.invoke(app, ["api", "delete", "categories", "abc-123", "--yes"])
        assert result.exit_code == 0

    def test_deletable_includes_expected(self):
        from loyverse_sdk.cli._metadata import get_deletable_resources

        resources = get_deletable_resources()
        assert "categories" in resources
        assert "discounts" in resources
        assert "merchant" not in resources
        assert "employees" not in resources
