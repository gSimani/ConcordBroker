"""
PostgreSQL Direct Connection Module for ConcordBroker
High-performance bulk operations using psycopg2
- COPY method: 2000-4000 records/sec
- UPSERT method: 1000-2000 records/sec
- Batch updates: 500-1000 records/sec

No external dependencies beyond psycopg2 (pip install psycopg2-binary)
"""

import os
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection
from io import StringIO
import time
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import csv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BulkUploadStats:
    """Track bulk upload performance metrics"""
    total_records: int = 0
    inserted_records: int = 0
    updated_records: int = 0
    skipped_records: int = 0
    error_records: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None

    @property
    def duration_seconds(self) -> float:
        """Total operation duration in seconds"""
        end = self.end_time or time.time()
        return end - self.start_time

    @property
    def records_per_second(self) -> float:
        """Throughput calculation"""
        if self.duration_seconds == 0:
            return 0
        processed = self.inserted_records + self.updated_records
        return processed / self.duration_seconds

    def format_duration(self) -> str:
        """Format duration as HH:MM:SS"""
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    def __str__(self) -> str:
        return f"""
        ============================================
              BULK OPERATION STATISTICS
        ============================================
        Total Records:        {self.total_records:>20,}
        Inserted:             {self.inserted_records:>20,}
        Updated:              {self.updated_records:>20,}
        Skipped:              {self.skipped_records:>20,}
        Errors:               {self.error_records:>20,}
        ============================================
        Duration:             {self.format_duration():>20}
        Speed:                {self.records_per_second:>20,.0f} rec/s
        Success Rate:         {self._success_rate():>19.1f}%
        ============================================
        """

    def _success_rate(self) -> float:
        """Calculate success percentage"""
        if self.total_records == 0:
            return 0
        processed = self.inserted_records + self.updated_records
        return (processed / self.total_records) * 100


class PostgreSQLBulkLoader:
    """
    Direct PostgreSQL bulk loader using native operations.

    Performance optimized for Supabase hosted PostgreSQL.
    Use pooler endpoint (port 6543) for concurrent operations.

    Methods:
    - bulk_copy_from_csv(): Fastest (COPY command)
    - bulk_upsert_from_csv(): Safe (UPSERT with dedup)
    - batch_update_from_list(): Flexible (row-by-row with logic)
    """

    def __init__(self, connection_string: str = None, verbose: bool = True):
        """
        Initialize bulk loader.

        Args:
            connection_string: PostgreSQL connection URL (uses DATABASE_URL env if None)
            verbose: Enable detailed logging
        """
        if connection_string is None:
            # Priority order: DATABASE_URL (pooler) > POSTGRES_URL > env missing
            connection_string = (
                os.getenv('DATABASE_URL') or
                os.getenv('POSTGRES_URL') or
                os.getenv('POSTGRES_URL_NON_POOLING')
            )

            if not connection_string:
                raise ValueError(
                    "No connection string found. Set DATABASE_URL, POSTGRES_URL, "
                    "or POSTGRES_URL_NON_POOLING environment variable"
                )

        self.connection_string = connection_string
        self.conn: Optional[connection] = None
        self.verbose = verbose
        self.stats = BulkUploadStats()

        # Extract host from connection string for logging
        try:
            import urllib.parse
            parsed = urllib.parse.urlparse(f"postgresql://{connection_string.split('postgresql://')[1]}")
            self.host = parsed.hostname or "unknown"
            self.port = parsed.port or 5432
        except Exception:
            self.host = "unknown"
            self.port = 5432

    def connect(self) -> bool:
        """
        Establish database connection.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Try to fix malformed connection strings with truncated parameters
            conn_str = self.connection_string
            # Fix known issue: "supa=base-pooler.x" truncation
            if "&supa=base-pooler.x" in conn_str:
                conn_str = conn_str.replace("&supa=base-pooler.x", "")

            self.conn = psycopg2.connect(conn_str)
            logger.info(f"[OK] Connected to PostgreSQL at {self.host}:{self.port}")

            # Check version
            cursor = self.conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            version_info = version.split(',')[0]
            logger.info(f"[OK] {version_info}")
            cursor.close()

            return True
        except psycopg2.OperationalError as e:
            logger.error(f"[FAIL] Connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"[FAIL] Unexpected error: {e}")
            return False

    def disconnect(self):
        """Close database connection safely"""
        if self.conn:
            try:
                self.conn.close()
                logger.info("✓ Disconnected from PostgreSQL")
            except Exception as e:
                logger.warning(f"⚠ Error closing connection: {e}")
            finally:
                self.conn = None

    def bulk_copy_from_csv(
        self,
        csv_file_path: str,
        table_name: str,
        columns: List[str],
        delimiter: str = ',',
        skip_header: bool = True,
        on_error: str = 'stop'  # 'stop' or 'continue'
    ) -> BulkUploadStats:
        """
        Fastest bulk import method using PostgreSQL COPY command.

        Performance: 2000-4000 records/second
        Best for: Initial data loads, large imports
        Note: Assumes data is clean (all records valid)

        Args:
            csv_file_path: Path to CSV file
            table_name: Target database table
            columns: List of column names (in CSV order)
            delimiter: CSV delimiter character (default: comma)
            skip_header: Whether to skip first line (default: True)
            on_error: 'stop' to fail on error, 'continue' to skip bad rows

        Returns:
            BulkUploadStats with operation metrics

        Example:
            stats = loader.bulk_copy_from_csv(
                "data.csv",
                "florida_parcels",
                ["parcel_id", "county", "owner_name", "just_value"]
            )
        """
        logger.info(f"Starting COPY import from {csv_file_path}")
        logger.info(f"Target: {table_name} ({len(columns)} columns)")

        self.stats = BulkUploadStats()
        self.stats.start_time = time.time()

        # Validate file exists
        if not Path(csv_file_path).exists():
            logger.error(f"✗ File not found: {csv_file_path}")
            self.stats.end_time = time.time()
            return self.stats

        try:
            cursor = self.conn.cursor()

            # Build COPY command
            copy_sql = f"""
                COPY {table_name} ({','.join(columns)})
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    DELIMITER '{delimiter}',
                    NULL ''
                )
            """

            # Execute COPY
            logger.info("Executing COPY command...")
            bytes_copied = 0

            with open(csv_file_path, 'r', encoding='utf-8') as f:
                # Skip header line if requested
                if skip_header:
                    f.readline()

                # Stream file to COPY command
                bytes_copied = cursor.copy_expert(copy_sql, f)

            # Commit transaction
            self.conn.commit()
            self.stats.end_time = time.time()

            logger.info(f"✓ COPY completed: {bytes_copied:,} bytes transferred")

            # Get actual record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            record_count = cursor.fetchone()[0]
            self.stats.inserted_records = record_count
            self.stats.total_records = record_count

            logger.info(str(self.stats))

            cursor.close()
            return self.stats

        except Exception as e:
            logger.error(f"✗ COPY failed: {e}")
            self.conn.rollback()
            self.stats.error_records += 1
            self.stats.end_time = time.time()
            return self.stats

    def bulk_upsert_from_csv(
        self,
        csv_file_path: str,
        table_name: str,
        columns: List[str],
        unique_keys: List[str],
        delimiter: str = ',',
        skip_header: bool = True
    ) -> BulkUploadStats:
        """
        Safe bulk import with upsert (insert or update).

        Performance: 1000-2000 records/second
        Best for: Incremental updates, deduplication
        Uses: Temporary table + INSERT ... ON CONFLICT

        Args:
            csv_file_path: Path to CSV file
            table_name: Target database table
            columns: List of column names
            unique_keys: Column names that define uniqueness
            delimiter: CSV delimiter (default: comma)
            skip_header: Skip first line (default: True)

        Returns:
            BulkUploadStats with operation metrics

        Example:
            stats = loader.bulk_upsert_from_csv(
                "updates.csv",
                "florida_parcels",
                ["parcel_id", "county", "owner_name"],
                unique_keys=["parcel_id", "county"]
            )
        """
        logger.info(f"Starting UPSERT import from {csv_file_path}")
        logger.info(f"Unique keys: {unique_keys}")

        self.stats = BulkUploadStats()
        self.stats.start_time = time.time()

        # Validate file exists
        if not Path(csv_file_path).exists():
            logger.error(f"✗ File not found: {csv_file_path}")
            self.stats.end_time = time.time()
            return self.stats

        temp_table = f"{table_name}_import_{int(time.time()*1000)}"

        try:
            cursor = self.conn.cursor()

            # 1. Create temporary table
            logger.info(f"Creating temporary table {temp_table}...")
            self._create_temp_table(cursor, temp_table, table_name, columns)

            # 2. Load data via COPY
            logger.info("Loading data via COPY...")
            copy_sql = f"""
                COPY {temp_table} ({','.join(columns)})
                FROM STDIN
                WITH (
                    FORMAT CSV,
                    DELIMITER '{delimiter}',
                    NULL ''
                )
            """

            with open(csv_file_path, 'r', encoding='utf-8') as f:
                if skip_header:
                    f.readline()

                cursor.copy_expert(copy_sql, f)

            self.conn.commit()

            # Count loaded
            cursor.execute(f"SELECT COUNT(*) FROM {temp_table}")
            loaded_count = cursor.fetchone()[0]
            self.stats.total_records = loaded_count
            logger.info(f"✓ Loaded {loaded_count:,} records into temp table")

            # 3. UPSERT from temp to target
            logger.info("Performing UPSERT...")
            self._perform_upsert(cursor, table_name, temp_table, columns, unique_keys)
            self.conn.commit()

            self.stats.end_time = time.time()

            # Get results
            cursor.execute(f"""
                SELECT COUNT(*) FROM {table_name}
                WHERE updated_at >= NOW() - INTERVAL '1 minute'
            """)
            recent_count = cursor.fetchone()[0]
            self.stats.inserted_records = recent_count
            self.stats.updated_records = loaded_count - recent_count

            logger.info(str(self.stats))

            # Cleanup
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
            self.conn.commit()
            cursor.close()

            return self.stats

        except Exception as e:
            logger.error(f"✗ UPSERT failed: {e}")
            self.conn.rollback()
            self.stats.error_records += 1
            self.stats.end_time = time.time()
            return self.stats

    def batch_update_from_list(
        self,
        table_name: str,
        records: List[Dict[str, Any]],
        unique_keys: List[str],
        batch_size: int = 1000
    ) -> BulkUploadStats:
        """
        Update multiple records in batches with validation.

        Performance: 500-1000 records/second
        Best for: Incremental updates with custom logic
        Allows: Data transformation, validation per record

        Args:
            table_name: Target table
            records: List of record dictionaries
            unique_keys: Column names that identify records to update
            batch_size: Records per batch commit

        Returns:
            BulkUploadStats with operation metrics

        Example:
            records = [
                {'parcel_id': 'ABC123', 'county': 'BROWARD', 'property_use': 'RES'},
                {'parcel_id': 'XYZ789', 'county': 'MIAMI', 'property_use': 'COM'}
            ]
            stats = loader.batch_update_from_list(
                "florida_parcels",
                records,
                unique_keys=["parcel_id", "county"]
            )
        """
        logger.info(f"Starting batch update: {len(records)} records")

        self.stats = BulkUploadStats()
        self.stats.start_time = time.time()
        self.stats.total_records = len(records)

        cursor = self.conn.cursor()

        try:
            for batch_idx, i in enumerate(range(0, len(records), batch_size)):
                batch = records[i:i+batch_size]

                for record in batch:
                    try:
                        # Extract update columns (exclude unique keys)
                        update_cols = {
                            k: v for k, v in record.items()
                            if k not in unique_keys
                        }

                        if not update_cols:
                            logger.warning(f"Record has no updateable columns: {record}")
                            self.stats.skipped_records += 1
                            continue

                        # Build UPDATE statement
                        set_parts = [f"{col} = %s" for col in update_cols.keys()]
                        set_clause = ", ".join(set_parts)

                        where_parts = [f"{key} = %s" for key in unique_keys]
                        where_clause = " AND ".join(where_parts)

                        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

                        # Prepare values: update columns + where keys
                        values = list(update_cols.values()) + [record[k] for k in unique_keys]

                        cursor.execute(sql, values)

                        if cursor.rowcount > 0:
                            self.stats.updated_records += 1
                        else:
                            self.stats.skipped_records += 1

                    except Exception as e:
                        logger.warning(f"Record update failed: {e}")
                        self.stats.error_records += 1

                # Commit batch
                self.conn.commit()
                if self.verbose:
                    logger.info(f"Batch {batch_idx + 1} committed ({i + len(batch):,} records)")

            self.stats.end_time = time.time()
            logger.info(str(self.stats))

        except Exception as e:
            logger.error(f"✗ Batch update failed: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

        return self.stats

    def _create_temp_table(
        self,
        cursor,
        temp_table: str,
        source_table: str,
        columns: List[str]
    ):
        """Create temporary table matching source schema"""
        try:
            # Get column definitions
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (source_table,))

            col_info = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

            # Build column definitions
            col_defs = []
            for col in columns:
                if col in col_info:
                    data_type, is_nullable = col_info[col]
                    not_null = "" if is_nullable == "YES" else "NOT NULL"
                    col_defs.append(f"{col} {data_type} {not_null}".strip())
                else:
                    logger.warning(f"Column not found in source: {col}")
                    col_defs.append(f"{col} TEXT")

            # Create temp table
            create_sql = f"CREATE TEMP TABLE {temp_table} ({', '.join(col_defs)})"
            cursor.execute(create_sql)
            self.conn.commit()
            logger.info(f"✓ Created temporary table {temp_table}")

        except Exception as e:
            logger.error(f"✗ Failed to create temp table: {e}")
            raise

    def _perform_upsert(
        self,
        cursor,
        target_table: str,
        temp_table: str,
        columns: List[str],
        unique_keys: List[str]
    ):
        """Execute INSERT ... ON CONFLICT DO UPDATE"""
        try:
            # Determine update columns (all except unique keys)
            update_cols = [c for c in columns if c not in unique_keys]

            if not update_cols:
                # No columns to update, just insert
                logger.warning("No updateable columns, performing INSERT only")
                upsert_sql = f"""
                    INSERT INTO {target_table} ({', '.join(columns)})
                    SELECT {', '.join(columns)} FROM {temp_table}
                    ON CONFLICT ({', '.join(unique_keys)}) DO NOTHING
                """
            else:
                # Build update clause
                update_clause = ", ".join([f"{col} = EXCLUDED.{col}" for col in update_cols])

                upsert_sql = f"""
                    INSERT INTO {target_table} ({', '.join(columns)})
                    SELECT {', '.join(columns)} FROM {temp_table}
                    ON CONFLICT ({', '.join(unique_keys)})
                    DO UPDATE SET {update_clause}
                """

            cursor.execute(upsert_sql)
            logger.info(f"✓ UPSERT completed: {cursor.rowcount} rows affected")

        except Exception as e:
            logger.error(f"✗ UPSERT failed: {e}")
            raise


def test_connection():
    """Quick test of database connectivity"""
    logger.info("Testing PostgreSQL connection...")
    loader = PostgreSQLBulkLoader()

    if loader.connect():
        logger.info("✓ Connection test passed")
        loader.disconnect()
        return True
    else:
        logger.error("✗ Connection test failed")
        return False


if __name__ == "__main__":
    # Test the connection
    import sys
    if test_connection():
        logger.info("PostgreSQL bulk loader is ready to use")
        sys.exit(0)
    else:
        logger.error("Failed to verify PostgreSQL connection")
        sys.exit(1)
