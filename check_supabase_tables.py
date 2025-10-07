"""
Check what tables exist in Supabase
"""
import os
from supabase import create_client, Client
import psycopg2

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.mcp')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("=" * 80)
print("SUPABASE TABLES INSPECTION")
print("=" * 80)

# Parse the connection string from SUPABASE_URL
# Format: https://PROJECT_ID.supabase.co
import re
match = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
if match:
    project_id = match.group(1)
    # Construct PostgreSQL connection string
    # You'll need the database password from environment
    db_password = os.getenv('SUPABASE_DB_PASSWORD', '')

    if db_password:
        try:
            conn = psycopg2.connect(
                host=f"db.{project_id}.supabase.co",
                port=5432,
                database="postgres",
                user="postgres",
                password=db_password
            )

            cursor = conn.cursor()

            # List all tables
            cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name;
            """)

            tables = cursor.fetchall()

            print(f"\nFound {len(tables)} tables:\n")
            print(f"{'Schema':<20} {'Table Name':<40}")
            print("-" * 80)

            for schema, table_name in tables:
                print(f"{schema:<20} {table_name:<40}")

                # Check if it's a property-related table
                if 'property' in table_name.lower() or 'parcel' in table_name.lower() or 'florida' in table_name.lower():
                    # Get row count and column info
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table_name};")
                        count = cursor.fetchone()[0]

                        cursor.execute(f"""
                            SELECT column_name, data_type
                            FROM information_schema.columns
                            WHERE table_schema = '{schema}'
                            AND table_name = '{table_name}'
                            AND column_name ILIKE '%living%'
                            ORDER BY ordinal_position;
                        """)
                        living_cols = cursor.fetchall()

                        print(f"  -> {count:,} records")
                        if living_cols:
                            print(f"  -> Living area columns: {', '.join([col[0] for col in living_cols])}")
                    except Exception as e:
                        print(f"  -> ERROR: {e}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"\nPostgreSQL connection failed: {e}")
            print("\nPlease set SUPABASE_DB_PASSWORD in .env.mcp")
    else:
        print("\nSUPABASE_DB_PASSWORD not found in .env.mcp")
        print("Cannot connect directly to PostgreSQL")

# Try with Supabase client to list accessible tables
print("\n" + "=" * 80)
print("TRYING COMMON TABLE NAMES")
print("=" * 80)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

common_tables = [
    'florida_parcels',
    'properties',
    'property_data',
    'parcels',
    'nal_data',
    'property_appraiser',
    'florida_properties'
]

for table in common_tables:
    try:
        result = supabase.table(table).select('*').limit(1).execute()
        print(f"✓ {table:<30} - EXISTS ({len(result.data)} sample)")
    except Exception as e:
        if '42P01' in str(e):
            print(f"✗ {table:<30} - DOES NOT EXIST")
        else:
            print(f"? {table:<30} - ERROR: {e}")

print("\n" + "=" * 80)