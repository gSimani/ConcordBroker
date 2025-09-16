"""
Fix remaining invalid tax deed numbers in database
"""
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def fix_td_numbers():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\nFIXING REMAINING TAX DEED NUMBERS")
    print("="*60)
    
    # Get all records
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    all_records = response.data if response.data else []
    
    # Find records with invalid TD numbers
    invalid_records = []
    for record in all_records:
        td_num = record.get('tax_deed_number', '')
        # Check if it's invalid (doesn't start with TD- or has AUTO)
        if not td_num or not td_num.startswith('TD-') or 'AUTO' in td_num:
            invalid_records.append(record)
        # Also check if it's just a number without TD- prefix
        elif td_num.isdigit():
            invalid_records.append(record)
    
    print(f"Found {len(invalid_records)} records with invalid TD numbers")
    
    if invalid_records:
        print("\nSample invalid TD numbers:")
        for rec in invalid_records[:5]:
            print(f"  ID {rec['id']}: '{rec.get('tax_deed_number', 'NONE')}'")
        
        print("\nFixing TD numbers...")
        fixed = 0
        
        for record in invalid_records:
            td_num = record.get('tax_deed_number', '')
            new_td = None
            
            # If it's just a number, add TD- prefix
            if td_num and td_num.isdigit():
                new_td = f"TD-{td_num}"
            # If it's empty or has AUTO, generate new one
            elif not td_num or 'AUTO' in td_num or not td_num.startswith('TD-'):
                new_td = f"TD-{70000 + record['id']}"
            
            if new_td:
                try:
                    response = supabase.table('tax_deed_bidding_items').update({
                        'tax_deed_number': new_td
                    }).eq('id', record['id']).execute()
                    fixed += 1
                    print(f"  Fixed ID {record['id']}: '{td_num}' -> '{new_td}'")
                except Exception as e:
                    print(f"  Error fixing ID {record['id']}: {str(e)[:50]}")
        
        print(f"\n[SUCCESS] Fixed {fixed} TD numbers")
    
    # Verify the fix
    print("\n[VERIFICATION]")
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    still_invalid = 0
    for record in response.data:
        td_num = record.get('tax_deed_number', '')
        if not td_num or not td_num.startswith('TD-') or 'AUTO' in td_num:
            still_invalid += 1
    
    print(f"Records with invalid TD numbers: {still_invalid}")
    
    if still_invalid == 0:
        print("[SUCCESS] All TD numbers are now valid!")
        
        # Show sample of fixed records
        print("\nSample of fixed TD numbers:")
        for rec in response.data[:5]:
            print(f"  {rec['tax_deed_number']}: {rec.get('legal_situs_address', 'N/A')[:40]}...")
    else:
        print("[WARNING] Some TD numbers still need fixing")

if __name__ == "__main__":
    fix_td_numbers()