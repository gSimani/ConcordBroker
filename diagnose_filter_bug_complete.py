"""
COMPREHENSIVE FILTER BUG DIAGNOSIS
Using Supabase PostgREST client to diagnose why only 7 properties show up
Expected: 140,742 large buildings (7,500+ sqft)
Actual: 7 properties shown in UI
"""
import sys
import json
from datetime import datetime
from supabase import create_client, Client
from postgrest import SyncSelectRequestBuilder

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 100)
print("COMPREHENSIVE FILTER BUG DIAGNOSIS")
print("=" * 100)
print()

diagnosis = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "root_cause": None,
    "fix_recommendations": []
}

# ============================================================================
# TEST 1: Basic Query - No Filters
# ============================================================================
print("TEST 1: Basic Query - Count ALL properties with buildings")
print("-" * 100)

test1_result = {"name": "Basic Query", "status": "PENDING"}

try:
    # Method 1: Using count with limit
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .gt('total_living_area', 0)\
        .limit(1)\
        .execute()

    total_with_buildings = response.count if hasattr(response, 'count') else 0
    print(f"✓ Properties with buildings (total_living_area > 0): {total_with_buildings:,}")

    test1_result["status"] = "PASS"
    test1_result["count"] = total_with_buildings

except Exception as e:
    print(f"✗ ERROR: {e}")
    test1_result["status"] = "FAIL"
    test1_result["error"] = str(e)

diagnosis["tests"].append(test1_result)
print()

# ============================================================================
# TEST 2: Large Buildings Query (10k-20k sqft)
# ============================================================================
print("TEST 2: Large Buildings Query (10,000-20,000 sqft)")
print("-" * 100)

test2_result = {"name": "Large Buildings 10k-20k", "status": "PENDING"}

try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(1)\
        .execute()

    count_10k_20k = response.count if hasattr(response, 'count') else 0
    print(f"✓ Properties in 10k-20k range: {count_10k_20k:,}")

    test2_result["status"] = "PASS"
    test2_result["count"] = count_10k_20k

    if count_10k_20k < 100:
        print(f"⚠️  WARNING: Expected ~45,000, got {count_10k_20k}")
        test2_result["warning"] = "Count much lower than expected"

except Exception as e:
    print(f"✗ ERROR: {e}")
    test2_result["status"] = "FAIL"
    test2_result["error"] = str(e)

diagnosis["tests"].append(test2_result)
print()

# ============================================================================
# TEST 3: Simulate Frontend Filter Request
# ============================================================================
print("TEST 3: Simulate Frontend Filter Request (with all typical filters)")
print("-" * 100)

test3_result = {"name": "Frontend Simulation", "status": "PENDING", "scenarios": []}

# Scenario A: Only building size filter
print("  Scenario A: Only building size filter (minBuildingSqFt=10000, maxBuildingSqFt=20000)")
try:
    query = supabase.table('florida_parcels')\
        .select('*', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(100)

    response = query.execute()
    count_a = response.count if hasattr(response, 'count') else len(response.data)

    print(f"    Result: {count_a:,} properties (first 100 of {response.count if hasattr(response, 'count') else 'unknown'})")

    test3_result["scenarios"].append({
        "name": "Building size only",
        "count": count_a,
        "full_count": response.count if hasattr(response, 'count') else None,
        "status": "PASS" if count_a > 7 else "FAIL"
    })

except Exception as e:
    print(f"    ERROR: {e}")
    test3_result["scenarios"].append({
        "name": "Building size only",
        "status": "FAIL",
        "error": str(e)
    })

# Scenario B: Building size + Year filter
print("  Scenario B: Building size + Year (minBuildingSqFt=10000, year=2025)")
try:
    query = supabase.table('florida_parcels')\
        .select('*', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .eq('year', 2025)\
        .limit(100)

    response = query.execute()
    count_b = response.count if hasattr(response, 'count') else len(response.data)

    print(f"    Result: {count_b:,} properties")

    test3_result["scenarios"].append({
        "name": "Building size + year",
        "count": count_b,
        "status": "PASS" if count_b > 7 else "FAIL"
    })

except Exception as e:
    print(f"    ERROR: {e}")
    test3_result["scenarios"].append({
        "name": "Building size + year",
        "status": "FAIL",
        "error": str(e)
    })

# Scenario C: Building size + County filter
print("  Scenario C: Building size + County (minBuildingSqFt=10000, county=MIAMI-DADE)")
try:
    query = supabase.table('florida_parcels')\
        .select('*', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .eq('county', 'MIAMI-DADE')\
        .limit(100)

    response = query.execute()
    count_c = response.count if hasattr(response, 'count') else len(response.data)

    print(f"    Result: {count_c:,} properties")

    test3_result["scenarios"].append({
        "name": "Building size + county",
        "count": count_c,
        "status": "PASS" if count_c > 7 else "FAIL"
    })

except Exception as e:
    print(f"    ERROR: {e}")
    test3_result["scenarios"].append({
        "name": "Building size + county",
        "status": "FAIL",
        "error": str(e)
    })

# Scenario D: Exact replication of what frontend might send
print("  Scenario D: Full frontend params (all filters)")
try:
    query = supabase.table('florida_parcels')\
        .select('*', count='exact')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .eq('year', 2025)\
        .order('just_value', desc=True)\
        .range(0, 99)

    response = query.execute()
    count_d = len(response.data)
    full_count_d = response.count if hasattr(response, 'count') else None

    print(f"    Result: {count_d} properties returned (total: {full_count_d:,})")

    test3_result["scenarios"].append({
        "name": "Full params with pagination",
        "count": count_d,
        "full_count": full_count_d,
        "status": "PASS" if full_count_d and full_count_d > 7 else "FAIL"
    })

except Exception as e:
    print(f"    ERROR: {e}")
    test3_result["scenarios"].append({
        "name": "Full params with pagination",
        "status": "FAIL",
        "error": str(e)
    })

test3_result["status"] = "PASS" if any(s.get("status") == "PASS" for s in test3_result["scenarios"]) else "FAIL"
diagnosis["tests"].append(test3_result)
print()

# ============================================================================
# TEST 4: Check for Data Inconsistencies
# ============================================================================
print("TEST 4: Data Inconsistency Check")
print("-" * 100)

test4_result = {"name": "Data Consistency", "status": "PENDING", "checks": []}

# Check for NULL values
print("  Checking for NULL/invalid values in total_living_area...")
try:
    # Count properties where total_living_area is NULL
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .is_('total_living_area', 'null')\
        .limit(1)\
        .execute()

    null_count = response.count if hasattr(response, 'count') else 0
    print(f"    NULL values: {null_count:,}")

    test4_result["checks"].append({
        "name": "NULL values",
        "count": null_count,
        "status": "OK"
    })

except Exception as e:
    print(f"    ERROR: {e}")

# Check for zero values
print("  Checking for zero values in total_living_area...")
try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .eq('total_living_area', 0)\
        .limit(1)\
        .execute()

    zero_count = response.count if hasattr(response, 'count') else 0
    print(f"    Zero values: {zero_count:,}")

    test4_result["checks"].append({
        "name": "Zero values",
        "count": zero_count,
        "status": "OK"
    })

except Exception as e:
    print(f"    ERROR: {e}")

# Check for negative values
print("  Checking for negative values in total_living_area...")
try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id', count='exact')\
        .lt('total_living_area', 0)\
        .limit(1)\
        .execute()

    negative_count = response.count if hasattr(response, 'count') else 0
    print(f"    Negative values: {negative_count:,}")

    test4_result["checks"].append({
        "name": "Negative values",
        "count": negative_count,
        "status": "OK" if negative_count == 0 else "WARNING"
    })

except Exception as e:
    print(f"    ERROR: {e}")

test4_result["status"] = "PASS"
diagnosis["tests"].append(test4_result)
print()

# ============================================================================
# TEST 5: Actual Property Retrieval
# ============================================================================
print("TEST 5: Actual Property Retrieval (get real data)")
print("-" * 100)

test5_result = {"name": "Property Retrieval", "status": "PENDING", "samples": []}

try:
    response = supabase.table('florida_parcels')\
        .select('parcel_id, county, total_living_area, owner_name, just_value')\
        .gte('total_living_area', 10000)\
        .lte('total_living_area', 20000)\
        .limit(10)\
        .execute()

    if response.data:
        print(f"✓ Retrieved {len(response.data)} sample properties:")
        print()
        print(f"{'Parcel ID':<20} {'County':<15} {'SqFt':>10} {'Value':>15}")
        print("-" * 65)

        for prop in response.data:
            parcel = prop.get('parcel_id', 'N/A')
            county = prop.get('county', 'N/A')
            sqft = prop.get('total_living_area', 0)
            value = prop.get('just_value', 0)

            print(f"{parcel:<20} {county:<15} {sqft:>10,} ${value:>14,}")

            test5_result["samples"].append({
                "parcel_id": parcel,
                "county": county,
                "sqft": sqft,
                "value": value
            })

        test5_result["status"] = "PASS"
        test5_result["count"] = len(response.data)
    else:
        print("✗ No properties returned!")
        test5_result["status"] = "FAIL"
        test5_result["count"] = 0

except Exception as e:
    print(f"✗ ERROR: {e}")
    test5_result["status"] = "FAIL"
    test5_result["error"] = str(e)

diagnosis["tests"].append(test5_result)
print()

# ============================================================================
# TEST 6: Check Current API Implementation
# ============================================================================
print("TEST 6: Analyze Current API Implementation")
print("-" * 100)

test6_result = {"name": "API Analysis", "status": "PENDING", "findings": []}

print("  Checking property_live_api.py for potential issues...")

api_file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\apps\api\property_live_api.py"

try:
    with open(api_file_path, 'r', encoding='utf-8') as f:
        api_content = f.read()

    # Check for building sqft filter implementation
    if 'minBuildingSqFt' in api_content:
        print("  ✓ Found minBuildingSqFt parameter handling")
        test6_result["findings"].append("minBuildingSqFt parameter exists")

        # Check if it uses total_living_area
        if 'total_living_area' in api_content:
            print("  ✓ Uses total_living_area column")
            test6_result["findings"].append("Correct column name used")
        else:
            print("  ✗ WARNING: May not use total_living_area column")
            test6_result["findings"].append("WARNING: Column name may be wrong")
    else:
        print("  ✗ minBuildingSqFt parameter NOT found in API!")
        test6_result["findings"].append("CRITICAL: minBuildingSqFt not implemented")

    # Check for default filters
    if 'limit(' in api_content:
        import re
        limits = re.findall(r'\.limit\((\d+)\)', api_content)
        if limits:
            print(f"  ⚠️  Found limit() calls: {limits}")
            test6_result["findings"].append(f"Pagination limits found: {limits}")

    test6_result["status"] = "PASS"

except FileNotFoundError:
    print(f"  ✗ API file not found: {api_file_path}")
    test6_result["status"] = "FAIL"
    test6_result["error"] = "API file not found"
except Exception as e:
    print(f"  ✗ ERROR: {e}")
    test6_result["status"] = "FAIL"
    test6_result["error"] = str(e)

diagnosis["tests"].append(test6_result)
print()

# ============================================================================
# ROOT CAUSE ANALYSIS
# ============================================================================
print()
print("=" * 100)
print("ROOT CAUSE ANALYSIS")
print("=" * 100)
print()

# Analyze all test results
database_working = test2_result.get("count", 0) > 1000
frontend_issue = any(s.get("count", 0) < 100 for s in test3_result.get("scenarios", []))

if database_working and not frontend_issue:
    diagnosis["root_cause"] = "DATABASE_HEALTHY"
    print("✓ ROOT CAUSE: Database has all the data!")
    print(f"  - Supabase contains {test2_result.get('count', 0):,} properties in 10k-20k range")
    print("  - All test queries returned correct counts")
    print("  - Issue is likely in frontend filter application or API parameter mapping")
    print()

    diagnosis["fix_recommendations"] = [
        "Check PropertySearch.tsx filter state management",
        "Verify API parameters are being sent correctly (check Network tab)",
        "Add logging to property_live_api.py to see actual filters received",
        "Check if default filters are being applied (county, year, etc.)",
        "Verify pagination isn't limiting results to 7"
    ]

elif not database_working:
    diagnosis["root_cause"] = "DATABASE_ISSUE"
    print("✗ ROOT CAUSE: Database query issue")
    print(f"  - Expected ~45,000 properties in 10k-20k range")
    print(f"  - Got {test2_result.get('count', 0):,} properties")
    print()

    diagnosis["fix_recommendations"] = [
        "Check if total_living_area column has correct data type",
        "Verify data import completed successfully",
        "Check for indexing issues causing query problems",
        "Re-import NAL files if necessary"
    ]
else:
    diagnosis["root_cause"] = "COMPLEX_ISSUE"
    print("⚠️  ROOT CAUSE: Complex issue requiring deeper investigation")
    print()

    diagnosis["fix_recommendations"] = [
        "Enable detailed logging in both frontend and backend",
        "Use browser DevTools to inspect actual API calls",
        "Check Supabase dashboard for query performance issues",
        "Review PostgREST query construction in API"
    ]

# Print recommendations
print("RECOMMENDED FIXES:")
print("-" * 100)
for i, rec in enumerate(diagnosis["fix_recommendations"], 1):
    print(f"  {i}. {rec}")

print()

# ============================================================================
# SAVE DIAGNOSIS REPORT
# ============================================================================
output_file = f"filter_bug_diagnosis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(output_file, 'w') as f:
    json.dump(diagnosis, f, indent=2, default=str)

print()
print("=" * 100)
print("DIAGNOSIS COMPLETE")
print("=" * 100)
print(f"Report saved to: {output_file}")
print()
print("Summary:")
print(f"  - Tests run: {len(diagnosis['tests'])}")
print(f"  - Root cause: {diagnosis['root_cause']}")
print(f"  - Recommendations: {len(diagnosis['fix_recommendations'])}")
print()
print("=" * 100)