#!/usr/bin/env python3
"""
Broward County NAL Data Import Pipeline
Imports NAL property data into Supabase with address-based organization
"""

import os
import sys
import csv
import asyncio
import asyncpg
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NALDataImporter:
    """Import NAL property data with address-based organization"""
    
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.batch_size = 1000
        self.imported_count = 0
        self.updated_count = 0
        self.error_count = 0
        
    async def connect_db(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = await asyncpg.connect(self.db_url)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def close_db(self):
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            await self.conn.close()
            logger.info("Database connection closed")

    def load_nal_data(self, file_path: str) -> pd.DataFrame:
        """Load NAL CSV data"""
        logger.info(f"Loading NAL data from {file_path}")
        
        try:
            # Load with proper encoding and error handling
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                low_memory=False,
                dtype=str,  # Load all as strings initially
                na_values=['', ' ', 'NULL', 'null', 'N/A']
            )
            
            logger.info(f"Loaded {len(df)} records from NAL file")
            return df
            
        except Exception as e:
            logger.error(f"Error loading NAL data: {e}")
            raise

    def transform_property_record(self, row: pd.Series) -> Dict[str, Any]:
        """Transform NAL row to property record with address focus"""
        
        def safe_float(value, default=None):
            try:
                return float(value) if pd.notna(value) and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        def safe_int(value, default=None):
            try:
                return int(float(value)) if pd.notna(value) and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        def clean_string(value, max_length=None):
            if pd.isna(value):
                return None
            cleaned = str(value).strip()
            if not cleaned:
                return None
            if max_length and len(cleaned) > max_length:
                cleaned = cleaned[:max_length].strip()
            return cleaned

        # Core property record with address as primary organization
        record = {
            # Primary identifiers
            'parcel_id': clean_string(row.get('PARCEL_ID')),
            
            # Address (Primary Organization Method)
            'phy_addr1': clean_string(row.get('PHY_ADDR1'), 255),
            'phy_addr2': clean_string(row.get('PHY_ADDR2'), 255),
            'phy_city': clean_string(row.get('PHY_CITY'), 100),
            'phy_zipcd': clean_string(row.get('PHY_ZIPCD'), 10),
            
            # Property Classification
            'dor_uc': clean_string(row.get('DOR_UC'), 4),
            
            # Core Values
            'jv': safe_float(row.get('JV')),  # Just/Market Value
            'av_sd': safe_float(row.get('AV_SD')),  # Assessed Value School
            'tv_sd': safe_float(row.get('TV_SD')),  # Taxable Value School
            'av_nsd': safe_float(row.get('AV_NSD')),  # Assessed Value Non-School
            'tv_nsd': safe_float(row.get('TV_NSD')),  # Taxable Value Non-School
            'lnd_val': safe_float(row.get('LND_VAL')),  # Land Value
            
            # Owner Information
            'own_name': clean_string(row.get('OWN_NAME'), 255),
            'own_addr1': clean_string(row.get('OWN_ADDR1'), 255),
            'own_addr2': clean_string(row.get('OWN_ADDR2'), 255),
            'own_city': clean_string(row.get('OWN_CITY'), 100),
            'own_state': clean_string(row.get('OWN_STATE'), 50),
            'own_zipcd': clean_string(row.get('OWN_ZIPCD'), 10),
            
            # Physical Characteristics
            'lnd_sqfoot': safe_int(row.get('LND_SQFOOT')),
            'tot_lvg_area': safe_int(row.get('TOT_LVG_AREA')),
            'act_yr_blt': safe_int(row.get('ACT_YR_BLT')),
            'eff_yr_blt': safe_int(row.get('EFF_YR_BLT')),
            'no_buldng': safe_int(row.get('NO_BULDNG')),
            'no_res_unts': safe_int(row.get('NO_RES_UNTS')),
            
            # Geographic/Legal
            'section_num': safe_int(row.get('SECTION_NUM')),
            'township': clean_string(row.get('TOWNSHIP'), 10),
            'range': clean_string(row.get('RANGE'), 10),
            'census_block': clean_string(row.get('CENSUS_BLOCK'), 20),
            'nbrhd_cd': clean_string(row.get('NBRHD_CD'), 10),
            
            # Metadata
            'co_no': safe_int(row.get('CO_NO', 16)),  # Broward County
            'asmnt_yr': safe_int(row.get('ASMNT_YR')),
            'file_t': clean_string(row.get('FILE_T', 'R'), 1),
            'source_file': 'NAL_IMPORT',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        return record

    def transform_sales_record(self, row: pd.Series, property_id: int) -> Optional[Dict[str, Any]]:
        """Transform NAL row to sales record if sale data exists"""
        
        def safe_float(value, default=None):
            try:
                return float(value) if pd.notna(value) and str(value).strip() else default
            except (ValueError, TypeError):
                return default
        
        def clean_string(value, max_length=None):
            if pd.isna(value):
                return None
            cleaned = str(value).strip()
            if not cleaned:
                return None
            if max_length and len(cleaned) > max_length:
                cleaned = cleaned[:max_length].strip()
            return cleaned
        
        def parse_date(date_str):
            if pd.isna(date_str) or not str(date_str).strip():
                return None
            try:
                # Try common date formats
                for fmt in ['%Y%m%d', '%m/%d/%Y', '%Y-%m-%d']:
                    try:
                        return datetime.strptime(str(date_str).strip(), fmt).date()
                    except ValueError:
                        continue
                return None
            except Exception:
                return None

        # Check if there's sale data
        sale_price = safe_float(row.get('SALE_PRICE'))
        sale_date = parse_date(row.get('SALE_DATE'))
        
        if not sale_price and not sale_date:
            return None
        
        return {
            'property_id': property_id,
            'parcel_id': clean_string(row.get('PARCEL_ID')),
            'sale_date': sale_date,
            'sale_price': sale_price,
            'sale_type': clean_string(row.get('SALE_TYPE'), 50),
            'qual_cd': clean_string(row.get('QUAL_CD'), 2),
            'vi_cd': clean_string(row.get('VI_CD'), 2),
            'grantor': clean_string(row.get('GRANTOR'), 255),
            'grantee': clean_string(row.get('GRANTEE'), 255),
            'or_book': clean_string(row.get('OR_BOOK'), 10),
            'or_page': clean_string(row.get('OR_PAGE'), 10),
            'clerk_no': clean_string(row.get('CLERK_NO'), 20),
            'multi_parcel_sale': False,  # Default, could be determined by logic
            'created_at': datetime.now()
        }

    async def import_property_batch(self, batch: List[Dict[str, Any]]) -> List[int]:
        """Import a batch of property records, return property IDs"""
        
        property_ids = []
        
        for record in batch:
            try:
                # Check if property exists by parcel_id
                existing = await self.conn.fetchrow(
                    "SELECT id FROM properties WHERE parcel_id = $1",
                    record['parcel_id']
                )
                
                if existing:
                    # Update existing property
                    update_fields = []
                    update_values = []
                    param_count = 1
                    
                    for key, value in record.items():
                        if key not in ['parcel_id', 'created_at']:
                            if key == 'updated_at':
                                value = datetime.now()
                            update_fields.append(f"{key} = ${param_count}")
                            update_values.append(value)
                            param_count += 1
                    
                    update_values.append(record['parcel_id'])  # WHERE clause
                    
                    update_query = f"""
                        UPDATE properties 
                        SET {', '.join(update_fields)}
                        WHERE parcel_id = ${param_count}
                        RETURNING id
                    """
                    
                    result = await self.conn.fetchrow(update_query, *update_values)
                    property_ids.append(result['id'])
                    self.updated_count += 1
                    
                else:
                    # Insert new property
                    columns = list(record.keys())
                    placeholders = [f'${i+1}' for i in range(len(columns))]
                    values = [record[col] for col in columns]
                    
                    insert_query = f"""
                        INSERT INTO properties ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                        RETURNING id
                    """
                    
                    result = await self.conn.fetchrow(insert_query, *values)
                    property_ids.append(result['id'])
                    self.imported_count += 1
                
            except Exception as e:
                logger.error(f"Error importing property {record.get('parcel_id')}: {e}")
                self.error_count += 1
        
        return property_ids

    async def import_sales_batch(self, sales_records: List[Dict[str, Any]]):
        """Import sales records"""
        
        for record in sales_records:
            try:
                # Check if sale exists
                existing = await self.conn.fetchrow(
                    """SELECT id FROM property_sales 
                       WHERE property_id = $1 AND sale_date = $2 AND sale_price = $3""",
                    record['property_id'], record['sale_date'], record['sale_price']
                )
                
                if not existing:
                    columns = list(record.keys())
                    placeholders = [f'${i+1}' for i in range(len(columns))]
                    values = [record[col] for col in columns]
                    
                    insert_query = f"""
                        INSERT INTO property_sales ({', '.join(columns)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    await self.conn.execute(insert_query, *values)
                    
            except Exception as e:
                logger.error(f"Error importing sale for property {record.get('property_id')}: {e}")

    async def import_nal_file(self, file_path: str):
        """Import complete NAL file with address-based organization"""
        
        logger.info("Starting NAL import process")
        start_time = datetime.now()
        
        # Load data
        df = self.load_nal_data(file_path)
        total_records = len(df)
        
        # Process in batches
        property_batch = []
        sales_batch = []
        
        for idx, (_, row) in enumerate(df.iterrows()):
            # Transform property record
            property_record = self.transform_property_record(row)
            
            # Skip if no valid address or parcel ID
            if not property_record.get('parcel_id'):
                logger.warning(f"Row {idx}: Missing parcel_id, skipping")
                continue
            
            property_batch.append(property_record)
            
            # Process batch when full
            if len(property_batch) >= self.batch_size:
                property_ids = await self.import_property_batch(property_batch)
                
                # Process sales records for this batch
                sales_records = []
                for i, prop_record in enumerate(property_batch):
                    if i < len(property_ids):
                        sales_record = self.transform_sales_record(
                            df.iloc[idx - self.batch_size + i + 1], 
                            property_ids[i]
                        )
                        if sales_record:
                            sales_records.append(sales_record)
                
                if sales_records:
                    await self.import_sales_batch(sales_records)
                
                # Clear batches
                property_batch = []
                
                # Log progress
                processed = idx + 1
                progress = (processed / total_records) * 100
                logger.info(f"Progress: {processed}/{total_records} ({progress:.1f}%)")
        
        # Process remaining records
        if property_batch:
            property_ids = await self.import_property_batch(property_batch)
            
            sales_records = []
            for i, prop_record in enumerate(property_batch):
                if i < len(property_ids):
                    sales_record = self.transform_sales_record(
                        df.iloc[total_records - len(property_batch) + i], 
                        property_ids[i]
                    )
                    if sales_record:
                        sales_records.append(sales_record)
            
            if sales_records:
                await self.import_sales_batch(sales_records)
        
        # Log final results
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info("=" * 50)
        logger.info("NAL IMPORT COMPLETED")
        logger.info(f"Total records processed: {total_records}")
        logger.info(f"Properties imported: {self.imported_count}")
        logger.info(f"Properties updated: {self.updated_count}")
        logger.info(f"Errors: {self.error_count}")
        logger.info(f"Duration: {duration}")
        logger.info("=" * 50)

async def main():
    """Main import function"""
    
    # Default file path
    default_file = project_root / "TEMP" / "NAL16P202501.csv"
    
    file_path = sys.argv[1] if len(sys.argv) > 1 else str(default_file)
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        sys.exit(1)
    
    importer = NALDataImporter()
    
    try:
        await importer.connect_db()
        await importer.import_nal_file(file_path)
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
        
    finally:
        await importer.close_db()

if __name__ == "__main__":
    asyncio.run(main())