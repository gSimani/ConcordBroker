#!/usr/bin/env python3
"""
Florida Database Agent
Specialized agent for Supabase database operations

Features:
- Batch upsert operations for performance
- Automatic schema detection and table creation
- Conflict resolution and duplicate handling
- Transaction management with rollback
- Connection pooling and retry logic
- Data integrity validation
- Performance monitoring and optimization
"""

import asyncio
import asyncpg
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib
import time
from contextlib import asynccontextmanager

# Add parent directories to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "workers"))

from supabase_config import SupabaseConfig

logger = logging.getLogger(__name__)

@dataclass
class DatabaseOperation:
    """Database operation record"""
    operation_id: str
    operation_type: str  # insert, update, upsert, delete
    table_name: str
    records_affected: int
    duration_seconds: float
    status: str  # success, failed, partial
    error_message: Optional[str] = None
    timestamp: datetime = None

@dataclass
class TableSchema:
    """Database table schema"""
    table_name: str
    columns: Dict[str, str]  # column_name: data_type
    primary_key: List[str]
    indexes: List[str]
    constraints: List[str]

class FloridaDatabaseAgent:
    """Agent responsible for database operations with Supabase"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_config()
        
        # Database configuration
        self.supabase_config = SupabaseConfig()
        self.db_url = self.supabase_config.SUPABASE_DB_URL
        self.connection_pool = None
        self.batch_size = self.config.get("database", {}).get("batch_size", 1000)
        self.max_connections = self.config.get("database", {}).get("max_connections", 10)
        self.retry_attempts = self.config.get("database", {}).get("retry_attempts", 3)
        
        # Performance settings
        self.enable_parallel_processing = self.config.get("database", {}).get("enable_parallel", True)
        self.max_parallel_operations = self.config.get("database", {}).get("max_parallel_ops", 5)
        
        # Statistics
        self.stats = {
            "operations_performed": 0,
            "records_inserted": 0,
            "records_updated": 0,
            "records_deleted": 0,
            "batch_operations": 0,
            "connection_errors": 0,
            "last_operation": None,
            "average_operation_time": 0.0,
            "total_data_size_mb": 0.0
        }
        
        # Operation history
        self.operation_history: List[DatabaseOperation] = []
        
        # Table schemas cache
        self.table_schemas: Dict[str, TableSchema] = {}
        
        # Prepared statements cache
        self.prepared_statements: Dict[str, str] = {}

    async def initialize(self):
        """Initialize the database agent"""
        logger.info("Initializing Florida Database Agent...")
        
        try:
            # Create connection pool
            self.connection_pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=self.max_connections,
                max_queries=50000,
                max_inactive_connection_lifetime=300.0,
                command_timeout=60
            )
            
            # Test connection
            async with self.connection_pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            # Initialize schemas for Florida data tables
            await self._initialize_florida_schemas()
            
            logger.info(f"✅ Florida Database Agent initialized (pool size: {self.max_connections})")
            
        except Exception as e:
            logger.error(f"Failed to initialize database agent: {e}")
            raise

    async def cleanup(self):
        """Cleanup database connections"""
        if self.connection_pool:
            await self.connection_pool.close()
        
        logger.info("✅ Florida Database Agent cleanup complete")

    async def _initialize_florida_schemas(self):
        """Initialize schemas for Florida property data tables"""
        
        # NAL (Name Address Legal) table schema
        nal_schema = TableSchema(
            table_name="florida_nal_data",
            columns={
                "id": "SERIAL PRIMARY KEY",
                "parcel_id": "VARCHAR(50) NOT NULL",
                "county_code": "VARCHAR(2) NOT NULL",
                "year": "VARCHAR(6) NOT NULL",
                "owner_name": "TEXT",
                "owner_name_2": "TEXT",
                "property_address": "TEXT",
                "property_city": "VARCHAR(100)",
                "property_state": "VARCHAR(2)",
                "property_zip": "VARCHAR(10)",
                "owner_address": "TEXT",
                "owner_city": "VARCHAR(100)",
                "owner_state": "VARCHAR(2)", 
                "owner_zip": "VARCHAR(10)",
                "legal_description": "TEXT",
                "file_type": "VARCHAR(10) DEFAULT 'NAL'",
                "source_file": "VARCHAR(200)",
                "row_number": "INTEGER",
                "record_hash": "VARCHAR(32)",
                "processed_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
            },
            primary_key=["id"],
            indexes=[
                "parcel_id", "county_code", "year", "record_hash",
                "owner_name", "property_address"
            ],
            constraints=[
                "UNIQUE(parcel_id, county_code, year, record_hash)"
            ]
        )
        
        # NAP (Name Address Property) table schema  
        nap_schema = TableSchema(
            table_name="florida_nap_data",
            columns={
                "id": "SERIAL PRIMARY KEY",
                "parcel_id": "VARCHAR(50) NOT NULL",
                "county_code": "VARCHAR(2) NOT NULL", 
                "year": "VARCHAR(6) NOT NULL",
                "property_use_code": "VARCHAR(10)",
                "assessed_value": "DECIMAL(15,2)",
                "just_value": "DECIMAL(15,2)",
                "taxable_value": "DECIMAL(15,2)",
                "exemption_amount": "DECIMAL(15,2)",
                "land_value": "DECIMAL(15,2)",
                "building_value": "DECIMAL(15,2)",
                "living_area": "INTEGER",
                "year_built": "INTEGER",
                "bedrooms": "INTEGER",
                "bathrooms": "DECIMAL(3,1)",
                "pool": "VARCHAR(1)",
                "file_type": "VARCHAR(10) DEFAULT 'NAP'",
                "source_file": "VARCHAR(200)",
                "row_number": "INTEGER",
                "record_hash": "VARCHAR(32)",
                "processed_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
            },
            primary_key=["id"],
            indexes=[
                "parcel_id", "county_code", "year", "record_hash",
                "property_use_code", "assessed_value", "just_value"
            ],
            constraints=[
                "UNIQUE(parcel_id, county_code, year, record_hash)"
            ]
        )
        
        # SDF (Sales Data Files) table schema
        sdf_schema = TableSchema(
            table_name="florida_sdf_data",
            columns={
                "id": "SERIAL PRIMARY KEY",
                "parcel_id": "VARCHAR(50) NOT NULL",
                "county_code": "VARCHAR(2) NOT NULL",
                "year": "VARCHAR(6) NOT NULL", 
                "sale_date": "DATE",
                "sale_price": "DECIMAL(15,2)",
                "qualified_sale": "VARCHAR(1)",
                "deed_book": "VARCHAR(20)",
                "deed_page": "VARCHAR(20)",
                "grantor_name": "TEXT",
                "grantee_name": "TEXT",
                "sale_type": "VARCHAR(50)",
                "financing_type": "VARCHAR(50)",
                "file_type": "VARCHAR(10) DEFAULT 'SDF'",
                "source_file": "VARCHAR(200)",
                "row_number": "INTEGER", 
                "record_hash": "VARCHAR(32)",
                "processed_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "created_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
                "updated_at": "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"
            },
            primary_key=["id"],
            indexes=[
                "parcel_id", "county_code", "year", "record_hash",
                "sale_date", "sale_price", "qualified_sale"
            ],
            constraints=[
                "UNIQUE(parcel_id, county_code, year, sale_date, record_hash)"
            ]
        )
        
        # Store schemas
        self.table_schemas = {
            "NAL": nal_schema,
            "NAP": nap_schema,
            "SDF": sdf_schema
        }
        
        # Ensure tables exist
        for file_type, schema in self.table_schemas.items():
            await self._ensure_table_exists(schema)

    async def _ensure_table_exists(self, schema: TableSchema):
        """Ensure a table exists with the correct schema"""
        try:
            async with self.connection_pool.acquire() as conn:
                # Check if table exists
                exists = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = $1
                    )
                """, schema.table_name)
                
                if not exists:
                    # Create table
                    columns_sql = ", ".join([
                        f"{col_name} {col_type}" 
                        for col_name, col_type in schema.columns.items()
                    ])
                    
                    create_table_sql = f"""
                        CREATE TABLE {schema.table_name} (
                            {columns_sql}
                        )
                    """
                    
                    await conn.execute(create_table_sql)
                    logger.info(f"Created table: {schema.table_name}")
                    
                    # Create indexes
                    for index_col in schema.indexes:
                        if index_col not in schema.primary_key:
                            index_name = f"idx_{schema.table_name}_{index_col}"
                            index_sql = f"""
                                CREATE INDEX IF NOT EXISTS {index_name} 
                                ON {schema.table_name} ({index_col})
                            """
                            await conn.execute(index_sql)
                    
                    # Add constraints  
                    for constraint in schema.constraints:
                        constraint_name = f"uk_{schema.table_name}_{hash(constraint) % 10000}"
                        constraint_sql = f"""
                            ALTER TABLE {schema.table_name} 
                            ADD CONSTRAINT {constraint_name} {constraint}
                        """
                        try:
                            await conn.execute(constraint_sql)
                        except Exception as e:
                            if "already exists" not in str(e):
                                logger.warning(f"Failed to add constraint to {schema.table_name}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to ensure table {schema.table_name} exists: {e}")
            raise

    async def update_database(self, processed_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update database with processed data using batch operations"""
        logger.info(f"💾 Starting database update with {len(processed_data)} records...")
        
        start_time = datetime.now()
        operation_id = f"db_update_{start_time.strftime('%Y%m%d_%H%M%S')}"
        
        # Group records by file type
        grouped_data = {}
        for record in processed_data:
            file_type = record.get('file_type', 'UNKNOWN')
            if file_type not in grouped_data:
                grouped_data[file_type] = []
            grouped_data[file_type].append(record)
        
        total_records_updated = 0
        operations = []
        errors = []
        
        try:
            # Process each file type
            if self.enable_parallel_processing and len(grouped_data) > 1:
                # Process file types in parallel
                semaphore = asyncio.Semaphore(self.max_parallel_operations)
                tasks = []
                
                for file_type, records in grouped_data.items():
                    task = asyncio.create_task(
                        self._process_file_type_data(semaphore, file_type, records, operation_id)
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Collect results
                for result in results:
                    if isinstance(result, Exception):
                        errors.append({
                            "component": "database_parallel_processing",
                            "error": str(result),
                            "timestamp": datetime.now()
                        })
                    elif result:
                        operations.append(result["operation"])
                        total_records_updated += result["records_updated"]
                        if result.get("errors"):
                            errors.extend(result["errors"])
            else:
                # Process file types sequentially
                for file_type, records in grouped_data.items():
                    try:
                        result = await self._process_file_type_data(None, file_type, records, operation_id)
                        operations.append(result["operation"])
                        total_records_updated += result["records_updated"]
                        if result.get("errors"):
                            errors.extend(result["errors"])
                            
                    except Exception as e:
                        logger.error(f"Failed to process {file_type} data: {e}")
                        errors.append({
                            "component": "database_sequential_processing",
                            "file_type": file_type,
                            "error": str(e),
                            "timestamp": datetime.now()
                        })
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds()
            
            self.stats["operations_performed"] += len(operations)
            self.stats["records_updated"] += total_records_updated
            self.stats["last_operation"] = datetime.now()
            
            # Update average operation time
            if self.stats["operations_performed"] > 0:
                self.stats["average_operation_time"] = (
                    (self.stats["average_operation_time"] * (self.stats["operations_performed"] - len(operations)) + 
                     duration) / self.stats["operations_performed"]
                )
            
            logger.info(f"✅ Database update complete: {total_records_updated} records updated "
                       f"in {duration:.2f}s ({len(errors)} errors)")
            
            return {
                "operation_id": operation_id,
                "records_updated": total_records_updated,
                "operations": operations,
                "duration_seconds": duration,
                "errors": errors,
                "success": len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Database update failed: {e}")
            duration = (datetime.now() - start_time).total_seconds()
            
            self.stats["connection_errors"] += 1
            
            return {
                "operation_id": operation_id,
                "records_updated": 0,
                "operations": [],
                "duration_seconds": duration,
                "errors": [{
                    "component": "database_update",
                    "error": str(e),
                    "timestamp": datetime.now()
                }],
                "success": False
            }

    async def _process_file_type_data(self, semaphore: Optional[asyncio.Semaphore],
                                    file_type: str, records: List[Dict[str, Any]],
                                    operation_id: str) -> Dict[str, Any]:
        """Process data for a specific file type"""
        async def _process():
            start_time = datetime.now()
            
            # Get table schema
            schema = self.table_schemas.get(file_type)
            if not schema:
                raise ValueError(f"Unknown file type: {file_type}")
            
            # Split records into batches
            batches = [
                records[i:i + self.batch_size] 
                for i in range(0, len(records), self.batch_size)
            ]
            
            total_updated = 0
            errors = []
            
            for batch_num, batch in enumerate(batches):
                try:
                    batch_result = await self._upsert_batch(schema, batch)
                    total_updated += batch_result["records_affected"]
                    
                    if batch_result.get("errors"):
                        errors.extend(batch_result["errors"])
                    
                    logger.debug(f"Processed batch {batch_num + 1}/{len(batches)} for {file_type}: "
                               f"{batch_result['records_affected']} records")
                               
                except Exception as e:
                    logger.error(f"Batch {batch_num + 1} failed for {file_type}: {e}")
                    errors.append({
                        "component": "batch_processing",
                        "file_type": file_type,
                        "batch_number": batch_num + 1,
                        "error": str(e),
                        "timestamp": datetime.now()
                    })
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Create operation record
            operation = DatabaseOperation(
                operation_id=f"{operation_id}_{file_type}",
                operation_type="upsert",
                table_name=schema.table_name,
                records_affected=total_updated,
                duration_seconds=duration,
                status="success" if len(errors) == 0 else "partial",
                error_message=f"{len(errors)} batch errors" if errors else None,
                timestamp=datetime.now()
            )
            
            # Store in operation history
            self.operation_history.append(operation)
            
            # Keep only last 1000 operations in memory
            if len(self.operation_history) > 1000:
                self.operation_history = self.operation_history[-1000:]
            
            return {
                "operation": operation,
                "records_updated": total_updated,
                "errors": errors
            }
        
        if semaphore:
            async with semaphore:
                return await _process()
        else:
            return await _process()

    async def _upsert_batch(self, schema: TableSchema, batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch upsert operation with conflict resolution"""
        
        for attempt in range(self.retry_attempts):
            try:
                async with self.connection_pool.acquire() as conn:
                    async with conn.transaction():
                        # Prepare the upsert statement
                        upsert_sql = self._build_upsert_statement(schema, batch[0])
                        
                        # Execute batch upsert
                        records_affected = 0
                        
                        for record in batch:
                            # Filter record to only include columns that exist in the schema
                            filtered_record = {
                                col: record.get(col) 
                                for col in schema.columns.keys() 
                                if col in record and col != 'id'  # Skip auto-increment ID
                            }
                            
                            # Add/update timestamps
                            filtered_record['updated_at'] = datetime.now()
                            if 'created_at' not in filtered_record:
                                filtered_record['created_at'] = datetime.now()
                            
                            # Execute upsert
                            values = list(filtered_record.values())
                            result = await conn.execute(upsert_sql, *values)
                            
                            # Parse result to get affected rows
                            if result.startswith('INSERT') or result.startswith('UPDATE'):
                                records_affected += 1
                        
                        return {
                            "records_affected": records_affected,
                            "errors": []
                        }
                
            except Exception as e:
                logger.warning(f"Upsert attempt {attempt + 1}/{self.retry_attempts} failed: {e}")
                
                if attempt < self.retry_attempts - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    return {
                        "records_affected": 0,
                        "errors": [{
                            "component": "batch_upsert",
                            "table": schema.table_name,
                            "batch_size": len(batch),
                            "error": str(e),
                            "timestamp": datetime.now()
                        }]
                    }

    def _build_upsert_statement(self, schema: TableSchema, sample_record: Dict[str, Any]) -> str:
        """Build an upsert SQL statement for the given schema and record"""
        
        # Get columns that exist in both the schema and the record (excluding ID)
        columns = [col for col in schema.columns.keys() if col in sample_record and col != 'id']
        
        # Build the INSERT part
        placeholders = ', '.join([f'${i+1}' for i in range(len(columns))])
        insert_sql = f"""
            INSERT INTO {schema.table_name} ({', '.join(columns)})
            VALUES ({placeholders})
        """
        
        # Build the ON CONFLICT part
        # Use the unique constraint for conflict resolution
        conflict_columns = []
        for constraint in schema.constraints:
            if constraint.startswith('UNIQUE'):
                # Extract column names from UNIQUE constraint
                # Format: UNIQUE(col1, col2, ...)
                start = constraint.find('(') + 1
                end = constraint.find(')')
                conflict_columns = [col.strip() for col in constraint[start:end].split(',')]
                break
        
        if not conflict_columns:
            # Fallback to primary key if no unique constraint found
            conflict_columns = [col for col in schema.primary_key if col in columns]
        
        if conflict_columns:
            # Build UPDATE part for conflict resolution
            update_assignments = ', '.join([
                f"{col} = EXCLUDED.{col}" 
                for col in columns 
                if col not in conflict_columns
            ])
            
            on_conflict_sql = f"""
                ON CONFLICT ({', '.join(conflict_columns)})
                DO UPDATE SET {update_assignments}, updated_at = NOW()
            """
            
            upsert_sql = insert_sql + ' ' + on_conflict_sql
        else:
            # No conflict resolution possible, just INSERT
            upsert_sql = insert_sql
        
        return upsert_sql

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            stats = {}
            
            async with self.connection_pool.acquire() as conn:
                # Get table statistics
                for file_type, schema in self.table_schemas.items():
                    table_stats = await conn.fetchrow(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(DISTINCT parcel_id) as unique_parcels,
                            COUNT(DISTINCT county_code) as counties,
                            MIN(created_at) as oldest_record,
                            MAX(created_at) as newest_record,
                            pg_size_pretty(pg_total_relation_size('{schema.table_name}')) as table_size
                        FROM {schema.table_name}
                    """)
                    
                    stats[file_type] = dict(table_stats) if table_stats else {}
                
                # Get overall database size
                db_stats = await conn.fetchrow("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as database_size
                """)
                
                stats["database_size"] = dict(db_stats)["database_size"] if db_stats else "Unknown"
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    async def cleanup_old_data(self, retention_days: int = 365) -> Dict[str, Any]:
        """Cleanup old data based on retention policy"""
        logger.info(f"Starting cleanup of data older than {retention_days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        deleted_records = {}
        errors = []
        
        try:
            async with self.connection_pool.acquire() as conn:
                for file_type, schema in self.table_schemas.items():
                    try:
                        # Delete old records
                        result = await conn.execute(f"""
                            DELETE FROM {schema.table_name} 
                            WHERE created_at < $1
                        """, cutoff_date)
                        
                        # Parse result to get deleted count
                        deleted_count = int(result.split()[-1]) if result.startswith('DELETE') else 0
                        deleted_records[file_type] = deleted_count
                        
                        logger.info(f"Deleted {deleted_count} old records from {schema.table_name}")
                        
                    except Exception as e:
                        logger.error(f"Failed to cleanup {schema.table_name}: {e}")
                        errors.append({
                            "table": schema.table_name,
                            "error": str(e),
                            "timestamp": datetime.now()
                        })
                
                # Vacuum tables for space reclamation
                for file_type, schema in self.table_schemas.items():
                    try:
                        await conn.execute(f"VACUUM ANALYZE {schema.table_name}")
                    except Exception as e:
                        logger.warning(f"Failed to vacuum {schema.table_name}: {e}")
            
            total_deleted = sum(deleted_records.values())
            logger.info(f"✅ Cleanup complete: {total_deleted} records deleted")
            
            return {
                "total_deleted": total_deleted,
                "deleted_by_table": deleted_records,
                "errors": errors,
                "success": len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Cleanup operation failed: {e}")
            return {
                "total_deleted": 0,
                "deleted_by_table": {},
                "errors": [{"error": str(e), "timestamp": datetime.now()}],
                "success": False
            }

    async def get_health_status(self):
        """Get health status of the database agent"""
        from dataclasses import dataclass
        from typing import List
        
        @dataclass
        class AgentHealth:
            name: str
            status: str
            last_run: Optional[datetime]
            success_rate: float
            error_count: int
            performance_metrics: Dict[str, float]
            alerts: List[str]
        
        # Calculate success rate
        total_operations = self.stats["operations_performed"]
        connection_errors = self.stats["connection_errors"]
        success_rate = (
            (total_operations - connection_errors) / total_operations 
            if total_operations > 0 else 1.0
        )
        
        # Determine status
        if success_rate > 0.95:
            status = "healthy"
        elif success_rate > 0.8:
            status = "degraded"
        else:
            status = "failed"
        
        # Check connection pool health
        if not self.connection_pool:
            status = "failed"
        
        alerts = []
        if connection_errors > 0:
            alerts.append(f"{connection_errors} connection errors")
        
        if self.stats["last_operation"]:
            time_since_last = datetime.now() - self.stats["last_operation"]
            if time_since_last > timedelta(days=2):
                alerts.append("No database operations in over 2 days")
        
        # Check connection pool size
        if self.connection_pool:
            try:
                pool_size = self.connection_pool.get_size()
                if pool_size < 2:
                    alerts.append("Low connection pool size")
            except:
                pass
        
        return AgentHealth(
            name="database_agent",
            status=status,
            last_run=self.stats["last_operation"],
            success_rate=success_rate,
            error_count=connection_errors,
            performance_metrics={
                "operations_performed": self.stats["operations_performed"],
                "records_updated": self.stats["records_updated"],
                "average_operation_time": self.stats["average_operation_time"],
                "batch_operations": self.stats["batch_operations"]
            },
            alerts=alerts
        )