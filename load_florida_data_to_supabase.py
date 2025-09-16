#!/usr/bin/env python3
"""
Load Florida Data to Supabase
Comprehensive script to load all downloaded Florida data into Supabase tables
"""

import os
import csv
import json
import asyncio
import logging
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd
import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloridaDataLoader:
    """Load Florida data files into Supabase"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Missing Supabase credentials in .env file")
            raise ValueError("Supabase credentials not found")
        
        self.api_url = f"{self.supabase_url}/rest/v1"
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Data file mappings
        self.data_files = {
            'NAL': {
                'file': 'data/florida/revenue_portal/broward/NAL16P202501.csv',
                'table': 'fl_nal_name_address',
                'batch_size': 100,
                'key_fields': ['PARCEL_ID', 'ASMNT_YR']
            },
            'NAP': {
                'file': 'data/florida/revenue_portal/broward/NAP16P202501.csv',
                'table': 'fl_nap_assessments',
                'batch_size': 200,
                'key_fields': ['PARCEL_ID', 'ASMNT_YR']
            },
            'SDF': {
                'file': 'data/florida/revenue_portal/broward/SDF16P202501.csv',
                'table': 'fl_sdf_sales',
                'batch_size': 500,
                'key_fields': ['PARCEL_ID', 'SALE_ID_CD']
            }
        }

    async def check_table_exists(self, table_name: str) -> bool:
        """Check if table exists in Supabase"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(
                    f"{self.api_url}/{table_name}",
                    headers=self.headers
                ) as response:
                    return response.status != 404
            except Exception as e:
                logger.error(f"Error checking table {table_name}: {e}")
                return False

    async def get_record_count(self, table_name: str) -> int:
        """Get current record count in table"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.head(
                    f"{self.api_url}/{table_name}?select=*",
                    headers=self.headers
                ) as response:
                    count_header = response.headers.get('Content-Range')
                    if count_header:
                        # Format: "0-99/1000" -> extract total
                        total = count_header.split('/')[-1]
                        return int(total) if total != '*' else 0
                    return 0
            except Exception as e:
                logger.error(f"Error getting count for {table_name}: {e}")
                return 0

    def clean_row_data(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and prepare row data for Supabase"""
        cleaned = {}
        for key, value in row.items():
            # Clean column names (lowercase, no spaces)
            clean_key = key.lower().replace(' ', '_').replace('-', '_')
            
            # Handle empty/null values
            if value == '' or value is None or value == 'NULL':
                cleaned[clean_key] = None
            elif isinstance(value, str):
                # Truncate very long strings
                cleaned[clean_key] = value.strip()[:500] if len(value) > 500 else value.strip()
            else:
                cleaned[clean_key] = value
        
        return cleaned

    async def load_csv_to_table(self, dataset_name: str, config: Dict) -> Dict[str, Any]:
        """Load a CSV file to Supabase table"""
        file_path = Path(config['file'])
        table_name = config['table']
        batch_size = config.get('batch_size', 100)
        
        logger.info(f"Loading {dataset_name} from {file_path} to {table_name}")
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {'status': 'error', 'message': 'File not found'}
        
        # Check if table exists
        table_exists = await self.check_table_exists(table_name)
        if not table_exists:
            logger.warning(f"Table {table_name} does not exist - skipping")
            return {'status': 'skipped', 'message': 'Table does not exist'}
        
        # Get current record count
        current_count = await self.get_record_count(table_name)
        logger.info(f"Current records in {table_name}: {current_count}")
        
        stats = {
            'total_rows': 0,
            'processed': 0,
            'inserted': 0,
            'errors': 0,
            'status': 'in_progress'
        }
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path, dtype=str, na_filter=False)
            stats['total_rows'] = len(df)
            
            logger.info(f"File has {stats['total_rows']} rows")
            
            # Process in batches
            async with aiohttp.ClientSession() as session:
                for i in range(0, len(df), batch_size):
                    batch_df = df.iloc[i:i+batch_size]
                    batch_data = []
                    
                    for _, row in batch_df.iterrows():
                        cleaned_row = self.clean_row_data(row.to_dict())
                        batch_data.append(cleaned_row)
                    
                    # Insert batch
                    try:
                        async with session.post(
                            f"{self.api_url}/{table_name}",
                            headers=self.headers,
                            json=batch_data
                        ) as response:
                            if response.status in [200, 201]:
                                stats['inserted'] += len(batch_data)
                            else:
                                error_text = await response.text()
                                logger.error(f"Batch insert failed: {response.status} - {error_text}")
                                stats['errors'] += len(batch_data)
                    
                    except Exception as e:
                        logger.error(f"Error inserting batch: {e}")
                        stats['errors'] += len(batch_data)
                    
                    stats['processed'] += len(batch_data)
                    
                    # Progress update
                    if stats['processed'] % 1000 == 0:
                        logger.info(f"Processed {stats['processed']}/{stats['total_rows']} rows")
            
            stats['status'] = 'completed'
            logger.info(f"Completed loading {dataset_name}: {stats['inserted']} inserted, {stats['errors']} errors")
            
        except Exception as e:
            logger.error(f"Error loading {dataset_name}: {e}")
            stats['status'] = 'error'
            stats['error_message'] = str(e)
        
        return stats

    async def create_florida_parcels_summary(self):
        """Create summary records in main florida_parcels table"""
        logger.info("Creating Florida parcels summary from NAL data")
        
        # This would be a more complex query combining NAL, NAP, and SDF data
        # For now, just ensure the table exists
        table_exists = await self.check_table_exists('florida_parcels')
        if not table_exists:
            logger.warning("florida_parcels table does not exist")
            return
        
        # Get count of existing parcels
        count = await self.get_record_count('florida_parcels')
        logger.info(f"florida_parcels currently has {count} records")

    async def load_all_data(self):
        """Load all Florida data files"""
        logger.info("=" * 60)
        logger.info("FLORIDA DATA LOADING TO SUPABASE")
        logger.info("=" * 60)
        
        results = {}
        total_inserted = 0
        
        # Load each dataset
        for dataset_name, config in self.data_files.items():
            logger.info(f"\nLoading {dataset_name}...")
            result = await self.load_csv_to_table(dataset_name, config)
            results[dataset_name] = result
            
            if result.get('status') == 'completed':
                total_inserted += result.get('inserted', 0)
        
        # Create summary data
        await self.create_florida_parcels_summary()
        
        # Final report
        logger.info("\n" + "=" * 60)
        logger.info("LOADING COMPLETE - SUMMARY")
        logger.info("=" * 60)
        
        for dataset, result in results.items():
            status = result.get('status', 'unknown')
            inserted = result.get('inserted', 0)
            errors = result.get('errors', 0)
            logger.info(f"{dataset}: {status} - {inserted} inserted, {errors} errors")
        
        logger.info(f"\nTotal records inserted: {total_inserted}")
        
        return results

    async def verify_data_loaded(self):
        """Verify data was loaded successfully"""
        logger.info("\nVerifying loaded data...")
        
        verification = {}
        
        for dataset_name, config in self.data_files.items():
            table_name = config['table']
            count = await self.get_record_count(table_name)
            verification[table_name] = count
            logger.info(f"{table_name}: {count} records")
        
        # Check main parcels table
        parcel_count = await self.get_record_count('florida_parcels')
        verification['florida_parcels'] = parcel_count
        logger.info(f"florida_parcels: {parcel_count} records")
        
        return verification


async def main():
    """Main execution"""
    loader = FloridaDataLoader()
    
    # Load all data
    results = await loader.load_all_data()
    
    # Verify loading
    verification = await loader.verify_data_loaded()
    
    # Save results
    summary = {
        'timestamp': datetime.now().isoformat(),
        'loading_results': results,
        'verification': verification
    }
    
    with open('florida_data_loading_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nSummary saved to: florida_data_loading_summary.json")
    
    return summary


if __name__ == "__main__":
    asyncio.run(main())