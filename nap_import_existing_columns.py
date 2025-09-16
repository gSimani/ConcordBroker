#!/usr/bin/env python3
"""
NAP Import using only existing columns in florida_parcels table
- Maps NAP fields to existing florida_parcels columns
- Performs batch updates/inserts for essential property data
- Optimized for fast website property extraction
"""

import csv
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from supabase import create_client, Client
import time

class NAPImporterExistingColumns:
    def __init__(self):
        # Supabase connection
        self.url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        self.service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
        self.supabase = create_client(self.url, self.service_key)
        
        # File and batch settings
        self.nap_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAP16P202501.csv"
        self.batch_size = 1000  # Larger batches for better performance
        self.max_retries = 3
        
        # Field mapping to EXISTING columns only
        self.existing_field_mapping = {
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
            'TAX_VAL': 'taxable_value'
        }
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_updates': 0,
            'errors': 0,
            'start_time': None,
            'batch_times': []
        }

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
        
        return value[:255] if len(str(value)) > 255 else value  # Truncate long values

    def transform_record(self, csv_row, headers):
        """Transform CSV row to database record using existing columns only"""
        record = {}
        
        for i, header in enumerate(headers):
            if header in self.existing_field_mapping:
                db_field = self.existing_field_mapping[header]
                raw_value = csv_row[i] if i < len(csv_row) else ''
                
                # Apply data type specific cleaning
                if db_field in ['just_value', 'assessed_value', 'taxable_value']:
                    record[db_field] = self.clean_value(raw_value, 'decimal')
                elif db_field == 'year':
                    record[db_field] = self.clean_value(raw_value, 'int')
                else:
                    record[db_field] = self.clean_value(raw_value, 'text')
        
        # Add metadata using existing columns
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
                    return len(result.data)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Batch upsert attempt {attempt + 1} failed: {error_msg[:150]}")
                if attempt == self.max_retries - 1:
                    return 0
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return 0

    def process_nap_file(self):
        """Process NAP CSV file in batches"""
        print("=== PROCESSING NAP FILE (EXISTING COLUMNS ONLY) ===")
        print(f"File: {self.nap_file}")
        print(f"Batch size: {self.batch_size}")
        print("Using existing florida_parcels columns only")
        
        self.stats['start_time'] = datetime.now()
        
        try:
            with open(self.nap_file, 'r', encoding='latin1') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                
                print(f"NAP Headers found: {len(headers)}")
                print(f"Mapped fields: {list(self.existing_field_mapping.values())}")
                
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
                            
                            successful_records = self.upsert_batch(batch)
                            if successful_records > 0:
                                batch_time = time.time() - batch_start
                                self.stats['batch_times'].append(batch_time)
                                self.stats['successful_updates'] += successful_records
                                print(f"  Batch {batch_num}: {successful_records} records in {batch_time:.2f}s")
                            else:
                                print(f"  Batch {batch_num} FAILED")
                                self.stats['errors'] += len(batch)
                            
                            batch = []
                            self.stats['total_processed'] += len(batch) if successful_records == 0 else successful_records
                            
                            # Progress update every 10 batches
                            if batch_num % 10 == 0:
                                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                                rate = self.stats['successful_updates'] / elapsed if elapsed > 0 else 0
                                print(f"  Progress: {self.stats['successful_updates']:,} successful updates in {elapsed:.0f}s ({rate:.1f} rec/s)")
                    
                    except Exception as e:
                        print(f"Error processing row {row_num}: {str(e)[:100]}")
                        self.stats['errors'] += 1
                
                # Process final batch
                if batch:
                    batch_num += 1
                    print(f"Processing final batch {batch_num} ({len(batch)} records)")
                    successful_records = self.upsert_batch(batch)
                    if successful_records > 0:
                        self.stats['successful_updates'] += successful_records
                        print(f"  Final batch: {successful_records} records processed")
                    else:
                        print(f"  Final batch FAILED")
                        self.stats['errors'] += len(batch)
                    
                    self.stats['total_processed'] += successful_records if successful_records > 0 else len(batch)
                
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
            
            if self.stats['successful_updates'] > 0:
                rate = self.stats['successful_updates'] / elapsed
                print(f"Processing rate: {rate:.1f} records/second")
        
        print(f"Total records processed: {self.stats['total_processed']:,}")
        print(f"Successful updates: {self.stats['successful_updates']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        if self.stats['batch_times']:
            avg_batch_time = sum(self.stats['batch_times']) / len(self.stats['batch_times'])
            print(f"Average batch time: {avg_batch_time:.2f} seconds")

    def verify_import(self):
        """Verify the import by checking updated records"""
        print("\n=== IMPORT VERIFICATION ===")
        
        try:
            # Get total count of records
            count_result = self.supabase.table('florida_parcels').select("*", count="exact").limit(1).execute()
            total_count = count_result.count if hasattr(count_result, 'count') else "Unknown"
            print(f"Total records in florida_parcels: {total_count}")
            
            # Get sample of updated records
            sample = self.supabase.table('florida_parcels')\
                .select("parcel_id,owner_name,phy_addr1,phy_city,just_value,assessed_value,data_source,update_date")\
                .eq('data_source', 'NAP_2025')\
                .limit(5)\
                .execute()
            
            if sample.data:
                print(f"Sample NAP records found: {len(sample.data)}")
                for i, record in enumerate(sample.data):
                    print(f"  {i+1}. {record.get('parcel_id')} | {record.get('owner_name')} | {record.get('phy_addr1')}")
            else:
                print("No NAP records found - checking all records...")
                
                # Check any records with values
                all_sample = self.supabase.table('florida_parcels')\
                    .select("parcel_id,owner_name,just_value,assessed_value")\
                    .not_.is_('owner_name', 'null')\
                    .limit(5)\
                    .execute()
                
                if all_sample.data:
                    print(f"Records with owner names: {len(all_sample.data)}")
                    for record in all_sample.data:
                        print(f"  - {record.get('parcel_id')}: {record.get('owner_name')}")
            
        except Exception as e:
            print(f"Error during verification: {e}")

    def run_import(self):
        """Execute the complete NAP import process"""
        print("=== NAP IMPORTER (EXISTING COLUMNS) STARTING ===")
        print(f"Target database: {self.url}")
        print(f"Source file: {self.nap_file}")
        print("Strategy: Update existing florida_parcels with NAP data using existing columns")
        
        # Process NAP file
        success = self.process_nap_file()
        
        # Print statistics
        self.print_statistics()
        
        # Verify import
        self.verify_import()
        
        if success and self.stats['successful_updates'] > 0:
            print("\n=== NAP IMPORT COMPLETED SUCCESSFULLY ===")
            print("Essential property data has been imported using existing table structure.")
            print("For additional fields, table schema modification may be needed.")
        else:
            print("\n=== NAP IMPORT COMPLETED WITH ISSUES ===")
        
        return success

def main():
    importer = NAPImporterExistingColumns()
    importer.run_import()

if __name__ == "__main__":
    main()