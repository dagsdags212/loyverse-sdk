"""
Customer analytics — RFM segmentation, retention, top spenders.
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


class CustomerAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def new_vs_returning(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Count of new vs returning customers per day."""
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
                COUNT(*) AS total_tx,
                COUNT(DISTINCT r.customer_id) AS unique_customers,
                COUNT(DISTINCT CASE WHEN c.first_visit >= r.receipt_date::DATE
                    THEN r.customer_id END) AS new_customers,
                COUNT(DISTINCT CASE WHEN c.first_visit < r.receipt_date::DATE
                    THEN r.customer_id END) AS returning_customers
            FROM receipts r
            LEFT JOIN customers c ON r.customer_id = c.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL
              AND r.customer_id IS NOT NULL{df}{sf}
            GROUP BY date
            ORDER BY date DESC
        """,
            dp + sp,
            fmt=fmt,
        )

    def rfm_analysis(
        self,
        as_of_date: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """RFM (Recency, Frequency, Monetary) scoring for all customers.

        Returns a DataFrame with: customer_id, name, recency_days, frequency,
        monetary, r_score, f_score, m_score, segment.

        Scores are 1–5 quintiles. Segment labels: Champions, Loyal,
        Potential, At Risk, Lost.
        """
        as_of = as_of_date or "CURRENT_DATE"

        return _query(
            self._conn,
            f"""
            WITH rfm AS (
                SELECT
                    c.id AS customer_id,
                    c.name,
                    ({as_of}::DATE - MAX(r.receipt_date)::DATE) AS recency_days,
                    COUNT(DISTINCT r.receipt_number) AS frequency,
                    COALESCE(SUM(r.total_money), 0) AS monetary
                FROM customers c
                LEFT JOIN receipts r ON c.id = r.customer_id
                    AND r.receipt_type = 'SALE'
                    AND r.cancelled_at IS NULL
                GROUP BY c.id, c.name
            ),
            scored AS (
                SELECT
                    *,
                    NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
                    NTILE(5) OVER (ORDER BY frequency ASC)  AS f_score,
                    NTILE(5) OVER (ORDER BY monetary ASC)   AS m_score
                FROM rfm
            )
            SELECT
                customer_id,
                name,
                recency_days,
                frequency,
                ROUND(monetary, 2) AS monetary,
                r_score,
                f_score,
                m_score,
                (r_score * 100 + f_score * 10 + m_score) AS rfm_cell,
                CASE
                    WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
                    WHEN r_score >= 4 AND f_score >= 3 THEN 'Loyal'
                    WHEN f_score >= 4 AND m_score >= 4 THEN 'Big Spenders'
                    WHEN r_score >= 4 THEN 'New/Recent'
                    WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Lost'
                    WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
                    ELSE 'Average'
                END AS segment
            FROM scored
            ORDER BY rfm_cell DESC
        """,
            fmt=fmt,
        )

    def top_customers(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        n: int = 10,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Top N customers by total spend."""
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
                c.id AS customer_id,
                c.name,
                COUNT(DISTINCT r.receipt_number) AS visits,
                ROUND(SUM(r.total_money), 2) AS total_spent,
                ROUND(AVG(r.total_money), 2) AS avg_ticket
            FROM receipts r
            JOIN customers c ON r.customer_id = c.id
            WHERE r.receipt_type = 'SALE'
              AND r.cancelled_at IS NULL{df}{sf}
            GROUP BY c.id, c.name
            ORDER BY total_spent DESC
            LIMIT ?
        """,
            dp + sp + [n],
            fmt=fmt,
        )

    def unique_customers(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> int | str:
        """Count of distinct customers in the period."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND store_id = ?"
            sp = [store_id]

        result = _scalar(
            self._conn,
            f"""
            SELECT COUNT(DISTINCT customer_id)
            FROM receipts
            WHERE receipt_type = 'SALE'
              AND cancelled_at IS NULL
              AND customer_id IS NOT NULL{df}{sf}
        """,
            dp + sp,
        )
        raw = int(result or 0)
        if fmt == "dataframe":
            return raw
        return _scalar_to_output(raw, fmt, "unique_customers")

    def retention_rate(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        fmt: Format = "dataframe",
    ) -> float | str:
        """Percentage of customers who visited more than once in the period."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)
        raw = (
            _scalar(
                self._conn,
                f"""
            WITH cust_visits AS (
                SELECT customer_id, COUNT(DISTINCT receipt_number) AS visits
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL
                  AND customer_id IS NOT NULL{df}
                GROUP BY customer_id
            )
            SELECT
                ROUND(
                    COUNT(CASE WHEN visits > 1 THEN 1 END) * 100.0
                    / NULLIF(COUNT(*), 0), 1
                )
            FROM cust_visits
        """,
                dp,
            )
            or 0
        )
        if fmt == "dataframe":
            return raw
        return _scalar_to_output(raw, fmt, "retention_rate")

    def customer_visit_distribution(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 365,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Distribution of visit counts across the customer base."""
        df, dp = date_filter("receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            WITH visit_counts AS (
                SELECT
                    customer_id,
                    COUNT(DISTINCT receipt_number) AS visits
                FROM receipts
                WHERE receipt_type = 'SALE'
                  AND cancelled_at IS NULL
                  AND customer_id IS NOT NULL{df}
                GROUP BY customer_id
            )
            SELECT
                visits,
                COUNT(*) AS customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct
            FROM visit_counts
            GROUP BY visits
            ORDER BY visits
        """,
            dp,
            fmt=fmt,
        )
