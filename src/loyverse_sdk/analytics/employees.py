"""
Employee performance analytics.
"""

from datetime import datetime

import duckdb
import polars as pl

from loyverse_sdk.analytics._base import (
    Format,
    _query,
    date_filter,
)


class EmployeeAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def revenue_by_employee(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Revenue, transaction count, and average ticket per employee."""
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
                e.name AS employee,
                COUNT(*) AS tx_count,
                ROUND(SUM(r.total_money), 2) AS revenue,
                ROUND(AVG(r.total_money), 2) AS avg_ticket,
                ROUND(SUM(r.tip), 2) AS total_tips
            FROM receipts r
            JOIN employees e ON r.employee_id = e.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY e.name
            ORDER BY revenue DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def employee_daily_summary(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Daily transaction counts and revenue per employee."""
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
                e.name AS employee,
                COUNT(*) AS tx_count,
                ROUND(SUM(r.total_money), 2) AS revenue
            FROM receipts r
            JOIN employees e ON r.employee_id = e.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY date, e.name
            ORDER BY date DESC, employee
        """,
            dp + sp,
            fmt=fmt,
        )

    def tip_by_employee(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Tip totals and tip rate per employee."""
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                e.name AS employee,
                ROUND(SUM(r.tip), 2) AS total_tips,
                ROUND(AVG(r.tip), 2) AS avg_tip,
                ROUND(
                    SUM(r.tip) / NULLIF(SUM(r.total_money), 0) * 100, 1
                ) AS tip_rate_pct
            FROM receipts r
            JOIN employees e ON r.employee_id = e.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}
            GROUP BY e.name
            ORDER BY total_tips DESC
        """,
            dp,
            fmt=fmt,
        )
