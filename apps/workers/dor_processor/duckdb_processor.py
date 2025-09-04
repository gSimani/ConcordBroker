"""
DuckDB-based Florida DOR Data Processor
Efficiently handles large Excel/CSV files from Florida Department of Revenue
"""

import os
import asyncio
import logging
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import duckdb
import pandas as pd
import aiohttp
import asyncpg
# from supabase import create_client, Client  # Temporarily disabled due to version conflict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DORDuckDBProcessor:
    """High-performance DOR data processor using DuckDB"""
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
        self.database_url = os.getenv('DATABASE_URL')
        self.data_dir = Path(os.getenv('DOR_DATA_DIR', 'C:/Users/gsima/Documents/MyProject/ConcordBroker/data/dor'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # self.supabase: Optional[Client] = None  # Temporarily disabled
        self.conn: Optional[duckdb.DuckDBPyConnection] = None
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize connections"""
        # self.supabase = create_client(self.supabase_url, self.supabase_key)  # Temporarily disabled
        
        self.conn = duckdb.connect(':memory:')
        self.conn.execute("SET memory_limit='4GB'")
        self.conn.execute("SET threads=4")
        
        self.conn.execute("INSTALL postgres")
        self.conn.execute("LOAD postgres")
        
        # Parse the database URL to extract connection parameters
        from urllib.parse import urlparse
        
        parsed = urlparse(self.database_url)
        
        # Extract connection details
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_user = parsed.username
        db_password = parsed.password
        db_name = parsed.path[1:] if parsed.path else 'postgres'
        
        # Handle SSL mode from query parameters
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self.pool = await asyncpg.create_pool(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name,
            min_size=2,
            max_size=10,
            command_timeout=300,
            ssl=ssl_context
        )
        
        await self.setup_tables()
        
    async def close(self):
        """Close connections"""
        if self.conn:
            self.conn.close()
        if self.pool:
            await self.pool.close()
            
    async def setup_tables(self):
        """Create optimized tables in Supabase"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dor_properties (
                    id BIGSERIAL PRIMARY KEY,
                    folio VARCHAR(30) UNIQUE NOT NULL,
                    county VARCHAR(50),
                    year INTEGER,
                    
                    -- Owner Information
                    owner_name TEXT,
                    owner_type VARCHAR(20),
                    
                    -- Mailing Address
                    mail_address_1 TEXT,
                    mail_address_2 TEXT,
                    mail_city VARCHAR(100),
                    mail_state VARCHAR(2),
                    mail_zip VARCHAR(10),
                    mail_country VARCHAR(50),
                    
                    -- Property Address
                    situs_address_1 TEXT,
                    situs_address_2 TEXT,
                    situs_city VARCHAR(100),
                    situs_state VARCHAR(2) DEFAULT 'FL',
                    situs_zip VARCHAR(10),
                    
                    -- Property Details
                    use_code VARCHAR(10),
                    use_description TEXT,
                    subdivision TEXT,
                    section VARCHAR(10),
                    township VARCHAR(10),
                    range VARCHAR(10),
                    legal_description TEXT,
                    
                    -- Physical Characteristics
                    land_area_sf NUMERIC,
                    building_area_sf NUMERIC,
                    living_area_sf NUMERIC,
                    year_built INTEGER,
                    effective_year_built INTEGER,
                    bedrooms INTEGER,
                    bathrooms NUMERIC(4,2),
                    pool BOOLEAN DEFAULT FALSE,
                    
                    -- Values
                    land_value NUMERIC(15,2),
                    building_value NUMERIC(15,2),
                    extra_feature_value NUMERIC(15,2),
                    just_value NUMERIC(15,2),
                    assessed_value NUMERIC(15,2),
                    taxable_value NUMERIC(15,2),
                    
                    -- Tax Information
                    millage_rate NUMERIC(8,4),
                    tax_amount NUMERIC(12,2),
                    exemptions JSONB,
                    
                    -- Metadata
                    source_file VARCHAR(255),
                    load_timestamp TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- Full-text search
                    search_vector tsvector GENERATED ALWAYS AS (
                        to_tsvector('english',
                            COALESCE(owner_name, '') || ' ' ||
                            COALESCE(situs_address_1, '') || ' ' ||
                            COALESCE(situs_city, '') || ' ' ||
                            COALESCE(subdivision, '')
                        )
                    ) STORED
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dor_sales (
                    id BIGSERIAL PRIMARY KEY,
                    folio VARCHAR(30),
                    county VARCHAR(50),
                    
                    -- Sale Information
                    sale_date DATE,
                    recording_date DATE,
                    sale_price NUMERIC(15,2),
                    sale_type VARCHAR(50),
                    sale_qualification VARCHAR(10),
                    
                    -- Parties
                    grantor TEXT,
                    grantee TEXT,
                    
                    -- Recording Info
                    deed_type VARCHAR(50),
                    instrument_number VARCHAR(50),
                    book VARCHAR(20),
                    page VARCHAR(20),
                    
                    -- Property Details at Sale
                    vacant_at_sale BOOLEAN,
                    multi_parcel BOOLEAN,
                    parcel_count INTEGER,
                    
                    -- Verification
                    verified BOOLEAN DEFAULT FALSE,
                    verification_code VARCHAR(10),
                    
                    -- Metadata
                    source_file VARCHAR(255),
                    load_timestamp TIMESTAMP DEFAULT NOW(),
                    
                    FOREIGN KEY (folio) REFERENCES dor_properties(folio)
                )
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_dor_properties_folio ON dor_properties(folio);
                CREATE INDEX IF NOT EXISTS idx_dor_properties_owner ON dor_properties(LOWER(owner_name));
                CREATE INDEX IF NOT EXISTS idx_dor_properties_city ON dor_properties(situs_city);
                CREATE INDEX IF NOT EXISTS idx_dor_properties_value ON dor_properties(just_value DESC);
                CREATE INDEX IF NOT EXISTS idx_dor_properties_search ON dor_properties USING GIN(search_vector);
                
                CREATE INDEX IF NOT EXISTS idx_dor_sales_folio ON dor_sales(folio);
                CREATE INDEX IF NOT EXISTS idx_dor_sales_date ON dor_sales(sale_date DESC);
                CREATE INDEX IF NOT EXISTS idx_dor_sales_price ON dor_sales(sale_price DESC);
            """)
            
    async def download_dor_file(self, url: str, county: str, year: int) -> Path:
        """Download DOR file from Florida Revenue website"""
        logger.info(f"Downloading {county} {year} data from {url}")
        
        filename = f"{county}_{year}_NAL.zip"
        filepath = self.data_dir / filename
        
        if filepath.exists():
            logger.info(f"File already exists: {filepath}")
            return filepath
            
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024 * 10) == 0:  # Log every 10MB
                                logger.info(f"Download progress: {progress:.1f}%")
                                
        logger.info(f"Downloaded: {filepath}")
        return filepath
        
    def extract_zip(self, zip_path: Path) -> List[Path]:
        """Extract ZIP file and return list of extracted files"""
        extract_dir = zip_path.parent / zip_path.stem
        extract_dir.mkdir(exist_ok=True)
        
        extracted_files = []
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            for name in zip_ref.namelist():
                extracted_files.append(extract_dir / name)
                
        logger.info(f"Extracted {len(extracted_files)} files to {extract_dir}")
        return extracted_files
        
    async def process_with_duckdb(self, file_path: Path, county: str, year: int) -> Tuple[int, int]:
        """Process file using DuckDB for maximum efficiency"""
        logger.info(f"Processing {file_path} with DuckDB")
        
        file_ext = file_path.suffix.lower()
        
        if file_ext in ['.xlsx', '.xls']:
            # For Excel files, use pandas to read then register with DuckDB
            import pandas as pd
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path)
            logger.info(f"Excel columns detected: {list(df.columns)}")
            logger.info(f"Loaded {len(df)} rows from Excel")
            
            # Register the DataFrame as a DuckDB table
            self.conn.register('raw_data', df)
            self.conn.execute("CREATE OR REPLACE TABLE raw_data AS SELECT * FROM raw_data")
        elif file_ext == '.csv':
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE raw_data AS 
                SELECT * FROM read_csv_auto('{file_path}', 
                    sample_size=100000,
                    all_varchar=false,
                    header=true)
            """)
        elif file_ext in ['.txt', '.dat']:
            # Handle fixed-width format
            self.conn.execute(f"""
                CREATE OR REPLACE TABLE raw_data AS 
                SELECT * FROM read_csv('{file_path}', 
                    delim='|',
                    header=false,
                    columns={self.get_nal_columns()})
            """)
        else:
            logger.warning(f"Unsupported file type: {file_ext}")
            return 0, 0
            
        # Get column mapping
        columns = self.conn.execute("SELECT * FROM raw_data LIMIT 1").df().columns
        logger.info(f"Available columns: {list(columns)}")
        
        # Process properties data
        property_count = await self.process_properties(county, year, file_path.name)
        
        # Process sales data if available
        sales_count = await self.process_sales(county, file_path.name)
        
        return property_count, sales_count
        
    def get_nal_columns(self) -> str:
        """Get NAL fixed-width column definitions"""
        return """
            {'folio': 'VARCHAR', 'account_type': 'VARCHAR', 'owner_name': 'VARCHAR',
             'mail_line_1': 'VARCHAR', 'mail_line_2': 'VARCHAR', 'mail_city': 'VARCHAR',
             'mail_state': 'VARCHAR', 'mail_zip': 'VARCHAR', 'mail_country': 'VARCHAR',
             'situs_line_1': 'VARCHAR', 'situs_line_2': 'VARCHAR', 'situs_city': 'VARCHAR',
             'situs_zip': 'VARCHAR', 'use_code': 'VARCHAR', 'subdivision': 'VARCHAR',
             'plat_book': 'VARCHAR', 'plat_page': 'VARCHAR', 'living_area': 'INTEGER',
             'year_built': 'INTEGER', 'bedrooms': 'INTEGER', 'bathrooms': 'DECIMAL',
             'pool': 'VARCHAR', 'just_value': 'DECIMAL', 'taxable_value': 'DECIMAL',
             'land_value': 'DECIMAL', 'building_value': 'DECIMAL'}
        """
        
    async def process_properties(self, county: str, year: int, source_file: str) -> int:
        """Process property records"""
        
        # Transform and clean data
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE properties_clean AS
            SELECT 
                TRIM(COALESCE(folio, parcel_id, account_no)) AS folio,
                '{county}' AS county,
                {year} AS year,
                TRIM(owner_name) AS owner_name,
                TRIM(mail_address_1) AS mail_address_1,
                TRIM(mail_address_2) AS mail_address_2,
                TRIM(mail_city) AS mail_city,
                TRIM(mail_state) AS mail_state,
                TRIM(mail_zip) AS mail_zip,
                TRIM(situs_address_1) AS situs_address_1,
                TRIM(situs_address_2) AS situs_address_2,
                TRIM(situs_city) AS situs_city,
                TRIM(situs_zip) AS situs_zip,
                use_code,
                subdivision,
                TRY_CAST(living_area AS INTEGER) AS living_area_sf,
                TRY_CAST(year_built AS INTEGER) AS year_built,
                TRY_CAST(bedrooms AS INTEGER) AS bedrooms,
                TRY_CAST(bathrooms AS DECIMAL) AS bathrooms,
                CASE WHEN UPPER(pool) = 'Y' THEN TRUE ELSE FALSE END AS pool,
                TRY_CAST(REPLACE(REPLACE(land_value, ',', ''), '$', '') AS DECIMAL) AS land_value,
                TRY_CAST(REPLACE(REPLACE(building_value, ',', ''), '$', '') AS DECIMAL) AS building_value,
                TRY_CAST(REPLACE(REPLACE(just_value, ',', ''), '$', '') AS DECIMAL) AS just_value,
                TRY_CAST(REPLACE(REPLACE(taxable_value, ',', ''), '$', '') AS DECIMAL) AS taxable_value,
                '{source_file}' AS source_file,
                NOW() AS load_timestamp
            FROM raw_data
            WHERE folio IS NOT NULL OR parcel_id IS NOT NULL OR account_no IS NOT NULL
        """)
        
        # Export to Supabase using COPY
        count = self.conn.execute("SELECT COUNT(*) FROM properties_clean").fetchone()[0]
        
        if count > 0:
            # For now, use batch insert via asyncpg until we configure DuckDB postgres extension
            logger.info(f"Inserting {count} property records to Supabase...")
            
            # Convert to pandas for batch processing
            df = self.conn.execute("SELECT * FROM properties_clean").df()
            
            # Insert in batches using asyncpg
            batch_size = 1000
            inserted = 0
            
            async with self.pool.acquire() as conn:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    values = []
                    for _, row in batch.iterrows():
                        values.append((
                            row['folio'], row['county'], row['year'],
                            row['owner_name'], row['mail_address_1'], row['mail_address_2'],
                            row['mail_city'], row['mail_state'], row['mail_zip'],
                            row['situs_address_1'], row['situs_address_2'],
                            row['situs_city'], row['situs_zip'],
                            row['use_code'], row['subdivision'],
                            row['living_area_sf'], row['year_built'],
                            row['bedrooms'], row['bathrooms'], row['pool'],
                            row['land_value'], row['building_value'],
                            row['just_value'], row['taxable_value'],
                            row['source_file']
                        ))
                    
                    await conn.executemany("""
                        INSERT INTO dor_properties (
                            folio, county, year, owner_name,
                            mail_address_1, mail_address_2, mail_city, mail_state, mail_zip,
                            situs_address_1, situs_address_2, situs_city, situs_zip,
                            use_code, subdivision,
                            living_area_sf, year_built, bedrooms, bathrooms, pool,
                            land_value, building_value, just_value, taxable_value,
                            source_file
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                                 $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
                        ON CONFLICT (folio) DO UPDATE SET
                            county = EXCLUDED.county,
                            year = EXCLUDED.year,
                            owner_name = EXCLUDED.owner_name,
                            updated_at = NOW()
                    """, values)
                    
                    inserted += len(batch)
                    if inserted % 10000 == 0:
                        logger.info(f"Inserted {inserted}/{count} records...")
            
        logger.info(f"Processed {count} property records")
        return count
        
    async def process_sales(self, county: str, source_file: str) -> int:
        """Process sales records if available"""
        
        # Check if sales data exists
        columns = self.conn.execute("SELECT * FROM raw_data LIMIT 1").df().columns
        
        if 'sale_date' not in columns and 'sale_price' not in columns:
            logger.info("No sales data found in this file")
            return 0
            
        self.conn.execute(f"""
            CREATE OR REPLACE TABLE sales_clean AS
            SELECT 
                TRIM(COALESCE(folio, parcel_id, account_no)) AS folio,
                '{county}' AS county,
                TRY_CAST(sale_date AS DATE) AS sale_date,
                TRY_CAST(REPLACE(REPLACE(sale_price, ',', ''), '$', '') AS DECIMAL) AS sale_price,
                sale_type,
                grantor,
                grantee,
                instrument_number,
                deed_type,
                '{source_file}' AS source_file,
                NOW() AS load_timestamp
            FROM raw_data
            WHERE sale_date IS NOT NULL AND sale_price IS NOT NULL
        """)
        
        count = self.conn.execute("SELECT COUNT(*) FROM sales_clean").fetchone()[0]
        
        if count > 0:
            logger.info(f"Inserting {count} sales records to Supabase...")
            df_sales = self.conn.execute("SELECT * FROM sales_clean").df()
            
            batch_size = 1000
            inserted = 0
            
            async with self.pool.acquire() as conn:
                for i in range(0, len(df_sales), batch_size):
                    batch = df_sales.iloc[i:i+batch_size]
                    
                    values = []
                    for _, row in batch.iterrows():
                        values.append((
                            row['folio'], row['county'],
                            row['sale_date'], row['sale_price'],
                            row['sale_type'], row['grantor'], row['grantee'],
                            row.get('instrument_number'), row.get('deed_type'),
                            row['source_file']
                        ))
                    
                    await conn.executemany("""
                        INSERT INTO dor_sales (
                            folio, county, sale_date, sale_price, sale_type,
                            grantor, grantee, instrument_number, deed_type, source_file
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT DO NOTHING
                    """, values)
                    
                    inserted += len(batch)
            
        logger.info(f"Processed {count} sales records")
        return count
        
    async def process_county_data(self, url: str, county: str, year: int = 2025):
        """Complete pipeline for processing county data"""
        try:
            # Download file
            zip_path = await self.download_dor_file(url, county, year)
            
            # Extract files
            extracted_files = self.extract_zip(zip_path)
            
            total_properties = 0
            total_sales = 0
            
            # Process each file
            for file_path in extracted_files:
                if file_path.suffix.lower() in ['.xlsx', '.xls', '.csv', '.txt', '.dat']:
                    props, sales = await self.process_with_duckdb(file_path, county, year)
                    total_properties += props
                    total_sales += sales
                    
            logger.info(f"Total processed: {total_properties} properties, {total_sales} sales")
            
            # Generate summary report
            await self.generate_summary(county, year)
            
            return {
                'county': county,
                'year': year,
                'properties': total_properties,
                'sales': total_sales
            }
            
        except Exception as e:
            logger.error(f"Error processing {county} data: {e}")
            raise
            
    async def generate_summary(self, county: str, year: int):
        """Generate summary Excel report"""
        
        # Query aggregated data
        summary_query = f"""
            SELECT 
                situs_city AS city,
                use_code,
                COUNT(*) AS property_count,
                AVG(just_value) AS avg_value,
                SUM(just_value) AS total_value,
                AVG(living_area_sf) AS avg_living_area,
                AVG(year_built) AS avg_year_built
            FROM dor_properties
            WHERE county = '{county}' AND year = {year}
            GROUP BY situs_city, use_code
            ORDER BY total_value DESC
        """
        
        df_summary = self.conn.execute(summary_query).df()
        
        # Top properties
        top_properties = self.conn.execute(f"""
            SELECT 
                folio,
                owner_name,
                situs_address_1,
                situs_city,
                use_code,
                just_value,
                living_area_sf,
                year_built
            FROM dor_properties
            WHERE county = '{county}' AND year = {year}
            ORDER BY just_value DESC
            LIMIT 1000
        """).df()
        
        # Recent sales
        recent_sales = self.conn.execute(f"""
            SELECT 
                s.folio,
                p.owner_name,
                p.situs_address_1,
                s.sale_date,
                s.sale_price,
                p.just_value,
                s.sale_price / NULLIF(p.just_value, 0) AS price_to_value_ratio
            FROM dor_sales s
            JOIN dor_properties p ON s.folio = p.folio
            WHERE s.county = '{county}'
            ORDER BY s.sale_date DESC
            LIMIT 1000
        """).df()
        
        # Write to Excel
        output_file = self.data_dir / f"{county}_{year}_summary.xlsx"
        with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            top_properties.to_excel(writer, sheet_name='Top Properties', index=False)
            recent_sales.to_excel(writer, sheet_name='Recent Sales', index=False)
            
        logger.info(f"Summary report generated: {output_file}")


async def main():
    """Main execution"""
    processor = DORDuckDBProcessor()
    
    try:
        await processor.initialize()
        
        # Process Broward County 2025 preliminary data
        broward_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Broward%2016%20Preliminary%20NAL%202025.zip"
        
        result = await processor.process_county_data(
            url=broward_url,
            county="Broward",
            year=2025
        )
        
        logger.info(f"Processing complete: {result}")
        
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())