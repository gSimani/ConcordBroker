#!/usr/bin/env python3
"""
Execute Database Report Queries
Analyzes the Florida Property Database in Supabase
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from tabulate import tabulate

# Load environment variables
load_dotenv('apps/web/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Supabase credentials not found in environment")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def get_table_counts():
    """Get row counts for all main tables"""
    tables = [
        'florida_parcels',
        'properties', 
        'property_sales_history',
        'nav_assessments',
        'sunbiz_corporate',
        'sunbiz_fictitious',
        'sunbiz_corporate_events',
        'sunbiz_officers'
    ]
    
    results = []
    for table in tables:
        try:
            # Use count exact for accurate counts
            response = supabase.table(table).select('*', count='exact', head=True).execute()
            count = response.count if hasattr(response, 'count') else 0
            
            if count == 0:
                status = 'EMPTY - Needs Data'
            elif count < 100:
                status = 'Low Data'
            elif count < 1000:
                status = 'Moderate Data'
            else:
                status = 'Good Data'
            
            results.append([table, f"{count:,}", status])
        except Exception as e:
            results.append([table, "ERROR", f"Error: {str(e)[:30]}"])
    
    return results

def get_florida_parcels_stats():
    """Get statistics for florida_parcels table"""
    stats = []
    
    try:
        # Total count
        total = supabase.table('florida_parcels').select('*', count='exact', head=True).execute()
        stats.append(['Total Properties', f"{total.count:,}" if total.count else "0"])
        
        # Sample data to check fields
        sample = supabase.table('florida_parcels').select('*').limit(100).execute()
        
        if sample.data:
            # Count non-null values
            cities = len(set(r.get('phy_city') for r in sample.data if r.get('phy_city')))
            owners = sum(1 for r in sample.data if r.get('owner_name'))
            with_value = sum(1 for r in sample.data if r.get('taxable_value', 0) > 0)
            with_year = sum(1 for r in sample.data if r.get('year_built', 0) > 0)
            
            stats.append(['Unique Cities (sample)', str(cities)])
            stats.append(['Properties with Owner Name', f"{owners}/{len(sample.data)}"])
            stats.append(['Properties with Taxable Value', f"{with_value}/{len(sample.data)}"])
            stats.append(['Properties with Year Built', f"{with_year}/{len(sample.data)}"])
            
            # Average taxable value
            values = [r.get('taxable_value', 0) for r in sample.data if r.get('taxable_value', 0) > 0]
            if values:
                avg_value = sum(values) / len(values)
                stats.append(['Avg Taxable Value (sample)', f"${avg_value:,.0f}"])
    except Exception as e:
        stats.append(['Error', str(e)[:50]])
    
    return stats

def get_city_distribution():
    """Get top cities by property count"""
    try:
        # Get sample of properties grouped by city
        response = supabase.table('florida_parcels')\
            .select('phy_city')\
            .not_.is_('phy_city', 'null')\
            .limit(1000)\
            .execute()
        
        if response.data:
            # Count by city
            city_counts = {}
            for row in response.data:
                city = row.get('phy_city', 'Unknown')
                city_counts[city] = city_counts.get(city, 0) + 1
            
            # Sort and get top 10
            top_cities = sorted(city_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            return [[city, count] for city, count in top_cities]
    except Exception as e:
        return [['Error', str(e)[:50]]]
    
    return [['No data', '']]

def check_sunbiz_data():
    """Specifically check Sunbiz tables for the test property"""
    owner_name = "SIMANI,GUY & SARAH"
    address = "3930 SW 53 CT"
    
    results = []
    
    # Check sunbiz_corporate
    try:
        # Check total count
        corp_count = supabase.table('sunbiz_corporate').select('*', count='exact', head=True).execute()
        results.append(['sunbiz_corporate total', f"{corp_count.count:,}" if corp_count.count else "0"])
        
        # Search for owner
        owner_search = supabase.table('sunbiz_corporate')\
            .select('*')\
            .ilike('entity_name', '%SIMANI%')\
            .execute()
        results.append(['Entities matching SIMANI', len(owner_search.data) if owner_search.data else 0])
        
        # Search for address
        addr_search = supabase.table('sunbiz_corporate')\
            .select('*')\
            .or_(f"prin_addr1.ilike.%3930%,mail_addr1.ilike.%3930%")\
            .execute()
        results.append(['Entities at 3930 address', len(addr_search.data) if addr_search.data else 0])
        
    except Exception as e:
        results.append(['sunbiz_corporate error', str(e)[:40]])
    
    # Check sunbiz_fictitious
    try:
        fict_count = supabase.table('sunbiz_fictitious').select('*', count='exact', head=True).execute()
        results.append(['sunbiz_fictitious total', f"{fict_count.count:,}" if fict_count.count else "0"])
    except Exception as e:
        results.append(['sunbiz_fictitious error', str(e)[:40]])
    
    # Check sunbiz_officers
    try:
        officer_count = supabase.table('sunbiz_officers').select('*', count='exact', head=True).execute()
        results.append(['sunbiz_officers total', f"{officer_count.count:,}" if officer_count.count else "0"])
    except Exception as e:
        results.append(['sunbiz_officers', 'Table may not exist'])
    
    return results

def get_sample_properties():
    """Get sample properties with complete data"""
    try:
        response = supabase.table('florida_parcels')\
            .select('parcel_id, phy_addr1, phy_city, owner_name, taxable_value, year_built')\
            .not_.is_('phy_addr1', 'null')\
            .not_.is_('owner_name', 'null')\
            .gt('taxable_value', 0)\
            .limit(5)\
            .execute()
        
        if response.data:
            results = []
            for prop in response.data:
                results.append([
                    prop.get('parcel_id', 'N/A')[:20],
                    prop.get('phy_addr1', 'N/A')[:30],
                    prop.get('phy_city', 'N/A')[:15],
                    prop.get('owner_name', 'N/A')[:25],
                    f"${prop.get('taxable_value', 0):,.0f}",
                    prop.get('year_built', 'N/A')
                ])
            return results
    except Exception as e:
        return [['Error', str(e)[:50], '', '', '', '']]
    
    return [['No data found', '', '', '', '', '']]

def main():
    """Execute comprehensive database report"""
    
    print_section("FLORIDA PROPERTY DATABASE REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {SUPABASE_URL[:40]}...")
    
    # 1. Table row counts
    print_section("1. TABLE ROW COUNTS AND STATUS")
    table_counts = get_table_counts()
    print(tabulate(table_counts, headers=['Table Name', 'Row Count', 'Status'], tablefmt='grid'))
    
    # 2. Florida parcels statistics
    print_section("2. FLORIDA_PARCELS STATISTICS")
    stats = get_florida_parcels_stats()
    print(tabulate(stats, headers=['Metric', 'Value'], tablefmt='grid'))
    
    # 3. City distribution
    print_section("3. TOP CITIES BY PROPERTY COUNT (Sample)")
    cities = get_city_distribution()
    print(tabulate(cities, headers=['City', 'Count'], tablefmt='grid'))
    
    # 4. Sunbiz data check
    print_section("4. SUNBIZ DATA CHECK (For Test Property)")
    sunbiz = check_sunbiz_data()
    print(tabulate(sunbiz, headers=['Check', 'Result'], tablefmt='grid'))
    
    # 5. Sample properties
    print_section("5. SAMPLE PROPERTIES WITH DATA")
    samples = get_sample_properties()
    print(tabulate(samples, 
                  headers=['Parcel ID', 'Address', 'City', 'Owner', 'Value', 'Year'],
                  tablefmt='grid'))
    
    # 6. Summary and recommendations
    print_section("6. SUMMARY AND RECOMMENDATIONS")
    
    # Analyze results
    empty_tables = []
    low_data_tables = []
    
    for row in table_counts:
        if 'EMPTY' in row[2]:
            empty_tables.append(row[0])
        elif 'Low Data' in row[2]:
            low_data_tables.append(row[0])
    
    print("\nDATABASE HEALTH SUMMARY:")
    print("-" * 40)
    
    if empty_tables:
        print(f"\nCRITICAL - Empty tables requiring immediate data load:")
        for table in empty_tables:
            print(f"   - {table}")
            if 'sunbiz' in table:
                print(f"     -> This is why the Sunbiz tab shows no data")
    
    if low_data_tables:
        print(f"\nWARNING - Tables with low data:")
        for table in low_data_tables:
            print(f"   - {table}")
    
    print("\nRECOMMENDATIONS:")
    print("-" * 40)
    
    if 'sunbiz_corporate' in empty_tables:
        print("\n1. SUNBIZ DATA LOADING (Priority 1)")
        print("   The Sunbiz tables are completely empty, causing the Sunbiz tab to fail.")
        print("   Actions needed:")
        print("   - Run the Sunbiz data pipeline to load Florida business data")
        print("   - Execute: python apps/api/sunbiz_pipeline.py")
        print("   - Or load sample data: python load_sample_sunbiz_data.py")
    
    if 'property_sales_history' in empty_tables:
        print("\n2. SALES HISTORY DATA (Priority 2)")
        print("   No sales history data is available.")
        print("   Actions needed:")
        print("   - Load sales data from Florida revenue files")
        print("   - Execute: python load_sales_data.py")
    
    if 'nav_assessments' in empty_tables:
        print("\n3. ASSESSMENT DATA (Priority 3)")
        print("   No assessment data is available.")
        print("   Actions needed:")
        print("   - Load NAV assessment files")
        print("   - Execute: python apps/workers/nav_assessments/load_nav_data.py")
    
    print("\nWORKING COMPONENTS:")
    print("-" * 40)
    if 'florida_parcels' not in empty_tables:
        print("- Florida parcels table has data - property search should work")
    if 'properties' not in empty_tables:
        print("- Properties table has data - basic property info available")
    
    print("\n" + "=" * 80)
    print(" Report Complete")
    print("=" * 80)

if __name__ == "__main__":
    main()