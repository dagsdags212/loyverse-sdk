from pathlib import Path

import typer

from loyverse_sdk.cli._async import console
from loyverse_sdk.core.config import config


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


def init(
    db_path: str = typer.Option(
        None, "--db-path", "-d", help="Database path (default: loyverse.db)"
    ),
) -> None:
    """Set up your Loyverse API token and database path in a .env file."""
    env_path = Path(".env")
    content, existing = _read_env(env_path)

    console.print("[bold]Loyverse SDK Setup[/bold]\n")

    token = _prompt_for(
        "LOYVERSE_API_TOKEN",
        existing,
        "Enter your Loyverse API token",
        hide=True,
    )

    db_default = db_path or config.LOYVERSE_DB_PATH
    db = _prompt_for(
        "LOYVERSE_DB_PATH",
        existing,
        "Database path",
        default=db_default,
    )
    if db is None:
        db = existing.get("LOYVERSE_DB_PATH", config.LOYVERSE_DB_PATH)

    updates: dict[str, str] = {}
    if token is not None:
        updates["LOYVERSE_API_TOKEN"] = token
    if db is not None:
        updates["LOYVERSE_DB_PATH"] = db

    if not updates:
        console.print("[dim]Nothing to update.[/dim]")
        return

    _write_env(env_path, content, updates)
    console.print(f"\n[green]✓  Configuration saved to .env[/green]")
    console.print(
        f"[dim]  LOYVERSE_DB_PATH={updates.get('LOYVERSE_DB_PATH', config.LOYVERSE_DB_PATH)}[/dim]"
    )
