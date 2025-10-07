#!/usr/bin/env python3
import os
import json
import requests
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL", "")
key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")
supabase: Client = create_client(url, key)

# Property to investigate
parcel_id = "504231242730"

print("=" * 100)
print(f"COMPREHENSIVE PROPERTY REPORT FOR FOLIO: {parcel_id}")
print("=" * 100)
print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 100)

# 1. DATABASE QUERY - Get ALL fields
print("\n[1] DIRECT DATABASE QUERY (florida_parcels table)")
print("-" * 50)

response = supabase.table('florida_parcels').select("*").eq('parcel_id', parcel_id).execute()

if response.data:
    prop = response.data[0]

    # Group and display all fields
    print("\n[PROPERTY LOCATION]")
    print(f"  Physical Address 1: {prop.get('phy_addr1', 'N/A')}")
    print(f"  Physical Address 2: {prop.get('phy_addr2', 'N/A')}")
    print(f"  City: {prop.get('phy_city', 'N/A')}")
    print(f"  State: {prop.get('phy_state', 'N/A')}")
    print(f"  Zip: {prop.get('phy_zipcd', 'N/A')}")
    print(f"  County: {prop.get('county', 'N/A')}")
    print(f"  Subdivision: {prop.get('subdivision', 'N/A')}")

    print("\n[OWNER INFORMATION]")
    print(f"  Owner Name: {prop.get('owner_name', 'N/A')}")
    print(f"  Owner Address 1: {prop.get('owner_addr1', 'N/A')}")
    print(f"  Owner Address 2: {prop.get('owner_addr2', 'N/A')}")
    print(f"  Owner City: {prop.get('owner_city', 'N/A')}")
    print(f"  Owner State: {prop.get('owner_state', 'N/A')}")
    print(f"  Owner Zip: {prop.get('owner_zipcd', 'N/A')}")

    print("\n[PROPERTY VALUES]")
    print(f"  Just Value (Market): ${prop.get('just_value', 0):,.2f}")
    print(f"  Assessed Value: ${prop.get('assessed_value', 0):,.2f}")
    print(f"  Taxable Value: ${prop.get('taxable_value', 0):,.2f}")
    print(f"  Land Value: ${prop.get('land_value', 0):,.2f}")
    print(f"  Building Value: ${prop.get('building_value', 0):,.2f}")
    print(f"  Extra Features Value: ${prop.get('xf_value', 0):,.2f}")

    print("\n[PROPERTY CHARACTERISTICS]")
    print(f"  Year Built: {prop.get('year_built', 'N/A')}")
    print(f"  Effective Year Built: {prop.get('eff_year_built', 'N/A')}")
    print(f"  Total Living Area: {prop.get('total_living_area', 0):,} sq ft")
    print(f"  Adjusted Area: {prop.get('adjusted_area', 0):,} sq ft")
    print(f"  Land Square Feet: {prop.get('land_sqft', 0):,} sq ft")
    print(f"  Bedrooms: {prop.get('bedrooms', 'N/A')}")
    print(f"  Bathrooms: {prop.get('bathrooms', 'N/A')}")
    print(f"  Half Bathrooms: {prop.get('half_bathrooms', 'N/A')}")
    print(f"  Stories/Floors: {prop.get('stories', 'N/A')}")
    print(f"  Units: {prop.get('units', 'N/A')}")

    print("\n[LAND USE & ZONING]")
    print(f"  Property Use Code: {prop.get('property_use', 'N/A')}")
    print(f"  Land Use Code: {prop.get('land_use_code', 'N/A')}")
    print(f"  Land Use Description: {prop.get('land_use_desc', 'N/A')}")
    print(f"  Zoning: {prop.get('zoning', 'N/A')}")
    print(f"  PA Zone: {prop.get('pa_zone', 'N/A')}")
    print(f"  DOR Use Code: {prop.get('dor_uc', 'N/A')}")

    print("\n[SALES INFORMATION]")
    print(f"  Sale Date: {prop.get('sale_date', 'N/A')}")
    print(f"  Sale Price: ${prop.get('sale_price', 0):,.2f}" if prop.get('sale_price') else "  Sale Price: N/A")
    print(f"  Sale Qualification: {prop.get('sale_qualification', 'N/A')}")
    print(f"  OR Book: {prop.get('or_book', 'N/A')}")
    print(f"  OR Page: {prop.get('or_page', 'N/A')}")
    print(f"  Document Number: {prop.get('doc_no', 'N/A')}")
    print(f"  Grantor: {prop.get('grantor', 'N/A')}")
    print(f"  Grantee: {prop.get('grantee', 'N/A')}")

    print("\n[TAX INFORMATION]")
    print(f"  Tax District: {prop.get('tax_district', 'N/A')}")
    print(f"  Millage Rate: {prop.get('millage_rate', 'N/A')}")
    print(f"  Homestead Exemption: {prop.get('homestead_exemption', False)}")
    print(f"  Exempt Value: ${prop.get('exempt_val', 0):,.2f}")

    print("\n[METADATA]")
    print(f"  Data Source: {prop.get('data_source', 'N/A')}")
    print(f"  Import Date: {prop.get('import_date', 'N/A')}")
    print(f"  Update Date: {prop.get('update_date', 'N/A')}")
    print(f"  Year: {prop.get('year', 'N/A')}")

    # Show all other fields not categorized
    categorized_fields = {
        'phy_addr1', 'phy_addr2', 'phy_city', 'phy_state', 'phy_zipcd', 'county', 'subdivision',
        'owner_name', 'owner_addr1', 'owner_addr2', 'owner_city', 'owner_state', 'owner_zipcd',
        'just_value', 'assessed_value', 'taxable_value', 'land_value', 'building_value', 'xf_value',
        'year_built', 'eff_year_built', 'total_living_area', 'adjusted_area', 'land_sqft',
        'bedrooms', 'bathrooms', 'half_bathrooms', 'stories', 'units',
        'property_use', 'land_use_code', 'land_use_desc', 'zoning', 'pa_zone', 'dor_uc',
        'sale_date', 'sale_price', 'sale_qualification', 'or_book', 'or_page', 'doc_no', 'grantor', 'grantee',
        'tax_district', 'millage_rate', 'homestead_exemption', 'exempt_val',
        'data_source', 'import_date', 'update_date', 'year', 'id', 'parcel_id', 'is_redacted'
    }

    other_fields = {k: v for k, v in prop.items() if k not in categorized_fields and v is not None and v != "" and v != "None"}
    if other_fields:
        print("\n[ADDITIONAL FIELDS]")
        for field, value in other_fields.items():
            print(f"  {field}: {value}")

else:
    print("[X] Property not found in database!")

# 2. API QUERY
print("\n" + "=" * 100)
print("[2] API ENDPOINT QUERY (http://localhost:8000)")
print("-" * 50)

try:
    api_response = requests.get(f"http://localhost:8000/api/properties/{parcel_id}")
    if api_response.status_code == 200:
        api_data = api_response.json()

        if api_data.get('success'):
            prop_data = api_data.get('property', {})
            bcpa = prop_data.get('bcpaData', {})

            print("\n[OK] API Response Success")
            print("\n[API CALCULATED METRICS]")
            print(f"  Investment Score: {prop_data.get('investmentScore', 'N/A')}")
            print(f"  Is in CDD: {prop_data.get('isInCDD', False)}")
            print(f"  Total NAV Assessment: ${prop_data.get('totalNavAssessment', 0):,.2f}")

            if prop_data.get('opportunities'):
                print(f"\n[OPPORTUNITIES]")
                for opp in prop_data.get('opportunities', []):
                    print(f"  - {opp}")

            if prop_data.get('riskFactors'):
                print(f"\n[RISK FACTORS]")
                for risk in prop_data.get('riskFactors', []):
                    print(f"  - {risk}")

            print(f"\n[DATA QUALITY]")
            dq = prop_data.get('dataQuality', {})
            print(f"  BCPA Data: {'YES' if dq.get('bcpa') else 'NO'}")
            print(f"  SDF Data: {'YES' if dq.get('sdf') else 'NO'}")
            print(f"  NAV Data: {'YES' if dq.get('nav') else 'NO'}")
            print(f"  TPP Data: {'YES' if dq.get('tpp') else 'NO'}")
            print(f"  Sunbiz Data: {'YES' if dq.get('sunbiz') else 'NO'}")

            # Check for sales history
            sales = prop_data.get('sales_history', [])
            if sales:
                print(f"\n[SALES HISTORY] ({len(sales)} transactions):")
                for sale in sales[:5]:  # Show first 5
                    print(f"  {sale.get('sale_date', 'N/A')}: ${sale.get('sale_price', 0):,.2f}")

        else:
            print("[X] API returned unsuccessful response")
    else:
        print(f"[X] API Error: Status {api_response.status_code}")
except Exception as e:
    print(f"[X] Failed to connect to API: {str(e)}")

# 3. CHECK FOR RELATED DATA
print("\n" + "=" * 100)
print("[3] RELATED DATA CHECK")
print("-" * 50)

# Check for tax certificates
try:
    tax_response = supabase.table('tax_certificates').select("*").eq('parcel_id', parcel_id).limit(5).execute()
    if tax_response.data:
        print(f"\n[TAX CERTIFICATES]: Found {len(tax_response.data)} certificate(s)")
        for cert in tax_response.data:
            print(f"  Year: {cert.get('tax_year')} - Amount: ${cert.get('total_amount', 0):,.2f}")
except:
    print("  Tax Certificates: Table not accessible or doesn't exist")

# Check for permits
try:
    permit_response = supabase.table('permits').select("*").eq('folio', parcel_id).limit(5).execute()
    if permit_response.data:
        print(f"\n[PERMITS]: Found {len(permit_response.data)} permit(s)")
except:
    print("  Permits: Table not accessible or doesn't exist")

print("\n" + "=" * 100)
print("END OF REPORT")
print("=" * 100)