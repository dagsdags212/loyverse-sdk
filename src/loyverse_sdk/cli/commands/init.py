from pathlib import Path

import typer

from loyverse_sdk.cli._async import console
from loyverse_sdk.core.config import config
from loyverse_sdk.core.paths import (
    config_dir,
    db_dir,
    ensure_dirs,
    env_file,
    write_pointer,
)

_ENV_KEYS = ("LOYVERSE_API_TOKEN", "LOYVERSE_DB_PATH")


def _read_env(path: Path) -> tuple[str, dict[str, str]]:
    """Read .env file, returning (raw_content, parsed_vars)."""
    existing: dict[str, str] = {}
    content = ""
    if path.exists():
        content = path.read_text()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                existing[key.strip()] = value.strip().strip('"').strip("'")
    return content, existing


def _write_env(path: Path, content: str, updates: dict[str, str]) -> None:
    """Write updated .env content, replacing or appending keys."""
    lines = content.splitlines() if content else []
    updated_keys: set[str] = set()
    with open(path, "w") as f:
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.partition("=")[0].strip()
                if key in updates:
                    f.write(f"{key}={updates[key]}\n")
                    updated_keys.add(key)
                    continue
            f.write(f"{line}\n")
        for key, value in updates.items():
            if key not in updated_keys:
                if path.exists() and path.stat().st_size > 0:
                    f.write("\n")
                f.write(f"{key}={value}\n")


def _prompt_for(
    key: str,
    existing: dict[str, str],
    prompt_text: str,
    default: str = "",
    hide: bool = False,
) -> str | None:
    if key in existing:
        console.print(f"[yellow]{key} is already set:[/yellow] {existing[key]}")
        if not typer.confirm("Do you want to overwrite it?"):
            console.print(f"[dim]Keeping existing {key}.[/dim]")
            return None
    value = typer.prompt(prompt_text, default=default, show_default=bool(default))
    value = value.strip()
    if not value:
        console.print(f"[red]{key} cannot be empty.[/red]")
        raise typer.Exit(1)
    return value


def _db_location(db_name: str, config_path: Path) -> Path:
    """Where a database name resolves under *config_path* (bare name -> db/)."""
    p = Path(db_name).expanduser()
    if p.parent == Path("."):
        return db_dir(config_path) / p.name
    return p


def init(
    config_dir_opt: str = typer.Option(
        None,
        "--config-dir",
        "-c",
        help="Directory for Loyverse config and databases (default: ~/.loyverse)",
    ),
    db_path: str = typer.Option(
        None, "--db-path", "-d", help="Database name or path (default: loyverse.db)"
    ),
    api_token: str = typer.Option(
        None,
        "--api-token",
        "-t",
        help="Loyverse API token (skips the interactive prompt)",
    ),
) -> None:
    """Set up your Loyverse config directory, API token, and database name."""
    console.print("[bold]Loyverse SDK Setup[/bold]\n")

    # 1. Where the config and databases live (default: the active dir, ~/.loyverse).
    if config_dir_opt is None:
        config_dir_opt = typer.prompt("Config directory", default=str(config_dir()))
    config_path = Path(config_dir_opt.strip()).expanduser()
    ensure_dirs(config_path)
    env_path = env_file(config_path)
    content, existing = _read_env(env_path)

    # 2. API token — from the flag, or prompted (paste) if not provided.
    if api_token is not None:
        token: str | None = api_token.strip()
        if not token:
            console.print("[red]API token cannot be empty.[/red]")
            raise typer.Exit(1)
    else:
        token = _prompt_for(
            "LOYVERSE_API_TOKEN",
            existing,
            "Enter your Loyverse API token",
            hide=True,
        )

    # 3. Database name — from the flag, or prompted with a sensible default.
    if db_path is not None:
        db: str | None = db_path.strip() or config.LOYVERSE_DB_PATH
    else:
        db_default = existing.get("LOYVERSE_DB_PATH", config.LOYVERSE_DB_PATH)
        db = _prompt_for(
            "LOYVERSE_DB_PATH",
            existing,
            "Database name",
            default=db_default,
        )
        if db is None:
            db = existing.get("LOYVERSE_DB_PATH", config.LOYVERSE_DB_PATH)

    updates: dict[str, str] = {}
    if token is not None:
        updates["LOYVERSE_API_TOKEN"] = token
    if db is not None:
        updates["LOYVERSE_DB_PATH"] = db

    if updates:
        _write_env(env_path, content, updates)

    # Record the chosen config directory so later CLI commands find it.
    write_pointer(config_path)

    db_name = updates.get(
        "LOYVERSE_DB_PATH",
        existing.get("LOYVERSE_DB_PATH", config.LOYVERSE_DB_PATH),
    )
    console.print("\n[green]✓  Configuration saved[/green]")
    console.print(f"[dim]  Config dir: {config_path}[/dim]")
    console.print(f"[dim]  Env file:   {env_path}[/dim]")
    console.print(f"[dim]  Database:   {_db_location(db_name, config_path)}[/dim]")
