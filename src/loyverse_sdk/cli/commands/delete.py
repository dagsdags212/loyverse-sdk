import json

import typer

from loyverse_sdk import LoyverseClient
from loyverse_sdk.cli._async import console, err_console, run_async
from loyverse_sdk.cli._metadata import get_deletable_resources
from loyverse_sdk.exceptions import NotFoundError


def delete_resource(
    resource: str,
    id: str,
    yes: bool = False,
) -> None:
    """Delete a resource record.  This cannot be undone.

    \b
    Examples:
        loyverse delete categories <ID>
        loyverse delete customers <ID>
        loyverse delete discounts <ID> --yes
    """
    deletable = get_deletable_resources()
    if resource not in deletable:
        valid = "', '".join(sorted(deletable))
        console.print(f"[red]Cannot delete '{resource}'.[/red] Deletable: '{valid}'")
        raise typer.Exit(1)

    async def _run(client: LoyverseClient) -> None:
        endpoint = getattr(client, resource)

        if not yes:
            with err_console.status(
                f"[bold]Fetching {resource}…[/bold]", spinner="dots"
            ):
                try:
                    record = await endpoint.retrieve(id=id)
                except NotFoundError:
                    console.print(f"[red]{resource} with ID '{id}' not found.[/red]")
                    raise typer.Exit(1) from None
                except AttributeError:
                    console.print(
                        f"[red]Cannot fetch individual '{resource}' "
                        f"records for confirmation.[/red]"
                    )
                    raise typer.Exit(1) from None

            console.print(
                f"\n[bold red]Delete [cyan]{resource}[/cyan] "
                f"[yellow]{id}[/yellow]?[/bold red]"
            )
            if hasattr(record, "model_dump"):
                console.print(json.dumps(record.model_dump(), indent=2, default=str))
            else:
                console.print(json.dumps(record, indent=2, default=str))

            console.print("\n[red]This cannot be undone.[/red]")
            confirmed = typer.confirm("Proceed?")
            if not confirmed:
                console.print("[dim]Cancelled.[/dim]")
                raise typer.Exit(0)

        with err_console.status(f"[bold]Deleting {resource}…[/bold]", spinner="dots"):
            result = await endpoint.delete(id=id)

        console.print(f"[green]✓  Deleted {resource} {id}[/green]")
        console.print(json.dumps(result, indent=2, default=str))

    run_async(_run)
