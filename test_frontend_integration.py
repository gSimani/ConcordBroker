#!/usr/bin/env python3
"""
Test Frontend Integration
=========================

Tests that the property data can be fetched the same way the frontend would,
simulating the usePropertyData hook behavior.
"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

def test_property_data_integration():
    """Test property data integration like the frontend usePropertyData hook."""
    
    load_dotenv('apps/web/.env')
    supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))
    
    # Test property ID
    parcel_id = '474131031040'
    print(f"Testing property integration for parcel: {parcel_id}")
    print("=" * 60)
    
    # 1. Test florida_parcels query (primary data source)
    print("1. Testing florida_parcels table query...")
    florida_parcels_result = supabase.table('florida_parcels').select('*').eq('parcel_id', parcel_id).limit(1).execute()
    
    if florida_parcels_result.data:
        florida_parcel = florida_parcels_result.data[0]
        print(f"   ✅ Found in florida_parcels")
        print(f"   Address: {florida_parcel.get('phy_addr1')}, {florida_parcel.get('phy_city')}")
        print(f"   Owner: {florida_parcel.get('owner_name')}")
        print(f"   Just Value: ${florida_parcel.get('just_value', 0):,}")
        print(f"   Taxable Value: ${florida_parcel.get('taxable_value', 0):,}")
        print(f"   Year Built: {florida_parcel.get('year_built')}")
        print(f"   Living Area: {florida_parcel.get('total_living_area')} sqft")
        print(f"   Bedrooms: {florida_parcel.get('bedrooms')}")
        print(f"   Bathrooms: {florida_parcel.get('bathrooms')}")
    else:
        print(f"   ❌ Not found in florida_parcels")
        florida_parcel = None
    
    # 2. Test fallback to fl_properties table
    print("\\n2. Testing fl_properties table fallback...")
    try:
        bcpa_result = supabase.table('properties').select('*').eq('parcel_id', parcel_id).limit(1).execute()
        if bcpa_result.data:
            print(f"   ✅ Found in properties table")
        else:
            print(f"   ❌ Not found in properties table")
    except Exception as e:
        print(f"   ❌ Properties table query failed: {e}")
    
    # 3. Test property sales history
    print("\\n3. Testing property_sales_history table...")
    sales_result = supabase.table('property_sales_history').select('*').eq('parcel_id', parcel_id).order('sale_date', desc=True).execute()
    
    if sales_result.data:
        print(f"   ✅ Found {len(sales_result.data)} sales records")
        for i, sale in enumerate(sales_result.data[:3]):
            sale_price = int(float(sale.get('sale_price', 0)))
            print(f"     Sale {i+1}: ${sale_price:,} on {sale['sale_date']} - {sale['deed_type']}")
    else:
        print(f"   ❌ No sales history found")
    
    # 4. Test NAV assessments
    print("\\n4. Testing nav_assessments table...")
    try:
        nav_result = supabase.table('nav_assessments').select('*').eq('parcel_id', parcel_id).execute()
        if nav_result.data:
            total_assessment = sum(float(nav.get('total_assessment', 0)) for nav in nav_result.data)
            print(f"   ✅ Found {len(nav_result.data)} NAV assessment records")
            print(f"   Total Assessment: ${total_assessment:,.2f}")
        else:
            print(f"   ❌ No NAV assessments found")
    except Exception as e:
        print(f"   ❌ NAV assessments query failed: {e}")
    
    # 5. Test Sunbiz data (corporate records)
    print("\\n5. Testing sunbiz_corporate table...")
    if florida_parcel and florida_parcel.get('owner_name'):
        owner_name = florida_parcel['owner_name']
        try:
            # Search for company by name
            sunbiz_result = supabase.table('sunbiz_corporate').select('*').ilike('corporate_name', f'%{owner_name.split()[0]}%').limit(3).execute()
            if sunbiz_result.data:
                print(f"   ✅ Found {len(sunbiz_result.data)} potential Sunbiz matches")
                for company in sunbiz_result.data:
                    print(f"     Company: {company.get('corporate_name')}")
            else:
                print(f"   ❌ No Sunbiz matches found for owner: {owner_name}")
        except Exception as e:
            print(f"   ❌ Sunbiz query failed: {e}")
    
    # 6. Generate frontend-compatible data structure
    print("\\n6. Generating frontend-compatible data structure...")
    
    if florida_parcel:
        # Simulate the data transformation done in usePropertyData.ts
        bcpa_data = {
            'parcel_id': florida_parcel['parcel_id'],
            'property_address_full': f"{florida_parcel.get('phy_addr1', '')}, {florida_parcel.get('phy_city', '')}, FL {florida_parcel.get('phy_zipcd', '')}",
            'property_address_street': florida_parcel.get('phy_addr1'),
            'property_address_city': florida_parcel.get('phy_city'),
            'property_address_zip': florida_parcel.get('phy_zipcd'),
            'owner_name': florida_parcel.get('owner_name'),
            'assessed_value': florida_parcel.get('assessed_value'),
            'taxable_value': florida_parcel.get('taxable_value'),
            'market_value': florida_parcel.get('just_value') or florida_parcel.get('market_value'),
            'just_value': florida_parcel.get('just_value'),
            'land_value': florida_parcel.get('land_value'),
            'building_value': florida_parcel.get('building_value'),
            'year_built': florida_parcel.get('year_built'),
            'living_area': florida_parcel.get('total_living_area'),
            'bedrooms': florida_parcel.get('bedrooms'),
            'bathrooms': florida_parcel.get('bathrooms'),
            'property_use_code': florida_parcel.get('property_use'),
            'sale_price': florida_parcel.get('sale_price'),
            'sale_date': florida_parcel.get('sale_date'),
        }
        
        print("   ✅ Generated bcpaData structure:")
        print(f"   Address: {bcpa_data['property_address_full']}")
        print(f"   Owner: {bcpa_data['owner_name']}")
        print(f"   Market Value: ${bcpa_data['market_value'] or 0:,}")
        print(f"   Year Built: {bcpa_data['year_built']}")
        print(f"   {bcpa_data['bedrooms']}BR / {bcpa_data['bathrooms']}BA")
        print(f"   Living Area: {bcpa_data['living_area']} sqft")
        
    print("\\n" + "=" * 60)
    print("Integration test completed!")
    
    # Summary
    has_basic_data = florida_parcel is not None
    has_sales_data = len(sales_result.data) > 0 if sales_result.data else False
    
    print(f"\\nSummary for property {parcel_id}:")
    print(f"  ✅ Basic property data: {'Yes' if has_basic_data else 'No'}")
    print(f"  {'✅' if has_sales_data else '❌'} Sales history: {'Yes' if has_sales_data else 'No'}")
    print(f"  {'✅' if has_basic_data else '❌'} Ready for frontend: {'Yes' if has_basic_data else 'No'}")
    
    if has_basic_data:
        print(f"\\n🎉 Property {parcel_id} should now display real data instead of N/A values!")
    else:
        print(f"\\n⚠️  Property {parcel_id} still needs data import to show real values.")

if __name__ == "__main__":
    test_property_data_integration()