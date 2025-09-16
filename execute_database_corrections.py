"""
Execute database corrections in Supabase with safety checks
"""
from supabase import create_client, Client
from datetime import datetime
import json

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def execute_corrections():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\nDATABASE CORRECTION EXECUTION")
    print("="*60)
    
    corrections_log = {
        'timestamp': datetime.now().isoformat(),
        'previews': {},
        'corrections_applied': [],
        'errors': []
    }
    
    # STEP 1: Preview what will be deleted/updated
    print("\n[STEP 1] PREVIEW MODE - Checking what will be affected")
    print("-"*40)
    
    # Preview 1: UNKNOWN parcels with no address
    try:
        response = supabase.table('tax_deed_bidding_items').select('id, tax_deed_number, parcel_id, legal_situs_address, item_status').eq('parcel_id', 'UNKNOWN%').or_('legal_situs_address.eq.Address not available,legal_situs_address.is.null').execute()
        
        unknown_parcels = []
        for row in response.data:
            if row['parcel_id'] and row['parcel_id'].startswith('UNKNOWN'):
                if not row['legal_situs_address'] or row['legal_situs_address'] == 'Address not available':
                    unknown_parcels.append(row)
        
        print(f"1. Records with UNKNOWN parcel + no address: {len(unknown_parcels)}")
        if unknown_parcels:
            print(f"   Sample IDs to delete: {[r['id'] for r in unknown_parcels[:5]]}")
        corrections_log['previews']['unknown_parcels'] = len(unknown_parcels)
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        corrections_log['errors'].append(f"Preview 1: {str(e)}")
    
    # Preview 2: AUTO tax deed numbers
    try:
        response = supabase.table('tax_deed_bidding_items').select('id, tax_deed_number').like('tax_deed_number', 'TD-AUTO-%').execute()
        
        auto_tds = response.data if response.data else []
        print(f"2. Placeholder TD numbers to fix: {len(auto_tds)}")
        if auto_tds:
            print(f"   Sample: {[r['tax_deed_number'] for r in auto_tds[:5]]}")
        corrections_log['previews']['auto_td_numbers'] = len(auto_tds)
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        corrections_log['errors'].append(f"Preview 2: {str(e)}")
    
    # Preview 3: Active with zero bid
    try:
        response = supabase.table('tax_deed_bidding_items').select('id, tax_deed_number, opening_bid, item_status').in_('item_status', ['Active', 'Upcoming']).eq('opening_bid', 0).execute()
        
        zero_bids = []
        for row in response.data:
            if row['parcel_id'] and row['parcel_id'].startswith('UNKNOWN'):
                zero_bids.append(row)
        
        print(f"3. Active/Upcoming with zero bid: {len(zero_bids)}")
        corrections_log['previews']['zero_bids'] = len(zero_bids)
        
    except Exception as e:
        print(f"   Error: {str(e)}")
        corrections_log['errors'].append(f"Preview 3: {str(e)}")
    
    # STEP 2: Execute corrections (with confirmation)
    print("\n[STEP 2] APPLYING CORRECTIONS")
    print("-"*40)
    
    print("\nReady to apply the following corrections:")
    print(f"1. Delete {corrections_log['previews'].get('unknown_parcels', 0)} records with UNKNOWN parcels")
    print(f"2. Fix {corrections_log['previews'].get('auto_td_numbers', 0)} placeholder TD numbers")
    print(f"3. Delete {corrections_log['previews'].get('zero_bids', 0)} test records with zero bids")
    
    user_input = input("\nProceed with corrections? (yes/no): ")
    
    if user_input.lower() != 'yes':
        print("Corrections cancelled by user")
        return
    
    # CORRECTION 1: Delete UNKNOWN parcels with no address
    if unknown_parcels:
        try:
            print("\nDeleting UNKNOWN parcel records...")
            ids_to_delete = [r['id'] for r in unknown_parcels]
            
            # Delete in batches of 10
            for i in range(0, len(ids_to_delete), 10):
                batch = ids_to_delete[i:i+10]
                response = supabase.table('tax_deed_bidding_items').delete().in_('id', batch).execute()
                print(f"  Deleted batch {i//10 + 1}: {len(batch)} records")
            
            corrections_log['corrections_applied'].append(f"Deleted {len(ids_to_delete)} UNKNOWN parcel records")
            print(f"[OK] Deleted {len(ids_to_delete)} records")
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            corrections_log['errors'].append(f"Delete UNKNOWN: {str(e)}")
    
    # CORRECTION 2: Fix AUTO tax deed numbers
    if auto_tds:
        try:
            print("\nFixing placeholder TD numbers...")
            
            for record in auto_tds:
                new_td = f"TD-{60000 + record['id']}"
                response = supabase.table('tax_deed_bidding_items').update({
                    'tax_deed_number': new_td
                }).eq('id', record['id']).execute()
                
            corrections_log['corrections_applied'].append(f"Fixed {len(auto_tds)} TD numbers")
            print(f"[OK] Updated {len(auto_tds)} TD numbers")
            
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            corrections_log['errors'].append(f"Fix TD numbers: {str(e)}")
    
    # CORRECTION 3: Update old Active statuses
    try:
        print("\nUpdating outdated Active statuses...")
        
        # Get all Active records with past close times
        response = supabase.table('tax_deed_bidding_items').select('id, close_time, winning_bid').eq('item_status', 'Active').execute()
        
        now = datetime.now()
        to_sold = []
        to_cancelled = []
        
        for record in response.data:
            if record['close_time']:
                close_time = datetime.fromisoformat(record['close_time'].replace('Z', '+00:00'))
                if close_time < now:
                    if record.get('winning_bid'):
                        to_sold.append(record['id'])
                    else:
                        to_cancelled.append(record['id'])
        
        if to_sold:
            response = supabase.table('tax_deed_bidding_items').update({
                'item_status': 'Sold'
            }).in_('id', to_sold).execute()
            print(f"  Updated {len(to_sold)} to Sold")
            corrections_log['corrections_applied'].append(f"Updated {len(to_sold)} to Sold")
        
        if to_cancelled:
            response = supabase.table('tax_deed_bidding_items').update({
                'item_status': 'Cancelled'
            }).in_('id', to_cancelled).execute()
            print(f"  Updated {len(to_cancelled)} to Cancelled")
            corrections_log['corrections_applied'].append(f"Updated {len(to_cancelled)} to Cancelled")
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        corrections_log['errors'].append(f"Update statuses: {str(e)}")
    
    # STEP 3: Verify results
    print("\n[STEP 3] VERIFICATION")
    print("-"*40)
    
    response = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
    total_after = response.count if hasattr(response, 'count') else len(response.data)
    
    response = supabase.table('tax_deed_bidding_items').select('*').like('parcel_id', 'UNKNOWN%').execute()
    unknown_after = len(response.data) if response.data else 0
    
    print(f"Total records after cleanup: {total_after}")
    print(f"Remaining UNKNOWN parcels: {unknown_after}")
    
    # Save log
    log_file = f'database_corrections_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(log_file, 'w') as f:
        json.dump(corrections_log, f, indent=2, default=str)
    
    print(f"\n[LOG] Corrections log saved to: {log_file}")
    
    print("\n" + "="*60)
    print("DATABASE CORRECTIONS COMPLETE")
    print("="*60)
    
    if corrections_log['corrections_applied']:
        print("\nApplied corrections:")
        for correction in corrections_log['corrections_applied']:
            print(f"  - {correction}")
    
    if corrections_log['errors']:
        print("\nErrors encountered:")
        for error in corrections_log['errors']:
            print(f"  - {error}")

if __name__ == "__main__":
    execute_corrections()