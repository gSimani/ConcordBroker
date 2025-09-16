#!/usr/bin/env python3
"""
Quick test to check if database is ready for localhost
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the api directory to path
sys.path.append(str(Path(__file__).parent / 'apps' / 'api'))

# Load environment
load_dotenv('.env.new')
if not os.path.exists('.env.new'):
    load_dotenv('.env')

print("=" * 50)
print("ConcordBroker Database Readiness Check")
print("=" * 50)
print()

# Check environment variables
env_vars = {
    'SUPABASE_URL': os.getenv('SUPABASE_URL'),
    'SUPABASE_SERVICE_ROLE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY'),
    'DATABASE_URL': os.getenv('DATABASE_URL')
}

print("1. Environment Variables:")
for key, value in env_vars.items():
    if value:
        masked = value[:20] + "..." if len(value) > 20 else value
        print(f"   [OK] {key}: {masked}")
    else:
        print(f"   [MISSING] {key}: NOT SET")

print()

# Test connection
print("2. Database Connection:")
try:
    from supabase_client import get_supabase_client
    client = get_supabase_client()
    print("   [OK] Connected to Supabase")
except Exception as e:
    print(f"   [FAIL] Connection failed: {e}")
    sys.exit(1)

print()

# Check tables
print("3. Database Tables:")
tables_to_check = [
    'florida_parcels',
    'florida_condo_units',
    'sunbiz_entities',
    'property_profiles'
]

existing_tables = []
missing_tables = []

for table in tables_to_check:
    try:
        result = client.table(table).select('count', count='exact').limit(1).execute()
        count = result.count if hasattr(result, 'count') else 0
        existing_tables.append(f"{table} ({count} records)")
        print(f"   [OK] {table}: {count} records")
    except Exception as e:
        missing_tables.append(table)
        print(f"   [FAIL] {table}: Does not exist")

print()

# Check data files
print("4. Data Files:")
data_files = {
    'NAP16P202501.csv': 'Parcel attributes',
    'SDF16P202501.csv': 'Sales data'
}

for file, description in data_files.items():
    if os.path.exists(file):
        size = os.path.getsize(file) / (1024 * 1024)  # MB
        print(f"   [OK] {file}: {description} ({size:.1f} MB)")
    else:
        print(f"   [FAIL] {file}: Not found")

print()
print("=" * 50)
print("Summary:")
print("=" * 50)

if all(env_vars.values()):
    print("[OK] Environment configured")
else:
    print("[FAIL] Environment variables missing")

if existing_tables:
    print(f"[OK] {len(existing_tables)} tables exist")
else:
    print("[FAIL] No tables found - run schema creation")

if missing_tables:
    print(f"[WARNING]  {len(missing_tables)} tables need to be created")
    print("   Run the SQL schema in Supabase dashboard")

print()
print("Next Steps:")
if missing_tables:
    print("1. Go to Supabase SQL Editor")
    print("2. Run the SQL from apps/api/supabase_schema.sql")
    print("3. Run: python setup_database.py")
else:
    print("1. Run: python setup_database.py (to load data)")
    print("2. Run: .\\start-localhost.ps1 (to start services)")

print()