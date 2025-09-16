#!/usr/bin/env python3
"""
Florida Parcels Data Import Script
==================================

Imports NAL (Name and Address Listing) and NAP (Name and Property) data
into Supabase florida_parcels table with efficient batch processing.

This script handles:
- Large file processing (387MB NAL file)
- Data cleaning and validation
- UPSERT operations to avoid duplicates
- Proper data type conversion
- Progress tracking
- Error handling and recovery
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_parcels_import.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class FloridaParcelsImporter:
    def __init__(self):
        """Initialize the importer with database connection."""
        load_dotenv('apps/web/.env')
        
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials. Check apps/web/.env file.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # File paths
        self.nal_file = 'TEMP/NAL16P202501.csv'
        self.nap_file = 'TEMP/NAP16P202501.csv'
        
        # Batch processing settings
        self.batch_size = 500  # Process 500 records at a time
        self.max_retries = 3
        
        # Statistics
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    def safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to integer."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return None
                # Remove any non-numeric characters except minus sign
                value = ''.join(c for c in value if c.isdigit() or c == '-')
                if value == '' or value == '-':
                    return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def safe_bigint(self, value: Any) -> Optional[int]:
        """Safely convert value to bigint (for monetary values)."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return None
                # Remove any non-numeric characters except minus sign and decimal
                value = ''.join(c for c in value if c.isdigit() or c == '-' or c == '.')
                if value == '' or value == '-':
                    return None
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if pd.isna(value) or value == '' or value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if value == '':
                    return None
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def safe_str(self, value: Any) -> Optional[str]:
        """Safely convert value to string."""
        if pd.isna(value) or value is None:
            return None
        value = str(value).strip()
        return value if value != '' else None
    
    def parse_sale_date(self, year: Any, month: Any) -> Optional[str]:
        """Parse sale date from year and month."""
        year_int = self.safe_int(year)
        month_int = self.safe_int(month)
        
        if not year_int or year_int < 1900 or year_int > 2030:
            return None
        if not month_int or month_int < 1 or month_int > 12:
            return None
            
        try:
            sale_date = date(year_int, month_int, 1)
            return sale_date.isoformat()
        except ValueError:
            return None
    
    def clean_address(self, address: str) -> Optional[str]:
        """Clean and standardize address."""
        if not address:
            return None
        
        # Remove extra whitespace
        address = ' '.join(address.split())
        
        # Convert to title case for better readability
        address = address.title()
        
        # Fix common abbreviations
        address = address.replace(' St ', ' ST ')
        address = address.replace(' Rd ', ' RD ')
        address = address.replace(' Ave ', ' AVE ')
        address = address.replace(' Dr ', ' DR ')
        address = address.replace(' Ln ', ' LN ')
        address = address.replace(' Ct ', ' CT ')
        address = address.replace(' Pl ', ' PL ')
        address = address.replace(' Blvd ', ' BLVD ')
        
        return address
    
    def estimate_bedrooms_bathrooms(self, living_area: Optional[int], year_built: Optional[int], 
                                  property_use: Optional[str]) -> tuple[Optional[int], Optional[float]]:
        """Estimate bedrooms and bathrooms based on living area and property type."""
        if not living_area or living_area < 500:
            return None, None
        
        bedrooms = None
        bathrooms = None
        
        # Estimate based on property type
        if property_use and any(x in property_use.upper() for x in ['SINGLE', 'RESIDENTIAL', 'HOME', 'HOUSE']):
            if living_area < 800:
                bedrooms, bathrooms = 2, 1.0
            elif living_area < 1200:
                bedrooms, bathrooms = 3, 2.0
            elif living_area < 1800:
                bedrooms, bathrooms = 3, 2.0
            elif living_area < 2500:
                bedrooms, bathrooms = 4, 2.5
            else:
                bedrooms, bathrooms = 4, 3.0
        elif property_use and 'CONDO' in property_use.upper():
            if living_area < 700:
                bedrooms, bathrooms = 1, 1.0
            elif living_area < 1100:
                bedrooms, bathrooms = 2, 2.0
            else:
                bedrooms, bathrooms = 3, 2.0
        
        return bedrooms, bathrooms
    
    def transform_nal_record(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a NAL CSV row into florida_parcels table format."""
        # Parse sale date
        sale_date = self.parse_sale_date(row.get('SALE_YR1'), row.get('SALE_MO1'))
        
        # Estimate bedrooms/bathrooms
        living_area = self.safe_int(row.get('TOT_LVG_AREA'))
        year_built = self.safe_int(row.get('ACT_YR_BLT'))
        property_use = self.safe_str(row.get('DOR_UC'))
        bedrooms, bathrooms = self.estimate_bedrooms_bathrooms(living_area, year_built, property_use)
        
        # Clean addresses
        phy_addr1 = self.clean_address(self.safe_str(row.get('PHY_ADDR1')))
        owner_name = self.safe_str(row.get('OWN_NAME'))
        
        # Create full address for frontend compatibility
        property_address_full = None
        if phy_addr1:
            city = self.safe_str(row.get('PHY_CITY'))
            zipcode = self.safe_str(row.get('PHY_ZIPCD'))
            property_address_full = f"{phy_addr1}"
            if city:
                property_address_full += f", {city}"
            property_address_full += ", FL"
            if zipcode:
                property_address_full += f" {zipcode}"
        
        # Transform the record
        transformed = {
            # Core identifiers
            'co_no': self.safe_int(row.get('CO_NO')),
            'parcel_id': self.safe_str(row.get('PARCEL_ID')),
            'file_t': self.safe_str(row.get('FILE_T')),
            'asmnt_yr': self.safe_int(row.get('ASMNT_YR')),
            
            # Geographic
            'twn': self.safe_str(row.get('TWN')),
            'rng': self.safe_str(row.get('RNG')),
            'sec': self.safe_str(row.get('SEC')),
            'census_bk': self.safe_str(row.get('CENSUS_BK')),
            
            # Physical address
            'phy_addr1': phy_addr1,
            'phy_addr2': self.clean_address(self.safe_str(row.get('PHY_ADDR2'))),
            'phy_city': self.safe_str(row.get('PHY_CITY')),
            'phy_zipcd': self.safe_str(row.get('PHY_ZIPCD')),
            
            # Owner information
            'owner_name': owner_name,
            'owner_addr1': self.safe_str(row.get('OWN_ADDR1')),
            'owner_addr2': self.safe_str(row.get('OWN_ADDR2')),
            'owner_city': self.safe_str(row.get('OWN_CITY')),
            'owner_state': self.safe_str(row.get('OWN_STATE')),
            'owner_zip': self.safe_str(row.get('OWN_ZIPCD')),
            'owner_state_dom': self.safe_str(row.get('OWN_STATE_DOM')),
            
            # Fiduciary info
            'fidu_name': self.safe_str(row.get('FIDU_NAME')),
            'fidu_addr1': self.safe_str(row.get('FIDU_ADDR1')),
            'fidu_addr2': self.safe_str(row.get('FIDU_ADDR2')),
            'fidu_city': self.safe_str(row.get('FIDU_CITY')),
            'fidu_state': self.safe_str(row.get('FIDU_STATE')),
            'fidu_zipcd': self.safe_str(row.get('FIDU_ZIPCD')),
            'fidu_cd': self.safe_str(row.get('FIDU_CD')),
            
            # Property values
            'just_value': self.safe_bigint(row.get('JV')),
            'taxable_value': self.safe_bigint(row.get('TV_SD')),
            'assessed_value': self.safe_bigint(row.get('AV_SD')),
            'land_value': self.safe_bigint(row.get('LND_VAL')),
            'building_value': None,  # Calculate from just_value - land_value if needed
            
            # Homestead and exemptions
            'jv_hmstd': self.safe_bigint(row.get('JV_HMSTD')),
            'av_hmstd': self.safe_bigint(row.get('AV_HMSTD')),
            'homestead_exemption': 'Y' if self.safe_bigint(row.get('JV_HMSTD')) and self.safe_bigint(row.get('JV_HMSTD')) > 0 else 'N',
            
            # Property characteristics
            'property_use': self.safe_str(row.get('DOR_UC')),
            'pa_uc': self.safe_str(row.get('PA_UC')),
            
            # Building details
            'year_built': year_built,
            'eff_year_built': self.safe_int(row.get('EFF_YR_BLT')),
            'total_living_area': living_area,
            'no_buldng': self.safe_int(row.get('NO_BULDNG')),
            'no_res_unts': self.safe_int(row.get('NO_RES_UNTS')),
            
            # Land characteristics
            'land_sqft': self.safe_bigint(row.get('LND_SQFOOT')),
            'lnd_unts_cd': self.safe_str(row.get('LND_UNTS_CD')),
            'no_lnd_unts': self.safe_int(row.get('NO_LND_UNTS')),
            
            # Building quality
            'imp_qual': self.safe_str(row.get('IMP_QUAL')),
            'const_class': self.safe_str(row.get('CONST_CLASS')),
            'spec_feat_val': self.safe_bigint(row.get('SPEC_FEAT_VAL')),
            
            # Sale information
            'sale_price': self.safe_bigint(row.get('SALE_PRC1')),
            'sale_date': sale_date,
            'sale_yr1': self.safe_int(row.get('SALE_YR1')),
            'sale_mo1': self.safe_int(row.get('SALE_MO1')),
            'qual_cd1': self.safe_str(row.get('QUAL_CD1')),
            'vi_cd1': self.safe_str(row.get('VI_CD1')),
            'or_book1': self.safe_str(row.get('OR_BOOK1')),
            'or_page1': self.safe_str(row.get('OR_PAGE1')),
            'clerk_no1': self.safe_str(row.get('CLERK_NO1')),
            'sal_chng_cd1': self.safe_str(row.get('SAL_CHNG_CD1')),
            'multi_par_sal1': self.safe_str(row.get('MULTI_PAR_SAL1')),
            
            # Second sale
            'sale_prc2': self.safe_bigint(row.get('SALE_PRC2')),
            'sale_yr2': self.safe_int(row.get('SALE_YR2')),
            'sale_mo2': self.safe_int(row.get('SALE_MO2')),
            'qual_cd2': self.safe_str(row.get('QUAL_CD2')),
            'vi_cd2': self.safe_str(row.get('VI_CD2')),
            'or_book2': self.safe_str(row.get('OR_BOOK2')),
            'or_page2': self.safe_str(row.get('OR_PAGE2')),
            'clerk_no2': self.safe_str(row.get('CLERK_NO2')),
            
            # Legal description
            's_legal': self.safe_str(row.get('S_LEGAL')),
            
            # Assessment info
            'app_stat': self.safe_str(row.get('APP_STAT')),
            'co_app_stat': self.safe_str(row.get('CO_APP_STAT')),
            'mkt_ar': self.safe_str(row.get('MKT_AR')),
            'nbrhd_cd': self.safe_str(row.get('NBRHD_CD')),
            
            # Additional fields
            'alt_key': self.safe_str(row.get('ALT_KEY')),
            'public_lnd': self.safe_str(row.get('PUBLIC_LND')),
            'tax_auth_cd': self.safe_str(row.get('TAX_AUTH_CD')),
            'dt_last_inspt': self.safe_str(row.get('DT_LAST_INSPT')),
            
            # Assessment transfer
            'ass_trnsfr_fg': self.safe_str(row.get('ASS_TRNSFR_FG')),
            'prev_hmstd_own': self.safe_str(row.get('PREV_HMSTD_OWN')),
            'ass_dif_trns': self.safe_bigint(row.get('ASS_DIF_TRNS')),
            'cono_prv_hm': self.safe_str(row.get('CONO_PRV_HM')),
            'parcel_id_prv_hmstd': self.safe_str(row.get('PARCEL_ID_PRV_HMSTD')),
            'yr_val_trnsf': self.safe_int(row.get('YR_VAL_TRNSF')),
            
            # Record info
            'seq_no': self.safe_int(row.get('SEQ_NO')),
            'rs_id': self.safe_str(row.get('RS_ID')),
            'mp_id': self.safe_str(row.get('MP_ID')),
            'state_par_id': self.safe_str(row.get('STATE_PAR_ID')),
            'spc_cir_cd': self.safe_str(row.get('SPC_CIR_CD')),
            'spc_cir_yr': self.safe_int(row.get('SPC_CIR_YR')),
            'spc_cir_txt': self.safe_str(row.get('SPC_CIR_TXT')),
            
            # Frontend compatibility fields
            'property_address_full': property_address_full,
            'market_value': self.safe_bigint(row.get('JV')),  # Alias for just_value
            'bedrooms': bedrooms,
            'bathrooms': bathrooms,
            'units': self.safe_int(row.get('NO_RES_UNTS')) or 1,
            'stories': 1,  # Default, can be estimated later
            
            # All exemption codes
            'exmpt_01': self.safe_bigint(row.get('EXMPT_01')),
            'exmpt_02': self.safe_bigint(row.get('EXMPT_02')),
            'exmpt_03': self.safe_bigint(row.get('EXMPT_03')),
            'exmpt_04': self.safe_bigint(row.get('EXMPT_04')),
            'exmpt_05': self.safe_bigint(row.get('EXMPT_05')),
            'exmpt_06': self.safe_bigint(row.get('EXMPT_06')),
            'exmpt_07': self.safe_bigint(row.get('EXMPT_07')),
            'exmpt_08': self.safe_bigint(row.get('EXMPT_08')),
            'exmpt_09': self.safe_bigint(row.get('EXMPT_09')),
            'exmpt_10': self.safe_bigint(row.get('EXMPT_10')),
            'exmpt_11': self.safe_bigint(row.get('EXMPT_11')),
            'exmpt_12': self.safe_bigint(row.get('EXMPT_12')),
            'exmpt_13': self.safe_bigint(row.get('EXMPT_13')),
            'exmpt_14': self.safe_bigint(row.get('EXMPT_14')),
            'exmpt_15': self.safe_bigint(row.get('EXMPT_15')),
            'exmpt_16': self.safe_bigint(row.get('EXMPT_16')),
            'exmpt_17': self.safe_bigint(row.get('EXMPT_17')),
            'exmpt_18': self.safe_bigint(row.get('EXMPT_18')),
            'exmpt_19': self.safe_bigint(row.get('EXMPT_19')),
            'exmpt_20': self.safe_bigint(row.get('EXMPT_20')),
            'exmpt_21': self.safe_bigint(row.get('EXMPT_21')),
            'exmpt_22': self.safe_bigint(row.get('EXMPT_22')),
            'exmpt_23': self.safe_bigint(row.get('EXMPT_23')),
            'exmpt_24': self.safe_bigint(row.get('EXMPT_24')),
            'exmpt_25': self.safe_bigint(row.get('EXMPT_25')),
            'exmpt_26': self.safe_bigint(row.get('EXMPT_26')),
            'exmpt_27': self.safe_bigint(row.get('EXMPT_27')),
            'exmpt_28': self.safe_bigint(row.get('EXMPT_28')),
            'exmpt_29': self.safe_bigint(row.get('EXMPT_29')),
            'exmpt_30': self.safe_bigint(row.get('EXMPT_30')),
            'exmpt_31': self.safe_bigint(row.get('EXMPT_31')),
            'exmpt_32': self.safe_bigint(row.get('EXMPT_32')),
            'exmpt_33': self.safe_bigint(row.get('EXMPT_33')),
            'exmpt_34': self.safe_bigint(row.get('EXMPT_34')),
            'exmpt_35': self.safe_bigint(row.get('EXMPT_35')),
            'exmpt_36': self.safe_bigint(row.get('EXMPT_36')),
            'exmpt_37': self.safe_bigint(row.get('EXMPT_37')),
            'exmpt_38': self.safe_bigint(row.get('EXMPT_38')),
            'exmpt_39': self.safe_bigint(row.get('EXMPT_39')),
            'exmpt_40': self.safe_bigint(row.get('EXMPT_40')),
            'exmpt_41': self.safe_bigint(row.get('EXMPT_41')),
            'exmpt_42': self.safe_bigint(row.get('EXMPT_42')),
            'exmpt_43': self.safe_bigint(row.get('EXMPT_43')),
            'exmpt_44': self.safe_bigint(row.get('EXMPT_44')),
            'exmpt_45': self.safe_bigint(row.get('EXMPT_45')),
            'exmpt_46': self.safe_bigint(row.get('EXMPT_46')),
            'exmpt_80': self.safe_bigint(row.get('EXMPT_80')),
            'exmpt_81': self.safe_bigint(row.get('EXMPT_81')),
            'exmpt_82': self.safe_bigint(row.get('EXMPT_82')),
        }
        
        # Calculate building value if we have just_value and land_value
        if transformed['just_value'] and transformed['land_value']:
            transformed['building_value'] = max(0, transformed['just_value'] - transformed['land_value'])
        
        return transformed
    
    def create_table(self):
        """Create the florida_parcels table using the SQL schema."""
        logger.info("Creating florida_parcels table...")
        
        try:
            with open('create_florida_parcels_schema.sql', 'r') as f:
                schema_sql = f.read()
            
            # Execute the schema creation
            # Note: Supabase Python client doesn't support raw SQL execution
            # So we'll just log that the schema should be run manually
            logger.info("Please run the SQL schema manually in Supabase SQL editor:")
            logger.info("File: create_florida_parcels_schema.sql")
            
        except FileNotFoundError:
            logger.error("Schema file not found. Please create create_florida_parcels_schema.sql")
            raise
    
    def process_nal_file(self):
        """Process the NAL file in batches."""
        logger.info(f"Starting NAL file processing: {self.nal_file}")
        
        if not os.path.exists(self.nal_file):
            logger.error(f"NAL file not found: {self.nal_file}")
            return False
        
        batch = []
        batch_num = 0
        
        try:
            # Use pandas for efficient CSV reading
            chunk_size = self.batch_size
            
            for chunk in pd.read_csv(self.nal_file, chunksize=chunk_size, dtype=str):
                batch_num += 1
                logger.info(f"Processing batch {batch_num} ({len(chunk)} records)")
                
                # Transform records
                batch_records = []
                for _, row in chunk.iterrows():
                    try:
                        transformed = self.transform_nal_record(row.to_dict())
                        if transformed['parcel_id']:  # Only include records with valid parcel_id
                            batch_records.append(transformed)
                    except Exception as e:
                        logger.error(f"Error transforming record: {e}")
                        self.stats['errors'] += 1
                
                # Insert batch
                if batch_records:
                    success = self.insert_batch(batch_records)
                    if success:
                        self.stats['processed'] += len(batch_records)
                        logger.info(f"Batch {batch_num} completed: {len(batch_records)} records")
                    else:
                        logger.error(f"Batch {batch_num} failed")
                
                # Progress report every 10 batches
                if batch_num % 10 == 0:
                    logger.info(f"Progress: {self.stats['processed']} records processed")
            
        except Exception as e:
            logger.error(f"Error processing NAL file: {e}")
            return False
        
        return True
    
    def insert_batch(self, records: List[Dict[str, Any]]) -> bool:
        """Insert a batch of records using UPSERT."""
        for attempt in range(self.max_retries):
            try:
                # Use upsert to handle duplicates
                result = self.supabase.table('florida_parcels').upsert(
                    records,
                    on_conflict='parcel_id'
                ).execute()
                
                if result.data:
                    self.stats['inserted'] += len(records)
                    return True
                else:
                    logger.warning(f"Upsert returned no data (attempt {attempt + 1})")
                
            except Exception as e:
                logger.error(f"Error inserting batch (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    self.stats['errors'] += len(records)
                    return False
        
        return False
    
    def run_import(self):
        """Run the complete import process."""
        logger.info("Starting Florida Parcels Import")
        self.stats['start_time'] = datetime.now()
        
        try:
            # Process NAL file
            success = self.process_nal_file()
            
            if success:
                logger.info("Import completed successfully!")
            else:
                logger.error("Import failed!")
            
        except Exception as e:
            logger.error(f"Import failed with error: {e}")
            success = False
        
        finally:
            self.stats['end_time'] = datetime.now()
            duration = self.stats['end_time'] - self.stats['start_time']
            
            logger.info("Import Statistics:")
            logger.info(f"  Duration: {duration}")
            logger.info(f"  Records Processed: {self.stats['processed']}")
            logger.info(f"  Records Inserted: {self.stats['inserted']}")
            logger.info(f"  Errors: {self.stats['errors']}")
            
            # Save stats to file
            with open('import_stats.json', 'w') as f:
                stats_copy = self.stats.copy()
                stats_copy['start_time'] = stats_copy['start_time'].isoformat() if stats_copy['start_time'] else None
                stats_copy['end_time'] = stats_copy['end_time'].isoformat() if stats_copy['end_time'] else None
                stats_copy['duration_seconds'] = duration.total_seconds()
                json.dump(stats_copy, f, indent=2)
        
        return success

def main():
    """Main entry point."""
    logger.info("Florida Parcels Import Script")
    logger.info("=" * 50)
    
    try:
        importer = FloridaParcelsImporter()
        success = importer.run_import()
        
        if success:
            logger.info("Import completed successfully!")
            return 0
        else:
            logger.error("Import failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())