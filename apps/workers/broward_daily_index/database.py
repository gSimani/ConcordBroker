"""
Database integration for Broward County Daily Index data
Stores parsed records in Supabase
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent.parent.parent / 'web' / '.env'
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class BrowardIndexDatabase:
    """Database handler for Broward daily index data"""
    
    def __init__(self):
        """Initialize database connection"""
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not found in environment")
        
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Table names
        self.tables = {
            'records': 'broward_daily_records',
            'metadata': 'broward_daily_metadata',
            'properties': 'broward_daily_properties'
        }
        
        # Ensure tables exist
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Check if required tables exist"""
        for table_name in self.tables.values():
            url = f"{self.supabase_url}/rest/v1/{table_name}?limit=1"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 404:
                logger.warning(f"Table {table_name} does not exist. Please create it in Supabase.")
    
    def insert_records(self, records: List[Dict], batch_size: int = 500) -> Dict:
        """
        Insert parsed records into database
        
        Args:
            records: List of parsed records
            batch_size: Number of records per batch
            
        Returns:
            Summary of insertion results
        """
        if not records:
            return {'inserted': 0, 'failed': 0, 'errors': []}
        
        table = self.tables['records']
        url = f"{self.supabase_url}/rest/v1/{table}"
        
        inserted = 0
        failed = 0
        errors = []
        
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Add timestamps
            for record in batch:
                if 'created_at' not in record:
                    record['created_at'] = datetime.now().isoformat()
                if 'updated_at' not in record:
                    record['updated_at'] = datetime.now().isoformat()
            
            # Insert batch
            headers = {
                **self.headers,
                'Prefer': 'resolution=merge-duplicates,return=minimal'
            }
            
            try:
                response = requests.post(url, json=batch, headers=headers)
                
                if response.status_code in [200, 201, 204]:
                    inserted += len(batch)
                    logger.debug(f"Inserted batch of {len(batch)} records")
                else:
                    failed += len(batch)
                    error_msg = f"Batch insert failed: {response.status_code} - {response.text}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                failed += len(batch)
                error_msg = f"Exception during batch insert: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        logger.info(f"Insert complete: {inserted} inserted, {failed} failed")
        
        return {
            'inserted': inserted,
            'failed': failed,
            'errors': errors[:10]  # Limit error messages
        }
    
    def update_property_links(self, records: List[Dict]) -> Dict:
        """
        Link daily index records to properties
        
        Args:
            records: Records with parcel IDs
            
        Returns:
            Summary of linking results
        """
        linked = 0
        
        for record in records:
            if 'parcel_id' in record and record['parcel_id']:
                # Check if property exists in main property table
                parcel_id = record['parcel_id']
                
                # Update florida_parcels with latest transaction info
                if record.get('record_type') in ['Real Estate Deed', 'Mortgage']:
                    update_data = {
                        'parcel_id': parcel_id,
                        'last_transaction_date': record.get('recorded_date'),
                        'last_transaction_type': record.get('doc_type'),
                        'last_transaction_amount': record.get('consideration')
                    }
                    
                    # Update property record
                    url = f"{self.supabase_url}/rest/v1/florida_parcels"
                    headers = {
                        **self.headers,
                        'Prefer': 'resolution=merge-duplicates,return=minimal'
                    }
                    
                    response = requests.post(url, json=[update_data], headers=headers)
                    
                    if response.status_code in [200, 201, 204]:
                        linked += 1
        
        logger.info(f"Linked {linked} records to properties")
        
        return {'linked': linked}
    
    def save_metadata(self, metadata: Dict):
        """
        Save metadata about the data load
        
        Args:
            metadata: Metadata dictionary
        """
        table = self.tables['metadata']
        url = f"{self.supabase_url}/rest/v1/{table}"
        
        metadata['created_at'] = datetime.now().isoformat()
        
        response = requests.post(url, json=metadata, headers=self.headers)
        
        if response.status_code in [200, 201, 204]:
            logger.info("Metadata saved successfully")
        else:
            logger.error(f"Failed to save metadata: {response.status_code}")
    
    def get_recent_records(self, days: int = 7, limit: int = 100) -> List[Dict]:
        """
        Get recent records from database
        
        Args:
            days: Number of days to look back
            limit: Maximum records to return
            
        Returns:
            List of recent records
        """
        table = self.tables['records']
        
        # Calculate date cutoff
        cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff = cutoff.replace(day=cutoff.day - days)
        
        url = f"{self.supabase_url}/rest/v1/{table}"
        params = {
            'recorded_date': f'gte.{cutoff.isoformat()}',
            'order': 'recorded_date.desc',
            'limit': limit
        }
        
        response = requests.get(url, params=params, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to fetch recent records: {response.status_code}")
            return []
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        for name, table in self.tables.items():
            url = f"{self.supabase_url}/rest/v1/{table}?select=count"
            headers = {
                **self.headers,
                'Prefer': 'count=exact'
            }
            
            response = requests.head(url, headers=headers)
            
            if response.status_code == 200:
                count = response.headers.get('content-range', '*/0').split('/')[-1]
                stats[name] = int(count)
            else:
                stats[name] = 0
        
        return stats