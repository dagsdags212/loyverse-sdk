from datetime import datetime

import pytz
import typer

from loyverse_sdk import LoyverseClient
from loyverse_sdk.cli._async import console, run_async
from loyverse_sdk.cli._dates import normalize_date
from loyverse_sdk.cli._metadata import get_listable_resources
from loyverse_sdk.core.config import config
from loyverse_sdk.core.paths import resolve_db_path
from loyverse_sdk.exceptions import ExportError


def export_resources(
    db_path: str | None = typer.Argument(
        None,
        help="Path or name for the DuckDB database (default: loyverse.db)",
    ),
    resource: list[str] = typer.Option(
        None,
        "--resource",
        "-r",
        help="Export specific resources (repeatable; omit for all)",
    ),
    created_at_min: str | None = typer.Option(
        None,
        "--created-at-min",
        help="Earliest created_at (ISO-8601, YYYY-MM-DD, today, yesterday)",
    ),
    created_at_max: str | None = typer.Option(
        None,
        "--created-at-max",
        help="Latest created_at (ISO-8601, YYYY-MM-DD, today, yesterday)",
    ),
    batch_size: int = typer.Option(
        1000,
        "--batch-size",
        "-b",
        help="Records to insert per transaction",
    ),
    no_indexes: bool = typer.Option(
        False,
        "--no-indexes",
        help="Skip index creation after export",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress progress display",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Full export from scratch (skip incremental sync)",
    ),
) -> None:
    """Export API data to a local DuckDB database for analytics.

    By default performs an incremental sync — only fetches records updated
    since the last export. Use --force for a full export.

    \b
    Examples:
        loyverse export
        loyverse export mydata.duckdb
        loyverse export --resource receipts
        loyverse export --created-at-min 2024-01-01
        loyverse export --force
    """
    db_path = str(resolve_db_path(db_path or config.LOYVERSE_DB_PATH))
    resources: list[str] | None = None
    if resource:
        listable = get_listable_resources()
        invalid = [r for r in resource if r not in listable]
        if invalid:
            valid = "', '".join(sorted(listable))
            console.print(
                f"[red]Unknown resource(s): {', '.join(invalid)}[/red]. "
                f"Valid: '{valid}'"
            )
            raise typer.Exit(1)
        resources = resource

    def _parse_date(value: str) -> datetime:
        normalized = normalize_date(value)
        dt = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        return dt.astimezone(pytz.utc).replace(tzinfo=None)

    kwargs: dict = {
        "db_path": db_path,
        "batch_size": batch_size,
        "create_indexes": not no_indexes,
        "show_progress": not quiet,
    }
    if created_at_min:
        kwargs["created_at_min"] = _parse_date(created_at_min)
    if created_at_max:
        kwargs["created_at_max"] = _parse_date(created_at_max)
    if resources:
        kwargs["resources"] = resources

    async def _run(client: LoyverseClient) -> None:
        try:
            do_full = force or created_at_min is not None or created_at_max is not None
            if do_full:
                counts = await client.export_to_duckdb(**kwargs)
            else:
                counts = await client.sync_to_duckdb(
                    db_path=db_path,
                    resources=resources,
                    batch_size=batch_size,
                    show_progress=not quiet,
                    create_indexes=not no_indexes,
                )
        except ExportError as e:
            console.print(f"[red]Export failed: {e}[/red]")
            raise typer.Exit(1)

        verb = "Export" if do_full else "Sync"
        total = sum(counts.values())
        console.print(
            f"\n[bold green]{verb} complete: {total:,} records "
            f"across {len(counts)} resources[/bold green]"
        )
        console.print(f"[dim]Database: {db_path}[/dim]")

    run_async(_run)
