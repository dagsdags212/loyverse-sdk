"""
CLI subcommands for the analytics engine.

Provides ``loyverse analytics <metric>`` commands that mirror the Python
analytics API. The ``--db-path`` flag is optional and defaults to the
``LOYVERSE_DB_PATH`` env var or ``loyverse.db``:

    loyverse analytics revenue --days 30
    loyverse analytics revenue --by-month --days 365
    loyverse analytics products --top-n 10
    loyverse analytics customers --rfm
    loyverse analytics employees
    loyverse analytics operations --peak-hours
    loyverse analytics time-series --monthly
"""

import re
from datetime import datetime

import duckdb
import typer

from loyverse_sdk.analytics import AnalyticsEngine
from loyverse_sdk.cli._async import console
from loyverse_sdk.core.config import config
from loyverse_sdk.core.paths import resolve_db_path


def _open_engine(db_path: str | None = None) -> AnalyticsEngine:
    db_path = str(resolve_db_path(db_path or config.LOYVERSE_DB_PATH))
    try:
        return AnalyticsEngine(db_path)
    except FileNotFoundError as e:
        console.print(
            f"\n[red]Database not found:[/red] {db_path}\n\n"
            f"[dim]Run [bold]loyverse export[/bold] "
            f"to pull data from the Loyverse API first.[/dim]\n"
        )
        raise typer.Exit(1)


def _handle_query_error(db_path: str, exc: Exception) -> None:
    msg = str(exc)
    match = re.search(r"Table with name (\w+) does not exist", msg)
    if match:
        table = match.group(1)
        console.print(
            f"\n[red]Missing table:[/red] '{table}' not found in the database.\n\n"
            f"[dim]The database may be incomplete. "
            f"Run [bold]loyverse export {db_path}[/bold] "
            f"to re-export all data.[/dim]\n"
        )
    else:
        console.print(f"\n[red]Query error:[/red] {msg}\n")
    raise typer.Exit(1)


from loyverse_sdk.cli._display import build_table_from_dicts

analytics_app = typer.Typer(
    name="analytics",
    help="Business analytics on exported Loyverse data",
    no_args_is_help=True,
)

DB_OPTION = typer.Option(None, "--db-path", "-d", help="Path to DuckDB database")
DAYS_OPTION = typer.Option(30, "--days", "-n", help="Number of days to look back")
STORE_OPTION = typer.Option(None, "--store-id", "-s", help="Filter by store ID")
DATE_START = typer.Option(None, "--date-start", help="Start date (YYYY-MM-DD)")
DATE_END = typer.Option(None, "--date-end", help="End date (YYYY-MM-DD)")
FORMAT_OPTION = typer.Option(
    "table", "--format", "-f", help="Output format: table, json, csv"
)
N_OPTION = typer.Option(10, "--top-n", "-t", help="Number of top results")
PERIOD_OPTION = typer.Option("month", "--period", "-p", help="Period: month or week")
MONTHS_OPTION = typer.Option(12, "--months", "-m", help="Number of months")
WINDOW_OPTION = typer.Option(7, "--window", "-w", help="Moving average window (days)")


def _output(df, fmt: str) -> None:
    data = df.to_dicts()
    if not data:
        console.print("[dim]No data.[/dim]")
        return

    if fmt == "json":
        import json

        console.print_json(json.dumps(data))
    elif fmt == "csv":
        df.write_csv(None)
    else:
        table = build_table_from_dicts(data, max_cols=len(df.columns))
        console.print(table)


# ── revenue ──────────────────────────────────────────────────────────────


@analytics_app.command(name="revenue")
def analytics_revenue(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    by_store: bool = typer.Option(False, "--by-store", help="Break down by store"),
    growth: bool = typer.Option(
        False, "--growth", help="Show period-over-period growth"
    ),
    by_month: bool = typer.Option(
        False, "--by-month", help="Aggregate revenue by month"
    ),
) -> None:
    """Daily revenue, totals, and growth rates."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if growth:
            df = engine.revenue.revenue_growth(
                period="month",
                months=12,
                store_id=store_id,
            )
        elif by_store:
            df = engine.revenue.revenue_by_store(
                date_start=ds,
                date_end=de,
                days=days,
            )
        elif by_month:
            df = engine.revenue.total_revenue_by_month(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        else:
            df = engine.revenue.daily_revenue(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ── products ─────────────────────────────────────────────────────────────


@analytics_app.command(name="products")
def analytics_products(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    top_n: int = N_OPTION,
    by_category: bool = typer.Option(
        False,
        "--by-category",
        help="Revenue breakdown by category",
    ),
    basket: bool = typer.Option(
        False,
        "--basket",
        help="Items per transaction analysis",
    ),
) -> None:
    """Top items, category mix, and basket composition."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if by_category:
            df = engine.products.revenue_by_category(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        elif basket:
            result = engine.products.items_per_transaction(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
            console.print(
                f"[bold]Average items per transaction:[/bold] {result['average']}"
            )
            console.print("[bold]Distribution:[/bold]")
            console.print(result["distribution"])
            return
        else:
            df = engine.products.top_items(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
                n=top_n,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ── customers ────────────────────────────────────────────────────────────


@analytics_app.command(name="customers")
def analytics_customers(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    top_n: int = N_OPTION,
    rfm: bool = typer.Option(False, "--rfm", help="RFM segmentation analysis"),
    retention: bool = typer.Option(
        False, "--retention", help="Customer retention rate"
    ),
    unique: bool = typer.Option(
        False, "--unique", help="Count of unique customers in the period"
    ),
) -> None:
    """Customer analytics: RFM segmentation, top spenders, retention."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if rfm:
            df = engine.customers.rfm_analysis()
        elif retention:
            rate = engine.customers.retention_rate(
                date_start=ds,
                date_end=de,
                days=days,
            )
            console.print(f"[bold]Retention rate:[/bold] {rate}%")
            return
        elif unique:
            count = engine.customers.unique_customers(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
            console.print(f"[bold]Unique customers:[/bold] {count}")
            return
        else:
            df = engine.customers.top_customers(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
                n=top_n,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ── employees ────────────────────────────────────────────────────────────


@analytics_app.command(name="employees")
def analytics_employees(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    tips: bool = typer.Option(False, "--tips", help="Show tip analysis"),
) -> None:
    """Employee performance: revenue, transactions, tips."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if tips:
            df = engine.employees.tip_by_employee(
                date_start=ds,
                date_end=de,
                days=days,
            )
        else:
            df = engine.employees.revenue_by_employee(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ── operations ───────────────────────────────────────────────────────────


@analytics_app.command(name="operations")
def analytics_operations(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    peak_hours: bool = typer.Option(
        False, "--peak-hours", help="Transaction count by hour of day"
    ),
    peak_days: bool = typer.Option(
        False, "--peak-days", help="Transaction count by day of week"
    ),
    payments: bool = typer.Option(False, "--payments", help="Payment method breakdown"),
    discounts: bool = typer.Option(False, "--discounts", help="Discount analysis"),
    tip_analysis: bool = typer.Option(False, "--tips", help="Tip analysis"),
    dining: bool = typer.Option(False, "--dining", help="Dining option breakdown"),
) -> None:
    """Operational metrics: peak hours, payment mix, discounts, tips."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if peak_hours:
            df = engine.operations.peak_hours(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        elif peak_days:
            df = engine.operations.peak_days(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        elif payments:
            df = engine.operations.payment_method_split(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        elif discounts:
            df = engine.operations.discount_analysis(
                date_start=ds,
                date_end=de,
                days=days,
            )
        elif tip_analysis:
            df = engine.operations.tip_analysis(
                date_start=ds,
                date_end=de,
                days=days,
            )
        elif dining:
            df = engine.operations.dining_option_split(
                date_start=ds,
                date_end=de,
                days=days,
            )
        else:
            df = engine.operations.peak_hours(
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ── time-series ──────────────────────────────────────────────────────────


@analytics_app.command(name="time-series")
def analytics_time_series(
    db_path: str | None = DB_OPTION,
    days: int = typer.Option(90, "--days", "-n", help="Number of days to look back"),
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    format: str = FORMAT_OPTION,
    window: int = WINDOW_OPTION,
    moving_average: bool = typer.Option(
        True,
        "--moving-average/--no-moving-average",
        help="N-day moving average of daily revenue",
    ),
    wow: bool = typer.Option(False, "--wow", help="Week-over-week growth"),
    monthly: bool = typer.Option(
        False, "--monthly", help="Monthly summary with MoM growth"
    ),
    months: int = MONTHS_OPTION,
) -> None:
    """Time-series analysis: moving averages, growth rates, monthly trends."""
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None

        if wow:
            df = engine.time_series.week_over_week_growth(
                date_start=ds,
                date_end=de,
                days=days,
            )
        elif monthly:
            df = engine.time_series.monthly_summary(
                months=months,
                store_id=store_id,
            )
        else:
            df = engine.time_series.moving_average_revenue(
                window=window,
                date_start=ds,
                date_end=de,
                days=days,
                store_id=store_id,
            )
        _output(df, format)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        console.print(f"[red]Invalid date: {value}[/red] (use YYYY-MM-DD)")
        raise typer.Exit(1)
