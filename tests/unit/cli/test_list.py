import asyncio
from unittest import mock
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from loyverse_sdk.cli.main import app

runner = CliRunner()


@pytest.fixture
def mock_run_async():
    with mock.patch("loyverse_sdk.cli.commands.list.run_async") as m:
        m.side_effect = lambda fn: None
        yield m


def _make_executing_run_async(raw_response: dict):
    """Build a run_async replacement that actually executes the inner ``_run``
    coroutine against a fake client, so the format/rendering code paths run
    without any network access.

    The fake client exposes attribute access for any resource name, returning
    an endpoint stub whose ``_get`` is an ``AsyncMock`` returning
    *raw_response*, and which carries the ``path``/``items_key`` attributes the
    command relies on.
    """

    class _EndpointStub:
        def __init__(self, name: str) -> None:
            self.path = name
            self._get = mock.AsyncMock(return_value=raw_response)

    class _FakeClient:
        def __getattr__(self, name: str):
            return _EndpointStub(name)

        async def close(self) -> None:  # pragma: no cover - lifecycle no-op
            pass

    def _run_async(main_coro):
        asyncio.run(main_coro(_FakeClient()))

    return _run_async, _FakeClient


class TestListCommandValidation:
    def test_rejects_unknown_resource(self):
        result = runner.invoke(app, ["api", "list", "unknown"])
        assert result.exit_code == 1
        assert "Unknown resource" in result.stdout

    def test_rejects_invalid_format(self):
        result = runner.invoke(app, ["api", "list", "categories", "--format", "xml"])
        assert result.exit_code == 1
        assert "Invalid --format" in result.stdout

    def test_accepts_valid_resource(self, mock_run_async):
        result = runner.invoke(app, ["api", "list", "categories"])
        assert result.exit_code == 0

    def test_accepts_all_formats(self, mock_run_async):
        for fmt in ("json", "table", "csv", "parquet"):
            result = runner.invoke(app, ["api", "list", "categories", "--format", fmt])
            assert result.exit_code == 0

    def test_accepts_limit(self, mock_run_async):
        result = runner.invoke(app, ["api", "list", "categories", "--limit", "10"])
        assert result.exit_code == 0

    def test_accepts_date_filters(self, mock_run_async):
        result = runner.invoke(
            app,
            [
                "api",
                "list",
                "receipts",
                "--created-at-min",
                "2024-01-01",
                "--created-at-max",
                "2024-12-31",
            ],
        )
        assert result.exit_code == 0

    def test_list_resources_includes_expected(self):
        """Verify that a list of expected resources exists."""
        from loyverse_sdk.cli._metadata import get_listable_resources

        resources = get_listable_resources()
        assert "customers" in resources
        assert "receipts" in resources
        assert "items" in resources
        assert "categories" in resources


def _category_response(n: int = 2) -> dict:
    return {
        "categories": [
            {"id": str(uuid4()), "name": f"Cat {i}", "color": "RED"}
            for i in range(n)
        ],
        "cursor": None,
    }


class TestListCommandExecution:
    """Drive the inner ``_run`` coroutine for each format so the fetching and
    rendering code paths actually execute (no network)."""

    def _invoke(self, raw, extra_args=None):
        run_async, _ = _make_executing_run_async(raw)
        with mock.patch(
            "loyverse_sdk.cli.commands.list.run_async", side_effect=run_async
        ):
            return runner.invoke(
                app, ["api", "list", "categories", *(extra_args or [])]
            )

    def test_json_output_prints_records(self):
        result = self._invoke(_category_response())
        assert result.exit_code == 0
        # JSON output echoes the raw payload.
        assert "categories" in result.stdout

    def test_table_output_renders(self):
        result = self._invoke(_category_response(), ["--format", "table"])
        assert result.exit_code == 0
        assert "Category" in result.stdout

    def test_table_output_empty(self):
        result = self._invoke(
            {"categories": [], "cursor": None}, ["--format", "table"]
        )
        assert result.exit_code == 0
        assert "No categories found" in result.stdout

    def test_table_output_shows_next_cursor(self):
        raw = _category_response()
        raw["cursor"] = "NEXT-PAGE-CURSOR"
        result = self._invoke(raw, ["--format", "table"])
        assert result.exit_code == 0
        assert "NEXT-PAGE-CURSOR" in result.stdout

    def test_csv_output_writes_rows(self):
        result = self._invoke(_category_response(2), ["--format", "csv"])
        assert result.exit_code == 0
        # CSV header from flattened category fields.
        assert "name" in result.stdout

    def test_parquet_output_runs(self):
        # Parquet writes binary to stdout; we only assert the path executes
        # cleanly and reports the record count to stderr.
        result = self._invoke(_category_response(1), ["--format", "parquet"])
        assert result.exit_code == 0

    def test_extra_args_forwarded_as_params(self):
        # An unknown flag should be parsed and passed through to the API call.
        raw = _category_response()
        captured = {}

        def _capturing(main_coro):
            class _EndpointStub:
                def __init__(self, name):
                    self.path = name

                async def _get(self, path, params=None):
                    captured["params"] = params
                    return raw

            class _FakeClient:
                def __getattr__(self, name):
                    return _EndpointStub(name)

                async def close(self):
                    pass

            asyncio.run(main_coro(_FakeClient()))

        with mock.patch(
            "loyverse_sdk.cli.commands.list.run_async", side_effect=_capturing
        ):
            result = runner.invoke(
                app, ["api", "list", "categories", "--show-deleted", "true"]
            )
        assert result.exit_code == 0
        assert captured["params"].get("show_deleted") == "true"

    def test_limit_above_250_paginates(self):
        # When limit > 250 the command uses _fetch_all_pages, which loops until
        # the cursor is exhausted. Provide a page then a terminating empty page.
        pages = [
            {
                "categories": [
                    {"id": str(uuid4()), "name": "A", "color": "RED"}
                ],
                "cursor": "c1",
            },
            {"categories": [], "cursor": None},
        ]

        def _paginating(main_coro):
            class _EndpointStub:
                def __init__(self, name):
                    self.path = name
                    self._calls = 0

                async def _get(self, path, params=None):
                    page = pages[min(self._calls, len(pages) - 1)]
                    self._calls += 1
                    return page

            class _FakeClient:
                def __getattr__(self, name):
                    return _EndpointStub(name)

                async def close(self):
                    pass

            asyncio.run(main_coro(_FakeClient()))

        with mock.patch(
            "loyverse_sdk.cli.commands.list.run_async", side_effect=_paginating
        ):
            result = runner.invoke(
                app, ["api", "list", "categories", "--limit", "300"]
            )
        assert result.exit_code == 0
        assert "categories" in result.stdout


class TestParseExtraArgs:
    def test_parses_key_value_pairs(self):
        from loyverse_sdk.cli.commands.list import _parse_extra_args

        result = _parse_extra_args(["--email", "a@b.com", "--store-id", "s1"])
        assert result == {"email": "a@b.com", "store_id": "s1"}

    def test_flag_without_value_becomes_true(self):
        from loyverse_sdk.cli.commands.list import _parse_extra_args

        result = _parse_extra_args(["--show-deleted"])
        assert result == {"show_deleted": "true"}

    def test_ignores_non_flag_tokens(self):
        from loyverse_sdk.cli.commands.list import _parse_extra_args

        result = _parse_extra_args(["positional", "--limit", "5"])
        assert result == {"limit": "5"}
