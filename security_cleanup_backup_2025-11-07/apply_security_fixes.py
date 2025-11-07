#!/usr/bin/env python3
"""
Apply Security Quick Wins to Supabase
"""

import psycopg2
from datetime import datetime

# Connect to Supabase
conn = psycopg2.connect(
    host='aws-1-us-east-1.pooler.supabase.com',
    port=5432,
    database='postgres',
    user='postgres.pmispwtdngkcmsrsjwbp',
    password='West@Boca613!',
    sslmode='require'
)
conn.autocommit = True
cur = conn.cursor()

print("="*70)
print("APPLYING SECURITY QUICK WINS")
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

fixes_applied = []
errors = []

# 1. Enable RLS on property_assessments
print("\n1. Enabling RLS on property_assessments...")
try:
    cur.execute("ALTER TABLE public.property_assessments ENABLE ROW LEVEL SECURITY")
    print("   [OK] RLS enabled on property_assessments")
    fixes_applied.append("RLS enabled on property_assessments")
except Exception as e:
    if "already enabled" in str(e).lower():
        print("   - RLS already enabled on property_assessments")
    else:
        print(f"   [ERROR] Error: {e}")
        errors.append(str(e))

# 2. Create public read policy for property_assessments
print("\n2. Creating public read policy for property_assessments...")
try:
    cur.execute("""
        CREATE POLICY "Public read assessments" 
        ON public.property_assessments 
        FOR SELECT 
        TO anon, authenticated 
        USING (true)
    """)
    print("   [OK] Public read policy created")
    fixes_applied.append("Public read policy created for property_assessments")
except Exception as e:
    if "already exists" in str(e).lower():
        print("   - Policy already exists")
    else:
        print(f"   [ERROR] Error: {e}")
        errors.append(str(e))

# 3. Enable RLS on florida_parcels
print("\n3. Enabling RLS on florida_parcels...")
try:
    cur.execute("ALTER TABLE public.florida_parcels ENABLE ROW LEVEL SECURITY")
    print("   [OK] RLS enabled on florida_parcels")
    fixes_applied.append("RLS enabled on florida_parcels")
except Exception as e:
    if "already enabled" in str(e).lower():
        print("   - RLS already enabled on florida_parcels")
    else:
        print(f"   [ERROR] Error: {e}")
        errors.append(str(e))

# 4. Enable RLS on florida_processing_log
print("\n4. Enabling RLS on florida_processing_log...")
try:
    cur.execute("ALTER TABLE public.florida_processing_log ENABLE ROW LEVEL SECURITY")
    print("   [OK] RLS enabled on florida_processing_log")
    fixes_applied.append("RLS enabled on florida_processing_log")
except Exception as e:
    if "already enabled" in str(e).lower():
        print("   - RLS already enabled on florida_processing_log")
    else:
        print(f"   [ERROR] Error: {e}")
        errors.append(str(e))

# 5. Add policies for tables without them
print("\n5. Adding policies for monitoring tables...")
tables_needing_policies = [
    ('monitoring_agents', 'Authenticated read monitoring_agents'),
    ('parcel_update_history', 'Authenticated read parcel_update_history')
]

for table, policy_name in tables_needing_policies:
    try:
        # Check if table exists
        cur.execute(f"""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = '{table}'
            )
        """)
        if cur.fetchone()[0]:
            # Create policy
            cur.execute(f"""
                CREATE POLICY "{policy_name}" 
                ON public.{table} 
                FOR SELECT 
                TO authenticated 
                USING (true)
            """)
            print(f"   [OK] Policy created for {table}")
            fixes_applied.append(f"Policy created for {table}")
    except Exception as e:
        if "already exists" in str(e).lower():
            print(f"   - Policy already exists for {table}")
        elif "does not exist" in str(e).lower():
            print(f"   - Table {table} does not exist")
        else:
            print(f"   ✗ Error on {table}: {e}")
            errors.append(str(e))

# Verify RLS status
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

cur.execute("""
    SELECT 
        tablename,
        rowsecurity
    FROM pg_tables
    WHERE schemaname = 'public'
    AND tablename IN (
        'property_assessments',
        'florida_parcels',
        'florida_processing_log',
        'monitoring_agents',
        'parcel_update_history'
    )
    ORDER BY tablename
""")

print("\nRLS Status:")
for table, rls_enabled in cur.fetchall():
    status = "[OK] ENABLED" if rls_enabled else "[X] DISABLED"
    print(f"  {table:30} {status}")

# Check policies
cur.execute("""
    SELECT 
        tablename,
        COUNT(*) as policy_count
    FROM pg_policies
    WHERE schemaname = 'public'
    AND tablename IN (
        'property_assessments',
        'florida_parcels',
        'florida_processing_log',
        'monitoring_agents',
        'parcel_update_history'
    )
    GROUP BY tablename
    ORDER BY tablename
""")

print("\nPolicy Count:")
for table, count in cur.fetchall():
    print(f"  {table:30} {count} policies")

cur.close()
conn.close()

print("\n" + "="*70)
print("SECURITY FIXES COMPLETE")
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Fixes Applied: {len(fixes_applied)}")
if errors:
    print(f"Errors: {len(errors)}")
print("="*70)