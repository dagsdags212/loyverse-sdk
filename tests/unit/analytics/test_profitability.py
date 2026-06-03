"""Tests for profitability analytics module."""

from loyverse_sdk.analytics.profitability import ProfitabilityAnalytics


class TestGrossProfit:
    def test_returns_daily_data(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.gross_profit(days=90)
        assert len(df) >= 1
        assert "revenue" in df.columns
        assert "cost" in df.columns
        assert "gross_profit" in df.columns
        assert "margin_pct" in df.columns

    def test_profit_is_positive(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.gross_profit(days=90)
        assert df["gross_profit"].sum() > 0

    def test_revenue_matches_known_total(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.gross_profit(days=90)
        # 6 sales: Wash 800 + Dry 500 + Detergent 150 = 1450
        # REFUND receipt excluded
        assert abs(df["revenue"].sum() - 1450.0) < 1


class TestProfitMargins:
    def test_returns_item_margins(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_margins(days=90, n=10)
        assert len(df) == 3
        assert "item" in df.columns
        assert "gross_profit" in df.columns
        assert "margin_pct" in df.columns

    def test_respects_limit(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_margins(days=90, n=2)
        assert len(df) == 2

    def test_sort_by_margin_pct(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_margins(days=90, n=10, sort_by="margin_pct")
        assert df["margin_pct"][0] >= df["margin_pct"][-1]

    def test_sort_by_revenue(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_margins(days=90, n=10, sort_by="revenue")
        assert df["revenue"][0] >= df["revenue"][-1]

    def test_wash_gross_profit(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_margins(days=90, n=10)
        wash = df.filter(df["item"] == "Wash")
        # Wash: 800 revenue, 240 cost, 560 profit
        assert wash["revenue"][0] == 800.0
        assert wash["gross_profit"][0] == 560.0


class TestProfitByCategory:
    def test_returns_categories(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_by_category(days=90)
        assert len(df) == 2  # Service + Soaps
        assert "category" in df.columns
        assert "margin_pct" in df.columns

    def test_service_profit(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.profit_by_category(days=90)
        svc = df.filter(df["category"] == "Service")
        # Service: Wash(560) + Dry(340) = 900 profit
        assert svc["gross_profit"][0] == 900.0


class TestOverallMargin:
    def test_returns_scalar(self, db):
        a = ProfitabilityAnalytics(db)
        result = a.overall_margin(days=90)
        # 1000 / 1450 = 68.97
        assert 65.0 <= result <= 72.0

    def test_with_store_id_no_data(self, db):
        a = ProfitabilityAnalytics(db)
        result = a.overall_margin(days=90, store_id="nonexistent")
        assert result == 0.0


class TestMarginTrend:
    def test_returns_trend(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.margin_trend(days=90)
        assert len(df) > 0
        assert "margin_pct" in df.columns
        assert "margin_change" in df.columns


class TestItemsWithoutCost:
    def test_all_items_have_cost(self, db):
        a = ProfitabilityAnalytics(db)
        df = a.items_without_cost()
        assert len(df) == 0  # All test items have cost data
