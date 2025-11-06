"""
Verify final database state and propose constraints to prevent future issues
"""
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from datetime import datetime
import json

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'REDACTED'

def verify_database_state():
    try:
        load_dotenv('.env.mcp')
        env_url = os.getenv('SUPABASE_URL')
        env_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY')
        url = env_url or SUPABASE_URL
        key = env_key or SUPABASE_KEY
    except Exception:
        url = SUPABASE_URL
        key = SUPABASE_KEY
    supabase = create_client(url, key)
    
    print("\nFINAL DATABASE STATE VERIFICATION")
    print("="*60)
    
    verification_results = {
        'timestamp': datetime.now().isoformat(),
        'checks': {},
        'issues_found': [],
        'all_clear': True
    }
    
    # Get all records
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    all_records = response.data if response.data else []
    
    print(f"Total records in database: {len(all_records)}")
    verification_results['checks']['total_records'] = len(all_records)
    
    # CHECK 1: Status distribution
    print("\n[CHECK 1] Status Distribution:")
    status_counts = {}
    for record in all_records:
        status = record.get('item_status', 'Unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    verification_results['checks']['status_distribution'] = status_counts
    
    # CHECK 2: UNKNOWN parcels or placeholder addresses
    print("\n[CHECK 2] Data Quality Checks:")
    
    unknown_parcels = [r for r in all_records if r.get('parcel_id', '').startswith('UNKNOWN')]
    placeholder_addresses = [r for r in all_records if r.get('legal_situs_address') in ['Address not available', 'Address pending', None, '']]
    
    print(f"  UNKNOWN parcels: {len(unknown_parcels)}")
    print(f"  Placeholder addresses: {len(placeholder_addresses)}")
    
    if unknown_parcels:
        verification_results['issues_found'].append(f"{len(unknown_parcels)} UNKNOWN parcels remain")
        verification_results['all_clear'] = False
        print("  ⚠️ WARNING: Still have UNKNOWN parcels!")
        for r in unknown_parcels[:3]:
            print(f"    - ID {r['id']}: {r['tax_deed_number']}")
    
    if placeholder_addresses:
        verification_results['issues_found'].append(f"{len(placeholder_addresses)} placeholder addresses remain")
        verification_results['all_clear'] = False
        print("  ⚠️ WARNING: Still have placeholder addresses!")
        for r in placeholder_addresses[:3]:
            print(f"    - ID {r['id']}: {r['tax_deed_number']}")
    
    # CHECK 3: Tax deed number format
    print("\n[CHECK 3] Tax Deed Number Format:")
    
    invalid_td_numbers = []
    for record in all_records:
        td_num = record.get('tax_deed_number', '')
        if not td_num or not td_num.startswith('TD-') or 'AUTO' in td_num:
            invalid_td_numbers.append(record)
    
    print(f"  Invalid TD numbers: {len(invalid_td_numbers)}")
    
    if invalid_td_numbers:
        verification_results['issues_found'].append(f"{len(invalid_td_numbers)} invalid TD numbers")
        verification_results['all_clear'] = False
        print("  ⚠️ WARNING: Invalid TD numbers found!")
        for r in invalid_td_numbers[:3]:
            print(f"    - ID {r['id']}: '{r.get('tax_deed_number', 'NONE')}'")
    
    # CHECK 4: Active/Upcoming with zero bids
    print("\n[CHECK 4] Active Properties Validation:")
    
    active_zero_bids = [r for r in all_records 
                        if r.get('item_status') in ['Active', 'Upcoming'] 
                        and (not r.get('opening_bid') or r['opening_bid'] == 0)]
    
    print(f"  Active/Upcoming with zero bid: {len(active_zero_bids)}")
    
    if active_zero_bids:
        verification_results['issues_found'].append(f"{len(active_zero_bids)} active properties with zero bid")
        verification_results['all_clear'] = False
        print("  ⚠️ WARNING: Active properties with no opening bid!")
        for r in active_zero_bids[:3]:
            print(f"    - ID {r['id']}: {r['tax_deed_number']}")
    
    # CHECK 5: Sample of good data
    print("\n[CHECK 5] Sample of Clean Data:")
    good_records = [r for r in all_records 
                   if r.get('parcel_id') and not r['parcel_id'].startswith('UNKNOWN')
                   and r.get('legal_situs_address') and r['legal_situs_address'] not in ['Address not available', 'Address pending']
                   and r.get('opening_bid', 0) > 0]
    
    print(f"  Records with complete data: {len(good_records)}/{len(all_records)} ({len(good_records)*100//max(len(all_records),1)}%)")
    
    if good_records:
        print("\n  Sample good records:")
        for r in good_records[:3]:
            print(f"    {r['tax_deed_number']}: {r['legal_situs_address'][:40]}... (${r['opening_bid']:,.2f})")
    
    # FINAL VERDICT
    print("\n" + "="*60)
    print("VERIFICATION RESULTS:")
    print("="*60)
    
    if verification_results['all_clear']:
        print("✅ DATABASE IS CLEAN - All checks passed!")
        print("\nDatabase contains:")
        print(f"  • {len(all_records)} total properties")
        print(f"  • {len(good_records)} with complete data ({len(good_records)*100//max(len(all_records),1)}%)")
        print(f"  • No UNKNOWN parcels")
        print(f"  • No placeholder addresses")
        print(f"  • All proper TD numbers")
    else:
        print("⚠️ ISSUES DETECTED:")
        for issue in verification_results['issues_found']:
            print(f"  • {issue}")
    
    # PROPOSE CONSTRAINTS
    print("\n" + "="*60)
    print("RECOMMENDED DATABASE CONSTRAINTS:")
    print("="*60)
    print("\nTo prevent future data quality issues, add these constraints:")
    print("\n```sql")
    print("-- 1. Prevent UNKNOWN parcels")
    print("ALTER TABLE tax_deed_bidding_items")
    print("ADD CONSTRAINT check_parcel_format")
    print("CHECK (parcel_id NOT LIKE 'UNKNOWN%' AND parcel_id NOT LIKE 'PARCEL-%');")
    print("")
    print("-- 2. Require real addresses for Active properties")
    print("ALTER TABLE tax_deed_bidding_items")
    print("ADD CONSTRAINT check_active_has_address")
    print("CHECK (")
    print("  (item_status NOT IN ('Active', 'Upcoming')) OR")
    print("  (legal_situs_address IS NOT NULL AND")
    print("   legal_situs_address != 'Address not available' AND")
    print("   legal_situs_address != 'Address pending')")
    print(");")
    print("")
    print("-- 3. Require proper TD number format")
    print("ALTER TABLE tax_deed_bidding_items")
    print("ADD CONSTRAINT check_td_number_format")
    print("CHECK (tax_deed_number LIKE 'TD-%' AND tax_deed_number NOT LIKE '%AUTO%');")
    print("")
    print("-- 4. Require opening bid for Active properties")
    print("ALTER TABLE tax_deed_bidding_items")
    print("ADD CONSTRAINT check_active_has_bid")
    print("CHECK (")
    print("  (item_status NOT IN ('Active', 'Upcoming')) OR")
    print("  (opening_bid > 0)")
    print(");")
    print("```")
    
    # Save verification report
    report_file = f'final_database_verification_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump(verification_results, f, indent=2, default=str)
    
    print(f"\n[REPORT] Verification saved to: {report_file}")
    
    return verification_results['all_clear']

if __name__ == "__main__":
    is_clean = verify_database_state()
    
    if is_clean:
        print("\n✅ Database is ready for production use!")
    else:
        print("\n⚠️ Additional cleanup may be needed.")

