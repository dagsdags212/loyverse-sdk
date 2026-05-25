"""
DuckDB connection management utilities.

Provides connection pooling, transaction management, and context managers
for working with DuckDB databases.
"""

from contextlib import contextmanager
from typing import Generator, Optional
import duckdb

from loyverse_sdk.exceptions import ExportError


class DuckDBConnection:
    """
    Manages DuckDB database connections with transaction support.

    Provides context managers for safe connection and transaction handling.

    Example:
        connection = DuckDBConnection("loyverse.duckdb")

        # Use connection
        conn = connection.connect()
        result = conn.execute("SELECT * FROM categories").fetchall()
        connection.close()

        # Use transaction context manager
        with connection.transaction() as conn:
            conn.execute("INSERT INTO categories ...")
    """

    def __init__(
        self,
        db_path: str,
        memory_limit: str = "4GB",
        threads: int = 4,
        read_only: bool = False,
    ):
        """
        Initialize DuckDB connection manager.

        Args:
            db_path: Path to DuckDB database file
            memory_limit: Maximum memory DuckDB can use (e.g., "4GB", "8GB")
            threads: Number of threads for parallel operations
            read_only: If True, opens database in read-only mode
        """
        self.db_path = db_path
        self.memory_limit = memory_limit
        self.threads = threads
        self.read_only = read_only
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Get or create a connection to the DuckDB database.

        Returns:
            Active DuckDB connection

        Example:
            conn = connection.connect()
            result = conn.execute("SELECT * FROM stores").fetchall()
        """
        if self._conn is None:
            config = {
                "memory_limit": self.memory_limit,
                "threads": self.threads,
            }

            self._conn = duckdb.connect(
                self.db_path,
                read_only=self.read_only,
                config=config,
            )

        return self._conn

    def close(self) -> None:
        """
        Close the active database connection.

        Example:
            connection.close()
        """
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def is_connected(self) -> bool:
        """Check if connection is active."""
        return self._conn is not None

    @contextmanager
    def transaction(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """
        Context manager for transaction management.

        Automatically begins a transaction, commits on success, and rolls back on error.

        Yields:
            DuckDB connection with active transaction

        Raises:
            Exception: Any exception that occurs during the transaction

        Example:
            with connection.transaction() as conn:
                conn.execute("INSERT INTO categories ...")
                conn.execute("INSERT INTO items ...")
                # Automatically commits if no exception
        """
        conn = self.connect()
        try:
            conn.begin()
            yield conn
            conn.commit()
        except (duckdb.Error, ExportError):
            conn.rollback()
            raise

    @contextmanager
    def cursor(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """
        Context manager for one-off queries.

        Automatically manages connection lifecycle for single operations.

        Yields:
            DuckDB connection

        Example:
            with connection.cursor() as conn:
                result = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()
                print(f"Total receipts: {result[0]}")
        """
        conn = self.connect()
        try:
            yield conn
        finally:
            # Don't close shared connection in cursor context
            pass

    def __enter__(self):
        """Support using DuckDBConnection as a context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure connection is closed when exiting context."""
        self.close()
        return False


def get_table_count(db_path: str, table_name: str) -> int:
    """
    Get the number of records in a table.

    Args:
        db_path: Path to DuckDB database
        table_name: Name of the table

    Returns:
        Number of records in the table

    Example:
        count = get_table_count("loyverse.duckdb", "receipts")
        print(f"Total receipts: {count}")
    """
    conn = duckdb.connect(db_path, read_only=True)
    try:
        result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
        return result[0] if result else 0
    finally:
        conn.close()


def get_all_tables(db_path: str) -> list[str]:
    """
    Get list of all tables in the database.

    Args:
        db_path: Path to DuckDB database

    Returns:
        List of table names

    Example:
        tables = get_all_tables("loyverse.duckdb")
        print(f"Tables: {', '.join(tables)}")
    """
    conn = duckdb.connect(db_path, read_only=True)
    try:
        result = conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]
    finally:
        conn.close()


def table_exists(db_path: str, table_name: str) -> bool:
    """
    Check if a table exists in the database.

    Args:
        db_path: Path to DuckDB database
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise

    Example:
        if table_exists("loyverse.duckdb", "receipts"):
            print("Receipts table exists")
    """
    tables = get_all_tables(db_path)
    return table_name in tables
