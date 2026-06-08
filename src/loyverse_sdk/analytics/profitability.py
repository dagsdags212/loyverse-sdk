"""
Profitability analytics — gross profit, margins, margin trends.

Uses per-line-item COGS data from ``receipt_line_items.cost_total``
captured at time of sale to calculate true gross profit.
"""

from datetime import datetime

import duckdb
import polars as pl

from loyverse_sdk.analytics._base import (
    Format,
    _query,
    _scalar,
    _scalar_to_output,
    date_filter,
)


class ProfitabilityAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def gross_profit(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Daily gross profit and margin percentage.

        Returns columns: date, revenue, cost, gross_profit, margin_pct.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                r.receipt_date::DATE AS date,
                ROUND(SUM(l.total_money), 2) AS revenue,
                ROUND(COALESCE(SUM(l.cost_total), 0), 2) AS cost,
                ROUND(SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0), 2) AS gross_profit,
                ROUND(
                    (SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0))
                    / NULLIF(SUM(l.total_money), 0) * 100, 1
                ) AS margin_pct
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def profit_by_category(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Gross profit and margin broken down by product category.

        Returns columns: category, revenue, cost, gross_profit, margin_pct.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                COALESCE(c.name, 'Uncategorised') AS category,
                ROUND(SUM(l.total_money), 2) AS revenue,
                ROUND(COALESCE(SUM(l.cost_total), 0), 2) AS cost,
                ROUND(SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0), 2) AS gross_profit,
                ROUND(
                    (SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0))
                    / NULLIF(SUM(l.total_money), 0) * 100, 1
                ) AS margin_pct
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            JOIN items i ON l.item_id = i.id
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY c.name
            ORDER BY gross_profit DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def profit_margins(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        n: int = 20,
        sort_by: str = "gross_profit",
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Item-level profit margins with COGS.

        Ranks items by profit, margin %, or revenue. Items missing cost data
        are shown with margin_pct = NULL.

        Returns columns: item, qty_sold, revenue, cost, gross_profit, margin_pct.

        Args:
            sort_by: 'gross_profit', 'margin_pct', or 'revenue'.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        order_col = {
            "gross_profit": "gross_profit DESC",
            "margin_pct": "margin_pct DESC NULLS LAST",
            "revenue": "revenue DESC",
        }.get(sort_by, "gross_profit DESC")

        return _query(
            self._conn,
            f"""
            SELECT
                l.item_name AS item,
                SUM(l.quantity) AS qty_sold,
                ROUND(SUM(l.total_money), 2) AS revenue,
                ROUND(COALESCE(SUM(l.cost_total), 0), 2) AS cost,
                ROUND(SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0), 2) AS gross_profit,
                ROUND(
                    (SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0))
                    / NULLIF(SUM(l.total_money), 0) * 100, 1
                ) AS margin_pct
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY l.item_name
            ORDER BY {order_col}
            LIMIT ?
        """,
            dp + sp + [n],
            fmt=fmt,
        )

    def margin_trend(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 90,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Daily margin percentage trend with revenue and cost context.

        Returns columns: date, revenue, cost, gross_profit, margin_pct,
        prev_margin_pct, margin_change.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            WITH daily_margin AS (
                SELECT
                    r.receipt_date::DATE AS date,
                    ROUND(SUM(l.total_money), 2) AS revenue,
                    ROUND(COALESCE(SUM(l.cost_total), 0), 2) AS cost,
                    ROUND(SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0), 2) AS gross_profit,
                    ROUND(
                        (SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0))
                        / NULLIF(SUM(l.total_money), 0) * 100, 1
                    ) AS margin_pct
                FROM receipt_line_items l
                JOIN receipts r ON l.receipt_id = r.receipt_number
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}{sf}
                GROUP BY date
            )
            SELECT
                date,
                revenue,
                cost,
                gross_profit,
                margin_pct,
                LAG(margin_pct) OVER (ORDER BY date) AS prev_margin_pct,
                ROUND(
                    margin_pct - LAG(margin_pct) OVER (ORDER BY date), 1
                ) AS margin_change
            FROM daily_margin
            ORDER BY date DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def overall_margin(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> float | str:
        """Single-period overall gross margin percentage."""
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        raw = (
            _scalar(
                self._conn,
                f"""
                SELECT ROUND(
                    (SUM(l.total_money) - COALESCE(SUM(l.cost_total), 0))
                    / NULLIF(SUM(l.total_money), 0) * 100, 1
                )
                FROM receipt_line_items l
                JOIN receipts r ON l.receipt_id = r.receipt_number
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}{sf}
            """,
                dp + sp,
            )
            or 0.0
        )
        if fmt == "dataframe":
            return raw
        return _scalar_to_output(raw, fmt, "overall_margin_pct")

    def items_without_cost(
        self,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """List items that have been sold but have no COGS data in line items.

        Items without cost tracking won't appear in margin calculations.
        """
        return _query(
            self._conn,
            """
            SELECT DISTINCT
                l.item_name AS item,
                COUNT(*) AS times_sold,
                ROUND(SUM(l.total_money), 2) AS total_revenue
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL
              AND (l.cost IS NULL OR l.cost_total IS NULL)
            GROUP BY l.item_name
            ORDER BY total_revenue DESC
        """,
            fmt=fmt,
        )
