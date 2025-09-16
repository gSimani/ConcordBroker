#!/usr/bin/env python3
"""
Deploy tax certificates table and sample data to Supabase
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

def deploy_tax_certificates_table():
    """Deploy the tax certificates table to Supabase"""
    
    # Get Supabase credentials
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
    database_url = os.getenv('DATABASE_URL')
    
    if not all([supabase_url, supabase_key]):
        print("[ERROR] Missing Supabase credentials in .env file")
        print("Please ensure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are set")
        return False
    
    print("[INFO] Deploying tax certificates table to Supabase...")
    
    try:
        # If we have a direct database URL, use psycopg2
        if database_url:
            print("[INFO] Using direct database connection...")
            
            # Parse the database URL
            url = urlparse(database_url)
            
            # Connect to the database
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port,
                database=url.path[1:],
                user=url.username,
                password=url.password,
                sslmode='require'
            )
            
            cur = conn.cursor()
            
            # Read and execute the SQL file
            with open('create_tax_certificates_table.sql', 'r') as f:
                sql_script = f.read()
            
            # Execute the SQL script
            cur.execute(sql_script)
            conn.commit()
            
            print("[SUCCESS] Tax certificates table created successfully!")
            
            # Verify the table was created
            cur.execute("""
                SELECT COUNT(*) FROM tax_certificates;
            """)
            count = cur.fetchone()[0]
            print(f"[INFO] Table contains {count} sample certificates")
            
            cur.close()
            conn.close()
            
        else:
            print("[WARNING] No direct database URL found, using Supabase client...")
            
            # Create Supabase client
            supabase: Client = create_client(supabase_url, supabase_key)
            
            # Check if table exists by trying to query it
            try:
                result = supabase.table('tax_certificates').select('*').limit(1).execute()
                print("[SUCCESS] Tax certificates table already exists")
                print(f"[INFO] Table contains {len(result.data)} records")
            except:
                print("[ERROR] Tax certificates table doesn't exist")
                print("Please run the SQL script manually in Supabase SQL Editor:")
                print("1. Go to your Supabase dashboard")
                print("2. Navigate to SQL Editor")
                print("3. Copy and paste the contents of create_tax_certificates_table.sql")
                print("4. Run the script")
                return False
        
        print("\n[SUCCESS] Tax certificates table is ready!")
        print("\n[INFO] Sample data has been inserted for testing:")
        print("  - Parcel: 064210010010 (3 certificates)")
        print("  - Parcel: 064210020020 (1 certificate)")
        print("  - Parcel: 064210030030 (1 certificate)")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error deploying tax certificates table: {str(e)}")
        print("\n[TIP] To manually deploy:")
        print("1. Go to your Supabase dashboard")
        print("2. Navigate to SQL Editor")
        print("3. Copy and paste the contents of create_tax_certificates_table.sql")
        print("4. Run the script")
        return False

def test_tax_certificates_query():
    """Test querying tax certificates from Supabase"""
    
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
    
    if not all([supabase_url, supabase_key]):
        print("[ERROR] Missing Supabase credentials")
        return
    
    print("\n[TEST] Testing tax certificates query...")
    
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Query for a specific parcel
        test_parcel = '064210010010'
        result = supabase.table('tax_certificates') \
            .select('*') \
            .eq('parcel_id', test_parcel) \
            .order('tax_year', desc=True) \
            .execute()
        
        if result.data:
            print(f"[SUCCESS] Found {len(result.data)} certificates for parcel {test_parcel}")
            for cert in result.data:
                print(f"  - Certificate #{cert['certificate_number']}: ${cert['face_amount']} ({cert['status']})")
        else:
            print(f"[INFO] No certificates found for parcel {test_parcel}")
        
        # Query all active certificates
        active_result = supabase.table('tax_certificates') \
            .select('*') \
            .eq('status', 'active') \
            .execute()
        
        if active_result.data:
            print(f"\n[INFO] Total active certificates: {len(active_result.data)}")
            
            # Calculate total face amount
            total_amount = sum(cert['face_amount'] for cert in active_result.data)
            print(f"[INFO] Total face amount: ${total_amount:,.2f}")
        
    except Exception as e:
        print(f"[ERROR] Error testing query: {str(e)}")

if __name__ == "__main__":
    print("=" * 60)
    print("TAX CERTIFICATES TABLE DEPLOYMENT")
    print("=" * 60)
    
    # Deploy the table
    success = deploy_tax_certificates_table()
    
    if success:
        # Test the deployment
        test_tax_certificates_query()
    
    print("\n" + "=" * 60)
    print("Deployment complete!")
    print("=" * 60)