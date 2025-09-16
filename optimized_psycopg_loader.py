"""
Optimized PostgreSQL COPY Loader for Florida Property Data
Uses psycopg with direct connection for maximum performance
"""

import os
import glob
import csv
import psycopg
from psycopg import sql
from datetime import datetime
import time
import traceback
from typing import Dict, List

# Database configuration - Using pooler for connectivity
DATABASE_HOST = "aws-0-us-east-1.pooler.supabase.com"
DATABASE_NAME = "postgres"
DATABASE_USER = "postgres.pmispwtdngkcmsrsjwbp"  # Using main postgres user
DATABASE_PASSWORD = "West@Boca613!"  # Direct database password
DATABASE_PORT = 5432

# Data source
BASE_PATH = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"

# Expected counts for validation
EXPECTED_COUNTS = {
    'BROWARD': 753242, 'DADE': 933276, 'PALM BEACH': 616436,
    'HILLSBOROUGH': 524735, 'ORANGE': 445018, 'PINELLAS': 444821,
    'LEE': 389491, 'POLK': 309595, 'DUVAL': 305928,
    'BREVARD': 283107, 'VOLUSIA': 258456, 'SEMINOLE': 192525,
    'PASCO': 181865, 'COLLIER': 167456, 'SARASOTA': 167214,
    'MANATEE': 156303, 'MARION': 155808, 'OSCEOLA': 136648,
    'LAKE': 135299, 'ST. LUCIE': 134308
}

def get_connection_string():
    """Build direct connection string (bypasses PgBouncer)"""
    return f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"

def check_current_status(conn) -> Dict[str, int]:
    """Check current row counts by county"""
    status = {}
    
    with conn.cursor() as cur:
        print("Checking current database status...")
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
        total = cur.fetchone()[0]
        print(f"Total records: {total:,}")
        
        # Get counts by county
        cur.execute("""
            SELECT county, COUNT(*) as count
            FROM public.florida_parcels
            GROUP BY county
            ORDER BY count DESC
        """)
        
        for row in cur.fetchall():
            status[row[0]] = row[1]
    
    return status

def prepare_staging_table(conn):
    """Ensure staging table exists and is ready"""
    with conn.cursor() as cur:
        print("Preparing staging table...")
        
        # Create staging table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS public.florida_parcels_staging (
                LIKE public.florida_parcels INCLUDING DEFAULTS INCLUDING GENERATED
            )
        """)
        
        # Clear any existing data
        cur.execute("TRUNCATE public.florida_parcels_staging")
        
        conn.commit()
        print("Staging table ready")

def prepare_csv_for_copy(county_folder: str, output_path: str) -> int:
    """Prepare county CSV for COPY command with proper column mapping"""
    
    county_path = os.path.join(BASE_PATH, county_folder, 'NAL')
    if not os.path.exists(county_path):
        return 0
    
    csv_files = glob.glob(os.path.join(county_path, '*.csv'))
    if not csv_files:
        return 0
    
    row_count = 0
    
    # Write consolidated CSV for COPY
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.writer(outfile)
        
        # Write header matching florida_parcels columns
        writer.writerow([
            'parcel_id', 'county', 'year', 'owner_name', 'owner_addr1', 'owner_addr2',
            'owner_city', 'owner_state', 'owner_zip', 'phy_addr1', 'phy_addr2',
            'phy_city', 'phy_state', 'phy_zipcd', 'just_value', 'taxable_value',
            'land_value', 'land_sqft', 'building_value', 'land_use_code',
            'property_use', 'property_use_desc', 'sale_price', 'legal_desc',
            'year_built', 'total_living_area', 'bedrooms', 'bathrooms',
            'data_source', 'import_date'
        ])
        
        # Process each source CSV
        for csv_file in csv_files:
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                
                for row in reader:
                    # Map and clean fields
                    writer.writerow([
                        row.get('PARCEL_ID', '').strip()[:100],
                        county_folder.upper(),
                        2025,
                        row.get('OWN_NAME', '').strip()[:500],
                        row.get('OWN_ADDR1', '').strip()[:200],
                        row.get('OWN_ADDR2', '').strip()[:200],
                        row.get('OWN_CITY', '').strip()[:100],
                        row.get('OWN_STATE', '').strip()[:2],  # Truncate to 2 chars
                        row.get('OWN_ZIPCD', '').strip()[:20],
                        row.get('PHY_ADDR1', '').strip()[:200],
                        row.get('PHY_ADDR2', '').strip()[:200],
                        row.get('PHY_CITY', '').strip()[:100],
                        row.get('PHY_STATE', '').strip()[:2],  # Truncate to 2 chars
                        row.get('PHY_ZIPCD', '').strip()[:20],
                        row.get('JV', '0').replace(',', '') or '0',
                        row.get('TV_SD', '0').replace(',', '') or '0',
                        row.get('LND_VAL', '0').replace(',', '') or '0',
                        row.get('LND_SQFOOT', '0').replace(',', '') or '0',
                        row.get('BLD_VAL', '0').replace(',', '') or '0',
                        row.get('DOR_UC', '').strip()[:10],
                        row.get('DOR_UC', '').strip()[:10],
                        row.get('PA_UC_DESC', '').strip()[:200],
                        row.get('SALE_PRC1', '0').replace(',', '') or '0',
                        row.get('LEGAL1', '').strip()[:500],
                        row.get('ACT_YR_BLT', '0') or '0',
                        row.get('TOT_LVG_AREA', '0').replace(',', '') or '0',
                        row.get('NO_BDRMS', '0') or '0',
                        row.get('NO_BATHS', '0') or '0',
                        'NAL_2025',
                        datetime.now().isoformat()
                    ])
                    row_count += 1
    
    return row_count

def copy_county_to_staging(conn, county: str) -> int:
    """Copy county data to staging table using COPY command"""
    
    # Prepare CSV file
    temp_csv = f"temp_{county}.csv"
    row_count = prepare_csv_for_copy(county, temp_csv)
    
    if row_count == 0:
        print(f"  No data found for {county}")
        return 0
    
    print(f"  Loading {row_count:,} records for {county}...")
    
    try:
        with conn.cursor() as cur:
            # Optimize session for bulk loading
            cur.execute("SET statement_timeout = '0'")
            cur.execute("SET lock_timeout = '0'")
            cur.execute("SET idle_in_transaction_session_timeout = '0'")
            cur.execute("SET synchronous_commit = off")
            cur.execute("SET work_mem = '256MB'")
            cur.execute("SET maintenance_work_mem = '512MB'")
            
            # Use COPY for maximum speed
            with open(temp_csv, 'r', encoding='utf-8') as f:
                start_time = time.time()
                
                cur.copy("""
                    COPY public.florida_parcels_staging (
                        parcel_id, county, year, owner_name, owner_addr1, owner_addr2,
                        owner_city, owner_state, owner_zip, phy_addr1, phy_addr2,
                        phy_city, phy_state, phy_zipcd, just_value, taxable_value,
                        land_value, land_sqft, building_value, land_use_code,
                        property_use, property_use_desc, sale_price, legal_desc,
                        year_built, total_living_area, bedrooms, bathrooms,
                        data_source, import_date
                    )
                    FROM STDIN WITH (FORMAT CSV, HEADER TRUE)
                """, f)
                
                elapsed = time.time() - start_time
                rate = row_count / elapsed if elapsed > 0 else 0
                
                print(f"    Loaded in {elapsed:.1f}s ({rate:.0f} records/sec)")
                
        conn.commit()
        
        # Clean up temp file
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        
        return row_count
        
    except Exception as e:
        print(f"    Error: {e}")
        traceback.print_exc()
        conn.rollback()
        
        # Clean up temp file
        if os.path.exists(temp_csv):
            os.remove(temp_csv)
        
        return 0

def migrate_staging_to_final(conn):
    """Migrate data from staging to final table with deduplication"""
    
    print("\nMigrating staging to final table...")
    
    with conn.cursor() as cur:
        # Count staging records
        cur.execute("SELECT COUNT(*) FROM public.florida_parcels_staging")
        staging_count = cur.fetchone()[0]
        print(f"  Staging has {staging_count:,} records")
        
        if staging_count == 0:
            print("  No records to migrate")
            return
        
        # Migrate with ON CONFLICT handling
        print("  Migrating with deduplication...")
        start_time = time.time()
        
        cur.execute("""
            INSERT INTO public.florida_parcels (
                parcel_id, county, year, owner_name, owner_addr1, owner_addr2,
                owner_city, owner_state, owner_zip, phy_addr1, phy_addr2,
                phy_city, phy_state, phy_zipcd, just_value, taxable_value,
                land_value, land_sqft, building_value, land_use_code,
                property_use, property_use_desc, sale_price, legal_desc,
                year_built, total_living_area, bedrooms, bathrooms,
                data_source, import_date
            )
            SELECT 
                parcel_id, county, year, owner_name, owner_addr1, owner_addr2,
                owner_city, owner_state, owner_zip, phy_addr1, phy_addr2,
                phy_city, phy_state, phy_zipcd, just_value, taxable_value,
                land_value, land_sqft, building_value, land_use_code,
                property_use, property_use_desc, sale_price, legal_desc,
                year_built, total_living_area, bedrooms, bathrooms,
                data_source, import_date
            FROM public.florida_parcels_staging
            ON CONFLICT (parcel_id, county, year) 
            DO UPDATE SET import_date = EXCLUDED.import_date
        """)
        
        rows_affected = cur.rowcount
        elapsed = time.time() - start_time
        
        print(f"    Migrated {rows_affected:,} records in {elapsed:.1f}s")
        
        # Clear staging
        cur.execute("TRUNCATE public.florida_parcels_staging")
        
    conn.commit()

def create_indexes(conn):
    """Create indexes after bulk loading"""
    
    print("\nCreating indexes...")
    
    indexes = [
        ("idx_florida_parcels_county", "county"),
        ("idx_florida_parcels_parcel_id", "parcel_id"),
        ("idx_florida_parcels_year", "year"),
        ("idx_florida_parcels_owner_name", "owner_name"),
        ("idx_florida_parcels_property_use", "property_use")
    ]
    
    with conn.cursor() as cur:
        for index_name, column in indexes:
            print(f"  Creating {index_name}...")
            try:
                # Use CONCURRENTLY to avoid locking (must be outside transaction)
                conn.autocommit = True
                cur.execute(f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name}
                    ON public.florida_parcels({column})
                """)
                print(f"    {index_name} created")
            except Exception as e:
                if "already exists" in str(e):
                    print(f"    - {index_name} already exists")
                else:
                    print(f"    Error creating {index_name}: {e}")
            finally:
                conn.autocommit = False
        
        # Update statistics
        print("  Analyzing table...")
        cur.execute("ANALYZE public.florida_parcels")
        print("    Statistics updated")

def main():
    """Main execution"""
    
    print("=" * 80)
    print("OPTIMIZED POSTGRESQL COPY LOADER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Password is now configured
    print("Database password configured")
    
    try:
        # Connect with direct connection (no PgBouncer)
        print(f"\nConnecting to database...")
        conn_string = get_connection_string()
        
        with psycopg.connect(conn_string) as conn:
            print("Connected successfully")
            
            # Check current status
            current_status = check_current_status(conn)
            
            # Prepare staging
            prepare_staging_table(conn)
            
            # Process counties needing upload
            counties_to_process = []
            for county, expected in EXPECTED_COUNTS.items():
                current = current_status.get(county, 0)
                if current < expected * 0.95:  # Less than 95% complete
                    counties_to_process.append((county, current, expected))
            
            counties_to_process.sort(key=lambda x: x[2] - x[1], reverse=True)  # Largest missing first
            
            print(f"\nFound {len(counties_to_process)} counties to process")
            
            # Process each county
            total_loaded = 0
            for i, (county, current, expected) in enumerate(counties_to_process, 1):
                print(f"\n[{i}/{len(counties_to_process)}] Processing {county}")
                print(f"  Current: {current:,} | Expected: {expected:,}")
                
                # Load to staging
                loaded = copy_county_to_staging(conn, county)
                total_loaded += loaded
                
                # Migrate staging to final after each county (or batch)
                if loaded > 0:
                    migrate_staging_to_final(conn)
            
            # Create indexes after all data loaded
            if total_loaded > 0:
                create_indexes(conn)
            
            # Final verification
            print("\n" + "=" * 80)
            print("FINAL VERIFICATION")
            print("=" * 80)
            
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM public.florida_parcels")
                final_count = cur.fetchone()[0]
                print(f"Total records in database: {final_count:,}")
                print(f"Expected total: {sum(EXPECTED_COUNTS.values()):,}")
                print(f"Completion: {final_count / sum(EXPECTED_COUNTS.values()) * 100:.2f}%")
    
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()