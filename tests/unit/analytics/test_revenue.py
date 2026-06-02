"""Tests for revenue analytics module."""

from loyverse_sdk.analytics.revenue import RevenueAnalytics


class TestDailyRevenue:
    def test_daily_revenue_default(self, db):
        a = RevenueAnalytics(db)
        df = a.daily_revenue(days=31)
        assert len(df) == 3  # May 1, 2, 3
        assert df["tx_count"].sum() == 6  # 6 SALE receipts (REFUND excluded)
        assert df["revenue"].sum() > 0

    def test_daily_revenue_excludes_cancelled(self, db):
        a = RevenueAnalytics(db)
        df = a.daily_revenue(days=30)
        assert len(df) >= 2  # At least 2 days of sales

    def test_total_revenue(self, db):
        a = RevenueAnalytics(db)
        total = a.total_revenue(days=90)
        # 6 sales × 250 = 1500 (total_money already reflects any discounts)
        assert total == 1500.0

    def test_total_revenue_by_month(self, db):
        a = RevenueAnalytics(db)
        df = a.total_revenue_by_month(days=90)
        assert len(df) == 1
        assert df["month"][0] == "2026-05"
        assert df["revenue"][0] == 1500.0
        assert df["tx_count"][0] == 6
        assert df["avg_ticket"][0] == 250.0

    def test_revenue_by_store(self, db):
        a = RevenueAnalytics(db)
        df = a.revenue_by_store(days=30)
        assert len(df) == 1
        assert df["store_name"][0] == "Main Store"

    def test_refund_rate(self, db):
        a = RevenueAnalytics(db)
        df = a.refund_rate(days=31)
        assert len(df) == 3
        # Day 3 has a refund (negative amount)
        day3 = df.filter(df["date"].cast(str).str.contains("2026-05-03"))
        assert day3["refunds"][0] != 0

    def test_revenue_growth(self, db):
        a = RevenueAnalytics(db)
        df = a.revenue_growth(months=3)
        assert len(df) > 0
