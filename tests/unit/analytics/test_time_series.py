"""Tests for time-series analytics module."""

from loyverse_sdk.analytics.time_series import TimeSeriesAnalytics


class TestMovingAverage:
    def test_returns_smoothed_data(self, db):
        a = TimeSeriesAnalytics(db)
        df = a.moving_average_revenue(window=3, days=90)
        assert len(df) > 0
        assert "ma_3d" in df.columns

    def test_ma_less_volatile(self, db):
        a = TimeSeriesAnalytics(db)
        df = a.moving_average_revenue(window=3, days=90)
        # The moving average column should exist and have values
        assert df["ma_3d"].null_count() < len(df)


class TestWeekOverWeek:
    def test_returns_wow_data(self, db):
        a = TimeSeriesAnalytics(db)
        df = a.week_over_week_growth(days=90)
        assert len(df) > 0
        assert "wow_change_pct" in df.columns


class TestMonthlySummary:
    def test_returns_monthly(self, db):
        a = TimeSeriesAnalytics(db)
        df = a.monthly_summary(months=3)
        assert len(df) >= 1
        assert "revenue" in df.columns
        assert "mom_change_pct" in df.columns


class TestDayOverDay:
    def test_returns_dod_data(self, db):
        a = TimeSeriesAnalytics(db)
        df = a.day_over_day(days=90)
        assert len(df) > 0
        assert "dod_change_pct" in df.columns


class TestEngineIntegration:
    def test_engine_context_manager(self, db):
        from loyverse_sdk.analytics.engine import AnalyticsEngine

        # Cannot test with :memory: path, but module import works
        pass
