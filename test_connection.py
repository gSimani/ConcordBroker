#!/usr/bin/env python3
"""Test Supabase connection"""

import psycopg2
import time

print("Testing Supabase connection...")

# Try different connection methods
connections = [
    {
        "name": "Pooler Connection",
        "host": "aws-1-us-east-1.pooler.supabase.com",
        "port": 6543,
        "database": "postgres",
        "user": "postgres.pmispwtdngkcmsrsjwbp",
        "password": "West@Boca613!"
    },
    {
        "name": "Direct Connection",
        "host": "db.pmispwtdngkcmsrsjwbp.supabase.co",
        "port": 5432,
        "database": "postgres",
        "user": "postgres",
        "password": "West@Boca613!"
    }
]

for conn_params in connections:
    print(f"\nTrying {conn_params['name']}...")
    try:
        start = time.time()
        conn = psycopg2.connect(
            host=conn_params['host'],
            port=conn_params['port'],
            database=conn_params['database'],
            user=conn_params['user'],
            password=conn_params['password'],
            connect_timeout=10
        )

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        count = cursor.fetchone()[0]

        print(f"[SUCCESS] Connected in {time.time() - start:.2f}s")
        print(f"  Found {count} tables in public schema")

        cursor.close()
        conn.close()
        break

    except Exception as e:
        print(f"[FAILED] {str(e)[:100]}")

print("\nDone.")