#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick audit of 2023 data upload status
"""
import psycopg2
from urllib.parse import urlparse
import os
import sys

# Ensure output encoding is UTF-8
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

# Get DATABASE_URL from environment (use non-pooling connection for stability)
db_url = os.getenv('POSTGRES_URL_NON_POOLING', 'postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require')

print("=" * 70)
print("2023 DATA UPLOAD STATUS AUDIT")
print("=" * 70)

try:
    # Connect to database
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Check 2023 NAL data
    print("\n[NAL DATA] florida_parcels table:")
    print("-" * 70)

    cur.execute("""
        SELECT
            COUNT(*) as total_rows,
            COUNT(DISTINCT county) as counties_count,
            MIN(import_date) as first_import,
            MAX(import_date) as last_import
        FROM public.florida_parcels
        WHERE year = 2023
    """)

    row = cur.fetchone()
    if row:
        print(f"  Total 2023 rows: {row[0]:,}")
        print(f"  Counties represented: {row[1]}")
        print(f"  First import: {row[2]}")
        print(f"  Last import: {row[3]}")

    # Count by county
    print("\n[COUNTIES] Rows per county:")
    cur.execute("""
        SELECT county, COUNT(*) as count
        FROM public.florida_parcels
        WHERE year = 2023
        GROUP BY county
        ORDER BY count DESC
        LIMIT 20
    """)

    counties = cur.fetchall()
    if counties:
        for county, count in counties:
            print(f"  {county:20s}: {count:>10,} rows")
        if len(counties) == 20:
            print(f"  ... and {row[1] - 20} more counties")
    else:
        print("  [WARNING] No 2023 NAL data found!")

    # Check progress table
    print("\n[PROGRESS] Tracking (ingestion_progress table):")
    print("-" * 70)

    cur.execute("""
        SELECT
            created_at,
            county,
            done,
            total,
            percent,
            current,
            run_id
        FROM public.ingestion_progress
        WHERE run_id LIKE '%2023%'
        ORDER BY created_at DESC
        LIMIT 5
    """)

    progress_rows = cur.fetchall()
    if progress_rows:
        print("  Last 5 progress entries:")
        for p in progress_rows:
            print(f"    {p[0]} | {p[1]:15s} | {p[2]:3d}/{p[3]:3d} ({p[4]:2d}%) | {p[5][:40]}")
    else:
        print("  [WARNING] No progress tracking entries found for 2023")

    # Check 2023 SDF data
    print("\n[SDF DATA] property_sales_history table:")
    print("-" * 70)

    cur.execute("""
        SELECT COUNT(*)
        FROM public.property_sales_history
        WHERE sale_year = 2023
    """)

    sdf_count = cur.fetchone()[0]
    print(f"  Total 2023 sales: {sdf_count:,}")
    if sdf_count == 0:
        print("  [INFO] No 2023 SDF data loaded yet")

    # Check 2023 NAP data
    print("\n[NAP DATA] tangible_personal_property table:")
    print("-" * 70)

    try:
        cur.execute("""
            SELECT COUNT(*)
            FROM public.florida_tangible_personal_property
            WHERE year = 2023
        """)

        nap_count = cur.fetchone()[0]
        print(f"  Total 2023 TPP records: {nap_count:,}")
        if nap_count == 0:
            print("  [INFO] No 2023 NAP data loaded yet")
    except:
        print("  [WARNING] Table may not exist yet")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY:")
    print("=" * 70)

    if row[0] == 0:
        print("[X] No 2023 NAL data found - Need to start/resume upload")
    elif row[0] < 1000000:
        print(f"[!] Partial 2023 NAL data ({row[0]:,} rows) - Upload in progress or stopped")
    else:
        print(f"[OK] Substantial 2023 NAL data present ({row[0]:,} rows)")

    if sdf_count == 0:
        print("[...] 2023 SDF data pending")
    else:
        print(f"[OK] 2023 SDF data loaded ({sdf_count:,} records)")

    # Estimate completion percentage
    # Assuming ~9.7M total properties for 2023
    if row[0] > 0:
        estimated_percent = (row[0] / 9700000) * 100
        print(f"\n[PROGRESS] Estimated completion: {estimated_percent:.1f}% of expected ~9.7M properties")

    cur.close()
    conn.close()

    print("\n" + "=" * 70)

except Exception as e:
    print(f"\n[ERROR] Database connection failed: {e}")
    print("   Make sure POSTGRES_URL_NON_POOLING is set correctly in .env")
