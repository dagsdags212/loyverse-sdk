import json

import typer

from loyverse_sdk import LoyverseClient
from loyverse_sdk.cli._async import console, err_console, run_async
from loyverse_sdk.cli._display import build_table
from loyverse_sdk.cli._metadata import get_listable_resources
from loyverse_sdk.exceptions import NotFoundError


def get_resource(
    resource: str,
    id: str,
    fmt: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Output format: json, table",
    ),
) -> None:
    """Retrieve a single resource record by its ID.

    \b
    Examples:
        loyverse get customers <ID>
        loyverse get receipts <ID>
        loyverse get items <ID> --format table
    """
    listable = get_listable_resources()
    if resource not in listable and resource != "merchant":
        valid = "', '".join(sorted(listable) + ["merchant"])
        console.print(f"[red]Unknown resource '{resource}'.[/red] Valid: '{valid}'")
        raise typer.Exit(1)

    fmt = fmt.lower()
    if fmt not in ("json", "table"):
        console.print(f"[red]Invalid --format '{fmt}' (use json or table)[/red]")
        raise typer.Exit(1)

    async def _run(client: LoyverseClient) -> None:
        endpoint = getattr(client, resource)

        with err_console.status(f"[bold]Fetching {resource}…[/bold]", spinner="dots"):
            try:
                record = await endpoint.retrieve(id=id)
            except AttributeError:
                console.print(
                    f"[red]Cannot retrieve individual '{resource}' records.[/red]"
                )
                raise typer.Exit(1) from None
            except NotFoundError:
                console.print(f"[red]{resource} with ID '{id}' not found.[/red]")
                raise typer.Exit(1) from None

        if fmt == "json":
            console.print(
                json.dumps(
                    record.model_dump() if hasattr(record, "model_dump") else record,
                    indent=2,
                    default=str,
                )
            )
        elif fmt == "table":
            console.print(build_table([record]))

    run_async(_run)
