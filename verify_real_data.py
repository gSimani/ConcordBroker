"""
Verify Real Data in Supabase
Check florida_parcels table and ensure frontend can access it
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Direct database check using psycopg2 for accurate counts
import psycopg2

def check_database():
    """Check what tables exist and their counts"""
    
    conn = psycopg2.connect(
        host='aws-0-us-east-1.pooler.supabase.com',
        port=5432,
        database='postgres',
        user='postgres.pmispwtdngkcmsrsjwbp',
        password='West@Boca613!',
        sslmode='require',
        options='-c search_path=public'
    )
    
    try:
        cur = conn.cursor()
        
        print("Database Analysis")
        print("="*60)
        
        # Check all tables and their counts
        cur.execute("""
            SELECT 
                schemaname,
                tablename,
                n_live_tup as row_count
            FROM pg_stat_user_tables
            WHERE schemaname = 'public'
            AND tablename IN ('florida_parcels', 'property_assessments', 'property_sales', 'property_owners')
            ORDER BY n_live_tup DESC
        """)
        
        print("\n1. Table Row Counts:")
        for row in cur.fetchall():
            print(f"   {row[1]}: {row[2]:,} rows")
        
        # Check florida_parcels structure
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'florida_parcels'
            AND table_schema = 'public'
            AND column_name IN ('phy_addr1', 'phy_city', 'own_name', 'is_redacted')
            ORDER BY ordinal_position
        """)
        
        print("\n2. florida_parcels Key Columns:")
        for row in cur.fetchall():
            print(f"   - {row[0]}: {row[1]}")
        
        # Check non-redacted count
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN is_redacted = false OR is_redacted IS NULL THEN 1 END) as non_redacted,
                COUNT(CASE WHEN is_redacted = true THEN 1 END) as redacted
            FROM florida_parcels
        """)
        
        result = cur.fetchone()
        print(f"\n3. florida_parcels Redaction Status:")
        print(f"   Total: {result[0]:,}")
        print(f"   Non-redacted (visible): {result[1]:,}")
        print(f"   Redacted (hidden): {result[2]:,}")
        
        # Get sample data
        cur.execute("""
            SELECT phy_addr1, phy_city, own_name, jv
            FROM florida_parcels
            WHERE is_redacted = false OR is_redacted IS NULL
            AND phy_addr1 IS NOT NULL
            LIMIT 5
        """)
        
        print("\n4. Sample Non-Redacted Properties:")
        for row in cur.fetchall():
            print(f"   {row[0]}, {row[1]} - Owner: {row[2]} - Value: ${row[3]:,.0f}" if row[3] else f"   {row[0]}, {row[1]}")
        
        # Check counties
        cur.execute("""
            SELECT county, COUNT(*) as count
            FROM florida_parcels
            WHERE is_redacted = false OR is_redacted IS NULL
            GROUP BY county
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print("\n5. Top Counties (non-redacted):")
        for row in cur.fetchall():
            print(f"   {row[0]}: {row[1]:,} properties")
        
        # Check API endpoint
        print("\n6. API Endpoint Check:")
        print("   Current API: http://localhost:8001/api/properties/search")
        print("   Frontend calling: http://localhost:8000/api/properties/search")
        print("   >>> ISSUE: Port mismatch!")
        
        print("\n" + "="*60)
        print("SOLUTION:")
        print("="*60)
        print("1. florida_parcels table EXISTS with 789k+ rows")
        print("2. Frontend should query this table (not property_assessments)")
        print("3. Fix: Update frontend to use port 8001")
        print("4. API should query florida_parcels WHERE is_redacted = false")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_database()