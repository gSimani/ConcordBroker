"""
Optimize database performance for fast website data extraction
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get("VITE_SUPABASE_URL")
key = os.environ.get("VITE_SUPABASE_ANON_KEY")
supabase = create_client(url, key)

def check_database_performance():
    """Check current database state and performance"""
    
    print("DATABASE PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    # 1. Check total record count
    try:
        result = supabase.table('florida_parcels').select('id', count='exact').execute()
        total_count = result.count or 0
        print(f"Total Properties: {total_count:,}")
        
        # 2. Check properties with key data
        value_result = supabase.table('florida_parcels').select('id', count='exact').gt('just_value', 0).execute()
        value_count = value_result.count or 0
        print(f"Properties with Values: {value_count:,} ({(value_count/total_count*100):.1f}%)")
        
        # 3. Check address completeness
        addr_result = supabase.table('florida_parcels').select('id', count='exact').neq('phy_addr1', None).execute()
        addr_count = addr_result.count or 0
        print(f"Properties with Addresses: {addr_count:,} ({(addr_count/total_count*100):.1f}%)")
        
        # 4. Check owner data
        owner_result = supabase.table('florida_parcels').select('id', count='exact').neq('owner_name', None).execute()
        owner_count = owner_result.count or 0
        print(f"Properties with Owners: {owner_count:,} ({(owner_count/total_count*100):.1f}%)")
        
    except Exception as e:
        print(f"Error checking database: {e}")
    
    print("\nSAMPLE DATA QUALITY CHECK")
    print("-" * 30)
    
    # Sample data check
    try:
        sample = supabase.table('florida_parcels').select(
            'parcel_id, owner_name, phy_addr1, just_value, assessed_value'
        ).neq('just_value', None).order('just_value', desc=True).limit(5).execute()
        
        if sample.data:
            print("Top 5 properties by value:")
            for prop in sample.data:
                parcel = prop.get('parcel_id', 'N/A')
                owner = prop.get('owner_name', 'N/A')[:30]
                addr = prop.get('phy_addr1', 'N/A')[:40]
                value = prop.get('just_value', 0)
                print(f"  {parcel}: ${value:,} - {owner} at {addr}")
    
    except Exception as e:
        print(f"Error getting sample data: {e}")

def test_query_performance():
    """Test query performance for common website operations"""
    
    print(f"\nQUERY PERFORMANCE TEST")
    print("-" * 30)
    
    import time
    
    # Test 1: Property lookup by parcel ID (most common)
    start_time = time.time()
    try:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
        lookup_time = (time.time() - start_time) * 1000
        success = len(result.data) > 0
        print(f"Property lookup by ID: {lookup_time:.0f}ms {'✓' if success else '✗'}")
    except Exception as e:
        print(f"Property lookup failed: {e}")
    
    # Test 2: Search by city (property search page)
    start_time = time.time()
    try:
        result = supabase.table('florida_parcels').select('parcel_id, phy_addr1, just_value').eq('phy_city', 'PARKLAND').limit(10).execute()
        city_time = (time.time() - start_time) * 1000
        success = len(result.data) > 0
        print(f"Search by city: {city_time:.0f}ms {'✓' if success else '✗'} ({len(result.data)} results)")
    except Exception as e:
        print(f"City search failed: {e}")
    
    # Test 3: Value range query (market analysis)
    start_time = time.time()
    try:
        result = supabase.table('florida_parcels').select('parcel_id, just_value').gte('just_value', 500000).lte('just_value', 1000000).limit(10).execute()
        value_time = (time.time() - start_time) * 1000
        success = len(result.data) > 0
        print(f"Value range query: {value_time:.0f}ms {'✓' if success else '✗'} ({len(result.data)} results)")
    except Exception as e:
        print(f"Value range failed: {e}")
    
    # Test 4: Owner search (business intelligence)
    start_time = time.time()
    try:
        result = supabase.table('florida_parcels').select('parcel_id, phy_addr1').ilike('owner_name', '%INVITATION%').limit(5).execute()
        owner_time = (time.time() - start_time) * 1000
        success = len(result.data) > 0
        print(f"Owner name search: {owner_time:.0f}ms {'✓' if success else '✗'} ({len(result.data)} results)")
    except Exception as e:
        print(f"Owner search failed: {e}")

def check_specific_property():
    """Check our corrected property data"""
    
    print(f"\nSPECIFIC PROPERTY CHECK")
    print("-" * 30)
    
    try:
        result = supabase.table('florida_parcels').select('*').eq('parcel_id', '474131031040').execute()
        
        if result.data:
            prop = result.data[0]
            print(f"Property 474131031040 (12681 NW 78 MNR):")
            print(f"  Owner: {prop.get('owner_name')}")
            print(f"  Address: {prop.get('phy_addr1')}")
            print(f"  Just Value: ${prop.get('just_value', 0):,}")
            print(f"  Assessed: ${prop.get('assessed_value', 0):,}")
            print(f"  Living Area: {prop.get('total_living_area', 0)} sq ft")
            print(f"  Bedrooms: {prop.get('bedrooms', 'N/A')}")
            print(f"  Bathrooms: {prop.get('bathrooms', 'N/A')}")
            
            # Check data completeness
            fields = ['owner_name', 'phy_addr1', 'just_value', 'assessed_value', 'total_living_area']
            complete_fields = sum(1 for field in fields if prop.get(field))
            completeness = (complete_fields / len(fields)) * 100
            print(f"  Data Completeness: {completeness:.0f}% ({complete_fields}/{len(fields)} fields)")
            
        else:
            print("Property 474131031040 not found!")
    
    except Exception as e:
        print(f"Error checking property: {e}")

def provide_optimization_recommendations():
    """Provide recommendations for database optimization"""
    
    print(f"\nOPTIMIZATION RECOMMENDATIONS")
    print("-" * 40)
    
    print("For optimal website performance:")
    print("1. ✓ Primary key on parcel_id for fast property lookups")
    print("2. ✓ Index on phy_city for property search by location") 
    print("3. ✓ Index on just_value for value-based filtering")
    print("4. ✓ Index on owner_name for business intelligence queries")
    print("5. ✓ Composite index on (phy_city, just_value) for market analysis")
    
    print("\nSUGGESTED SUPABASE SQL (run in SQL Editor):")
    print('''
-- Create performance indexes for fast website queries
CREATE INDEX IF NOT EXISTS idx_parcel_id ON florida_parcels(parcel_id);
CREATE INDEX IF NOT EXISTS idx_phy_city ON florida_parcels(phy_city);
CREATE INDEX IF NOT EXISTS idx_just_value ON florida_parcels(just_value);
CREATE INDEX IF NOT EXISTS idx_owner_name ON florida_parcels USING gin(owner_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_city_value ON florida_parcels(phy_city, just_value);
    ''')

if __name__ == "__main__":
    check_database_performance()
    test_query_performance() 
    check_specific_property()
    provide_optimization_recommendations()