#!/usr/bin/env python3
"""
Discover all actual tables in Supabase database
"""

import psycopg2
import os

# Database connection
conn = psycopg2.connect(
    host="db.pmispwtdngkcmsrsjwbp.supabase.co",
    database="postgres",
    user="postgres",
    password="West@Boca613!",
    port="5432",
    sslmode="require"
)

cursor = conn.cursor()

# Query to get all tables in public schema
cursor.execute("""
    SELECT
        table_name,
        (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema='public' AND table_name=t.table_name) as column_count
    FROM information_schema.tables t
    WHERE table_schema='public'
    AND table_type='BASE TABLE'
    ORDER BY table_name;
""")

tables = cursor.fetchall()

print("\n=== ALL TABLES IN SUPABASE ===\n")
for table, col_count in tables:
    print(f"{table:<40} ({col_count} columns)")

# Get row counts for key tables
print("\n=== TABLE ROW COUNTS ===\n")
key_tables = [
    'florida_parcels',
    'fl_parcels',
    'parcels',
    'property_sales_history',
    'sunbiz_corporate',
    'florida_entities',
    'fl_entities',
    'tax_certificates',
    'fl_sdf_sales',
    'sdf_sales',
    'owner_identities',
    'property_ownership'
]

for table in key_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table:<40} {count:,} rows")
    except Exception as e:
        print(f"{table:<40} [NOT FOUND]")

cursor.close()
conn.close()
