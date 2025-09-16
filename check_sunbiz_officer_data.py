"""
Check existing Sunbiz officer data in database for contact information
"""
import os
import sys
import io
from pathlib import Path
from supabase import create_client

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_sunbiz_data():
    """Check what Sunbiz officer data we have"""
    
    # Supabase connection
    supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
    supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("=" * 60)
    print("SUNBIZ OFFICER DATA ANALYSIS")
    print("=" * 60)
    
    # Check sunbiz_officers table
    try:
        print("\n1. CHECKING SUNBIZ_OFFICERS TABLE:")
        print("-" * 40)
        
        # Get total count
        result = supabase.table('sunbiz_officers').select('*', count='exact').limit(0).execute()
        total_count = result.count
        print(f"Total records: {total_count:,}")
        
        # Get sample records
        sample = supabase.table('sunbiz_officers').select('*').limit(5).execute()
        
        if sample.data:
            # Analyze structure
            first_record = sample.data[0]
            print(f"\nTable structure ({len(first_record)} columns):")
            for key, value in first_record.items():
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"  {key:20}: {value_str}")
            
            # Check for contact information
            print("\n2. CONTACT INFORMATION ANALYSIS:")
            print("-" * 40)
            
            # Check for email patterns
            email_fields = ['email', 'email_address', 'contact_email', 'officer_email']
            phone_fields = ['phone', 'telephone', 'contact_phone', 'officer_phone']
            
            # Check each sample record for emails/phones
            email_count = 0
            phone_count = 0
            
            for record in sample.data:
                record_str = str(record).lower()
                if '@' in record_str:
                    email_count += 1
                if any(char.isdigit() for char in record_str) and ('phone' in record_str or len([x for x in record_str if x.isdigit()]) >= 10):
                    phone_count += 1
            
            print(f"Records with email patterns: {email_count}/{len(sample.data)}")
            print(f"Records with phone patterns: {phone_count}/{len(sample.data)}")
            
            # Search for specific patterns in all data (sample)
            print("\n3. SEARCHING FOR CONTACT PATTERNS:")
            print("-" * 40)
            
            # Search for records with @ symbol
            email_search = supabase.table('sunbiz_officers').select('*').ilike('officer_name', '%@%').limit(10).execute()
            print(f"Records with '@' in officer_name: {len(email_search.data)}")
            
            # Check address fields for emails
            address_email_search = supabase.table('sunbiz_officers').select('*').ilike('address', '%@%').limit(10).execute()
            print(f"Records with '@' in address: {len(address_email_search.data)}")
            
            # Show sample data that might contain emails
            if email_search.data:
                print("\nSample records with email patterns:")
                for record in email_search.data[:2]:
                    print(f"  - {record.get('officer_name', 'N/A')}")
                    print(f"    Address: {record.get('address', 'N/A')}")
            
    except Exception as e:
        print(f"Error accessing sunbiz_officers: {e}")
    
    # Check for other potential officer tables
    print("\n4. CHECKING OTHER TABLES:")
    print("-" * 40)
    
    potential_tables = [
        'sunbiz_directors', 
        'sunbiz_registered_agents',
        'sunbiz_corporate_filings',
        'officers',
        'directors',
        'registered_agents'
    ]
    
    for table_name in potential_tables:
        try:
            result = supabase.table(table_name).select('*', count='exact').limit(1).execute()
            if result.count > 0:
                print(f"  ✅ {table_name:25}: {result.count:,} records")
                
                # Check first record for contact info
                if result.data:
                    record = result.data[0]
                    has_email = '@' in str(record).lower()
                    has_phone = any(str(value).replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit() 
                                  and len(str(value).replace('-', '').replace('(', '').replace(')', '').replace(' ', '')) >= 10 
                                  for value in record.values())
                    
                    contact_info = []
                    if has_email:
                        contact_info.append("emails")
                    if has_phone:
                        contact_info.append("phones")
                    
                    if contact_info:
                        print(f"    📞 Contains: {', '.join(contact_info)}")
                    
        except Exception as e:
            pass  # Table doesn't exist
    
    print("\n5. RECOMMENDATIONS:")
    print("-" * 40)
    print("Based on analysis:")
    print("1. Focus on downloading 'off' (officers) directory from FTP")
    print("2. Parse officer files for direct contact information")
    print("3. Cross-reference with existing property owner data")
    print("4. Consider using alternative APIs (OpenCorporates, etc.)")
    
    return True

if __name__ == "__main__":
    check_sunbiz_data()