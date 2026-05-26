"""
DuckDB exporter for Loyverse data.

This module orchestrates the export of all Loyverse resources to a DuckDB database,
handling pagination, data transformation, and batch insertion.
"""

from datetime import datetime
from typing import Callable, Optional
import duckdb
import polars as pl

from loyverse_sdk.db.schema_builder import create_duckdb_schema, create_indexes
from loyverse_sdk.db.connection import DuckDBConnection, table_exists
from loyverse_sdk.db.converters import pydantic_to_sql_dict, split_nested_data
from loyverse_sdk.exceptions import ExportError


class DuckDBExporter:
    """
    Orchestrates export of Loyverse data to DuckDB database.

    Handles streaming data from the API, transforming it for DuckDB,
    and batch insertion with proper transaction management.

    Example:
        from loyverse_sdk import LoyverseClient
        from loyverse_sdk.db.exporter import DuckDBExporter

        client = LoyverseClient()
        exporter = DuckDBExporter(client, "loyverse.duckdb")

        # Full export
        counts = await exporter.export_all()
        print(f"Exported {sum(counts.values())} total records")

        await client.close()
    """

    # Resource export order (respects foreign key dependencies)
    RESOURCE_ORDER = [
        # Independent tables (no foreign keys)
        "categories",
        "stores",
        "suppliers",
        "taxes",
        "modifiers",
        "discounts",
        # Depends on stores
        "employees",
        "pos_devices",
        # Independent
        "customers",
        "payment_types",
        # Depends on categories, suppliers
        "items",
        # Depends on items
        "variants",
        # Depends on variants + stores (variant_id FK, store_id FK)
        "inventory",
        # Depends on many (customer, employee, store, device, payment_type)
        "receipts",
        # Merchant (single record)
        "merchant",
    ]

    def __init__(self, client, db_path: str):
        """
        Initialize the DuckDB exporter.

        Args:
            client: LoyverseClient instance
            db_path: Path to DuckDB database file

        Example:
            from loyverse_sdk import LoyverseClient

            client = LoyverseClient()
            exporter = DuckDBExporter(client, "loyverse.duckdb")
        """
        self.client = client
        self.db_path = db_path
        self.connection = DuckDBConnection(db_path)

    async def export_all(
        self,
        resources: Optional[list[str]] = None,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None,
        updated_at_min: Optional[datetime] = None,
        updated_at_max: Optional[datetime] = None,
        batch_size: int = 1000,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
        create_indexes_after: bool = True,
    ) -> dict[str, int]:
        """
        Export all or selected resources to DuckDB.

        Args:
            resources: List of resource names to export (None = all)
            created_at_min: Filter records created after this datetime
            created_at_max: Filter records created before this datetime
            updated_at_min: Filter records updated after this datetime
            updated_at_max: Filter records updated before this datetime
            batch_size: Number of records to insert per transaction
            progress_callback: Optional callback(resource_name, current, total)
            create_indexes_after: Create indexes after export completes

        Returns:
            Dictionary mapping resource names to record counts

        Raises:
            ExportError: If export fails

        Example:
            # Full export
            counts = await exporter.export_all()

            # Selective export
            counts = await exporter.export_all(
                resources=["categories", "items", "receipts"]
            )

            # Date range export
            from datetime import datetime, timedelta
            counts = await exporter.export_all(
                created_at_min=datetime.now() - timedelta(days=30)
            )
        """
        # Initialize schema if needed
        if not table_exists(self.db_path, "categories"):
            self.init_schema(drop_existing=False)

        # Filter resources if specified
        resource_order = self.RESOURCE_ORDER.copy()
        if resources:
            resource_order = [r for r in resource_order if r in resources]

        # Export each resource in dependency order
        export_counts = {}
        for resource_name in resource_order:
            try:
                count = await self.export_resource(
                    resource_name,
                    created_at_min=created_at_min,
                    created_at_max=created_at_max,
                    updated_at_min=updated_at_min,
                    updated_at_max=updated_at_max,
                    batch_size=batch_size,
                    progress_callback=progress_callback,
                )
                export_counts[resource_name] = count
            except (ExportError, duckdb.Error) as e:
                if not isinstance(e, ExportError):
                    e = ExportError(str(e), resource_name=resource_name)
                raise ExportError(
                    f"Failed to export {resource_name}: {e}",
                    resource_name=resource_name,
                )

        # Create indexes if requested
        if create_indexes_after:
            try:
                create_indexes(self.db_path)
            except duckdb.Error as e:
                # Don't fail export if index creation fails
                print(f"Warning: Failed to create indexes: {e}")

        # Update sync metadata
        self._update_sync_metadata(export_counts)

        return export_counts

    async def export_resource(
        self,
        resource_name: str,
        created_at_min: Optional[datetime] = None,
        created_at_max: Optional[datetime] = None,
        updated_at_min: Optional[datetime] = None,
        updated_at_max: Optional[datetime] = None,
        batch_size: int = 1000,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> int:
        """
        Export a single resource to DuckDB.

        Args:
            resource_name: Name of resource (e.g., "receipts", "items")
            created_at_min: Filter records created after this datetime
            created_at_max: Filter records created before this datetime
            updated_at_min: Filter records updated after this datetime
            updated_at_max: Filter records updated before this datetime
            batch_size: Number of records per batch
            progress_callback: Optional callback(resource_name, current, total)

        Returns:
            Number of records exported

        Raises:
            ExportError: If export fails

        Example:
            count = await exporter.export_resource("receipts")
            print(f"Exported {count} receipts")
        """
        # Get endpoint for this resource
        if resource_name not in self.client.endpoints:
            raise ExportError(
                f"Unknown resource: {resource_name}", resource_name=resource_name
            )

        endpoint = self.client.endpoints[resource_name]

        # Check if endpoint supports pagination
        if not hasattr(endpoint, "iter_all"):
            # Merchant endpoint doesn't support pagination (single record)
            if resource_name == "merchant":
                return await self._export_merchant()
            else:
                raise ExportError(
                    f"Resource {resource_name} does not support pagination",
                    resource_name=resource_name,
                )

        # Stream records and batch insert
        total_count = 0
        batch = []

        async for record in endpoint.iter_all(
            created_at_min=created_at_min,
            created_at_max=created_at_max,
            updated_at_min=updated_at_min,
            updated_at_max=updated_at_max,
        ):
            # Convert Pydantic model to dict
            record_dict = pydantic_to_sql_dict(record)

            # Split into main/junction/child data
            main_record, junction_records, child_records = split_nested_data(
                resource_name, record_dict
            )

            # Add to batch
            batch.append((main_record, junction_records, child_records))
            total_count += 1

            # Insert batch when size reached
            if len(batch) >= batch_size:
                self._batch_insert(resource_name, batch)
                batch = []

            # Call progress callback
            if progress_callback:
                progress_callback(resource_name, total_count, -1)

        # Insert remaining records
        if batch:
            self._batch_insert(resource_name, batch)

        return total_count

    async def _export_merchant(self) -> int:
        """Export merchant (single record endpoint)."""
        try:
            merchant = await self.client.merchant.retrieve()
            merchant_dict = pydantic_to_sql_dict(merchant)

            with self.connection.transaction() as conn:
                self._insert_records_to_table(conn, "merchant", [merchant_dict])

            return 1
        except Exception as e:
            if not isinstance(e, ExportError):
                raise ExportError(f"Failed to export merchant: {e}", "merchant") from e
            raise

    def _batch_insert(
        self, resource_name: str, batch: list[tuple[dict, dict, dict]]
    ) -> None:
        """
        Insert a batch of records with transaction management.

        Args:
            resource_name: Name of the resource
            batch: List of (main_record, junction_records, child_records) tuples

        Raises:
            ExportError: If insertion fails
        """
        if not batch:
            return

        try:
            with self.connection.transaction() as conn:
                # Insert main table records
                main_records = [item[0] for item in batch]
                if main_records:
                    self._insert_records_to_table(conn, resource_name, main_records)

                # Insert junction table records
                all_junction_records = {}
                for _, junction_records, _ in batch:
                    for table_name, records in junction_records.items():
                        if table_name not in all_junction_records:
                            all_junction_records[table_name] = []
                        all_junction_records[table_name].extend(records)

                for table_name, records in all_junction_records.items():
                    if records:
                        self._insert_records_to_table(conn, table_name, records)

                # Insert child table records
                all_child_records = {}
                for _, _, child_records in batch:
                    for table_name, records in child_records.items():
                        if table_name not in all_child_records:
                            all_child_records[table_name] = []
                        all_child_records[table_name].extend(records)

                for table_name, records in all_child_records.items():
                    if records:
                        self._insert_records_to_table(conn, table_name, records)

        except (ExportError, duckdb.Error) as e:
            if not isinstance(e, ExportError):
                raise ExportError(str(e), resource_name=resource_name) from e
            raise ExportError(
                f"Failed to insert batch for {resource_name}: {e}",
                resource_name=resource_name,
            )

    def _insert_records_to_table(
        self, conn: duckdb.DuckDBPyConnection, table_name: str, records: list[dict]
    ) -> None:
        """
        Insert records into a table using Polars + DuckDB for performance.

        Uses INSERT OR REPLACE for upsert semantics.

        Args:
            conn: DuckDB connection
            table_name: Target table name
            records: List of record dictionaries

        Raises:
            Exception: If insertion fails
        """
        if not records:
            return

        try:
            # Convert to Polars DataFrame
            df = pl.DataFrame(records)

            # Register DataFrame with DuckDB
            conn.register("temp_df", df)

            # Insert using INSERT OR REPLACE (upsert)
            # Note: DuckDB doesn't have native UPSERT, so we use INSERT OR REPLACE
            # which works for tables with PRIMARY KEY constraints
            conn.execute(f"""
                INSERT OR REPLACE INTO {table_name}
                SELECT * FROM temp_df
            """)

            # Unregister temporary DataFrame
            conn.unregister("temp_df")

        except pl.exceptions.PolarsError as e:
            # Try alternative approach if Polars fails
            try:
                # Fallback: Use DuckDB's direct insert
                # Build column list from first record
                if records:
                    columns = list(records[0].keys())
                    placeholders = ", ".join(["?" for _ in columns])
                    columns_str = ", ".join(columns)

                    # Prepare values
                    values = [[r.get(c) for c in columns] for r in records]

                    # Execute batch insert
                    conn.executemany(
                        f"INSERT OR REPLACE INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                        values,
                    )
            except duckdb.Error as fallback_error:
                raise ExportError(
                    f"Failed to insert into {table_name}: {e}. "
                    f"Fallback also failed: {fallback_error}"
                )

    def init_schema(self, drop_existing: bool = False) -> None:
        """
        Initialize the DuckDB database schema.

        Args:
            drop_existing: If True, drops all tables before creating

        Example:
            exporter.init_schema(drop_existing=True)
        """
        create_duckdb_schema(self.db_path, drop_existing=drop_existing)

    def _update_sync_metadata(self, export_counts: dict[str, int]) -> None:
        """
        Update sync metadata table with export information.

        Args:
            export_counts: Dictionary of resource names to record counts
        """
        try:
            with self.connection.transaction() as conn:
                current_time = datetime.now()

                for resource_name, count in export_counts.items():
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO sync_metadata
                        (resource_name, last_sync_at, records_count, sync_type)
                        VALUES (?, ?, ?, ?)
                    """,
                        (resource_name, current_time, count, "full"),
                    )

        except duckdb.Error as e:
            # Don't fail export if metadata update fails
            print(f"Warning: Failed to update sync metadata: {e}")

    def get_sync_metadata(self) -> dict[str, dict]:
        """
        Get sync metadata for all resources.

        Returns:
            Dictionary mapping resource names to metadata

        Example:
            metadata = exporter.get_sync_metadata()
            for resource, info in metadata.items():
                print(f"{resource}: {info['records_count']} records, "
                      f"last synced {info['last_sync_at']}")
        """
        try:
            conn = self.connection.connect()
            result = conn.execute("""
                SELECT resource_name, last_sync_at, records_count, sync_type
                FROM sync_metadata
                ORDER BY last_sync_at DESC
            """).fetchall()

            metadata = {}
            for row in result:
                metadata[row[0]] = {
                    "last_sync_at": row[1],
                    "records_count": row[2],
                    "sync_type": row[3],
                }

            return metadata

        except duckdb.Error:
            return {}

    def get_table_counts(self) -> dict[str, int]:
        """
        Get record counts for all main tables.

        Returns:
            Dictionary mapping table names to record counts

        Example:
            counts = exporter.get_table_counts()
            print(f"Database contains {sum(counts.values())} total records")
        """
        try:
            conn = self.connection.connect()
            counts = {}

            for resource in self.RESOURCE_ORDER:
                try:
                    result = conn.execute(f"SELECT COUNT(*) FROM {resource}").fetchone()
                    counts[resource] = result[0] if result else 0
                except duckdb.Error:
                    counts[resource] = 0

            return counts

        except duckdb.Error:
            return {}

    def close(self) -> None:
        """Close the database connection."""
        self.connection.close()

    def __enter__(self):
        """Support using exporter as context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context."""
        self.close()
        return False


def quick_export(
    client, db_path: str, resources: Optional[list[str]] = None, **kwargs
) -> dict[str, int]:
    """
    Convenience function for quick exports.

    Args:
        client: LoyverseClient instance
        db_path: Path to DuckDB database
        resources: Optional list of resources to export
        **kwargs: Additional arguments passed to export_all()

    Returns:
        Dictionary of resource counts

    Example:
        from loyverse_sdk import LoyverseClient
        from loyverse_sdk.db.exporter import quick_export

        async def main():
            client = LoyverseClient()
            counts = await quick_export(
                client,
                "loyverse.duckdb",
                resources=["receipts", "customers"]
            )
            await client.close()
    """
    exporter = DuckDBExporter(client, db_path)
    try:
        return exporter.export_all(resources=resources, **kwargs)
    finally:
        exporter.close()
