"""
Rich-based progress display for DuckDB exports.

Provides a live-updating table that shows what resource is being fetched,
running record counts, warnings, and errors during the export process.
"""

from dataclasses import dataclass, field
from datetime import datetime

from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.text import Text

SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]


@dataclass
class ResourceStatus:
    name: str
    count: int = 0
    status: str = "pending"
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    warnings: list[str] = field(default_factory=list)


class ExportProgress:
    """Live progress display for DuckDB export operations.

    Renders a minimal Rich table that updates in real-time as each resource is
    streamed from the API and inserted into DuckDB. Resources currently being
    fetched show an animated spinner next to the running record count.

    Example:
        progress = ExportProgress(total_resources=17)
        progress.start()

        for resource in resources:
            progress.begin_resource(resource)
            # ... stream records ...
            progress.update_count(resource, 250)
            progress.finish_resource(resource, 1250)

        progress.finish()
    """

    def __init__(
        self,
        total_resources: int,
        console: Console | None = None,
        enabled: bool = True,
    ):
        self.total_resources = total_resources
        self.console = console or Console(color_system="truecolor")
        self.enabled = enabled
        self._live: Live | None = None
        self._resources: dict[str, ResourceStatus] = {}
        self._resource_order: list[str] = []
        self._warnings: list[str] = []
        self._errors: list[str] = []
        self._frame: int = 0

    def start(self) -> None:
        if not self.enabled:
            return
        self._live = Live(
            self._render(),
            console=self.console,
            refresh_per_second=8,
            transient=False,
        )
        self._live.start()

    def begin_resource(self, name: str) -> None:
        status = ResourceStatus(name=name, status="fetching", started_at=datetime.now())
        self._resources[name] = status
        self._resource_order.append(name)
        self._refresh()

    def update_count(self, name: str, count: int) -> None:
        if name in self._resources:
            self._resources[name].count = count
        self._refresh()

    def finish_resource(self, name: str, count: int) -> None:
        if name in self._resources:
            self._resources[name].count = count
            self._resources[name].status = "done"
            self._resources[name].finished_at = datetime.now()
        self._refresh()

    def warn_resource(self, name: str, message: str) -> None:
        if name in self._resources:
            self._resources[name].warnings.append(message)
            self._resources[name].status = "warning"
        self._warnings.append(f"[{name}] {message}")
        self._refresh()

    def error_resource(self, name: str, message: str) -> None:
        if name in self._resources:
            self._resources[name].error = message
            self._resources[name].status = "error"
        self._errors.append(f"[{name}] {message}")
        self._refresh()

    def add_warning(self, message: str) -> None:
        self._warnings.append(message)
        self._refresh()

    def finish(self, total_records: int = 0) -> None:
        if self._live is not None:
            try:
                self._live.update(self._render(final=True))
                self._live.stop()
            except Exception:
                pass

    def stop(self) -> None:
        if self._live is not None:
            try:
                self._live.stop()
            except Exception:
                pass

    def _refresh(self) -> None:
        if self._live is not None:
            self._frame += 1
            try:
                self._live.update(self._render())
            except Exception:
                pass

    def _render(self, final: bool = False) -> Table | Group:
        spinner_char = SPINNER_FRAMES[self._frame % len(SPINNER_FRAMES)]

        table = Table(
            show_header=True,
            header_style="bold",
            box=None,
            padding=(0, 1),
            show_edge=False,
        )
        table.add_column("Resource", style="dim", width=15)
        table.add_column("Records", justify="right", width=14)

        for name in self._resource_order:
            r = self._resources[name]

            if r.status == "fetching":
                icon = f"[bold yellow]{spinner_char}[/bold yellow]"
                style = "yellow"
            elif r.status == "done":
                icon = "[green]✓[/green]"
                style = "green"
            elif r.status == "warning":
                icon = "[yellow]⚠[/yellow]"
                style = "yellow"
            elif r.status == "error":
                icon = "[red]✗[/red]"
                style = "red"
            else:
                icon = "·"
                style = "dim"

            if r.count > 0:
                record_str = f"{icon} {r.count:,}"
            else:
                record_str = f"{icon} —"

            table.add_row(name, record_str, style=style)

        completed = sum(
            1 for r in self._resources.values() if r.status in ("done", "warning")
        )
        remaining = self.total_resources - completed

        if remaining > 0 and not final:
            table.add_row(
                "[dim]remaining[/dim]",
                f"[dim]{remaining} resources[/dim]",
                style="dim",
            )

        renderables: list = [table]
        if final:
            if self._warnings:
                for w in self._warnings[-5:]:
                    renderables.append(Text(f"  ⚠ {w}", style="yellow"))
            if self._errors:
                for e in self._errors[-5:]:
                    renderables.append(Text(f"  ✗ {e}", style="red"))

        if len(renderables) == 1:
            return renderables[0]
        return Group(*renderables)
