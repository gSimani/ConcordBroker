"""
Verification script for Florida Data Automation deployment
"""
import requests
import json
from datetime import datetime
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://observant-purpose-concordbrokerproduction.up.railway.app"

print("=" * 80)
print("FLORIDA DATA AUTOMATION - DEPLOYMENT VERIFICATION")
print("=" * 80)
print()

# Test 1: Health Check
print("1. Testing Health Endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=10)
    if response.status_code == 200:
        print(f"   [OK] Health check passed: {response.json()}")
    else:
        print(f"   [FAIL] Health check failed: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

print()

# Test 2: Check Ingestion Status
print("2. Checking Ingestion Status...")
try:
    response = requests.get(f"{BASE_URL}/ingest/status", timeout=10)
    if response.status_code == 200:
        data = response.json()
        runs = data.get("recent_runs", [])
        print(f"   [OK] Total runs found: {len(runs)}")
        if runs:
            latest = runs[0]
            print(f"   Latest run:")
            print(f"      - ID: {latest['id']}")
            print(f"      - Timestamp: {latest['run_timestamp']}")
            print(f"      - Status: {latest['status']}")
            print(f"      - Rows inserted: {latest['rows_inserted']}")
            print(f"      - Rows updated: {latest['rows_updated']}")
    else:
        print(f"   [FAIL] Status check failed: {response.status_code}")
except Exception as e:
    print(f"   [ERROR] Error: {e}")

print()

# Test 3: Verify Cron Configuration
print("3. Cron Configuration (from railway.toml):")
print("   Schedule: 0 8 * * * (3 AM ET / 8 AM UTC daily)")
print("   Command: python florida_data_orchestrator.py sync")
print("   ⚠️  Verify this appears in Railway Dashboard → Settings → Cron")

print()

# Test 4: Next Steps
print("4. Next Steps:")
print("   - Verify cron job appears in Railway dashboard")
print("   - Monitor Railway logs for actual data downloads")
print("   - Check Supabase for data in staging/production tables")

print()
print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
