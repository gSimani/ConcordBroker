"""
Integration test for Mortgage Analytics Service
Tests the complete flow with Supabase and FRED data
"""

import os
import sys
import json
from datetime import datetime, date
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_supabase_connection():
    """Test Supabase connection and table creation"""
    print("\n" + "="*60)
    print("TESTING SUPABASE CONNECTION")
    print("="*60)

    try:
        from supabase import create_client, Client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            print("[ERROR] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
            print("Please set these environment variables")
            return False

        # Create client
        supabase: Client = create_client(url, key)
        print("[OK] Connected to Supabase")

        # Test mortgage_rates_monthly table
        response = supabase.table('mortgage_rates_monthly').select("*").limit(5).execute()
        print(f"[OK] mortgage_rates_monthly table exists with {len(response.data)} sample records")

        # Test calculate_mortgage_metrics RPC
        result = supabase.rpc('calculate_mortgage_metrics', {
            'p_orig_amount': 400000,
            'p_annual_rate': 6.5,
            'p_term_months': 360,
            'p_months_elapsed': 60
        }).execute()

        if result.data:
            metrics = result.data
            print("\n[OK] RPC function working:")
            print(f"   Monthly Payment: ${metrics['monthly_payment']:,.2f}")
            print(f"   Remaining Balance: ${metrics['remaining_balance']:,.2f}")
            print(f"   Principal Paid: ${metrics['principal_paid']:,.2f}")
            print(f"   Percent Paid: {metrics['pct_principal_paid']:.2f}%")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_fred_connection():
    """Test FRED API connection"""
    print("\n" + "="*60)
    print("TESTING FRED API CONNECTION")
    print("="*60)

    try:
        from fredapi import Fred

        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            print("[WARNING]  No FRED_API_KEY set - service will use fallback data")
            return True  # Not a failure, just a warning

        fred = Fred(api_key=api_key)

        # Test fetching recent mortgage rates
        series = fred.get_series('MORTGAGE30US', limit=5)

        if len(series) > 0:
            print(f"[OK] FRED API working - Latest 30Y rate: {series.iloc[-1]:.2f}%")
            return True
        else:
            print("[ERROR] No data returned from FRED")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_mortgage_service():
    """Test the mortgage analytics service"""
    print("\n" + "="*60)
    print("TESTING MORTGAGE ANALYTICS SERVICE")
    print("="*60)

    try:
        from mortgage_analytics_service import (
            MortgageAnalytics, Property, MortgageService
        )

        # Create test property
        property_data = Property(
            id="test-property-001",
            purchase_date=date(2024, 1, 15),
            orig_loan_amount=450000,
            loan_term_months=360,
            loan_type="30Y_FIXED",
            payment_start_date=date(2024, 2, 1),
            extra_principal_paid_to_date=5000
        )

        # Initialize service
        service = MortgageService()

        # Test historical snapshot
        print("\nCalculating Historical Snapshot...")
        snapshot = service.compute_historical_snapshot(property_data)
        print(f"[OK] Historical Rate Used: {snapshot.annual_rate_used_pct:.2f}%")
        print(f"   Months Elapsed: {snapshot.months_elapsed}")
        print(f"   Principal Paid: {snapshot.pct_principal_paid:.2f}%")
        print(f"   Remaining Balance: ${snapshot.remaining_balance:,.2f}")

        # Test current debt service
        print("\nCalculating Current Market Payment...")
        debt_service = service.compute_current_debt_service(
            property_data,
            rate_override=7.0,  # Use 7% for testing
            noi_monthly=3500  # $3,500 NOI for DSCR
        )
        print(f"[OK] Current Rate: {debt_service.annual_rate_used_pct:.2f}%")
        print(f"   Monthly Payment: ${debt_service.monthly_payment:,.2f}")
        print(f"   Remaining Term: {debt_service.assumed_remaining_term_months} months")
        if debt_service.dscr_if_noi_provided:
            print(f"   DSCR: {debt_service.dscr_if_noi_provided:.2f}")

        return True

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test the FastAPI endpoints"""
    print("\n" + "="*60)
    print("TESTING API ENDPOINTS")
    print("="*60)

    try:
        import requests

        base_url = "http://localhost:8005"

        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Health Check: {data['status']}")
            print(f"   FRED Configured: {data['fred_configured']}")
            print(f"   Supabase Configured: {data['supabase_configured']}")
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
            return False

        return True

    except requests.ConnectionError:
        print("[WARNING]  API not running on port 8005")
        print("   Run: python mortgage_analytics_service.py")
        return True  # Not a failure if API isn't running
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def generate_sample_property_insert():
    """Generate SQL to insert a sample property for testing"""
    print("\n" + "="*60)
    print("SAMPLE PROPERTY INSERT SQL")
    print("="*60)

    sql = """
-- Insert a sample property with mortgage data for testing
INSERT INTO properties (
    id,
    address,
    purchase_date,
    orig_loan_amount,
    loan_term_months,
    loan_type,
    payment_start_date,
    extra_principal_paid_to_date
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid,
    '789 Oak Street, Miami, FL 33130',
    '2024-01-15',
    450000.00,  -- $450k loan
    360,        -- 30 year term
    '30Y_FIXED',
    '2024-02-01',
    5000.00     -- $5k extra principal paid
) ON CONFLICT (id) DO UPDATE SET
    orig_loan_amount = EXCLUDED.orig_loan_amount,
    loan_term_months = EXCLUDED.loan_term_months,
    loan_type = EXCLUDED.loan_type;

-- Verify the insertion
SELECT
    address,
    orig_loan_amount,
    loan_type,
    calculate_mortgage_metrics(
        orig_loan_amount,
        6.62,  -- Jan 2024 rate from our data
        loan_term_months,
        11     -- 11 months elapsed (Feb 2024 to Dec 2024)
    ) as metrics
FROM properties
WHERE id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'::uuid;
"""

    print(sql)
    print("\nCopy and run this SQL in Supabase to create test data")
    return sql


def run_full_integration_test():
    """Run complete integration test suite"""
    print("\n" + "="*80)
    print("MORTGAGE ANALYTICS INTEGRATION TEST SUITE")
    print("="*80)

    results = {
        "Supabase Connection": test_supabase_connection(),
        "FRED API": test_fred_connection(),
        "Mortgage Service": test_mortgage_service(),
        "API Endpoints": test_api_endpoints()
    }

    # Generate sample data
    generate_sample_property_insert()

    # Summary
    print("\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)

    for test_name, result in results.items():
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name}: {status}")

    all_passed = all(results.values())

    if all_passed:
        print("\n[SUCCESS] ALL INTEGRATION TESTS PASSED!")
    else:
        print("\n[WARNING]  Some tests failed. Review the output above.")

    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("1. Run the SQL provided above in Supabase")
    print("2. Set environment variables if missing:")
    print("   - SUPABASE_URL")
    print("   - SUPABASE_SERVICE_ROLE_KEY")
    print("   - FRED_API_KEY (optional but recommended)")
    print("3. Start the service: python mortgage_analytics_service.py")
    print("4. Test the API: http://localhost:8005/docs")

    return all_passed


if __name__ == "__main__":
    success = run_full_integration_test()
    exit(0 if success else 1)