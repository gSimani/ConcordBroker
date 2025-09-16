#!/usr/bin/env python3
"""
NAP Dedicated Table Importer
- Imports NAP data into dedicated broward_nap_2025 table
- Optimized for fast website extraction
- Handles all NAP fields with proper data types
"""

import csv
import hashlib
from datetime import datetime
from decimal import Decimal, InvalidOperation
from supabase import create_client, Client
import time

class NAPDedicatedImporter:
    def __init__(self):
        # Supabase connection
        self.url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
        self.service_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"
        self.supabase = create_client(self.url, self.service_key)
        
        # File and batch settings
        self.nap_file = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\NAP16P202501.csv"
        self.batch_size = 1000  # Optimized batch size
        self.max_retries = 3
        
        # Complete field mapping from NAP CSV to database
        self.field_mapping = {
            'CO_NO': 'co_no',
            'ACCT_ID': 'acct_id',
            'FILE_T': 'file_t',
            'ASMNT_YR': 'asmnt_yr',
            'TAX_AUTH_CD': 'tax_auth_cd',
            'NAICS_CD': 'naics_cd',
            'JV_F_F_E': 'jv_f_f_e',
            'JV_LESE_IMP': 'jv_lese_imp',
            'JV_TOTAL': 'jv_total',
            'AV_TOTAL': 'av_total',
            'JV_POL_CONTRL': 'jv_pol_contrl',
            'AV_POL_CONTRL': 'av_pol_contrl',
            'EXMPT_VAL': 'exmpt_val',
            'TAX_VAL': 'tax_val',
            'PEN_RATE': 'pen_rate',
            'OWN_NAM': 'own_nam',
            'OWN_ADDR': 'own_addr',
            'OWN_CITY': 'own_city',
            'OWN_STATE': 'own_state',
            'OWN_ZIPCD': 'own_zipcd',
            'OWN_STATE_DOM': 'own_state_dom',
            'FIDU_NAME': 'fidu_name',
            'FIDU_ADDR': 'fidu_addr',
            'FIDU_CITY': 'fidu_city',
            'FIDU_STATE': 'fidu_state',
            'FIDU_ZIPCD': 'fidu_zipcd',
            'FIDU_CD': 'fidu_cd',
            'PHY_ADDR': 'phy_addr',
            'PHY_CITY': 'phy_city',
            'PHY_ZIPCD': 'phy_zipcd',
            'FIL': 'fil',
            'ALT_KEY': 'alt_key',
            'EXMPT': 'exmpt',
            'ACCT_ID_CNG': 'acct_id_cng',
            'SEQ_NO': 'seq_no',
            'TS_ID': 'ts_id'
        }
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'successful_inserts': 0,
            'errors': 0,
            'start_time': None,
            'batch_times': []
        }

    def clean_value(self, value, data_type='text'):
        """Clean and validate field values with proper type conversion"""
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
        elif data_type == 'text':
            # Truncate very long text values to prevent database errors
            return value[:500] if len(value) > 500 else value
        
        return value

    def generate_data_hash(self, record):
        """Generate hash of record data for change detection"""
        # Create hash of key fields
        key_fields = ['acct_id', 'own_nam', 'jv_total', 'av_total', 'tax_val']
        hash_string = '|'.join(str(record.get(field, '')) for field in key_fields)
        return hashlib.md5(hash_string.encode()).hexdigest()

    def transform_record(self, csv_row, headers):
        """Transform CSV row to database record with proper data types"""
        record = {}
        
        # Decimal fields (financial values)
        decimal_fields = {
            'jv_f_f_e', 'jv_lese_imp', 'jv_total', 'av_total', 
            'jv_pol_contrl', 'av_pol_contrl', 'exmpt_val', 'tax_val', 'pen_rate'
        }
        
        # Integer fields
        integer_fields = {'asmnt_yr', 'seq_no'}
        
        for i, header in enumerate(headers):
            if header in self.field_mapping:
                db_field = self.field_mapping[header]
                raw_value = csv_row[i] if i < len(csv_row) else ''
                
                # Apply appropriate data type conversion
                if db_field in decimal_fields:
                    record[db_field] = self.clean_value(raw_value, 'decimal')
                elif db_field in integer_fields:
                    record[db_field] = self.clean_value(raw_value, 'int')
                else:
                    record[db_field] = self.clean_value(raw_value, 'text')
        
        # Add metadata
        record['county'] = 'BROWARD'
        record['data_source'] = 'NAP_2025'
        record['import_date'] = datetime.now().isoformat()
        record['update_date'] = datetime.now().isoformat()
        record['data_hash'] = self.generate_data_hash(record)
        
        return record

    def insert_batch(self, records):
        """Insert a batch of records with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Use simple insert (not upsert since this is a new table)
                result = self.supabase.table('broward_nap_2025').insert(records).execute()
                
                if result.data:
                    return len(result.data)
                    
            except Exception as e:
                error_msg = str(e)
                print(f"Batch insert attempt {attempt + 1} failed: {error_msg[:150]}")
                if attempt == self.max_retries - 1:
                    return 0
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return 0

    def check_table_exists(self):
        """Check if the broward_nap_2025 table exists"""
        try:
            # Try to query the table
            result = self.supabase.table('broward_nap_2025').select("*").limit(1).execute()
            return True
        except Exception as e:
            if "does not exist" in str(e).lower():
                return False
            return True  # Assume exists if different error

    def process_nap_file(self):
        """Process NAP CSV file in optimized batches"""
        print("=== PROCESSING NAP FILE INTO DEDICATED TABLE ===")
        print(f"File: {self.nap_file}")
        print(f"Target table: broward_nap_2025")
        print(f"Batch size: {self.batch_size}")
        
        # Check if table exists
        if not self.check_table_exists():
            print("ERROR: Table broward_nap_2025 does not exist!")
            print("Please run the SQL script: create_nap_table.sql first")
            return False
        
        self.stats['start_time'] = datetime.now()
        
        try:
            with open(self.nap_file, 'r', encoding='latin1') as f:
                reader = csv.reader(f)
                headers = next(reader)  # Skip header row
                
                print(f"NAP Headers found: {len(headers)}")
                print(f"Mapped fields: {len(self.field_mapping)}")
                
                batch = []
                batch_num = 0
                
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Transform CSV row to database record
                        record = self.transform_record(row, headers)
                        
                        # Skip records without account ID
                        if not record.get('acct_id'):
                            continue
                            
                        batch.append(record)
                        
                        # Process batch when full
                        if len(batch) >= self.batch_size:
                            batch_num += 1
                            batch_start = time.time()
                            
                            print(f"Processing batch {batch_num} (rows {row_num-len(batch)+1}-{row_num})")
                            
                            successful_records = self.insert_batch(batch)
                            if successful_records > 0:
                                batch_time = time.time() - batch_start
                                self.stats['batch_times'].append(batch_time)
                                self.stats['successful_inserts'] += successful_records
                                print(f"  Batch {batch_num}: {successful_records} records in {batch_time:.2f}s")
                            else:
                                print(f"  Batch {batch_num} FAILED")
                                self.stats['errors'] += len(batch)
                            
                            batch = []
                            self.stats['total_processed'] += self.batch_size
                            
                            # Progress update every 10 batches
                            if batch_num % 10 == 0:
                                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                                rate = self.stats['successful_inserts'] / elapsed if elapsed > 0 else 0
                                print(f"  Progress: {self.stats['successful_inserts']:,} inserts in {elapsed:.0f}s ({rate:.1f} rec/s)")
                    
                    except Exception as e:
                        print(f"Error processing row {row_num}: {str(e)[:100]}")
                        self.stats['errors'] += 1
                
                # Process final batch
                if batch:
                    batch_num += 1
                    print(f"Processing final batch {batch_num} ({len(batch)} records)")
                    successful_records = self.insert_batch(batch)
                    if successful_records > 0:
                        self.stats['successful_inserts'] += successful_records
                        print(f"  Final batch: {successful_records} records processed")
                    else:
                        print(f"  Final batch FAILED")
                        self.stats['errors'] += len(batch)
                    
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
            
            if self.stats['successful_inserts'] > 0:
                rate = self.stats['successful_inserts'] / elapsed
                print(f"Processing rate: {rate:.1f} records/second")
        
        print(f"Total records processed: {self.stats['total_processed']:,}")
        print(f"Successful inserts: {self.stats['successful_inserts']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        if self.stats['batch_times']:
            avg_batch_time = sum(self.stats['batch_times']) / len(self.stats['batch_times'])
            print(f"Average batch time: {avg_batch_time:.2f} seconds")

    def verify_import(self):
        """Verify the import by checking inserted records"""
        print("\n=== IMPORT VERIFICATION ===")
        
        try:
            # Get total count of imported records
            count_result = self.supabase.table('broward_nap_2025').select("*", count="exact").limit(1).execute()
            total_count = count_result.count if hasattr(count_result, 'count') else "Unknown"
            print(f"Total records in broward_nap_2025: {total_count}")
            
            # Get sample records
            sample = self.supabase.table('broward_nap_2025')\
                .select("acct_id,own_nam,phy_addr,phy_city,jv_total,av_total,tax_val")\
                .limit(5)\
                .execute()
            
            if sample.data:
                print(f"Sample NAP records:")
                for i, record in enumerate(sample.data):
                    acct_id = record.get('acct_id', 'N/A')
                    owner = record.get('own_nam', 'N/A')[:30]
                    address = record.get('phy_addr', 'N/A')[:25]
                    city = record.get('phy_city', 'N/A')
                    jv = record.get('jv_total', 0) or 0
                    av = record.get('av_total', 0) or 0
                    tv = record.get('tax_val', 0) or 0
                    print(f"  {i+1}. {acct_id} | {owner} | {address} | {city}")
                    print(f"     Just: ${jv:,.2f} | Assessed: ${av:,.2f} | Taxable: ${tv:,.2f}")
            
            # Check value statistics
            highest = self.supabase.table('broward_nap_2025')\
                .select("acct_id,own_nam,phy_city,jv_total")\
                .not_.is_('jv_total', 'null')\
                .order('jv_total', desc=True)\
                .limit(3).execute()
            
            if highest.data:
                print(f"\nHighest valued properties:")
                for i, record in enumerate(highest.data):
                    owner = record.get('own_nam', 'N/A')[:40]
                    city = record.get('phy_city', 'N/A')
                    value = record.get('jv_total', 0) or 0
                    print(f"  {i+1}. {owner} in {city}: ${value:,.2f}")
            
        except Exception as e:
            print(f"Error during verification: {e}")

    def run_import(self):
        """Execute the complete NAP import process"""
        print("=== NAP DEDICATED TABLE IMPORTER STARTING ===")
        print(f"Target database: {self.url}")
        print(f"Source file: {self.nap_file}")
        print("Strategy: Import into dedicated broward_nap_2025 table")
        
        # Process NAP file
        success = self.process_nap_file()
        
        # Print statistics
        self.print_statistics()
        
        # Verify import
        if success:
            self.verify_import()
        
        if success and self.stats['successful_inserts'] > 0:
            print("\n=== NAP IMPORT COMPLETED SUCCESSFULLY ===")
            print("Broward County NAP 2025 data has been imported into dedicated table.")
            print("The website can now access comprehensive property valuation data.")
        else:
            print("\n=== NAP IMPORT COMPLETED WITH ISSUES ===")
        
        return success

def main():
    importer = NAPDedicatedImporter()
    importer.run_import()

if __name__ == "__main__":
    main()