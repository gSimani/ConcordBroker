#!/usr/bin/env python3
"""
Florida Database Update Agent
Updates Supabase database with Florida property data using UPSERT operations.
Maintains data integrity and relationships while handling large datasets efficiently.
"""

import asyncio
import asyncpg
import logging
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import csv
from decimal import Decimal
import sqlite3

# Add parent directory to path to import supabase config
sys.path.append(str(Path(__file__).parent.parent.parent / 'apps' / 'workers'))
from supabase_config import SupabaseConfig, SupabaseUpdateMonitor

logger = logging.getLogger(__name__)

@dataclass
class UpdateResult:
    """Result of database update operation"""
    file_path: str
    file_type: str
    county: str
    total_records: int
    inserted_records: int
    updated_records: int
    skipped_records: int
    error_records: int
    update_time: float
    success: bool
    error: Optional[str] = None
    table_name: Optional[str] = None

@dataclass
class TableMapping:
    """Database table mapping configuration"""
    table_name: str
    primary_key: List[str]
    columns: Dict[str, str]  # field_name -> column_name
    indexes: List[str]
    constraints: List[str]

class FloridaDatabaseUpdater:
    """Updates Supabase database with Florida property data"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.batch_size = config.get('batch_size', 5000)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 30)
        self.create_tables = config.get('create_tables', True)
        self.create_indexes = config.get('create_indexes', True)
        self.enable_rls = config.get('enable_row_level_security', False)
        
        # Database configuration
        self.supabase_config = SupabaseConfig()
        self.pool = None
        self.update_monitor = None
        
        # State database
        self.db_path = Path(config.get('state_db_path', 'florida_database_updater_state.db'))
        
        # Table mappings
        self.table_mappings = self._get_table_mappings()
        
        # Initialize state database
        self._init_database()
        
        # Statistics
        self.update_stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'records_inserted': 0,
            'records_updated': 0,
            'total_time': 0.0
        }
    
    def _init_database(self):
        """Initialize SQLite database for update state"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS update_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    county TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    total_records INTEGER,
                    inserted_records INTEGER,
                    updated_records INTEGER,
                    skipped_records INTEGER,
                    error_records INTEGER,
                    update_time REAL,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN,
                    error TEXT,
                    metadata TEXT
                )
            ''')
            
            conn.commit()
    
    def _get_table_mappings(self) -> Dict[str, TableMapping]:
        """Get table mappings for different file types"""
        return {
            'NAL': TableMapping(
                table_name='florida_nal_property_details',
                primary_key=['county_code', 'parcel_id'],
                columns={
                    'county_code': 'county_code',
                    'parcel_id': 'parcel_id',
                    'parcel_number': 'parcel_number',
                    'owner_name': 'owner_name',
                    'owner_address_1': 'owner_address_1',
                    'owner_address_2': 'owner_address_2',
                    'owner_city': 'owner_city',
                    'owner_state': 'owner_state',
                    'owner_zip': 'owner_zip',
                    'property_address': 'property_address',
                    'property_city': 'property_city',
                    'property_zip': 'property_zip',
                    'legal_description': 'legal_description',
                    'property_use_code': 'property_use_code',
                    'land_value': 'land_value',
                    'just_value': 'just_value',
                    'assessed_value': 'assessed_value',
                    'source_file': 'source_file',
                    'processed_at': 'processed_at'
                },
                indexes=[
                    'idx_nal_county_parcel ON florida_nal_property_details(county_code, parcel_id)',
                    'idx_nal_owner_name ON florida_nal_property_details(owner_name)',
                    'idx_nal_property_address ON florida_nal_property_details(property_address)',
                    'idx_nal_property_use ON florida_nal_property_details(property_use_code)'
                ],
                constraints=[]
            ),
            'NAP': TableMapping(
                table_name='florida_nap_assessments',
                primary_key=['county_code', 'parcel_id', 'tax_year'],
                columns={
                    'county_code': 'county_code',
                    'parcel_id': 'parcel_id',
                    'parcel_number': 'parcel_number',
                    'land_value': 'land_value',
                    'just_value': 'just_value',
                    'assessed_value': 'assessed_value',
                    'exempt_value': 'exempt_value',
                    'taxable_value': 'taxable_value',
                    'tax_year': 'tax_year',
                    'millage_rate': 'millage_rate',
                    'source_file': 'source_file',
                    'processed_at': 'processed_at'
                },
                indexes=[
                    'idx_nap_county_parcel_year ON florida_nap_assessments(county_code, parcel_id, tax_year)',
                    'idx_nap_tax_year ON florida_nap_assessments(tax_year)',
                    'idx_nap_just_value ON florida_nap_assessments(just_value)'
                ],
                constraints=[]
            ),
            'SDF': TableMapping(
                table_name='florida_sdf_sales',
                primary_key=['county_code', 'parcel_id', 'sale_date', 'deed_book', 'deed_page'],
                columns={
                    'county_code': 'county_code',
                    'parcel_id': 'parcel_id',
                    'parcel_number': 'parcel_number',
                    'sale_date': 'sale_date',
                    'sale_price': 'sale_price',
                    'deed_book': 'deed_book',
                    'deed_page': 'deed_page',
                    'grantor': 'grantor',
                    'grantee': 'grantee',
                    'deed_type': 'deed_type',
                    'qualification_code': 'qualification_code',
                    'source_file': 'source_file',
                    'processed_at': 'processed_at'
                },
                indexes=[
                    'idx_sdf_county_parcel ON florida_sdf_sales(county_code, parcel_id)',
                    'idx_sdf_sale_date ON florida_sdf_sales(sale_date)',
                    'idx_sdf_sale_price ON florida_sdf_sales(sale_price)',
                    'idx_sdf_deed_ref ON florida_sdf_sales(deed_book, deed_page)'
                ],
                constraints=[]
            )
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.pool = await self.supabase_config.get_db_pool()
        self.update_monitor = SupabaseUpdateMonitor(self.pool)
        await self.update_monitor.initialize_tracking_tables()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.pool:
            await self.pool.close()
    
    async def update_from_file(self, file_path: str, file_type: str, county: str) -> UpdateResult:
        """Update database from processed CSV file"""
        start_time = datetime.now()
        file_path_obj = Path(file_path)
        
        try:
            logger.info(f"Starting database update from {file_type} file: {file_path}")
            
            if not file_path_obj.exists():
                raise Exception(f"File not found: {file_path}")
            
            # Get table mapping
            if file_type not in self.table_mappings:
                raise Exception(f"No table mapping for file type: {file_type}")
            
            table_mapping = self.table_mappings[file_type]
            
            # Ensure table exists
            if self.create_tables:
                await self._ensure_table_exists(table_mapping)
            
            # Create indexes if needed
            if self.create_indexes:
                await self._ensure_indexes_exist(table_mapping)
            
            # Process file in batches
            total_records = 0
            inserted_records = 0
            updated_records = 0
            skipped_records = 0
            error_records = 0
            
            async for batch_result in self._process_file_batches(file_path_obj, table_mapping):
                total_records += batch_result['total']
                inserted_records += batch_result['inserted']
                updated_records += batch_result['updated']
                skipped_records += batch_result['skipped']
                error_records += batch_result['errors']
                
                logger.debug(f"Processed batch: +{batch_result['inserted']} ~{batch_result['updated']} "
                           f"#{batch_result['skipped']} !{batch_result['errors']}")
            
            # Update statistics
            update_time = (datetime.now() - start_time).total_seconds()
            
            result = UpdateResult(
                file_path=file_path,
                file_type=file_type,
                county=county,
                total_records=total_records,
                inserted_records=inserted_records,
                updated_records=updated_records,
                skipped_records=skipped_records,
                error_records=error_records,
                update_time=update_time,
                success=True,
                table_name=table_mapping.table_name
            )
            
            # Save update result
            await self._save_update_result(result)
            
            # Update monitoring
            await self.update_monitor.record_update(
                agent_name=f"database_updater_{file_type.lower()}",
                source_url=file_path,
                update_data={
                    'status': 'completed',
                    'records_processed': total_records,
                    'new_records': inserted_records,
                    'updated_records': updated_records
                }
            )
            
            # Update statistics
            self._update_stats(result)
            
            logger.info(f"Database update completed: {inserted_records:,} inserted, "
                       f"{updated_records:,} updated in {update_time:.1f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Database update failed for {file_path}: {str(e)}"
            logger.error(error_msg)
            
            update_time = (datetime.now() - start_time).total_seconds()
            
            result = UpdateResult(
                file_path=file_path,
                file_type=file_type,
                county=county,
                total_records=0,
                inserted_records=0,
                updated_records=0,
                skipped_records=0,
                error_records=0,
                update_time=update_time,
                success=False,
                error=error_msg
            )
            
            await self._save_update_result(result)
            self._update_stats(result)
            
            return result
    
    async def _ensure_table_exists(self, table_mapping: TableMapping):
        """Ensure database table exists with proper schema"""
        async with self.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval('''
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                )
            ''', table_mapping.table_name)
            
            if table_exists:
                logger.debug(f"Table {table_mapping.table_name} already exists")
                return
            
            # Create table
            columns_sql = []
            for field_name, column_name in table_mapping.columns.items():
                column_type = self._get_column_type(field_name)
                columns_sql.append(f"{column_name} {column_type}")
            
            # Add primary key
            if table_mapping.primary_key:
                pk_columns = [table_mapping.columns[field] for field in table_mapping.primary_key 
                             if field in table_mapping.columns]
                if pk_columns:
                    columns_sql.append(f"PRIMARY KEY ({', '.join(pk_columns)})")
            
            create_sql = f'''
                CREATE TABLE {table_mapping.table_name} (
                    id SERIAL,
                    {', '.join(columns_sql)},
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            '''
            
            await conn.execute(create_sql)
            logger.info(f"Created table {table_mapping.table_name}")
            
            # Enable RLS if configured
            if self.enable_rls:
                await conn.execute(f'''
                    ALTER TABLE {table_mapping.table_name} ENABLE ROW LEVEL SECURITY
                ''')
                logger.info(f"Enabled RLS on {table_mapping.table_name}")
    
    def _get_column_type(self, field_name: str) -> str:
        """Get PostgreSQL column type for field"""
        type_mappings = {
            'county_code': 'VARCHAR(2)',
            'parcel_id': 'VARCHAR(50)',
            'parcel_number': 'VARCHAR(50)',
            'owner_name': 'TEXT',
            'owner_address_1': 'TEXT',
            'owner_address_2': 'TEXT',
            'owner_city': 'VARCHAR(100)',
            'owner_state': 'VARCHAR(2)',
            'owner_zip': 'VARCHAR(10)',
            'property_address': 'TEXT',
            'property_city': 'VARCHAR(100)',
            'property_zip': 'VARCHAR(10)',
            'legal_description': 'TEXT',
            'property_use_code': 'VARCHAR(10)',
            'land_value': 'DECIMAL(15,2)',
            'just_value': 'DECIMAL(15,2)',
            'assessed_value': 'DECIMAL(15,2)',
            'exempt_value': 'DECIMAL(15,2)',
            'taxable_value': 'DECIMAL(15,2)',
            'tax_year': 'INTEGER',
            'millage_rate': 'DECIMAL(8,4)',
            'sale_date': 'DATE',
            'sale_price': 'DECIMAL(15,2)',
            'deed_book': 'VARCHAR(20)',
            'deed_page': 'VARCHAR(20)',
            'grantor': 'TEXT',
            'grantee': 'TEXT',
            'deed_type': 'VARCHAR(50)',
            'qualification_code': 'VARCHAR(10)',
            'source_file': 'TEXT',
            'processed_at': 'TIMESTAMP WITH TIME ZONE',
            'row_number': 'INTEGER'
        }
        
        return type_mappings.get(field_name, 'TEXT')
    
    async def _ensure_indexes_exist(self, table_mapping: TableMapping):
        """Ensure indexes exist on table"""
        async with self.pool.acquire() as conn:
            for index_def in table_mapping.indexes:
                try:
                    await conn.execute(f'CREATE INDEX IF NOT EXISTS {index_def}')
                    logger.debug(f"Ensured index: {index_def}")
                except Exception as e:
                    logger.warning(f"Failed to create index {index_def}: {e}")
    
    async def _process_file_batches(self, file_path: Path, table_mapping: TableMapping):
        """Process file in batches and yield results"""
        batch_data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Prepare row for database
                db_row = self._prepare_row_for_db(row, table_mapping)
                batch_data.append(db_row)
                
                if len(batch_data) >= self.batch_size:
                    batch_result = await self._process_batch(batch_data, table_mapping)
                    yield batch_result
                    batch_data = []
            
            # Process final batch
            if batch_data:
                batch_result = await self._process_batch(batch_data, table_mapping)
                yield batch_result
    
    def _prepare_row_for_db(self, row: Dict[str, str], table_mapping: TableMapping) -> Dict[str, Any]:
        """Prepare CSV row for database insertion"""
        db_row = {}
        
        for field_name, column_name in table_mapping.columns.items():
            value = row.get(field_name, '').strip()
            
            if not value or value.lower() in ('', 'null', 'none'):
                db_row[column_name] = None
                continue
            
            # Type conversions
            try:
                if field_name in ['land_value', 'just_value', 'assessed_value', 'exempt_value', 
                                 'taxable_value', 'sale_price', 'millage_rate']:
                    if value and value != '0':
                        db_row[column_name] = Decimal(value.replace(',', ''))
                    else:
                        db_row[column_name] = None
                elif field_name in ['tax_year', 'row_number']:
                    db_row[column_name] = int(value) if value.isdigit() else None
                elif field_name == 'sale_date':
                    if len(value) == 8 and value.isdigit():
                        date_obj = datetime.strptime(value, '%Y%m%d').date()
                        db_row[column_name] = date_obj
                    else:
                        db_row[column_name] = None
                elif field_name == 'processed_at':
                    if value:
                        db_row[column_name] = datetime.fromisoformat(value)
                    else:
                        db_row[column_name] = datetime.now()
                else:
                    db_row[column_name] = value
            except (ValueError, TypeError, InvalidOperation) as e:
                logger.warning(f"Type conversion error for {field_name}='{value}': {e}")
                db_row[column_name] = None
        
        return db_row
    
    async def _process_batch(self, batch_data: List[Dict[str, Any]], 
                           table_mapping: TableMapping) -> Dict[str, int]:
        """Process a batch of records with UPSERT"""
        if not batch_data:
            return {'total': 0, 'inserted': 0, 'updated': 0, 'skipped': 0, 'errors': 0}
        
        async with self.pool.acquire() as conn:
            # Prepare UPSERT query
            columns = list(batch_data[0].keys())
            placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
            
            # Build conflict columns (primary key)
            conflict_columns = [table_mapping.columns[field] for field in table_mapping.primary_key 
                              if field in table_mapping.columns]
            
            # Build update clause for ON CONFLICT
            update_clauses = []
            for col in columns:
                if col not in conflict_columns:  # Don't update primary key columns
                    update_clauses.append(f"{col} = EXCLUDED.{col}")
            
            if conflict_columns and update_clauses:
                upsert_sql = f'''
                    INSERT INTO {table_mapping.table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT ({', '.join(conflict_columns)})
                    DO UPDATE SET
                        {', '.join(update_clauses)},
                        updated_at = NOW()
                    RETURNING 
                        CASE 
                            WHEN xmax = 0 THEN 'inserted'
                            ELSE 'updated'
                        END as action
                '''
            else:
                # Fallback to simple INSERT with conflict handling
                upsert_sql = f'''
                    INSERT INTO {table_mapping.table_name} ({', '.join(columns)})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                    RETURNING 'inserted' as action
                '''
            
            # Execute batch
            inserted = 0
            updated = 0
            errors = 0
            
            async with conn.transaction():
                for row_data in batch_data:
                    try:
                        values = [row_data.get(col) for col in columns]
                        result = await conn.fetchrow(upsert_sql, *values)
                        
                        if result:
                            if result['action'] == 'inserted':
                                inserted += 1
                            else:
                                updated += 1
                        else:
                            # ON CONFLICT DO NOTHING was triggered
                            pass
                            
                    except Exception as e:
                        logger.warning(f"Error inserting record: {e}")
                        errors += 1
            
            return {
                'total': len(batch_data),
                'inserted': inserted,
                'updated': updated,
                'skipped': len(batch_data) - inserted - updated - errors,
                'errors': errors
            }
    
    async def _save_update_result(self, result: UpdateResult):
        """Save update result to state database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO update_history 
                (file_path, file_type, county, table_name, total_records, inserted_records, 
                 updated_records, skipped_records, error_records, update_time, success, error, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                result.file_path,
                result.file_type,
                result.county,
                result.table_name,
                result.total_records,
                result.inserted_records,
                result.updated_records,
                result.skipped_records,
                result.error_records,
                result.update_time,
                result.success,
                result.error,
                json.dumps(asdict(result), default=str)
            ))
            conn.commit()
    
    def _update_stats(self, result: UpdateResult):
        """Update processing statistics"""
        self.update_stats['total_updates'] += 1
        
        if result.success:
            self.update_stats['successful_updates'] += 1
            self.update_stats['records_inserted'] += result.inserted_records
            self.update_stats['records_updated'] += result.updated_records
            self.update_stats['total_time'] += result.update_time
        else:
            self.update_stats['failed_updates'] += 1
    
    async def get_table_stats(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a table"""
        async with self.pool.acquire() as conn:
            # Get record count
            total_records = await conn.fetchval(f'SELECT COUNT(*) FROM {table_name}')
            
            # Get date range if applicable
            date_columns = ['created_at', 'updated_at', 'sale_date', 'processed_at']
            date_stats = {}
            
            for col in date_columns:
                try:
                    min_date = await conn.fetchval(f'SELECT MIN({col}) FROM {table_name} WHERE {col} IS NOT NULL')
                    max_date = await conn.fetchval(f'SELECT MAX({col}) FROM {table_name} WHERE {col} IS NOT NULL')
                    
                    if min_date and max_date:
                        date_stats[col] = {
                            'min': min_date.isoformat() if hasattr(min_date, 'isoformat') else str(min_date),
                            'max': max_date.isoformat() if hasattr(max_date, 'isoformat') else str(max_date)
                        }
                except Exception:
                    pass
            
            # Get county distribution if county_code column exists
            county_stats = {}
            try:
                county_counts = await conn.fetch(f'''
                    SELECT county_code, COUNT(*) as count 
                    FROM {table_name} 
                    WHERE county_code IS NOT NULL
                    GROUP BY county_code 
                    ORDER BY count DESC
                ''')
                county_stats = {row['county_code']: row['count'] for row in county_counts}
            except Exception:
                pass
            
            return {
                'table_name': table_name,
                'total_records': total_records,
                'date_stats': date_stats,
                'county_stats': county_stats
            }
    
    def get_update_stats(self) -> Dict[str, Any]:
        """Get update statistics"""
        return self.update_stats.copy()
    
    def get_update_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get update history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM update_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    async def cleanup_old_data(self, table_name: str, days_old: int = 90):
        """Clean up old data from table"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        async with self.pool.acquire() as conn:
            deleted_count = await conn.fetchval(f'''
                WITH deleted AS (
                    DELETE FROM {table_name} 
                    WHERE created_at < $1
                    RETURNING 1
                )
                SELECT COUNT(*) FROM deleted
            ''', cutoff_date)
            
            logger.info(f"Cleaned up {deleted_count:,} old records from {table_name}")
            return deleted_count

# Standalone execution for testing
async def main():
    """Test the database updater"""
    config = {
        'batch_size': 1000,
        'create_tables': True,
        'create_indexes': True,
        'max_retries': 3
    }
    
    async with FloridaDatabaseUpdater(config) as updater:
        # Test file (replace with actual processed file path)
        test_file = "test_processed_data.csv"
        
        if Path(test_file).exists():
            result = await updater.update_from_file(test_file, 'NAL', 'broward')
            
            print(f"Database update result:")
            print(f"  Success: {result.success}")
            print(f"  Total records: {result.total_records:,}")
            print(f"  Inserted: {result.inserted_records:,}")
            print(f"  Updated: {result.updated_records:,}")
            print(f"  Skipped: {result.skipped_records:,}")
            print(f"  Errors: {result.error_records:,}")
            print(f"  Update time: {result.update_time:.1f}s")
            print(f"  Table: {result.table_name}")
            
            if result.error:
                print(f"  Error: {result.error}")
        else:
            print(f"Test file {test_file} not found")

if __name__ == "__main__":
    asyncio.run(main())