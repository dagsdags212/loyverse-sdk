import json
from typing import Any

from rich.table import Table


def items_key(endpoint: Any) -> str:
    """Get the JSON key used for the items array in API responses."""
    key: str | None = getattr(endpoint, "items_key", None)
    return key if key else endpoint.path


def flatten_for_export(items: list[Any]) -> list[dict[str, object]]:
    """Convert Pydantic model instances to plain dicts with list/dict
    fields serialised as JSON strings so they survive CSV / Parquet."""
    flat: list[dict[str, object]] = []
    for item in items:
        d: dict[str, object] = item.model_dump()
        for key, val in d.items():
            if isinstance(val, (list, dict)):
                d[key] = json.dumps(val, default=str)
        flat.append(d)
    return flat


def build_table(items: list[Any], max_cols: int = 7) -> Table:
    """Build a Rich table from a list of Pydantic model instances."""
    if not items:
        return Table(title="(empty)")

    model = type(items[0])
    flat: list[str] = []
    for name, fi in model.model_fields.items():
        origin = getattr(fi.annotation, "__origin__", None)
        if origin in (list, dict):
            continue
        flat.append(name)

    cols = flat[:max_cols]
    label = f" ({len(items)} record{'s' if len(items) != 1 else ''})"
    table = Table(title=f"{model.__name__}{label}", header_style="bold cyan")
    for c in cols:
        table.add_column(c, no_wrap=True)

    for item in items:
        row: list[str] = []
        for c in cols:
            val = getattr(item, c, None)
            if val is None:
                row.append("\u2014")
            else:
                s = str(val)
                row.append(s[:72] + ("\u2026" if len(s) > 72 else ""))
        table.add_row(*row)
    return table


def build_table_from_dicts(
    rows: list[dict[str, Any]],
    title: str = "Results",
    max_cols: int = 8,
) -> Table:
    """Build a Rich table from a list of plain dictionaries."""
    if not rows:
        return Table(title="(empty)")

    cols = list(rows[0].keys())[:max_cols]
    label = f" ({len(rows)} record{'s' if len(rows) != 1 else ''})"
    table = Table(title=f"{title}{label}", header_style="bold cyan")
    for c in cols:
        width = min(max(len(c), 10), 24)
        table.add_column(c, width=width)

    for row in rows:
        cells: list[str] = []
        for c in cols:
            val = row.get(c)
            if val is None:
                cells.append("\u2014")
            else:
                s = str(val)
                cells.append(s[:72] + ("\u2026" if len(s) > 72 else ""))
        table.add_row(*cells)
    return table
