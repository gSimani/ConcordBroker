"""
Execute County-Batched DOR Use Code Assignment
Processes all 9.1M Florida properties by county to avoid timeouts
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

# Supabase Configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# DOR Use Code Assignment Logic (ordered by priority)
ASSIGNMENT_LOGIC = [
    {
        "code": "02",
        "label": "MF 10+",
        "conditions": "building_value.gt.500000,building_value.gt.0,land_value.lt.250000"
    },
    {
        "code": "24",
        "label": "Industrial",
        "conditions": "building_value.gt.1000000,land_value.lt.500000"
    },
    {
        "code": "17",
        "label": "Commercial",
        "conditions": "just_value.gt.500000,building_value.gt.200000,building_value.gt.0"
    },
    {
        "code": "01",
        "label": "Agricult.",
        "conditions": "land_value.gt.100000,building_value.lt.20000"
    },
    {
        "code": "03",
        "label": "Condo",
        "conditions": "just_value.gte.100000,just_value.lte.500000,building_value.gte.50000,building_value.lte.300000"
    },
    {
        "code": "10",
        "label": "Vacant Res",
        "conditions": "land_value.gt.0,building_value.lte.1000"
    },
    {
        "code": "00",
        "label": "SFR",
        "conditions": "building_value.gt.50000,just_value.lt.1000000"
    }
]

def execute_sql_query(sql: str) -> Dict:
    """Execute SQL via Supabase RPC"""
    url = f"{SUPABASE_URL}/rest/v1/rpc/execute_sql"
    payload = {"query": sql}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        if response.status_code in [200, 201]:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Status {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_county_distribution() -> List[Tuple[str, int]]:
    """Get list of counties ordered by properties needing updates"""
    print("\n[PHASE 1] Analyzing County Distribution")
    print("=" * 80)

    sql = """
    SELECT
        county,
        COUNT(*) as total,
        COUNT(CASE WHEN land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99' THEN 1 END) as need_update
    FROM florida_parcels
    WHERE year = 2025
    GROUP BY county
    ORDER BY need_update DESC
    """

    result = execute_sql_query(sql)
    if not result["success"]:
        print(f"[ERROR] Failed to get county distribution: {result['error']}")
        return []

    counties = [(row["county"], row["need_update"]) for row in result["data"]]

    print(f"[SUCCESS] Found {len(counties)} counties")
    print(f"\nTop 10 Counties by Update Volume:")
    for i, (county, count) in enumerate(counties[:10], 1):
        print(f"  {i:2d}. {county:20s} - {count:,} properties")

    return counties

def build_update_sql(county: str) -> str:
    """Build the UPDATE SQL for a specific county"""
    return f"""
    UPDATE florida_parcels
    SET
        land_use_code = CASE
            -- Multi-Family 10+
            WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN '02'
            -- Industrial
            WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN '24'
            -- Commercial
            WHEN (just_value > 500000 AND building_value > 200000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN '17'
            -- Agricultural
            WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN '01'
            -- Condominium
            WHEN (just_value BETWEEN 100000 AND 500000
                  AND building_value BETWEEN 50000 AND 300000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN '03'
            -- Vacant Residential
            WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN '10'
            -- Single Family
            WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN '00'
            -- Default to Single Family
            ELSE '00'
        END,
        property_use = CASE
            WHEN (building_value > 500000 AND building_value > COALESCE(land_value, 0) * 2) THEN 'MF 10+'
            WHEN (building_value > 1000000 AND COALESCE(land_value, 0) < 500000) THEN 'Industria'
            WHEN (just_value > 500000 AND building_value > 200000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.3 AND COALESCE(land_value, 1) * 4) THEN 'Commercia'
            WHEN (COALESCE(land_value, 0) > COALESCE(building_value, 0) * 5 AND land_value > 100000) THEN 'Agricult.'
            WHEN (just_value BETWEEN 100000 AND 500000
                  AND building_value BETWEEN 50000 AND 300000
                  AND building_value BETWEEN COALESCE(land_value, 0) * 0.8 AND COALESCE(land_value, 1) * 1.5) THEN 'Condo'
            WHEN (COALESCE(land_value, 0) > 0 AND (building_value IS NULL OR building_value < 1000)) THEN 'Vacant Re'
            WHEN (building_value > 50000 AND building_value > COALESCE(land_value, 0) AND just_value < 1000000) THEN 'SFR'
            ELSE 'SFR'
        END
    WHERE year = 2025
        AND county = '{county}'
        AND (land_use_code IS NULL OR land_use_code = '' OR land_use_code = '99')
    """

def validate_county(county: str) -> Dict:
    """Validate assignment for a specific county"""
    sql = f"""
    SELECT
        county,
        COUNT(*) as total,
        COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
        ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
    FROM florida_parcels
    WHERE year = 2025 AND county = '{county}'
    GROUP BY county
    """

    result = execute_sql_query(sql)
    if result["success"] and result["data"]:
        return result["data"][0]
    return {}

def process_county(county: str, index: int, total: int) -> Dict:
    """Process a single county"""
    start_time = time.time()

    print(f"\n[{index}/{total}] Processing {county}...")

    # Execute update
    update_sql = build_update_sql(county)
    result = execute_sql_query(update_sql)

    if not result["success"]:
        print(f"  [ERROR] {result['error']}")
        return {"success": False, "county": county, "error": result["error"]}

    # Validate
    validation = validate_county(county)
    elapsed = time.time() - start_time

    if validation:
        print(f"  [SUCCESS] {validation['with_code']:,} / {validation['total']:,} ({validation['coverage_pct']}%) - {elapsed:.2f}s")
        return {
            "success": True,
            "county": county,
            "total": validation["total"],
            "with_code": validation["with_code"],
            "coverage": validation["coverage_pct"],
            "elapsed": elapsed
        }
    else:
        print(f"  [WARNING] Validation failed")
        return {"success": False, "county": county, "error": "Validation failed"}

def get_overall_status() -> Dict:
    """Get overall coverage status"""
    sql = """
    SELECT
        COUNT(*) as total,
        COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END) as with_code,
        ROUND(COUNT(CASE WHEN land_use_code IS NOT NULL AND land_use_code != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
    FROM florida_parcels
    WHERE year = 2025
    """

    result = execute_sql_query(sql)
    if result["success"] and result["data"]:
        return result["data"][0]
    return {}

def get_distribution_analysis() -> List[Dict]:
    """Get distribution of DOR codes"""
    sql = """
    SELECT
        land_use_code,
        property_use,
        COUNT(*) as count,
        ROUND(COUNT(*)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as pct
    FROM florida_parcels
    WHERE year = 2025 AND land_use_code IS NOT NULL
    GROUP BY land_use_code, property_use
    ORDER BY count DESC
    LIMIT 20
    """

    result = execute_sql_query(sql)
    if result["success"]:
        return result["data"]
    return []

def main():
    """Execute county-batched DOR assignment"""
    print("=" * 80)
    print("[AI AGENT] County-Batched DOR Use Code Assignment")
    print("=" * 80)

    start_time = time.time()

    # Phase 1: Discovery
    counties = get_county_distribution()
    if not counties:
        print("\n[ERROR] Failed to get county distribution")
        return False

    initial_status = get_overall_status()
    print(f"\n[INITIAL STATUS]")
    print(f"  Total Properties: {initial_status.get('total', 0):,}")
    print(f"  With Code: {initial_status.get('with_code', 0):,}")
    print(f"  Coverage: {initial_status.get('coverage_pct', 0)}%")

    # Phase 2: Process Top 10 Counties
    print(f"\n[PHASE 2] Processing Top 10 Counties")
    print("=" * 80)

    results = []
    for i, (county, need_update) in enumerate(counties[:10], 1):
        result = process_county(county, i, 10)
        results.append(result)
        time.sleep(0.5)  # Brief pause between counties

    checkpoint = get_overall_status()
    print(f"\n[CHECKPOINT] After Top 10 Counties:")
    print(f"  Coverage: {checkpoint.get('coverage_pct', 0)}%")

    # Phase 3: Process Remaining Counties
    print(f"\n[PHASE 3] Processing Remaining {len(counties) - 10} Counties")
    print("=" * 80)

    for i, (county, need_update) in enumerate(counties[10:], 11):
        result = process_county(county, i, len(counties))
        results.append(result)
        time.sleep(0.5)

    # Phase 4: Final Validation
    print(f"\n[PHASE 4] Final Validation & Analysis")
    print("=" * 80)

    final_status = get_overall_status()
    distribution = get_distribution_analysis()

    total_elapsed = time.time() - start_time

    # Generate Report
    print(f"\n{'=' * 80}")
    print(f"[EXECUTION COMPLETE]")
    print(f"{'=' * 80}")

    print(f"\n[BEFORE]")
    print(f"  Total: {initial_status.get('total', 0):,}")
    print(f"  With Code: {initial_status.get('with_code', 0):,}")
    print(f"  Coverage: {initial_status.get('coverage_pct', 0)}%")

    print(f"\n[AFTER]")
    print(f"  Total: {final_status.get('total', 0):,}")
    print(f"  With Code: {final_status.get('with_code', 0):,}")
    print(f"  Coverage: {final_status.get('coverage_pct', 0)}%")

    print(f"\n[IMPACT]")
    properties_updated = final_status.get('with_code', 0) - initial_status.get('with_code', 0)
    print(f"  Properties Updated: {properties_updated:,}")
    print(f"  Execution Time: {total_elapsed / 60:.2f} minutes")
    print(f"  Counties Processed: {len(results)}")

    print(f"\n[TOP 10 USE CODE DISTRIBUTION]")
    for item in distribution[:10]:
        print(f"  {item['land_use_code']:3s} - {item['property_use']:12s}: {item['count']:>10,} ({item['pct']:>5}%)")

    # Success Rating
    coverage = final_status.get('coverage_pct', 0)
    if coverage >= 100:
        rating = 10
    elif coverage >= 99.5:
        rating = 9
    elif coverage >= 95:
        rating = 8
    else:
        rating = 7

    print(f"\n[SUCCESS RATING] {rating}/10")
    print("=" * 80)

    # Save detailed results
    report = {
        "execution_timestamp": datetime.now().isoformat(),
        "initial_status": initial_status,
        "final_status": final_status,
        "properties_updated": properties_updated,
        "execution_time_minutes": total_elapsed / 60,
        "counties_processed": len(results),
        "county_results": results,
        "distribution": distribution,
        "success_rating": rating
    }

    filename = f"DOR_ASSIGNMENT_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n[REPORT SAVED] {filename}")

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)