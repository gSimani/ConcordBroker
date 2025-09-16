#!/usr/bin/env python3
"""
NAL Batch Import Agent
=====================
High-performance batch import agent with parallel processing for Supabase.
Optimized for importing 753K+ records across 7 normalized tables efficiently.
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import psycopg2
from psycopg2.extras import execute_batch, execute_values
from psycopg2.pool import ThreadedConnectionPool
import sqlalchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class BatchImportResult:
    """Result of batch import operation"""
    batch_number: int
    processed: int = 0
    successful: int = 0
    failed: int = 0
    processing_time: float = 0
    errors: List[str] = None
    table_results: Dict[str, Dict] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.table_results is None:
            self.table_results = {}

@dataclass
class TableImportConfig:
    """Configuration for importing to specific table"""
    table_name: str
    insert_sql: str
    field_mapping: Dict[str, str]
    batch_size: int = 1000
    max_retries: int = 3
    priority: int = 1  # 1 = highest priority

class NALBatchImportAgent:
    """
    Agent specialized in high-performance batch imports to Supabase
    
    Features:
    - Parallel processing across multiple tables
    - Connection pooling for optimal performance
    - Batch optimization with conflict resolution
    - Memory-efficient processing
    - Error handling and retry logic
    - Progress tracking and metrics
    """
    
    def __init__(self, batch_size: int = 2000, max_workers: int = 4, enable_parallel_tables: bool = True):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.enable_parallel_tables = enable_parallel_tables
        
        # Database connection configuration
        self.db_config = self._load_database_config()
        self.connection_pool = None
        self.engine = None
        
        # Performance tracking
        self.import_metrics = {
            'batches_processed': 0,
            'records_imported': 0,
            'total_errors': 0,
            'avg_batch_time': 0,
            'throughput_records_per_second': 0,
            'table_performance': {}
        }
        
        # Table configurations
        self.table_configs = self._setup_table_configurations()
        
        logger.info(f"NAL Batch Import Agent initialized")
        logger.info(f"Batch size: {batch_size}, Max workers: {max_workers}")
        logger.info(f"Parallel tables: {enable_parallel_tables}")
    
    def _load_database_config(self) -> Dict[str, str]:
        """Load database configuration from environment or config file"""
        # Try to load from environment variables first
        db_config = {
            'host': os.getenv('SUPABASE_HOST', 'localhost'),
            'port': os.getenv('SUPABASE_PORT', '5432'),
            'database': os.getenv('SUPABASE_DATABASE', 'postgres'),
            'username': os.getenv('SUPABASE_USERNAME', 'postgres'),
            'password': os.getenv('SUPABASE_PASSWORD', ''),
            'sslmode': 'require' if 'supabase.co' in os.getenv('SUPABASE_HOST', '') else 'prefer'
        }
        
        # Try to load from supabase config if environment vars not available
        try:
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'api'))
            from supabase_client import get_supabase_client
            
            # This is a fallback - in production we'd use proper config management
            db_config.update({
                'host': 'aws-0-us-west-1.pooler.supabase.com',
                'port': '6543',
                'database': 'postgres',
                # Note: In production, these should come from secure environment variables
            })
        except ImportError:
            logger.warning("Could not import supabase_client, using default config")
        
        return db_config
    
    def _setup_table_configurations(self) -> Dict[str, TableImportConfig]:
        """Setup table-specific import configurations"""
        return {
            'florida_properties_core': TableImportConfig(
                table_name='florida_properties_core',
                insert_sql="""
                INSERT INTO florida_properties_core (
                    parcel_id, county_code, county_name, assessment_year, file_type, group_number,
                    physical_address_1, physical_address_2, physical_city, physical_state, physical_zipcode,
                    owner_name, owner_address_1, owner_city, owner_state, owner_zipcode,
                    dor_use_code, property_appraiser_use_code, neighborhood_code, tax_authority_code,
                    just_value, assessed_value_school_district, taxable_value_school_district, land_value,
                    year_built, total_living_area, number_of_buildings, land_square_footage,
                    created_at, updated_at, is_active, data_source
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    county_code = EXCLUDED.county_code,
                    assessment_year = EXCLUDED.assessment_year,
                    just_value = EXCLUDED.just_value,
                    assessed_value_school_district = EXCLUDED.assessed_value_school_district,
                    taxable_value_school_district = EXCLUDED.taxable_value_school_district,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=1000,
                priority=1
            ),
            
            'property_valuations': TableImportConfig(
                table_name='property_valuations',
                insert_sql="""
                INSERT INTO property_valuations (
                    parcel_id, assessed_value_non_school_district, taxable_value_non_school_district,
                    just_value_homestead, assessed_value_homestead,
                    just_value_non_homestead_residential, assessed_value_non_homestead_residential,
                    just_value_residential_non_residential, assessed_value_residential_non_residential,
                    just_value_classification_use, assessed_value_classification_use,
                    just_value_water_recharge, assessed_value_water_recharge,
                    just_value_conservation_land, assessed_value_conservation_land,
                    just_value_historic_commercial, assessed_value_historic_commercial,
                    just_value_historic_significant, assessed_value_historic_significant,
                    just_value_working_waterfront, assessed_value_working_waterfront,
                    new_construction_value, deleted_value, special_features_value, value_transfer_year,
                    just_value_change_flag, just_value_change_code, assessment_transfer_flag,
                    assessment_difference_transfer, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    assessed_value_non_school_district = EXCLUDED.assessed_value_non_school_district,
                    just_value_homestead = EXCLUDED.just_value_homestead,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=1500,
                priority=2
            ),
            
            'property_exemptions': TableImportConfig(
                table_name='property_exemptions',
                insert_sql="""
                INSERT INTO property_exemptions (
                    parcel_id, previous_homestead_owner, homestead_exemption, senior_exemption,
                    disability_exemption, veteran_exemption, agricultural_exemption,
                    all_exemptions, total_exemption_amount, active_exemption_count,
                    has_homestead, has_agricultural, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    homestead_exemption = EXCLUDED.homestead_exemption,
                    total_exemption_amount = EXCLUDED.total_exemption_amount,
                    has_homestead = EXCLUDED.has_homestead,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=2000,
                priority=3
            ),
            
            'property_characteristics': TableImportConfig(
                table_name='property_characteristics',
                insert_sql="""
                INSERT INTO property_characteristics (
                    parcel_id, effective_year_built, actual_year_built, improvement_quality,
                    construction_class, number_residential_units, land_units_code, land_units_count,
                    public_land_indicator, quality_code_1, vacancy_indicator_1, sale_change_code_1,
                    quality_code_2, vacancy_indicator_2, sale_change_code_2, short_legal_description,
                    market_area, township, range_info, section_info, census_block,
                    created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    actual_year_built = EXCLUDED.actual_year_built,
                    improvement_quality = EXCLUDED.improvement_quality,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=1500,
                priority=4
            ),
            
            'property_sales_enhanced': TableImportConfig(
                table_name='property_sales_enhanced',
                insert_sql="""
                INSERT INTO property_sales_enhanced (
                    parcel_id, multiple_parcel_sale_1, sale_price_1, sale_year_1, sale_month_1,
                    official_record_book_1, official_record_page_1, clerk_number_1,
                    multiple_parcel_sale_2, sale_price_2, sale_year_2, sale_month_2,
                    official_record_book_2, official_record_page_2, clerk_number_2,
                    latest_sale_date, latest_sale_price, previous_sale_date, previous_sale_price,
                    price_change_percentage, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    sale_price_1 = EXCLUDED.sale_price_1,
                    latest_sale_date = EXCLUDED.latest_sale_date,
                    latest_sale_price = EXCLUDED.latest_sale_price,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=1500,
                priority=5
            ),
            
            'property_addresses': TableImportConfig(
                table_name='property_addresses',
                insert_sql="""
                INSERT INTO property_addresses (
                    parcel_id, address_type, name, address_1, address_2, city, state, zipcode,
                    state_domicile, fiduciary_code, is_primary, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id, address_type) DO UPDATE SET
                    name = EXCLUDED.name,
                    address_1 = EXCLUDED.address_1,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=2000,
                priority=6
            ),
            
            'property_admin_data': TableImportConfig(
                table_name='property_admin_data',
                insert_sql="""
                INSERT INTO property_admin_data (
                    parcel_id, appraisal_status, county_appraisal_status, sequence_number,
                    real_personal_status_id, multiple_parcel_id, state_parcel_id,
                    special_circumstance_code, special_circumstance_year, special_circumstance_text,
                    last_inspection_date, parcel_split, alternative_key, base_start, active_value_start,
                    district_code, district_year, special_assessment_code, county_previous_homestead,
                    parcel_id_previous_homestead, created_at, updated_at
                ) VALUES %s
                ON CONFLICT (parcel_id) DO UPDATE SET
                    appraisal_status = EXCLUDED.appraisal_status,
                    sequence_number = EXCLUDED.sequence_number,
                    updated_at = EXCLUDED.updated_at
                """,
                field_mapping={},
                batch_size=1500,
                priority=7
            )
        }
    
    async def initialize_database_connection(self):
        """Initialize database connection pool"""
        try:
            # Create connection string
            conn_string = (
                f"postgresql://{self.db_config['username']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
                f"?sslmode={self.db_config['sslmode']}"
            )
            
            # Create SQLAlchemy engine
            self.engine = create_engine(
                conn_string,
                pool_size=self.max_workers * 2,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
            
            # Create psycopg2 connection pool for batch operations
            self.connection_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=self.max_workers * 2,
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password'],
                sslmode=self.db_config['sslmode']
            )
            
            logger.info(f"Connection pool created with {self.max_workers * 2} connections")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    async def deploy_database_schema(self):
        """Deploy the optimized database schema"""
        try:
            logger.info("Deploying NAL database schema...")
            
            # Read and execute schema file
            schema_file_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'optimized_nal_database_schema.sql'
            )
            
            if os.path.exists(schema_file_path):
                with open(schema_file_path, 'r') as f:
                    schema_sql = f.read()
                
                # Split into individual statements
                statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
                
                # Execute statements
                with self.engine.connect() as conn:
                    for i, statement in enumerate(statements):
                        if statement and not statement.startswith('--'):
                            try:
                                conn.execute(text(statement))
                                if i % 10 == 0:
                                    logger.debug(f"Executed {i+1}/{len(statements)} schema statements")
                            except Exception as stmt_error:
                                # Log but continue with non-critical errors
                                logger.warning(f"Schema statement failed (continuing): {stmt_error}")
                    
                    conn.commit()
                
                logger.info("Database schema deployed successfully")
            else:
                logger.warning(f"Schema file not found: {schema_file_path}")
                
        except Exception as e:
            logger.error(f"Schema deployment failed: {e}")
            raise
    
    async def import_batch(self, transformed_data: Dict[str, List[Dict]], batch_number: int) -> BatchImportResult:
        """
        Import a batch of transformed data across all tables
        
        Args:
            transformed_data: Dict mapping table names to lists of records
            batch_number: Batch identifier for tracking
            
        Returns:
            BatchImportResult with processing statistics
        """
        start_time = time.time()
        result = BatchImportResult(batch_number=batch_number)
        
        logger.debug(f"Starting batch {batch_number} import")
        
        try:
            if self.enable_parallel_tables:
                # Import tables in parallel
                result = await self._import_batch_parallel(transformed_data, result)
            else:
                # Import tables sequentially
                result = await self._import_batch_sequential(transformed_data, result)
            
            result.processing_time = time.time() - start_time
            
            # Update metrics
            self.import_metrics['batches_processed'] += 1
            self.import_metrics['records_imported'] += result.successful
            self.import_metrics['total_errors'] += result.failed
            
            # Calculate average batch time
            total_time = (
                self.import_metrics['avg_batch_time'] * (self.import_metrics['batches_processed'] - 1) +
                result.processing_time
            )
            self.import_metrics['avg_batch_time'] = total_time / self.import_metrics['batches_processed']
            
            logger.debug(f"Batch {batch_number} completed in {result.processing_time:.2f}s - "
                        f"Success: {result.successful}, Failed: {result.failed}")
            
            return result
            
        except Exception as e:
            result.errors.append(str(e))
            result.failed = sum(len(records) for records in transformed_data.values())
            result.processing_time = time.time() - start_time
            
            logger.error(f"Batch {batch_number} failed: {e}")
            return result
    
    async def _import_batch_parallel(self, transformed_data: Dict[str, List[Dict]], result: BatchImportResult) -> BatchImportResult:
        """Import batch with parallel table processing"""
        
        # Sort tables by priority (core table first)
        sorted_tables = sorted(
            transformed_data.items(),
            key=lambda x: self.table_configs.get(x[0], TableImportConfig('', '', {}, priority=10)).priority
        )
        
        # Import core table first (required for foreign keys)
        if 'florida_properties_core' in transformed_data:
            core_records = transformed_data['florida_properties_core']
            if core_records:
                logger.debug(f"Importing {len(core_records)} core property records")
                core_result = await self._import_table_records(
                    'florida_properties_core', core_records
                )
                result.table_results['florida_properties_core'] = core_result
                result.processed += len(core_records)
                result.successful += core_result.get('successful', 0)
                result.failed += core_result.get('failed', 0)
                if core_result.get('errors'):
                    result.errors.extend(core_result['errors'])
        
        # Import remaining tables in parallel
        remaining_tables = [(table, records) for table, records in sorted_tables 
                          if table != 'florida_properties_core' and records]
        
        if remaining_tables:
            # Use ThreadPoolExecutor for parallel processing
            loop = asyncio.get_event_loop()
            
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(remaining_tables))) as executor:
                # Submit all table import tasks
                future_to_table = {}
                
                for table_name, records in remaining_tables:
                    future = executor.submit(
                        self._import_table_records_sync, table_name, records
                    )
                    future_to_table[future] = table_name
                
                # Collect results as they complete
                for future in as_completed(future_to_table):
                    table_name = future_to_table[future]
                    try:
                        table_result = future.result()
                        result.table_results[table_name] = table_result
                        
                        # Update totals
                        records_count = len(transformed_data[table_name])
                        result.processed += records_count
                        result.successful += table_result.get('successful', 0)
                        result.failed += table_result.get('failed', 0)
                        
                        if table_result.get('errors'):
                            result.errors.extend(table_result['errors'])
                        
                        logger.debug(f"Table {table_name} import completed: "
                                   f"{table_result.get('successful', 0)} successful, "
                                   f"{table_result.get('failed', 0)} failed")
                        
                    except Exception as table_error:
                        logger.error(f"Table {table_name} import failed: {table_error}")
                        result.errors.append(f"{table_name}: {table_error}")
                        result.failed += len(transformed_data[table_name])
        
        return result
    
    async def _import_batch_sequential(self, transformed_data: Dict[str, List[Dict]], result: BatchImportResult) -> BatchImportResult:
        """Import batch with sequential table processing"""
        
        # Sort tables by priority
        sorted_tables = sorted(
            transformed_data.items(),
            key=lambda x: self.table_configs.get(x[0], TableImportConfig('', '', {}, priority=10)).priority
        )
        
        for table_name, records in sorted_tables:
            if not records:
                continue
            
            logger.debug(f"Importing {len(records)} records to {table_name}")
            
            try:
                table_result = await self._import_table_records(table_name, records)
                result.table_results[table_name] = table_result
                
                result.processed += len(records)
                result.successful += table_result.get('successful', 0)
                result.failed += table_result.get('failed', 0)
                
                if table_result.get('errors'):
                    result.errors.extend(table_result['errors'])
                
            except Exception as table_error:
                logger.error(f"Table {table_name} import failed: {table_error}")
                result.errors.append(f"{table_name}: {table_error}")
                result.failed += len(records)
        
        return result
    
    async def _import_table_records(self, table_name: str, records: List[Dict]) -> Dict[str, Any]:
        """Import records to a specific table (async wrapper)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._import_table_records_sync, table_name, records
        )
    
    def _import_table_records_sync(self, table_name: str, records: List[Dict]) -> Dict[str, Any]:
        """Import records to a specific table (synchronous implementation)"""
        
        table_config = self.table_configs.get(table_name)
        if not table_config:
            return {
                'successful': 0,
                'failed': len(records),
                'errors': [f"No configuration found for table {table_name}"]
            }
        
        result = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        conn = None
        try:
            # Get connection from pool
            conn = self.connection_pool.getconn()
            cursor = conn.cursor()
            
            # Prepare data for batch insert
            values_list = []
            
            for record in records:
                # Handle special cases for different tables
                if table_name == 'property_addresses':
                    # Property addresses may have multiple records per parcel
                    if not isinstance(record, list):
                        records_to_process = [record]
                    else:
                        records_to_process = record
                    
                    for addr_record in records_to_process:
                        values = self._prepare_record_values(table_name, addr_record)
                        if values:
                            values_list.append(values)
                else:
                    values = self._prepare_record_values(table_name, record)
                    if values:
                        values_list.append(values)
            
            if not values_list:
                return result
            
            # Execute batch insert with retry logic
            max_retries = table_config.max_retries
            
            for attempt in range(max_retries):
                try:
                    execute_values(
                        cursor,
                        table_config.insert_sql,
                        values_list,
                        template=None,
                        page_size=table_config.batch_size
                    )
                    conn.commit()
                    
                    result['successful'] = len(values_list)
                    break
                    
                except Exception as insert_error:
                    logger.warning(f"Insert attempt {attempt + 1} failed for {table_name}: {insert_error}")
                    conn.rollback()
                    
                    if attempt == max_retries - 1:
                        # Final attempt failed
                        result['failed'] = len(records)
                        result['errors'].append(f"All {max_retries} attempts failed: {insert_error}")
                    else:
                        # Wait before retry
                        time.sleep(0.5 * (attempt + 1))
            
        except Exception as e:
            result['failed'] = len(records)
            result['errors'].append(str(e))
            logger.error(f"Table {table_name} import error: {e}")
            
        finally:
            if conn:
                # Return connection to pool
                self.connection_pool.putconn(conn)
        
        return result
    
    def _prepare_record_values(self, table_name: str, record: Dict) -> Optional[Tuple]:
        """Prepare record values for database insertion"""
        
        try:
            if table_name == 'florida_properties_core':
                return (
                    record.get('parcel_id'),
                    record.get('county_code', '016'),  # Default to Broward
                    'Broward County',  # Default county name
                    record.get('assessment_year', 2025),
                    record.get('file_type', 'R'),
                    record.get('group_number'),
                    record.get('physical_address_1'),
                    record.get('physical_address_2'),
                    record.get('physical_city'),
                    'FL',  # Default state
                    record.get('physical_zipcode'),
                    record.get('owner_name'),
                    record.get('owner_address_1'),
                    record.get('owner_city'),
                    record.get('owner_state'),
                    record.get('owner_zipcode'),
                    record.get('dor_use_code'),
                    record.get('property_appraiser_use_code'),
                    record.get('neighborhood_code'),
                    record.get('tax_authority_code'),
                    record.get('just_value', 0),
                    record.get('assessed_value_school_district', 0),
                    record.get('taxable_value_school_district', 0),
                    record.get('land_value', 0),
                    record.get('year_built'),
                    record.get('total_living_area'),
                    record.get('number_of_buildings', 0),
                    record.get('land_square_footage'),
                    record.get('created_at'),
                    record.get('updated_at'),
                    True,  # is_active
                    'nal'  # data_source
                )
            
            elif table_name == 'property_valuations':
                return (
                    record.get('parcel_id'),
                    record.get('assessed_value_non_school_district', 0),
                    record.get('taxable_value_non_school_district', 0),
                    record.get('just_value_homestead'),
                    record.get('assessed_value_homestead'),
                    record.get('just_value_non_homestead_residential'),
                    record.get('assessed_value_non_homestead_residential'),
                    record.get('just_value_residential_non_residential'),
                    record.get('assessed_value_residential_non_residential'),
                    record.get('just_value_classification_use'),
                    record.get('assessed_value_classification_use'),
                    record.get('just_value_water_recharge'),
                    record.get('assessed_value_water_recharge'),
                    record.get('just_value_conservation_land'),
                    record.get('assessed_value_conservation_land'),
                    record.get('just_value_historic_commercial'),
                    record.get('assessed_value_historic_commercial'),
                    record.get('just_value_historic_significant'),
                    record.get('assessed_value_historic_significant'),
                    record.get('just_value_working_waterfront'),
                    record.get('assessed_value_working_waterfront'),
                    record.get('new_construction_value', 0),
                    record.get('deleted_value', 0),
                    record.get('special_features_value', 0),
                    record.get('value_transfer_year'),
                    record.get('just_value_change_flag'),
                    record.get('just_value_change_code'),
                    record.get('assessment_transfer_flag'),
                    record.get('assessment_difference_transfer'),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            elif table_name == 'property_exemptions':
                return (
                    record.get('parcel_id'),
                    record.get('previous_homestead_owner'),
                    record.get('homestead_exemption'),
                    record.get('senior_exemption'),
                    record.get('disability_exemption'),
                    record.get('veteran_exemption'),
                    record.get('agricultural_exemption'),
                    record.get('all_exemptions'),  # JSONB field
                    record.get('total_exemption_amount', 0),
                    record.get('active_exemption_count', 0),
                    record.get('has_homestead', False),
                    record.get('has_agricultural', False),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            elif table_name == 'property_characteristics':
                return (
                    record.get('parcel_id'),
                    record.get('effective_year_built'),
                    record.get('actual_year_built'),
                    record.get('improvement_quality'),
                    record.get('construction_class'),
                    record.get('number_residential_units'),
                    record.get('land_units_code'),
                    record.get('land_units_count'),
                    record.get('public_land_indicator'),
                    record.get('quality_code_1'),
                    record.get('vacancy_indicator_1'),
                    record.get('sale_change_code_1'),
                    record.get('quality_code_2'),
                    record.get('vacancy_indicator_2'),
                    record.get('sale_change_code_2'),
                    record.get('short_legal_description'),
                    record.get('market_area'),
                    record.get('township'),
                    record.get('range_info'),
                    record.get('section_info'),
                    record.get('census_block'),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            elif table_name == 'property_sales_enhanced':
                return (
                    record.get('parcel_id'),
                    record.get('multiple_parcel_sale_1'),
                    record.get('sale_price_1'),
                    record.get('sale_year_1'),
                    record.get('sale_month_1'),
                    record.get('official_record_book_1'),
                    record.get('official_record_page_1'),
                    record.get('clerk_number_1'),
                    record.get('multiple_parcel_sale_2'),
                    record.get('sale_price_2'),
                    record.get('sale_year_2'),
                    record.get('sale_month_2'),
                    record.get('official_record_book_2'),
                    record.get('official_record_page_2'),
                    record.get('clerk_number_2'),
                    record.get('latest_sale_date'),
                    record.get('latest_sale_price'),
                    record.get('previous_sale_date'),
                    record.get('previous_sale_price'),
                    record.get('price_change_percentage'),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            elif table_name == 'property_addresses':
                return (
                    record.get('parcel_id'),
                    record.get('address_type', 'owner'),
                    record.get('name'),
                    record.get('address_1'),
                    record.get('address_2'),
                    record.get('city'),
                    record.get('state'),
                    record.get('zipcode'),
                    record.get('state_domicile'),
                    record.get('fiduciary_code'),
                    record.get('is_primary', False),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            elif table_name == 'property_admin_data':
                return (
                    record.get('parcel_id'),
                    record.get('appraisal_status'),
                    record.get('county_appraisal_status'),
                    record.get('sequence_number'),
                    record.get('real_personal_status_id'),
                    record.get('multiple_parcel_id'),
                    record.get('state_parcel_id'),
                    record.get('special_circumstance_code'),
                    record.get('special_circumstance_year'),
                    record.get('special_circumstance_text'),
                    record.get('last_inspection_date'),
                    record.get('parcel_split'),
                    record.get('alternative_key'),
                    record.get('base_start'),
                    record.get('active_value_start'),
                    record.get('district_code'),
                    record.get('district_year'),
                    record.get('special_assessment_code'),
                    record.get('county_previous_homestead'),
                    record.get('parcel_id_previous_homestead'),
                    record.get('created_at'),
                    record.get('updated_at')
                )
            
            else:
                logger.warning(f"Unknown table: {table_name}")
                return None
                
        except Exception as e:
            logger.warning(f"Failed to prepare values for {table_name}: {e}")
            return None
    
    async def validate_import_results(self) -> Dict[str, Any]:
        """Validate import results by checking record counts and data integrity"""
        
        logger.info("Validating import results...")
        
        try:
            validation_result = {
                'table_counts': {},
                'integrity_checks': {},
                'performance_metrics': self.import_metrics,
                'is_valid': True,
                'issues': []
            }
            
            # Check record counts for each table
            with self.engine.connect() as conn:
                for table_name in self.table_configs.keys():
                    try:
                        count_result = conn.execute(
                            text(f"SELECT COUNT(*) as count FROM {table_name}")
                        ).fetchone()
                        validation_result['table_counts'][table_name] = count_result.count
                        
                        logger.info(f"Table {table_name}: {count_result.count:,} records")
                        
                    except Exception as table_error:
                        logger.error(f"Failed to count records in {table_name}: {table_error}")
                        validation_result['issues'].append(f"Could not validate {table_name}: {table_error}")
                
                # Check referential integrity
                try:
                    # Check for orphaned records (records without corresponding core property)
                    for table_name in self.table_configs.keys():
                        if table_name == 'florida_properties_core':
                            continue
                        
                        orphan_check = conn.execute(text(f"""
                            SELECT COUNT(*) as orphans 
                            FROM {table_name} t 
                            WHERE NOT EXISTS (
                                SELECT 1 FROM florida_properties_core c 
                                WHERE c.parcel_id = t.parcel_id
                            )
                        """)).fetchone()
                        
                        validation_result['integrity_checks'][f'{table_name}_orphans'] = orphan_check.orphans
                        
                        if orphan_check.orphans > 0:
                            logger.warning(f"Found {orphan_check.orphans} orphaned records in {table_name}")
                            validation_result['issues'].append(
                                f"{table_name} has {orphan_check.orphans} orphaned records"
                            )
                
                except Exception as integrity_error:
                    logger.error(f"Integrity checks failed: {integrity_error}")
                    validation_result['issues'].append(f"Integrity validation failed: {integrity_error}")
            
            # Calculate final performance metrics
            total_records = sum(validation_result['table_counts'].values())
            if self.import_metrics['avg_batch_time'] > 0:
                self.import_metrics['throughput_records_per_second'] = (
                    self.import_metrics['records_imported'] / 
                    (self.import_metrics['avg_batch_time'] * self.import_metrics['batches_processed'])
                )
            
            validation_result['performance_metrics'] = self.import_metrics
            
            if validation_result['issues']:
                validation_result['is_valid'] = False
            
            logger.info(f"Import validation complete: {len(validation_result['issues'])} issues found")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Import validation failed: {e}")
            raise
    
    def __del__(self):
        """Cleanup resources"""
        if self.connection_pool:
            self.connection_pool.closeall()
        if self.engine:
            self.engine.dispose()