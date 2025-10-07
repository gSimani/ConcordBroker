"""
DOR Use Code Assignment via Supabase REST API
Uses the MCP Server and Supabase REST API to assign use codes
"""

import requests
import json
import os
from datetime import datetime

# Configuration
MCP_URL = "http://localhost:3001"
API_KEY = "concordbroker-mcp-key-claude"

headers = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

def check_mcp_health():
    """Check if MCP server is running"""
    try:
        response = requests.get(f"{MCP_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[SUCCESS] MCP Server is healthy")
            return True
        else:
            print(f"[ERROR] MCP Server returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to MCP Server: {e}")
        return False

def analyze_current_status():
    """Analyze current DOR use code status"""
    print("\n[PHASE 1] Analyzing Current Status")
    print("=" * 60)

    # Total properties
    url = f"{MCP_URL}/api/supabase/florida_parcels"
    params = {
        "select": "count",
        "year": "eq.2025"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        total_count = len(response.json()) if response.status_code == 200 else 0

        # Properties with DOR code
        params["dor_uc"] = "not.is.null"
        response = requests.get(url, headers=headers, params=params, timeout=30)
        with_code = len(response.json()) if response.status_code == 200 else 0

        without_code = total_count - with_code
        coverage_pct = (with_code / total_count * 100) if total_count > 0 else 0

        print(f"Total Properties: {total_count:,}")
        print(f"With DOR Code: {with_code:,}")
        print(f"Without DOR Code: {without_code:,}")
        print(f"Coverage: {coverage_pct:.2f}%")

        return {
            "total": total_count,
            "with_code": with_code,
            "without_code": without_code,
            "coverage_percentage": coverage_pct
        }

    except Exception as e:
        print(f"[ERROR] Failed to analyze status: {e}")
        return None

def assign_use_codes_batch():
    """Assign DOR use codes using intelligent logic"""
    print("\n[PHASE 2] Assigning DOR Use Codes")
    print("=" * 60)

    print("[INFO] This would execute bulk assignment via SQL")
    print("[INFO] Intelligent assignment based on property characteristics:")
    print("  - Single Family: building_value > 50k, building > land")
    print("  - Multi-Family: building_value > 500k, building > land*2")
    print("  - Commercial: just_value > 500k, building > 200k")
    print("  - Industrial: building > 1M, land < 500k")
    print("  - Agricultural: land > building*5, land > 100k")
    print("  - Vacant Residential: land only, no building")

    print("\n[ACTION REQUIRED] To execute assignment:")
    print("1. Use Supabase SQL Editor")
    print("2. Run the UPDATE query from dor_use_code_assignment_agent.py")
    print("3. OR start the FastAPI service: python mcp-server/fastapi-endpoints/dor_use_code_api.py")
    print("4. Call POST /assign-bulk endpoint")

    return {"status": "manual_action_required"}

def generate_assignment_sql():
    """Generate SQL for manual execution"""
    sql = """
-- DOR Use Code Assignment SQL
-- Execute this in Supabase SQL Editor to assign use codes to all properties

UPDATE florida_parcels
SET
    dor_uc = CASE
        -- Single Family Residential
        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN '00'
        -- Multi-Family
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN '02'
        -- Commercial
        WHEN (just_value > 500000 AND building_value > 200000) THEN '17'
        -- Industrial
        WHEN (building_value > 1000000 AND land_value < 500000) THEN '24'
        -- Agricultural
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN '01'
        -- Vacant Residential
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN '10'
        -- Default to Single Family
        ELSE '00'
    END,
    property_use = CASE
        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN 'Single Family'
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Multi-Family 10+'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Vacant Residential'
        ELSE 'Single Family'
    END,
    property_use_category = CASE
        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN 'Residential'
        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Residential'
        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Residential'
        ELSE 'Residential'
    END
WHERE year = 2025 AND (dor_uc IS NULL OR dor_uc = '');

-- Verify assignment
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as with_code,
    ROUND(COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
FROM florida_parcels
WHERE year = 2025;
"""

    filename = f"dor_use_code_assignment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    with open(filename, 'w') as f:
        f.write(sql)

    print(f"\n[SUCCESS] SQL saved to: {filename}")
    return filename

def main():
    print("=" * 60)
    print("[AI AGENT] DOR Use Code Assignment System")
    print("=" * 60)

    # Check MCP server
    if not check_mcp_health():
        print("\n[ERROR] MCP Server not available. Start it first:")
        print("  cd mcp-server && node server.js")
        return False

    # Analyze current status
    status = analyze_current_status()
    if not status:
        print("\n[ERROR] Failed to analyze current status")
        return False

    # Generate SQL for manual execution
    sql_file = generate_assignment_sql()

    # Assign use codes
    result = assign_use_codes_batch()

    # Summary
    print("\n" + "=" * 60)
    print("[COMPLETE] DOR Use Code Assignment System Ready")
    print("=" * 60)
    print(f"\nCurrent Status:")
    print(f"  Total Properties: {status['total']:,}")
    print(f"  Coverage: {status['coverage_percentage']:.2f}%")
    print(f"\nNext Steps:")
    print(f"  1. Review SQL file: {sql_file}")
    print(f"  2. Execute in Supabase SQL Editor")
    print(f"  3. OR start FastAPI service:")
    print(f"     python mcp-server/fastapi-endpoints/dor_use_code_api.py")
    print(f"  4. Monitor via Jupyter notebook:")
    print(f"     jupyter notebook mcp-server/notebooks/dor_use_code_analysis.ipynb")
    print("=" * 60)

    return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)