from datetime import datetime
from unittest import mock

import duckdb
import pytest
import typer
from typer.testing import CliRunner

from loyverse_sdk.cli.commands import analytics
from loyverse_sdk.cli.commands.analytics import (
    _handle_query_error,
    _open_engine,
    _output,
    _parse_date,
)
from loyverse_sdk.cli.main import app

runner = CliRunner()


def _make_engine_returning(value):
    """Build a Mock engine whose every accessor method returns *value*."""
    engine = mock.MagicMock()

    class _Module:
        def __getattr__(self, name):
            return lambda *a, **k: value

    for module_name in (
        "revenue",
        "products",
        "customers",
        "employees",
        "operations",
        "profitability",
        "inventory",
        "time_series",
    ):
        setattr(engine, module_name, _Module())

    engine.close = mock.MagicMock()
    return engine


class TestParseDate:
    def test_valid_iso_date_returns_datetime(self):
        result = _parse_date("2026-01-15")
        assert isinstance(result, datetime)
        assert result == datetime(2026, 1, 15)

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None

    def test_invalid_value_raises_exit(self):
        with pytest.raises(typer.Exit):
            _parse_date("not-a-date")


class TestOutput:
    def test_str_input_is_printed(self):
        with mock.patch.object(analytics.console, "print") as p:
            _output("hello world", "table")
        p.assert_called_once_with("hello world")

    def test_dict_input_json_format(self):
        with mock.patch.object(analytics.console, "print_json") as pj:
            _output({"revenue": 100}, "json")
        pj.assert_called_once()

    def test_scalar_input_default_format(self):
        with mock.patch.object(analytics.console, "print") as p:
            _output(42, "table")
        p.assert_called_once_with(42)

    def test_object_with_to_dicts_table_format(self):
        frame = mock.MagicMock()
        frame.to_dicts.return_value = [{"a": 1, "b": 2}]
        frame.columns = ["a", "b"]
        with (
            mock.patch.object(analytics, "build_table_from_dicts") as build,
            mock.patch.object(analytics.console, "print") as p,
        ):
            build.return_value = "TABLE"
            _output(frame, "table")
        frame.to_dicts.assert_called_once()
        build.assert_called_once()
        p.assert_called_once_with("TABLE")

    def test_object_with_to_dicts_empty_prints_no_data(self):
        frame = mock.MagicMock()
        frame.to_dicts.return_value = []
        frame.columns = []
        with mock.patch.object(analytics.console, "print") as p:
            _output(frame, "table")
        p.assert_called_once_with("[dim]No data.[/dim]")


class TestOpenEngine:
    def test_missing_db_raises_exit(self):
        with mock.patch.object(
            analytics, "AnalyticsEngine", side_effect=FileNotFoundError("nope")
        ):
            with pytest.raises(typer.Exit):
                _open_engine("/nonexistent/path.db")

    def test_returns_engine_when_present(self):
        sentinel = mock.MagicMock()
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=sentinel):
            assert _open_engine("anything.db") is sentinel


class TestHandleQueryError:
    def test_missing_table_prints_hint_and_exits(self):
        exc = duckdb.CatalogException(
            "Catalog Error: Table with name receipts does not exist!"
        )
        with mock.patch.object(analytics.console, "print") as p:
            with pytest.raises(typer.Exit):
                _handle_query_error("loyverse.db", exc)
        printed = " ".join(str(c.args[0]) for c in p.call_args_list)
        assert "Missing table" in printed
        assert "receipts" in printed

    def test_generic_error_prints_query_error_and_exits(self):
        exc = Exception("some other failure")
        with mock.patch.object(analytics.console, "print") as p:
            with pytest.raises(typer.Exit):
                _handle_query_error("loyverse.db", exc)
        printed = " ".join(str(c.args[0]) for c in p.call_args_list)
        assert "Query error" in printed


class TestRevenueCommand:
    def test_default_daily_revenue(self):
        engine = _make_engine_returning("revenue-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "revenue"])
        assert result.exit_code == 0
        engine.close.assert_called_once()

    def test_by_store_flag(self):
        engine = _make_engine_returning("revenue-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "revenue", "--by-store"])
        assert result.exit_code == 0

    def test_growth_flag(self):
        engine = _make_engine_returning("revenue-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "revenue", "--growth"])
        assert result.exit_code == 0

    def test_with_days_and_format_json(self):
        engine = _make_engine_returning({"total": 1000})
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(
                app, ["analytics", "revenue", "--days", "60", "--format", "json"]
            )
        assert result.exit_code == 0

    def test_invalid_date_exits_nonzero(self):
        engine = _make_engine_returning("revenue-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(
                app, ["analytics", "revenue", "--date-start", "bogus"]
            )
        assert result.exit_code == 1


class TestProductsCommand:
    def test_default_top_items(self):
        engine = _make_engine_returning("products-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "products"])
        assert result.exit_code == 0

    def test_by_category_flag(self):
        engine = _make_engine_returning("products-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "products", "--by-category"])
        assert result.exit_code == 0

    def test_basket_flag(self):
        engine = _make_engine_returning("products-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "products", "--basket"])
        assert result.exit_code == 0


class TestCustomersCommand:
    def test_default_top_customers(self):
        engine = _make_engine_returning("customers-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "customers"])
        assert result.exit_code == 0

    def test_rfm_flag(self):
        engine = _make_engine_returning("customers-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "customers", "--rfm"])
        assert result.exit_code == 0

    def test_retention_flag(self):
        engine = _make_engine_returning("customers-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "customers", "--retention"])
        assert result.exit_code == 0


class TestOtherCommands:
    def test_employees_default(self):
        engine = _make_engine_returning("emp-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "employees"])
        assert result.exit_code == 0

    def test_operations_payments(self):
        engine = _make_engine_returning("ops-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "operations", "--payments"])
        assert result.exit_code == 0

    def test_profitability_margins(self):
        engine = _make_engine_returning("profit-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(
                app, ["analytics", "profitability", "--margins"]
            )
        assert result.exit_code == 0

    def test_inventory_low_stock(self):
        engine = _make_engine_returning("inv-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(
                app, ["analytics", "inventory", "--low-stock"]
            )
        assert result.exit_code == 0

    def test_time_series_monthly(self):
        engine = _make_engine_returning("ts-out")
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "time-series", "--monthly"])
        assert result.exit_code == 0


class TestCommandQueryErrorHandling:
    def test_catalog_exception_exits_nonzero(self):
        engine = mock.MagicMock()
        engine.revenue.daily_revenue.side_effect = duckdb.CatalogException(
            "Catalog Error: Table with name receipts does not exist!"
        )
        with mock.patch.object(analytics, "AnalyticsEngine", return_value=engine):
            result = runner.invoke(app, ["analytics", "revenue"])
        assert result.exit_code == 1
        engine.close.assert_called_once()
