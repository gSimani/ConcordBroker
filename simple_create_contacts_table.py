"""
Simple table creation by inserting a sample record (Supabase will auto-create)
"""
import os
import sys
import io
from pathlib import Path
from supabase import create_client
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_table_simple():
    """Create table by inserting sample data"""
    
    # Supabase connection
    supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("=" * 60)
    print("CREATING SUNBIZ OFFICER CONTACTS TABLE")
    print("=" * 60)
    
    # Create sample record to establish table structure
    sample_record = {
        'entity_name': 'SAMPLE LLC',
        'officer_name': 'JOHN DOE',
        'officer_email': 'john.doe@example.com',
        'officer_phone': '305-555-0001',
        'additional_emails': 'alternate@example.com',
        'additional_phones': '305-555-0002',
        'source_file': 'SAMPLE_OFFICERS.txt',
        'source_line': 1,
        'context': 'Sample context for table creation',
        'extracted_date': datetime.now().isoformat(),
        'import_date': datetime.now().isoformat()
    }
    
    try:
        print("🔍 Checking if table exists...")
        
        # Try to query the table first
        try:
            result = supabase.table('sunbiz_officer_contacts').select('*').limit(1).execute()
            print("✅ Table already exists!")
            print(f"Current records: {len(result.data)}")
            return True
            
        except Exception as e:
            print("❌ Table doesn't exist, creating...")
            
            # Insert sample record (this will create the table)
            print("🚀 Inserting sample record to create table...")
            result = supabase.table('sunbiz_officer_contacts').insert(sample_record).execute()
            
            if result.data:
                print("✅ Table created successfully!")
                print(f"Sample record ID: {result.data[0]['id']}")
                
                # Verify table creation
                verify_result = supabase.table('sunbiz_officer_contacts').select('*').execute()
                print(f"✅ Verification: {len(verify_result.data)} records in table")
                
                return True
            else:
                print("❌ Failed to create table")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = create_table_simple()
    if success:
        print("\n🎉 Ready to proceed with FTP download!")
    else:
        print("\n💥 Table creation failed")