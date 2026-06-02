"""Tests for operations analytics module."""

from loyverse_sdk.analytics.operations import OperationsAnalytics


class TestPeakHours:
    def test_returns_hours(self, db):
        a = OperationsAnalytics(db)
        df = a.peak_hours(days=30)
        assert len(df) > 0
        assert "hour" in df.columns
        assert "tx_count" in df.columns

    def test_hours_in_range(self, db):
        a = OperationsAnalytics(db)
        df = a.peak_hours(days=30)
        assert df["hour"].min() >= 0
        assert df["hour"].max() <= 23


class TestPeakDays:
    def test_returns_all_days(self, db):
        a = OperationsAnalytics(db)
        df = a.peak_days(days=30)
        assert len(df) >= 1
        assert "day_name" in df.columns


class TestPaymentMethodSplit:
    def test_returns_data(self, db):
        a = OperationsAnalytics(db)
        df = a.payment_method_split(days=30)
        assert len(df) > 0


class TestDiscountAnalysis:
    def test_returns_discount_data(self, db):
        a = OperationsAnalytics(db)
        df = a.discount_analysis(days=30)
        assert len(df) > 0
        assert "discounts" in df.columns


class TestTipAnalysis:
    def test_returns_tip_data(self, db):
        a = OperationsAnalytics(db)
        df = a.tip_analysis(days=30)
        assert len(df) > 0
        assert "total_tips" in df.columns


class TestDiningOptionSplit:
    def test_returns_data(self, db):
        a = OperationsAnalytics(db)
        df = a.dining_option_split(days=30)
        assert len(df) >= 1
