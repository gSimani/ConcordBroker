"""
Verify email data was loaded and create contact views
"""

import sys
import io
import psycopg2
from urllib.parse import urlparse
import json

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def verify_email_data():
    """Check officer emails and create views"""
    
    print("=" * 60)
    print("VERIFYING EMAIL DATA")
    print("=" * 60)
    
    # Database connection
    db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
    parsed = urlparse(db_url)
    conn_params = {
        'host': parsed.hostname,
        'port': parsed.port or 5432,
        'database': parsed.path.lstrip('/'),
        'user': parsed.username,
        'password': parsed.password.replace('%40', '@') if parsed.password else None,
        'sslmode': 'require'
    }
    
    try:
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Check officer data
        print("\n1. OFFICER DATA CHECK")
        print("-" * 40)
        
        cur.execute("SELECT COUNT(*) FROM sunbiz_officers")
        total_officers = cur.fetchone()[0]
        print(f"✅ Total officers: {total_officers:,}")
        
        cur.execute("SELECT COUNT(*) FROM sunbiz_officers WHERE officer_email IS NOT NULL")
        with_email = cur.fetchone()[0]
        print(f"📧 Officers with email: {with_email:,}")
        
        cur.execute("SELECT COUNT(*) FROM sunbiz_officers WHERE officer_phone IS NOT NULL")
        with_phone = cur.fetchone()[0]
        print(f"📞 Officers with phone: {with_phone:,}")
        
        # Sample emails
        print("\n2. SAMPLE EMAIL ADDRESSES")
        print("-" * 40)
        
        cur.execute("""
            SELECT officer_name, officer_email, officer_phone
            FROM sunbiz_officers
            WHERE officer_email IS NOT NULL
            LIMIT 10
        """)
        
        samples = cur.fetchall()
        for name, email, phone in samples:
            print(f"  {name}: {email} | {phone or 'No phone'}")
        
        # Check Sunbiz corporate table columns
        print("\n3. CHECKING SUNBIZ_CORPORATE COLUMNS")
        print("-" * 40)
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'sunbiz_corporate'
            ORDER BY ordinal_position
        """)
        
        columns = [row[0] for row in cur.fetchall()]
        print(f"Available columns: {', '.join(columns[:10])}...")
        
        # Create contact view with correct columns
        print("\n4. CREATING CONTACT VIEW")
        print("-" * 40)
        
        cur.execute("DROP MATERIALIZED VIEW IF EXISTS sunbiz_contacts CASCADE")
        
        # Build view with available columns
        view_sql = """
            CREATE MATERIALIZED VIEW sunbiz_contacts AS
            SELECT DISTINCT
                so.doc_number,
                so.officer_name,
                so.officer_title,
                so.officer_email,
                so.officer_phone,
                so.officer_address,
                so.officer_city,
                so.officer_state,
                so.officer_zip,
                sc.entity_name,
                sc.status,
                sc.filing_date,
                sc.state_country,
                sc.prin_city,
                sc.prin_state
            FROM sunbiz_officers so
            LEFT JOIN sunbiz_corporate sc ON so.doc_number = sc.doc_number
            WHERE so.officer_email IS NOT NULL 
               OR so.officer_phone IS NOT NULL
        """
        
        cur.execute(view_sql)
        
        # Create indexes
        cur.execute("""
            CREATE INDEX idx_contacts_email 
                ON sunbiz_contacts(officer_email)
                WHERE officer_email IS NOT NULL;
                
            CREATE INDEX idx_contacts_phone
                ON sunbiz_contacts(officer_phone)
                WHERE officer_phone IS NOT NULL;
                
            CREATE INDEX idx_contacts_entity
                ON sunbiz_contacts(entity_name)
                WHERE entity_name IS NOT NULL;
        """)
        
        conn.commit()
        print("✅ Contact view created successfully")
        
        # Count contacts
        cur.execute("SELECT COUNT(*) FROM sunbiz_contacts")
        total_contacts = cur.fetchone()[0]
        print(f"✅ Total contacts: {total_contacts:,}")
        
        # Sample joined data
        print("\n5. SAMPLE CONTACT RECORDS")
        print("-" * 40)
        
        cur.execute("""
            SELECT 
                entity_name,
                officer_name,
                officer_title,
                officer_email
            FROM sunbiz_contacts
            WHERE entity_name IS NOT NULL
            LIMIT 5
        """)
        
        results = cur.fetchall()
        if results:
            for entity, name, title, email in results:
                print(f"\n  Company: {entity}")
                print(f"  Contact: {name} ({title})")
                print(f"  Email: {email}")
        else:
            print("  No matched entities yet (sample data)")
        
        # Create search function
        print("\n6. CREATING SEARCH FUNCTION")
        print("-" * 40)
        
        cur.execute("""
            CREATE OR REPLACE FUNCTION search_contacts_by_email(search_term TEXT)
            RETURNS TABLE (
                doc_number VARCHAR,
                entity_name VARCHAR,
                officer_name VARCHAR,
                officer_email VARCHAR,
                officer_phone VARCHAR
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    sc.doc_number,
                    sc.entity_name,
                    sc.officer_name,
                    sc.officer_email,
                    sc.officer_phone
                FROM sunbiz_contacts sc
                WHERE sc.officer_email ILIKE '%' || search_term || '%'
                LIMIT 100;
            END;
            $$;
            
            CREATE OR REPLACE FUNCTION search_entity_contacts(entity_search TEXT)
            RETURNS TABLE (
                entity_name VARCHAR,
                officer_name VARCHAR,
                officer_email VARCHAR,
                officer_phone VARCHAR
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                SELECT 
                    sc.entity_name,
                    sc.officer_name,
                    sc.officer_email,
                    sc.officer_phone
                FROM sunbiz_contacts sc
                WHERE sc.entity_name ILIKE '%' || entity_search || '%'
                  AND sc.officer_email IS NOT NULL
                LIMIT 100;
            END;
            $$;
        """)
        
        conn.commit()
        print("✅ Search functions created")
        
        print("\n" + "=" * 60)
        print("EMAIL DATA VERIFICATION COMPLETE")
        print("=" * 60)
        
        print("\n✅ SUCCESS! Email data is loaded and indexed")
        print(f"📧 {with_email:,} email addresses available")
        print(f"📞 {with_phone:,} phone numbers available")
        
        print("\n📝 USAGE EXAMPLES:")
        print("-" * 40)
        print("\n-- Find all contacts for a company:")
        print("SELECT * FROM sunbiz_contacts WHERE entity_name ILIKE '%CONCORD%';")
        
        print("\n-- Search by email domain:")
        print("SELECT * FROM search_contacts_by_email('gmail.com');")
        
        print("\n-- Get entity contacts:")
        print("SELECT * FROM search_entity_contacts('LLC');")
        
        print("\n-- Export all emails:")
        print("SELECT DISTINCT officer_email FROM sunbiz_contacts")
        print("WHERE officer_email IS NOT NULL;")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    verify_email_data()