"""
Targeted cleanup of UNKNOWN parcel records in database
"""
from supabase import create_client, Client
from datetime import datetime

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def cleanup_unknown_records():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\nTARGETED CLEANUP: REMOVING UNKNOWN RECORDS")
    print("="*60)
    
    # Get all UNKNOWN records
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    unknown_records = []
    for record in response.data:
        # Check if it's an UNKNOWN record
        if (record.get('parcel_id', '').startswith('UNKNOWN') or 
            record.get('parcel_id', '').startswith('PARCEL-')):
            # Also check if it has no real address
            if (not record.get('legal_situs_address') or 
                record['legal_situs_address'] == 'Address not available' or
                record['legal_situs_address'] == 'Address pending' or
                'ET on the Thursday' in record.get('legal_situs_address', '')):
                unknown_records.append(record)
    
    print(f"Found {len(unknown_records)} UNKNOWN/placeholder records to remove")
    
    if unknown_records:
        print("\nSample records to delete:")
        for rec in unknown_records[:5]:
            print(f"  ID {rec['id']}: {rec['tax_deed_number']} - Parcel: {rec['parcel_id'][:20]}... - Address: {rec.get('legal_situs_address', 'None')[:30]}...")
        
        # Delete them
        ids_to_delete = [r['id'] for r in unknown_records]
        
        print(f"\nDeleting {len(ids_to_delete)} records...")
        
        # Delete in batches
        batch_size = 10
        deleted = 0
        
        for i in range(0, len(ids_to_delete), batch_size):
            batch = ids_to_delete[i:i+batch_size]
            try:
                response = supabase.table('tax_deed_bidding_items').delete().in_('id', batch).execute()
                deleted += len(batch)
                print(f"  Deleted batch {i//batch_size + 1}: {len(batch)} records")
            except Exception as e:
                print(f"  Error deleting batch: {str(e)}")
        
        print(f"\n[SUCCESS] Deleted {deleted} placeholder records")
    
    # Verify what's left
    print("\n[VERIFICATION]")
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    total_remaining = len(response.data)
    
    # Count good vs bad records
    good_records = 0
    still_unknown = 0
    
    for record in response.data:
        if (record.get('parcel_id') and 
            not record['parcel_id'].startswith('UNKNOWN') and
            not record['parcel_id'].startswith('PARCEL-') and
            record.get('legal_situs_address') and
            record['legal_situs_address'] != 'Address not available'):
            good_records += 1
        else:
            still_unknown += 1
    
    print(f"Total records remaining: {total_remaining}")
    print(f"Good records with real data: {good_records}")
    print(f"Still have issues: {still_unknown}")
    
    # Show sample of good records
    print("\nSample of GOOD records remaining:")
    good_samples = [r for r in response.data if r.get('parcel_id') and not r['parcel_id'].startswith('UNKNOWN')][:5]
    for rec in good_samples:
        print(f"  {rec['tax_deed_number']}: {rec.get('legal_situs_address', 'N/A')[:50]}... (${rec.get('opening_bid', 0):,.2f})")
    
    print("\n" + "="*60)
    print("CLEANUP COMPLETE")
    print("="*60)

if __name__ == "__main__":
    cleanup_unknown_records()