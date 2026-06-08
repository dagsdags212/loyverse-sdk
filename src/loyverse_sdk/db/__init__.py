"""
Database export utilities for Loyverse SDK.

This module provides DuckDB export functionality with:
- Schema management
- Data conversion
- Batch insertion
- Transaction management
"""

from loyverse_sdk.db.connection import (
    DuckDBConnection,
    database_exists,
    get_all_tables,
    get_table_count,
    table_exists,
)
from loyverse_sdk.db.converters import (
    convert_uuid_fields,
    pydantic_to_sql_dict,
    split_nested_data,
)
from loyverse_sdk.db.exporter import (
    DuckDBExporter,
    quick_export,
)
from loyverse_sdk.db.progress import ExportProgress
from loyverse_sdk.db.schema_builder import (
    create_duckdb_schema,
    create_indexes,
)

__all__ = [
    # Schema
    "create_duckdb_schema",
    "create_indexes",
    # Connection
    "DuckDBConnection",
    "database_exists",
    "get_table_count",
    "get_all_tables",
    "table_exists",
    # Converters
    "pydantic_to_sql_dict",
    "split_nested_data",
    "convert_uuid_fields",
    # Exporter
    "DuckDBExporter",
    "quick_export",
    # Progress
    "ExportProgress",
]
