"""
NAV Database Module for Supabase
Handles all NAV assessment data operations in Supabase
"""

import asyncpg
import logging
from typing import Dict, List, Optional
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_supabase_db import BaseSupabaseDB

logger = logging.getLogger(__name__)

class NAVSupabaseDB(BaseSupabaseDB):
    """NAV-specific Supabase database operations"""
    
    def __init__(self):
        super().__init__('nav')
        self.summary_table = 'fl_nav_parcel_summary'
        self.detail_table = 'fl_nav_assessment_detail'
    
    async def create_tables(self):
        """Create NAV-specific tables (already in migration)"""
        # Tables are created via Supabase migration
        pass
    
    async def bulk_insert_nav_summary(self, records: List[Dict]) -> Dict:
        """Bulk insert NAV parcel summaries to Supabase"""
        
        # Prepare records
        for record in records:
            record['county_number'] = record.get('CO_NO', '').strip('"')
            record['parcel_id'] = record.get('PARCEL_ID', '').strip('"')
            record['assessment_year'] = int(record.get('ASMNT_YR', 0))
            record['tax_year'] = int(record.get('TAX_YR', 0))
            record['roll_type'] = record.get('ROLL_TYPE', '').strip('"')
            
            try:
                record['total_nav_units'] = float(record.get('TOT_NAV_UNITS', '0').strip('"').replace(',', ''))
            except:
                record['total_nav_units'] = 0
                
            try:
                record['total_nav_assessment'] = float(record.get('TOT_NAV_ASMT', '0').strip('"').replace(',', ''))
            except:
                record['total_nav_assessment'] = 0
            
            record['created_at'] = datetime.now()
            record['updated_at'] = datetime.now()
        
        # Bulk upsert to Supabase
        stats = await self.bulk_upsert(
            self.summary_table,
            records,
            unique_columns=['county_number', 'parcel_id', 'assessment_year', 'tax_year']
        )
        
        return stats
    
    async def bulk_insert_nav_detail(self, records: List[Dict]) -> Dict:
        """Bulk insert NAV assessment details to Supabase"""
        
        cdd_count = 0
        municipal_count = 0
        
        # Prepare records
        for record in records:
            record['county_number'] = record.get('CO_NO', '').strip('"')
            record['parcel_id'] = record.get('PARCEL_ID', '').strip('"')
            record['assessment_year'] = int(record.get('ASMNT_YR', 0))
            record['tax_year'] = int(record.get('TAX_YR', 0))
            record['roll_type'] = record.get('ROLL_TYPE', '').strip('"')
            record['nav_tax_code'] = record.get('NAV_TAX_CD', '').strip('"')
            
            try:
                record['nav_units'] = float(record.get('NAV_UNITS', '0').strip('"').replace(',', ''))
            except:
                record['nav_units'] = 0
                
            try:
                record['nav_assessment'] = float(record.get('NAV_ASMT', '0').strip('"').replace(',', ''))
            except:
                record['nav_assessment'] = 0
            
            # Identify CDDs and municipal services
            tax_code = record['nav_tax_code'].upper()
            if 'CDD' in tax_code or 'COMMUNITY' in tax_code:
                record['is_cdd'] = True
                cdd_count += 1
            else:
                record['is_cdd'] = False
                
            if 'MUNICIPAL' in tax_code or 'CITY' in tax_code:
                record['is_municipal'] = True
                municipal_count += 1
            else:
                record['is_municipal'] = False
            
            # Parse authority info from tax code if available
            record['authority_name'] = self.parse_authority_name(tax_code)
            record['authority_type'] = self.determine_authority_type(tax_code)
            record['district_name'] = self.parse_district_name(tax_code)
            
            record['created_at'] = datetime.now()
            record['updated_at'] = datetime.now()
        
        # Bulk upsert to Supabase
        stats = await self.bulk_upsert(
            self.detail_table,
            records,
            unique_columns=['county_number', 'parcel_id', 'assessment_year', 'tax_year', 'nav_tax_code']
        )
        
        stats['cdd_assessments'] = cdd_count
        stats['municipal_assessments'] = municipal_count
        
        return stats
    
    def parse_authority_name(self, tax_code: str) -> str:
        """Parse authority name from tax code"""
        # This would be enhanced with actual mapping
        if 'CDD' in tax_code:
            return tax_code.replace('_', ' ').title()
        return tax_code
    
    def determine_authority_type(self, tax_code: str) -> str:
        """Determine authority type from tax code"""
        tax_code_upper = tax_code.upper()
        
        if 'CDD' in tax_code_upper:
            return 'Community Development District'
        elif 'MUNICIPAL' in tax_code_upper:
            return 'Municipal Service'
        elif 'FIRE' in tax_code_upper:
            return 'Fire District'
        elif 'WATER' in tax_code_upper:
            return 'Water District'
        elif 'HOSPITAL' in tax_code_upper:
            return 'Hospital District'
        else:
            return 'Special District'
    
    def parse_district_name(self, tax_code: str) -> str:
        """Parse district name from tax code"""
        # Extract readable district name
        name = tax_code.replace('_', ' ').replace('-', ' ')
        return ' '.join(word.capitalize() for word in name.split())
    
    async def get_cdd_properties(self, limit: int = 100) -> List[Dict]:
        """Get properties in CDDs"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    d.parcel_id,
                    d.authority_name,
                    d.district_name,
                    d.nav_assessment,
                    s.total_nav_assessment
                FROM fl_nav_assessment_detail d
                JOIN fl_nav_parcel_summary s ON d.parcel_id = s.parcel_id
                    AND d.assessment_year = s.assessment_year
                WHERE d.is_cdd = TRUE
                ORDER BY d.nav_assessment DESC
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def get_high_assessment_properties(self, threshold: float = 10000) -> List[Dict]:
        """Get properties with high NAV assessments"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    parcel_id,
                    COUNT(DISTINCT nav_tax_code) as assessment_count,
                    SUM(nav_assessment) as total_assessment,
                    STRING_AGG(DISTINCT authority_type, ', ') as authority_types
                FROM fl_nav_assessment_detail
                WHERE nav_assessment > $1
                GROUP BY parcel_id
                ORDER BY total_assessment DESC
                LIMIT 100
            """, threshold)
            
            return [dict(row) for row in rows]
    
    async def get_assessment_summary(self, county_number: str = None) -> Dict:
        """Get NAV assessment summary statistics"""
        async with self.pool.acquire() as conn:
            where_clause = "WHERE county_number = $1" if county_number else ""
            param = [county_number] if county_number else []
            
            result = await conn.fetchrow(f"""
                SELECT
                    COUNT(DISTINCT parcel_id) as total_parcels,
                    COUNT(*) as total_assessments,
                    SUM(nav_assessment) as total_value,
                    AVG(nav_assessment) as avg_assessment,
                    MAX(nav_assessment) as max_assessment,
                    SUM(CASE WHEN is_cdd THEN 1 ELSE 0 END) as cdd_count,
                    SUM(CASE WHEN is_municipal THEN 1 ELSE 0 END) as municipal_count
                FROM fl_nav_assessment_detail
                {where_clause}
            """, *param)
            
            return dict(result) if result else {}