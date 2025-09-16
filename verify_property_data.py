#!/usr/bin/env python3
"""
Verify Property Data Upload to Supabase
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
cur = conn.cursor()

print("="*70)
print("PROPERTY DATA VERIFICATION REPORT")
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# 1. Check record counts per table
print("\n1. RECORD COUNTS BY TABLE:")
print("-"*40)

tables = [
    'property_assessments',
    'property_owners',
    'property_sales',
    'nav_summaries',
    'nav_details',
    'properties_master'
]

for table in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM public.{table}")
        count = cur.fetchone()[0]
        print(f"   {table:25} {count:>10,} records")
    except Exception as e:
        print(f"   {table:25} Error: {str(e)[:30]}")

# 2. Check counties loaded
print("\n2. COUNTIES LOADED (property_assessments):")
print("-"*40)

cur.execute("""
    SELECT county_name, county_code, COUNT(*) as records
    FROM public.property_assessments
    GROUP BY county_name, county_code
    ORDER BY county_name
""")

counties = cur.fetchall()
print(f"   Total Counties: {len(counties)}")
for county_name, county_code, count in counties[:10]:
    print(f"   {county_name:20} (Code: {county_code:2}) - {count:>8,} properties")
if len(counties) > 10:
    print(f"   ... and {len(counties) - 10} more counties")

# 3. Sample property data
print("\n3. SAMPLE PROPERTY DATA:")
print("-"*40)

cur.execute("""
    SELECT parcel_id, owner_name, property_address, 
           property_city, taxable_value
    FROM public.property_assessments
    WHERE taxable_value > 0
    ORDER BY taxable_value DESC
    LIMIT 5
""")

properties = cur.fetchall()
for parcel_id, owner, address, city, value in properties:
    print(f"\n   Parcel: {parcel_id}")
    print(f"   Owner:  {owner[:50] if owner else 'N/A'}")
    print(f"   Addr:   {address[:50] if address else 'N/A'}, {city}")
    print(f"   Value:  ${value:,.0f}")

# 4. Data quality check
print("\n4. DATA QUALITY METRICS:")
print("-"*40)

cur.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(DISTINCT parcel_id) as unique_parcels,
        COUNT(owner_name) as has_owner,
        COUNT(property_address) as has_address,
        COUNT(CASE WHEN taxable_value > 0 THEN 1 END) as has_value
    FROM public.property_assessments
""")

total, unique_parcels, has_owner, has_address, has_value = cur.fetchone()
print(f"   Total Records:        {total:>10,}")
print(f"   Unique Parcels:       {unique_parcels:>10,}")
print(f"   With Owner Name:      {has_owner:>10,} ({100*has_owner/total:.1f}%)")
print(f"   With Address:         {has_address:>10,} ({100*has_address/total:.1f}%)")
print(f"   With Value > 0:       {has_value:>10,} ({100*has_value/total:.1f}%)")

# 5. Value distribution
print("\n5. PROPERTY VALUE DISTRIBUTION:")
print("-"*40)

cur.execute("""
    SELECT 
        COUNT(CASE WHEN taxable_value < 100000 THEN 1 END) as under_100k,
        COUNT(CASE WHEN taxable_value BETWEEN 100000 AND 250000 THEN 1 END) as range_100_250k,
        COUNT(CASE WHEN taxable_value BETWEEN 250000 AND 500000 THEN 1 END) as range_250_500k,
        COUNT(CASE WHEN taxable_value BETWEEN 500000 AND 1000000 THEN 1 END) as range_500k_1m,
        COUNT(CASE WHEN taxable_value > 1000000 THEN 1 END) as over_1m
    FROM public.property_assessments
    WHERE taxable_value > 0
""")

under_100k, range_100_250k, range_250_500k, range_500k_1m, over_1m = cur.fetchone()
print(f"   Under $100K:          {under_100k:>10,}")
print(f"   $100K - $250K:        {range_100_250k:>10,}")
print(f"   $250K - $500K:        {range_250_500k:>10,}")
print(f"   $500K - $1M:          {range_500k_1m:>10,}")
print(f"   Over $1M:             {over_1m:>10,}")

cur.close()
conn.close()

print("\n" + "="*70)
print("VERIFICATION COMPLETE!")
print("Data is successfully loaded and accessible via SQL")
print("="*70)
