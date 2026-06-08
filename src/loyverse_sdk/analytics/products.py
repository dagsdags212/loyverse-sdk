"""
Product / service analytics — category mix, top items, basket composition.
"""

from datetime import datetime

import duckdb
import polars as pl

from loyverse_sdk.analytics._base import (
    Format,
    _dict_to_output,
    _query,
    _scalar,
    date_filter,
)


class ProductAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def revenue_by_category(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Revenue breakdown by product category, with share percentages."""
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
                COUNT(DISTINCT r.receipt_number) AS tx_count,
                ROUND(SUM(l.total_money), 2) AS revenue,
                SUM(l.quantity) AS units_sold,
                ROUND(
                    SUM(l.total_money)
                    / NULLIF(SUM(SUM(l.total_money)) OVER (), 0) * 100,
                    1
                ) AS pct_share
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            JOIN items i ON l.item_id = i.id
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY c.name
            ORDER BY revenue DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def top_items(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        n: int = 10,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Top N items by revenue and quantity sold."""
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
                l.item_name AS item,
                SUM(l.quantity) AS total_qty,
                ROUND(SUM(l.total_money), 2) AS total_revenue,
                COUNT(DISTINCT r.receipt_number) AS tx_count
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY l.item_name
            ORDER BY total_revenue DESC
            LIMIT ?
        """,
            dp + sp + [n],
            fmt=fmt,
        )

    def items_per_transaction(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> dict | str:
        """Average items per transaction, plus distribution percentiles."""
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND r.store_id = ?"
            sp = [store_id]

        avg_items = (
            _scalar(
                self._conn,
                f"""
            SELECT ROUND(AVG(line_count * 1.0), 1)
            FROM (
                SELECT r.receipt_number, COUNT(l.id) AS line_count
                FROM receipts r
                JOIN receipt_line_items l ON r.receipt_number = l.receipt_id
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}{sf}
                GROUP BY r.receipt_number
            )
        """,
                dp + sp,
            )
            or 0
        )

        percentiles = _query(
            self._conn,
            f"""
            WITH counts AS (
                SELECT COUNT(l.id) AS line_count
                FROM receipts r
                JOIN receipt_line_items l ON r.receipt_number = l.receipt_id
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}{sf}
                GROUP BY r.receipt_number
            )
            SELECT
                MIN(line_count) AS min_items,
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY line_count) AS p25,
                PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY line_count) AS p50,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY line_count) AS p75,
                MAX(line_count) AS max_items
            FROM counts
        """,
            dp + sp,
        )

        result = {"average": avg_items, "distribution": percentiles}
        if fmt == "dataframe":
            return result
        return _dict_to_output(result, fmt)

    def category_mix_trend(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 90,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Monthly category revenue share over time."""
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                DATE_TRUNC('MONTH', r.receipt_date) AS month,
                COALESCE(c.name, 'Uncategorised') AS category,
                ROUND(SUM(l.total_money), 2) AS revenue
            FROM receipt_line_items l
            JOIN receipts r ON l.receipt_id = r.receipt_number
            JOIN items i ON l.item_id = i.id
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}
            GROUP BY month, c.name
            ORDER BY month DESC, revenue DESC
        """,
            dp,
            fmt=fmt,
        )
