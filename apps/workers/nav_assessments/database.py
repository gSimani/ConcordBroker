"""
Database operations for NAV (Non Ad Valorem) Assessments data
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import asyncpg
from asyncpg.pool import Pool

try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)

class NAVAssessmentsDB:
    """Database operations for NAV Assessments data"""
    
    def __init__(self):
        self.pool: Pool = None
        self.dsn = settings.DATABASE_URL
    
    async def connect(self):
        """Create connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.dsn,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            logger.info("NAV Assessments DB pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("NAV Assessments DB pool closed")
    
    async def create_nav_tables(self):
        """Create NAV data tables if they don't exist"""
        if not self.pool:
            await self.connect()
        
        create_sql = """
        -- NAV N Table (Parcel Assessment Summaries)
        CREATE TABLE IF NOT EXISTS nav_parcel_assessments (
            id SERIAL PRIMARY KEY,
            
            -- Core identifiers
            roll_type VARCHAR(1),
            county_number VARCHAR(2),
            pa_parcel_number VARCHAR(26),
            tc_account_number VARCHAR(30),
            tax_year VARCHAR(4),
            
            -- Assessment summary
            total_assessments DECIMAL(12,2),
            number_of_assessments INTEGER,
            tax_roll_sequence_number INTEGER,
            
            -- Metadata
            county_name VARCHAR(50),
            data_source VARCHAR(100) DEFAULT 'florida_revenue_nav',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            UNIQUE(county_number, pa_parcel_number, tax_year)
        );
        
        -- NAV D Table (Assessment Details)
        CREATE TABLE IF NOT EXISTS nav_assessment_details (
            id SERIAL PRIMARY KEY,
            
            -- Core identifiers  
            record_type VARCHAR(1),
            county_number VARCHAR(2),
            pa_parcel_number VARCHAR(26),
            
            -- Assessment details
            levy_identifier VARCHAR(12),
            local_government_code INTEGER,
            function_code INTEGER,
            assessment_amount DECIMAL(9,2),
            tax_roll_sequence_number INTEGER,
            
            -- Enriched data
            county_name VARCHAR(50),
            function_description VARCHAR(100),
            tax_year VARCHAR(4),
            
            -- Metadata
            data_source VARCHAR(100) DEFAULT 'florida_revenue_nav',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Indexes for NAV N
        CREATE INDEX IF NOT EXISTS idx_nav_parcel_county_year ON nav_parcel_assessments(county_number, tax_year);
        CREATE INDEX IF NOT EXISTS idx_nav_parcel_number ON nav_parcel_assessments(pa_parcel_number);
        CREATE INDEX IF NOT EXISTS idx_nav_parcel_tc_account ON nav_parcel_assessments(tc_account_number);
        CREATE INDEX IF NOT EXISTS idx_nav_parcel_total_assessment ON nav_parcel_assessments(total_assessments);
        
        -- Indexes for NAV D  
        CREATE INDEX IF NOT EXISTS idx_nav_detail_county_year ON nav_assessment_details(county_number, tax_year);
        CREATE INDEX IF NOT EXISTS idx_nav_detail_parcel ON nav_assessment_details(pa_parcel_number);
        CREATE INDEX IF NOT EXISTS idx_nav_detail_levy ON nav_assessment_details(levy_identifier);
        CREATE INDEX IF NOT EXISTS idx_nav_detail_function ON nav_assessment_details(function_code);
        CREATE INDEX IF NOT EXISTS idx_nav_detail_amount ON nav_assessment_details(assessment_amount);
        
        -- Jobs table for tracking loads
        CREATE TABLE IF NOT EXISTS nav_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50),
            table_type VARCHAR(10), -- 'N' or 'D' 
            county_number VARCHAR(2),
            tax_year VARCHAR(4),
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            success BOOLEAN,
            records_processed INTEGER,
            records_created INTEGER,
            records_updated INTEGER,
            errors TEXT,
            parameters JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_sql)
            logger.info("NAV tables created/verified")
    
    async def bulk_insert_nav_parcels(self, records: List[Dict], tax_year: str) -> Dict:
        """Bulk insert NAV N (parcel) records"""
        if not self.pool:
            await self.connect()
        
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0
        }
        
        upsert_sql = """
        INSERT INTO nav_parcel_assessments (
            roll_type, county_number, pa_parcel_number, tc_account_number,
            tax_year, total_assessments, number_of_assessments,
            tax_roll_sequence_number, county_name
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (county_number, pa_parcel_number, tax_year)
        DO UPDATE SET
            total_assessments = EXCLUDED.total_assessments,
            number_of_assessments = EXCLUDED.number_of_assessments,
            tax_roll_sequence_number = EXCLUDED.tax_roll_sequence_number,
            updated_at = CURRENT_TIMESTAMP
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for record in records:
                    try:
                        cleaned_record = self._clean_nav_n_record(record, tax_year)
                        
                        # Check if exists
                        existing = await conn.fetchval(
                            "SELECT id FROM nav_parcel_assessments WHERE county_number = $1 AND pa_parcel_number = $2 AND tax_year = $3",
                            cleaned_record['county_number'],
                            cleaned_record['pa_parcel_number'], 
                            cleaned_record['tax_year']
                        )
                        
                        await conn.execute(upsert_sql, *self._prepare_nav_n_values(cleaned_record))
                        
                        if existing:
                            stats["updated"] += 1
                        else:
                            stats["created"] += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to insert NAV N record: {e}")
                        stats["failed"] += 1
        
        logger.info(f"NAV N bulk insert - Created: {stats['created']}, Updated: {stats['updated']}, Failed: {stats['failed']}")
        return stats
    
    async def bulk_insert_nav_details(self, records: List[Dict], tax_year: str) -> Dict:
        """Bulk insert NAV D (detail) records"""
        if not self.pool:
            await self.connect()
        
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0
        }
        
        insert_sql = """
        INSERT INTO nav_assessment_details (
            record_type, county_number, pa_parcel_number, levy_identifier,
            local_government_code, function_code, assessment_amount,
            tax_roll_sequence_number, county_name, function_description, tax_year
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for record in records:
                    try:
                        cleaned_record = self._clean_nav_d_record(record, tax_year)
                        await conn.execute(insert_sql, *self._prepare_nav_d_values(cleaned_record))
                        stats["created"] += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to insert NAV D record: {e}")
                        stats["failed"] += 1
        
        logger.info(f"NAV D bulk insert - Created: {stats['created']}, Failed: {stats['failed']}")
        return stats
    
    def _clean_nav_n_record(self, record: List, tax_year: str) -> Dict:
        """Clean NAV N record from CSV row"""
        def safe_decimal(value: str) -> Optional[float]:
            if not value or not str(value).strip():
                return None
            try:
                return float(str(value).strip().replace(',', ''))
            except (ValueError, TypeError):
                return None
        
        def safe_int(value: str) -> Optional[int]:
            if not value or not str(value).strip():
                return None
            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return None
        
        def clean_string(value: str) -> Optional[str]:
            if not value:
                return None
            cleaned = str(value).strip().strip('"')
            return cleaned if cleaned else None
        
        return {
            'roll_type': clean_string(record[0]) if len(record) > 0 else None,
            'county_number': clean_string(record[1]) if len(record) > 1 else None,
            'pa_parcel_number': clean_string(record[2]) if len(record) > 2 else None,
            'tc_account_number': clean_string(record[3]) if len(record) > 3 else None,
            'tax_year': tax_year,
            'total_assessments': safe_decimal(record[5]) if len(record) > 5 else None,
            'number_of_assessments': safe_int(record[6]) if len(record) > 6 else None,
            'tax_roll_sequence_number': safe_int(record[7]) if len(record) > 7 else None,
            'county_name': settings.get_county_name(clean_string(record[1]) if len(record) > 1 else "")
        }
    
    def _clean_nav_d_record(self, record: List, tax_year: str) -> Dict:
        """Clean NAV D record from CSV row"""
        def safe_decimal(value: str) -> Optional[float]:
            if not value or not str(value).strip():
                return None
            try:
                return float(str(value).strip().replace(',', ''))
            except (ValueError, TypeError):
                return None
        
        def safe_int(value: str) -> Optional[int]:
            if not value or not str(value).strip():
                return None
            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return None
        
        def clean_string(value: str) -> Optional[str]:
            if not value:
                return None
            cleaned = str(value).strip().strip('"')
            return cleaned if cleaned else None
        
        function_code = safe_int(record[5]) if len(record) > 5 else None
        
        return {
            'record_type': clean_string(record[0]) if len(record) > 0 else None,
            'county_number': clean_string(record[1]) if len(record) > 1 else None,
            'pa_parcel_number': clean_string(record[2]) if len(record) > 2 else None,
            'levy_identifier': clean_string(record[3]) if len(record) > 3 else None,
            'local_government_code': safe_int(record[4]) if len(record) > 4 else None,
            'function_code': function_code,
            'assessment_amount': safe_decimal(record[6]) if len(record) > 6 else None,
            'tax_roll_sequence_number': safe_int(record[7]) if len(record) > 7 else None,
            'county_name': settings.get_county_name(clean_string(record[1]) if len(record) > 1 else ""),
            'function_description': settings.get_function_description(function_code) if function_code else None,
            'tax_year': tax_year
        }
    
    def _prepare_nav_n_values(self, record: Dict) -> tuple:
        """Prepare NAV N values for SQL insert"""
        return (
            record.get('roll_type'),
            record.get('county_number'),
            record.get('pa_parcel_number'),
            record.get('tc_account_number'),
            record.get('tax_year'),
            record.get('total_assessments'),
            record.get('number_of_assessments'),
            record.get('tax_roll_sequence_number'),
            record.get('county_name')
        )
    
    def _prepare_nav_d_values(self, record: Dict) -> tuple:
        """Prepare NAV D values for SQL insert"""
        return (
            record.get('record_type'),
            record.get('county_number'),
            record.get('pa_parcel_number'),
            record.get('levy_identifier'),
            record.get('local_government_code'),
            record.get('function_code'),
            record.get('assessment_amount'),
            record.get('tax_roll_sequence_number'),
            record.get('county_name'),
            record.get('function_description'),
            record.get('tax_year')
        )
    
    async def get_assessment_summary(self, county_number: str = None, tax_year: str = None) -> Dict:
        """Get summary of assessments"""
        if not self.pool:
            await self.connect()
        
        where_clauses = []
        params = []
        param_count = 0
        
        if county_number:
            param_count += 1
            where_clauses.append(f"county_number = ${param_count}")
            params.append(county_number)
        
        if tax_year:
            param_count += 1  
            where_clauses.append(f"tax_year = ${param_count}")
            params.append(tax_year)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql = f"""
        SELECT 
            COUNT(*) as total_parcels,
            SUM(total_assessments) as total_assessment_amount,
            AVG(total_assessments) as avg_assessment_amount,
            MAX(total_assessments) as max_assessment_amount,
            SUM(number_of_assessments) as total_individual_assessments
        FROM nav_parcel_assessments 
        {where_clause}
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
            return dict(row) if row else {}
    
    async def get_top_assessed_parcels(self, county_number: str = None, tax_year: str = None, limit: int = 20) -> List[Dict]:
        """Get parcels with highest assessments"""
        if not self.pool:
            await self.connect()
        
        where_clauses = []
        params = []
        param_count = 0
        
        if county_number:
            param_count += 1
            where_clauses.append(f"county_number = ${param_count}")
            params.append(county_number)
        
        if tax_year:
            param_count += 1
            where_clauses.append(f"tax_year = ${param_count}")
            params.append(tax_year)
        
        param_count += 1
        params.append(limit)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql = f"""
        SELECT 
            pa_parcel_number,
            tc_account_number,
            county_name,
            tax_year,
            total_assessments,
            number_of_assessments
        FROM nav_parcel_assessments 
        {where_clause}
        ORDER BY total_assessments DESC 
        LIMIT ${param_count}
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def get_function_analysis(self, county_number: str = None, tax_year: str = None) -> List[Dict]:
        """Get analysis by function code"""
        if not self.pool:
            await self.connect()
        
        where_clauses = []
        params = []
        param_count = 0
        
        if county_number:
            param_count += 1
            where_clauses.append(f"county_number = ${param_count}")
            params.append(county_number)
        
        if tax_year:
            param_count += 1
            where_clauses.append(f"tax_year = ${param_count}")
            params.append(tax_year)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql = f"""
        SELECT 
            function_code,
            function_description,
            COUNT(*) as assessment_count,
            SUM(assessment_amount) as total_amount,
            AVG(assessment_amount) as avg_amount,
            COUNT(DISTINCT pa_parcel_number) as unique_parcels
        FROM nav_assessment_details 
        {where_clause}
        GROUP BY function_code, function_description 
        ORDER BY total_amount DESC
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def log_job(self, job_stats: Dict):
        """Log job execution"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO nav_jobs (
                    job_type, table_type, county_number, tax_year, started_at, finished_at, 
                    success, records_processed, records_created, records_updated, errors, parameters
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                job_stats.get('type', 'nav_assessments'),
                job_stats.get('table_type'),
                job_stats.get('county_number'),
                job_stats.get('tax_year'),
                datetime.fromisoformat(job_stats.get('started_at')) if job_stats.get('started_at') else None,
                datetime.fromisoformat(job_stats.get('finished_at')) if job_stats.get('finished_at') else None,
                job_stats.get('success', False),
                job_stats.get('records_processed', 0),
                job_stats.get('records_created', 0),
                job_stats.get('records_updated', 0),
                json.dumps(job_stats.get('errors', [])) if job_stats.get('errors') else None,
                json.dumps({
                    'counties': job_stats.get('counties', []),
                    'files_processed': job_stats.get('files_processed', 0)
                })
            )