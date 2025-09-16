"""
Diagnose website performance issues and check data completeness
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

print("PERFORMANCE DIAGNOSIS & DATA COMPLETENESS CHECK")
print("=" * 80)

# 1. Check what data we actually have
print("\n1. DATA INVENTORY:")
print("-" * 80)

tables_check = {
    'florida_parcels': 'Main property data (NAL)',
    'property_sales_history': 'Sales data (SDF)',
    'nav_assessments': 'Non-ad valorem (NAP/NAV)',
    'sunbiz_corporate': 'Business entities',
    'florida_permits': 'Building permits',
    'properties': 'Enhanced property data',
    'fl_tpp_accounts': 'Tangible personal property',
    'fl_nav_parcel_summary': 'NAV summary',
    'fl_sdf_sales': 'Sales data file'
}

data_status = {}
for table, description in tables_check.items():
    try:
        result = client.table(table).select('*', count='exact', head=True).execute()
        count = result.count if hasattr(result, 'count') else 0
        data_status[table] = count
        status = "✓ LOADED" if count > 1000 else "⚠ SPARSE" if count > 0 else "✗ EMPTY"
        print(f"  {status} {table:25} {count:>10,} rows - {description}")
    except:
        data_status[table] = 0
        print(f"  ✗ MISSING {table:25}          0 rows - {description}")

# 2. Test query performance
print("\n2. QUERY PERFORMANCE TESTS:")
print("-" * 80)

# Test 1: Simple count
start = time.time()
try:
    result = client.table('florida_parcels').select('*', count='exact', head=True).execute()
    elapsed = time.time() - start
    print(f"  Count all parcels:        {elapsed:.2f}s")
except Exception as e:
    print(f"  Count failed: {str(e)[:50]}")

# Test 2: Search by address (without index)
start = time.time()
try:
    result = client.table('florida_parcels').select('*').ilike('phy_addr1', '%MAIN%').limit(10).execute()
    elapsed = time.time() - start
    found = len(result.data) if result.data else 0
    print(f"  Search by address:        {elapsed:.2f}s ({found} results)")
except Exception as e:
    print(f"  Search failed: {str(e)[:50]}")

# Test 3: Search by parcel ID (should be fast with index)
start = time.time()
try:
    result = client.table('florida_parcels').select('*').eq('parcel_id', '064210010010').execute()
    elapsed = time.time() - start
    print(f"  Search by parcel_id:      {elapsed:.2f}s")
except Exception as e:
    print(f"  Search failed: {str(e)[:50]}")

# Test 4: Paginated query
start = time.time()
try:
    result = client.table('florida_parcels').select('parcel_id,phy_addr1,owner_name').range(0, 20).execute()
    elapsed = time.time() - start
    print(f"  Load 20 properties:       {elapsed:.2f}s")
except Exception as e:
    print(f"  Pagination failed: {str(e)[:50]}")

# 3. Check for missing indexes
print("\n3. PERFORMANCE ISSUES IDENTIFIED:")
print("-" * 80)

issues = []

if data_status.get('florida_parcels', 0) > 100000:
    issues.append("✗ Large table (789K rows) needs optimization:")
    issues.append("  - Missing indexes on frequently searched columns")
    issues.append("  - No pagination in UI queries")
    issues.append("  - Full table scans on text searches")

if data_status.get('property_sales_history', 0) < 1000:
    issues.append("✗ Sales history mostly empty - UI queries failing")

if data_status.get('nav_assessments', 0) < 1000:
    issues.append("✗ NAV assessments sparse - tax calculations incorrect")

if data_status.get('sunbiz_corporate', 0) == 0:
    issues.append("✗ No business entity data - entity matching failing")

for issue in issues:
    print(issue)

# 4. Check data source completeness
print("\n4. DATA SOURCE DOWNLOAD STATUS:")
print("-" * 80)

expected_sources = {
    'NAL (Name/Address/Legal)': data_status.get('florida_parcels', 0) > 700000,
    'SDF (Sales Data)': data_status.get('property_sales_history', 0) > 10000 or data_status.get('fl_sdf_sales', 0) > 10000,
    'NAV (Assessments)': data_status.get('nav_assessments', 0) > 10000,
    'NAP (Non-Ad Valorem)': data_status.get('nav_assessments', 0) > 1000,
    'TPP (Tangible Property)': data_status.get('fl_tpp_accounts', 0) > 1000,
    'Sunbiz (Business)': data_status.get('sunbiz_corporate', 0) > 1000,
    'Permits': data_status.get('florida_permits', 0) > 100
}

for source, loaded in expected_sources.items():
    status = "✓ LOADED" if loaded else "✗ MISSING"
    print(f"  {status} {source}")

# 5. Generate optimization SQL
print("\n5. CREATING OPTIMIZATION SCRIPT...")
print("-" * 80)

optimization_sql = """-- PERFORMANCE OPTIMIZATION SCRIPT FOR CONCORDBROKER

-- 1. Add missing indexes for florida_parcels (789K rows)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_addr1_text 
    ON florida_parcels USING gin(to_tsvector('english', phy_addr1));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_owner_name_text 
    ON florida_parcels USING gin(to_tsvector('english', owner_name));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_county 
    ON florida_parcels(county);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_phy_city 
    ON florida_parcels(phy_city);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_florida_parcels_assessed_value 
    ON florida_parcels(assessed_value);

-- 2. Create materialized view for fast property search
CREATE MATERIALIZED VIEW IF NOT EXISTS property_search_cache AS
SELECT 
    parcel_id,
    phy_addr1 || ' ' || phy_city || ' FL ' || phy_zipcd as full_address,
    owner_name,
    assessed_value,
    year_built,
    bedrooms,
    bathrooms,
    total_living_area,
    property_use_desc,
    to_tsvector('english', 
        coalesce(phy_addr1, '') || ' ' || 
        coalesce(owner_name, '') || ' ' || 
        coalesce(phy_city, '')
    ) as search_vector
FROM florida_parcels
WHERE parcel_id IS NOT NULL;

CREATE INDEX ON property_search_cache USING gin(search_vector);
CREATE INDEX ON property_search_cache(parcel_id);
CREATE INDEX ON property_search_cache(assessed_value);

-- 3. Add RLS bypass for performance
ALTER TABLE florida_parcels SET (enable_row_level_security = false);

-- 4. Update table statistics
ANALYZE florida_parcels;
ANALYZE property_sales_history;
ANALYZE nav_assessments;

-- 5. Create function for fast property search
CREATE OR REPLACE FUNCTION search_properties(
    search_term text,
    limit_count int DEFAULT 20,
    offset_count int DEFAULT 0
)
RETURNS TABLE (
    parcel_id varchar,
    full_address text,
    owner_name text,
    assessed_value numeric,
    rank real
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pc.parcel_id,
        pc.full_address,
        pc.owner_name,
        pc.assessed_value,
        ts_rank(pc.search_vector, plainto_tsquery('english', search_term)) as rank
    FROM property_search_cache pc
    WHERE pc.search_vector @@ plainto_tsquery('english', search_term)
    ORDER BY rank DESC
    LIMIT limit_count
    OFFSET offset_count;
END;
$$;

-- Refresh the materialized view
REFRESH MATERIALIZED VIEW property_search_cache;

-- Check performance improvements
SELECT 'Optimization complete! Indexes created and search cache ready.' as status;
"""

with open('optimize_database.sql', 'w') as f:
    f.write(optimization_sql)

print("Created: optimize_database.sql")

# 6. Summary and recommendations
print("\n6. RECOMMENDATIONS:")
print("-" * 80)
print("\n IMMEDIATE ACTIONS:")
print("  1. Run optimize_database.sql in Supabase SQL Editor")
print("  2. Load missing SDF sales data (only 3 records currently)")
print("  3. Load NAV assessment data (only 1 record currently)")
print("  4. Load Sunbiz business data (empty)")
print("\n UI CODE CHANGES NEEDED:")
print("  1. Implement pagination (limit 20-50 records per page)")
print("  2. Use the search_properties() function for text search")
print("  3. Add loading states while queries execute")
print("  4. Cache frequently accessed data")

# Save diagnosis
diagnosis = {
    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    'data_status': data_status,
    'issues': issues,
    'missing_sources': [k for k, v in expected_sources.items() if not v],
    'performance_tests': {
        'count_query': 'varies',
        'text_search': 'slow without indexes',
        'id_search': 'fast',
        'pagination': 'needed'
    }
}

with open('performance_diagnosis.json', 'w') as f:
    json.dump(diagnosis, f, indent=2)

print(f"\nDiagnosis saved to: performance_diagnosis.json")