import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection parameters (env-driven; no hardcoded secrets)
conn_params = {
    'host': os.getenv('POSTGRES_HOST'),
    'database': os.getenv('POSTGRES_DATABASE', 'postgres'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'port': int(os.getenv('POSTGRES_PORT', '6543'))
}

def execute_sql_file(filename):
    """Execute SQL script from file"""
    try:
        missing = [k for k, v in conn_params.items() if not v and k not in ('port',)]
        if missing:
            print(f"[ERROR] Missing DB connection params: {missing}. Configure POSTGRES_* env vars.")
            return False
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Read SQL file
        with open(filename, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # Execute the script
        cur.execute(sql_script)
        conn.commit()
        
        print(f"[SUCCESS] Successfully executed {filename}")
        
        # Verify the data was inserted
        cur.execute("SELECT COUNT(*) FROM tax_certificates")
        count = cur.fetchone()[0]
        print(f"[DATA] Total tax certificates in database: {count}")
        
        # Show summary by status
        cur.execute("""
            SELECT status, COUNT(*), SUM(face_amount)
            FROM tax_certificates
            GROUP BY status
        """)
        results = cur.fetchall()
        print("\n[SUMMARY] Tax Certificates Summary:")
        for status, cert_count, total_amount in results:
            print(f"  - {status}: {cert_count} certificates, Total: ${total_amount:,.2f}")
        
        # Show properties with certificates
        cur.execute("""
            SELECT parcel_id, COUNT(*) as cert_count, SUM(redemption_amount) as total_due
            FROM tax_certificates
            WHERE status = 'active'
            GROUP BY parcel_id
            ORDER BY total_due DESC
            LIMIT 5
        """)
        results = cur.fetchall()
        print("\n[TOP PROPERTIES] Top 5 Properties with Active Tax Certificates:")
        for parcel, count, total in results:
            print(f"  - Parcel {parcel}: {count} certificates, Total Due: ${total:,.2f}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error executing SQL file: {e}")
        return False

if __name__ == "__main__":
    print("Deploying Tax Certificates Table with Real Data...")
    print("=" * 50)
    
    # Execute the SQL script
    if execute_sql_file('create_tax_certificates_real_data.sql'):
        print("\n[SUCCESS] Tax certificates table successfully created and populated!")
        print("[INFO] The table now contains real-world tax certificate data")
        print("[INFO] Your application can now fetch this data via Supabase")
    else:
        print("\n[ERROR] Failed to deploy tax certificates table")
