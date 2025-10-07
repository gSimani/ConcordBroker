"""
Supabase Batch Uploader
High-performance batch uploader for Florida sales data with comprehensive
conflict resolution, error handling, and progress tracking.
"""

import os
import json
import time
import logging
import psycopg2
import psycopg2.extras
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from contextlib import contextmanager
from io import StringIO
import csv

from supabase import create_client, Client
import pandas as pd


@dataclass
class UploadStats:
    """Track upload statistics"""
    county: str
    total_records: int = 0
    successful_inserts: int = 0
    successful_updates: int = 0
    duplicates_skipped: int = 0
    errors: int = 0
    upload_time: float = 0.0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    error_details: List[Dict] = None

    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []


class SupabaseBatchUploader:
    """
    High-performance batch uploader for Supabase with advanced conflict resolution
    """

    def __init__(self,
                 supabase_url: str = None,
                 supabase_key: str = None,
                 postgres_url: str = None,
                 batch_size: int = 1000,
                 max_workers: int = 4):
        """
        Initialize the Supabase uploader

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase service role key
            postgres_url: Direct PostgreSQL connection URL
            batch_size: Records per batch
            max_workers: Concurrent upload threads
        """
        # Load credentials from environment or use provided
        self.supabase_url = supabase_url or self._get_env_var('SUPABASE_URL')
        self.supabase_key = supabase_key or self._get_env_var('SUPABASE_SERVICE_ROLE_KEY')
        self.postgres_url = postgres_url or self._get_env_var('POSTGRES_URL')

        self.batch_size = batch_size
        self.max_workers = max_workers

        # Initialize clients
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Setup logging
        self.setup_logging()

        # Upload tracking
        self.upload_stats: Dict[str, UploadStats] = {}
        self.upload_queue = Queue()
        self.error_queue = Queue()

        # Thread safety
        self.stats_lock = threading.Lock()

        # Performance optimization settings
        self.connection_pool_size = max_workers * 2
        self.enable_direct_postgres = True

    def _get_env_var(self, var_name: str) -> str:
        """Get environment variable with error handling"""
        value = os.getenv(var_name)
        if not value:
            raise ValueError(f"Environment variable {var_name} not found")
        return value

    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("C:/Users/gsima/Documents/MyProject/ConcordBroker/TEMP/UPLOAD_LOGS")
        log_dir.mkdir(parents=True, exist_ok=True)

        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] - %(message)s'
        )

        file_handler = logging.FileHandler(
            log_dir / f'supabase_uploader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        )
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger = logging.getLogger('SupabaseUploader')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    @contextmanager
    def get_postgres_connection(self):
        """Get direct PostgreSQL connection with proper resource management"""
        conn = None
        try:
            conn = psycopg2.connect(
                self.postgres_url,
                connect_timeout=30,
                application_name='SDF_Uploader'
            )
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"PostgreSQL connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def create_upsert_sql(self, table_name: str = 'property_sales_history') -> str:
        """
        Create optimized UPSERT SQL for sales data

        Args:
            table_name: Target table name

        Returns:
            SQL statement for batch upsert
        """
        return f"""
        INSERT INTO {table_name} (
            parcel_id, county, sale_date, sale_year, sale_month, sale_day,
            sale_price, grantor, grantee, instrument_type, instrument_number,
            or_book, or_page, clerk_no, sale_qualification, quality_code,
            vi_code, reason, vacant_improved, property_use, qualified_sale,
            arms_length, multi_parcel, foreclosure, rea_sale, short_sale,
            distressed_sale, data_source, import_date
        ) VALUES %s
        ON CONFLICT (parcel_id, sale_date, sale_price, or_book, or_page)
        DO UPDATE SET
            county = EXCLUDED.county,
            sale_year = EXCLUDED.sale_year,
            sale_month = EXCLUDED.sale_month,
            sale_day = EXCLUDED.sale_day,
            grantor = EXCLUDED.grantor,
            grantee = EXCLUDED.grantee,
            instrument_type = EXCLUDED.instrument_type,
            instrument_number = EXCLUDED.instrument_number,
            clerk_no = EXCLUDED.clerk_no,
            sale_qualification = EXCLUDED.sale_qualification,
            quality_code = EXCLUDED.quality_code,
            vi_code = EXCLUDED.vi_code,
            reason = EXCLUDED.reason,
            vacant_improved = EXCLUDED.vacant_improved,
            property_use = EXCLUDED.property_use,
            qualified_sale = EXCLUDED.qualified_sale,
            arms_length = EXCLUDED.arms_length,
            multi_parcel = EXCLUDED.multi_parcel,
            foreclosure = EXCLUDED.foreclosure,
            rea_sale = EXCLUDED.rea_sale,
            short_sale = EXCLUDED.short_sale,
            distressed_sale = EXCLUDED.distressed_sale,
            data_source = EXCLUDED.data_source,
            import_date = EXCLUDED.import_date,
            updated_at = NOW()
        WHERE
            property_sales_history.parcel_id = EXCLUDED.parcel_id
            AND property_sales_history.sale_date = EXCLUDED.sale_date
            AND property_sales_history.sale_price = EXCLUDED.sale_price
            AND property_sales_history.or_book = EXCLUDED.or_book
            AND property_sales_history.or_page = EXCLUDED.or_page
        """

    def prepare_record_tuple(self, record: Dict) -> Tuple:
        """
        Convert record dictionary to tuple for PostgreSQL insert

        Args:
            record: Record dictionary

        Returns:
            Tuple of values in correct order
        """
        return (
            record.get('parcel_id', ''),
            record.get('county', ''),
            record.get('sale_date'),
            record.get('sale_year', 0),
            record.get('sale_month', 0),
            record.get('sale_day', 1),
            record.get('sale_price', 0.0),
            record.get('grantor', ''),
            record.get('grantee', ''),
            record.get('instrument_type', ''),
            record.get('instrument_number', ''),
            record.get('or_book', ''),
            record.get('or_page', ''),
            record.get('clerk_no', ''),
            record.get('sale_qualification', ''),
            record.get('quality_code', ''),
            record.get('vi_code', ''),
            record.get('reason', ''),
            record.get('vacant_improved', ''),
            record.get('property_use', ''),
            record.get('qualified_sale', False),
            record.get('arms_length', False),
            record.get('multi_parcel', False),
            record.get('foreclosure', False),
            record.get('rea_sale', False),
            record.get('short_sale', False),
            record.get('distressed_sale', False),
            record.get('data_source', 'SDF'),
            record.get('import_date', datetime.now().isoformat())
        )

    def upload_batch_postgres(self, records: List[Dict], county: str) -> Tuple[int, int, List[str]]:
        """
        Upload batch using direct PostgreSQL connection

        Args:
            records: List of records to upload
            county: County name for logging

        Returns:
            Tuple of (successful_inserts, conflicts_resolved, errors)
        """
        if not records:
            return 0, 0, []

        errors = []
        successful_inserts = 0
        conflicts_resolved = 0

        try:
            with self.get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    # Prepare data tuples
                    data_tuples = [self.prepare_record_tuple(record) for record in records]

                    # Execute batch upsert
                    upsert_sql = self.create_upsert_sql()

                    start_time = time.time()

                    # Use execute_values for high performance
                    psycopg2.extras.execute_values(
                        cursor,
                        upsert_sql,
                        data_tuples,
                        template=None,
                        page_size=self.batch_size
                    )

                    # Get affected rows count
                    rows_affected = cursor.rowcount

                    # Commit transaction
                    conn.commit()

                    upload_time = time.time() - start_time

                    # Estimate inserts vs updates (approximate)
                    successful_inserts = min(rows_affected, len(records))

                    self.logger.info(
                        f"{county}: Uploaded {len(records)} records in {upload_time:.2f}s "
                        f"({len(records)/upload_time:.0f} records/sec)"
                    )

        except psycopg2.IntegrityError as e:
            # Handle constraint violations
            conn.rollback()
            error_msg = f"Integrity error: {str(e)}"
            errors.append(error_msg)
            self.logger.warning(f"{county}: {error_msg}")

        except psycopg2.DatabaseError as e:
            # Handle database errors
            conn.rollback()
            error_msg = f"Database error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"{county}: {error_msg}")

        except Exception as e:
            # Handle other errors
            error_msg = f"Unexpected error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"{county}: {error_msg}")
            self.logger.debug(traceback.format_exc())

        return successful_inserts, conflicts_resolved, errors

    def upload_batch_supabase(self, records: List[Dict], county: str) -> Tuple[int, int, List[str]]:
        """
        Upload batch using Supabase client (fallback method)

        Args:
            records: List of records to upload
            county: County name for logging

        Returns:
            Tuple of (successful_inserts, conflicts_resolved, errors)
        """
        if not records:
            return 0, 0, []

        errors = []
        successful_inserts = 0
        conflicts_resolved = 0

        try:
            start_time = time.time()

            # Use Supabase upsert
            response = self.supabase.table('property_sales_history').upsert(
                records,
                on_conflict='parcel_id,sale_date,sale_price,or_book,or_page'
            ).execute()

            upload_time = time.time() - start_time

            if response.data:
                successful_inserts = len(response.data)

            self.logger.info(
                f"{county}: Uploaded {len(records)} records via Supabase in {upload_time:.2f}s"
            )

        except Exception as e:
            error_msg = f"Supabase error: {str(e)}"
            errors.append(error_msg)
            self.logger.error(f"{county}: {error_msg}")

        return successful_inserts, conflicts_resolved, errors

    def upload_batch(self, records: List[Dict], county: str, retry_count: int = 3) -> Dict:
        """
        Upload batch with retry logic and fallback methods

        Args:
            records: List of records to upload
            county: County name
            retry_count: Number of retry attempts

        Returns:
            Upload results dictionary
        """
        result = {
            'successful_inserts': 0,
            'conflicts_resolved': 0,
            'errors': 0,
            'error_messages': []
        }

        for attempt in range(retry_count):
            try:
                if self.enable_direct_postgres:
                    # Try PostgreSQL first (faster)
                    inserts, conflicts, error_msgs = self.upload_batch_postgres(records, county)
                else:
                    # Fallback to Supabase client
                    inserts, conflicts, error_msgs = self.upload_batch_supabase(records, county)

                result['successful_inserts'] = inserts
                result['conflicts_resolved'] = conflicts
                result['error_messages'].extend(error_msgs)
                result['errors'] = len(error_msgs)

                if result['errors'] == 0:
                    # Success, no retry needed
                    break

            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                result['error_messages'].append(error_msg)
                self.logger.warning(f"{county}: {error_msg}")

                if attempt < retry_count - 1:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    self.logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)

                    # Switch to fallback method on failure
                    if self.enable_direct_postgres:
                        self.logger.info("Switching to Supabase client fallback")
                        self.enable_direct_postgres = False

        result['errors'] = len(result['error_messages'])
        return result

    def upload_county_data(self, county: str, data_source: Any) -> UploadStats:
        """
        Upload all data for a county

        Args:
            county: County name
            data_source: Data source (file path, list of records, or generator)

        Returns:
            Upload statistics
        """
        # Initialize stats
        with self.stats_lock:
            self.upload_stats[county] = UploadStats(
                county=county,
                start_time=datetime.now().isoformat()
            )
            stats = self.upload_stats[county]

        self.logger.info(f"Starting upload for {county}")

        try:
            # Handle different data source types
            if isinstance(data_source, (str, Path)):
                # File path
                records = self._load_records_from_file(data_source)
            elif hasattr(data_source, '__iter__'):
                # Iterable (list or generator)
                records = data_source
            else:
                raise ValueError(f"Unsupported data source type: {type(data_source)}")

            # Process records in batches
            batch = []
            batch_count = 0

            for record in records:
                batch.append(record)
                stats.total_records += 1

                if len(batch) >= self.batch_size:
                    # Upload batch
                    result = self.upload_batch(batch, county)

                    # Update statistics
                    with self.stats_lock:
                        stats.successful_inserts += result['successful_inserts']
                        stats.successful_updates += result['conflicts_resolved']
                        stats.errors += result['errors']
                        stats.error_details.extend([
                            {'batch': batch_count, 'error': msg}
                            for msg in result['error_messages']
                        ])

                    batch = []
                    batch_count += 1

                    # Log progress
                    if batch_count % 10 == 0:
                        self.logger.info(
                            f"{county} progress: {stats.total_records:,} records processed, "
                            f"{stats.successful_inserts:,} uploaded"
                        )

            # Upload final batch
            if batch:
                result = self.upload_batch(batch, county)

                with self.stats_lock:
                    stats.successful_inserts += result['successful_inserts']
                    stats.successful_updates += result['conflicts_resolved']
                    stats.errors += result['errors']
                    stats.error_details.extend([
                        {'batch': batch_count, 'error': msg}
                        for msg in result['error_messages']
                    ])

        except Exception as e:
            with self.stats_lock:
                stats.error_details.append({'general_error': str(e)})
            self.logger.error(f"Error uploading {county}: {e}")
            self.logger.debug(traceback.format_exc())

        # Finalize statistics
        with self.stats_lock:
            stats.end_time = datetime.now().isoformat()
            start_dt = datetime.fromisoformat(stats.start_time)
            end_dt = datetime.fromisoformat(stats.end_time)
            stats.upload_time = (end_dt - start_dt).total_seconds()

        self.logger.info(
            f"Completed {county}: {stats.successful_inserts:,}/{stats.total_records:,} "
            f"uploaded in {stats.upload_time:.1f}s"
        )

        return stats

    def _load_records_from_file(self, file_path: Path) -> List[Dict]:
        """Load records from JSON file"""
        with open(file_path, 'r') as f:
            return json.load(f)

    def upload_multiple_counties(self, counties_data: Dict[str, Any]) -> Dict:
        """
        Upload data for multiple counties concurrently

        Args:
            counties_data: Dictionary mapping county names to data sources

        Returns:
            Summary statistics
        """
        self.logger.info(f"Starting upload for {len(counties_data)} counties")

        start_time = datetime.now()

        # Use ThreadPoolExecutor for concurrent uploads
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit upload tasks
            future_to_county = {
                executor.submit(self.upload_county_data, county, data_source): county
                for county, data_source in counties_data.items()
            }

            # Wait for completion
            for future in as_completed(future_to_county):
                county = future_to_county[future]
                try:
                    stats = future.result()
                    self.logger.info(f"Upload completed for {county}")
                except Exception as e:
                    self.logger.error(f"Upload failed for {county}: {e}")

        # Calculate summary
        end_time = datetime.now()
        total_records = sum(s.total_records for s in self.upload_stats.values())
        total_uploaded = sum(s.successful_inserts for s in self.upload_stats.values())
        total_errors = sum(s.errors for s in self.upload_stats.values())

        summary = {
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': (end_time - start_time).total_seconds() / 3600,
            'counties_processed': len(counties_data),
            'total_records': total_records,
            'total_uploaded': total_uploaded,
            'total_errors': total_errors,
            'upload_rate_per_hour': total_uploaded / max((end_time - start_time).total_seconds() / 3600, 0.001),
            'success_rate': total_uploaded / total_records if total_records > 0 else 0,
            'county_details': {
                county: asdict(stats) for county, stats in self.upload_stats.items()
            }
        }

        self.logger.info("Upload Summary:")
        self.logger.info(f"  Total Records: {total_records:,}")
        self.logger.info(f"  Uploaded: {total_uploaded:,}")
        self.logger.info(f"  Errors: {total_errors:,}")
        self.logger.info(f"  Success Rate: {summary['success_rate']*100:.1f}%")
        self.logger.info(f"  Duration: {summary['duration_hours']:.2f} hours")

        return summary

    def get_upload_status(self) -> Dict:
        """Get current upload status"""
        with self.stats_lock:
            return {
                'counties_processed': len(self.upload_stats),
                'total_records': sum(s.total_records for s in self.upload_stats.values()),
                'total_uploaded': sum(s.successful_inserts for s in self.upload_stats.values()),
                'total_errors': sum(s.errors for s in self.upload_stats.values()),
                'details': {county: asdict(stats) for county, stats in self.upload_stats.items()}
            }


if __name__ == "__main__":
    # Example usage
    uploader = SupabaseBatchUploader()

    # Test with sample data
    sample_records = [
        {
            'parcel_id': 'TEST001',
            'county': 'LAFAYETTE',
            'sale_date': '2024-01-15',
            'sale_year': 2024,
            'sale_month': 1,
            'sale_day': 15,
            'sale_price': 150000.0,
            'qualified_sale': True,
            'arms_length': True,
            'data_source': 'SDF'
        }
    ]

    print("Testing uploader with sample data...")
    stats = uploader.upload_county_data('TEST', sample_records)
    print(f"Upload completed: {stats.successful_inserts} records uploaded")