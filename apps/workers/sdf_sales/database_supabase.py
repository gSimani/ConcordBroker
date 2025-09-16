"""
SDF Sales Database Module for Supabase
Handles all SDF sales data operations in Supabase
"""

import asyncpg
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_supabase_db import BaseSupabaseDB
from config import settings

logger = logging.getLogger(__name__)

class SDFSupabaseDB(BaseSupabaseDB):
    """SDF Sales-specific Supabase database operations"""
    
    def __init__(self):
        super().__init__('sdf_sales')
        self.table_name = 'fl_sdf_sales'
    
    async def create_tables(self):
        """Create SDF-specific tables (already in migration)"""
        # Tables are created via Supabase migration
        # Add any runtime table for major owners tracking
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS fl_major_owners (
                    owner_name TEXT,
                    property_count INTEGER,
                    total_value DECIMAL,
                    data_source TEXT,
                    last_updated TIMESTAMPTZ,
                    PRIMARY KEY (owner_name, data_source)
                )
            """)
    
    async def bulk_insert_sdf_sales(self, sales: List[Dict]) -> Dict:
        """Bulk insert SDF sales to Supabase"""
        
        stats = {
            'created': 0,
            'updated': 0,
            'distressed': 0,
            'qualified': 0,
            'bank_sales': 0
        }
        
        # Prepare records
        for sale in sales:
            # Clean and prepare data
            sale['county_number'] = sale.get('CO_NO', '').strip('"')
            sale['parcel_id'] = sale.get('PARCEL_ID', '').strip('"')
            sale['assessment_year'] = int(sale.get('ASMNT_YR', 0))
            sale['sale_year'] = int(sale.get('SALE_YR', 0))
            sale['sale_month'] = int(sale.get('SALE_MO', 0)) if sale.get('SALE_MO') else None
            
            # Process qualification code
            qual_code = sale.get('QUAL_CD', '').strip('"')
            sale['qualification_code'] = qual_code
            sale['qualification_description'] = settings.get_qualification_info(qual_code)['description']
            
            # Determine sale types
            sale['is_qualified_sale'] = settings.is_qualified_sale(qual_code)
            sale['is_distressed_sale'] = settings.is_distressed_sale(qual_code)
            sale['is_bank_sale'] = qual_code in ['11', '12']  # Bank/REO sales
            
            if sale['is_distressed_sale']:
                stats['distressed'] += 1
            if sale['is_qualified_sale']:
                stats['qualified'] += 1
            if sale['is_bank_sale']:
                stats['bank_sales'] += 1
            
            # Parse sale price
            try:
                sale['sale_price'] = float(sale.get('SALE_PRC', '0').strip('"').replace(',', ''))
            except:
                sale['sale_price'] = 0
            
            # Other fields
            sale['dor_use_code'] = sale.get('DOR_UC', '').strip('"')
            sale['neighborhood_code'] = sale.get('NBRHD_CD', '').strip('"')
            sale['market_area'] = sale.get('MKT_AR', '').strip('"')
            sale['sale_id_code'] = sale.get('SALE_ID_CD', '').strip('"')
            sale['clerk_number'] = sale.get('CLERK_NO', '').strip('"')
            sale['multi_parcel_sale'] = sale.get('MULTI_PAR_SAL', '').strip('"')
            sale['state_parcel_id'] = sale.get('STATE_PARCEL_ID', '').strip('"')
            
            sale['created_at'] = datetime.now()
            sale['updated_at'] = datetime.now()
        
        # Bulk upsert to Supabase
        db_stats = await self.bulk_upsert(
            self.table_name,
            sales,
            unique_columns=['county_number', 'parcel_id', 'sale_id_code']
        )
        
        stats['created'] = db_stats['created']
        stats['updated'] = db_stats['updated']
        
        # Track distressed properties
        await self.track_distressed_properties(sales)
        
        # Identify potential flips
        await self.identify_flip_candidates(sales)
        
        return stats
    
    async def track_distressed_properties(self, sales: List[Dict]):
        """Track distressed property sales"""
        distressed_sales = [
            s for s in sales 
            if s.get('is_distressed_sale') and s.get('sale_price', 0) > 1000
        ]
        
        if distressed_sales:
            logger.info(f"Tracking {len(distressed_sales)} distressed sales")
            
            # Store in tracking table for alerts
            async with self.pool.acquire() as conn:
                for sale in distressed_sales[:100]:  # Top 100
                    await conn.execute("""
                        INSERT INTO fl_distressed_alerts (
                            parcel_id, sale_date, sale_price, 
                            qualification_code, neighborhood_code,
                            alert_status, created_at
                        ) VALUES ($1, $2, $3, $4, $5, 'new', NOW())
                        ON CONFLICT (parcel_id, sale_date) DO NOTHING
                    """, sale['parcel_id'], 
                        datetime(sale['sale_year'], sale.get('sale_month', 1), 1),
                        sale['sale_price'], 
                        sale['qualification_code'],
                        sale['neighborhood_code'])
    
    async def identify_flip_candidates(self, sales: List[Dict]):
        """Identify properties sold multiple times (flip candidates)"""
        # Group sales by parcel
        parcel_sales = {}
        for sale in sales:
            parcel = sale.get('parcel_id')
            if parcel and sale.get('sale_price', 0) > 1000:
                if parcel not in parcel_sales:
                    parcel_sales[parcel] = []
                parcel_sales[parcel].append(sale)
        
        # Find properties sold 2+ times
        flip_candidates = []
        for parcel, sales_list in parcel_sales.items():
            if len(sales_list) >= 2:
                # Sort by date
                sales_list.sort(key=lambda x: (x.get('sale_year', 0), x.get('sale_month', 0)))
                
                # Calculate flip metrics
                first_sale = sales_list[0]
                last_sale = sales_list[-1]
                
                price_delta = last_sale['sale_price'] - first_sale['sale_price']
                
                # Calculate days between sales
                first_date = datetime(first_sale['sale_year'], first_sale.get('sale_month', 1), 1)
                last_date = datetime(last_sale['sale_year'], last_sale.get('sale_month', 1), 1)
                days_held = (last_date - first_date).days
                
                if price_delta > 0 and days_held > 0:
                    flip_candidates.append({
                        'parcel_id': parcel,
                        'buy_price': first_sale['sale_price'],
                        'sell_price': last_sale['sale_price'],
                        'price_delta': price_delta,
                        'days_held': days_held,
                        'roi_percent': (price_delta / first_sale['sale_price']) * 100
                    })
        
        if flip_candidates:
            logger.info(f"Identified {len(flip_candidates)} potential flips")
    
    async def get_market_summary(self, county_number: str = None, 
                                year: int = None, month: int = None) -> Dict:
        """Get market summary statistics from materialized view"""
        async with self.pool.acquire() as conn:
            # Use materialized view for performance
            where_clauses = []
            params = []
            
            if county_number:
                where_clauses.append(f"county_number = ${len(params) + 1}")
                params.append(county_number)
            
            if year:
                where_clauses.append(f"EXTRACT(YEAR FROM month) = ${len(params) + 1}")
                params.append(year)
            
            if month:
                where_clauses.append(f"EXTRACT(MONTH FROM month) = ${len(params) + 1}")
                params.append(month)
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            result = await conn.fetchrow(f"""
                SELECT
                    COUNT(*) as months_count,
                    SUM(total_sales) as total_sales,
                    SUM(unique_properties) as unique_properties,
                    SUM(distressed_sales) as distressed_sales,
                    SUM(bank_sales) as bank_sales,
                    AVG(avg_sale_price) as avg_sale_price,
                    SUM(total_volume) as total_volume,
                    MAX(max_sale_price) as max_sale_price
                FROM mv_market_summary_monthly
                {where_clause}
            """, *params)
            
            return dict(result) if result else {}
    
    async def get_distressed_properties(self, limit: int = 20) -> List[Dict]:
        """Get recent distressed property sales from materialized view"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM mv_distressed_pipeline
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def find_flip_candidates(self, months_back: int = 24) -> List[Dict]:
        """Find properties that were flipped"""
        async with self.pool.acquire() as conn:
            cutoff_date = datetime.now() - timedelta(days=months_back * 30)
            
            rows = await conn.fetch("""
                WITH property_sales AS (
                    SELECT 
                        parcel_id,
                        sale_date,
                        sale_price,
                        qualification_code,
                        ROW_NUMBER() OVER (PARTITION BY parcel_id ORDER BY sale_date) as sale_num,
                        COUNT(*) OVER (PARTITION BY parcel_id) as total_sales
                    FROM fl_sdf_sales
                    WHERE sale_date >= $1
                        AND sale_price > 1000
                )
                SELECT 
                    ps1.parcel_id,
                    ps1.sale_price as min_price,
                    ps2.sale_price as max_price,
                    ps2.sale_price - ps1.sale_price as price_delta,
                    EXTRACT(DAYS FROM ps2.sale_date - ps1.sale_date) as days_held,
                    ((ps2.sale_price - ps1.sale_price) / ps1.sale_price * 100) as roi_percent
                FROM property_sales ps1
                JOIN property_sales ps2 ON ps1.parcel_id = ps2.parcel_id
                WHERE ps1.sale_num = 1
                    AND ps2.sale_num = ps1.total_sales
                    AND ps2.sale_price > ps1.sale_price
                    AND ps1.total_sales >= 2
                ORDER BY roi_percent DESC
                LIMIT 100
            """, cutoff_date)
            
            return [dict(row) for row in rows]
    
    async def refresh_analytics(self):
        """Refresh SDF analytics views"""
        await self.refresh_views([
            'mv_market_summary_monthly',
            'mv_distressed_pipeline'
        ])