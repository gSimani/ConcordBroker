"""
Simple Supabase verification script
Tests what tables and functions exist
"""

import os
from supabase import create_client

def main():
    print("=" * 60)
    print("SUPABASE VERIFICATION")
    print("=" * 60)

    # Check environment
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not url or not key:
        print("[ERROR] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return

    print(f"URL: {url}")
    print(f"Key: {key[:20]}...")

    try:
        supabase = create_client(url, key)
        print("[OK] Connected to Supabase")

        # Test 1: Try to access mortgage_rates_monthly
        print("\n1. Testing mortgage_rates_monthly table...")
        try:
            result = supabase.table('mortgage_rates_monthly').select('*').limit(3).execute()
            print(f"   [OK] Found {len(result.data)} records")
            if result.data:
                print(f"   Sample: {result.data[0]}")
        except Exception as e:
            print(f"   [ERROR] {e}")

        # Test 2: Try to access loan_snapshots
        print("\n2. Testing loan_snapshots table...")
        try:
            result = supabase.table('loan_snapshots').select('*').limit(1).execute()
            print(f"   [OK] Table exists, {len(result.data)} records")
        except Exception as e:
            print(f"   [ERROR] {e}")

        # Test 3: Try the NEW working test function
        print("\n3. Testing mortgage_test_calc function...")
        try:
            result = supabase.rpc('mortgage_test_calc', {
                'loan_amount': 400000,
                'interest_rate': 6.5,
                'years_term': 30
            }).execute()
            print(f"   [OK] NEW function works: {result.data}")
            if result.data:
                print(f"   Monthly Payment: ${result.data.get('monthly_payment', 0):,.2f}")
                print(f"   Status: {result.data.get('test_status', 'unknown')}")
        except Exception as e:
            print(f"   [ERROR] New function failed: {e}")

        # Test 4: Try old function for comparison
        print("\n4. Testing old calculate_mortgage_metrics function...")
        try:
            result = supabase.rpc('calculate_mortgage_metrics', {
                'principal': 400000,
                'annual_rate': 6.5,
                'years': 30
            }).execute()
            print(f"   [OK] Old function works: {result.data}")
        except Exception as e:
            print(f"   [ERROR] Old function still failing: {e}")

        # Test 4: Try raw SQL query
        print("\n4. Testing raw SQL access...")
        try:
            # This tests if we can run any SQL at all
            result = supabase.rpc('exec', {
                'sql': 'SELECT current_database(), current_user;'
            }).execute()
            print(f"   [OK] Raw SQL works")
        except Exception as e:
            print(f"   [ERROR] Raw SQL failed: {e}")

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")

if __name__ == "__main__":
    main()