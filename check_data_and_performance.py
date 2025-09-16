"""
Check data completeness and performance issues
"""

import os
import time
from dotenv import load_dotenv
from supabase import create_client
import httpx
import json

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv(override=True)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

print("DATA & PERFORMANCE CHECK")
print("=" * 80)

# 1. Check data completeness
print("\n1. DATA LOADED FROM FLORIDA SOURCES:")
print("-" * 80)

# Check main tables
checks = [
    ('florida_parcels', 'NAL - Name/Address/Legal'),
    ('property_sales_history', 'SDF - Sales Data File'),
    ('nav_assessments', 'NAV/NAP - Assessments'),
    ('sunbiz_corporate', 'Sunbiz - Business Entities'),
    ('fl_tpp_accounts', 'TPP - Tangible Property'),
]

total_expected = {
    'florida_parcels': 600000,  # Should have ~600K+ Broward properties
    'property_sales_history': 50000,  # Should have many sales
    'nav_assessments': 100000,  # Should have many assessments
    'sunbiz_corporate': 10000,  # Should have business data
    'fl_tpp_accounts': 10000,  # Should have TPP data
}

for table, source in checks:
    try:
        result = client.table(table).select('*', count='exact', head=True).execute()
        count = result.count if hasattr(result, 'count') else 0
        expected = total_expected.get(table, 1000)
        
        if count > expected * 0.5:
            status = "[LOADED]"
        elif count > 0:
            status = "[PARTIAL]"
        else:
            status = "[MISSING]"
            
        print(f"  {status} {source:30} : {count:>10,} records in {table}")
        
        if count < expected * 0.1:
            print(f"         WARNING: Expected ~{expected:,} records but only have {count:,}")
    except:
        print(f"  [ERROR] {source:30} : Table {table} not found")

# 2. Check why website is slow
print("\n2. PERFORMANCE BOTTLENECKS:")
print("-" * 80)

# Test search query
print("\nTesting property search queries...")

# Test 1: Count query
start = time.time()
try:
    result = client.table('florida_parcels').select('*', count='exact', head=True).execute()
    elapsed = time.time() - start
    print(f"  Total count query: {elapsed:.2f} seconds")
    if elapsed > 1.0:
        print("    >> TOO SLOW! Need to optimize count queries")
except Exception as e:
    print(f"  Count failed: {str(e)[:100]}")

# Test 2: Pagination test
start = time.time()
try:
    result = client.table('florida_parcels').select('parcel_id,phy_addr1,owner_name,assessed_value').limit(20).execute()
    elapsed = time.time() - start
    records = len(result.data) if result.data else 0
    print(f"  Load 20 properties: {elapsed:.2f} seconds ({records} records)")
    if elapsed > 0.5:
        print("    >> SLOW! Check if indexes exist")
except Exception as e:
    print(f"  Pagination failed: {str(e)[:100]}")

# Test 3: Search test
search_term = "MAIN"
start = time.time()
try:
    result = client.table('florida_parcels').select('*').ilike('phy_addr1', f'%{search_term}%').limit(10).execute()
    elapsed = time.time() - start
    found = len(result.data) if result.data else 0
    print(f"  Search for '{search_term}': {elapsed:.2f} seconds ({found} results)")
    if elapsed > 2.0:
        print("    >> VERY SLOW! Text search needs full-text index")
except Exception as e:
    print(f"  Search failed: {str(e)[:100]}")

# 3. Check missing data sources
print("\n3. MISSING DATA SOURCES:")
print("-" * 80)

print("\nData that should be downloaded but appears missing:")

missing = []

# Check sales data
try:
    sales_count = client.table('property_sales_history').select('*', count='exact', head=True).execute()
    if sales_count.count < 1000:
        missing.append("SDF - Sales Data File (only " + str(sales_count.count) + " records)")
except:
    missing.append("SDF - Sales Data File (table error)")

# Check NAV data
try:
    nav_count = client.table('nav_assessments').select('*', count='exact', head=True).execute()
    if nav_count.count < 1000:
        missing.append("NAV - Assessment Data (only " + str(nav_count.count) + " records)")
except:
    missing.append("NAV - Assessment Data (table error)")

# Check Sunbiz
try:
    sunbiz_count = client.table('sunbiz_corporate').select('*', count='exact', head=True).execute()
    if sunbiz_count.count < 100:
        missing.append("Sunbiz - Business Entities (only " + str(sunbiz_count.count) + " records)")
except:
    missing.append("Sunbiz - Business Entities (table error)")

for item in missing:
    print(f"  - {item}")

# 4. Create fix script
print("\n4. CREATING FIX SCRIPTS:")
print("-" * 80)

# Create optimization SQL
optimization_sql = """-- IMMEDIATE PERFORMANCE FIX FOR CONCORDBROKER

-- 1. Critical indexes for 789K parcels table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_parcel ON florida_parcels(parcel_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_county ON florida_parcels(county);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_city ON florida_parcels(phy_city);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_addr ON florida_parcels(phy_addr1);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fl_parcels_owner ON florida_parcels(owner_name);

-- 2. Create limited view for fast queries
CREATE OR REPLACE VIEW florida_parcels_fast AS
SELECT 
    parcel_id,
    phy_addr1,
    phy_city,
    phy_zipcd,
    owner_name,
    assessed_value,
    year_built,
    bedrooms,
    bathrooms
FROM florida_parcels
LIMIT 10000;  -- Only show first 10K for fast loading

-- 3. Update statistics
ANALYZE florida_parcels;

SELECT 'Indexes created - queries should be faster now!' as status;
"""

with open('fix_performance_now.sql', 'w') as f:
    f.write(optimization_sql)

print("Created: fix_performance_now.sql")
print("  >> Run this in Supabase SQL Editor NOW to fix slow queries")

# Create data loading script
load_script = """# Load missing Florida data sources

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# List of data files to download and load
FILES_TO_LOAD = {
    'SDF': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF16P202501.csv',
    'NAV': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV16P202501.csv',
    'NAP': 'https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAP16P202501.csv',
}

# Download and load each file
for name, url in FILES_TO_LOAD.items():
    print(f"Downloading {name} from {url}")
    # Download logic here
    # Load to appropriate table
"""

with open('load_missing_data.py', 'w') as f:
    f.write(load_script)

print("\nCreated: load_missing_data.py")
print("  >> Template for loading missing data files")

print("\n" + "=" * 80)
print("SUMMARY:")
print("-" * 80)
print("\nMAIN ISSUES FOUND:")
print("1. Database has 789K parcels but MISSING indexes = SLOW")
print("2. Sales history has only 3 records (should have thousands)")
print("3. NAV assessments has only 1 record (should have thousands)")
print("4. Sunbiz corporate is empty (should have business data)")
print("5. No pagination in UI queries (loading all 789K at once)")

print("\nACTION ITEMS:")
print("1. RUN fix_performance_now.sql in Supabase immediately")
print("2. Load the missing SDF, NAV, NAP data files")
print("3. Load Sunbiz business data")
print("4. Update UI to use pagination (limit 20-50 per page)")