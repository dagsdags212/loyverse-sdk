from pathlib import Path

import pytest

from loyverse_sdk.core import paths


@pytest.fixture
def config_home(tmp_path, monkeypatch):
    monkeypatch.setenv("LOYVERSE_CONFIG_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """No env override; pointer file lives under an isolated XDG home."""
    monkeypatch.delenv("LOYVERSE_CONFIG_DIR", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    return tmp_path


class TestConfigDir:
    def test_defaults_to_home_loyverse(self, isolated):
        assert paths.config_dir() == Path.home() / ".loyverse"

    def test_env_var_takes_precedence(self, config_home):
        assert paths.config_dir() == config_home
        assert paths.env_file() == config_home / ".loyverse.env"
        assert paths.db_dir() == config_home / "db"

    def test_pointer_used_when_no_env_var(self, isolated):
        target = isolated / "custom-config"
        paths.write_pointer(target)
        assert paths.config_dir() == target

    def test_env_var_beats_pointer(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
        paths.write_pointer(tmp_path / "pointed")
        monkeypatch.setenv("LOYVERSE_CONFIG_DIR", str(tmp_path / "env"))
        assert paths.config_dir() == tmp_path / "env"

    def test_ensure_dirs_creates_layout(self, config_home):
        paths.ensure_dirs()
        assert config_home.is_dir()
        assert (config_home / "db").is_dir()

    def test_ensure_dirs_with_explicit_path(self, isolated):
        target = isolated / "explicit"
        paths.ensure_dirs(target)
        assert target.is_dir()
        assert (target / "db").is_dir()


class TestPointerFile:
    def test_write_and_read(self, isolated):
        target = isolated / "somewhere"
        paths.write_pointer(target)
        assert paths.pointer_file().exists()
        assert paths.read_pointer() == target

    def test_read_missing_returns_none(self, isolated):
        assert paths.read_pointer() is None

    def test_read_empty_returns_none(self, isolated):
        pf = paths.pointer_file()
        pf.parent.mkdir(parents=True, exist_ok=True)
        pf.write_text("\n")
        assert paths.read_pointer() is None


class TestResolveDbPath:
    def test_bare_name_goes_under_db_dir(self, config_home):
        resolved = paths.resolve_db_path("mydata.duckdb")
        assert resolved == config_home / "db" / "mydata.duckdb"
        assert (config_home / "db").is_dir()

    def test_none_uses_default_name(self, config_home):
        resolved = paths.resolve_db_path(None)
        assert resolved == config_home / "db" / paths.DEFAULT_DB_NAME

    def test_explicit_config_path_overrides_active(self, config_home, tmp_path):
        other = tmp_path / "other"
        resolved = paths.resolve_db_path("x.duckdb", config_path=other)
        assert resolved == other / "db" / "x.duckdb"

    def test_relative_path_with_separator_is_literal(self, config_home):
        assert paths.resolve_db_path("./local/x.duckdb") == Path("local/x.duckdb")

    def test_absolute_path_is_literal(self, config_home, tmp_path):
        target = tmp_path / "elsewhere" / "x.duckdb"
        assert paths.resolve_db_path(str(target)) == target

    def test_user_expansion(self, config_home):
        assert (
            paths.resolve_db_path("~/custom/x.duckdb")
            == Path.home() / "custom" / "x.duckdb"
        )


class TestMigrateLegacyEnv:
    def test_migrates_when_home_missing(self, config_home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        Path(".env").write_text("LOYVERSE_API_TOKEN=legacy-token\n")
        assert paths.migrate_legacy_env() is True
        assert paths.env_file().read_text() == "LOYVERSE_API_TOKEN=legacy-token\n"

    def test_noop_when_home_exists(self, config_home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        Path(".env").write_text("LOYVERSE_API_TOKEN=legacy-token\n")
        paths.ensure_dirs()
        paths.env_file().write_text("LOYVERSE_API_TOKEN=existing-token\n")
        assert paths.migrate_legacy_env() is False
        assert "existing-token" in paths.env_file().read_text()

    def test_noop_when_no_legacy(self, config_home, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert paths.migrate_legacy_env() is False
        assert not paths.env_file().exists()
