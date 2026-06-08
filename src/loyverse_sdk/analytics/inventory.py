"""
Inventory analytics — turnover, stock value, low-stock alerts.

Uses ``inventory.in_stock``, ``receipt_line_items.quantity``, and
``variants.cost`` to calculate inventory performance metrics.
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


class InventoryAnalytics:
    def __init__(self, conn: duckdb.DuckDBPyConnection):
        self._conn = conn

    def turnover(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        store_id: str | None = None,
        n: int = 20,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Inventory turnover rate = units sold ÷ average stock.

        High turnover = fast-moving items. Low turnover = slow/overstocked.
        Items with cost=0 are excluded from valuation but shown for movement visibility.

        Returns columns: item, variant_sku, units_sold, current_stock,
        avg_cost, turnover_rate, days_to_sell.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        sf = ""
        sp: list = []
        if store_id:
            sf = " AND inv.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            WITH sold AS (
                SELECT
                    l.item_name,
                    COALESCE(l.variant_id, l.item_id) AS variant_id,
                    SUM(l.quantity) AS units_sold
                FROM receipt_line_items l
                JOIN receipts r ON l.receipt_id = r.receipt_number
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}
                GROUP BY l.item_name, COALESCE(l.variant_id, l.item_id)
            ),
            stock AS (
                SELECT
                    inv.variant_id,
                    inv.in_stock AS current_stock,
                    MAX(v.cost) AS unit_cost
                FROM inventory inv
                LEFT JOIN variants v ON inv.variant_id = v.id
                WHERE 1=1{sf}
                GROUP BY inv.variant_id, inv.in_stock
            )
            SELECT
                s.item_name AS item,
                COALESCE(v.sku, 'N/A') AS variant_sku,
                s.units_sold,
                COALESCE(st.current_stock, 0) AS current_stock,
                ROUND(COALESCE(st.unit_cost, 0), 2) AS avg_cost,
                ROUND(
                    s.units_sold
                    / NULLIF(GREATEST(st.current_stock, 1.0), 0), 1
                ) AS turnover_rate,
                ROUND(
                    GREATEST(st.current_stock, 0)
                    / NULLIF(s.units_sold / {days}.0, 0), 0
                ) AS days_to_sell
            FROM sold s
            LEFT JOIN stock st ON s.variant_id = st.variant_id
            LEFT JOIN variants v ON s.variant_id = v.id
            WHERE s.units_sold > 0
            ORDER BY turnover_rate DESC
            LIMIT ?
        """,
            sp + [n],
            fmt=fmt,
        )

    def stock_value(
        self,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Total inventory value = current stock × unit cost per variant.

        Returns columns: item_name, variant_sku, in_stock, unit_cost,
        stock_value.
        """
        sf = ""
        sp: list = []
        if store_id:
            sf = " AND inv.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                COALESCE(i.name, 'Unknown') AS item_name,
                COALESCE(v.sku, 'N/A') AS variant_sku,
                inv.in_stock,
                ROUND(COALESCE(v.cost, 0), 2) AS unit_cost,
                ROUND(inv.in_stock * COALESCE(v.cost, 0), 2) AS stock_value
            FROM inventory inv
            LEFT JOIN variants v ON inv.variant_id = v.id
            LEFT JOIN items i ON v.item_id = i.id
            WHERE inv.in_stock > 0{sf}
            ORDER BY stock_value DESC
        """,
            sp,
            fmt=fmt,
        )

    def total_inventory_value(
        self,
        store_id: str | None = None,
        fmt: Format = "dataframe",
    ) -> float | str:
        """Total inventory value across all items as a single scalar."""
        sf = ""
        sp: list = []
        if store_id:
            sf = " AND inv.store_id = ?"
            sp = [store_id]

        raw = (
            _scalar(
                self._conn,
                f"""
                SELECT ROUND(
                    COALESCE(SUM(inv.in_stock * v.cost), 0), 2
                )
                FROM inventory inv
                LEFT JOIN variants v ON inv.variant_id = v.id
                WHERE 1=1{sf}
            """,
                sp,
            )
            or 0.0
        )
        if fmt == "dataframe":
            return raw
        return _scalar_to_output(raw, fmt, "total_inventory_value")

    def stock_value_by_store(
        self,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Inventory value broken down by store.

        Returns columns: store_name, total_items, total_stock_value.
        """
        return _query(
            self._conn,
            """
            SELECT
                COALESCE(s.name, 'Unknown') AS store_name,
                COUNT(DISTINCT inv.variant_id) AS unique_variants,
                SUM(inv.in_stock) AS total_units,
                ROUND(COALESCE(SUM(inv.in_stock * v.cost), 0), 2) AS stock_value
            FROM inventory inv
            LEFT JOIN variants v ON inv.variant_id = v.id
            LEFT JOIN stores s ON inv.store_id = s.id
            WHERE inv.in_stock > 0
            GROUP BY s.name
            ORDER BY stock_value DESC
        """,
            fmt=fmt,
        )

    def low_stock(
        self,
        store_id: str | None = None,
        threshold: int = 5,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Items at or below a stock threshold with turnover context.

        Uses ``variant_store.low_stock_threshold`` if set, falling back to
        the supplied threshold parameter.

        Returns columns: item_name, variant_sku, current_stock,
        threshold, days_since_last_sale.
        """
        sf = ""
        sp: list = []
        if store_id:
            sf = " AND inv.store_id = ?"
            sp = [store_id]

        return _query(
            self._conn,
            f"""
            SELECT
                COALESCE(i.name, 'Unknown') AS item_name,
                COALESCE(v.sku, 'N/A') AS variant_sku,
                inv.in_stock AS current_stock,
                GREATEST(
                    inv.in_stock,
                    COALESCE(vs.low_stock_threshold, {threshold})
                ) AS alert_threshold,
                s.name AS store_name,
                MAX(r.receipt_date) AS last_sold
            FROM inventory inv
            LEFT JOIN variants v ON inv.variant_id = v.id
            LEFT JOIN items i ON v.item_id = i.id
            LEFT JOIN stores s ON inv.store_id = s.id
            LEFT JOIN variant_store vs
                ON inv.variant_id = vs.variant_id AND inv.store_id = vs.store_id
            LEFT JOIN receipt_line_items l ON l.variant_id = inv.variant_id
            LEFT JOIN receipts r ON l.receipt_id = r.receipt_number
                AND r.receipt_type = 'SALE'
                AND r.cancelled_at IS NULL
            WHERE inv.in_stock <= COALESCE(vs.low_stock_threshold, {threshold}){sf}
            GROUP BY i.name, v.sku, inv.in_stock, vs.low_stock_threshold, s.name
            ORDER BY inv.in_stock ASC
        """,
            sp,
            fmt=fmt,
        )

    def items_never_sold(
        self,
        date_start: datetime | str | None = None,
        date_end: datetime | str | None = None,
        days: int | None = 30,
        fmt: Format = "dataframe",
    ) -> pl.DataFrame | str:
        """Items with stock on hand that have not sold in the period.

        Useful for identifying dead stock and over-ordering.
        """
        df, dp = date_filter("r.receipt_date", date_start, date_end, days)

        return _query(
            self._conn,
            f"""
            WITH sold_in_period AS (
                SELECT DISTINCT COALESCE(variant_id, item_id) AS vid
                FROM receipt_line_items l
                JOIN receipts r ON l.receipt_id = r.receipt_number
                WHERE r.receipt_type = 'SALE'
                  AND r.cancelled_at IS NULL{df}
            )
            SELECT
                COALESCE(i.name, 'Unknown') AS item_name,
                COALESCE(v.sku, 'N/A') AS variant_sku,
                inv.in_stock AS current_stock,
                ROUND(inv.in_stock * COALESCE(v.cost, 0), 2) AS tied_up_value
            FROM inventory inv
            LEFT JOIN variants v ON inv.variant_id = v.id
            LEFT JOIN items i ON v.item_id = i.id
            WHERE inv.in_stock > 0
              AND inv.variant_id NOT IN (SELECT vid FROM sold_in_period)
            ORDER BY tied_up_value DESC
        """,
            dp,
            fmt=fmt,
        )
