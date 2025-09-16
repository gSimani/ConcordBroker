"""
Quick property data fetcher for testing
"""

import json
from supabase import create_client

# Supabase connection
url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
supabase = create_client(url, key)

# Get property data
response = supabase.table('florida_parcels').select('*').eq('parcel_id', 'C00002861551').execute()

if response.data and len(response.data) > 0:
    prop = response.data[0]

    # Format the complete property data
    property_data = {
        # Essential IDs
        'id': prop.get('parcel_id'),
        'parcel_id': prop.get('parcel_id'),

        # Property address information
        'phy_addr1': prop.get('phy_addr1', ''),
        'phy_addr2': prop.get('phy_addr2', ''),
        'phy_city': prop.get('phy_city', ''),
        'phy_state': prop.get('phy_state', 'FL'),
        'phy_zipcd': prop.get('phy_zipcd', ''),

        # Owner information
        'owner_name': prop.get('owner_name', ''),
        'owner_addr1': prop.get('owner_addr1', ''),
        'owner_addr2': prop.get('owner_addr2', ''),
        'owner_city': prop.get('owner_city', ''),
        'owner_state': prop.get('owner_state', ''),
        'owner_zip': prop.get('owner_zip', ''),

        # Property characteristics
        'property_use': prop.get('property_use', ''),
        'dor_uc': prop.get('dor_uc', prop.get('property_use', '')),
        'yr_blt': prop.get('yr_blt'),
        'act_yr_blt': prop.get('act_yr_blt', prop.get('yr_blt')),
        'bedroom_cnt': prop.get('bedroom_cnt'),
        'bathroom_cnt': prop.get('bathroom_cnt'),
        'tot_lvg_area': prop.get('tot_lvg_area'),
        'lnd_sqfoot': prop.get('lnd_sqfoot'),
        'no_res_unts': prop.get('no_res_unts', 1),

        # Values
        'jv': prop.get('jv') or prop.get('just_value'),
        'just_value': prop.get('just_value') or prop.get('jv'),
        'av_sd': prop.get('av_sd') or prop.get('assessed_value'),
        'assessed_value': prop.get('assessed_value') or prop.get('av_sd'),
        'tv_sd': prop.get('tv_sd') or prop.get('taxable_value'),
        'taxable_value': prop.get('taxable_value') or prop.get('tv_sd'),
        'lnd_val': prop.get('lnd_val') or prop.get('land_value'),
        'tax_amount': prop.get('tax_amount'),

        # Sales information
        'sale_prc1': prop.get('sale_prc1'),
        'sale_yr1': prop.get('sale_yr1'),
        'sale_mo1': prop.get('sale_mo1'),
        'qual_cd1': prop.get('qual_cd1'),

        # Additional info
        'subdivision': prop.get('subdivision'),
        'exempt_val': prop.get('exempt_val'),
        'county': prop.get('county'),
        'year': prop.get('year'),
        'nbhd_cd': prop.get('nbhd_cd'),
        'millage_rate': prop.get('millage_rate')
    }

    print(json.dumps(property_data, indent=2))
else:
    print("Property not found")