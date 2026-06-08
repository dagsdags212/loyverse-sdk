import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

import typer
from rich.console import Console

from loyverse_sdk import LoyverseClient
from loyverse_sdk.exceptions import ConfigurationError, LoyverseSDKError

console = Console()
err_console = Console(stderr=True)


def run_async(main_coro: Callable[[LoyverseClient], Coroutine[Any, Any, None]]) -> None:
    """Execute an async coroutine with managed client lifecycle.

    Creates a ``LoyverseClient``, runs *main_coro* with it, handles
    configuration/API/unexpected errors uniformly, and closes the client
    when done (even on error).
    """

    async def _run() -> None:
        try:
            client = LoyverseClient()
        except (ConfigurationError, Exception) as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            console.print("[dim]Run 'loyverse init' to set up your API token.[/dim]")
            raise typer.Exit(1) from e

        try:
            await main_coro(client)
        except typer.Exit:
            raise
        except LoyverseSDKError as e:
            console.print(f"[red]{type(e).__name__}: {e}[/red]")
            raise typer.Exit(1) from e
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            raise typer.Exit(1) from e
        finally:
            await client.close()

    asyncio.run(_run())
