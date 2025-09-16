#!/usr/bin/env python3
"""
Live Property Data Loader for ConcordBroker
Loads Broward County property data (939K records) to Supabase for immediate frontend use
"""

import pandas as pd
import numpy as np
from supabase import create_client, Client
import json
import os
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_data_load.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Data paths (prioritize Broward County for immediate results)
BROWARD_DATA_PATH = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP\BROWARD"

class PropertyDataLoader:
    def __init__(self):
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.batch_size = 1000
        self.max_workers = 4
        self.records_loaded = 0
        self.start_time = None

    def clean_numeric_value(self, value):
        """Clean numeric values for database insertion"""
        if pd.isna(value) or value == '' or value == 'NaN':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def clean_text_value(self, value):
        """Clean text values for database insertion"""
        if pd.isna(value) or value == 'NaN':
            return None
        return str(value).strip() if value else None

    def clean_date_value(self, year, month):
        """Create proper date from year/month or return None"""
        try:
            if pd.isna(year) or pd.isna(month) or year == '' or month == '':
                return None
            year_int = int(float(year))
            month_int = int(float(month))
            if year_int > 1900 and 1 <= month_int <= 12:
                return f"{year_int:04d}-{month_int:02d}-01T00:00:00"
            return None
        except (ValueError, TypeError):
            return None

    def process_nal_file(self, file_path):
        """Process NAL (Names and Addresses) file with optimized column mapping"""
        logger.info(f"Processing NAL file: {file_path}")

        try:
            # Read CSV with error handling
            df = pd.read_csv(file_path, dtype=str, low_memory=False)
            logger.info(f"Loaded {len(df)} records from NAL file")

            # Critical column mapping based on database schema
            column_mapping = {
                'PARCEL_ID': 'parcel_id',
                'OWN_NAME': 'owner_name',
                'PHY_ADDR1': 'phy_addr1',
                'PHY_ADDR2': 'phy_addr2',
                'PHY_CITY': 'property_city',
                'PHY_ZIPCD': 'property_zip',
                'OWN_ADDR1': 'owner_addr1',
                'OWN_ADDR2': 'owner_addr2',
                'OWN_CITY': 'owner_city',
                'OWN_STATE': 'owner_state',
                'OWN_ZIPCD': 'owner_zip',
                'LND_SQFOOT': 'land_sqft',
                'LND_VAL': 'land_value',
                'JV': 'just_value',
                'TV_NSD': 'taxable_value',
                'JV_CHNG': 'just_value_change',
                'SAL_PRC1': 'sale_price1',
                'SALE_YR1': 'sale_year1',
                'SALE_MO1': 'sale_month1',
                'SPEC_FEAT_VAL': 'special_features_value'
            }

            # Process records in batches
            processed_records = []
            for _, row in df.iterrows():
                try:
                    # Create clean record
                    record = {
                        'parcel_id': self.clean_text_value(row.get('PARCEL_ID')),
                        'county': 'BROWARD',
                        'year': 2025,
                        'owner_name': self.clean_text_value(row.get('OWN_NAME')),
                        'phy_addr1': self.clean_text_value(row.get('PHY_ADDR1')),
                        'phy_addr2': self.clean_text_value(row.get('PHY_ADDR2')),
                        'property_city': self.clean_text_value(row.get('PHY_CITY')),
                        'property_zip': self.clean_text_value(row.get('PHY_ZIPCD')),
                        'owner_addr1': self.clean_text_value(row.get('OWN_ADDR1')),
                        'owner_addr2': self.clean_text_value(row.get('OWN_ADDR2')),
                        'owner_city': self.clean_text_value(row.get('OWN_CITY')),
                        'owner_state': self.clean_text_value(row.get('OWN_STATE', ''))[:2] if row.get('OWN_STATE') else None,
                        'owner_zip': self.clean_text_value(row.get('OWN_ZIPCD')),
                        'land_sqft': self.clean_numeric_value(row.get('LND_SQFOOT')),
                        'land_value': self.clean_numeric_value(row.get('LND_VAL')),
                        'just_value': self.clean_numeric_value(row.get('JV')),
                        'taxable_value': self.clean_numeric_value(row.get('TV_NSD')),
                        'just_value_change': self.clean_numeric_value(row.get('JV_CHNG')),
                        'sale_price1': self.clean_numeric_value(row.get('SAL_PRC1')),
                        'sale_date': self.clean_date_value(row.get('SALE_YR1'), row.get('SALE_MO1')),
                        'special_features_value': self.clean_numeric_value(row.get('SPEC_FEAT_VAL')),
                        'created_at': datetime.now().isoformat()
                    }

                    # Only add records with valid parcel_id
                    if record['parcel_id']:
                        processed_records.append(record)

                except Exception as e:
                    logger.warning(f"Error processing record: {e}")
                    continue

            logger.info(f"Processed {len(processed_records)} valid records")
            return processed_records

        except Exception as e:
            logger.error(f"Error processing NAL file: {e}")
            return []

    def upload_batch(self, batch_data, batch_num):
        """Upload a batch of records to Supabase with retry logic"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                # Use upsert for conflict resolution
                result = self.supabase.table('florida_parcels').upsert(
                    batch_data,
                    on_conflict='parcel_id,county,year'
                ).execute()

                self.records_loaded += len(batch_data)

                # Calculate progress
                elapsed = time.time() - self.start_time
                rate = self.records_loaded / elapsed if elapsed > 0 else 0

                logger.info(f"✅ Batch {batch_num}: {len(batch_data)} records uploaded "
                           f"(Total: {self.records_loaded:,}, Rate: {rate:.0f} records/sec)")
                return True

            except Exception as e:
                logger.warning(f"⚠️ Batch {batch_num} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"❌ Batch {batch_num} failed after {max_retries} attempts")
                    return False

        return False

    def load_broward_properties(self):
        """Load Broward County property data with parallel processing"""
        self.start_time = time.time()
        logger.info("🚀 Starting live property data load for Broward County")

        # Check for NAL file
        nal_file = Path(BROWARD_DATA_PATH) / "NAL2025.csv"
        if not nal_file.exists():
            logger.error(f"NAL file not found: {nal_file}")
            return False

        # Process the NAL file
        records = self.process_nal_file(nal_file)
        if not records:
            logger.error("No valid records to upload")
            return False

        logger.info(f"📊 Preparing to upload {len(records):,} records in batches of {self.batch_size}")

        # Split into batches
        batches = [records[i:i + self.batch_size] for i in range(0, len(records), self.batch_size)]

        # Upload batches in parallel
        successful_uploads = 0
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all batch upload tasks
            future_to_batch = {
                executor.submit(self.upload_batch, batch, i + 1): i + 1
                for i, batch in enumerate(batches)
            }

            # Process completed uploads
            for future in as_completed(future_to_batch):
                batch_num = future_to_batch[future]
                try:
                    success = future.result()
                    if success:
                        successful_uploads += 1
                except Exception as e:
                    logger.error(f"❌ Batch {batch_num} execution error: {e}")

        # Final statistics
        elapsed = time.time() - self.start_time
        success_rate = (successful_uploads / len(batches)) * 100 if batches else 0

        logger.info(f"""
🎉 BROWARD COUNTY DATA LOAD COMPLETE!
════════════════════════════════════════
📈 Records Uploaded: {self.records_loaded:,}
⏱️  Total Time: {elapsed:.1f} seconds
🚀 Upload Rate: {self.records_loaded / elapsed:.0f} records/second
✅ Success Rate: {success_rate:.1f}%
📊 Batches Processed: {successful_uploads}/{len(batches)}
        """)

        return successful_uploads > 0

def main():
    """Main execution function"""
    print("🏠 ConcordBroker Live Property Data Loader")
    print("=" * 50)

    # Verify dependencies
    try:
        loader = PropertyDataLoader()

        # Test Supabase connection
        logger.info("Testing Supabase connection...")
        test_result = loader.supabase.table('florida_parcels').select('*').limit(1).execute()
        logger.info("✅ Supabase connection successful")

        # Load Broward County data
        success = loader.load_broward_properties()

        if success:
            print("\n🎊 SUCCESS! Property data is now live!")
            print("🌐 Visit http://localhost:5173/properties to see the data")
            print("📊 Database now contains real Florida property records")
        else:
            print("\n❌ Data load failed. Check logs for details.")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Application error: {e}")

if __name__ == "__main__":
    main()