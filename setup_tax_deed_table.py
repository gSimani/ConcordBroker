"""
Set up Supabase table for tax deed properties
"""
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Need service role key for table creation

if not SUPABASE_KEY:
    print("SUPABASE_SERVICE_ROLE_KEY not found in environment variables")
    print("Using anon key - table may already exist")
    SUPABASE_KEY = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjU0ODI2MzQsImV4cCI6MjA0MTA1ODYzNH0.nArQA_3BKm8wPq3eOYUQJpYZMgTPh0Tz_4CvpEfww1A')

def check_table_exists():
    """Check if the tax deed table exists"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to query the table
        response = supabase.table('tax_deed_properties_with_contacts').select('id').limit(1).execute()
        print("SUCCESS: Table 'tax_deed_properties_with_contacts' already exists")
        
        # Get count of records
        count_response = supabase.table('tax_deed_properties_with_contacts').select('*', count='exact').execute()
        print(f"Current records in table: {count_response.count if hasattr(count_response, 'count') else len(count_response.data)}")
        
        return True
        
    except Exception as e:
        if 'relation' in str(e).lower() and 'does not exist' in str(e).lower():
            print("ERROR: Table 'tax_deed_properties_with_contacts' does not exist")
            print("Please run the SQL script in Supabase SQL Editor:")
            print("   1. Go to https://supabase.com/dashboard/project/pmispwtdngkcmsrsjwbp/sql")
            print("   2. Copy the contents of 'create_tax_deed_table.sql'")
            print("   3. Paste and run in the SQL Editor")
            return False
        else:
            print(f"Error checking table: {e}")
            return False

def test_table_operations():
    """Test basic table operations"""
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Test insert
        test_data = {
            'composite_key': 'TEST-001_123456789',
            'tax_deed_number': 'TEST-001',
            'parcel_number': '123456789',
            'situs_address': '123 Test Street, Fort Lauderdale, FL 33301',
            'opening_bid': 50000,
            'status': 'Test',
            'applicant': 'Test Applicant'
        }
        
        # Try to insert
        response = supabase.table('tax_deed_properties_with_contacts').upsert(test_data).execute()
        print("Successfully inserted test record")
        
        # Delete test record
        supabase.table('tax_deed_properties_with_contacts').delete().eq('composite_key', 'TEST-001_123456789').execute()
        print("Successfully deleted test record")
        
        print("Table is ready for use!")
        return True
        
    except Exception as e:
        print(f"Error testing table operations: {e}")
        return False

if __name__ == "__main__":
    print("Checking Supabase table setup...")
    print(f"Supabase URL: {SUPABASE_URL}")
    
    if check_table_exists():
        test_table_operations()
    else:
        print("\nPlease create the table first using the SQL script in Supabase dashboard")
        print("Then run this script again to verify")