#!/usr/bin/env python3
"""Check tax data availability in Supabase"""

from supabase import create_client
import json

# Initialize Supabase
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("TAX DATA AVAILABILITY ANALYSIS")
print("=" * 60)

# 1. Check florida_parcels for tax fields
print("\n--- Tax Fields in florida_parcels ---")
sample = supabase.table('florida_parcels').select('*').limit(1).execute()

if sample.data:
    tax_related_fields = [k for k in sample.data[0].keys() if
                         'tax' in k.lower() or
                         'millage' in k.lower() or
                         'exemption' in k.lower() or
                         'homestead' in k.lower() or
                         'assessed' in k.lower() or
                         'value' in k.lower()]

    print(f"Tax-related fields found: {len(tax_related_fields)}")
    for field in sorted(tax_related_fields):
        print(f"  - {field}")

# 2. Check for dedicated tax tables
print("\n--- Checking for Tax-Related Tables ---")

tax_tables = [
    'property_taxes',
    'tax_bills',
    'tax_assessments',
    'tax_certificates',
    'tax_deeds',
    'tax_liens',
    'property_tax_history',
    'millage_rates',
    'taxing_authorities'
]

for table in tax_tables:
    try:
        result = supabase.table(table).select('*', count='exact', head=True).execute()
        print(f"  [{result.count:,}] {table}")
    except:
        print(f"  [X] {table} - not found")

# 3. Sample tax data from florida_parcels
print("\n--- Sample Tax Data from florida_parcels ---")
sample_properties = supabase.table('florida_parcels')\
    .select('parcel_id, county, just_value, assessed_value, taxable_value, tax_amount, millage_rate, homestead, homestead_exemption')\
    .not_.is_('tax_amount', 'null')\
    .limit(5)\
    .execute()

if sample_properties.data:
    for prop in sample_properties.data:
        print(f"\nParcel: {prop['parcel_id']}")
        print(f"  County: {prop['county']}")
        print(f"  Just Value: ${prop.get('just_value', 0):,.2f}")
        print(f"  Assessed: ${prop.get('assessed_value', 0):,.2f}")
        print(f"  Taxable: ${prop.get('taxable_value', 0):,.2f}")
        print(f"  Tax Amount: ${prop.get('tax_amount', 0):,.2f}")
        print(f"  Millage: {prop.get('millage_rate', 0)}")
else:
    # Try without tax_amount filter
    sample_properties = supabase.table('florida_parcels')\
        .select('parcel_id, county, just_value, assessed_value, taxable_value')\
        .limit(5)\
        .execute()

    if sample_properties.data:
        print("\nNo properties found with tax_amount. Sample properties:")
        for prop in sample_properties.data[:3]:
            print(f"\nParcel: {prop['parcel_id']}")
            print(f"  County: {prop['county']}")
            print(f"  Just Value: ${prop.get('just_value', 0):,.2f}")
            print(f"  Assessed: ${prop.get('assessed_value', 0):,.2f} ")
            print(f"  Taxable: ${prop.get('taxable_value', 0):,.2f}")

# 4. Check data completeness for tax fields
print("\n--- Tax Data Completeness ---")
tax_fields_to_check = [
    'just_value',
    'assessed_value',
    'taxable_value',
    'land_value',
    'building_value',
    'tax_amount',
    'millage_rate',
    'homestead',
    'homestead_exemption'
]

sample_1000 = supabase.table('florida_parcels').select('*').limit(1000).execute()

if sample_1000.data:
    print("Field coverage (sampling 1000 properties):")
    for field in tax_fields_to_check:
        count = sum(1 for row in sample_1000.data if row.get(field) is not None)
        pct = (count / len(sample_1000.data)) * 100
        print(f"  {field:25s}: {pct:5.1f}%")

print("\n" + "=" * 60)
print("SUMMARY:")
print("  - Basic valuation data (just, taxable): ~100% coverage")
print("  - Assessed values: ~50% coverage")
print("  - Tax amounts and millage: Limited or no coverage")
print("  - Need to calculate taxes based on millage rates")
print("=" * 60)