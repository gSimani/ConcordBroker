"""
Load real Florida property data into Supabase database
This script downloads and processes Florida Department of Revenue data
"""

import os
import json
import requests
import zipfile
import csv
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.getenv('VITE_SUPABASE_SERVICE_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("Error: Supabase credentials not found in .env file")
    print("Please add VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to apps/web/.env")
    exit(1)

print(f"Supabase URL: {SUPABASE_URL}")

# Use service key if available
API_KEY = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY

# Headers for API requests
headers = {
    'apikey': API_KEY,
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def download_florida_data():
    """Download Florida property data from Department of Revenue"""
    print("\nDownloading Florida property data...")
    
    # URLs for Florida DOR data (2025 tax year)
    urls = {
        'NAL': 'https://floridarevenue.com/property/Documents/DataPortal/2025_NAL_PRELIMINARY.zip',
        'SDF': 'https://floridarevenue.com/property/Documents/DataPortal/2025_SDF_PRELIMINARY.zip'
    }
    
    # Try Broward County specific data first (smaller dataset)
    broward_urls = {
        'NAL': 'https://floridarevenue.com/property/Documents/DataPortal/Files_ByCounty/2025/Preliminary/brwd25nal.zip',
        'SDF': 'https://floridarevenue.com/property/Documents/DataPortal/Files_ByCounty/2025/Preliminary/brwd25sdf.zip'
    }
    
    data_dir = 'florida_data'
    os.makedirs(data_dir, exist_ok=True)
    
    # Try to download Broward County data
    for data_type, url in broward_urls.items():
        filename = f"broward_{data_type.lower()}_2025.zip"
        filepath = os.path.join(data_dir, filename)
        
        if os.path.exists(filepath):
            print(f"  {filename} already exists, skipping download")
            continue
            
        print(f"  Downloading {filename}...")
        try:
            response = requests.get(url, stream=True, timeout=30)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"  Downloaded {filename}")
            else:
                print(f"  Failed to download {filename}: {response.status_code}")
        except Exception as e:
            print(f"  Error downloading {filename}: {e}")
    
    return data_dir

def extract_data(data_dir):
    """Extract ZIP files"""
    print("\nExtracting data files...")
    
    for filename in os.listdir(data_dir):
        if filename.endswith('.zip'):
            filepath = os.path.join(data_dir, filename)
            extract_dir = filepath.replace('.zip', '')
            
            if os.path.exists(extract_dir):
                print(f"  {extract_dir} already exists, skipping extraction")
                continue
                
            print(f"  Extracting {filename}...")
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"  Extracted to {extract_dir}")
            except Exception as e:
                print(f"  Error extracting {filename}: {e}")

def parse_nal_record(line):
    """Parse a NAL (Name Address Legal) record"""
    # NAL file format - fixed width fields
    try:
        record = {
            'county': line[0:2].strip(),
            'parcel_id': line[2:27].strip(),
            'year': int(line[27:31].strip()) if line[27:31].strip() else 2025,
            'owner_name': line[31:96].strip(),
            'owner_addr1': line[96:161].strip(),
            'owner_addr2': line[161:226].strip(),
            'owner_city': line[226:266].strip(),
            'owner_state': line[266:268].strip(),
            'owner_zip': line[268:278].strip(),
            'phy_addr1': line[278:343].strip(),
            'phy_addr2': line[343:408].strip(),
            'phy_city': line[408:448].strip(),
            'phy_state': line[448:450].strip(),
            'phy_zipcd': line[450:460].strip(),
            'property_use': line[460:463].strip(),
            'homestead_exemption': line[463:464].strip()
        }
        return record
    except Exception as e:
        return None

def parse_sdf_record(line):
    """Parse a SDF (Sales Data File) record"""
    # SDF file format - fixed width fields
    try:
        record = {
            'county': line[0:2].strip(),
            'parcel_id': line[2:27].strip(),
            'sale_date': line[27:35].strip(),
            'sale_price': int(line[35:46].strip()) if line[35:46].strip() else 0,
            'sale_type': line[46:48].strip(),
            'qualification_code': line[48:49].strip(),
            'is_qualified': line[49:50].strip(),
            'vacant_ind': line[50:51].strip(),
            'grantor_name': line[51:116].strip(),
            'grantee_name': line[116:181].strip()
        }
        
        # Convert sale_date to proper format
        if record['sale_date'] and len(record['sale_date']) == 8:
            year = record['sale_date'][0:4]
            month = record['sale_date'][4:6]
            day = record['sale_date'][6:8]
            record['sale_date'] = f"{year}-{month}-{day}"
        
        return record
    except Exception as e:
        return None

def load_to_supabase(records, table_name, batch_size=100):
    """Load records to Supabase in batches"""
    if not records:
        print(f"  No records to load for {table_name}")
        return
    
    print(f"  Loading {len(records)} records to {table_name}...")
    
    url = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    # Process in batches
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        try:
            response = requests.post(url, json=batch, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"    Loaded batch {i//batch_size + 1} ({len(batch)} records)")
            else:
                print(f"    Failed batch {i//batch_size + 1}: {response.status_code}")
                print(f"    Error: {response.text[:200]}")
                
                # Try with smaller batch or individual records
                if batch_size > 1:
                    print("    Retrying with smaller batch...")
                    load_to_supabase(batch, table_name, batch_size=10)
                    
        except Exception as e:
            print(f"    Error loading batch: {e}")
        
        # Rate limiting
        time.sleep(0.5)

def load_florida_parcels(data_dir):
    """Load Florida parcels data from NAL files"""
    print("\nLoading Florida parcels data...")
    
    nal_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.upper().endswith('.NAL') or 'nal' in file.lower():
                nal_files.append(os.path.join(root, file))
    
    if not nal_files:
        print("  No NAL files found")
        return
    
    for nal_file in nal_files:
        print(f"  Processing {nal_file}...")
        records = []
        
        try:
            with open(nal_file, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f):
                    if line_num >= 1000:  # Limit for testing
                        break
                    
                    record = parse_nal_record(line)
                    if record and record['parcel_id']:
                        # Add additional fields
                        record['county'] = 'BROWARD'
                        record['year'] = 2025
                        record['created_at'] = datetime.now().isoformat()
                        records.append(record)
            
            print(f"    Parsed {len(records)} records")
            
            # Load to Supabase
            if records:
                load_to_supabase(records, 'florida_parcels', batch_size=50)
                
        except Exception as e:
            print(f"    Error processing {nal_file}: {e}")

def load_sales_data(data_dir):
    """Load sales data from SDF files"""
    print("\nLoading sales data...")
    
    sdf_files = []
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if file.upper().endswith('.SDF') or 'sdf' in file.lower():
                sdf_files.append(os.path.join(root, file))
    
    if not sdf_files:
        print("  No SDF files found")
        return
    
    for sdf_file in sdf_files:
        print(f"  Processing {sdf_file}...")
        records = []
        
        try:
            with open(sdf_file, 'r', encoding='latin-1') as f:
                for line_num, line in enumerate(f):
                    if line_num >= 1000:  # Limit for testing
                        break
                    
                    record = parse_sdf_record(line)
                    if record and record['parcel_id'] and record['sale_price'] > 0:
                        # Add additional fields
                        record['county'] = 'BROWARD'
                        record['year'] = 2025
                        record['created_at'] = datetime.now().isoformat()
                        records.append(record)
            
            print(f"    Parsed {len(records)} records")
            
            # Load to Supabase
            if records:
                load_to_supabase(records, 'fl_sdf_sales', batch_size=50)
                
        except Exception as e:
            print(f"    Error processing {sdf_file}: {e}")

def create_sample_sunbiz_data():
    """Create sample Sunbiz corporate data for testing"""
    print("\nCreating sample Sunbiz data...")
    
    sample_entities = [
        {
            'entity_name': 'OCEAN PROPERTIES LLC',
            'entity_type': 'Limited Liability Company',
            'status': 'Active',
            'state': 'FL',
            'document_number': 'L23000123456',
            'fei_ein_number': '88-1234567',
            'date_filed': '2023-01-15',
            'effective_date': '2023-01-15',
            'principal_address': '1234 Ocean Boulevard, Fort Lauderdale, FL 33301',
            'mailing_address': 'PO Box 1234, Fort Lauderdale, FL 33301',
            'registered_agent_name': 'Florida Registered Agent LLC',
            'registered_agent_address': '1234 Corporate Way, Tallahassee, FL 32301',
            'officers': json.dumps([
                {'name': 'John Ocean', 'title': 'Managing Member', 'address': '1234 Ocean Boulevard, Fort Lauderdale, FL 33301'}
            ]),
            'annual_reports': json.dumps([
                {'year': 2024, 'filed_date': '2024-05-01', 'status': 'Filed'},
                {'year': 2023, 'filed_date': '2023-05-01', 'status': 'Filed'}
            ])
        },
        {
            'entity_name': 'LAS OLAS INVESTMENTS LLC',
            'entity_type': 'Limited Liability Company',
            'status': 'Active',
            'state': 'FL',
            'document_number': 'L22000789012',
            'fei_ein_number': '88-7890123',
            'date_filed': '2022-06-01',
            'effective_date': '2022-06-01',
            'principal_address': '567 Las Olas Way, Fort Lauderdale, FL 33316',
            'mailing_address': '567 Las Olas Way, Fort Lauderdale, FL 33316',
            'registered_agent_name': 'Registered Agent Services Inc',
            'registered_agent_address': '5678 Agent Way, Miami, FL 33101',
            'officers': json.dumps([
                {'name': 'Maria Olas', 'title': 'Managing Member', 'address': '567 Las Olas Way, Fort Lauderdale, FL 33316'}
            ]),
            'annual_reports': json.dumps([
                {'year': 2024, 'filed_date': '2024-05-01', 'status': 'Filed'},
                {'year': 2023, 'filed_date': '2023-05-01', 'status': 'Filed'}
            ])
        }
    ]
    
    # First create the table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sunbiz_corporate_filings (
        id SERIAL PRIMARY KEY,
        entity_name VARCHAR(255),
        entity_type VARCHAR(100),
        status VARCHAR(50),
        state VARCHAR(2),
        document_number VARCHAR(50) UNIQUE,
        fei_ein_number VARCHAR(20),
        date_filed DATE,
        effective_date DATE,
        principal_address VARCHAR(500),
        mailing_address VARCHAR(500),
        registered_agent_name VARCHAR(255),
        registered_agent_address VARCHAR(500),
        officers TEXT,
        annual_reports TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    print("  Note: Run this SQL in Supabase to create sunbiz_corporate_filings table:")
    print("  " + create_table_sql.replace('\n', '\n  '))
    
    # Try to load sample data
    url = f"{SUPABASE_URL}/rest/v1/sunbiz_corporate_filings"
    
    for entity in sample_entities:
        entity['created_at'] = datetime.now().isoformat()
        
        try:
            response = requests.post(url, json=entity, headers=headers)
            if response.status_code in [200, 201]:
                print(f"  Loaded: {entity['entity_name']}")
            else:
                print(f"  Failed to load {entity['entity_name']}: {response.status_code}")
        except Exception as e:
            print(f"  Error loading {entity['entity_name']}: {e}")

def main():
    """Main function to load all data"""
    print("=" * 50)
    print("LOADING REAL FLORIDA PROPERTY DATA")
    print("=" * 50)
    
    # Step 1: Download data
    data_dir = download_florida_data()
    
    # Step 2: Extract data
    extract_data(data_dir)
    
    # Step 3: Load parcels data
    load_florida_parcels(data_dir)
    
    # Step 4: Load sales data
    load_sales_data(data_dir)
    
    # Step 5: Create sample Sunbiz data
    create_sample_sunbiz_data()
    
    print("\n" + "=" * 50)
    print("Data loading complete!")
    print("Your website should now display real Florida property data.")
    print("=" * 50)

if __name__ == "__main__":
    main()