"""
Analytics engine for the Loyverse SDK.

Provides a single entry point for all analytics modules, backed by the
local DuckDB data warehouse populated by ``export_to_duckdb()``.

Example:
    from loyverse_sdk import LoyverseClient
    from loyverse_sdk.analytics import AnalyticsEngine

    client = LoyverseClient()
    await client.export_to_duckdb("loyverse.duckdb")
    await client.close()

    engine = AnalyticsEngine("loyverse.duckdb")

    # Revenue
    df = engine.revenue.daily_revenue(days=30)

    # RFM segmentation
    df = engine.customers.rfm_analysis()

    engine.close()
"""

from pathlib import Path
from typing import Optional
import duckdb

from loyverse_sdk.analytics.revenue import RevenueAnalytics
from loyverse_sdk.analytics.products import ProductAnalytics
from loyverse_sdk.analytics.customers import CustomerAnalytics
from loyverse_sdk.analytics.employees import EmployeeAnalytics
from loyverse_sdk.analytics.operations import OperationsAnalytics
from loyverse_sdk.analytics.time_series import TimeSeriesAnalytics
from loyverse_sdk.analytics.profitability import ProfitabilityAnalytics
from loyverse_sdk.analytics.inventory import InventoryAnalytics


class AnalyticsEngine:
    """Entry point for analytics on the Loyverse data warehouse.

    Wraps a DuckDB connection and exposes typed analytics modules for
    revenue, products, customers, employees, operations, time series,
    profitability, and inventory.
    """

    def __init__(
        self,
        db_path: str,
        read_only: bool = True,
    ):
        if not Path(db_path).exists():
            raise FileNotFoundError(
                f"Database not found: {db_path}. Run export_to_duckdb() first."
            )

        self.db_path = db_path
        self._conn = duckdb.connect(db_path, read_only=read_only)

        self.revenue = RevenueAnalytics(self._conn)
        self.products = ProductAnalytics(self._conn)
        self.customers = CustomerAnalytics(self._conn)
        self.employees = EmployeeAnalytics(self._conn)
        self.operations = OperationsAnalytics(self._conn)
        self.time_series = TimeSeriesAnalytics(self._conn)
        self.profitability = ProfitabilityAnalytics(self._conn)
        self.inventory = InventoryAnalytics(self._conn)

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
