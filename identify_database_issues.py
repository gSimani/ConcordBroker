"""
Identify specific database issues that need correction in Supabase
"""
from supabase import create_client, Client
from datetime import datetime
import json

# Supabase configuration
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

def identify_issues():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\nDATABASE ISSUES IDENTIFICATION")
    print("="*60)
    
    # Get all records
    response = supabase.table('tax_deed_bidding_items').select('*').execute()
    
    if not response.data:
        print("No data found in database")
        return
    
    issues = {
        'unknown_parcels': [],
        'no_address': [],
        'duplicate_td_numbers': {},
        'zero_opening_bid': [],
        'invalid_td_format': [],
        'missing_critical_data': []
    }
    
    td_number_counts = {}
    
    for prop in response.data:
        prop_id = prop['id']
        td_num = prop['tax_deed_number']
        
        # Check for UNKNOWN parcel IDs
        if prop['parcel_id'] and prop['parcel_id'].startswith('UNKNOWN'):
            issues['unknown_parcels'].append({
                'id': prop_id,
                'tax_deed_number': td_num,
                'parcel_id': prop['parcel_id'],
                'status': prop['item_status']
            })
        
        # Check for missing addresses
        if not prop['legal_situs_address'] or prop['legal_situs_address'] == 'Address not available':
            issues['no_address'].append({
                'id': prop_id,
                'tax_deed_number': td_num,
                'status': prop['item_status']
            })
        
        # Check for zero opening bids on Active properties
        if prop['item_status'] in ['Active', 'Upcoming'] and (not prop['opening_bid'] or prop['opening_bid'] == 0):
            issues['zero_opening_bid'].append({
                'id': prop_id,
                'tax_deed_number': td_num,
                'status': prop['item_status']
            })
        
        # Check for invalid TD number format
        if not td_num or not td_num.startswith('TD-'):
            issues['invalid_td_format'].append({
                'id': prop_id,
                'tax_deed_number': td_num,
                'status': prop['item_status']
            })
        
        # Count TD numbers for duplicates
        if td_num:
            if td_num not in td_number_counts:
                td_number_counts[td_num] = []
            td_number_counts[td_num].append(prop_id)
        
        # Check for missing critical data on Active properties
        if prop['item_status'] in ['Active', 'Upcoming']:
            missing_fields = []
            if not prop['parcel_id'] or prop['parcel_id'].startswith('UNKNOWN'):
                missing_fields.append('parcel_id')
            if not prop['legal_situs_address'] or prop['legal_situs_address'] == 'Address not available':
                missing_fields.append('address')
            if not prop['opening_bid'] or prop['opening_bid'] == 0:
                missing_fields.append('opening_bid')
            
            if missing_fields:
                issues['missing_critical_data'].append({
                    'id': prop_id,
                    'tax_deed_number': td_num,
                    'missing_fields': missing_fields,
                    'status': prop['item_status']
                })
    
    # Find duplicates
    for td_num, ids in td_number_counts.items():
        if len(ids) > 1:
            issues['duplicate_td_numbers'][td_num] = ids
    
    # Print summary
    print(f"\nISSUES FOUND:")
    print(f"1. Properties with UNKNOWN parcel IDs: {len(issues['unknown_parcels'])}")
    print(f"2. Properties with no/invalid address: {len(issues['no_address'])}")
    print(f"3. Active properties with zero opening bid: {len(issues['zero_opening_bid'])}")
    print(f"4. Invalid tax deed number format: {len(issues['invalid_td_format'])}")
    print(f"5. Duplicate tax deed numbers: {len(issues['duplicate_td_numbers'])}")
    print(f"6. Active properties missing critical data: {len(issues['missing_critical_data'])}")
    
    # Show samples
    if issues['unknown_parcels']:
        print(f"\nSample UNKNOWN parcels (first 5):")
        for prop in issues['unknown_parcels'][:5]:
            print(f"  ID {prop['id']}: {prop['tax_deed_number']} - {prop['parcel_id']} ({prop['status']})")
    
    if issues['no_address']:
        print(f"\nSample missing addresses (first 5):")
        for prop in issues['no_address'][:5]:
            print(f"  ID {prop['id']}: {prop['tax_deed_number']} ({prop['status']})")
    
    if issues['duplicate_td_numbers']:
        print(f"\nDuplicate tax deed numbers:")
        for td_num, ids in list(issues['duplicate_td_numbers'].items())[:5]:
            print(f"  {td_num}: IDs {ids}")
    
    # Generate SQL correction statements
    print("\n" + "="*60)
    print("SUGGESTED SQL CORRECTIONS FOR SUPABASE:")
    print("="*60)
    
    # 1. Delete records with UNKNOWN parcels and no address
    if issues['unknown_parcels']:
        unknown_ids = [p['id'] for p in issues['unknown_parcels'] if p['id'] in [x['id'] for x in issues['no_address']]]
        if unknown_ids:
            print(f"\n-- Delete {len(unknown_ids)} records with UNKNOWN parcels AND no address:")
            print(f"DELETE FROM tax_deed_bidding_items")
            print(f"WHERE id IN ({', '.join(map(str, unknown_ids[:10]))});")
    
    # 2. Update AUTO generated TD numbers
    auto_td_ids = [p['id'] for p in issues['invalid_td_format'] if p['tax_deed_number'] and 'AUTO' in p['tax_deed_number']]
    if auto_td_ids:
        print(f"\n-- Fix {len(auto_td_ids)} AUTO-generated tax deed numbers:")
        print(f"UPDATE tax_deed_bidding_items")
        print(f"SET tax_deed_number = 'TD-' || (50000 + id)")
        print(f"WHERE id IN ({', '.join(map(str, auto_td_ids[:10]))});")
    
    # 3. Remove duplicates (keep the one with most data)
    if issues['duplicate_td_numbers']:
        print(f"\n-- Remove duplicate tax deed numbers (keeping best record):")
        for td_num, ids in list(issues['duplicate_td_numbers'].items())[:3]:
            print(f"-- For {td_num}, keep ID {ids[0]} and delete {ids[1:]}")
            if len(ids) > 1:
                print(f"DELETE FROM tax_deed_bidding_items WHERE id IN ({', '.join(map(str, ids[1:]))});")
    
    # Save detailed report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_records': len(response.data),
        'issues': issues,
        'correction_priority': [
            'Delete records with UNKNOWN parcels and no address',
            'Fix AUTO-generated tax deed numbers',
            'Remove duplicate tax deed numbers',
            'Update zero opening bids for Active properties'
        ]
    }
    
    report_file = f'database_issues_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n[REPORT] Detailed report saved to: {report_file}")
    
    return issues

if __name__ == "__main__":
    identify_issues()