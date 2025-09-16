"""
Database operations for SDF (Sales Data File) data
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import asyncpg
from asyncpg.pool import Pool
from decimal import Decimal

try:
    from .config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)

class SDFSalesDB:
    """Database operations for SDF Sales data"""
    
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
            logger.info("SDF Sales DB pool created")
    
    async def disconnect(self):
        """Close connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("SDF Sales DB pool closed")
    
    async def create_sdf_tables(self):
        """Create SDF data tables if they don't exist"""
        if not self.pool:
            await self.connect()
        
        create_sql = """
        -- SDF Sales Table
        CREATE TABLE IF NOT EXISTS sdf_sales (
            id SERIAL PRIMARY KEY,
            
            -- Core identifiers
            county_number VARCHAR(10),
            parcel_id VARCHAR(50),
            assessment_year INTEGER,
            
            -- Property characteristics
            atv_start INTEGER,
            group_number INTEGER,
            dor_use_code VARCHAR(10),
            neighborhood_code VARCHAR(20),
            market_area VARCHAR(10),
            census_block VARCHAR(20),
            
            -- Sale information
            sale_id_code VARCHAR(50),
            sale_change_code VARCHAR(10),
            validity_indicator VARCHAR(5),
            or_book VARCHAR(20),
            or_page VARCHAR(20),
            clerk_number VARCHAR(50),
            qualification_code VARCHAR(10),
            sale_year INTEGER,
            sale_month INTEGER,
            sale_price DECIMAL(15,2),
            
            -- Additional fields
            multi_parcel_sale VARCHAR(5),
            rs_id VARCHAR(20),
            mp_id VARCHAR(20),
            state_parcel_id VARCHAR(100),
            
            -- Enriched data
            qualification_type VARCHAR(50),
            qualification_description VARCHAR(200),
            is_qualified_sale BOOLEAN,
            is_distressed_sale BOOLEAN,
            is_arms_length BOOLEAN,
            is_financial_institution BOOLEAN,
            dor_use_description VARCHAR(100),
            sale_date DATE,
            
            -- Metadata
            data_source VARCHAR(100) DEFAULT 'florida_revenue_sdf',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            UNIQUE(county_number, parcel_id, sale_id_code, assessment_year)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_sdf_parcel_id ON sdf_sales(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_year_month ON sdf_sales(sale_year, sale_month);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_price ON sdf_sales(sale_price);
        CREATE INDEX IF NOT EXISTS idx_sdf_qualification_code ON sdf_sales(qualification_code);
        CREATE INDEX IF NOT EXISTS idx_sdf_neighborhood ON sdf_sales(neighborhood_code);
        CREATE INDEX IF NOT EXISTS idx_sdf_dor_use ON sdf_sales(dor_use_code);
        CREATE INDEX IF NOT EXISTS idx_sdf_distressed ON sdf_sales(is_distressed_sale) WHERE is_distressed_sale = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sdf_qualified ON sdf_sales(is_qualified_sale) WHERE is_qualified_sale = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sdf_financial ON sdf_sales(is_financial_institution) WHERE is_financial_institution = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_date ON sdf_sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sdf_state_parcel ON sdf_sales(state_parcel_id);
        
        -- Analytics view for market analysis
        CREATE OR REPLACE VIEW sdf_market_analysis AS
        SELECT 
            neighborhood_code,
            sale_year,
            sale_month,
            qualification_code,
            qualification_type,
            COUNT(*) as transaction_count,
            AVG(CASE WHEN sale_price > 1000 THEN sale_price END) as avg_sale_price,
            MEDIAN(CASE WHEN sale_price > 1000 THEN sale_price END) as median_sale_price,
            MAX(sale_price) as max_sale_price,
            MIN(CASE WHEN sale_price > 1000 THEN sale_price END) as min_sale_price,
            SUM(CASE WHEN is_distressed_sale THEN 1 ELSE 0 END) as distressed_count,
            SUM(CASE WHEN is_financial_institution THEN 1 ELSE 0 END) as bank_sales_count
        FROM sdf_sales
        GROUP BY neighborhood_code, sale_year, sale_month, qualification_code, qualification_type;
        
        -- Jobs table for tracking loads
        CREATE TABLE IF NOT EXISTS sdf_jobs (
            id SERIAL PRIMARY KEY,
            job_type VARCHAR(50),
            county_number VARCHAR(10),
            assessment_year VARCHAR(10),
            started_at TIMESTAMP,
            finished_at TIMESTAMP,
            success BOOLEAN,
            records_processed INTEGER,
            records_created INTEGER,
            records_updated INTEGER,
            distressed_sales_found INTEGER,
            errors TEXT,
            parameters JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(create_sql)
            logger.info("SDF tables created/verified")
    
    async def bulk_insert_sdf_sales(self, records: List[Dict]) -> Dict:
        """Bulk insert SDF sales records"""
        if not self.pool:
            await self.connect()
        
        stats = {
            "created": 0,
            "updated": 0,
            "failed": 0,
            "distressed": 0,
            "qualified": 0,
            "bank_sales": 0
        }
        
        upsert_sql = """
        INSERT INTO sdf_sales (
            county_number, parcel_id, assessment_year, atv_start, group_number,
            dor_use_code, neighborhood_code, market_area, census_block,
            sale_id_code, sale_change_code, validity_indicator, or_book, or_page,
            clerk_number, qualification_code, sale_year, sale_month, sale_price,
            multi_parcel_sale, rs_id, mp_id, state_parcel_id,
            qualification_type, qualification_description, is_qualified_sale,
            is_distressed_sale, is_arms_length, is_financial_institution,
            dor_use_description, sale_date
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                 $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25, $26,
                 $27, $28, $29, $30, $31)
        ON CONFLICT (county_number, parcel_id, sale_id_code, assessment_year)
        DO UPDATE SET
            sale_price = EXCLUDED.sale_price,
            qualification_code = EXCLUDED.qualification_code,
            updated_at = CURRENT_TIMESTAMP
        """
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                for record in records:
                    try:
                        cleaned_record = self._clean_sdf_record(record)
                        
                        # Track statistics
                        if cleaned_record['is_distressed_sale']:
                            stats['distressed'] += 1
                        if cleaned_record['is_qualified_sale']:
                            stats['qualified'] += 1
                        if cleaned_record['is_financial_institution']:
                            stats['bank_sales'] += 1
                        
                        # Check if exists
                        existing = await conn.fetchval(
                            """SELECT id FROM sdf_sales 
                            WHERE county_number = $1 AND parcel_id = $2 
                            AND sale_id_code = $3 AND assessment_year = $4""",
                            cleaned_record['county_number'],
                            cleaned_record['parcel_id'],
                            cleaned_record['sale_id_code'],
                            cleaned_record['assessment_year']
                        )
                        
                        await conn.execute(upsert_sql, *self._prepare_sdf_values(cleaned_record))
                        
                        if existing:
                            stats["updated"] += 1
                        else:
                            stats["created"] += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to insert SDF record: {e}")
                        stats["failed"] += 1
        
        logger.info(f"SDF bulk insert - Created: {stats['created']}, Updated: {stats['updated']}, "
                   f"Failed: {stats['failed']}, Distressed: {stats['distressed']}, "
                   f"Bank sales: {stats['bank_sales']}")
        return stats
    
    def _clean_sdf_record(self, record: Dict) -> Dict:
        """Clean and enrich SDF record"""
        def safe_int(value: str) -> Optional[int]:
            if not value or not str(value).strip():
                return None
            try:
                cleaned = str(value).strip().strip('"')
                return int(cleaned) if cleaned else None
            except (ValueError, TypeError):
                return None
        
        def safe_decimal(value: str) -> Optional[float]:
            if not value or not str(value).strip():
                return None
            try:
                cleaned = str(value).strip().strip('"').replace(',', '')
                return float(cleaned) if cleaned else None
            except (ValueError, TypeError):
                return None
        
        def clean_string(value: str) -> Optional[str]:
            if not value:
                return None
            cleaned = str(value).strip().strip('"')
            return cleaned if cleaned else None
        
        # Basic cleaning
        cleaned = {
            'county_number': clean_string(record.get('CO_NO')),
            'parcel_id': clean_string(record.get('PARCEL_ID')),
            'assessment_year': safe_int(record.get('ASMNT_YR')),
            'atv_start': safe_int(record.get('ATV_STRT')),
            'group_number': safe_int(record.get('GRP_NO')),
            'dor_use_code': clean_string(record.get('DOR_UC')),
            'neighborhood_code': clean_string(record.get('NBRHD_CD')),
            'market_area': clean_string(record.get('MKT_AR')),
            'census_block': clean_string(record.get('CENSUS_BK')),
            'sale_id_code': clean_string(record.get('SALE_ID_CD')),
            'sale_change_code': clean_string(record.get('SAL_CHG_CD')),
            'validity_indicator': clean_string(record.get('VI_CD')),
            'or_book': clean_string(record.get('OR_BOOK')),
            'or_page': clean_string(record.get('OR_PAGE')),
            'clerk_number': clean_string(record.get('CLERK_NO')),
            'qualification_code': clean_string(record.get('QUAL_CD')),
            'sale_year': safe_int(record.get('SALE_YR')),
            'sale_month': safe_int(record.get('SALE_MO')),
            'sale_price': safe_decimal(record.get('SALE_PRC')),
            'multi_parcel_sale': clean_string(record.get('MULTI_PAR_SAL')),
            'rs_id': clean_string(record.get('RS_ID')),
            'mp_id': clean_string(record.get('MP_ID')),
            'state_parcel_id': clean_string(record.get('STATE_PARCEL_ID'))
        }
        
        # Enrich with qualification info
        qual_code = cleaned['qualification_code']
        qual_info = settings.get_qualification_info(qual_code) if qual_code else {}
        cleaned['qualification_type'] = qual_info.get('type')
        cleaned['qualification_description'] = qual_info.get('description')
        cleaned['is_qualified_sale'] = settings.is_qualified_sale(qual_code) if qual_code else False
        cleaned['is_distressed_sale'] = settings.is_distressed_sale(qual_code) if qual_code else False
        cleaned['is_arms_length'] = qual_code == '01'
        cleaned['is_financial_institution'] = qual_code in ['11', '12']
        
        # Enrich with DOR use description
        dor_code = cleaned['dor_use_code']
        cleaned['dor_use_description'] = settings.get_dor_use_description(dor_code) if dor_code else None
        
        # Create sale date
        if cleaned['sale_year'] and cleaned['sale_month']:
            try:
                cleaned['sale_date'] = datetime(cleaned['sale_year'], cleaned['sale_month'], 1)
            except:
                cleaned['sale_date'] = None
        else:
            cleaned['sale_date'] = None
        
        return cleaned
    
    def _prepare_sdf_values(self, record: Dict) -> tuple:
        """Prepare SDF values for SQL insert"""
        return (
            record.get('county_number'),
            record.get('parcel_id'),
            record.get('assessment_year'),
            record.get('atv_start'),
            record.get('group_number'),
            record.get('dor_use_code'),
            record.get('neighborhood_code'),
            record.get('market_area'),
            record.get('census_block'),
            record.get('sale_id_code'),
            record.get('sale_change_code'),
            record.get('validity_indicator'),
            record.get('or_book'),
            record.get('or_page'),
            record.get('clerk_number'),
            record.get('qualification_code'),
            record.get('sale_year'),
            record.get('sale_month'),
            record.get('sale_price'),
            record.get('multi_parcel_sale'),
            record.get('rs_id'),
            record.get('mp_id'),
            record.get('state_parcel_id'),
            record.get('qualification_type'),
            record.get('qualification_description'),
            record.get('is_qualified_sale'),
            record.get('is_distressed_sale'),
            record.get('is_arms_length'),
            record.get('is_financial_institution'),
            record.get('dor_use_description'),
            record.get('sale_date')
        )
    
    async def get_market_summary(self, county_number: str = None, 
                                 year: int = None, month: int = None) -> Dict:
        """Get market summary statistics"""
        if not self.pool:
            await self.connect()
        
        where_clauses = []
        params = []
        param_count = 0
        
        if county_number:
            param_count += 1
            where_clauses.append(f"county_number = ${param_count}")
            params.append(county_number)
        
        if year:
            param_count += 1
            where_clauses.append(f"sale_year = ${param_count}")
            params.append(year)
        
        if month:
            param_count += 1
            where_clauses.append(f"sale_month = ${param_count}")
            params.append(month)
        
        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        sql = f"""
        SELECT 
            COUNT(*) as total_sales,
            COUNT(DISTINCT parcel_id) as unique_properties,
            SUM(CASE WHEN is_qualified_sale THEN 1 ELSE 0 END) as qualified_sales,
            SUM(CASE WHEN is_distressed_sale THEN 1 ELSE 0 END) as distressed_sales,
            SUM(CASE WHEN is_financial_institution THEN 1 ELSE 0 END) as bank_sales,
            SUM(CASE WHEN is_arms_length THEN 1 ELSE 0 END) as arms_length_sales,
            AVG(CASE WHEN sale_price > 1000 THEN sale_price END) as avg_sale_price,
            MAX(sale_price) as max_sale_price,
            MIN(CASE WHEN sale_price > 1000 THEN sale_price END) as min_sale_price,
            SUM(sale_price) as total_volume
        FROM sdf_sales 
        {where_clause}
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql, *params)
            return dict(row) if row else {}
    
    async def get_distressed_properties(self, limit: int = 100) -> List[Dict]:
        """Get recent distressed property sales"""
        if not self.pool:
            await self.connect()
        
        sql = """
        SELECT 
            parcel_id,
            state_parcel_id,
            sale_date,
            sale_price,
            qualification_code,
            qualification_description,
            dor_use_description,
            neighborhood_code
        FROM sdf_sales 
        WHERE is_distressed_sale = TRUE
        AND sale_price > 1000
        ORDER BY sale_date DESC 
        LIMIT $1
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, limit)
            return [dict(row) for row in rows]
    
    async def get_neighborhood_analysis(self, neighborhood_code: str = None) -> List[Dict]:
        """Get neighborhood sales analysis"""
        if not self.pool:
            await self.connect()
        
        where_clause = "WHERE neighborhood_code = $1" if neighborhood_code else ""
        params = [neighborhood_code] if neighborhood_code else []
        
        sql = f"""
        SELECT 
            neighborhood_code,
            sale_year,
            sale_month,
            COUNT(*) as sales_count,
            AVG(CASE WHEN sale_price > 1000 THEN sale_price END) as avg_price,
            SUM(CASE WHEN is_distressed_sale THEN 1 ELSE 0 END) as distressed_count,
            ROUND(100.0 * SUM(CASE WHEN is_distressed_sale THEN 1 ELSE 0 END) / COUNT(*), 2) as distress_rate
        FROM sdf_sales 
        {where_clause}
        GROUP BY neighborhood_code, sale_year, sale_month 
        ORDER BY sale_year DESC, sale_month DESC
        LIMIT 24
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def find_flip_candidates(self, months_back: int = 24) -> List[Dict]:
        """Find properties sold multiple times (potential flips)"""
        if not self.pool:
            await self.connect()
        
        sql = """
        WITH multiple_sales AS (
            SELECT 
                parcel_id,
                COUNT(*) as sale_count,
                MIN(sale_price) as min_price,
                MAX(sale_price) as max_price,
                MAX(sale_price) - MIN(sale_price) as price_delta,
                MIN(sale_date) as first_sale,
                MAX(sale_date) as last_sale,
                EXTRACT(DAY FROM MAX(sale_date) - MIN(sale_date)) as days_held
            FROM sdf_sales
            WHERE sale_date >= CURRENT_DATE - INTERVAL '%s months'
            AND sale_price > 1000
            GROUP BY parcel_id
            HAVING COUNT(*) > 1
        )
        SELECT 
            ms.*,
            s1.qualification_code as first_qual_code,
            s2.qualification_code as last_qual_code,
            s1.dor_use_description,
            s1.neighborhood_code
        FROM multiple_sales ms
        JOIN sdf_sales s1 ON ms.parcel_id = s1.parcel_id AND ms.first_sale = s1.sale_date
        JOIN sdf_sales s2 ON ms.parcel_id = s2.parcel_id AND ms.last_sale = s2.sale_date
        WHERE ms.price_delta > 0
        ORDER BY ms.price_delta DESC
        LIMIT 100
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, months_back)
            return [dict(row) for row in rows]
    
    async def log_job(self, job_stats: Dict):
        """Log job execution"""
        if not self.pool:
            await self.connect()
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sdf_jobs (
                    job_type, county_number, assessment_year, started_at, finished_at, 
                    success, records_processed, records_created, records_updated,
                    distressed_sales_found, errors, parameters
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                job_stats.get('type', 'sdf_sales'),
                job_stats.get('county_number'),
                job_stats.get('assessment_year'),
                datetime.fromisoformat(job_stats.get('started_at')) if job_stats.get('started_at') else None,
                datetime.fromisoformat(job_stats.get('finished_at')) if job_stats.get('finished_at') else None,
                job_stats.get('success', False),
                job_stats.get('records_processed', 0),
                job_stats.get('records_created', 0),
                job_stats.get('records_updated', 0),
                job_stats.get('distressed_sales_found', 0),
                json.dumps(job_stats.get('errors', [])) if job_stats.get('errors') else None,
                json.dumps({
                    'year': job_stats.get('year'),
                    'qualified_sales': job_stats.get('qualified_sales', 0),
                    'bank_sales': job_stats.get('bank_sales', 0)
                })
            )