"""
Florida Revenue SDF (Sales Data File) Database Loader
Loads parsed SDF sales data to Supabase PostgreSQL database
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase credentials in environment variables")
    sys.exit(1)

import requests

class SDFDatabaseLoader:
    """Loads SDF sales data to Supabase database"""
    
    def __init__(self):
        """Initialize database loader"""
        self.supabase_url = SUPABASE_URL
        self.supabase_key = SUPABASE_KEY
        self.headers = {
            'apikey': self.supabase_key,
            'Authorization': f'Bearer {self.supabase_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal'
        }
        
        # Table name
        self.table_name = 'florida_sdf_sales'
        
        # Batch settings
        self.batch_size = 500
        
        logger.info("SDF Database Loader initialized")
    
    def create_table(self) -> bool:
        """
        Create SDF sales table in database if it doesn't exist
        
        Returns:
            Success status
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS florida_sdf_sales (
            id BIGSERIAL PRIMARY KEY,
            
            -- Key fields
            parcel_id VARCHAR(30) NOT NULL,
            county_number VARCHAR(2) NOT NULL,
            county_name VARCHAR(50),
            
            -- Sale information
            sale_date DATE,
            sale_year INTEGER,
            sale_month INTEGER,
            sale_day INTEGER,
            sale_price DECIMAL(15, 2),
            
            -- Official records
            or_book VARCHAR(10),
            or_page VARCHAR(10),
            clerk_no VARCHAR(20),
            
            -- Sale details
            qual_code VARCHAR(2),
            qual_desc VARCHAR(50),
            vi_code CHAR(1),
            grantor VARCHAR(100),
            grantee VARCHAR(100),
            
            -- Sale characteristics
            multi_parcel_sale BOOLEAN DEFAULT FALSE,
            sale_type VARCHAR(10),
            deed_type VARCHAR(10),
            instrument_type VARCHAR(10),
            
            -- Sale flags
            foreclosure_flag BOOLEAN DEFAULT FALSE,
            reo_flag BOOLEAN DEFAULT FALSE,
            short_sale_flag BOOLEAN DEFAULT FALSE,
            resale_flag BOOLEAN DEFAULT FALSE,
            arms_length_flag BOOLEAN DEFAULT FALSE,
            distressed_flag BOOLEAN DEFAULT FALSE,
            
            -- Property details
            transfer_acreage DECIMAL(10, 4),
            property_use VARCHAR(10),
            
            -- Address
            site_address VARCHAR(200),
            site_city VARCHAR(100),
            site_zip VARCHAR(20),
            
            -- Metadata
            data_source VARCHAR(20) DEFAULT 'SDF',
            file_name VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            
            CONSTRAINT unique_sdf_sale UNIQUE (parcel_id, county_number, sale_date, sale_price)
        );
        
        CREATE INDEX IF NOT EXISTS idx_sdf_parcel_id ON florida_sdf_sales(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_sdf_county ON florida_sdf_sales(county_number);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_date ON florida_sdf_sales(sale_date);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_year ON florida_sdf_sales(sale_year);
        CREATE INDEX IF NOT EXISTS idx_sdf_sale_price ON florida_sdf_sales(sale_price);
        CREATE INDEX IF NOT EXISTS idx_sdf_qual_code ON florida_sdf_sales(qual_code);
        CREATE INDEX IF NOT EXISTS idx_sdf_foreclosure ON florida_sdf_sales(foreclosure_flag) WHERE foreclosure_flag = TRUE;
        CREATE INDEX IF NOT EXISTS idx_sdf_arms_length ON florida_sdf_sales(arms_length_flag) WHERE arms_length_flag = TRUE;
        """
        
        # Note: Table creation would typically be done via Supabase dashboard
        # or migration scripts, not via REST API
        logger.info("Table should be created via Supabase dashboard or migration scripts")
        logger.info("Table: florida_sdf_sales")
        
        return True
    
    def load_records(self, records: List[Dict], file_name: str, county_number: str, 
                     county_name: str) -> Dict:
        """
        Load SDF records to database
        
        Args:
            records: List of parsed SDF records
            file_name: Source file name
            county_number: County code
            county_name: County name
            
        Returns:
            Load result
        """
        if not records:
            return {
                'status': 'no_data',
                'message': 'No records to load'
            }
        
        logger.info(f"Loading {len(records):,} SDF records for {county_name}")
        
        loaded = 0
        failed = 0
        errors = []
        duplicates = 0
        
        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]
            
            # Prepare batch data
            batch_data = []
            for record in batch:
                # Skip records without essential fields
                if not record.get('PARCEL_ID') or not record.get('SALE_PRC'):
                    failed += 1
                    continue
                
                data = {
                    'parcel_id': record.get('PARCEL_ID'),
                    'county_number': county_number,
                    'county_name': county_name,
                    'sale_date': record.get('SALE_DATE'),
                    'sale_year': record.get('SALE_YR'),
                    'sale_month': record.get('SALE_MO'),
                    'sale_day': record.get('SALE_DAY'),
                    'sale_price': record.get('SALE_PRC'),
                    'or_book': record.get('OR_BOOK'),
                    'or_page': record.get('OR_PAGE'),
                    'clerk_no': record.get('CLERK_NO'),
                    'qual_code': record.get('QUAL_CD'),
                    'qual_desc': record.get('QUAL_DESC'),
                    'vi_code': record.get('VI_CD'),
                    'grantor': record.get('GRANTOR')[:100] if record.get('GRANTOR') else None,
                    'grantee': record.get('GRANTEE')[:100] if record.get('GRANTEE') else None,
                    'multi_parcel_sale': record.get('IS_MULTI_PARCEL', False),
                    'sale_type': record.get('SALE_TYPE'),
                    'deed_type': record.get('DEED_TYPE'),
                    'instrument_type': record.get('INSTR_TYP'),
                    'foreclosure_flag': record.get('IS_FORECLOSURE', False),
                    'reo_flag': record.get('IS_REO', False),
                    'short_sale_flag': record.get('IS_SHORT_SALE', False),
                    'resale_flag': record.get('RESALE_FLAG') == 'Y',
                    'arms_length_flag': record.get('IS_ARMS_LENGTH', False),
                    'distressed_flag': record.get('IS_DISTRESSED', False),
                    'transfer_acreage': record.get('TRANSFER_ACREAGE'),
                    'property_use': record.get('PROPERTY_USE'),
                    'site_address': record.get('SITE_ADDRESS'),
                    'site_city': record.get('SITE_CITY'),
                    'site_zip': record.get('SITE_ZIP'),
                    'file_name': file_name,
                    'data_source': 'SDF'
                }
                
                # Clean data - remove None values
                data = {k: v for k, v in data.items() if v is not None}
                batch_data.append(data)
            
            if not batch_data:
                continue
            
            # Insert batch
            try:
                url = f"{self.supabase_url}/rest/v1/{self.table_name}"
                
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=batch_data
                )
                
                if response.status_code in [200, 201]:
                    loaded += len(batch_data)
                    logger.debug(f"Loaded batch {i//self.batch_size + 1}: {len(batch_data)} records")
                elif response.status_code == 409:
                    # Conflict - likely duplicates
                    duplicates += len(batch_data)
                    logger.debug(f"Batch {i//self.batch_size + 1} contains duplicates")
                else:
                    failed += len(batch_data)
                    error_msg = f"Batch insert failed: {response.status_code} - {response.text[:200]}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except Exception as e:
                failed += len(batch_data)
                error_msg = f"Error loading batch: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        result = {
            'status': 'success' if loaded > 0 else 'failed',
            'table': self.table_name,
            'total_records': len(records),
            'loaded': loaded,
            'failed': failed,
            'duplicates': duplicates,
            'errors': errors[:10]  # Limit errors
        }
        
        logger.info(f"SDF load complete: {loaded:,} loaded, {failed:,} failed, {duplicates:,} duplicates")
        
        return result
    
    def load_file(self, file_path: Path, parsed_data: Dict, county_number: str, 
                  county_name: str) -> Dict:
        """
        Load parsed SDF file to database
        
        Args:
            file_path: Path to SDF file
            parsed_data: Parsed data from SDFParser
            county_number: County code
            county_name: County name
            
        Returns:
            Load results
        """
        logger.info(f"Loading SDF data for {county_name} ({county_number})")
        
        if not parsed_data.get('success'):
            return {
                'status': 'parse_error',
                'error': parsed_data.get('error'),
                'county': county_name,
                'county_code': county_number
            }
        
        records = parsed_data.get('records', [])
        
        if not records:
            return {
                'status': 'no_data',
                'message': 'No records to load',
                'county': county_name,
                'county_code': county_number
            }
        
        # Load records
        result = self.load_records(
            records,
            file_path.name,
            county_number,
            county_name
        )
        
        result['county'] = county_name
        result['county_code'] = county_number
        
        # Add statistics
        if parsed_data.get('statistics'):
            stats = parsed_data['statistics']
            result['statistics'] = {
                'total_sales_volume': stats.get('total_sales_volume', 0),
                'average_sale_price': stats.get('average_sale_price', 0),
                'arms_length_sales': stats.get('arms_length_sales', 0),
                'foreclosure_sales': stats.get('foreclosure_sales', 0)
            }
        
        return result
    
    def get_statistics(self, county_number: Optional[str] = None, 
                      year: Optional[int] = None) -> Dict:
        """
        Get database statistics for SDF sales data
        
        Args:
            county_number: Filter by county (optional)
            year: Filter by year (optional)
            
        Returns:
            Statistics dictionary
        """
        stats = {
            'total_sales': 0,
            'total_volume': 0,
            'counties': [],
            'years': [],
            'sale_types': {}
        }
        
        try:
            # Build query
            url = f"{self.supabase_url}/rest/v1/{self.table_name}"
            params = {'select': 'count'}
            
            if county_number:
                params['county_number'] = f'eq.{county_number}'
            if year:
                params['sale_year'] = f'eq.{year}'
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 200:
                # Parse count from response header
                count_header = response.headers.get('content-range', '0-0/0')
                total = int(count_header.split('/')[-1])
                stats['total_sales'] = total
            
            # Get aggregated statistics (would need custom RPC functions in Supabase)
            # For now, just return the count
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
        
        return stats
    
    def update_sale_classifications(self, county_number: str) -> Dict:
        """
        Update sale classifications based on qualification codes
        
        Args:
            county_number: County to update
            
        Returns:
            Update results
        """
        logger.info(f"Updating sale classifications for county {county_number}")
        
        # Classification rules
        classifications = {
            'Q': 'Qualified',
            'U': 'Unqualified',
            'F': 'Foreclosure',
            'G': 'Gift',
            'E': 'Exchange'
        }
        
        updated = 0
        
        try:
            for qual_code, classification in classifications.items():
                url = f"{self.supabase_url}/rest/v1/{self.table_name}"
                
                # Update records with this qualification code
                data = {'qual_desc': classification}
                params = {
                    'county_number': f'eq.{county_number}',
                    'qual_code': f'eq.{qual_code}'
                }
                
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                
                if response.status_code in [200, 204]:
                    # Get count from response
                    count_header = response.headers.get('content-range', '0-0/0')
                    count = int(count_header.split('/')[-1])
                    updated += count
                    logger.debug(f"Updated {count} records with qual_code={qual_code}")
            
            logger.info(f"Updated {updated} sale classifications")
            
            return {
                'status': 'success',
                'updated': updated
            }
            
        except Exception as e:
            logger.error(f"Error updating classifications: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


if __name__ == "__main__":
    import argparse
    from sdf_parser import SDFParser
    
    parser = argparse.ArgumentParser(description='SDF Database Loader')
    parser.add_argument('--file', help='SDF file to load')
    parser.add_argument('--county', default='06', help='County number')
    parser.add_argument('--county-name', default='Broward', help='County name')
    parser.add_argument('--create-table', action='store_true', help='Create database table')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--update-classifications', action='store_true', 
                       help='Update sale classifications')
    
    args = parser.parse_args()
    
    # Initialize loader
    loader = SDFDatabaseLoader()
    
    if args.create_table:
        # Create table
        loader.create_table()
        print("Table creation SQL logged. Create table via Supabase dashboard.")
        
    elif args.stats:
        # Show statistics
        stats = loader.get_statistics(args.county)
        print("\nSDF Database Statistics:")
        print(f"  Total sales: {stats['total_sales']:,}")
        
    elif args.update_classifications:
        # Update classifications
        result = loader.update_sale_classifications(args.county)
        print(f"Updated {result.get('updated', 0):,} sale classifications")
        
    elif args.file:
        # Parse and load file
        sdf_parser = SDFParser()
        
        file_path = Path(args.file)
        
        # Parse file
        parsed = sdf_parser.parse_file(file_path)
        
        if parsed['success']:
            # Load to database
            result = loader.load_file(
                file_path,
                parsed,
                args.county,
                args.county_name
            )
            
            print(f"\nLoad complete: {result['status']}")
            print(f"  Loaded: {result.get('loaded', 0):,}")
            print(f"  Failed: {result.get('failed', 0):,}")
            print(f"  Duplicates: {result.get('duplicates', 0):,}")
            
            if result.get('statistics'):
                stats = result['statistics']
                print(f"\nSales Statistics:")
                print(f"  Total volume: ${stats['total_sales_volume']:,.2f}")
                print(f"  Average price: ${stats['average_sale_price']:,.2f}")
        else:
            print(f"Parse error: {parsed.get('error')}")
    
    else:
        print("Please specify --file to load or --stats to view statistics")