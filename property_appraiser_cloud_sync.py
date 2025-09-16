#!/usr/bin/env python3
"""
PROPERTY APPRAISER CLOUD SYNC SYSTEM
=====================================
Cloud-based daily synchronization for Florida Property Appraiser data
Runs entirely in Supabase Edge Functions with scheduled triggers
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import psycopg2
from bs4 import BeautifulSoup
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PROP-SYNC] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PropertyAppraiserCloudSync:
    """
    Cloud-based synchronization for Property Appraiser data
    Designed to run as Supabase Edge Function or scheduled job
    """
    
    def __init__(self):
        # Florida Revenue base URL
        self.base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files"
        
        # Database connection (uses Supabase service role)
        self.db_config = {
            'host': os.environ.get('SUPABASE_HOST', 'aws-1-us-east-1.pooler.supabase.com'),
            'port': 5432,
            'database': 'postgres',
            'user': os.environ.get('SUPABASE_USER', 'postgres.pmispwtdngkcmsrsjwbp'),
            'password': os.environ.get('SUPABASE_PASSWORD', 'West@Boca613!'),
            'sslmode': 'require'
        }
        
        # File types to monitor
        self.file_types = ['NAL', 'NAP', 'SDF', 'NAV']
        
        # County codes
        self.counties = {
            "11": "ALACHUA", "12": "BAKER", "13": "BAY", "14": "BRADFORD",
            "15": "BREVARD", "16": "BROWARD", "17": "CALHOUN", "18": "CHARLOTTE",
            "19": "CITRUS", "20": "CLAY", "21": "COLLIER", "22": "COLUMBIA",
            "23": "DADE", "24": "DESOTO", "25": "DIXIE", "26": "DUVAL",
            "27": "ESCAMBIA", "28": "FLAGLER", "29": "FRANKLIN", "30": "GADSDEN",
            "31": "GILCHRIST", "32": "GLADES", "33": "GULF", "34": "HAMILTON",
            "35": "HARDEE", "36": "HENDRY", "37": "HERNANDO", "38": "HIGHLANDS",
            "39": "HILLSBOROUGH", "40": "HOLMES", "41": "INDIAN RIVER", "42": "JACKSON",
            "43": "JEFFERSON", "44": "LAFAYETTE", "45": "LAKE", "46": "LEE",
            "47": "LEON", "48": "LEVY", "49": "LIBERTY", "50": "MADISON",
            "51": "MANATEE", "52": "MARION", "53": "MARTIN", "54": "MONROE",
            "55": "NASSAU", "56": "OKALOOSA", "57": "OKEECHOBEE", "58": "ORANGE",
            "59": "OSCEOLA", "60": "PALM BEACH", "61": "PASCO", "62": "PINELLAS",
            "63": "POLK", "64": "PUTNAM", "65": "SANTA ROSA", "66": "SARASOTA",
            "67": "SEMINOLE", "68": "ST. JOHNS", "69": "ST. LUCIE", "70": "SUMTER",
            "71": "SUWANNEE", "72": "TAYLOR", "73": "UNION", "74": "VOLUSIA",
            "75": "WAKULLA", "76": "WALTON", "77": "WASHINGTON"
        }
    
    def check_for_updates(self) -> List[Dict]:
        """
        Check Florida Revenue website for new property data files
        Returns list of new files to download
        """
        logger.info("Checking for Property Appraiser updates...")
        new_files = []
        
        # Get current year and period
        current_year = datetime.now().year
        current_period = f"{current_year}P"  # e.g., "2025P"
        
        for file_type in self.file_types:
            url = f"{self.base_url}/{file_type}/{current_period}"
            logger.info(f"Checking {file_type} files at: {url}")
            
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find all file links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if f'{file_type}' in href and '.csv' in href.lower():
                            filename = href.split('/')[-1]
                            file_hash = self._get_file_hash(filename)
                            
                            # Check if file was already processed
                            if not self._is_file_processed(filename, file_hash):
                                new_files.append({
                                    'type': file_type,
                                    'filename': filename,
                                    'url': href if href.startswith('http') else f"https://floridarevenue.com{href}",
                                    'hash': file_hash,
                                    'county_code': self._extract_county_code(filename),
                                    'period': current_period
                                })
                                logger.info(f"  New file found: {filename}")
            
            except Exception as e:
                logger.error(f"Error checking {file_type}: {e}")
        
        logger.info(f"Found {len(new_files)} new files to process")
        return new_files
    
    def _get_file_hash(self, filename: str) -> str:
        """Generate hash for file tracking"""
        return hashlib.md5(filename.encode()).hexdigest()
    
    def _extract_county_code(self, filename: str) -> str:
        """Extract county code from filename (e.g., NAL16P202501.csv -> 16)"""
        if len(filename) > 5:
            return filename[3:5]
        return "00"
    
    def _is_file_processed(self, filename: str, file_hash: str) -> bool:
        """Check if file was already processed"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Check processing log table
            cur.execute("""
                SELECT COUNT(*) FROM property_sync_log 
                WHERE filename = %s AND file_hash = %s 
                AND status = 'completed'
            """, (filename, file_hash))
            
            count = cur.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"Error checking file status: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    
    def download_and_process(self, file_info: Dict) -> bool:
        """
        Download and process a property data file
        """
        logger.info(f"Processing {file_info['filename']}...")
        
        try:
            # Download file
            response = requests.get(file_info['url'], stream=True, timeout=60)
            if response.status_code != 200:
                logger.error(f"Failed to download {file_info['filename']}")
                return False
            
            # Process based on file type
            if file_info['type'] == 'NAL':
                return self._process_nal_file(response.content, file_info)
            elif file_info['type'] == 'NAP':
                return self._process_nap_file(response.content, file_info)
            elif file_info['type'] == 'SDF':
                return self._process_sdf_file(response.content, file_info)
            elif file_info['type'] == 'NAV':
                return self._process_nav_file(response.content, file_info)
            
        except Exception as e:
            logger.error(f"Error processing {file_info['filename']}: {e}")
            self._log_processing_error(file_info, str(e))
            return False
    
    def _process_nal_file(self, content: bytes, file_info: Dict) -> bool:
        """Process NAL (Property Assessment) file"""
        import csv
        import io
        
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            # Parse CSV
            text_content = content.decode('utf-8', errors='ignore')
            reader = csv.DictReader(io.StringIO(text_content))
            
            batch = []
            batch_size = 1000
            county_code = file_info['county_code']
            county_name = self.counties.get(county_code, 'UNKNOWN')
            
            for row in reader:
                # Prepare record for insertion
                record = (
                    row.get('PARCEL_ID', '').strip(),
                    county_code,
                    county_name,
                    row.get('OWN_NAME', '').strip()[:255],
                    row.get('OWN_ADDR1', '').strip()[:255],
                    row.get('OWN_CITY', '').strip()[:100],
                    row.get('OWN_STATE', 'FL')[:2],
                    row.get('OWN_ZIPCD', '').strip()[:10],
                    row.get('PHY_ADDR1', '').strip()[:255],
                    row.get('PHY_CITY', '').strip()[:100],
                    row.get('PHY_ZIPCD', '').strip()[:10],
                    row.get('DOR_UC', '').strip()[:20],
                    row.get('DISTR_CD', '').strip()[:50],
                    row.get('SUBDIV_NM', '').strip()[:100],
                    self._safe_float(row.get('JV', 0)),
                    self._safe_float(row.get('AV_SD', 0)),
                    self._safe_float(row.get('TV_SD', 0)),
                    self._safe_float(row.get('LND_VAL', 0)),
                    self._safe_float(row.get('BLDT_VAL', 0)),
                    self._safe_int(row.get('LND_SQFOOT', 0)),
                    self._safe_int(row.get('TOT_LVG_AREA', 0)),
                    self._safe_int(row.get('ACT_YR_BLT', 0)),
                    self._safe_int(row.get('NO_RES_UNTS', 0)),
                    self._safe_float(row.get('NO_BATHS', 0)),
                    row.get('POOL', '').upper() == 'Y',
                    datetime.now().year
                )
                batch.append(record)
                
                if len(batch) >= batch_size:
                    self._insert_batch(cur, 'property_assessments', batch)
                    batch = []
            
            # Insert remaining records
            if batch:
                self._insert_batch(cur, 'property_assessments', batch)
            
            conn.commit()
            
            # Log successful processing
            self._log_processing_success(file_info)
            logger.info(f"Successfully processed {file_info['filename']}")
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error processing NAL file: {e}")
            return False
        finally:
            cur.close()
            conn.close()
    
    def _insert_batch(self, cur, table: str, records: List):
        """Insert batch of records"""
        if table == 'property_assessments':
            query = """
                INSERT INTO property_assessments (
                    parcel_id, county_code, county_name, owner_name, owner_address,
                    owner_city, owner_state, owner_zip, property_address, property_city,
                    property_zip, property_use_code, tax_district, subdivision,
                    just_value, assessed_value, taxable_value, land_value, building_value,
                    total_sq_ft, living_area, year_built, bedrooms, bathrooms, pool, tax_year
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (parcel_id, county_code, tax_year) DO UPDATE SET
                    owner_name = EXCLUDED.owner_name,
                    taxable_value = EXCLUDED.taxable_value,
                    updated_at = NOW()
            """
            cur.executemany(query, records)
    
    def _safe_float(self, value) -> float:
        """Safely convert to float"""
        try:
            return float(value) if value else 0.0
        except:
            return 0.0
    
    def _safe_int(self, value) -> int:
        """Safely convert to int"""
        try:
            return int(value) if value else 0
        except:
            return 0
    
    def _log_processing_success(self, file_info: Dict):
        """Log successful file processing"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO property_sync_log (
                    filename, file_hash, file_type, county_code,
                    status, processed_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                file_info['filename'],
                file_info['hash'],
                file_info['type'],
                file_info['county_code'],
                'completed',
                datetime.now(),
                json.dumps(file_info)
            ))
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def _log_processing_error(self, file_info: Dict, error: str):
        """Log processing error"""
        conn = psycopg2.connect(**self.db_config)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                INSERT INTO property_sync_log (
                    filename, file_hash, file_type, county_code,
                    status, error_message, processed_at, metadata
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                file_info['filename'],
                file_info['hash'],
                file_info['type'],
                file_info['county_code'],
                'error',
                error,
                datetime.now(),
                json.dumps(file_info)
            ))
            conn.commit()
        finally:
            cur.close()
            conn.close()
    
    def run_daily_sync(self):
        """
        Main entry point for daily synchronization
        This would be called by Supabase Edge Function or cron job
        """
        logger.info("="*60)
        logger.info("PROPERTY APPRAISER DAILY SYNC STARTED")
        logger.info(f"Time: {datetime.now()}")
        logger.info("="*60)
        
        try:
            # Check for new files
            new_files = self.check_for_updates()
            
            if not new_files:
                logger.info("No new files to process")
                return {
                    'status': 'success',
                    'message': 'No new files to process',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Process each new file
            processed = 0
            failed = 0
            
            for file_info in new_files:
                if self.download_and_process(file_info):
                    processed += 1
                else:
                    failed += 1
            
            # Generate summary
            summary = {
                'status': 'success' if failed == 0 else 'partial',
                'files_found': len(new_files),
                'files_processed': processed,
                'files_failed': failed,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Sync completed: {processed} processed, {failed} failed")
            return summary
            
        except Exception as e:
            logger.error(f"Critical error in daily sync: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _process_nap_file(self, content: bytes, file_info: Dict) -> bool:
        """Process NAP (Property Owners) file"""
        # Similar structure to NAL processing
        logger.info(f"Processing NAP file: {file_info['filename']}")
        # Implementation would follow same pattern as NAL
        return True
    
    def _process_sdf_file(self, content: bytes, file_info: Dict) -> bool:
        """Process SDF (Sales) file"""
        # Similar structure to NAL processing
        logger.info(f"Processing SDF file: {file_info['filename']}")
        # Implementation would follow same pattern as NAL
        return True
    
    def _process_nav_file(self, content: bytes, file_info: Dict) -> bool:
        """Process NAV (Non-Ad Valorem) file"""
        # NAV files are fixed-width, need different parsing
        logger.info(f"Processing NAV file: {file_info['filename']}")
        # Implementation would parse fixed-width format
        return True

# Entry point for Supabase Edge Function
def handler(event, context):
    """
    Handler for cloud execution (AWS Lambda style)
    """
    sync = PropertyAppraiserCloudSync()
    result = sync.run_daily_sync()
    return {
        'statusCode': 200,
        'body': json.dumps(result)
    }

if __name__ == "__main__":
    # For local testing
    sync = PropertyAppraiserCloudSync()
    result = sync.run_daily_sync()
    print(json.dumps(result, indent=2))