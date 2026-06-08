"""
Unit tests for the exporters package.

Tests the FlatFileExporter class and convenience functions for CSV and Parquet export.
"""

import tempfile
from pathlib import Path
from uuid import UUID, uuid4

import polars as pl
import pytest
from pydantic import BaseModel, Field

from loyverse_sdk.exceptions import ExportError

# ---------------------------------------------------------------------------
# Test models
# ---------------------------------------------------------------------------


class SampleExportModel(BaseModel):
    """Simple model for testing basic export functionality."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    count: int
    price: float
    description: str
    active: bool = True


class CommaSampleModel(BaseModel):
    """Model with fields containing commas for CSV quoting tests."""

    id: UUID = Field(default_factory=uuid4)
    text: str


class TypeSampleModel(BaseModel):
    """Model with diverse types for Parquet type preservation tests."""

    id: UUID = Field(default_factory=uuid4)
    int_field: int
    float_field: float
    str_field: str
    bool_field: bool


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_single_model():
    """Create a single test model instance."""
    return SampleExportModel(
        name="Test Item",
        count=42,
        price=9.99,
        description="A simple test item for export",
        active=True,
    )


def make_model_list(count: int = 3):
    """Create a list of test model instances."""
    models = []
    for i in range(count):
        models.append(
            SampleExportModel(
                name=f"Item {i:03d}",
                count=i * 10,
                price=float(i) + 0.99,
                description=f"Description for item {i}",
                active=i % 2 == 0,
            )
        )
    return models


def read_csv_headers(filepath):
    """Read only the header row from a CSV file."""
    with open(filepath) as f:
        return f.readline().strip()


# ---------------------------------------------------------------------------
# Tests: FlatFileExporter instantiation
# ---------------------------------------------------------------------------


def test_exporter_instantiation():
    """FlatFileExporter can be instantiated without arguments."""
    from loyverse_sdk.exporters import FlatFileExporter

    exporter = FlatFileExporter()
    assert exporter is not None
    assert isinstance(exporter, FlatFileExporter)


def test_exporter_has_export_csv_method():
    """FlatFileExporter has an export_csv method."""
    from loyverse_sdk.exporters import FlatFileExporter

    exporter = FlatFileExporter()
    assert hasattr(exporter, "export_csv")
    assert callable(exporter.export_csv)


def test_exporter_has_export_parquet_method():
    """FlatFileExporter has an export_parquet method."""
    from loyverse_sdk.exporters import FlatFileExporter

    exporter = FlatFileExporter()
    assert hasattr(exporter, "export_parquet")
    assert callable(exporter.export_parquet)


# ---------------------------------------------------------------------------
# Tests: CSV export
# ---------------------------------------------------------------------------


def test_export_csv_basic():
    """export_csv with a single model creates a valid CSV file with a header row."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_csv([model], filepath)
        assert Path(filepath).exists()
        # Verify file has content (header + data row)
        lines = Path(filepath).read_text().splitlines()
        assert len(lines) >= 2  # header + at least one data row
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_csv_has_correct_headers():
    """CSV output has correct column headers matching model fields."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_csv([model], filepath)
        header_line = read_csv_headers(filepath)
        # Model fields should appear as headers (Polars order)
        expected_fields = {"id", "name", "count", "price", "description", "active"}
        actual_headers = set(header_line.split(","))
        assert expected_fields.issubset(actual_headers), (
            f"Expected headers to include {expected_fields}, got {actual_headers}"
        )
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_csv_multiple_records():
    """export_csv with multiple models creates the right number of data rows."""
    from loyverse_sdk.exporters import FlatFileExporter

    models = make_model_list(5)
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_csv(models, filepath)
        lines = Path(filepath).read_text().splitlines()
        assert len(lines) == 6  # 1 header + 5 data rows
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_csv_commas_in_string():
    """Fields containing commas are double-quoted in CSV output."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = CommaSampleModel(text="Hello, world, with commas")
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_csv([model], filepath)
        content = Path(filepath).read_text()
        # Polars double-quotes fields containing commas
        assert '"Hello, world, with commas"' in content
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_csv_empty_list():
    """export_csv with empty list warns but does not crash, creates header-only file."""
    from loyverse_sdk.exporters import FlatFileExporter

    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_csv([], filepath)
        assert Path(filepath).exists()
        # File should exist (header-only or empty)
        # Even with empty list, Polars may create an empty file
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_csv_invalid_path():
    """export_csv with invalid path raises ExportError."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with pytest.raises(ExportError):
        exporter.export_csv([model], "/nonexistent/directory/file.csv")


def test_export_csv_pathlib():
    """export_csv accepts pathlib.Path as filepath argument."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test.csv"
        exporter.export_csv([model], filepath)
        assert filepath.exists()
        assert filepath.stat().st_size > 0


# ---------------------------------------------------------------------------
# Tests: Parquet export
# ---------------------------------------------------------------------------


def test_export_parquet_basic():
    """export_parquet with a single model creates a valid Parquet file."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_parquet([model], filepath)
        assert Path(filepath).exists()
        assert Path(filepath).stat().st_size > 0
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_parquet_readable():
    """Exported Parquet file is readable by polars.read_parquet()."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_parquet([model], filepath)
        df = pl.read_parquet(filepath)
        assert df.height == 1
        assert df.width >= 5  # model has at least 5 fields
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_parquet_type_preservation():
    """Parquet output preserves column types: int stays int, float stays float, string stays string."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = TypeSampleModel(
        int_field=42, float_field=3.14, str_field="hello", bool_field=True
    )
    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_parquet([model], filepath)
        df = pl.read_parquet(filepath)
        assert df["int_field"].dtype == pl.Int64
        assert df["float_field"].dtype == pl.Float64
        assert df["str_field"].dtype == pl.Utf8
        assert df["bool_field"].dtype == pl.Boolean
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_parquet_empty_list():
    """export_parquet with empty list warns but does not crash."""
    from loyverse_sdk.exporters import FlatFileExporter

    exporter = FlatFileExporter()

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        exporter.export_parquet([], filepath)
        assert Path(filepath).exists()
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_export_parquet_invalid_path():
    """export_parquet with invalid path raises ExportError."""
    from loyverse_sdk.exporters import FlatFileExporter

    model = make_single_model()
    exporter = FlatFileExporter()

    with pytest.raises(ExportError):
        exporter.export_parquet([model], "/nonexistent/directory/file.parquet")


# ---------------------------------------------------------------------------
# Tests: Convenience functions
# ---------------------------------------------------------------------------


def test_convenience_export_csv():
    """Module-level export_csv() convenience function works."""
    from loyverse_sdk.exporters import export_csv

    model = make_single_model()

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        filepath = f.name

    try:
        export_csv([model], filepath)
        assert Path(filepath).exists()
        assert Path(filepath).stat().st_size > 0
    finally:
        Path(filepath).unlink(missing_ok=True)


def test_convenience_export_parquet():
    """Module-level export_parquet() convenience function works."""
    from loyverse_sdk.exporters import export_parquet

    model = make_single_model()

    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        filepath = f.name

    try:
        export_parquet([model], filepath)
        assert Path(filepath).exists()
        assert Path(filepath).stat().st_size > 0
    finally:
        Path(filepath).unlink(missing_ok=True)
