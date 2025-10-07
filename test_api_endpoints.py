#!/usr/bin/env python3
"""
API Endpoints Test Script
=========================
Quick test of the FastAPI endpoints to verify functionality
"""

import requests
import json
from datetime import datetime

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8001"

    endpoints = [
        "/health",
        "/database/tables", 
        "/database/sales-tables",
        "/florida-parcels/stats",
        "/florida-parcels/counties",
        "/florida-parcels/completeness",
        "/property/1078130000370",
        "/property/504231242730"
    ]

    print("Testing FastAPI Endpoints")
    print("=" * 40)
    print(f"Base URL: {base_url}")
    print(f"Test Time: {datetime.now()}")
    print()

    for endpoint in endpoints:
        try:
            print(f"Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=30)

            if response.status_code == 200:
                data = response.json()
                print(f"  SUCCESS - Response size: {len(json.dumps(data))} chars")
            else:
                print(f"  FAILED - Status: {response.status_code}")

        except Exception as e:
            print(f"  ERROR - {str(e)}")

        print()

    print("API endpoint testing completed!")

if __name__ == "__main__":
    test_api_endpoints()
