"""Tests for employee analytics module."""

from loyverse_sdk.analytics.employees import EmployeeAnalytics


class TestRevenueByEmployee:
    def test_all_employees(self, db):
        a = EmployeeAnalytics(db)
        df = a.revenue_by_employee(days=30)
        assert len(df) == 2

    def test_bob_has_revenue(self, db):
        a = EmployeeAnalytics(db)
        df = a.revenue_by_employee(days=30)
        bob = df.filter(df["employee"] == "Bob")
        assert len(bob) == 1
        assert bob["revenue"][0] > 0


class TestEmployeeDailySummary:
    def test_returns_summary(self, db):
        a = EmployeeAnalytics(db)
        df = a.employee_daily_summary(days=30)
        assert len(df) > 0
        assert "employee" in df.columns
        assert "revenue" in df.columns


class TestTipByEmployee:
    def test_returns_tip_data(self, db):
        a = EmployeeAnalytics(db)
        df = a.tip_by_employee(days=30)
        assert len(df) > 0
        assert "total_tips" in df.columns
        # Alice (emp1) had tips on RCPT-0001
        alice = df.filter(df["employee"] == "Alice")
        if len(alice) > 0:
            assert alice["total_tips"][0] > 0
