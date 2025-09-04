"""
DOR Data Loader using Supabase REST API
Simpler approach that bypasses direct PostgreSQL connection issues
"""

import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import duckdb
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseRESTLoader:
    """Load DOR data to Supabase using REST API"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        self.api_url = f"{self.supabase_url}/rest/v1"
        
        # Headers for Supabase REST API
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        self.data_dir = Path('C:/Users/gsima/Documents/MyProject/ConcordBroker/data/dor')
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    async def check_tables(self):
        """Check if tables exist in Supabase"""
        async with aiohttp.ClientSession() as session:
            # Try to query the tables
            async with session.get(
                f"{self.api_url}/dor_properties?limit=1",
                headers=self.headers
            ) as response:
                if response.status == 200:
                    logger.info("✓ dor_properties table exists")
                    return True
                elif response.status == 404:
                    logger.warning("✗ dor_properties table not found")
                    logger.info("Please create the table using the SQL script in create_supabase_tables.sql")
                    return False
                else:
                    error = await response.text()
                    logger.error(f"Error checking tables: {error}")
                    return False
                    
    async def insert_properties(self, data: List[Dict]) -> int:
        """Insert property records using REST API"""
        if not data:
            return 0
            
        async with aiohttp.ClientSession() as session:
            batch_size = 500  # Supabase recommends smaller batches for REST API
            inserted = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                
                # Clean the data for JSON serialization
                cleaned_batch = []
                for record in batch:
                    clean_record = {}
                    for key, value in record.items():
                        if pd.isna(value) or value is None:
                            clean_record[key] = None
                        elif isinstance(value, (int, float, bool, str)):
                            clean_record[key] = value
                        else:
                            clean_record[key] = str(value)
                    cleaned_batch.append(clean_record)
                
                try:
                    async with session.post(
                        f"{self.api_url}/dor_properties",
                        headers={**self.headers, 'Prefer': 'resolution=merge-duplicates'},
                        json=cleaned_batch
                    ) as response:
                        if response.status in [200, 201]:
                            inserted += len(batch)
                            logger.info(f"Inserted batch: {inserted} records")
                        else:
                            error = await response.text()
                            logger.error(f"Error inserting batch: {error}")
                            
                except Exception as e:
                    logger.error(f"Exception during insert: {e}")
                    
        return inserted
        
    async def process_excel_file(self, file_path: Path) -> Dict:
        """Process Excel file and load to Supabase"""
        logger.info(f"Processing: {file_path}")
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path, nrows=1000)  # Start with 1000 rows for testing
            logger.info(f"Loaded {len(df)} rows from Excel")
            logger.info(f"Columns: {list(df.columns)}")
            
            # Map columns to our schema
            column_mapping = {
                'FOLIO': 'folio',
                'Folio': 'folio',
                'ParcelID': 'folio',
                'OWNER NAME': 'owner_name',
                'Owner Name': 'owner_name',
                'MAIL ADDRESS 1': 'mail_address_1',
                'MAIL ADDRESS 2': 'mail_address_2',
                'MAIL CITY': 'mail_city',
                'MAIL STATE': 'mail_state',
                'MAIL ZIP': 'mail_zip',
                'SITUS ADDRESS 1': 'situs_address_1',
                'SITUS ADDRESS 2': 'situs_address_2',
                'SITUS CITY': 'situs_city',
                'SITUS ZIP': 'situs_zip',
                'USE CODE': 'use_code',
                'SUBDIVISION': 'subdivision',
                'LIVING AREA': 'living_area_sf',
                'YEAR BUILT': 'year_built',
                'BEDROOMS': 'bedrooms',
                'BATHROOMS': 'bathrooms',
                'POOL': 'pool',
                'LAND VALUE': 'land_value',
                'BUILDING VALUE': 'building_value',
                'JUST VALUE': 'just_value',
                'TAXABLE VALUE': 'taxable_value'
            }
            
            # Rename columns
            df = df.rename(columns=column_mapping)
            
            # Add metadata
            df['county'] = 'Broward'
            df['year'] = 2025
            df['source_file'] = file_path.name
            df['load_timestamp'] = datetime.now().isoformat()
            
            # Convert DataFrame to list of dicts
            records = df.to_dict('records')
            
            # Insert to Supabase
            count = await self.insert_properties(records)
            
            return {
                'file': file_path.name,
                'rows_processed': len(df),
                'rows_inserted': count,
                'status': 'success' if count > 0 else 'failed'
            }
            
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {
                'file': file_path.name,
                'rows_processed': 0,
                'rows_inserted': 0,
                'status': 'error',
                'error': str(e)
            }
            
    async def download_and_process(self, url: str, county: str) -> Dict:
        """Download and process county data"""
        import zipfile
        import aiohttp
        
        filename = f"{county}_2025_NAL.zip"
        zip_path = self.data_dir / filename
        
        # Download file if not exists
        if not zip_path.exists():
            logger.info(f"Downloading {county} data...")
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    
                    with open(zip_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                            
            logger.info(f"Downloaded: {zip_path}")
            
        # Extract ZIP
        extract_dir = self.data_dir / county
        extract_dir.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            
        # Process Excel files
        results = []
        for excel_file in extract_dir.glob('*.xlsx'):
            result = await self.process_excel_file(excel_file)
            results.append(result)
            
        return {
            'county': county,
            'files_processed': len(results),
            'results': results
        }


async def main():
    """Test with Broward County data"""
    
    loader = SupabaseRESTLoader()
    
    # Check if tables exist
    if not await loader.check_tables():
        logger.error("Tables don't exist. Please create them in Supabase first.")
        logger.info("\nTo create tables:")
        logger.info("1. Go to https://pmispwtdngkcmsrsjwbp.supabase.co")
        logger.info("2. Navigate to SQL Editor")
        logger.info("3. Run the SQL from create_supabase_tables.sql")
        return
        
    # Process Broward County
    broward_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Broward%2016%20Preliminary%20NAL%202025.zip"
    
    result = await loader.download_and_process(broward_url, "Broward")
    
    logger.info("\n" + "="*60)
    logger.info("PROCESSING COMPLETE")
    logger.info("="*60)
    logger.info(f"County: {result['county']}")
    logger.info(f"Files processed: {result['files_processed']}")
    
    for file_result in result['results']:
        logger.info(f"  - {file_result['file']}: {file_result['rows_inserted']} rows inserted")
        
    logger.info("\n✓ Data loaded to Supabase via REST API!")
    logger.info("Check your Supabase dashboard to see the dor_properties table")


if __name__ == "__main__":
    asyncio.run(main())