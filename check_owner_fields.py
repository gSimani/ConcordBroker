#!/usr/bin/env python3
"""
Check owner name fields in database tables
"""

import asyncio
import asyncpg
import json
from datetime import datetime

async def check_owner_fields():
    """Check owner name fields and data in Supabase"""

    print("🔍 CHECKING OWNER NAME FIELDS IN DATABASE")
    print("=" * 60)

    # Database connection
    conn_string = "postgresql://postgres.pmispwtdngkcmsrsjwbp:vM4g2024$$Florida1@aws-0-us-east-1.pooler.supabase.com:6543/postgres"

    try:
        conn = await asyncpg.connect(conn_string)
        print("✅ Connected to Supabase database")

        # 1. Check florida_parcels schema for owner fields
        print("\n📋 FLORIDA_PARCELS TABLE SCHEMA:")
        print("-" * 40)

        schema_query = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'florida_parcels'
        AND column_name ILIKE '%own%'
        ORDER BY ordinal_position;
        """

        owner_columns = await conn.fetch(schema_query)

        if owner_columns:
            print("Found owner-related columns:")
            for col in owner_columns:
                print(f"  • {col['column_name']} ({col['data_type']}) - Nullable: {col['is_nullable']}")
        else:
            print("❌ No owner-related columns found in florida_parcels")

        # 2. Check actual data in owner fields
        print("\n📊 OWNER DATA SAMPLES:")
        print("-" * 40)

        # Check different owner field variations
        owner_field_checks = [
            "owner_name", "own_name", "owner", "ownr_name",
            "taxpayer_name", "tax_name", "owner1", "owner_1"
        ]

        existing_owner_fields = []

        for field in owner_field_checks:
            try:
                check_query = f"""
                SELECT '{field}' as field_name,
                       COUNT(*) as total_records,
                       COUNT({field}) as non_null_records,
                       COUNT(CASE WHEN {field} != '' THEN 1 END) as non_empty_records
                FROM florida_parcels
                WHERE {field} IS NOT NULL
                LIMIT 1;
                """
                result = await conn.fetchrow(check_query)
                if result:
                    existing_owner_fields.append(field)
                    print(f"✅ {field}: {result['non_null_records']:,} non-null records")
            except Exception as e:
                # Field doesn't exist
                pass

        if not existing_owner_fields:
            print("❌ No owner name fields found in florida_parcels table")

            # Check all columns to see what we have
            print("\n📋 ALL COLUMNS IN FLORIDA_PARCELS:")
            all_columns_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'florida_parcels'
            ORDER BY ordinal_position;
            """
            all_columns = await conn.fetch(all_columns_query)
            for i, col in enumerate(all_columns):
                print(f"  {i+1:2d}. {col['column_name']}")

        # 3. Sample actual owner data
        if existing_owner_fields:
            print(f"\n📝 SAMPLE OWNER DATA:")
            print("-" * 40)

            for field in existing_owner_fields[:3]:  # Check top 3 fields
                sample_query = f"""
                SELECT parcel_id, county, {field}
                FROM florida_parcels
                WHERE {field} IS NOT NULL
                AND {field} != ''
                LIMIT 5;
                """

                samples = await conn.fetch(sample_query)
                print(f"\n{field.upper()} samples:")
                for sample in samples:
                    print(f"  {sample['parcel_id']} ({sample['county']}): {sample[field]}")

        # 4. Check if there are any other tables with owner data
        print(f"\n🔍 OTHER TABLES WITH OWNER DATA:")
        print("-" * 40)

        tables_query = """
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE column_name ILIKE '%own%'
        AND table_schema = 'public'
        ORDER BY table_name;
        """

        owner_tables = await conn.fetch(tables_query)
        for table in owner_tables:
            table_name = table['table_name']
            print(f"📊 {table_name}")

            # Get owner columns for this table
            table_owner_cols = await conn.fetch(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            AND column_name ILIKE '%own%'
            ORDER BY ordinal_position;
            """)

            for col in table_owner_cols:
                print(f"  • {col['column_name']}")

        # 5. Check Property Appraiser raw data structure
        print(f"\n🏠 PROPERTY APPRAISER DATA STRUCTURE:")
        print("-" * 40)

        # Check for original property appraiser fields
        original_fields = [
            "own_name", "ownr_name", "owner_name", "taxpayer",
            "own_addr1", "own_addr2", "own_city", "own_state", "own_zipcd"
        ]

        for field in original_fields:
            try:
                count_query = f"""
                SELECT COUNT(*) as count
                FROM florida_parcels
                WHERE {field} IS NOT NULL;
                """
                result = await conn.fetchrow(count_query)
                print(f"  {field}: {result['count']:,} records")
            except:
                print(f"  {field}: Column not found")

        await conn.close()
        print("\n✅ Database check completed")

    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_owner_fields())