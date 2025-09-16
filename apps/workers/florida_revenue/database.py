"""
Database operations for Florida Revenue TPP data
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

class FloridaRevenueDB:
    """Database operations for Florida Revenue TPP data"""
    
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
            logger.info("Florida Revenue DB pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Florida Revenue DB pool closed")
    
    async def create_tpp_tables(self):
        """Create TPP data tables if they don't exist"""
        if not self.pool:
            await self.connect()
        
        create_sql = """
        CREATE TABLE IF NOT EXISTS tpp_properties (
            id SERIAL PRIMARY KEY,
            
            -- Core identifiers
            county_number VARCHAR(10),
            account_id VARCHAR(50) UNIQUE,
            file_type VARCHAR(10),
            assessment_year VARCHAR(4),
            tax_authority_code VARCHAR(10),
            naics_code VARCHAR(10),
            
            -- Valuation fields
            jv_furniture_fixtures DECIMAL(15,2),
            jv_leasehold_improvements DECIMAL(15,2),
            jv_total DECIMAL(15,2),
            av_total DECIMAL(15,2),
            jv_pollution_control DECIMAL(15,2),
            av_pollution_control DECIMAL(15,2),
            exempt_value DECIMAL(15,2),
            taxable_value DECIMAL(15,2),
            penalty_rate DECIMAL(8,4),
            
            -- Owner information
            owner_name VARCHAR(500),
            owner_address VARCHAR(300),
            owner_city VARCHAR(100),
            owner_state VARCHAR(10),
            owner_zip VARCHAR(20),
            owner_state_domicile VARCHAR(10),
            
            -- Fiduciary information
            fiduciary_name VARCHAR(300),
            fiduciary_address VARCHAR(300),
            fiduciary_city VARCHAR(100),
            fiduciary_state VARCHAR(10),
            fiduciary_zip VARCHAR(20),
            fiduciary_code VARCHAR(50),
            
            -- Physical location
            physical_address VARCHAR(300),
            physical_city VARCHAR(100),
            physical_zip VARCHAR(20),
            
            -- Administrative
            exemption_codes TEXT,
            sequence_number INTEGER,
            timestamp_id VARCHAR(50),
            
            -- Metadata
            data_source VARCHAR(100) DEFAULT 'florida_revenue_tpp',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Indexes
            UNIQUE(account_id, assessment_year)
        );
        
        CREATE INDEX IF NOT EXISTS idx_tpp_owner_name ON tpp_properties(owner_name);
        CREATE INDEX IF NOT EXISTS idx_tpp_naics_code ON tpp_properties(naics_code);
        CREATE INDEX IF NOT EXISTS idx_tpp_physical_city ON tpp_properties(physical_city);
        CREATE INDEX IF NOT EXISTS idx_tpp_jv_total ON tpp_properties(jv_total);
        CREATE INDEX IF NOT EXISTS idx_tpp_assessment_year ON tpp_properties(assessment_year);
        CREATE INDEX IF NOT EXISTS idx_tpp_account_id ON tpp_properties(account_id);
        
        -- Create jobs table for tracking loads
        CREATE TABLE IF NOT EXISTS tpp_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50),
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
            logger.info("TPP tables created/verified")
    
    async def bulk_insert_tpp_records(self, records: List[Dict]) -> Dict:
        """Bulk insert TPP records with upsert logic"""
        if not self.pool:
            await self.connect()
        
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0,
            "skipped": 0
        }
        
        upsert_sql = """
        INSERT INTO tpp_properties (
            county_number, account_id, file_type, assessment_year, tax_authority_code,
            naics_code, jv_furniture_fixtures, jv_leasehold_improvements, jv_total,
            av_total, jv_pollution_control, av_pollution_control, exempt_value,
            taxable_value, penalty_rate, owner_name, owner_address, owner_city,
            owner_state, owner_zip, owner_state_domicile, fiduciary_name,
            fiduciary_address, fiduciary_city, fiduciary_state, fiduciary_zip,
            fiduciary_code, physical_address, physical_city, physical_zip,
            exemption_codes, sequence_number, timestamp_id
        ) VALUES (
            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
            $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26, $27, $28, $29, $30,
            $31, $32, $33
        )
        ON CONFLICT (account_id, assessment_year) 
        DO UPDATE SET
            owner_name = EXCLUDED.owner_name,
            owner_address = EXCLUDED.owner_address,
            owner_city = EXCLUDED.owner_city,
            owner_state = EXCLUDED.owner_state,
            owner_zip = EXCLUDED.owner_zip,
            physical_address = EXCLUDED.physical_address,
            physical_city = EXCLUDED.physical_city,
            physical_zip = EXCLUDED.physical_zip,
            jv_total = EXCLUDED.jv_total,
            av_total = EXCLUDED.av_total,
            taxable_value = EXCLUDED.taxable_value,
            updated_at = CURRENT_TIMESTAMP
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for record in records:
                    try:
                        # Clean and prepare data
                        cleaned_record = self._clean_record(record)
                        
                        # Check if record exists
                        existing = await conn.fetchval(
                            "SELECT id FROM tpp_properties WHERE account_id = $1 AND assessment_year = $2",
                            cleaned_record['account_id'],
                            cleaned_record['assessment_year']
                        )
                        
                        # Execute upsert
                        await conn.execute(upsert_sql, *self._prepare_record_values(cleaned_record))
                        
                        if existing:
                            stats["updated"] += 1
                        else:
                            stats["created"] += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to insert record {record.get('ACCT_ID', 'unknown')}: {e}")
                        stats["failed"] += 1
        
        logger.info(f"TPP bulk insert complete - Created: {stats['created']}, "
                   f"Updated: {stats['updated']}, Failed: {stats['failed']}")
        
        return stats
    
    def _clean_record(self, raw_record: Dict) -> Dict:
        """Clean and normalize a TPP record"""
        def safe_decimal(value: str) -> Optional[float]:
            """Safely convert string to decimal"""
            if not value or not str(value).strip():
                return None
            try:
                return float(str(value).strip().replace(',', ''))
            except (ValueError, TypeError):
                return None
        
        def safe_int(value: str) -> Optional[int]:
            """Safely convert string to integer"""
            if not value or not str(value).strip():
                return None
            try:
                return int(str(value).strip())
            except (ValueError, TypeError):
                return None
        
        def clean_string(value: str) -> Optional[str]:
            """Clean string value"""
            if not value:
                return None
            cleaned = str(value).strip().strip('"')
            return cleaned if cleaned else None
        
        return {
            'county_number': clean_string(raw_record.get('CO_NO')),
            'account_id': clean_string(raw_record.get('ACCT_ID')),
            'file_type': clean_string(raw_record.get('FILE_T')),
            'assessment_year': clean_string(raw_record.get('ASMNT_YR')),
            'tax_authority_code': clean_string(raw_record.get('TAX_AUTH_CD')),
            'naics_code': clean_string(raw_record.get('NAICS_CD')),
            'jv_furniture_fixtures': safe_decimal(raw_record.get('JV_F_F_E')),
            'jv_leasehold_improvements': safe_decimal(raw_record.get('JV_LESE_IMP')),
            'jv_total': safe_decimal(raw_record.get('JV_TOTAL')),
            'av_total': safe_decimal(raw_record.get('AV_TOTAL')),
            'jv_pollution_control': safe_decimal(raw_record.get('JV_POL_CONTRL')),
            'av_pollution_control': safe_decimal(raw_record.get('AV_POL_CONTRL')),
            'exempt_value': safe_decimal(raw_record.get('EXMPT_VAL')),
            'taxable_value': safe_decimal(raw_record.get('TAX_VAL')),
            'penalty_rate': safe_decimal(raw_record.get('PEN_RATE')),
            'owner_name': clean_string(raw_record.get('OWN_NAM')),
            'owner_address': clean_string(raw_record.get('OWN_ADDR')),
            'owner_city': clean_string(raw_record.get('OWN_CITY')),
            'owner_state': clean_string(raw_record.get('OWN_STATE')),
            'owner_zip': clean_string(raw_record.get('OWN_ZIPCD')),
            'owner_state_domicile': clean_string(raw_record.get('OWN_STATE_DOM')),
            'fiduciary_name': clean_string(raw_record.get('FIDU_NAME')),
            'fiduciary_address': clean_string(raw_record.get('FIDU_ADDR')),
            'fiduciary_city': clean_string(raw_record.get('FIDU_CITY')),
            'fiduciary_state': clean_string(raw_record.get('FIDU_STATE')),
            'fiduciary_zip': clean_string(raw_record.get('FIDU_ZIPCD')),
            'fiduciary_code': clean_string(raw_record.get('FIDU_CD')),
            'physical_address': clean_string(raw_record.get('PHY_ADDR')),
            'physical_city': clean_string(raw_record.get('PHY_CITY')),
            'physical_zip': clean_string(raw_record.get('PHY_ZIPCD')),
            'exemption_codes': clean_string(raw_record.get('EXMPT')),
            'sequence_number': safe_int(raw_record.get('SEQ_NO')),
            'timestamp_id': clean_string(raw_record.get('TS_ID'))
        }
    
    def _prepare_record_values(self, record: Dict) -> tuple:
        """Prepare record values for SQL insert"""
        return (
            record.get('county_number'),
            record.get('account_id'),
            record.get('file_type'),
            record.get('assessment_year'),
            record.get('tax_authority_code'),
            record.get('naics_code'),
            record.get('jv_furniture_fixtures'),
            record.get('jv_leasehold_improvements'),
            record.get('jv_total'),
            record.get('av_total'),
            record.get('jv_pollution_control'),
            record.get('av_pollution_control'),
            record.get('exempt_value'),
            record.get('taxable_value'),
            record.get('penalty_rate'),
            record.get('owner_name'),
            record.get('owner_address'),
            record.get('owner_city'),
            record.get('owner_state'),
            record.get('owner_zip'),
            record.get('owner_state_domicile'),
            record.get('fiduciary_name'),
            record.get('fiduciary_address'),
            record.get('fiduciary_city'),
            record.get('fiduciary_state'),
            record.get('fiduciary_zip'),
            record.get('fiduciary_code'),
            record.get('physical_address'),
            record.get('physical_city'),
            record.get('physical_zip'),
            record.get('exemption_codes'),
            record.get('sequence_number'),
            record.get('timestamp_id')
        )
    
    async def get_top_owners(self, limit: int = 20) -> List[Dict]:
        """Get top property owners by count"""
        if not self.pool:
            await self.connect()
        
        sql = """
        SELECT 
            owner_name,
            COUNT(*) as property_count,
            SUM(jv_total) as total_value,
            AVG(jv_total) as avg_value,
            MAX(jv_total) as max_value
        FROM tpp_properties 
        WHERE owner_name IS NOT NULL
        GROUP BY owner_name 
        ORDER BY property_count DESC 
        LIMIT $1
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, limit)
            return [dict(row) for row in rows]
    
    async def get_naics_analysis(self, limit: int = 20) -> List[Dict]:
        """Get NAICS code analysis"""
        if not self.pool:
            await self.connect()
        
        sql = """
        SELECT 
            naics_code,
            COUNT(*) as record_count,
            SUM(jv_total) as total_value,
            AVG(jv_total) as avg_value
        FROM tpp_properties 
        WHERE naics_code IS NOT NULL
        GROUP BY naics_code 
        ORDER BY record_count DESC 
        LIMIT $1
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, limit)
            return [dict(row) for row in rows]
    
    async def log_job(self, job_stats: Dict):
        """Log job execution"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO tpp_jobs (
                    job_type, started_at, finished_at, success, 
                    records_processed, records_created, records_updated, errors, parameters
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                job_stats.get('type', 'florida_revenue_tpp'),
                datetime.fromisoformat(job_stats.get('started_at')) if job_stats.get('started_at') else None,
                datetime.fromisoformat(job_stats.get('finished_at')) if job_stats.get('finished_at') else None,
                job_stats.get('success', False),
                job_stats.get('records_processed', 0),
                job_stats.get('records_created', 0),
                job_stats.get('records_updated', 0),
                json.dumps(job_stats.get('errors', [])) if job_stats.get('errors') else None,
                json.dumps({
                    'year': job_stats.get('year'),
                    'data_fields': len(job_stats.get('data_fields', [])),
                    'total_value': job_stats.get('value_analysis', {}).get('total_value', 0)
                })
            )