#!/usr/bin/env python3
"""
Diagnose schema visibility issue
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

# Connect using pooler
conn = psycopg2.connect(
    host='aws-1-us-east-1.pooler.supabase.com',
    port=5432,
    database='postgres',
    user='postgres.pmispwtdngkcmsrsjwbp',
    password='West@Boca613!',
    sslmode='require'
)
cur = conn.cursor()

print("="*70)
print("SCHEMA VISIBILITY DIAGNOSTIC")
print("="*70)

# 1. Check current database and user
cur.execute("SELECT current_database(), current_user, current_schema(), version()")
result = cur.fetchone()
print(f"\nDatabase: {result[0]}")
print(f"User: {result[1]}")
print(f"Current Schema: {result[2]}")
print(f"Version: {result[3][:50]}...")

# 2. Check search path
cur.execute("SHOW search_path")
result = cur.fetchone()
print(f"\nSearch Path: {result[0]}")

# 3. Check if tables exist in any schema
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_name IN ('property_assessments', 'property_owners', 'property_sales')
    ORDER BY table_schema, table_name
""")
results = cur.fetchall()
print(f"\nTables found in schemas:")
for schema, table in results:
    print(f"  {schema}.{table}")

# 4. Check public schema specifically
cur.execute("""
    SELECT tablename 
    FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename LIKE 'property%'
    ORDER BY tablename
""")
results = cur.fetchall()
print(f"\nPublic schema property tables:")
for (table,) in results:
    print(f"  public.{table}")

# 5. Try setting search path
print("\n" + "="*70)
print("TESTING SEARCH PATH FIX")
print("="*70)

cur.execute("SET search_path TO public, '$user'")
print("Set search_path to: public, '$user'")

# 6. Check if table is now visible
try:
    cur.execute("SELECT COUNT(*) FROM property_assessments")
    count = cur.fetchone()[0]
    print(f"✅ SUCCESS: property_assessments is now visible! Count: {count}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# 7. Try with schema qualification
try:
    cur.execute("SELECT COUNT(*) FROM public.property_assessments")
    count = cur.fetchone()[0]
    print(f"✅ WITH SCHEMA: public.property_assessments works! Count: {count}")
except Exception as e:
    print(f"❌ WITH SCHEMA FAILED: {e}")

cur.close()
conn.close()

print("\n" + "="*70)
print("SOLUTION: Add 'SET search_path TO public' after connecting")
print("OR: Use 'public.property_assessments' in all queries")
print("="*70)