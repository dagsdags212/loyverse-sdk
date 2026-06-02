"""
Time-series analytics — moving averages, week-over-week growth, monthly trends.
"""

from datetime import datetime
from typing import Optional
import duckdb
import polars as pl

from loyverse_sdk.analytics._base import date_filter, _query


class TimeSeriesAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def moving_average_revenue(
        self,
        window: int = 7,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 90,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Daily revenue with N-day simple moving average."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            WITH daily AS (
                SELECT
                    receipt_date::DATE AS date,
                    SUM(total_money) AS revenue,
                    COUNT(*) AS tx_count
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL{df}{sf}
                GROUP BY date
            )
            SELECT
                date,
                revenue,
                tx_count,
                ROUND(
                    AVG(revenue) OVER (
                        ORDER BY date
                        ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW
                    ), 2
                ) AS ma_{window}d
            FROM daily
            ORDER BY date DESC
        """,
            dp + sp,
        )

    def week_over_week_growth(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 90,
    ) -> pl.DataFrame:
        """Daily revenue with week-over-week growth rate."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            WITH daily AS (
                SELECT
                    receipt_date::DATE AS date,
                    SUM(total_money) AS revenue
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL{df}
                GROUP BY date
            )
            SELECT
                date,
                revenue,
                LAG(revenue, 7) OVER (ORDER BY date) AS prev_week_revenue,
                ROUND(
                    (revenue - LAG(revenue, 7) OVER (ORDER BY date))
                    / NULLIF(LAG(revenue, 7) OVER (ORDER BY date), 0)
                    * 100, 1
                ) AS wow_change_pct
            FROM daily
            ORDER BY date DESC
        """,
            dp,
        )

    def monthly_summary(
        self,
        months: int = 12,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Monthly revenue, transaction count, unique customers, average ticket."""
        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            WITH monthly AS (
                SELECT
                    DATE_TRUNC('MONTH', receipt_date) AS month,
                    SUM(total_money) AS revenue,
                    COUNT(*) AS tx_count,
                    COUNT(DISTINCT customer_id) AS unique_customers,
                    ROUND(AVG(total_money), 2) AS avg_ticket
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL{sf}
                GROUP BY month
            )
            SELECT
                month,
                revenue,
                tx_count,
                unique_customers,
                avg_ticket,
                LAG(revenue) OVER (ORDER BY month) AS prev_month_revenue,
                ROUND(
                    (revenue - LAG(revenue) OVER (ORDER BY month))
                    / NULLIF(LAG(revenue) OVER (ORDER BY month), 0)
                    * 100, 1
                ) AS mom_change_pct
            FROM monthly
            ORDER BY month DESC
            LIMIT ?
        """,
            sp + [months],
        )

    def day_over_day(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Daily revenue with day-over-day change."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            WITH daily AS (
                SELECT
                    receipt_date::DATE AS date,
                    SUM(total_money) AS revenue,
                    COUNT(*) AS tx_count
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL{df}{sf}
                GROUP BY date
            )
            SELECT
                date,
                revenue,
                tx_count,
                ROUND(
                    (revenue - LAG(revenue) OVER (ORDER BY date))
                    / NULLIF(LAG(revenue) OVER (ORDER BY date), 0)
                    * 100, 1
                ) AS dod_change_pct
            FROM daily
            ORDER BY date DESC
        """,
            dp + sp,
        )
