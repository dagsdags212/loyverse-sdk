"""Smoke tests for MCP server registration."""

from unittest import mock

import pytest


class TestServerRegistration:
    def test_server_name(self):
        import loyverse_sdk.mcp.tools  # noqa: F401
        from loyverse_sdk.mcp.server import mcp

        assert mcp.name == "loyverse_mcp"

    def test_all_expected_tools_registered(self):
        import loyverse_sdk.mcp.tools  # noqa: F401
        from loyverse_sdk.mcp.server import mcp

        expected = {
            "loyverse_list_receipts",
            "loyverse_get_receipt",
            "loyverse_list_items",
            "loyverse_get_item",
            "loyverse_list_customers",
            "loyverse_get_customer",
            "loyverse_list_categories",
            "loyverse_get_category",
            "loyverse_list_employees",
            "loyverse_get_employee",
            "loyverse_list_shifts",
            "loyverse_get_shift",
            "loyverse_list_stores",
            "loyverse_get_store",
            "loyverse_list_inventory",
            "loyverse_list_payment_types",
            "loyverse_get_payment_type",
            "loyverse_get_merchant",
            "loyverse_analytics_daily_revenue",
            "loyverse_analytics_total_revenue",
            "loyverse_analytics_revenue_by_store",
            "loyverse_analytics_top_items",
            "loyverse_analytics_revenue_by_category",
            "loyverse_analytics_rfm_analysis",
            "loyverse_analytics_top_customers",
            "loyverse_analytics_unique_customers",
            "loyverse_analytics_revenue_by_employee",
            "loyverse_analytics_peak_hours",
            "loyverse_analytics_peak_days",
            "loyverse_analytics_monthly_summary",
        }
        registered = set(mcp._tool_manager._tools.keys())
        assert expected == registered

    def test_all_tools_read_only(self):
        import loyverse_sdk.mcp.tools  # noqa: F401
        from loyverse_sdk.mcp.server import mcp

        for name, tool in mcp._tool_manager._tools.items():
            ann = tool.annotations
            assert ann is not None and ann.readOnlyHint is True, (
                f"Tool '{name}' is missing readOnlyHint=True"
            )
            assert ann.destructiveHint is False, (
                f"Tool '{name}' is missing destructiveHint=False"
            )


class TestLifespan:
    """Exercise the FastMCP ``lifespan`` async context manager wiring."""

    @pytest.mark.asyncio
    async def test_lifespan_yields_client_engine_and_db_path(self):
        from loyverse_sdk.mcp import server

        fake_client = mock.MagicMock()
        fake_client.close = mock.AsyncMock()
        fake_engine = mock.MagicMock()

        with (
            mock.patch.object(
                server, "LoyverseClient", return_value=fake_client
            ) as client_cls,
            mock.patch.object(
                server, "resolve_db_path", return_value="/tmp/loyverse.duckdb"
            ),
            mock.patch(
                "loyverse_sdk.analytics.AnalyticsEngine",
                return_value=fake_engine,
            ),
        ):
            async with server.lifespan(server.mcp) as state:
                assert state["client"] is fake_client
                assert state["engine"] is fake_engine
                assert state["db_path"] == "/tmp/loyverse.duckdb"

        client_cls.assert_called_once()
        # Resources are torn down after the context exits.
        fake_engine.close.assert_called_once()
        fake_client.close.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lifespan_tolerates_engine_init_failure(self):
        from loyverse_sdk.mcp import server

        fake_client = mock.MagicMock()
        fake_client.close = mock.AsyncMock()

        with (
            mock.patch.object(server, "LoyverseClient", return_value=fake_client),
            mock.patch.object(
                server, "resolve_db_path", return_value="/tmp/loyverse.duckdb"
            ),
            mock.patch(
                "loyverse_sdk.analytics.AnalyticsEngine",
                side_effect=RuntimeError("no db"),
            ),
        ):
            async with server.lifespan(server.mcp) as state:
                # Engine init failure is swallowed; engine is None.
                assert state["engine"] is None
                assert state["client"] is fake_client

        # No engine to close, but the client is still closed.
        fake_client.close.assert_awaited_once()
