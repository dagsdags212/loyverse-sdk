from pathlib import Path

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def clean_env_file():
    """Ensure no .env file exists before/after test."""
    env_path = Path(".env")
    existed = env_path.exists()
    if existed:
        backup = env_path.read_text()
        env_path.unlink()
    yield
    if env_path.exists():
        env_path.unlink()
    if existed:
        env_path.write_text(backup)


class TestInitCommand:
    def test_init_creates_env_file(self, clean_env_file):
        result = runner.invoke(app, ["init"], input="test-token-123\n\n")
        assert result.exit_code == 0
        assert Path(".env").exists()
        content = Path(".env").read_text()
        assert "LOYVERSE_API_TOKEN=test-token-123" in content
        assert "LOYVERSE_DB_PATH=" in content

    def test_init_overwrites_existing(self, clean_env_file):
        Path(".env").write_text("LOYVERSE_API_TOKEN=old-token\n")
        result = runner.invoke(app, ["init"], input="y\nnew-token\n\n")
        assert result.exit_code == 0
        content = Path(".env").read_text()
        assert "LOYVERSE_API_TOKEN=new-token" in content

    def test_init_keeps_existing_on_no(self, clean_env_file):
        Path(".env").write_text("LOYVERSE_API_TOKEN=old-token\n")
        result = runner.invoke(app, ["init"], input="n\n\n")
        assert result.exit_code == 0
        content = Path(".env").read_text()
        assert "LOYVERSE_API_TOKEN=old-token" in content
