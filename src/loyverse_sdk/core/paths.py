"""Filesystem layout for the Loyverse CLI configuration directory.

By default everything lives under ``~/.loyverse``::

    ~/.loyverse/
    ├── .loyverse.env       # API token and settings
    └── db/
        └── loyverse.db     # exported DuckDB database(s)

The active config directory is resolved, in order, from:

1. the ``LOYVERSE_CONFIG_DIR`` environment variable,
2. a pointer file written by ``loyverse init`` (so a custom location chosen
   during setup is discovered automatically by later commands),
3. the default ``~/.loyverse``.

The pointer file lives under the XDG config home
(``~/.config/loyverse/config_dir``) — a fixed, well-known location the CLI can
read without already knowing where the config directory is.
"""

import os
import shutil
from pathlib import Path


DEFAULT_DB_NAME = "loyverse.db"
ENV_FILENAME = ".loyverse.env"
DEFAULT_CONFIG_DIR = Path.home() / ".loyverse"


def pointer_file() -> Path:
    """Location of the bootstrap file recording the active config directory."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "loyverse" / "config_dir"


def read_pointer() -> Path | None:
    """Return the config directory recorded in the pointer file, if any."""
    pf = pointer_file()
    if not pf.exists():
        return None
    raw = pf.read_text().strip()
    return Path(raw).expanduser() if raw else None


def write_pointer(config_path: Path) -> None:
    """Record *config_path* as the active config directory."""
    pf = pointer_file()
    pf.parent.mkdir(parents=True, exist_ok=True)
    pf.write_text(f"{config_path}\n")


def config_dir() -> Path:
    """Return the active Loyverse config directory.

    Resolution order: ``LOYVERSE_CONFIG_DIR`` env var, then the pointer file
    written by ``loyverse init``, then the default ``~/.loyverse``.
    """
    override = os.environ.get("LOYVERSE_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    pointed = read_pointer()
    if pointed is not None:
        return pointed
    return DEFAULT_CONFIG_DIR


def _base(config_path: Path | None) -> Path:
    return config_path if config_path is not None else config_dir()


def env_file(config_path: Path | None = None) -> Path:
    """Path to the env file inside *config_path* (or the active config dir)."""
    return _base(config_path) / ENV_FILENAME


def db_dir(config_path: Path | None = None) -> Path:
    """Directory where exported databases are stored."""
    return _base(config_path) / "db"


def ensure_dirs(config_path: Path | None = None) -> None:
    """Create the config and database directories if they don't exist."""
    base = _base(config_path)
    base.mkdir(parents=True, exist_ok=True)
    (base / "db").mkdir(parents=True, exist_ok=True)


def resolve_db_path(value: str | None, config_path: Path | None = None) -> Path:
    """Resolve a database name or path to an absolute filesystem location.

    A bare name (no directory component, e.g. ``mydata.duckdb``) is stored
    under :func:`db_dir`. A value containing a path separator or that is
    absolute (e.g. ``./local/x.duckdb`` or ``/tmp/x.duckdb``) is used as-is.
    """
    name = value or DEFAULT_DB_NAME
    p = Path(name).expanduser()
    if p.parent == Path("."):
        target_dir = db_dir(config_path)
        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir / p.name
    return p


def migrate_legacy_env() -> bool:
    """Copy a legacy ``.env`` from the working directory into the config dir.

    Runs only when the home config does not exist yet, so it is safe to call
    on every startup. Returns ``True`` if a migration was performed.
    """
    target = env_file()
    if target.exists():
        return False
    legacy = Path(".env")
    if not legacy.exists():
        return False
    config_dir().mkdir(parents=True, exist_ok=True)
    shutil.copyfile(legacy, target)
    return True
