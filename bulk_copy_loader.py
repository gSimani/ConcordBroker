"""
Bulk COPY loader for Florida Property Appraiser data
Uses PostgreSQL COPY command for efficient bulk loading as recommended by Supabase support
Addresses the statement timeout issues that caused 99.4% data loss
"""

import os
import csv
import glob
import psycopg
from psycopg import sql
from datetime import datetime
import pandas as pd
from io import StringIO
import traceback

# Direct PostgreSQL connection strings
# Using the service role key from the successful Supabase client
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Using pooler connection (this should work based on the service role key)
DATABASE_URL = f"postgresql://postgres.pmispwtdngkcmsrsjwbp:{SERVICE_ROLE_KEY}@aws-0-us-east-1.pooler.supabase.com:5432/postgres"

# Alternative: Direct connection if available
DIRECT_DATABASE_URL = f"postgresql://postgres.pmispwtdngkcmsrsjwbp:{SERVICE_ROLE_KEY}@db.pmispwtdngkcmsrsjwbp.supabase.co:5432/postgres"

def create_staging_table(conn):
    """Create staging table without indexes for fast loading"""
    with conn.cursor() as cur:
        # Drop existing staging table if exists
        cur.execute("DROP TABLE IF EXISTS florida_parcels_staging CASCADE")
        
        # Create staging table with same structure as florida_parcels
        cur.execute("""
            CREATE TABLE florida_parcels_staging (
                parcel_id VARCHAR(100),
                county VARCHAR(50),
                year INTEGER,
                owner_name VARCHAR(500),
                owner_addr1 VARCHAR(200),
                owner_addr2 VARCHAR(200),
                owner_city VARCHAR(100),
                owner_state VARCHAR(2),
                owner_zip VARCHAR(20),
                phy_addr1 VARCHAR(200),
                phy_addr2 VARCHAR(200),
                phy_city VARCHAR(100),
                phy_state VARCHAR(2),
                phy_zipcd VARCHAR(20),
                just_value BIGINT,
                taxable_value BIGINT,
                land_value BIGINT,
                land_sqft BIGINT,
                building_value BIGINT,
                land_use_code VARCHAR(10),
                property_use VARCHAR(10),
                property_use_desc VARCHAR(200),
                sale_price BIGINT,
                sale_year INTEGER,
                legal_desc TEXT,
                year_built INTEGER,
                total_living_area INTEGER,
                bedrooms INTEGER,
                bathrooms INTEGER,
                data_source VARCHAR(50),
                import_date TIMESTAMP
            )
        """)
        conn.commit()
        print("Created staging table: florida_parcels_staging")

def prepare_csv_data(csv_file, county_name):
    """Prepare CSV data for COPY command"""
    rows = []
    
    try:
        df = pd.read_csv(csv_file, low_memory=False, encoding='utf-8', on_bad_lines='skip')
        
        for _, row in df.iterrows():
            # Safe value extraction with proper truncation
            def safe_int(value):
                if pd.isna(value) or value == '' or value is None:
                    return '\\N'  # PostgreSQL NULL representation
                try:
                    return str(int(float(str(value).replace(',', ''))))
                except:
                    return '\\N'
            
            def safe_str(value, max_length=None):
                if pd.isna(value) or value is None:
                    return '\\N'
                result = str(value).strip().replace('\t', ' ').replace('\n', ' ').replace('\r', '')
                if max_length and len(result) > max_length:
                    result = result[:max_length]
                return result if result else '\\N'
            
            # Build row for COPY
            csv_row = [
                safe_str(row.get('PARCEL_ID'), 100),
                county_name.upper(),
                '2025',
                safe_str(row.get('OWN_NAME'), 500),
                safe_str(row.get('OWN_ADDR1'), 200),
                safe_str(row.get('OWN_ADDR2'), 200),
                safe_str(row.get('OWN_CITY'), 100),
                safe_str(row.get('OWN_STATE'), 2),  # Truncate to 2 chars
                safe_str(row.get('OWN_ZIPCD'), 20),
                safe_str(row.get('PHY_ADDR1'), 200),
                safe_str(row.get('PHY_ADDR2'), 200),
                safe_str(row.get('PHY_CITY'), 100),
                safe_str(row.get('PHY_STATE'), 2),  # Truncate to 2 chars
                safe_str(row.get('PHY_ZIPCD'), 20),
                safe_int(row.get('JV')),
                safe_int(row.get('TV_SD')),
                safe_int(row.get('LND_VAL')),
                safe_int(row.get('LND_SQFOOT')),
                safe_int(row.get('BLD_VAL')),
                safe_str(row.get('DOR_UC'), 10),
                safe_str(row.get('DOR_UC'), 10),
                safe_str(row.get('PA_UC_DESC'), 200),
                safe_int(row.get('SALE_PRC1')),
                safe_int(row.get('SALE_YR1')),
                safe_str(row.get('LEGAL1'), 500),
                safe_int(row.get('ACT_YR_BLT')),
                safe_int(row.get('TOT_LVG_AREA')),
                safe_int(row.get('NO_BDRMS')),
                safe_int(row.get('NO_BATHS')),
                'NAL_2025',
                datetime.now().isoformat()
            ]
            
            # Only add if we have a valid parcel_id
            if csv_row[0] != '\\N':
                rows.append('\t'.join(csv_row))
    
    except Exception as e:
        print(f"Error processing CSV: {e}")
        traceback.print_exc()
    
    return rows

def load_county_with_copy(conn, county_folder, base_path):
    """Load a county's data using COPY command"""
    county_path = os.path.join(base_path, county_folder)
    
    if not os.path.isdir(county_path):
        return 0, "Directory not found"
    
    # Skip non-county folders
    if county_folder in ['NAL_2025', 'NAL_2025P'] or county_folder.endswith('.json') or county_folder.endswith('.md'):
        return 0, "Not a county folder"
    
    print(f"\nProcessing {county_folder}...")
    
    # Get NAL data files
    nal_path = os.path.join(county_path, 'NAL')
    if not os.path.exists(nal_path):
        print(f"  No NAL folder found for {county_folder}")
        return 0, "No NAL folder"
    
    # Look for CSV files
    csv_files = glob.glob(os.path.join(nal_path, 'NAL*.csv'))
    if not csv_files:
        csv_files = glob.glob(os.path.join(nal_path, '*.csv'))
    
    if not csv_files:
        print(f"  No CSV files found for {county_folder}")
        return 0, "No CSV files"
    
    total_loaded = 0
    
    for csv_file in csv_files:
        print(f"  Loading {os.path.basename(csv_file)}...")
        
        try:
            # Prepare data
            rows = prepare_csv_data(csv_file, county_folder)
            
            if not rows:
                print(f"    No valid rows found")
                continue
            
            # Create StringIO object with data
            data_io = StringIO('\n'.join(rows))
            
            with conn.cursor() as cur:
                # Use COPY to load data
                cur.copy_expert(
                    sql="""
                    COPY florida_parcels_staging (
                        parcel_id, county, year, owner_name, owner_addr1, owner_addr2,
                        owner_city, owner_state, owner_zip, phy_addr1, phy_addr2,
                        phy_city, phy_state, phy_zipcd, just_value, taxable_value,
                        land_value, land_sqft, building_value, land_use_code,
                        property_use, property_use_desc, sale_price, sale_year,
                        legal_desc, year_built, total_living_area, bedrooms,
                        bathrooms, data_source, import_date
                    ) FROM STDIN WITH (FORMAT TEXT, NULL '\\N', DELIMITER E'\\t')
                    """,
                    file=data_io
                )
                
                loaded = len(rows)
                total_loaded += loaded
                print(f"    Loaded {loaded:,} rows via COPY")
                conn.commit()
        
        except Exception as e:
            print(f"    Error loading file: {e}")
            conn.rollback()
            traceback.print_exc()
            continue
    
    return total_loaded, None

def merge_staging_to_main(conn):
    """Merge data from staging table to main table"""
    print("\nMerging staging data to main table...")
    
    with conn.cursor() as cur:
        # Insert new records (not already in main table)
        cur.execute("""
            INSERT INTO florida_parcels
            SELECT * FROM florida_parcels_staging s
            WHERE NOT EXISTS (
                SELECT 1 FROM florida_parcels m
                WHERE m.parcel_id = s.parcel_id
                AND m.county = s.county
                AND m.year = s.year
            )
        """)
        
        inserted = cur.rowcount
        print(f"  Inserted {inserted:,} new records")
        
        # Update existing records if needed
        cur.execute("""
            UPDATE florida_parcels m
            SET 
                owner_name = s.owner_name,
                owner_addr1 = s.owner_addr1,
                owner_city = s.owner_city,
                owner_state = s.owner_state,
                owner_zip = s.owner_zip,
                phy_addr1 = s.phy_addr1,
                phy_city = s.phy_city,
                phy_state = s.phy_state,
                phy_zipcd = s.phy_zipcd,
                just_value = s.just_value,
                taxable_value = s.taxable_value,
                land_value = s.land_value,
                building_value = s.building_value,
                sale_price = s.sale_price,
                sale_year = s.sale_year,
                import_date = s.import_date
            FROM florida_parcels_staging s
            WHERE m.parcel_id = s.parcel_id
            AND m.county = s.county
            AND m.year = s.year
        """)
        
        updated = cur.rowcount
        print(f"  Updated {updated:,} existing records")
        
        conn.commit()
        return inserted + updated

def create_indexes(conn):
    """Create indexes after bulk load"""
    print("\nCreating performance indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_county ON florida_parcels(county)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_parcel_id ON florida_parcels(parcel_id)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_owner_name ON florida_parcels(owner_name)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_phy_addr ON florida_parcels(phy_addr1, phy_city)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_just_value ON florida_parcels(just_value)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_sale_year ON florida_parcels(sale_year)",
        "CREATE INDEX IF NOT EXISTS idx_florida_parcels_composite ON florida_parcels(county, year, parcel_id)"
    ]
    
    with conn.cursor() as cur:
        for idx_sql in indexes:
            try:
                print(f"  Creating: {idx_sql.split('ON')[0].split('INDEX')[-1].strip()}...")
                cur.execute(idx_sql)
                conn.commit()
            except Exception as e:
                print(f"    Error: {e}")
                conn.rollback()

def main():
    """Main execution"""
    print("=" * 80)
    print("FLORIDA PROPERTY APPRAISER BULK COPY LOADER")
    print("Using PostgreSQL COPY for efficient bulk loading")
    print("=" * 80)
    
    base_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"
    
    # Try pooler connection first (which we know works)
    print("\nConnecting to database...")
    try:
        # Try pooler first (should work)
        print("Trying pooler connection...")
        with psycopg.connect(DATABASE_URL) as conn:
            # Set statement timeout to 0 (no timeout) for bulk operations
            with conn.cursor() as cur:
                cur.execute("SET statement_timeout = 0")
                cur.execute("SET work_mem = '256MB'")
                cur.execute("SET maintenance_work_mem = '512MB'")
                conn.commit()
            
            print("Connected successfully")
            
            # Create staging table
            create_staging_table(conn)
            
            # Get all county folders
            county_folders = []
            for item in os.listdir(base_path):
                if os.path.isdir(os.path.join(base_path, item)):
                    if item not in ['NAL_2025', 'NAL_2025P']:
                        county_folders.append(item)
            
            county_folders.sort()
            print(f"\nFound {len(county_folders)} counties to process")
            
            # Process each county
            total_records = 0
            successful_counties = []
            failed_counties = []
            
            for i, county in enumerate(county_folders, 1):
                print(f"\n[{i}/{len(county_folders)}] Loading {county}...")
                
                try:
                    # Clear staging table
                    with conn.cursor() as cur:
                        cur.execute("TRUNCATE florida_parcels_staging")
                        conn.commit()
                    
                    # Load county data to staging
                    records, error = load_county_with_copy(conn, county, base_path)
                    
                    if records > 0:
                        # Merge to main table
                        merged = merge_staging_to_main(conn)
                        successful_counties.append(county)
                        total_records += merged
                        print(f"  Successfully loaded {county}: {merged:,} records")
                    elif error:
                        print(f"  Skipped {county}: {error}")
                    
                except Exception as e:
                    print(f"  Failed to process {county}: {e}")
                    failed_counties.append(county)
                    conn.rollback()
                    traceback.print_exc()
            
            # Create indexes after all data is loaded
            create_indexes(conn)
            
            # Final summary
            print("\n" + "=" * 80)
            print("BULK LOAD COMPLETE")
            print("=" * 80)
            print(f"Total records loaded: {total_records:,}")
            print(f"Successful counties: {len(successful_counties)}/{len(county_folders)}")
            
            if failed_counties:
                print(f"\nFailed counties: {', '.join(failed_counties)}")
            
            # Verify final counts
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT county, COUNT(*) as count 
                    FROM florida_parcels 
                    GROUP BY county 
                    ORDER BY count DESC
                    LIMIT 10
                """)
                
                print("\nTop 10 counties by record count:")
                for row in cur.fetchall():
                    print(f"  {row[0]}: {row[1]:,}")
                
                cur.execute("SELECT COUNT(*) FROM florida_parcels")
                total = cur.fetchone()[0]
                print(f"\nTotal records in database: {total:,}")
    
    except Exception as e:
        print(f"Connection error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()