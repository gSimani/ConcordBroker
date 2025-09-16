"""
TPP Database Module for Supabase
Handles all TPP data operations in Supabase
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

class TPPSupabaseDB(BaseSupabaseDB):
    """TPP-specific Supabase database operations"""
    
    def __init__(self):
        super().__init__('tpp')
        self.table_name = 'fl_tpp_accounts'
    
    async def create_tables(self):
        """Create TPP-specific tables (already in migration)"""
        # Tables are created via Supabase migration
        # This is just for any runtime adjustments
        pass
    
    async def bulk_insert_tpp_accounts(self, accounts: List[Dict]) -> Dict:
        """Bulk insert TPP accounts to Supabase"""
        
        # Prepare records for insertion
        for account in accounts:
            # Clean and prepare data
            account['county_number'] = account.get('CO_NO', '').strip('"')
            account['account_number'] = account.get('ACCT_NO', '').strip('"')
            account['assessment_year'] = int(account.get('ASMNT_YR', 0))
            account['owner_name'] = account.get('NAME_LINE_1', '').strip('"')
            account['owner_name2'] = account.get('NAME_LINE_2', '').strip('"')
            account['business_name'] = account.get('DBA_LINE_1', '').strip('"')
            account['business_name2'] = account.get('DBA_LINE_2', '').strip('"')
            
            # Parse numeric values
            try:
                account['tangible_value'] = float(account.get('JV', '0').strip('"').replace(',', ''))
            except:
                account['tangible_value'] = 0
                
            try:
                account['exemption_value'] = float(account.get('EX_VAL', '0').strip('"').replace(',', ''))
            except:
                account['exemption_value'] = 0
                
            try:
                account['taxable_value'] = float(account.get('TV', '0').strip('"').replace(',', ''))
            except:
                account['taxable_value'] = 0
            
            # Add metadata
            account['created_at'] = datetime.now()
            account['updated_at'] = datetime.now()
        
        # Bulk upsert to Supabase
        stats = await self.bulk_upsert(
            self.table_name,
            accounts,
            unique_columns=['county_number', 'account_number', 'assessment_year']
        )
        
        # Track major property owners
        await self.identify_major_owners(accounts)
        
        return stats
    
    async def identify_major_owners(self, accounts: List[Dict]):
        """Identify and track major property owners"""
        owner_stats = {}
        
        for account in accounts:
            owner = account.get('owner_name', '').upper()
            if owner and len(owner) > 3:  # Skip empty/short names
                if owner not in owner_stats:
                    owner_stats[owner] = {
                        'count': 0,
                        'total_value': 0
                    }
                owner_stats[owner]['count'] += 1
                owner_stats[owner]['total_value'] += account.get('taxable_value', 0)
        
        # Find major owners (10+ properties or $1M+ value)
        major_owners = [
            owner for owner, stats in owner_stats.items()
            if stats['count'] >= 10 or stats['total_value'] >= 1000000
        ]
        
        if major_owners:
            logger.info(f"Identified {len(major_owners)} major property owners")
            
            # Store in tracking table
            async with self.pool.acquire() as conn:
                for owner in major_owners[:10]:  # Top 10
                    stats = owner_stats[owner]
                    await conn.execute("""
                        INSERT INTO fl_major_owners (
                            owner_name, property_count, total_value, 
                            data_source, last_updated
                        ) VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (owner_name, data_source)
                        DO UPDATE SET
                            property_count = $2,
                            total_value = $3,
                            last_updated = $5
                    """, owner, stats['count'], stats['total_value'], 
                        'tpp', datetime.now())
    
    async def get_owner_summary(self, owner_name: str) -> Dict:
        """Get summary for a specific owner"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as property_count,
                    SUM(taxable_value) as total_value,
                    AVG(taxable_value) as avg_value,
                    MAX(taxable_value) as max_value,
                    STRING_AGG(DISTINCT county_number, ',') as counties
                FROM fl_tpp_accounts
                WHERE UPPER(owner_name) LIKE UPPER($1)
            """, f"%{owner_name}%")
            
            return dict(result) if result else {}
    
    async def get_top_owners(self, limit: int = 100) -> List[Dict]:
        """Get top property owners by count or value"""
        async with self.pool.acquire() as conn:
            # Use materialized view for performance
            rows = await conn.fetch("""
                SELECT * FROM mv_top_property_owners
                LIMIT $1
            """, limit)
            
            return [dict(row) for row in rows]
    
    async def refresh_analytics(self):
        """Refresh TPP analytics views"""
        await self.refresh_views(['mv_top_property_owners'])