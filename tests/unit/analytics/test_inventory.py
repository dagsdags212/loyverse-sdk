"""Tests for inventory analytics module."""

from loyverse_sdk.analytics.inventory import InventoryAnalytics


class TestTurnover:
    def test_returns_turnover_data(self, db):
        a = InventoryAnalytics(db)
        df = a.turnover(days=90, n=10)
        assert len(df) == 3
        assert "item" in df.columns
        assert "turnover_rate" in df.columns
        assert "days_to_sell" in df.columns

    def test_wash_turnover(self, db):
        a = InventoryAnalytics(db)
        df = a.turnover(days=90, n=10)
        wash = df.filter(df["item"] == "Wash")
        # Wash: 8 units sold, 10 in stock → turnover = 0.8
        assert wash["units_sold"][0] == 8.0
        assert wash["current_stock"][0] == 10

    def test_respects_limit(self, db):
        a = InventoryAnalytics(db)
        df = a.turnover(days=90, n=2)
        assert len(df) == 2


class TestStockValue:
    def test_returns_stock_values(self, db):
        a = InventoryAnalytics(db)
        df = a.stock_value()
        assert len(df) == 3
        assert "stock_value" in df.columns
        assert "unit_cost" in df.columns

    def test_total_value(self, db):
        a = InventoryAnalytics(db)
        df = a.stock_value()
        # Wash: 10 × 30 = 300, Dry: 5 × 40 = 200, Det: 3 × 10 = 30
        assert df["stock_value"].sum() == 530.0

    def test_detergent_has_lowest_value(self, db):
        a = InventoryAnalytics(db)
        df = a.stock_value()
        assert df["stock_value"].min() == 30.0


class TestTotalInventoryValue:
    def test_returns_scalar(self, db):
        a = InventoryAnalytics(db)
        result = a.total_inventory_value()
        assert result == 530.0


class TestStockValueByStore:
    def test_returns_store_values(self, db):
        a = InventoryAnalytics(db)
        df = a.stock_value_by_store()
        assert len(df) == 1
        assert df["store_name"][0] == "Main Store"
        assert df["stock_value"][0] == 530.0


class TestLowStock:
    def test_finds_low_stock(self, db):
        a = InventoryAnalytics(db)
        df = a.low_stock(threshold=5)
        # Detergent has 3 in stock, threshold 5
        assert len(df) >= 1
        assert "item_name" in df.columns

    def test_detergent_is_low(self, db):
        a = InventoryAnalytics(db)
        df = a.low_stock(threshold=5)
        det = df.filter(df["variant_sku"] == "SKU-DET")
        assert len(det) >= 1

    def test_threshold_uses_variant_store_config(self, db):
        a = InventoryAnalytics(db)
        df = a.low_stock(threshold=2)
        # Detergent is at 3, but variant_store has low_stock_threshold=5
        # so it gets caught by the configured threshold (3 <= 5)
        det = df.filter(df["variant_sku"] == "SKU-DET")
        assert len(det) == 1
        assert det["current_stock"][0] == 3


class TestItemsNeverSold:
    def test_no_dead_stock(self, db):
        a = InventoryAnalytics(db)
        df = a.items_never_sold(days=90)
        # All variants in the test data were sold at least once
        assert len(df) == 0
