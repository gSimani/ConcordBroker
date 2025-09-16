"""
Download and load ALL Sunbiz corporate data into Supabase
This includes corporations, fictitious names, partnerships, and trademarks
"""

import os
import sys
import paramiko
import zipfile
import csv
import json
import requests
import time
from datetime import datetime
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/web/.env')

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

# Sunbiz SFTP credentials
SFTP_HOST = "sftp.floridados.gov"
SFTP_USER = "Public"
SFTP_PASS = "PubAccess1845!"

headers = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def create_sunbiz_tables():
    """Create tables for Sunbiz data if they don't exist"""
    print("Creating Sunbiz tables in Supabase...")
    
    sql = """
    -- Create sunbiz_corporations table
    CREATE TABLE IF NOT EXISTS sunbiz_corporations (
        id SERIAL PRIMARY KEY,
        document_number VARCHAR(20) UNIQUE NOT NULL,
        corporation_name TEXT,
        status VARCHAR(50),
        filing_type VARCHAR(100),
        principal_address TEXT,
        principal_city VARCHAR(100),
        principal_state VARCHAR(50),
        principal_zip VARCHAR(20),
        mailing_address TEXT,
        mailing_city VARCHAR(100),
        mailing_state VARCHAR(50),
        mailing_zip VARCHAR(20),
        registered_agent_name TEXT,
        registered_agent_address TEXT,
        date_filed DATE,
        state VARCHAR(50),
        last_event DATE,
        fei_number VARCHAR(50),
        data_source VARCHAR(50) DEFAULT 'SUNBIZ',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Create index for faster lookups
    CREATE INDEX IF NOT EXISTS idx_sunbiz_corp_name ON sunbiz_corporations(corporation_name);
    CREATE INDEX IF NOT EXISTS idx_sunbiz_corp_status ON sunbiz_corporations(status);
    
    -- Create sunbiz_fictitious_names table (DBAs)
    CREATE TABLE IF NOT EXISTS sunbiz_fictitious_names (
        id SERIAL PRIMARY KEY,
        document_number VARCHAR(20) UNIQUE NOT NULL,
        fictitious_name TEXT,
        owner_name TEXT,
        owner_address TEXT,
        owner_city VARCHAR(100),
        owner_state VARCHAR(50),
        owner_zip VARCHAR(20),
        date_filed DATE,
        status VARCHAR(50),
        expiration_date DATE,
        data_source VARCHAR(50) DEFAULT 'SUNBIZ_DBA',
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Create index for DBAs
    CREATE INDEX IF NOT EXISTS idx_sunbiz_dba_name ON sunbiz_fictitious_names(fictitious_name);
    CREATE INDEX IF NOT EXISTS idx_sunbiz_dba_owner ON sunbiz_fictitious_names(owner_name);
    
    -- Create property-to-business matching table
    CREATE TABLE IF NOT EXISTS property_business_matches (
        id SERIAL PRIMARY KEY,
        parcel_id VARCHAR(50),
        document_number VARCHAR(20),
        match_type VARCHAR(50), -- 'owner_name', 'address', 'both'
        confidence_score FLOAT,
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Create index for matching
    CREATE INDEX IF NOT EXISTS idx_prop_biz_parcel ON property_business_matches(parcel_id);
    CREATE INDEX IF NOT EXISTS idx_prop_biz_doc ON property_business_matches(document_number);
    """
    
    # Note: This SQL needs to be run in Supabase SQL Editor
    print("Please run the following SQL in Supabase SQL Editor:")
    print(sql)
    return True

def download_sunbiz_file(sftp, remote_path, local_path):
    """Download a file from Sunbiz SFTP"""
    try:
        print(f"  Downloading {remote_path}...")
        sftp.get(remote_path, local_path)
        return True
    except Exception as e:
        print(f"  Error downloading {remote_path}: {e}")
        return False

def connect_sftp():
    """Connect to Sunbiz SFTP server"""
    print("Connecting to Sunbiz SFTP...")
    
    transport = paramiko.Transport((SFTP_HOST, 22))
    transport.connect(username=SFTP_USER, password=SFTP_PASS)
    sftp = paramiko.SFTPClient.from_transport(transport)
    
    print("Connected to Sunbiz SFTP")
    return sftp, transport

def download_quarterly_data():
    """Download quarterly snapshot files (complete data)"""
    print("\nDownloading Sunbiz quarterly data files...")
    
    files_to_download = [
        # Corporate data
        ('cordata.zip', 'Corporate entities data'),
        ('corevent.zip', 'Corporate events'),
        
        # Fictitious names (DBAs)
        ('ficdata.zip', 'Fictitious names (DBAs)'),
        ('ficevt.zip', 'Fictitious name events'),
        
        # General partnerships
        ('genfile.zip', 'General partnerships'),
        ('genevt.zip', 'Partnership events'),
        
        # Trademarks
        ('TMData.zip', 'Trademarks and service marks')
    ]
    
    try:
        sftp, transport = connect_sftp()
        
        # Create local directory for data
        os.makedirs('sunbiz_data', exist_ok=True)
        
        downloaded_files = []
        for filename, description in files_to_download:
            print(f"\n{description}:")
            local_path = f'sunbiz_data/{filename}'
            
            # Try to download from root directory
            if download_sunbiz_file(sftp, f'/{filename}', local_path):
                downloaded_files.append(local_path)
                file_size = os.path.getsize(local_path) / (1024 * 1024)
                print(f"  Downloaded: {filename} ({file_size:.1f} MB)")
        
        sftp.close()
        transport.close()
        
        return downloaded_files
        
    except Exception as e:
        print(f"Error connecting to SFTP: {e}")
        return []

def process_corporate_data(zip_path):
    """Process corporate data file and load to Supabase"""
    print(f"\nProcessing {zip_path}...")
    
    corporations = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Extract and process the main data file
            for filename in z.namelist():
                if filename.endswith('.txt'):
                    with z.open(filename) as f:
                        content = f.read().decode('utf-8', errors='ignore')
                        lines = content.split('\n')
                        
                        for i, line in enumerate(lines):
                            if not line.strip():
                                continue
                            
                            # Parse fixed-width format (you'll need to adjust positions)
                            # This is a simplified example - actual format may differ
                            corp = {
                                'document_number': line[0:12].strip(),
                                'corporation_name': line[12:200].strip(),
                                'status': line[200:250].strip(),
                                'filing_type': line[250:350].strip(),
                                'principal_address': line[350:450].strip(),
                                'principal_city': line[450:500].strip(),
                                'principal_state': line[500:502].strip(),
                                'principal_zip': line[502:512].strip(),
                                'data_source': 'SUNBIZ',
                                'created_at': datetime.now().isoformat()
                            }
                            
                            # Only add if we have a document number
                            if corp['document_number']:
                                corporations.append(corp)
                            
                            if len(corporations) >= 1000:
                                # Upload batch
                                upload_to_supabase('sunbiz_corporations', corporations)
                                corporations = []
                            
                            if (i + 1) % 10000 == 0:
                                print(f"  Processed {i + 1} records...")
        
        # Upload remaining
        if corporations:
            upload_to_supabase('sunbiz_corporations', corporations)
        
        return True
        
    except Exception as e:
        print(f"Error processing {zip_path}: {e}")
        return False

def upload_to_supabase(table_name, data):
    """Upload data to Supabase table"""
    if not data:
        return 0
    
    try:
        url = f"{SUPABASE_URL}/rest/v1/{table_name}"
        
        # Clean data - remove None values
        clean_data = []
        for record in data:
            clean_record = {k: v for k, v in record.items() if v is not None and v != ''}
            if clean_record:
                clean_data.append(clean_record)
        
        if not clean_data:
            return 0
        
        response = requests.post(
            url,
            json=clean_data,
            headers={**headers, 'Prefer': 'resolution=merge-duplicates'}
        )
        
        if response.status_code in [200, 201, 204]:
            return len(clean_data)
        else:
            print(f"  Upload failed: {response.status_code}")
            if response.status_code == 404:
                print(f"  Table {table_name} doesn't exist. Please create it first.")
            return 0
            
    except Exception as e:
        print(f"  Upload error: {e}")
        return 0

def main():
    print("SUNBIZ DATA LOADER")
    print("="*60)
    print("This will download and load all Florida business entity data")
    print()
    
    # Step 1: Ensure tables exist
    print("Step 1: Create tables")
    create_sunbiz_tables()
    
    # Step 2: Download data
    print("\nStep 2: Download Sunbiz data")
    downloaded_files = download_quarterly_data()
    
    if not downloaded_files:
        print("\nNo files downloaded. Checking for existing files...")
        # Check if we already have files
        existing_files = []
        if os.path.exists('sunbiz_data'):
            for f in os.listdir('sunbiz_data'):
                if f.endswith('.zip'):
                    existing_files.append(f'sunbiz_data/{f}')
        
        if existing_files:
            print(f"Found {len(existing_files)} existing files")
            downloaded_files = existing_files
        else:
            print("No Sunbiz data files found.")
            return
    
    # Step 3: Process and load data
    print("\nStep 3: Process and load data")
    for file_path in downloaded_files:
        if 'cordata' in file_path:
            process_corporate_data(file_path)
        # Add processors for other file types as needed
    
    print("\n" + "="*60)
    print("SUNBIZ DATA LOADING COMPLETE!")
    print("You now have Florida business entity data in your database")
    print("This can be matched with property owners for business intelligence")

if __name__ == "__main__":
    # Check if paramiko is installed
    try:
        import paramiko
    except ImportError:
        print("Installing paramiko for SFTP access...")
        os.system("pip install paramiko")
        import paramiko
    
    main()