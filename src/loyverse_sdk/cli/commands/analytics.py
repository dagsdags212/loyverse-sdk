"""
CLI subcommands for business analytics on exported Loyverse data.

Provides ``loyverse analytics <command>`` with the following groups:

    revenue         Daily totals, growth rates, store breakdowns
    products        Top items, category mix, basket composition
    customers       RFM segmentation, top spenders, retention
    employees       Revenue per employee, tip analysis
    operations      Peak hours, payment mix, discounts, dining options
    profitability   Gross profit, margins, COGS tracking
    inventory       Turnover, stock value, low-stock alerts
    time-series     Moving averages, week-over-week, monthly trends

All commands accept ``--db-path`` (defaults to ``LOYVERSE_DB_PATH`` or
``loyverse.db``) and ``--format`` (``table``, ``json``, ``csv``).

Examples:

    loyverse analytics revenue --days 30
    loyverse analytics revenue --by-month --format csv
    loyverse analytics products --by-category --days 90
    loyverse analytics customers --rfm
    loyverse analytics profitability --margins --sort-by margin_pct
    loyverse analytics inventory --turnover --days 30
    loyverse analytics inventory --low-stock
    loyverse analytics time-series --monthly --months 6
"""

import re
from datetime import datetime

import duckdb
import typer

from loyverse_sdk.analytics import AnalyticsEngine
from loyverse_sdk.analytics._base import Format
from loyverse_sdk.cli._async import console
from loyverse_sdk.cli._display import build_table_from_dicts
from loyverse_sdk.core.config import config
from loyverse_sdk.core.paths import resolve_db_path

# ── shared helpers ───────────────────────────────────────────────────────


def _open_engine(db_path: str | None = None) -> AnalyticsEngine:
    db_path = str(resolve_db_path(db_path or config.LOYVERSE_DB_PATH))
    try:
        return AnalyticsEngine(db_path)
    except FileNotFoundError:
        console.print(
            f"\n[red]Database not found:[/red] {db_path}\n\n"
            f"[dim]Run [bold]loyverse export[/bold] "
            f"to pull data from the Loyverse API first.[/dim]\n"
        )
        raise typer.Exit(1) from None


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


def _output(result, fmt: str) -> None:
    """Handle mixed return types (DataFrame, dict, scalar, or pre-formatted str)."""
    if isinstance(result, str):
        console.print(result)
        return

    if hasattr(result, "to_dicts"):
        data = result.to_dicts()
        if not data:
            console.print("[dim]No data.[/dim]")
            return
        if fmt == "table":
            table = build_table_from_dicts(data, max_cols=len(result.columns))
            console.print(table)
            return

    if fmt == "json":
        import json
        console.print_json(json.dumps(result, default=str))
    elif fmt == "csv":
        if hasattr(result, "write_csv"):
            result.write_csv(None)
    else:
        console.print(result)


def _parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        console.print(f"[red]Invalid date: {value}[/red] (use YYYY-MM-DD)")
        raise typer.Exit(1) from None


# ── option constants ─────────────────────────────────────────────────────


DB_OPTION = typer.Option(None, "--db-path", "-d", help="Path to DuckDB database")
DAYS_OPTION = typer.Option(30, "--days", "-n", help="Number of past days to analyze")
STORE_OPTION = typer.Option(None, "--store-id", "-s", help="Filter by store UUID")
DATE_START = typer.Option(
    None, "--date-start", help="Start date (ISO-8601, e.g. 2026-01-01)"
)
DATE_END = typer.Option(
    None, "--date-end", help="End date (ISO-8601, e.g. 2026-12-31)"
)
FORMAT_OPTION = typer.Option(
    "table", "--format", "-f", help="Output format: table, json, csv"
)
N_OPTION = typer.Option(10, "--top-n", "-t", help="Number of top results to return")
MONTHS_OPTION = typer.Option(12, "--months", "-m", help="Number of months to include")
WINDOW_OPTION = typer.Option(7, "--window", "-w", help="Moving average window in days")


# ── Typer app ────────────────────────────────────────────────────────────


analytics_app = typer.Typer(
    name="analytics",
    help="Business analytics on exported Loyverse data",
    no_args_is_help=True,
)


# ══════════════════════════════════════════════════════════════════════════
# revenue
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="revenue")
def analytics_revenue(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    by_store: bool = typer.Option(
        False, "--by-store", help="Revenue and transaction counts per store location"
    ),
    growth: bool = typer.Option(
        False,
        "--growth",
        help="Month-over-month revenue growth with percentage change",
    ),
    by_month: bool = typer.Option(
        False,
        "--by-month",
        help="Revenue aggregated by calendar month instead of daily",
    ),
    refunds: bool = typer.Option(
        False,
        "--refunds",
        help="Daily refund totals and refund rate as %% of sales",
    ),
) -> None:
    """Revenue analysis — daily totals, store breakdowns, growth rates, refunds.

    Default shows daily revenue, transaction count, and average ticket
    for the past 30 days.

    Examples:
        loyverse analytics revenue --days 90
        loyverse analytics revenue --by-store
        loyverse analytics revenue --by-month --format csv
        loyverse analytics revenue --growth
        loyverse analytics revenue --refunds --days 60
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if growth:
            result = engine.revenue.revenue_growth(
                period="month", months=12, store_id=store_id, fmt=af,
            )
        elif by_store:
            result = engine.revenue.revenue_by_store(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif by_month:
            result = engine.revenue.total_revenue_by_month(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif refunds:
            result = engine.revenue.refund_rate(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        else:
            result = engine.revenue.daily_revenue(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# products
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="products")
def analytics_products(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    top_n: int = N_OPTION,
    by_category: bool = typer.Option(
        False,
        "--by-category",
        help="Revenue breakdown by product category with %% share of total",
    ),
    basket: bool = typer.Option(
        False,
        "--basket",
        help="Average items per transaction and distribution percentiles",
    ),
) -> None:
    """Product analytics — top-selling items, category mix, basket size.

    Default shows the top 10 items ranked by revenue.

    Examples:
        loyverse analytics products --days 30
        loyverse analytics products --top-n 20 --store-id <UUID>
        loyverse analytics products --by-category --days 90
        loyverse analytics products --basket
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if by_category:
            result = engine.products.revenue_by_category(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif basket:
            result = engine.products.items_per_transaction(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        else:
            result = engine.products.top_items(
                date_start=ds, date_end=de, days=days, store_id=store_id,
                n=top_n, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# customers
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="customers")
def analytics_customers(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    top_n: int = N_OPTION,
    rfm: bool = typer.Option(
        False,
        "--rfm",
        help="RFM segmentation — scores every customer on recency, frequency, monetary value",
    ),
    retention: bool = typer.Option(
        False,
        "--retention",
        help="Percentage of customers who visited more than once in the period",
    ),
    unique: bool = typer.Option(
        False,
        "--unique",
        help="Count of distinct customers who made a purchase",
    ),
    new_vs_returning: bool = typer.Option(
        False,
        "--new-vs-returning",
        help="Daily new vs returning customer counts",
    ),
    visit_dist: bool = typer.Option(
        False,
        "--visit-distribution",
        help="Histogram of visit counts across the customer base",
    ),
) -> None:
    """Customer analytics — segmentation, retention, top spenders, visit patterns.

    Default shows the top 10 customers by total spend.

    Examples:
        loyverse analytics customers --days 30
        loyverse analytics customers --rfm
        loyverse analytics customers --retention --days 90
        loyverse analytics customers --unique --store-id <UUID>
        loyverse analytics customers --new-vs-returning
        loyverse analytics customers --visit-distribution --days 365
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if rfm:
            result = engine.customers.rfm_analysis(fmt=af)
        elif retention:
            result = engine.customers.retention_rate(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif unique:
            result = engine.customers.unique_customers(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif new_vs_returning:
            result = engine.customers.new_vs_returning(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif visit_dist:
            result = engine.customers.customer_visit_distribution(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        else:
            result = engine.customers.top_customers(
                date_start=ds, date_end=de, days=days, store_id=store_id,
                n=top_n, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# employees
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="employees")
def analytics_employees(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    tips: bool = typer.Option(
        False, "--tips", help="Tip totals, average tip, and tip rate per employee"
    ),
    daily: bool = typer.Option(
        False, "--daily", help="Daily transaction counts and revenue per employee"
    ),
) -> None:
    """Employee performance — revenue, transactions, tips.

    Default shows revenue, transaction count, average ticket, and tips
    per employee for the period.

    Examples:
        loyverse analytics employees --days 30
        loyverse analytics employees --tips
        loyverse analytics employees --daily --days 90
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if tips:
            result = engine.employees.tip_by_employee(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif daily:
            result = engine.employees.employee_daily_summary(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        else:
            result = engine.employees.revenue_by_employee(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# operations
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="operations")
def analytics_operations(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    peak_hours: bool = typer.Option(
        False,
        "--peak-hours",
        help="Transaction count and revenue by hour of day",
    ),
    peak_days: bool = typer.Option(
        False,
        "--peak-days",
        help="Transaction count and revenue by day of week",
    ),
    payments: bool = typer.Option(
        False, "--payments", help="Revenue and transaction count by payment method"
    ),
    discounts: bool = typer.Option(
        False, "--discounts", help="Daily discount totals and discount rate as %%"
    ),
    tips_analysis: bool = typer.Option(
        False, "--tips", help="Daily tip totals and average tip per transaction"
    ),
    dining: bool = typer.Option(
        False, "--dining", help="Revenue breakdown by dining option (dine-in, takeaway, etc.)"
    ),
) -> None:
    """Operational metrics — peak hours, payment mix, discounts, tips, dining.

    Default shows transaction count and revenue by peak hours.

    Examples:
        loyverse analytics operations --peak-hours --days 30
        loyverse analytics operations --peak-days
        loyverse analytics operations --payments
        loyverse analytics operations --discounts --days 90
        loyverse analytics operations --tips
        loyverse analytics operations --dining
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if peak_hours:
            result = engine.operations.peak_hours(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif peak_days:
            result = engine.operations.peak_days(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif payments:
            result = engine.operations.payment_method_split(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        elif discounts:
            result = engine.operations.discount_analysis(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif tips_analysis:
            result = engine.operations.tip_analysis(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif dining:
            result = engine.operations.dining_option_split(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        else:
            result = engine.operations.peak_hours(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# profitability
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="profitability")
def analytics_profitability(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    top_n: int = typer.Option(20, "--top-n", "-t", help="Number of items to show"),
    margins: bool = typer.Option(
        False,
        "--margins",
        help="Item-level gross profit margins — revenue, cost, margin, margin %%",
    ),
    sort_by: str = typer.Option(
        "gross_profit",
        "--sort-by",
        help="Sort item margins by: gross_profit, margin_pct, revenue",
    ),
    trend: bool = typer.Option(
        False,
        "--trend",
        help="Daily margin percentage trend with period-over-period change",
    ),
    by_category: bool = typer.Option(
        False,
        "--by-category",
        help="Gross profit and margin broken down by product category",
    ),
    missing: bool = typer.Option(
        False,
        "--missing-cost",
        help="Items sold without COGS data — must set variant costs in Loyverse",
    ),
) -> None:
    """Profitability analysis — gross profit, margins, COGS coverage.

    Default shows daily gross profit, cost, and margin percentage for the
    past 30 days. Items without cost data in Loyverse will show margin_pct
    as NULL.

    Examples:
        loyverse analytics profitability --days 30
        loyverse analytics profitability --margins --sort-by margin_pct
        loyverse analytics profitability --trend --days 90
        loyverse analytics profitability --by-category
        loyverse analytics profitability --missing-cost
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if margins:
            result = engine.profitability.profit_margins(
                date_start=ds, date_end=de, days=days,
                store_id=store_id, n=top_n, sort_by=sort_by, fmt=af,
            )
        elif trend:
            result = engine.profitability.margin_trend(
                date_start=ds, date_end=de, days=days,
                store_id=store_id, fmt=af,
            )
        elif by_category:
            result = engine.profitability.profit_by_category(
                date_start=ds, date_end=de, days=days,
                store_id=store_id, fmt=af,
            )
        elif missing:
            result = engine.profitability.items_without_cost(fmt=af)
        else:
            result = engine.profitability.gross_profit(
                date_start=ds, date_end=de, days=days,
                store_id=store_id, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# inventory
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="inventory")
def analytics_inventory(
    db_path: str | None = DB_OPTION,
    days: int = DAYS_OPTION,
    store_id: str | None = STORE_OPTION,
    fmt: str = FORMAT_OPTION,
    top_n: int = typer.Option(20, "--top-n", "-t", help="Number of items to show"),
    turnover: bool = typer.Option(
        False,
        "--turnover",
        help="Inventory turnover rate — units sold ÷ current stock, with days-to-sell estimate",
    ),
    value: bool = typer.Option(
        False,
        "--value",
        help="Current inventory value — stock × unit cost per variant",
    ),
    by_store: bool = typer.Option(
        False,
        "--by-store",
        help="Inventory value broken down by store location",
    ),
    low_stock: bool = typer.Option(
        False,
        "--low-stock",
        help="Items at or below stock threshold with last-sold date",
    ),
    threshold: int = typer.Option(
        5,
        "--threshold",
        help="Low-stock alert threshold (units, default 5)",
    ),
    never_sold: bool = typer.Option(
        False,
        "--never-sold",
        help="Items with stock on hand that have not sold in the period (dead stock)",
    ),
) -> None:
    """Inventory analytics — turnover, stock value, low-stock alerts, dead stock.

    Default shows inventory turnover rate across all items.

    Examples:
        loyverse analytics inventory --turnover --days 30
        loyverse analytics inventory --value
        loyverse analytics inventory --by-store
        loyverse analytics inventory --low-stock --threshold 3
        loyverse analytics inventory --never-sold --days 60
    """
    engine = _open_engine(db_path)
    try:
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if turnover:
            result = engine.inventory.turnover(
                days=days, store_id=store_id, n=top_n, fmt=af,
            )
        elif value:
            result = engine.inventory.stock_value(
                store_id=store_id, fmt=af,
            )
        elif by_store:
            result = engine.inventory.stock_value_by_store(fmt=af)
        elif low_stock:
            result = engine.inventory.low_stock(
                store_id=store_id, threshold=threshold, fmt=af,
            )
        elif never_sold:
            result = engine.inventory.items_never_sold(
                days=days, fmt=af,
            )
        else:
            result = engine.inventory.turnover(
                days=days, store_id=store_id, n=top_n, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()


# ══════════════════════════════════════════════════════════════════════════
# time-series
# ══════════════════════════════════════════════════════════════════════════


@analytics_app.command(name="time-series")
def analytics_time_series(
    db_path: str | None = DB_OPTION,
    days: int = typer.Option(90, "--days", "-n", help="Number of past days to analyze"),
    store_id: str | None = STORE_OPTION,
    date_start: str | None = DATE_START,
    date_end: str | None = DATE_END,
    fmt: str = FORMAT_OPTION,
    window: int = WINDOW_OPTION,
    moving_average: bool = typer.Option(
        True,
        "--moving-average/--no-moving-average",
        help="N-day moving average of daily revenue (default: on)",
    ),
    wow: bool = typer.Option(
        False,
        "--wow",
        help="Daily revenue with week-over-week percentage growth",
    ),
    monthly: bool = typer.Option(
        False,
        "--monthly",
        help="Monthly summary with revenue, customers, and month-over-month growth",
    ),
    dod: bool = typer.Option(
        False,
        "--dod",
        help="Daily revenue with day-over-day percentage change",
    ),
    months: int = MONTHS_OPTION,
) -> None:
    """Time-series analysis — moving averages, growth rates, monthly trends.

    Default shows daily revenue with a 7-day moving average.

    Examples:
        loyverse analytics time-series --days 90 --window 14
        loyverse analytics time-series --wow
        loyverse analytics time-series --monthly --months 6
        loyverse analytics time-series --dod --days 14
    """
    engine = _open_engine(db_path)
    try:
        ds = _parse_date(date_start) if date_start else None
        de = _parse_date(date_end) if date_end else None
        af: Format = "dataframe" if fmt == "table" else fmt  # type: ignore[assignment]

        if wow:
            result = engine.time_series.week_over_week_growth(
                date_start=ds, date_end=de, days=days, fmt=af,
            )
        elif monthly:
            result = engine.time_series.monthly_summary(
                months=months, store_id=store_id, fmt=af,
            )
        elif dod:
            result = engine.time_series.day_over_day(
                date_start=ds, date_end=de, days=days, store_id=store_id, fmt=af,
            )
        else:
            result = engine.time_series.moving_average_revenue(
                window=window, date_start=ds, date_end=de,
                days=days, store_id=store_id, fmt=af,
            )
        _output(result, fmt)
    except duckdb.CatalogException as e:
        _handle_query_error(db_path, e)
    finally:
        engine.close()
