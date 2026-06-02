"""
Revenue analytics — daily totals, growth rates, average transaction values.
"""

from datetime import datetime
from typing import Optional
import duckdb
import polars as pl

from loyverse_sdk.analytics._base import date_filter, store_filter, _query, _scalar


class RevenueAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def daily_revenue(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Daily revenue, transaction count, and average ticket.

        Returns a DataFrame with columns: date, revenue, tx_count, avg_ticket.
        """
        df, dp = date_filter("receipt_date", date_start, date_end, days)
        sf, sp = store_filter(store_id)

        return _query(
            self._conn,
            f"""
            SELECT
                receipt_date::DATE AS date,
                SUM(total_money) AS revenue,
                COUNT(*) AS tx_count,
                ROUND(AVG(total_money), 2) AS avg_ticket
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}{sf}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp + sp,
        )

    def revenue_by_store(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
    ) -> pl.DataFrame:
        """Revenue and transaction counts broken down by store."""
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                s.name AS store_name,
                COUNT(*) AS tx_count,
                ROUND(SUM(r.total_money), 2) AS revenue,
                ROUND(AVG(r.total_money), 2) AS avg_ticket
            FROM receipts r
            JOIN stores s ON r.store_id = s.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}
            GROUP BY s.name
            ORDER BY revenue DESC
        """,
            dp,
        )

    def revenue_growth(
        self,
        period: str = "month",
        months: int = 12,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Period-over-period revenue with growth rate.

        Args:
            period: 'month' or 'week'.
            months: Number of periods to return.
        """
        trunc = "MONTH" if period == "month" else "WEEK"
        sf, sp = store_filter(store_id)

        return _query(
            self._conn,
            f"""
            WITH monthly AS (
                SELECT
                    DATE_TRUNC('{trunc}', receipt_date) AS period,
                    SUM(total_money) AS revenue,
                    COUNT(*) AS tx_count
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL{sf}
                GROUP BY period
            )
            SELECT
                period,
                revenue,
                tx_count,
                LAG(revenue) OVER (ORDER BY period) AS prev_revenue,
                ROUND(
                    (revenue - LAG(revenue) OVER (ORDER BY period))
                    / NULLIF(LAG(revenue) OVER (ORDER BY period), 0) * 100,
                    1
                ) AS pct_change
            FROM monthly
            ORDER BY period DESC
            LIMIT ?
        """,
            sp + [months],
        )

    def total_revenue(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> float:
        """Total revenue as a single scalar."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)
        sf, sp = store_filter(store_id)
        return (
            _scalar(
                self._conn,
                f"""
            SELECT COALESCE(SUM(total_money), 0)
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}{sf}
        """,
                dp + sp,
            )
            or 0.0
        )

    def total_revenue_by_month(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Total revenue broken down by month.

        Returns a DataFrame with columns: month, revenue, tx_count, avg_ticket.
        """
        df, dp = date_filter("receipt_date", date_start, date_end, days)
        sf, sp = store_filter(store_id)

        return _query(
            self._conn,
            f"""
            SELECT
                STRFTIME(receipt_date, '%Y-%m') AS month,
                ROUND(SUM(total_money), 2) AS revenue,
                COUNT(*) AS tx_count,
                ROUND(AVG(total_money), 2) AS avg_ticket
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}{sf}
            GROUP BY month
            ORDER BY month DESC
        """,
            dp + sp,
        )

    def refund_rate(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
    ) -> pl.DataFrame:
        """Refund totals and rate as a percentage of sales."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                receipt_date::DATE AS date,
                SUM(CASE WHEN receipt_type = 'REFUND' THEN total_money ELSE 0 END) AS refunds,
                SUM(CASE WHEN receipt_type = 'SALE' THEN total_money ELSE 0 END) AS sales,
                ROUND(
                    ABS(SUM(CASE WHEN receipt_type = 'REFUND' THEN total_money ELSE 0 END))
                    / NULLIF(SUM(CASE WHEN receipt_type = 'SALE' THEN total_money ELSE 0 END), 0)
                    * 100, 2
                ) AS refund_pct
            FROM receipts
            WHERE cancelled_at IS NULL{df}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp,
        )
