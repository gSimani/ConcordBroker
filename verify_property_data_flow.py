#!/usr/bin/env python3
"""
Verify property data flow from database to UI
Tests property 474131031040 which has complete data
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import json

load_dotenv()

def get_connection():
    """Get database connection"""
    db_url = os.getenv('SUPABASE_DIRECT_URL')
    if not db_url:
        raise ValueError("SUPABASE_DIRECT_URL not found in environment")
    return psycopg2.connect(db_url, cursor_factory=RealDictCursor)

def verify_property_data(parcel_id='474131031040'):
    """Verify all data for a specific property"""
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"\n=== Verifying Data for Property {parcel_id} ===\n")
    
    # 1. Check florida_parcels table
    print("1. FLORIDA_PARCELS TABLE:")
    cur.execute("""
        SELECT 
            parcel_id,
            phy_addr1,
            phy_city,
            phy_zipcd,
            owner_name,
            just_value,
            taxable_value,
            sale_price,
            sale_date,
            tot_lvg_area,
            act_yr_blt,
            lnd_sqfoot,
            dor_uc
        FROM florida_parcels 
        WHERE parcel_id = %s
    """, (parcel_id,))
    
    parcel_data = cur.fetchone()
    if parcel_data:
        print(f"   Address: {parcel_data['phy_addr1']}, {parcel_data['phy_city']}, FL {parcel_data['phy_zipcd']}")
        print(f"   Owner: {parcel_data['owner_name']}")
        print(f"   Just Value: ${parcel_data['just_value']:,.0f}" if parcel_data['just_value'] else "   Just Value: N/A")
        print(f"   Taxable Value: ${parcel_data['taxable_value']:,.0f}" if parcel_data['taxable_value'] else "   Taxable Value: N/A")
        print(f"   Sale Price: ${parcel_data['sale_price']:,.0f}" if parcel_data['sale_price'] else "   Sale Price: N/A")
        print(f"   Sale Date: {parcel_data['sale_date']}" if parcel_data['sale_date'] else "   Sale Date: N/A")
        print(f"   Living Area: {parcel_data['tot_lvg_area']:,} sq ft" if parcel_data['tot_lvg_area'] else "   Living Area: N/A")
        print(f"   Year Built: {parcel_data['act_yr_blt']}" if parcel_data['act_yr_blt'] else "   Year Built: N/A")
        print(f"   Lot Size: {parcel_data['lnd_sqfoot']:,} sq ft" if parcel_data['lnd_sqfoot'] else "   Lot Size: N/A")
        print(f"   Property Use Code: {parcel_data['dor_uc']}" if parcel_data['dor_uc'] else "   Property Use Code: N/A")
    else:
        print("   NO DATA FOUND")
    
    # 2. Check property_sales_history table
    print("\n2. PROPERTY_SALES_HISTORY TABLE:")
    cur.execute("""
        SELECT 
            sale_date,
            sale_price,
            sale_type,
            grantor_name,
            grantee_name,
            qualified_sale,
            is_distressed,
            is_bank_sale
        FROM property_sales_history 
        WHERE parcel_id = %s 
        ORDER BY sale_date DESC 
        LIMIT 3
    """, (parcel_id,))
    
    sales = cur.fetchall()
    if sales:
        for i, sale in enumerate(sales, 1):
            print(f"   Sale {i}:")
            print(f"      Date: {sale['sale_date']}")
            print(f"      Price: ${sale['sale_price']:,.0f}" if sale['sale_price'] else "      Price: N/A")
            print(f"      Type: {sale['sale_type']}" if sale['sale_type'] else "      Type: N/A")
            print(f"      Grantor: {sale['grantor_name']}" if sale['grantor_name'] else "      Grantor: N/A")
            print(f"      Grantee: {sale['grantee_name']}" if sale['grantee_name'] else "      Grantee: N/A")
            print(f"      Qualified: {sale['qualified_sale']}")
            print(f"      Distressed: {sale['is_distressed']}")
            print(f"      Bank Sale: {sale['is_bank_sale']}")
    else:
        print("   NO SALES HISTORY FOUND")
    
    # 3. Check nav_assessments table
    print("\n3. NAV_ASSESSMENTS TABLE:")
    cur.execute("""
        SELECT 
            tax_year,
            taxing_authority,
            total_assessment,
            millage_rate
        FROM nav_assessments 
        WHERE parcel_id = %s 
        ORDER BY tax_year DESC
        LIMIT 5
    """, (parcel_id,))
    
    assessments = cur.fetchall()
    if assessments:
        for assessment in assessments:
            print(f"   {assessment['tax_year']} - {assessment['taxing_authority']}: ${assessment['total_assessment']:,.2f} (Rate: {assessment['millage_rate']})")
    else:
        print("   NO TAX ASSESSMENTS FOUND")
    
    # 4. Check sunbiz_corporations table for owner
    if parcel_data and parcel_data['owner_name']:
        print(f"\n4. SUNBIZ_CORPORATIONS TABLE (Owner: {parcel_data['owner_name']}):")
        owner_parts = parcel_data['owner_name'].split()
        if owner_parts:
            search_term = owner_parts[0]
            cur.execute("""
                SELECT 
                    corp_name,
                    status,
                    filing_type,
                    filed_date,
                    principal_addr
                FROM sunbiz_corporations 
                WHERE corp_name ILIKE %s 
                LIMIT 3
            """, (f'%{search_term}%',))
            
            corps = cur.fetchall()
            if corps:
                for corp in corps:
                    print(f"   {corp['corp_name']} ({corp['status']}) - {corp['filing_type']} - Filed: {corp['filed_date']}")
            else:
                print(f"   NO BUSINESS ENTITIES FOUND FOR '{search_term}'")
    
    # 5. Summary of data availability
    print("\n=== DATA AVAILABILITY SUMMARY ===")
    print(f"✓ Florida Parcels: {'YES' if parcel_data else 'NO'}")
    print(f"✓ Sales History: {'YES' if sales else 'NO'}")
    print(f"✓ Tax Assessments: {'YES' if assessments else 'NO'}")
    print(f"✓ Has Sale Price: {'YES' if parcel_data and parcel_data['sale_price'] else 'NO'}")
    print(f"✓ Has Just Value: {'YES' if parcel_data and parcel_data['just_value'] else 'NO'}")
    print(f"✓ Has Property Details: {'YES' if parcel_data and parcel_data['tot_lvg_area'] else 'NO'}")
    
    # 6. Data that should be displayed in UI
    print("\n=== EXPECTED UI DISPLAY ===")
    if parcel_data:
        print("Overview Tab - Most Recent Sale:")
        if parcel_data['sale_price']:
            print(f"   Should show: ${parcel_data['sale_price']:,.0f}")
        elif sales and sales[0]['sale_price']:
            print(f"   Should show: ${sales[0]['sale_price']:,.0f} (from sales history)")
        else:
            print("   Should show: N/A")
        
        print("\nValuation Summary:")
        print(f"   Just Value: ${parcel_data['just_value']:,.0f}" if parcel_data['just_value'] else "   Just Value: N/A")
        print(f"   Taxable Value: ${parcel_data['taxable_value']:,.0f}" if parcel_data['taxable_value'] else "   Taxable Value: N/A")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    # Test with the property that has complete data
    verify_property_data('474131031040')
    
    # Also test with a property that has tax deed
    print("\n" + "="*60)
    print("Testing Tax Deed Property:")
    verify_property_data('064210010010')