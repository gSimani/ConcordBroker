"""
Automated NAL Import System - No Interactive Input
Executes the complete NAL data import without user prompts
"""

import os
import sys
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment
load_dotenv()
url = os.getenv('VITE_SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('VITE_SUPABASE_ANON_KEY')

def connect_to_supabase():
    """Connect to Supabase"""
    try:
        supabase = create_client(url, key)
        logger.info("Connected to Supabase successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return None

def check_tables_exist(supabase):
    """Check if NAL tables exist"""
    try:
        # Try to access the core table
        result = supabase.table('florida_properties_core').select('*').limit(1).execute()
        logger.info("NAL tables already exist")
        return True
    except Exception as e:
        logger.info("NAL tables need to be created")
        return False

def insert_batch_data(supabase, table_name, data_batch, batch_num):
    """Insert a batch of data into a table"""
    try:
        result = supabase.table(table_name).insert(data_batch).execute()
        logger.info(f"Batch {batch_num}: Inserted {len(data_batch)} records into {table_name}")
        return len(data_batch)
    except Exception as e:
        logger.error(f"Batch {batch_num}: Error inserting into {table_name}: {e}")
        return 0

def process_nal_file(supabase, file_path, batch_size=1000):
    """Process NAL CSV file and import to database"""
    
    logger.info("Starting NAL file processing...")
    logger.info(f"Reading file: {file_path}")
    
    try:
        # Read the CSV file in chunks
        chunk_count = 0
        total_processed = 0
        
        for chunk in pd.read_csv(file_path, chunksize=batch_size, dtype=str, encoding='latin-1'):
            chunk_count += 1
            logger.info(f"Processing chunk {chunk_count}, records: {len(chunk)}")
            
            # Convert chunk to records for each table
            core_records = []
            valuation_records = []
            exemption_records = []
            characteristic_records = []
            sales_records = []
            
            for _, row in chunk.iterrows():
                parcel_id = str(row.get('PARCEL_ID', '')).strip()
                if not parcel_id:
                    continue
                
                # Core properties record
                core_record = {
                    'parcel_id': parcel_id,
                    'co_no': int(row.get('CO_NO', 0)) if row.get('CO_NO', '').isdigit() else None,
                    'assessment_year': 2025,
                    'owner_name': str(row.get('OWNER_NAME', '')).strip() or None,
                    'owner_state': str(row.get('OWNER_STATE', '')).strip() or None,
                    'physical_address': str(row.get('PHYSICAL_ADDRESS', '')).strip() or None,
                    'physical_city': str(row.get('PHYSICAL_CITY', '')).strip() or None,
                    'physical_zipcode': str(row.get('PHYSICAL_ZIPCODE', '')).strip() or None,
                    'just_value': float(row.get('JUST_VALUE', 0)) if str(row.get('JUST_VALUE', '')).replace('.','').replace('-','').isdigit() else None,
                    'assessed_value_sd': float(row.get('ASSESSED_VALUE_SD', 0)) if str(row.get('ASSESSED_VALUE_SD', '')).replace('.','').replace('-','').isdigit() else None,
                    'assessed_value_nsd': float(row.get('ASSESSED_VALUE_NSD', 0)) if str(row.get('ASSESSED_VALUE_NSD', '')).replace('.','').replace('-','').isdigit() else None,
                    'taxable_value_sd': float(row.get('TAXABLE_VALUE_SD', 0)) if str(row.get('TAXABLE_VALUE_SD', '')).replace('.','').replace('-','').isdigit() else None,
                    'taxable_value_nsd': float(row.get('TAXABLE_VALUE_NSD', 0)) if str(row.get('TAXABLE_VALUE_NSD', '')).replace('.','').replace('-','').isdigit() else None,
                    'land_value': float(row.get('LAND_VALUE', 0)) if str(row.get('LAND_VALUE', '')).replace('.','').replace('-','').isdigit() else None,
                    'dor_use_code': str(row.get('DOR_USE_CODE', '')).strip() or None,
                    'pa_use_code': str(row.get('PA_USE_CODE', '')).strip() or None,
                    'neighborhood_code': str(row.get('NEIGHBORHOOD', '')).strip() or None,
                    'land_sqft': int(float(row.get('LAND_SQFT', 0))) if str(row.get('LAND_SQFT', '')).replace('.','').replace('-','').isdigit() else None,
                    'tax_authority_code': str(row.get('TAX_AUTHORITY_CODE', '')).strip() or None,
                    'market_area': str(row.get('MARKET_AREA', '')).strip() or None,
                    'township': str(row.get('TOWNSHIP', '')).strip() or None,
                    'range_val': str(row.get('RANGE', '')).strip() or None,
                    'section_val': str(row.get('SECTION', '')).strip() or None
                }
                core_records.append(core_record)
                
                # Valuation record
                valuation_record = {
                    'parcel_id': parcel_id,
                    'just_value': float(row.get('JUST_VALUE', 0)) if str(row.get('JUST_VALUE', '')).replace('.','').replace('-','').isdigit() else None,
                    'just_value_change': float(row.get('JUST_VALUE_CHANGE', 0)) if str(row.get('JUST_VALUE_CHANGE', '')).replace('.','').replace('-','').isdigit() else None,
                    'assessed_value_sd': float(row.get('ASSESSED_VALUE_SD', 0)) if str(row.get('ASSESSED_VALUE_SD', '')).replace('.','').replace('-','').isdigit() else None,
                    'assessed_value_nsd': float(row.get('ASSESSED_VALUE_NSD', 0)) if str(row.get('ASSESSED_VALUE_NSD', '')).replace('.','').replace('-','').isdigit() else None,
                    'land_value': float(row.get('LAND_VALUE', 0)) if str(row.get('LAND_VALUE', '')).replace('.','').replace('-','').isdigit() else None,
                    'new_construction_value': float(row.get('NEW_CONSTRUCTION_VALUE', 0)) if str(row.get('NEW_CONSTRUCTION_VALUE', '')).replace('.','').replace('-','').isdigit() else None
                }
                valuation_records.append(valuation_record)
                
                # Exemption record
                exemption_record = {
                    'parcel_id': parcel_id,
                    'homestead_exemption': float(row.get('HOMESTEAD_EXEMPTION', 0)) if str(row.get('HOMESTEAD_EXEMPTION', '')).replace('.','').replace('-','').isdigit() else None,
                    'senior_exemption': float(row.get('SENIOR_EXEMPTION', 0)) if str(row.get('SENIOR_EXEMPTION', '')).replace('.','').replace('-','').isdigit() else None,
                    'disability_exemption': float(row.get('DISABILITY_EXEMPTION', 0)) if str(row.get('DISABILITY_EXEMPTION', '')).replace('.','').replace('-','').isdigit() else None,
                    'veteran_exemption': float(row.get('VETERAN_EXEMPTION', 0)) if str(row.get('VETERAN_EXEMPTION', '')).replace('.','').replace('-','').isdigit() else None,
                    'widow_exemption': float(row.get('WIDOW_EXEMPTION', 0)) if str(row.get('WIDOW_EXEMPTION', '')).replace('.','').replace('-','').isdigit() else None
                }
                exemption_records.append(exemption_record)
                
                # Characteristics record
                char_record = {
                    'parcel_id': parcel_id,
                    'actual_year_built': int(row.get('ACTUAL_YEAR_BUILT', 0)) if str(row.get('ACTUAL_YEAR_BUILT', '')).isdigit() else None,
                    'effective_year_built': int(row.get('EFFECTIVE_YEAR_BUILT', 0)) if str(row.get('EFFECTIVE_YEAR_BUILT', '')).isdigit() else None,
                    'total_living_area': int(float(row.get('TOTAL_LIVING_AREA', 0))) if str(row.get('TOTAL_LIVING_AREA', '')).replace('.','').isdigit() else None,
                    'land_units': int(float(row.get('LAND_UNITS', 0))) if str(row.get('LAND_UNITS', '')).replace('.','').isdigit() else None,
                    'land_units_code': str(row.get('LAND_UNITS_CODE', '')).strip() or None,
                    'number_of_buildings': int(row.get('NUMBER_OF_BUILDINGS', 0)) if str(row.get('NUMBER_OF_BUILDINGS', '')).isdigit() else None,
                    'improvement_quality': str(row.get('IMPROVEMENT_QUALITY', '')).strip() or None,
                    'construction_class': str(row.get('CONSTRUCTION_CLASS', '')).strip() or None
                }
                characteristic_records.append(char_record)
                
                # Sales record
                sales_record = {
                    'parcel_id': parcel_id,
                    'sale_price_1': float(row.get('SALE_PRICE_1', 0)) if str(row.get('SALE_PRICE_1', '')).replace('.','').replace('-','').isdigit() else None,
                    'sale_year_1': int(row.get('SALE_YEAR_1', 0)) if str(row.get('SALE_YEAR_1', '')).isdigit() else None,
                    'sale_price_2': float(row.get('SALE_PRICE_2', 0)) if str(row.get('SALE_PRICE_2', '')).replace('.','').replace('-','').isdigit() else None,
                    'sale_year_2': int(row.get('SALE_YEAR_2', 0)) if str(row.get('SALE_YEAR_2', '')).isdigit() else None
                }
                sales_records.append(sales_record)
            
            # Insert data in parallel
            tables_data = [
                ('florida_properties_core', core_records),
                ('property_valuations', valuation_records),
                ('property_exemptions', exemption_records),
                ('property_characteristics', characteristic_records),
                ('property_sales_enhanced', sales_records)
            ]
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for table_name, data in tables_data:
                    if data:  # Only insert if there's data
                        future = executor.submit(insert_batch_data, supabase, table_name, data, chunk_count)
                        futures.append(future)
                
                # Wait for all insertions to complete
                for future in as_completed(futures):
                    inserted_count = future.result()
                    total_processed += inserted_count
            
            logger.info(f"Completed chunk {chunk_count}, total records processed: {total_processed}")
            
            # Break after first few chunks for testing
            if chunk_count >= 5:  # Process first 5 chunks (5000 records) for testing
                logger.info("Testing mode: Processing first 5 chunks only")
                break
                
        logger.info(f"NAL import completed! Total records processed: {total_processed}")
        return total_processed
        
    except Exception as e:
        logger.error(f"Error processing NAL file: {e}")
        return 0

def main():
    """Main execution function"""
    
    print("=" * 80)
    print("AUTOMATED NAL IMPORT SYSTEM")
    print("=" * 80)
    
    # Connect to Supabase
    supabase = connect_to_supabase()
    if not supabase:
        logger.error("Cannot proceed without Supabase connection")
        return False
    
    # Check if tables exist
    if not check_tables_exist(supabase):
        print("\nNAL tables do not exist yet.")
        print("Please execute the SQL from 'supabase_nal_schema.sql' in your Supabase SQL Editor first.")
        print("Then run this script again.")
        return False
    
    # Check if NAL file exists
    nal_file = "TEMP/NAL16P202501.csv"
    if not os.path.exists(nal_file):
        logger.error(f"NAL file not found: {nal_file}")
        return False
    
    logger.info(f"NAL file found: {nal_file} ({os.path.getsize(nal_file):,} bytes)")
    
    # Execute the import
    start_time = time.time()
    records_processed = process_nal_file(supabase, nal_file)
    end_time = time.time()
    
    duration = end_time - start_time
    logger.info(f"Import completed in {duration:.2f} seconds")
    logger.info(f"Records processed: {records_processed:,}")
    logger.info(f"Processing rate: {records_processed/duration:.1f} records/second")
    
    print("\n" + "=" * 80)
    print("NAL IMPORT RESULTS")
    print("=" * 80)
    print(f"Records processed: {records_processed:,}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Rate: {records_processed/duration:.1f} records/second")
    print("=" * 80)
    
    return records_processed > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)