"""
Example usage of DuckDB export functionality.

This script demonstrates how to export Loyverse data to a local DuckDB database
for analytics and reporting purposes.

Prerequisites:
    - LOYVERSE_API_TOKEN environment variable set
    - Install dependencies: uv sync (or pip install loyverse-sdk)

Usage:
    python examples/duckdb_export.py
"""

import asyncio
import os
from datetime import datetime, timedelta

from loyverse_sdk import LoyverseClient


async def example_full_export():
    """Example 1: Export all Loyverse data to DuckDB."""
    print("\n=== Example 1: Full Export ===\n")

    # Initialize client
    client = LoyverseClient()

    # Export all data
    print("Exporting all Loyverse data...")
    counts = await client.export_to_duckdb("loyverse.duckdb")

    print("\n✓ Export completed!")
    print("\nRecords exported:")
    for resource, count in sorted(counts.items()):
        print(f"  {resource:20} {count:>6,} records")

    total = sum(counts.values())
    print(f"\n  {'Total':20} {total:>6,} records")

    await client.close()


async def example_selective_export():
    """Example 2: Export only specific resources."""
    print("\n=== Example 2: Selective Export ===\n")

    client = LoyverseClient()

    # Export only receipts, customers, and items
    print("Exporting receipts, customers, and items...")
    counts = await client.export_to_duckdb(
        "loyverse.duckdb",
        resources=["receipts", "customers", "items"]
    )

    print("\n✓ Export completed!")
    for resource, count in counts.items():
        print(f"  {resource}: {count:,} records")

    await client.close()


async def example_date_range_export():
    """Example 3: Export data for a specific date range."""
    print("\n=== Example 3: Date Range Export ===\n")

    client = LoyverseClient()

    # Export last 30 days of receipts
    start_date = datetime.now() - timedelta(days=30)
    end_date = datetime.now()

    print(f"Exporting receipts from {start_date.date()} to {end_date.date()}...")
    counts = await client.export_to_duckdb(
        "loyverse.duckdb",
        resources=["receipts"],
        created_at_min=start_date,
        created_at_max=end_date
    )

    print(f"\n✓ Exported {counts['receipts']:,} receipts from the last 30 days")

    await client.close()


async def example_with_progress_callback():
    """Example 4: Export with progress tracking."""
    print("\n=== Example 4: Export with Progress Tracking ===\n")

    client = LoyverseClient()

    def progress(resource_name: str, current: int, total: int):
        """Progress callback function."""
        # Note: total is -1 for streaming exports (unknown total)
        if total > 0:
            percent = (current / total) * 100
            print(f"  {resource_name}: {current:,}/{total:,} ({percent:.1f}%)")
        else:
            print(f"  {resource_name}: {current:,} records processed...")

    print("Exporting with progress tracking...")
    counts = await client.export_to_duckdb(
        "loyverse.duckdb",
        resources=["categories", "items"],
        progress_callback=progress
    )

    print("\n✓ Export completed!")
    for resource, count in counts.items():
        print(f"  {resource}: {count:,} records")

    await client.close()


async def example_single_resource():
    """Example 5: Export a single resource with fine-grained control."""
    print("\n=== Example 5: Single Resource Export ===\n")

    client = LoyverseClient()

    # Export only customers
    print("Exporting customers...")
    count = await client.export_resource_to_duckdb(
        "customers",
        "loyverse.duckdb"
    )

    print(f"\n✓ Exported {count:,} customers")

    await client.close()


async def example_schema_initialization():
    """Example 6: Initialize database schema without exporting data."""
    print("\n=== Example 6: Schema Initialization ===\n")

    client = LoyverseClient()

    # Create empty database with schema
    print("Initializing DuckDB schema...")
    client.init_duckdb_schema("loyverse.duckdb")

    print("✓ Schema created successfully!")
    print("\nDatabase tables created:")
    print("  - 14 main tables (categories, items, receipts, etc.)")
    print("  - 8 junction tables (many-to-many relationships)")
    print("  - 2 child tables (nested data)")
    print("  - 1 metadata table (sync tracking)")

    await client.close()


async def example_query_exported_data():
    """Example 7: Query exported data using DuckDB."""
    print("\n=== Example 7: Querying Exported Data ===\n")

    import duckdb

    # Connect to exported database
    conn = duckdb.connect("loyverse.duckdb")

    # Query 1: Top 10 customers by total spent
    print("Top 10 customers by total spent:")
    result = conn.execute("""
        SELECT
            c.name,
            COUNT(DISTINCT r.id) as receipt_count,
            SUM(r.total_amount) as total_spent
        FROM customers c
        JOIN receipts r ON c.id = r.customer_id
        WHERE r.receipt_type = 'SALE'
        GROUP BY c.id, c.name
        ORDER BY total_spent DESC
        LIMIT 10
    """).fetchall()

    if result:
        print("\n  Customer Name              Receipts    Total Spent")
        print("  " + "-" * 58)
        for row in result:
            print(f"  {row[0]:25} {row[1]:>8}    ${row[2]:>10,.2f}")
    else:
        print("  (No data found)")

    # Query 2: Daily revenue for last 30 days
    print("\n\nDaily revenue for last 30 days:")
    result = conn.execute("""
        SELECT
            DATE(receipt_date) as date,
            COUNT(*) as receipt_count,
            SUM(total_amount) as revenue
        FROM receipts
        WHERE receipt_type = 'SALE'
          AND receipt_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(receipt_date)
        ORDER BY date DESC
        LIMIT 10
    """).fetchall()

    if result:
        print("\n  Date          Receipts    Revenue")
        print("  " + "-" * 40)
        for row in result:
            print(f"  {row[0]}      {row[1]:>6}    ${row[2]:>10,.2f}")
    else:
        print("  (No data found)")

    # Query 3: Item performance
    print("\n\nTop 10 best-selling items:")
    result = conn.execute("""
        SELECT
            i.name,
            SUM(l.quantity) as units_sold,
            SUM(l.quantity * l.price) as revenue
        FROM items i
        JOIN receipt_line_items l ON i.id = l.item_id
        JOIN receipts r ON l.receipt_id = r.id
        WHERE r.receipt_type = 'SALE'
        GROUP BY i.id, i.name
        ORDER BY units_sold DESC
        LIMIT 10
    """).fetchall()

    if result:
        print("\n  Item Name                  Units Sold    Revenue")
        print("  " + "-" * 58)
        for row in result:
            print(f"  {row[0]:25} {row[1]:>10,}    ${row[2]:>10,.2f}")
    else:
        print("  (No data found)")

    conn.close()


async def example_incremental_update():
    """Example 8: Incremental update (export only new/updated records)."""
    print("\n=== Example 8: Incremental Update ===\n")

    client = LoyverseClient()

    # Export only receipts updated in the last 24 hours
    yesterday = datetime.now() - timedelta(days=1)

    print("Exporting receipts updated in last 24 hours...")
    counts = await client.export_to_duckdb(
        "loyverse.duckdb",
        resources=["receipts"],
        updated_at_min=yesterday
    )

    print(f"\n✓ Exported {counts['receipts']:,} updated receipts")
    print("Note: INSERT OR REPLACE will update existing records with same ID")

    await client.close()


async def main():
    """Run all examples."""
    print("=" * 60)
    print("  DuckDB Export Examples")
    print("=" * 60)

    # Check for API token
    if not os.getenv("LOYVERSE_API_TOKEN"):
        print("\nError: LOYVERSE_API_TOKEN environment variable not set")
        print("\nTo run these examples:")
        print("  1. Get your API token from https://r.loyverse.com/dashboard/settings/api")
        print("  2. Set environment variable: export LOYVERSE_API_TOKEN='your_token'")
        print("  3. Run: python examples/duckdb_export.py")
        return

    try:
        # Run examples sequentially
        await example_schema_initialization()
        await asyncio.sleep(1)

        await example_full_export()
        await asyncio.sleep(1)

        await example_selective_export()
        await asyncio.sleep(1)

        await example_date_range_export()
        await asyncio.sleep(1)

        await example_with_progress_callback()
        await asyncio.sleep(1)

        await example_single_resource()
        await asyncio.sleep(1)

        await example_query_exported_data()
        await asyncio.sleep(1)

        await example_incremental_update()

        print("\n" + "=" * 60)
        print("  All examples completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Open 'loyverse.duckdb' with DuckDB CLI or DBeaver")
        print("  - Run SQL queries to analyze your data")
        print("  - Build dashboards with tools like Metabase or Superset")
        print("  - Export to CSV: duckdb loyverse.duckdb \"COPY receipts TO 'receipts.csv'\"")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\nType: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
