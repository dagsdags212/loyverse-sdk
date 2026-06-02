"""
Analytics layer for the Loyverse SDK.

Provides business-metric functions that query the local DuckDB data
warehouse (populated by ``export_to_duckdb()``) without hitting the API.

Example:
    from loyverse_sdk.analytics import AnalyticsEngine

    engine = AnalyticsEngine("loyverse.duckdb")
    df = engine.revenue.daily_revenue(days=30)
    rfm = engine.customers.rfm_analysis()
    engine.close()
"""

from loyverse_sdk.analytics.engine import AnalyticsEngine

__all__ = ["AnalyticsEngine"]
