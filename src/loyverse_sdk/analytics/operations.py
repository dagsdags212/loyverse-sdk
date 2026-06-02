"""
Operational metrics — peak hours, payment mix, discounts, tips.
"""

from datetime import datetime
from typing import Optional
import duckdb
import polars as pl

from loyverse_sdk.analytics._base import date_filter, _query, _scalar


class OperationsAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def peak_hours(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Transaction count and revenue by hour of day."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                EXTRACT(HOUR FROM receipt_date) AS hour,
                COUNT(*) AS tx_count,
                ROUND(SUM(total_money), 2) AS revenue,
                ROUND(
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1
                ) AS pct_of_day
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}{sf}
            GROUP BY hour
            ORDER BY hour
        """,
            dp + sp,
        )

    def peak_days(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Transaction count by day of week."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                DAYNAME(receipt_date) AS day_name,
                COUNT(*) AS tx_count,
                ROUND(SUM(total_money), 2) AS revenue,
                ROUND(AVG(total_money), 2) AS avg_ticket
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}{sf}
            GROUP BY day_name
            ORDER BY
                CASE day_name
                    WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2
                    WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
                    WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                    WHEN 'Sunday' THEN 7
                END
        """,
            dp + sp,
        )

    def payment_method_split(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
        store_id: Optional[str] = None,
    ) -> pl.DataFrame:
        """Revenue and transaction count by payment type name.

        Note: Receipts store only a single payment_type_id on the main record.
        This reports the payment type captured in the receipts table.
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
                COALESCE(pt.name, 'Unknown') AS payment_type,
                COUNT(*) AS tx_count,
                ROUND(SUM(r.total_money), 2) AS revenue,
                ROUND(
                    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1
                ) AS tx_pct,
                ROUND(
                    SUM(r.total_money) * 100.0
                    / NULLIF(SUM(SUM(r.total_money)) OVER (), 0), 1
                ) AS revenue_pct
            FROM receipts r
            LEFT JOIN payment_types pt ON r.pos_device_id = pt.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY pt.name
            ORDER BY revenue DESC
        """,
            dp + sp,
        )

    def discount_analysis(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
    ) -> pl.DataFrame:
        """Daily discount totals and discount rate."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                receipt_date::DATE AS date,
                COUNT(*) AS tx_count,
                ROUND(SUM(total_money), 2) AS gross_revenue,
                ROUND(SUM(total_discount), 2) AS discounts,
                ROUND(
                    SUM(total_discount) / NULLIF(SUM(total_money + total_discount), 0)
                    * 100, 1
                ) AS discount_rate_pct
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp,
        )

    def tip_analysis(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
    ) -> pl.DataFrame:
        """Daily tip totals and average tip per transaction."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                receipt_date::DATE AS date,
                COUNT(*) AS tx_count,
                ROUND(SUM(tip), 2) AS total_tips,
                ROUND(AVG(tip), 2) AS avg_tip,
                ROUND(
                    SUM(tip) / NULLIF(SUM(total_money), 0) * 100, 1
                ) AS tip_rate_pct
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp,
        )

    def dining_option_split(
        self,
        date_start: Optional[datetime | str] = None,
        date_end: Optional[datetime | str] = None,
        days: Optional[int] = 30,
    ) -> pl.DataFrame:
        """Revenue breakdown by dining option (dine-in, takeaway, etc.)."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            SELECT
                COALESCE(dining_option, 'Unspecified') AS dining_option,
                COUNT(*) AS tx_count,
                ROUND(SUM(total_money), 2) AS revenue,
                ROUND(AVG(total_money), 2) AS avg_ticket
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL{df}
            GROUP BY dining_option
            ORDER BY revenue DESC
        """,
            dp,
        )
