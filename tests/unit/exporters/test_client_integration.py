"""
Integration tests for LoyverseClient flat-file export convenience methods.

Tests that LoyverseClient.export_to_csv() and .export_to_parquet()
correctly delegate to the exporters package functions.
"""

import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import polars as pl
from pydantic import BaseModel, Field

from loyverse_sdk import LoyverseClient

# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class _TestExportModel(BaseModel):
    """Simple model for integration tests."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    count: int
    active: bool = True


def _make_test_data(count: int = 3) -> list[_TestExportModel]:
    """Create a list of test model instances."""
    return [
        _TestExportModel(name=f"Item {i:03d}", count=i * 10, active=i % 2 == 0)
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Tests: Delegation (mocked)
# ---------------------------------------------------------------------------


def test_export_to_csv_delegates_to_exporters_module(mocker):
    """
    client.export_to_csv() calls exporters.export_csv() with the same args.
    """
    from loyverse_sdk import exporters

    data = _make_test_data()
    filepath = "test_output.csv"

    mock_fn = mocker.patch.object(exporters, "export_csv")

    client = LoyverseClient(api_token="test-token")
    client.export_to_csv(data, filepath)

    mock_fn.assert_called_once_with(data, filepath)


def test_export_to_parquet_delegates_to_exporters_module(mocker):
    """
    client.export_to_parquet() calls exporters.export_parquet() with the same args.
    """
    from loyverse_sdk import exporters

    data = _make_test_data()
    filepath = "test_output.parquet"

    mock_fn = mocker.patch.object(exporters, "export_parquet")

    client = LoyverseClient(api_token="test-token")
    client.export_to_parquet(data, filepath)

    mock_fn.assert_called_once_with(data, filepath)


# ---------------------------------------------------------------------------
# Tests: End-to-end file creation
# ---------------------------------------------------------------------------


def test_export_to_csv_creates_valid_file():
    """
    client.export_to_csv() writes a file with expected headers and content.
    """
    data = _make_test_data(3)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        client = LoyverseClient(api_token="test-token")
        client.export_to_csv(data, filepath)

        # File should exist and have content
        assert Path(filepath).exists()
        content = Path(filepath).read_text()
        lines = content.splitlines()
        assert len(lines) >= 2  # header + at least one data row

        # Verify expected headers
        headers = lines[0]
        assert "name" in headers
        assert "count" in headers
        assert "active" in headers

        # Verify data row contains expected values
        assert "Item 000" in content
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_to_parquet_creates_valid_file():
    """
    client.export_to_parquet() writes a file readable by pl.read_parquet().
    """
    data = _make_test_data(3)

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        client = LoyverseClient(api_token="test-token")
        client.export_to_parquet(data, filepath)

        # File should exist
        assert Path(filepath).exists()

        # Should be readable by Polars
        df = pl.read_parquet(filepath)
        assert df.shape[0] == 3  # 3 rows
        assert "name" in df.columns
        assert "count" in df.columns
        assert "active" in df.columns
    finally:
        Path(filepath).unlink(missing_ok=True)
