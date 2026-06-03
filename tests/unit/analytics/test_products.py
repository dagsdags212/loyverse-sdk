"""Tests for product analytics module."""

from loyverse_sdk.analytics.products import ProductAnalytics


class TestRevenueByCategory:
    def test_returns_categories(self, db):
        a = ProductAnalytics(db)
        df = a.revenue_by_category(days=90)
        assert len(df) == 2  # Service + Soaps
        categories = set(df["category"].to_list())
        assert "Service" in categories
        assert "Soaps" in categories

    def test_pct_share_sums_to_100(self, db):
        a = ProductAnalytics(db)
        df = a.revenue_by_category(days=90)
        assert abs(df["pct_share"].sum() - 100.0) < 0.5


class TestTopItems:
    def test_returns_top_items(self, db):
        a = ProductAnalytics(db)
        df = a.top_items(days=90, n=3)
        assert len(df) <= 3
        assert df["total_revenue"].sum() > 0

    def test_respects_limit(self, db):
        a = ProductAnalytics(db)
        df = a.top_items(days=90, n=1)
        assert len(df) == 1


class TestItemsPerTransaction:
    def test_returns_metrics(self, db):
        a = ProductAnalytics(db)
        result = a.items_per_transaction(days=90)
        assert "average" in result
        assert "distribution" in result
        assert result["average"] > 0

    def test_average_is_reasonable(self, db):
        a = ProductAnalytics(db)
        result = a.items_per_transaction(days=90)
        # 13 line items across 6 sales ≈ 2.2 items
        assert 2.0 <= result["average"] <= 3.0
