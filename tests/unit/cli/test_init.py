import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app
from loyverse_sdk.core import paths

runner = CliRunner()


@pytest.fixture
def home(tmp_path, monkeypatch):
    """Isolate the active config dir and the pointer (XDG) location."""
    cfg = tmp_path / "cfg"
    monkeypatch.setenv("LOYVERSE_CONFIG_DIR", str(cfg))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    return cfg


class TestInitCommand:
    def test_flags_write_to_config_dir(self, home, tmp_path):
        custom = tmp_path / "mycfg"
        result = runner.invoke(
            app,
            [
                "init",
                "--config-dir", str(custom),
                "--api-token", "tok-123",
                "--db-path", "mystore.duckdb",
            ],
        )
        assert result.exit_code == 0, result.output
        env_path = custom / ".loyverse.env"
        assert env_path.exists()
        content = env_path.read_text()
        assert "LOYVERSE_API_TOKEN=tok-123" in content
        assert "LOYVERSE_DB_PATH=mystore.duckdb" in content
        # db directory created and config location recorded in the pointer file
        assert (custom / "db").is_dir()
        assert paths.read_pointer() == custom

    def test_default_config_dir_when_flag_omitted(self, home):
        # Accept the prompted default config dir (the active one), flags for the rest.
        result = runner.invoke(
            app,
            ["init", "--api-token", "tok", "--db-path", "loyverse.db"],
            input="\n",
        )
        assert result.exit_code == 0, result.output
        assert (home / ".loyverse.env").exists()
        assert paths.read_pointer() == home

    def test_prompts_for_token_and_db(self, home, tmp_path):
        custom = tmp_path / "c2"
        result = runner.invoke(
            app, ["init", "--config-dir", str(custom)], input="tok-xyz\n\n"
        )
        assert result.exit_code == 0, result.output
        content = (custom / ".loyverse.env").read_text()
        assert "LOYVERSE_API_TOKEN=tok-xyz" in content
        assert "LOYVERSE_DB_PATH=loyverse.db" in content

    def test_overwrites_existing_token(self, home, tmp_path):
        custom = tmp_path / "c3"
        custom.mkdir()
        (custom / ".loyverse.env").write_text("LOYVERSE_API_TOKEN=old\n")
        # token: overwrite? y -> new value; db: accept default
        result = runner.invoke(
            app, ["init", "--config-dir", str(custom)], input="y\nnew-token\n\n"
        )
        assert result.exit_code == 0, result.output
        assert "LOYVERSE_API_TOKEN=new-token" in (custom / ".loyverse.env").read_text()

    def test_keeps_existing_on_no(self, home, tmp_path):
        custom = tmp_path / "c4"
        custom.mkdir()
        (custom / ".loyverse.env").write_text(
            "LOYVERSE_API_TOKEN=old-token\nLOYVERSE_DB_PATH=loyverse.db\n"
        )
        # token: overwrite? n ; db: overwrite? n
        result = runner.invoke(
            app, ["init", "--config-dir", str(custom)], input="n\nn\n"
        )
        assert result.exit_code == 0, result.output
        assert "LOYVERSE_API_TOKEN=old-token" in (custom / ".loyverse.env").read_text()

    def test_api_token_flag_overwrites_without_prompt(self, home, tmp_path):
        custom = tmp_path / "c5"
        custom.mkdir()
        (custom / ".loyverse.env").write_text("LOYVERSE_API_TOKEN=old\n")
        result = runner.invoke(
            app,
            [
                "init",
                "--config-dir", str(custom),
                "--api-token", "flag-token",
                "--db-path", "loyverse.db",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "LOYVERSE_API_TOKEN=flag-token" in (custom / ".loyverse.env").read_text()

    def test_does_not_write_cwd_dotenv(self, home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        custom = tmp_path / "c6"
        result = runner.invoke(
            app,
            [
                "init",
                "--config-dir", str(custom),
                "--api-token", "t",
                "--db-path", "loyverse.db",
            ],
        )
        assert result.exit_code == 0, result.output
        assert not (tmp_path / ".env").exists()
