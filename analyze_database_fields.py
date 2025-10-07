#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

parcel_id = "1078130000370"

print("=" * 80)
print("ANALYZING DATABASE SCHEMA AND DATA MAPPING")
print("=" * 80)

# Get all columns and their values for this property
response = supabase.table('florida_parcels').select("*").eq('parcel_id', parcel_id).execute()

if response.data:
    prop = response.data[0]

    print("\n[ALL DATABASE FIELDS AND VALUES]")
    print("-" * 40)

    # Group fields by category
    assessment_fields = {}
    land_fields = {}
    building_fields = {}
    sales_fields = {}
    owner_fields = {}
    address_fields = {}
    tax_fields = {}
    other_fields = {}

    for field, value in sorted(prop.items()):
        if value is not None and value != "" and value != "None":
            field_lower = field.lower()

            # Categorize fields
            if any(x in field_lower for x in ['value', 'val', 'price', 'amount']):
                assessment_fields[field] = value
            elif any(x in field_lower for x in ['land', 'lot', 'acre', 'sqft', 'sq_ft', 'lnd']):
                land_fields[field] = value
            elif any(x in field_lower for x in ['build', 'bldg', 'living', 'structure']):
                building_fields[field] = value
            elif any(x in field_lower for x in ['sale', 'sold', 'or_book', 'or_page', 'doc']):
                sales_fields[field] = value
            elif any(x in field_lower for x in ['owner', 'own']):
                owner_fields[field] = value
            elif any(x in field_lower for x in ['addr', 'phy_', 'city', 'state', 'zip']):
                address_fields[field] = value
            elif any(x in field_lower for x in ['tax', 'exempt', 'millage']):
                tax_fields[field] = value
            else:
                other_fields[field] = value

    # Print categorized fields
    if assessment_fields:
        print("\n[ASSESSMENT/VALUE FIELDS]")
        for field, value in assessment_fields.items():
            print(f"  {field}: {value}")

    if land_fields:
        print("\n[LAND FIELDS]")
        for field, value in land_fields.items():
            print(f"  {field}: {value}")

    if building_fields:
        print("\n[BUILDING FIELDS]")
        for field, value in building_fields.items():
            print(f"  {field}: {value}")

    if sales_fields:
        print("\n[SALES FIELDS]")
        for field, value in sales_fields.items():
            print(f"  {field}: {value}")

    if owner_fields:
        print("\n[OWNER FIELDS]")
        for field, value in owner_fields.items():
            print(f"  {field}: {value}")

    if address_fields:
        print("\n[ADDRESS FIELDS]")
        for field, value in address_fields.items():
            print(f"  {field}: {value}")

    if tax_fields:
        print("\n[TAX FIELDS]")
        for field, value in tax_fields.items():
            print(f"  {field}: {value}")

    if other_fields:
        print("\n[OTHER FIELDS]")
        for field, value in other_fields.items():
            print(f"  {field}: {value}")

    print("\n" + "=" * 80)
    print("FIELD MAPPING ANALYSIS")
    print("=" * 80)

    print("\n[IDENTIFIED ISSUES]")
    print("1. Assessed Value mismatch:")
    print(f"   - Database 'assessed_value': {prop.get('assessed_value', 'NOT FOUND')}")
    print(f"   - Should be: $27,458 for 2025")
    print(f"   - Possible correct field: {prop.get('assessed_val', 'NOT FOUND')}")

    print("\n2. Sales History:")
    print(f"   - sale_date: {prop.get('sale_date', 'NOT FOUND')}")
    print(f"   - sale_price: {prop.get('sale_price', 'NOT FOUND')}")
    print(f"   - or_book: {prop.get('or_book', 'NOT FOUND')}")
    print(f"   - or_page: {prop.get('or_page', 'NOT FOUND')}")
    print("   - Need to check if sales are in a separate table or different fields")

    print("\n3. Land Use/Zoning:")
    print(f"   - land_use: {prop.get('land_use', 'NOT FOUND')}")
    print(f"   - land_use_desc: {prop.get('land_use_desc', 'NOT FOUND')}")
    print(f"   - zoning: {prop.get('zoning', 'NOT FOUND')}")
    print(f"   - pa_zone: {prop.get('pa_zone', 'NOT FOUND')}")

    # Check for alternative field names
    print("\n[CHECKING ALTERNATIVE FIELD NAMES]")
    alternatives = {
        'sale': ['sale_date1', 'sale_dt', 'last_sale_date', 'sale_yr', 'sale_mo'],
        'price': ['sale_price1', 'sale_amt', 'last_sale_price', 'sale_amount'],
        'book': ['book_page', 'or_bk_pg', 'deed_book'],
        'assessed': ['assd_val', 'assessed_val', 'assess_val', 'av'],
        'zone': ['zone_code', 'muni_zone', 'zoning_code', 'zone_desc']
    }

    for category, field_list in alternatives.items():
        print(f"\n  {category.upper()} alternatives:")
        for field in field_list:
            if field in prop and prop[field]:
                print(f"    ✓ {field}: {prop[field]}")

else:
    print("Property not found in database!")

print("\n" + "=" * 80)