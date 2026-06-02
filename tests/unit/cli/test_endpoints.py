from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


class TestEndpointsCommand:
    def test_endpoints_lists_resources(self):
        result = runner.invoke(app, ["api", "endpoints"])
        assert result.exit_code == 0
        assert "categories" in result.stdout
        assert "receipts" in result.stdout
        assert "merchant" in result.stdout
        assert "list" in result.stdout
        assert "create" in result.stdout

    def test_endpoints_shows_paths(self):
        result = runner.invoke(app, ["api", "endpoints"])
        assert "/categories" in result.stdout
        assert "/receipts" in result.stdout
