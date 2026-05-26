"""
Export utilities for flat-file formats (CSV and Parquet).

Provides a stateless FlatFileExporter class that converts lists of Pydantic
model instances into CSV or Parquet files using Polars for efficient
serialization.
"""

from pathlib import Path
from typing import Sequence

import polars as pl
from pydantic import BaseModel

from loyverse_sdk.exceptions import ExportError


class FlatFileExporter:
    """
    Stateless exporter that writes Pydantic model instances to flat files.

    Converts lists of Pydantic model instances to Polars DataFrames,
    then writes them to CSV or Parquet files on disk.

    Two export methods are available:
    - ``export_csv``: Writes comma-separated values with headers and
      double-quote quoting for fields containing special characters.
    - ``export_parquet``: Writes Parquet files with Snappy compression.

    Usage::

        from loyverse_sdk.exporters import FlatFileExporter

        exporter = FlatFileExporter()
        exporter.export_csv(models, "output.csv")
        exporter.export_parquet(models, "output.parquet")
    """

    EXPORT_RESOURCE_NAME = "file_export"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_csv(self, data: Sequence[BaseModel], filepath: str | Path) -> None:
        """
        Export a list of Pydantic model instances to a CSV file.

        Uses Polars default CSV settings: comma delimiter, double-quote
        quoting, UTF-8 encoding, headers included.

        Args:
            data: A sequence of Pydantic model instances to export.
            filepath: Destination file path (``str`` or ``pathlib.Path``).

        Raises:
            ExportError: If the file cannot be written.

        Example:
            exporter.export_csv(customers, "customers.csv")
            exporter.export_csv(empty_list, "empty.csv")  # header-only
        """
        self._export(data, filepath, format="csv")

    def export_parquet(self, data: Sequence[BaseModel], filepath: str | Path) -> None:
        """
        Export a list of Pydantic model instances to a Parquet file.

        Uses Snappy compression (Polars default for Parquet).

        Args:
            data: A sequence of Pydantic model instances to export.
            filepath: Destination file path (``str`` or ``pathlib.Path``).

        Raises:
            ExportError: If the file cannot be written.

        Example:
            exporter.export_parquet(customers, "customers.parquet")
        """
        self._export(data, filepath, format="parquet")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _convert_to_dataframe(self, data: Sequence[BaseModel]) -> pl.DataFrame | None:
        """
        Convert a sequence of Pydantic models to a Polars DataFrame.

        Each model is serialized to a dict via ``model_dump()``. Empty input
        produces ``None`` so callers can decide how to handle it.

        Args:
            data: A sequence of Pydantic model instances.

        Returns:
            A Polars DataFrame, or ``None`` if the input is empty.
        """
        if not data:
            return None

        # Use mode='json' so UUID→str, datetime→ISO str, etc.
        # Polars CSV/Parquet writers don't support Object dtype.
        records = [model.model_dump(mode="json") for model in data]
        return pl.DataFrame(records)

    def _export(
        self,
        data: Sequence[BaseModel],
        filepath: str | Path,
        format: str,
    ) -> None:
        """
        Shared export logic for CSV and Parquet.

        Args:
            data: A sequence of Pydantic model instances.
            filepath: Destination file path.
            format: ``"csv"`` or ``"parquet"``.

        Raises:
            ExportError: If the write operation fails.
        """
        filepath = Path(filepath)
        df = self._convert_to_dataframe(data)

        try:
            if df is None:
                # Empty input — warn and write an empty file with headers if possible.
                print(
                    f"Warning: Empty data provided for {format} export "
                    f"to {filepath}. Creating empty file."
                )
                if format == "csv":
                    filepath.write_text("")
                elif format == "parquet":
                    # Parquet files require a schema; create an empty one.
                    # Using pl.DataFrame() with no data produces a valid
                    # 0-row, 0-column Parquet file.
                    pl.DataFrame().write_parquet(filepath)
                return

            if format == "csv":
                df.write_csv(filepath)
            elif format == "parquet":
                df.write_parquet(filepath, compression="snappy")
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            # Don't re-wrap ExportError instances
            if isinstance(e, ExportError):
                raise
            raise ExportError(
                f"Failed to write {format.upper()} file: {e}",
                resource_name=self.EXPORT_RESOURCE_NAME,
            ) from e


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------


def export_csv(data: Sequence[BaseModel], filepath: str | Path) -> None:
    """
    Convenience function for CSV export.

    Equivalent to ``FlatFileExporter().export_csv(data, filepath)``.

    Args:
        data: A sequence of Pydantic model instances to export.
        filepath: Destination file path (``str`` or ``pathlib.Path``).

    Raises:
        ExportError: If the file cannot be written.
    """
    FlatFileExporter().export_csv(data, filepath)


def export_parquet(data: Sequence[BaseModel], filepath: str | Path) -> None:
    """
    Convenience function for Parquet export.

    Equivalent to ``FlatFileExporter().export_parquet(data, filepath)``.

    Args:
        data: A sequence of Pydantic model instances to export.
        filepath: Destination file path (``str`` or ``pathlib.Path``).

    Raises:
        ExportError: If the file cannot be written.
    """
    FlatFileExporter().export_parquet(data, filepath)
