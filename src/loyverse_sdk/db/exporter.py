"""
DuckDB exporter for Loyverse data.

This module orchestrates the export of all Loyverse resources to a DuckDB database,
handling pagination, data transformation, and batch insertion.
"""

from collections.abc import Callable
from datetime import datetime

import duckdb
import polars as pl

from loyverse_sdk.core.console import console
from loyverse_sdk.db.connection import DuckDBConnection, database_exists
from loyverse_sdk.db.converters import pydantic_to_sql_dict, split_nested_data
from loyverse_sdk.db.progress import ExportProgress
from loyverse_sdk.db.schema_builder import create_duckdb_schema, create_indexes
from loyverse_sdk.exceptions import ExportError
from loyverse_sdk.models import (
    CategoryListQuery,
    CustomerListQuery,
    DiscountListQuery,
    EmployeeListQuery,
    InventoryListQuery,
    ItemListQuery,
    ModifierListQuery,
    PaymentTypeListQuery,
    PosDeviceListQuery,
    ReceiptListQuery,
    ShiftListQuery,
    StoreListQuery,
    SupplierListQuery,
    TaxListQuery,
    VariantListQuery,
    WebhookListQuery,
)


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
        # Depends on receipt-level metrics
        "shifts",
        # Independent (management)
        "webhooks",
        # Merchant (single record)
        "merchant",
    ]

    def __init__(self, client, db_path: str, show_progress: bool = True):
        """
        Initialize the DuckDB exporter.

        Args:
            client: LoyverseClient instance
            db_path: Path to DuckDB database file
            show_progress: Display real-time progress during export (default: True)

        Example:
            from loyverse_sdk import LoyverseClient

            client = LoyverseClient()
            exporter = DuckDBExporter(client, "loyverse.duckdb")
        """
        self.client = client
        self.db_path = db_path
        self.connection = DuckDBConnection(db_path)
        self.show_progress = show_progress

    # Mapping from resource names to their Query classes
    QUERY_CLASSES: dict[str, type] = {
        "categories": CategoryListQuery,
        "customers": CustomerListQuery,
        "discounts": DiscountListQuery,
        "employees": EmployeeListQuery,
        "inventory": InventoryListQuery,
        "items": ItemListQuery,
        "modifiers": ModifierListQuery,
        "payment_types": PaymentTypeListQuery,
        "pos_devices": PosDeviceListQuery,
        "receipts": ReceiptListQuery,
        "stores": StoreListQuery,
        "suppliers": SupplierListQuery,
        "taxes": TaxListQuery,
        "variants": VariantListQuery,
        "shifts": ShiftListQuery,
        "webhooks": WebhookListQuery,
    }

    async def export_all(
        self,
        resources: list[str] | None = None,
        created_at_min: datetime | None = None,
        created_at_max: datetime | None = None,
        updated_at_min: datetime | None = None,
        updated_at_max: datetime | None = None,
        batch_size: int = 1000,
        progress_callback: Callable[[str, int, int], None] | None = None,
        create_indexes_after: bool = True,
        show_progress: bool | None = None,
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
            show_progress: Display real-time progress (overrides instance default)

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
        # Determine if progress should be shown
        use_progress = (
            show_progress if show_progress is not None else self.show_progress
        )

        # Initialize schema if database doesn't exist yet
        schema_is_new = not database_exists(self.db_path)
        if schema_is_new:
            if use_progress:
                console.log("[bold]Initializing DuckDB schema...[/bold]")
            self.init_schema(drop_existing=False)

        # Filter resources if specified
        resource_order = self.RESOURCE_ORDER.copy()
        if resources:
            resource_order = [r for r in resource_order if r in resources]

        # Set up progress tracker
        tracker = ExportProgress(
            total_resources=len(resource_order),
            console=console,
            enabled=use_progress and progress_callback is None,
        )
        if tracker.enabled:
            tracker.start()

        # Export each resource in dependency order
        export_counts = {}
        total_errors = 0
        for resource_name in resource_order:
            if tracker.enabled:
                tracker.begin_resource(resource_name)
            try:
                # Chain the progress tracker into the callback
                def make_callback(name: str, t: ExportProgress):
                    def cb(rname: str, current: int, total: int) -> None:
                        if progress_callback:
                            progress_callback(rname, current, total)
                        if t.enabled:
                            t.update_count(name, current)

                    return cb

                count = await self.export_resource(
                    resource_name,
                    created_at_min=created_at_min,
                    created_at_max=created_at_max,
                    updated_at_min=updated_at_min,
                    updated_at_max=updated_at_max,
                    batch_size=batch_size,
                    progress_callback=make_callback(resource_name, tracker),
                )
                export_counts[resource_name] = count
                if tracker.enabled:
                    tracker.finish_resource(resource_name, count)
            except (ExportError, duckdb.Error) as e:
                if not isinstance(e, ExportError):
                    e = ExportError(str(e), resource_name=resource_name)
                total_errors += 1
                if tracker.enabled:
                    tracker.error_resource(resource_name, str(e))
                raise ExportError(
                    f"Failed to export {resource_name}: {e}",
                    resource_name=resource_name,
                ) from e

        # Create indexes if requested
        if create_indexes_after:
            try:
                if tracker.enabled:
                    console.log("[dim]Creating indexes...[/dim]")
                self.connection.close()
                create_indexes(self.db_path)
            except duckdb.Error as e:
                msg = f"Failed to create indexes: {e}"
                if tracker.enabled:
                    tracker.add_warning(msg)
                else:
                    console.log(f"[yellow]Warning: {msg}[/yellow]")

        # Update sync metadata
        self._update_sync_metadata(export_counts)

        # Finish progress display
        total_records = sum(export_counts.values())
        if tracker.enabled:
            tracker.finish(total_records)
            console.log(
                f"[bold green]Export complete: {total_records:,} records "
                f"across {len(export_counts)} resources[/bold green]"
            )
            if total_errors > 0:
                console.log(f"[bold red]{total_errors} resource(s) failed[/bold red]")

        return export_counts

    async def sync_all(
        self,
        resources: list[str] | None = None,
        batch_size: int = 1000,
        progress_callback: Callable[[str, int, int], None] | None = None,
        show_progress: bool | None = None,
        create_indexes_after: bool = True,
    ) -> dict[str, int]:
        """Incremental sync: only fetch records updated since the last sync.

        Reads ``last_sync_at`` from the ``sync_metadata`` table for each
        resource. Resources that have never been synced get a full export.
        After completion the metadata table is updated with
        ``sync_type="incremental"``.

        Args:
            resources: Resource names to sync (None = all).
            batch_size: Records per transaction.
            progress_callback: Optional ``callback(resource, current, total)``.
            show_progress: Override instance default for progress display.
            create_indexes_after: Create indexes when sync completes.

        Returns:
            Dictionary mapping resource names to record counts.

        Raises:
            ExportError: If the sync fails entirely.
        """
        use_progress = show_progress if show_progress is not None else self.show_progress

        schema_is_new = not database_exists(self.db_path)
        if schema_is_new:
            if use_progress:
                console.log("[bold]Initializing DuckDB schema...[/bold]")
            self.init_schema(drop_existing=False)

        sync_meta = self.get_sync_metadata() if not schema_is_new else {}

        ordered_resources = [
            r for r in self.RESOURCE_ORDER
            if resources is None or r in resources
        ]

        tracker = ExportProgress(
            total_resources=len(ordered_resources),
            console=console,
            enabled=use_progress,
        )
        if tracker.enabled:
            tracker.start()

        total_errors = 0
        export_counts: dict[str, int] = {}

        for resource in ordered_resources:
            tracker.begin_resource(resource)
            try:
                meta = sync_meta.get(resource)
                updated_at_min = meta["last_sync_at"] if meta else None

                def make_callback(
                    res: str,
                    tracker: ExportProgress = tracker,
                    user_cb=progress_callback,
                ):
                    def inner(resource_name: str, current: int, total: int):
                        tracker.update_count(resource_name, current)
                        if user_cb:
                            user_cb(resource_name, current, total)

                    return inner

                count = await self.export_resource(
                    resource,
                    updated_at_min=updated_at_min,
                    batch_size=batch_size,
                    progress_callback=make_callback(resource),
                )
                export_counts[resource] = count
                tracker.finish_resource(resource, count)
            except Exception as e:
                total_errors += 1
                msg = f"Failed to sync {resource}: {e}"
                if tracker.enabled:
                    tracker.error_resource(resource, str(e))
                    tracker.add_warning(msg)
                else:
                    console.log(f"[red]{msg}[/red]")
                export_counts[resource] = 0

        if sum(export_counts.values()) == 0 and total_errors == len(ordered_resources):
            raise ExportError("All resources failed to sync.")

        if create_indexes_after:
            try:
                if tracker.enabled:
                    console.log("[dim]Creating indexes...[/dim]")
                self.connection.close()
                create_indexes(self.db_path)
            except duckdb.Error as e:
                msg = f"Failed to create indexes: {e}"
                if tracker.enabled:
                    tracker.add_warning(msg)
                else:
                    console.log(f"[yellow]Warning: {msg}[/yellow]")

        self._update_sync_metadata(
            export_counts,
            sync_type="incremental" if not schema_is_new else "full",
        )

        total_records = sum(export_counts.values())
        if tracker.enabled:
            tracker.finish(total_records)
            console.log(
                f"[bold green]Sync complete: {total_records:,} new/updated records "
                f"across {len(export_counts)} resources[/bold green]"
            )
            if total_errors > 0:
                console.log(
                    f"[bold red]{total_errors} resource(s) failed[/bold red]"
                )

        return export_counts

    async def export_resource(
        self,
        resource_name: str,
        created_at_min: datetime | None = None,
        created_at_max: datetime | None = None,
        updated_at_min: datetime | None = None,
        updated_at_max: datetime | None = None,
        batch_size: int = 1000,
        progress_callback: Callable[[str, int, int], None] | None = None,
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

        # Build query using resource-specific Query class
        query_cls = self.QUERY_CLASSES.get(resource_name)
        if query_cls:
            query = query_cls(
                created_at_min=created_at_min,
                created_at_max=created_at_max,
                updated_at_min=updated_at_min,
                updated_at_max=updated_at_max,
            )
        else:
            # Fallback for resources without Query classes
            # (shouldn't happen with current RESOURCE_ORDER)
            query = None

        # Stream records and batch insert
        total_count = 0
        batch = []

        async for record in endpoint.iter_all(query=query):
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
            ) from e

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

            # Get column names in order and quote them for DuckDB
            columns = df.columns
            quoted_columns = [f'"{col}"' for col in columns]

            # Register DataFrame with DuckDB
            conn.register("temp_df", df)

            # Insert using INSERT OR REPLACE with explicit column list
            # Using explicit columns instead of SELECT * to avoid column count mismatches
            # Quoting column names to handle reserved words like "order"
            columns_str = ", ".join(quoted_columns)
            conn.execute(f"""
                INSERT OR REPLACE INTO {table_name} ({columns_str})
                SELECT {columns_str} FROM temp_df
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
                ) from fallback_error

    def init_schema(self, drop_existing: bool = False) -> None:
        """
        Initialize the DuckDB database schema.

        Args:
            drop_existing: If True, drops all tables before creating

        Example:
            exporter.init_schema(drop_existing=True)
        """
        create_duckdb_schema(self.db_path, drop_existing=drop_existing)

    def _update_sync_metadata(
        self,
        export_counts: dict[str, int],
        sync_type: str = "full",
    ) -> None:
        """Update sync metadata table with export information.

        Args:
            export_counts: Dictionary of resource names to record counts.
            sync_type: ``"full"`` or ``"incremental"``.
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
                        (resource_name, current_time, count, sync_type),
                    )

        except duckdb.Error as e:
            # Don't fail export if metadata update fails
            console.log(
                f"[yellow]Warning: Failed to update sync metadata: {e}[/yellow]"
            )

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


async def quick_export(
    client, db_path: str, resources: list[str] | None = None, **kwargs
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
        return await exporter.export_all(resources=resources, **kwargs)
    finally:
        exporter.close()
