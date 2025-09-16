"""
Fix the last 2 duplicate TD numbers
"""
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def fix_duplicates():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\nFIXING DUPLICATE TD NUMBERS")
    print("="*60)
    
    # Get records with problematic TD numbers
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    # Find the records that still need fixing
    to_fix = []
    for record in response.data:
        td_num = record.get('tax_deed_number', '')
        # Records with just numbers (no TD- prefix)
        if td_num and td_num.isdigit():
            to_fix.append(record)
    
    print(f"Found {len(to_fix)} records to fix")
    
    if to_fix:
        for record in to_fix:
            # Generate unique TD number using ID + 80000
            new_td = f"TD-{80000 + record['id']}"
            
            try:
                response = supabase.table('tax_deed_bidding_items').update({
                    'tax_deed_number': new_td
                }).eq('id', record['id']).execute()
                print(f"  Fixed ID {record['id']}: '{record['tax_deed_number']}' -> '{new_td}'")
            except Exception as e:
                print(f"  Error: {str(e)[:50]}")
    
    # Final verification
    print("\n[FINAL CHECK]")
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    all_valid = True
    for record in response.data:
        td_num = record.get('tax_deed_number', '')
        if not td_num or not td_num.startswith('TD-'):
            all_valid = False
            print(f"  Still invalid: ID {record['id']} = '{td_num}'")
    
    if all_valid:
        print("[SUCCESS] All TD numbers are now valid!")
        print(f"Total records: {len(response.data)}")
        print("All have proper TD-##### format")
    
    return all_valid

if __name__ == "__main__":
    fix_duplicates()