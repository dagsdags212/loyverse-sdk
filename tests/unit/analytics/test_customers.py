"""Tests for customer analytics module."""

from loyverse_sdk.analytics.customers import CustomerAnalytics


class TestRFM:
    def test_all_customers_included(self, db):
        a = CustomerAnalytics(db)
        df = a.rfm_analysis()
        assert len(df) == 3  # 3 customers seeded

    def test_segments_assigned(self, db):
        a = CustomerAnalytics(db)
        df = a.rfm_analysis()
        segments = set(df["segment"].to_list())
        assert len(segments) > 0
        assert all(
            s
            in [
                "Champions",
                "Loyal",
                "Big Spenders",
                "New/Recent",
                "Lost",
                "At Risk",
                "Average",
            ]
            for s in segments
        )

    def test_scores_in_range(self, db):
        a = CustomerAnalytics(db)
        df = a.rfm_analysis()
        assert df["r_score"].min() >= 1
        assert df["r_score"].max() <= 5
        assert df["f_score"].min() >= 1
        assert df["m_score"].min() >= 1


class TestTopCustomers:
    def test_returns_ranked(self, db):
        a = CustomerAnalytics(db)
        df = a.top_customers(days=30, n=10)
        assert len(df) >= 1
        # John has 2 purchases (RCPT-0001 and RCPT-0002)
        # each $250 with $25 discount on first = $475
        assert df["total_spent"].max() > 0


class TestRetention:
    def test_retention_rate(self, db):
        a = CustomerAnalytics(db)
        rate = a.retention_rate(days=30)
        assert 0 <= rate <= 100


class TestVisitDistribution:
    def test_returns_distribution(self, db):
        a = CustomerAnalytics(db)
        df = a.customer_visit_distribution(days=365)
        assert len(df) > 0
        assert df["pct"].sum() > 99  # should sum to ~100
