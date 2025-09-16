#!/usr/bin/env python3
"""Check columns in florida_parcels table"""

import psycopg2
import psycopg2.extras

conn = psycopg2.connect(
    host="aws-1-us-east-1.pooler.supabase.com",
    port=6543,
    database="postgres",
    user="postgres.pmispwtdngkcmsrsjwbp",
    password="West@Boca613!",
    connect_timeout=10
)

cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Get column information
cursor.execute("""
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
        AND table_name = 'florida_parcels'
    ORDER BY ordinal_position
""")

columns = cursor.fetchall()

print("Columns in florida_parcels table:")
print("-" * 50)

for col in columns:
    print(f"  {col['column_name']:30} {col['data_type']:20} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")

print(f"\nTotal columns: {len(columns)}")

cursor.close()
conn.close()