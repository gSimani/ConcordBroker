"""
DOR NAL/SDF Data Processor Worker
Processes Florida Department of Revenue Name & Address List and Sales Data Files
"""

import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
import polars as pl
import asyncpg
from typing import List, Dict, Optional, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NAL Field Specifications (Fixed-width format)
NAL_FIELDS = [
    ('FOLIO', 0, 23),           # Parcel ID
    ('ACCOUNT_TYPE', 23, 24),    # Account type code
    ('OWNER_NAME', 24, 144),     # Owner name (120 chars)
    ('MAIL_LINE_1', 144, 204),   # Mailing address line 1
    ('MAIL_LINE_2', 204, 264),   # Mailing address line 2
    ('MAIL_CITY', 264, 304),     # Mailing city
    ('MAIL_STATE', 304, 306),    # Mailing state
    ('MAIL_ZIP', 306, 316),      # Mailing ZIP code
    ('MAIL_COUNTRY', 316, 326),  # Mailing country
    ('SITUS_LINE_1', 326, 386),  # Property address line 1
    ('SITUS_LINE_2', 386, 446),  # Property address line 2
    ('SITUS_CITY', 446, 486),    # Property city
    ('SITUS_ZIP', 486, 496),     # Property ZIP
    ('USE_CODE', 496, 500),      # Property use code
    ('SUBDIVISION', 500, 600),   # Subdivision name
    ('PLAT_BOOK', 600, 604),     # Plat book number
    ('PLAT_PAGE', 604, 608),     # Plat page number
    ('LIVING_AREA', 608, 616),   # Living area sq ft
    ('YEAR_BUILT', 616, 620),    # Year built
    ('BEDROOMS', 620, 622),      # Number of bedrooms
    ('BATHROOMS', 622, 625),     # Number of bathrooms
    ('POOL', 625, 626),          # Pool flag
    ('JUST_VALUE', 626, 636),    # Just/market value
    ('TAXABLE_VALUE', 636, 646), # Taxable value
    ('LAND_VALUE', 646, 656),    # Land value
    ('BLDG_VALUE', 656, 666),    # Building value
]

# SDF Field Specifications (Sales Data File)
SDF_FIELDS = [
    ('FOLIO', 0, 23),             # Parcel ID
    ('SALE_DATE', 23, 31),        # Sale date YYYYMMDD
    ('SALE_PRICE', 31, 41),       # Sale price
    ('SALE_TYPE', 41, 43),        # Sale type code
    ('GRANTOR', 43, 143),         # Seller name
    ('GRANTEE', 143, 243),        # Buyer name
    ('BOOK', 243, 247),           # Record book
    ('PAGE', 247, 251),           # Record page
    ('INSTRUMENT', 251, 271),     # Instrument number
    ('QUALIFICATION', 271, 273),  # Qualification code
    ('VACANT_FLAG', 273, 274),    # Vacant at sale flag
    ('VI_CODE', 274, 276),        # Validity indicator
]

class DORProcessor:
    """Processes DOR NAL and SDF data files"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        self.data_dir = Path(os.getenv('DOR_DATA_DIR', '/data/dor'))
        self.pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self):
        """Initialize database connection"""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        
        # Create tables if needed
        await self.create_tables()
        
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            
    async def create_tables(self):
        """Create DOR data tables"""
        async with self.pool.acquire() as conn:
            # NAL table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dor_nal (
                    folio VARCHAR(23) PRIMARY KEY,
                    account_type VARCHAR(1),
                    owner_name VARCHAR(120),
                    mail_address_1 VARCHAR(60),
                    mail_address_2 VARCHAR(60),
                    mail_city VARCHAR(40),
                    mail_state VARCHAR(2),
                    mail_zip VARCHAR(10),
                    mail_country VARCHAR(10),
                    situs_address_1 VARCHAR(60),
                    situs_address_2 VARCHAR(60),
                    situs_city VARCHAR(40),
                    situs_zip VARCHAR(10),
                    use_code VARCHAR(4),
                    subdivision VARCHAR(100),
                    plat_book VARCHAR(4),
                    plat_page VARCHAR(4),
                    living_area INTEGER,
                    year_built INTEGER,
                    bedrooms INTEGER,
                    bathrooms NUMERIC(3,1),
                    has_pool BOOLEAN,
                    just_value NUMERIC(12,2),
                    taxable_value NUMERIC(12,2),
                    land_value NUMERIC(12,2),
                    building_value NUMERIC(12,2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # SDF table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dor_sales (
                    id SERIAL PRIMARY KEY,
                    folio VARCHAR(23),
                    sale_date DATE,
                    sale_price NUMERIC(12,2),
                    sale_type VARCHAR(2),
                    grantor VARCHAR(100),
                    grantee VARCHAR(100),
                    book VARCHAR(4),
                    page VARCHAR(4),
                    instrument VARCHAR(20),
                    qualification_code VARCHAR(2),
                    vacant_at_sale BOOLEAN,
                    validity_code VARCHAR(2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (folio) REFERENCES dor_nal(folio)
                )
            """)
            
            # Create indexes
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nal_owner 
                ON dor_nal(LOWER(owner_name))
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nal_use_code 
                ON dor_nal(use_code)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_nal_value 
                ON dor_nal(just_value DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sales_date 
                ON dor_sales(sale_date DESC)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_sales_price 
                ON dor_sales(sale_price DESC)
            """)
            
    def parse_fixed_width(self, file_path: Path, fields: List[tuple]) -> pl.DataFrame:
        """Parse fixed-width format file"""
        data = []
        
        with open(file_path, 'r', encoding='latin-1') as f:
            for line in f:
                if len(line.strip()) == 0:
                    continue
                    
                row = {}
                for field_name, start, end in fields:
                    value = line[start:end].strip()
                    row[field_name] = value
                    
                data.append(row)
                
        return pl.DataFrame(data)
        
    async def process_nal_file(self, file_path: Path) -> int:
        """Process NAL (Name & Address List) file"""
        logger.info(f"Processing NAL file: {file_path}")
        
        # Parse file
        df = self.parse_fixed_width(file_path, NAL_FIELDS)
        
        # Clean and transform data
        df = df.with_columns([
            # Clean numeric fields
            pl.col('JUST_VALUE').str.replace(',', '').cast(pl.Float64, strict=False),
            pl.col('TAXABLE_VALUE').str.replace(',', '').cast(pl.Float64, strict=False),
            pl.col('LAND_VALUE').str.replace(',', '').cast(pl.Float64, strict=False),
            pl.col('BLDG_VALUE').str.replace(',', '').cast(pl.Float64, strict=False),
            pl.col('LIVING_AREA').cast(pl.Int32, strict=False),
            pl.col('YEAR_BUILT').cast(pl.Int32, strict=False),
            pl.col('BEDROOMS').cast(pl.Int32, strict=False),
            pl.col('BATHROOMS').cast(pl.Float32, strict=False),
            # Convert pool flag
            (pl.col('POOL') == 'Y').alias('HAS_POOL'),
        ])
        
        # Insert to database
        count = 0
        async with self.pool.acquire() as conn:
            for row in df.iter_rows(named=True):
                try:
                    await conn.execute("""
                        INSERT INTO dor_nal (
                            folio, account_type, owner_name, 
                            mail_address_1, mail_address_2, mail_city, 
                            mail_state, mail_zip, mail_country,
                            situs_address_1, situs_address_2, situs_city, situs_zip,
                            use_code, subdivision, plat_book, plat_page,
                            living_area, year_built, bedrooms, bathrooms, has_pool,
                            just_value, taxable_value, land_value, building_value
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                                 $11, $12, $13, $14, $15, $16, $17, $18, $19,
                                 $20, $21, $22, $23, $24, $25, $26)
                        ON CONFLICT (folio) DO UPDATE SET
                            owner_name = EXCLUDED.owner_name,
                            mail_address_1 = EXCLUDED.mail_address_1,
                            mail_address_2 = EXCLUDED.mail_address_2,
                            mail_city = EXCLUDED.mail_city,
                            mail_state = EXCLUDED.mail_state,
                            mail_zip = EXCLUDED.mail_zip,
                            situs_address_1 = EXCLUDED.situs_address_1,
                            situs_address_2 = EXCLUDED.situs_address_2,
                            situs_city = EXCLUDED.situs_city,
                            situs_zip = EXCLUDED.situs_zip,
                            use_code = EXCLUDED.use_code,
                            living_area = EXCLUDED.living_area,
                            year_built = EXCLUDED.year_built,
                            bedrooms = EXCLUDED.bedrooms,
                            bathrooms = EXCLUDED.bathrooms,
                            has_pool = EXCLUDED.has_pool,
                            just_value = EXCLUDED.just_value,
                            taxable_value = EXCLUDED.taxable_value,
                            land_value = EXCLUDED.land_value,
                            building_value = EXCLUDED.building_value,
                            updated_at = NOW()
                    """,
                        row['FOLIO'], row['ACCOUNT_TYPE'], row['OWNER_NAME'],
                        row['MAIL_LINE_1'], row['MAIL_LINE_2'], row['MAIL_CITY'],
                        row['MAIL_STATE'], row['MAIL_ZIP'], row['MAIL_COUNTRY'],
                        row['SITUS_LINE_1'], row['SITUS_LINE_2'], row['SITUS_CITY'],
                        row['SITUS_ZIP'], row['USE_CODE'], row['SUBDIVISION'],
                        row['PLAT_BOOK'], row['PLAT_PAGE'], row['LIVING_AREA'],
                        row['YEAR_BUILT'], row['BEDROOMS'], row['BATHROOMS'],
                        row['HAS_POOL'], row['JUST_VALUE'], row['TAXABLE_VALUE'],
                        row['LAND_VALUE'], row['BLDG_VALUE']
                    )
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting NAL record {row['FOLIO']}: {e}")
                    
        logger.info(f"Processed {count} NAL records")
        return count
        
    async def process_sdf_file(self, file_path: Path) -> int:
        """Process SDF (Sales Data File)"""
        logger.info(f"Processing SDF file: {file_path}")
        
        # Parse file
        df = self.parse_fixed_width(file_path, SDF_FIELDS)
        
        # Clean and transform data
        df = df.with_columns([
            # Parse date
            pl.col('SALE_DATE').str.strptime(pl.Date, format='%Y%m%d', strict=False),
            # Clean numeric fields
            pl.col('SALE_PRICE').str.replace(',', '').cast(pl.Float64, strict=False),
            # Convert flags
            (pl.col('VACANT_FLAG') == 'Y').alias('VACANT_AT_SALE'),
        ])
        
        # Filter qualified sales (arms-length transactions)
        qualified_codes = ['Q', 'U']  # Qualified and Unqualified but usable
        df = df.filter(pl.col('QUALIFICATION').is_in(qualified_codes))
        
        # Insert to database
        count = 0
        async with self.pool.acquire() as conn:
            for row in df.iter_rows(named=True):
                try:
                    await conn.execute("""
                        INSERT INTO dor_sales (
                            folio, sale_date, sale_price, sale_type,
                            grantor, grantee, book, page, instrument,
                            qualification_code, vacant_at_sale, validity_code
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                    """,
                        row['FOLIO'], row['SALE_DATE'], row['SALE_PRICE'],
                        row['SALE_TYPE'], row['GRANTOR'], row['GRANTEE'],
                        row['BOOK'], row['PAGE'], row['INSTRUMENT'],
                        row['QUALIFICATION'], row['VACANT_AT_SALE'], row['VI_CODE']
                    )
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error inserting SDF record: {e}")
                    
        logger.info(f"Processed {count} SDF records")
        return count
        
    async def process_directory(self, directory: Path = None) -> Dict[str, int]:
        """Process all NAL and SDF files in directory"""
        if directory is None:
            directory = self.data_dir
            
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return {}
            
        results = {}
        
        # Process NAL files
        nal_files = list(directory.glob('*NAL*.txt')) + list(directory.glob('*NAL*.dat'))
        for nal_file in nal_files:
            count = await self.process_nal_file(nal_file)
            results[nal_file.name] = count
            
        # Process SDF files  
        sdf_files = list(directory.glob('*SDF*.txt')) + list(directory.glob('*SDF*.dat'))
        for sdf_file in sdf_files:
            count = await self.process_sdf_file(sdf_file)
            results[sdf_file.name] = count
            
        return results
        
    async def analyze_data(self):
        """Analyze processed DOR data"""
        async with self.pool.acquire() as conn:
            # Count records
            nal_count = await conn.fetchval("SELECT COUNT(*) FROM dor_nal")
            sdf_count = await conn.fetchval("SELECT COUNT(*) FROM dor_sales")
            
            logger.info(f"Database contains {nal_count} NAL records and {sdf_count} sales records")
            
            # Top value properties
            top_properties = await conn.fetch("""
                SELECT folio, owner_name, just_value, use_code
                FROM dor_nal
                ORDER BY just_value DESC
                LIMIT 10
            """)
            
            logger.info("Top 10 properties by value:")
            for prop in top_properties:
                logger.info(f"  {prop['folio']}: ${prop['just_value']:,.0f} - {prop['owner_name']}")
                
            # Recent high-value sales
            recent_sales = await conn.fetch("""
                SELECT s.*, n.owner_name, n.use_code
                FROM dor_sales s
                JOIN dor_nal n ON s.folio = n.folio
                WHERE s.sale_date >= CURRENT_DATE - INTERVAL '90 days'
                  AND s.sale_price > 1000000
                ORDER BY s.sale_date DESC
                LIMIT 10
            """)
            
            logger.info("Recent high-value sales:")
            for sale in recent_sales:
                logger.info(
                    f"  {sale['sale_date']}: ${sale['sale_price']:,.0f} - "
                    f"{sale['grantee']} bought from {sale['grantor']}"
                )


async def main():
    """Run DOR processor"""
    processor = DORProcessor()
    
    try:
        await processor.initialize()
        
        # Check for data files
        data_dir = Path(os.getenv('DOR_DATA_DIR', '/data/dor'))
        
        if data_dir.exists():
            logger.info(f"Processing DOR data from: {data_dir}")
            results = await processor.process_directory(data_dir)
            
            logger.info("Processing complete:")
            for filename, count in results.items():
                logger.info(f"  {filename}: {count} records")
                
            # Analyze data
            await processor.analyze_data()
        else:
            logger.warning(f"DOR data directory not found: {data_dir}")
            logger.info("Waiting for DOR data files...")
            logger.info("Place NAL and SDF files in the data directory to process")
            
            # Watch directory for new files
            while True:
                if data_dir.exists() and any(data_dir.glob('*.txt')):
                    logger.info("New files detected, processing...")
                    results = await processor.process_directory(data_dir)
                    await processor.analyze_data()
                    break
                    
                await asyncio.sleep(60)  # Check every minute
                
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())