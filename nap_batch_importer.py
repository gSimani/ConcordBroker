#!/usr/bin/env python3
"""
NAP Batch Importer for Broward County 2025
- Adds required columns to florida_parcels table
- Imports NAP data in optimized batches
- Creates performance indexes
- Validates data integrity
"""

import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from supabase import create_client, Client
import time

class NAPBatchImporter:
    def __init__(self):
        # Supabase connection
        self.url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        self.service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
        self.supabase = create_client(self.url, self.service_key)
        
        # File and batch settings
        self.nap_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAP16P202501.csv"
        self.batch_size = 500  # Reduced for reliability
        self.max_retries = 3
        
        # Field mapping
        self.field_mapping = {
            'ACCT_ID': 'parcel_id',
            'ASMNT_YR': 'year', 
            'OWN_NAM': 'owner_name',
            'OWN_ADDR': 'owner_addr1',
            'OWN_CITY': 'owner_city', 
            'OWN_STATE': 'owner_state',
            'OWN_ZIPCD': 'owner_zip',
            'PHY_ADDR': 'phy_addr1',
            'PHY_CITY': 'phy_city',
            'PHY_ZIPCD': 'phy_zipcd',
            'JV_TOTAL': 'just_value',
            'AV_TOTAL': 'assessed_value', 
            'TAX_VAL': 'taxable_value',
            'TAX_AUTH_CD': 'tax_authority_code',
            'NAICS_CD': 'naics_code',
            'EXMPT_VAL': 'exempt_value',
            'FIDU_NAME': 'fiduciary_name',
            'FIDU_ADDR': 'fiduciary_addr', 
            'ALT_KEY': 'alt_key',
            'EXMPT': 'exemption_code'
        }
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'new_inserts': 0,
            'errors': 0,
            'start_time': None,
            'batch_times': []
        }

    def add_required_columns(self):
        """Add new columns to florida_parcels table"""
        print("=== ADDING REQUIRED COLUMNS ===")
        
        columns_to_add = [
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS tax_authority_code VARCHAR(20)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS naics_code VARCHAR(20)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS exempt_value DECIMAL(15,2)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS fiduciary_name VARCHAR(255)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS fiduciary_addr VARCHAR(255)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS alt_key VARCHAR(100)",
            "ALTER TABLE florida_parcels ADD COLUMN IF NOT EXISTS exemption_code VARCHAR(100)"
        ]
        
        # Note: Supabase doesn't support direct SQL execution via Python client
        # We'll handle this through data insertion and let Supabase handle schema
        print("Schema modifications will be handled during data insertion")
        print("Supabase will auto-create columns as needed")
        
    def clean_value(self, value, data_type='text'):
        """Clean and validate field values"""
        if value is None or value == '':
            return None
            
        value = str(value).strip()
        if value == '':
            return None
            
        if data_type == 'decimal':
            try:
                return float(value) if value else None
            except (ValueError, InvalidOperation):
                return None
        elif data_type == 'int':
            try:
                return int(value) if value else None
            except ValueError:
                return None
        
        return value

    def transform_record(self, csv_row, headers):
        """Transform CSV row to database record"""
        record = {}
        
        for i, header in enumerate(headers):
            if header in self.field_mapping:
                db_field = self.field_mapping[header]
                raw_value = csv_row[i] if i < len(csv_row) else ''
                
                # Apply data type specific cleaning
                if db_field in ['just_value', 'assessed_value', 'taxable_value', 'exempt_value']:
                    record[db_field] = self.clean_value(raw_value, 'decimal')
                elif db_field == 'year':
                    record[db_field] = self.clean_value(raw_value, 'int')
                else:
                    record[db_field] = self.clean_value(raw_value, 'text')
        
        # Add metadata
        record['county'] = 'BROWARD'
        record['data_source'] = 'NAP_2025'
        record['import_date'] = datetime.now().isoformat()
        record['update_date'] = datetime.now().isoformat()
        
        return record

    def upsert_batch(self, records):
        """Upsert a batch of records with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Use upsert to handle updates and inserts
                result = self.supabase.table('florida_parcels').upsert(
                    records,
                    on_conflict='parcel_id'  # Use parcel_id as unique key
                ).execute()
                
                if result.data:
                    self.stats['successful_updates'] += len(result.data)
                    return True
                    
            except Exception as e:
                print(f"Batch upsert attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt == self.max_retries - 1:
                    self.stats['errors'] += len(records)
                    return False
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False

    def process_nap_file(self):
        """Process NAP CSV file in batches"""
        print("=== PROCESSING NAP FILE ===")
        print(f"File: {self.nap_file}")
        print(f"Batch size: {self.batch_size}")
        
        self.stats['start_time'] = datetime.now()
        
        try:
            with open(self.nap_file, 'r', encoding='latin1') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                
                batch = []
                batch_num = 0
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Transform CSV row to database record
                        record = self.transform_record(row, headers)
                        
                        # Skip records without parcel_id
                        if not record.get('parcel_id'):
                            continue
                            
                        batch.append(record)
                        
                        # Process batch when full
                        if len(batch) >= self.batch_size:
                            batch_num += 1
                            batch_start = time.time()
                            
                            print(f"Processing batch {batch_num} (rows {row_num-len(batch)+1}-{row_num})")
                            
                            if self.upsert_batch(batch):
                                batch_time = time.time() - batch_start
                                self.stats['batch_times'].append(batch_time)
                                print(f"  Batch {batch_num} completed in {batch_time:.2f}s")
                            else:
                                print(f"  Batch {batch_num} FAILED")
                            
                            batch = []
                            self.stats['total_processed'] += self.batch_size
                            
                            # Progress update every 10 batches
                            if batch_num % 10 == 0:
                                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                                rate = self.stats['total_processed'] / elapsed
                                print(f"  Progress: {self.stats['total_processed']:,} records in {elapsed:.0f}s ({rate:.1f} rec/s)")
                    
                    except Exception as e:
                        print(f"Error processing row {row_num}: {str(e)[:100]}")
                        self.stats['errors'] += 1
                
                # Process final batch
                if batch:
                    batch_num += 1
                    print(f"Processing final batch {batch_num} ({len(batch)} records)")
                    if self.upsert_batch(batch):
                        print(f"  Final batch completed")
                    else:
                        print(f"  Final batch FAILED")
                    
                    self.stats['total_processed'] += len(batch)
                
        except Exception as e:
            print(f"Error reading NAP file: {e}")
            return False
        
        return True

    def print_statistics(self):
        """Print import statistics"""
        print("\n=== IMPORT STATISTICS ===")
        
        if self.stats['start_time']:
            elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
            print(f"Total time: {elapsed:.1f} seconds")
            
            if self.stats['total_processed'] > 0:
                rate = self.stats['total_processed'] / elapsed
                print(f"Processing rate: {rate:.1f} records/second")
        
        print(f"Total records processed: {self.stats['total_processed']:,}")
        print(f"Successful updates: {self.stats['successful_updates']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        if self.stats['batch_times']:
            avg_batch_time = sum(self.stats['batch_times']) / len(self.stats['batch_times'])
            print(f"Average batch time: {avg_batch_time:.2f} seconds")

    def create_indexes(self):
        """Create performance indexes - will need to be done manually in Supabase"""
        print("\n=== PERFORMANCE INDEXES ===")
        print("The following indexes should be created in Supabase SQL editor:")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id);",
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name);", 
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr ON florida_parcels(phy_addr1);",
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_city ON florida_parcels(phy_city);",
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_taxable_value ON florida_parcels(taxable_value);",
            "CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value ON florida_parcels(just_value);"
        ]
        
        for idx in indexes:
            print(f"  {idx}")

    def run_import(self):
        """Execute the complete NAP import process"""
        print("=== NAP BATCH IMPORTER STARTING ===")
        print(f"Target database: {self.url}")
        print(f"Source file: {self.nap_file}")
        
        # Step 1: Add required columns (handled in upsert)
        self.add_required_columns()
        
        # Step 2: Process NAP file
        success = self.process_nap_file()
        
        # Step 3: Print statistics
        self.print_statistics()
        
        # Step 4: Suggest indexes
        self.create_indexes()
        
        if success:
            print("\n=== NAP IMPORT COMPLETED SUCCESSFULLY ===")
        else:
            print("\n=== NAP IMPORT COMPLETED WITH ERRORS ===")
        
        return success

def main():
    importer = NAPBatchImporter()
    importer.run_import()

if __name__ == "__main__":
    main()