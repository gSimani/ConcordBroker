#!/usr/bin/env python3
"""
Property Appraiser Data Loader for Supabase
Loads NAL, NAP, SDF, NAV N, and NAV D files into structured Supabase tables
Following the pattern used for Sunbiz data
"""

import os
import re
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import asyncio
import aiofiles
from supabase import create_client, Client
from dotenv import load_dotenv
import struct

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('property_appraiser_loader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA MODELS - Define structure for each data type
# ============================================================================

@dataclass
class PropertyAssessment:
    """NAL - Property Assessment Data"""
    parcel_id: str
    county_code: str
    county_name: str
    owner_name: str
    owner_address: str
    owner_city: str
    owner_state: str
    owner_zip: str
    property_address: str
    property_city: str
    property_zip: str
    property_use_code: str
    tax_district: str
    subdivision: str
    just_value: float
    assessed_value: float
    taxable_value: float
    land_value: float
    building_value: float
    total_sq_ft: int
    living_area: int
    year_built: int
    bedrooms: int
    bathrooms: float
    pool: bool
    tax_year: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class PropertyOwner:
    """NAP - Property Owner Information"""
    parcel_id: str
    county_code: str
    county_name: str
    owner_sequence: int
    owner_name: str
    owner_type: str  # Individual, Corporation, Trust, etc.
    mailing_address_1: str
    mailing_address_2: str
    mailing_city: str
    mailing_state: str
    mailing_zip: str
    mailing_country: str
    ownership_percentage: float
    tax_year: int
    created_at: Optional[str] = None

@dataclass
class PropertySale:
    """SDF - Sales Data File"""
    parcel_id: str
    county_code: str
    county_name: str
    sale_date: str
    sale_price: float
    sale_type: str
    deed_type: str
    grantor_name: str  # Seller
    grantee_name: str  # Buyer
    qualified_sale: bool
    vacant_at_sale: bool
    multi_parcel_sale: bool
    book_page: str
    instrument_number: str
    verification_code: str
    tax_year: int
    created_at: Optional[str] = None

@dataclass
class NonAdValoremSummary:
    """NAV N - Non Ad Valorem Summary (per parcel)"""
    parcel_id: str
    county_code: str
    county_name: str
    tax_account_number: str
    roll_type: str
    tax_year: int
    total_assessments: float
    num_assessments: int
    tax_roll_sequence: int
    created_at: Optional[str] = None

@dataclass
class NonAdValoremDetail:
    """NAV D - Non Ad Valorem Detail (individual levies)"""
    parcel_id: str
    county_code: str
    county_name: str
    levy_id: str
    levy_name: str
    local_gov_code: str
    function_code: str
    assessment_amount: float
    tax_roll_sequence: int
    tax_year: int
    created_at: Optional[str] = None


class PropertyAppraiserLoader:
    """Main loader class for Property Appraiser data"""
    
    # County code to name mapping
    COUNTY_CODES = {
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
    
    def __init__(self, data_path: str = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE PROPERTY APP"):
        self.data_path = Path(data_path)
        
        # Override with correct Supabase credentials
        os.environ['SUPABASE_URL'] = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0'
        
        # Initialize Supabase - use service role key for write access
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("Missing Supabase credentials in environment")
            raise ValueError("Please set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("✅ Supabase client initialized")
        
        # Statistics tracking
        self.stats = {
            'nal_processed': 0,
            'nap_processed': 0,
            'sdf_processed': 0,
            'nav_n_processed': 0,
            'nav_d_processed': 0,
            'total_records': 0,
            'errors': 0,
            'counties_processed': set()
        }
        
        # Batch settings
        self.batch_size = 500  # Records per batch
        self.max_retries = 3
    
    async def create_tables(self):
        """Create Supabase tables if they don't exist"""
        logger.info("Creating/verifying Supabase tables...")
        
        # This would normally be done via Supabase dashboard or migration
        # Here we document the schema for reference
        
        schemas = {
            'property_assessments': """
                CREATE TABLE IF NOT EXISTS property_assessments (
                    id SERIAL PRIMARY KEY,
                    parcel_id VARCHAR(50) NOT NULL,
                    county_code VARCHAR(5),
                    county_name VARCHAR(50),
                    owner_name VARCHAR(255),
                    owner_address VARCHAR(255),
                    owner_city VARCHAR(100),
                    owner_state VARCHAR(2),
                    owner_zip VARCHAR(10),
                    property_address VARCHAR(255),
                    property_city VARCHAR(100),
                    property_zip VARCHAR(10),
                    property_use_code VARCHAR(20),
                    tax_district VARCHAR(50),
                    subdivision VARCHAR(100),
                    just_value DECIMAL(12,2),
                    assessed_value DECIMAL(12,2),
                    taxable_value DECIMAL(12,2),
                    land_value DECIMAL(12,2),
                    building_value DECIMAL(12,2),
                    total_sq_ft INTEGER,
                    living_area INTEGER,
                    year_built INTEGER,
                    bedrooms INTEGER,
                    bathrooms DECIMAL(3,1),
                    pool BOOLEAN DEFAULT FALSE,
                    tax_year INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(parcel_id, county_code, tax_year)
                );
            """,
            
            'property_owners': """
                CREATE TABLE IF NOT EXISTS property_owners (
                    id SERIAL PRIMARY KEY,
                    parcel_id VARCHAR(50) NOT NULL,
                    county_code VARCHAR(5),
                    county_name VARCHAR(50),
                    owner_sequence INTEGER,
                    owner_name VARCHAR(255),
                    owner_type VARCHAR(50),
                    mailing_address_1 VARCHAR(255),
                    mailing_address_2 VARCHAR(255),
                    mailing_city VARCHAR(100),
                    mailing_state VARCHAR(2),
                    mailing_zip VARCHAR(10),
                    mailing_country VARCHAR(50),
                    ownership_percentage DECIMAL(5,2),
                    tax_year INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(parcel_id, county_code, owner_sequence, tax_year)
                );
            """,
            
            'property_sales': """
                CREATE TABLE IF NOT EXISTS property_sales (
                    id SERIAL PRIMARY KEY,
                    parcel_id VARCHAR(50) NOT NULL,
                    county_code VARCHAR(5),
                    county_name VARCHAR(50),
                    sale_date DATE,
                    sale_price DECIMAL(12,2),
                    sale_type VARCHAR(50),
                    deed_type VARCHAR(50),
                    grantor_name VARCHAR(255),
                    grantee_name VARCHAR(255),
                    qualified_sale BOOLEAN,
                    vacant_at_sale BOOLEAN,
                    multi_parcel_sale BOOLEAN,
                    book_page VARCHAR(50),
                    instrument_number VARCHAR(50),
                    verification_code VARCHAR(10),
                    tax_year INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    INDEX idx_parcel_sale (parcel_id, sale_date)
                );
            """,
            
            'nav_summaries': """
                CREATE TABLE IF NOT EXISTS nav_summaries (
                    id SERIAL PRIMARY KEY,
                    parcel_id VARCHAR(50) NOT NULL,
                    county_code VARCHAR(5),
                    county_name VARCHAR(50),
                    tax_account_number VARCHAR(50),
                    roll_type VARCHAR(10),
                    tax_year INTEGER,
                    total_assessments DECIMAL(10,2),
                    num_assessments INTEGER,
                    tax_roll_sequence INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(parcel_id, county_code, tax_year)
                );
            """,
            
            'nav_details': """
                CREATE TABLE IF NOT EXISTS nav_details (
                    id SERIAL PRIMARY KEY,
                    parcel_id VARCHAR(50) NOT NULL,
                    county_code VARCHAR(5),
                    county_name VARCHAR(50),
                    levy_id VARCHAR(50),
                    levy_name VARCHAR(255),
                    local_gov_code VARCHAR(20),
                    function_code VARCHAR(20),
                    assessment_amount DECIMAL(10,2),
                    tax_roll_sequence INTEGER,
                    tax_year INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    INDEX idx_parcel_levy (parcel_id, levy_id)
                );
            """
        }
        
        logger.info("Table schemas documented. Ensure these tables exist in Supabase.")
        return True
    
    async def load_nal_file(self, file_path: Path, county_name: str, county_code: str):
        """Load NAL (assessment) file"""
        logger.info(f"Loading NAL file: {file_path.name} for {county_name}")
        
        try:
            records = []
            
            # NAL files are typically CSV or fixed-width
            with open(file_path, 'r', encoding='latin-1') as f:
                # Try CSV first
                delimiter = self._detect_delimiter(file_path)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    try:
                        assessment = PropertyAssessment(
                            parcel_id=row.get('PARCEL_ID', '').strip(),
                            county_code=county_code,
                            county_name=county_name,
                            owner_name=row.get('OWNER_NAME', '').strip(),
                            owner_address=row.get('OWNER_ADDR', '').strip(),
                            owner_city=row.get('OWNER_CITY', '').strip(),
                            owner_state=row.get('OWNER_STATE', '').strip(),
                            owner_zip=row.get('OWNER_ZIP', '').strip(),
                            property_address=row.get('PHY_ADDR1', '').strip(),
                            property_city=row.get('PHY_CITY', '').strip(),
                            property_zip=row.get('PHY_ZIPCD', '').strip(),
                            property_use_code=row.get('DOR_UC', '').strip(),
                            tax_district=row.get('TAX_DIST', '').strip(),
                            subdivision=row.get('SUBDIVISION', '').strip(),
                            just_value=self._parse_float(row.get('JUST_VAL', 0)),
                            assessed_value=self._parse_float(row.get('ASSESSED_VAL', 0)),
                            taxable_value=self._parse_float(row.get('TAXABLE_VAL', 0)),
                            land_value=self._parse_float(row.get('LAND_VAL', 0)),
                            building_value=self._parse_float(row.get('BLDG_VAL', 0)),
                            total_sq_ft=self._parse_int(row.get('TOT_LVG_AREA', 0)),
                            living_area=self._parse_int(row.get('ACT_LVG_AREA', 0)),
                            year_built=self._parse_int(row.get('YEAR_BUILT', 0)),
                            bedrooms=self._parse_int(row.get('NO_BEDROOMS', 0)),
                            bathrooms=self._parse_float(row.get('NO_BATHS', 0)),
                            pool=row.get('POOL', 'N') == 'Y',
                            tax_year=2024,  # Current tax year
                            created_at=datetime.now().isoformat()
                        )
                        
                        records.append(asdict(assessment))
                        
                        # Batch upload
                        if len(records) >= self.batch_size:
                            await self._upload_batch('property_assessments', records)
                            self.stats['nal_processed'] += len(records)
                            records = []
                            
                    except Exception as e:
                        logger.debug(f"Error processing NAL row: {e}")
                        self.stats['errors'] += 1
                        continue
            
            # Upload remaining records
            if records:
                await self._upload_batch('property_assessments', records)
                self.stats['nal_processed'] += len(records)
            
            logger.info(f"✅ Loaded {self.stats['nal_processed']} NAL records for {county_name}")
            
        except Exception as e:
            logger.error(f"Failed to load NAL file {file_path}: {e}")
            self.stats['errors'] += 1
    
    async def load_nap_file(self, file_path: Path, county_name: str, county_code: str):
        """Load NAP (owner) file"""
        logger.info(f"Loading NAP file: {file_path.name} for {county_name}")
        
        try:
            records = []
            
            with open(file_path, 'r', encoding='latin-1') as f:
                delimiter = self._detect_delimiter(file_path)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    try:
                        owner = PropertyOwner(
                            parcel_id=row.get('PARCEL_ID', '').strip(),
                            county_code=county_code,
                            county_name=county_name,
                            owner_sequence=self._parse_int(row.get('OWNER_SEQ', 1)),
                            owner_name=row.get('OWNER_NAME', '').strip(),
                            owner_type=self._determine_owner_type(row.get('OWNER_NAME', '')),
                            mailing_address_1=row.get('MAIL_ADDR_1', '').strip(),
                            mailing_address_2=row.get('MAIL_ADDR_2', '').strip(),
                            mailing_city=row.get('MAIL_CITY', '').strip(),
                            mailing_state=row.get('MAIL_STATE', '').strip(),
                            mailing_zip=row.get('MAIL_ZIP', '').strip(),
                            mailing_country=row.get('MAIL_COUNTRY', 'USA').strip(),
                            ownership_percentage=self._parse_float(row.get('OWN_PERCENT', 100)),
                            tax_year=2024,
                            created_at=datetime.now().isoformat()
                        )
                        
                        records.append(asdict(owner))
                        
                        if len(records) >= self.batch_size:
                            await self._upload_batch('property_owners', records)
                            self.stats['nap_processed'] += len(records)
                            records = []
                            
                    except Exception as e:
                        logger.debug(f"Error processing NAP row: {e}")
                        self.stats['errors'] += 1
                        continue
            
            if records:
                await self._upload_batch('property_owners', records)
                self.stats['nap_processed'] += len(records)
            
            logger.info(f"✅ Loaded {self.stats['nap_processed']} NAP records for {county_name}")
            
        except Exception as e:
            logger.error(f"Failed to load NAP file {file_path}: {e}")
            self.stats['errors'] += 1
    
    async def load_sdf_file(self, file_path: Path, county_name: str, county_code: str):
        """Load SDF (sales) file"""
        logger.info(f"Loading SDF file: {file_path.name} for {county_name}")
        
        try:
            records = []
            
            with open(file_path, 'r', encoding='latin-1') as f:
                delimiter = self._detect_delimiter(file_path)
                reader = csv.DictReader(f, delimiter=delimiter)
                
                for row in reader:
                    try:
                        # Parse sale date
                        sale_date = self._parse_date(row.get('SALE_DATE', ''))
                        if not sale_date:
                            continue
                        
                        sale = PropertySale(
                            parcel_id=row.get('PARCEL_ID', '').strip(),
                            county_code=county_code,
                            county_name=county_name,
                            sale_date=sale_date,
                            sale_price=self._parse_float(row.get('SALE_PRICE', 0)),
                            sale_type=row.get('SALE_TYPE', '').strip(),
                            deed_type=row.get('DEED_TYPE', '').strip(),
                            grantor_name=row.get('GRANTOR', '').strip(),
                            grantee_name=row.get('GRANTEE', '').strip(),
                            qualified_sale=row.get('QUALIFIED', 'N') == 'Y',
                            vacant_at_sale=row.get('VACANT', 'N') == 'Y',
                            multi_parcel_sale=row.get('MULTI_PARCEL', 'N') == 'Y',
                            book_page=row.get('BOOK_PAGE', '').strip(),
                            instrument_number=row.get('INSTR_NUM', '').strip(),
                            verification_code=row.get('VI_CODE', '').strip(),
                            tax_year=2024,
                            created_at=datetime.now().isoformat()
                        )
                        
                        records.append(asdict(sale))
                        
                        if len(records) >= self.batch_size:
                            await self._upload_batch('property_sales', records)
                            self.stats['sdf_processed'] += len(records)
                            records = []
                            
                    except Exception as e:
                        logger.debug(f"Error processing SDF row: {e}")
                        self.stats['errors'] += 1
                        continue
            
            if records:
                await self._upload_batch('property_sales', records)
                self.stats['sdf_processed'] += len(records)
            
            logger.info(f"✅ Loaded {self.stats['sdf_processed']} SDF records for {county_name}")
            
        except Exception as e:
            logger.error(f"Failed to load SDF file {file_path}: {e}")
            self.stats['errors'] += 1
    
    async def load_nav_n_file(self, file_path: Path, county_name: str, county_code: str):
        """Load NAV N (summary) file - Fixed width format"""
        logger.info(f"Loading NAV N file: {file_path.name} for {county_name}")
        
        try:
            records = []
            
            # NAV N files are fixed-width format
            # Based on navlayout.pdf specifications
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    try:
                        # Parse fixed-width fields (positions from navlayout.pdf)
                        nav_summary = NonAdValoremSummary(
                            parcel_id=line[3:28].strip(),  # Positions 4-28
                            county_code=line[1:3].strip(),  # Positions 2-3
                            county_name=county_name,
                            tax_account_number=line[28:48].strip(),  # Positions 29-48
                            roll_type=line[0:1].strip(),  # Position 1
                            tax_year=self._parse_int(line[48:52]),  # Positions 49-52
                            total_assessments=self._parse_float(line[52:64]) / 100,  # Positions 53-64 (implied decimals)
                            num_assessments=self._parse_int(line[64:67]),  # Positions 65-67
                            tax_roll_sequence=self._parse_int(line[67:72]),  # Positions 68-72
                            created_at=datetime.now().isoformat()
                        )
                        
                        records.append(asdict(nav_summary))
                        
                        if len(records) >= self.batch_size:
                            await self._upload_batch('nav_summaries', records)
                            self.stats['nav_n_processed'] += len(records)
                            records = []
                            
                    except Exception as e:
                        logger.debug(f"Error processing NAV N line: {e}")
                        self.stats['errors'] += 1
                        continue
            
            if records:
                await self._upload_batch('nav_summaries', records)
                self.stats['nav_n_processed'] += len(records)
            
            logger.info(f"✅ Loaded {self.stats['nav_n_processed']} NAV N records for {county_name}")
            
        except Exception as e:
            logger.error(f"Failed to load NAV N file {file_path}: {e}")
            self.stats['errors'] += 1
    
    async def load_nav_d_file(self, file_path: Path, county_name: str, county_code: str):
        """Load NAV D (detail) file - Fixed width format"""
        logger.info(f"Loading NAV D file: {file_path.name} for {county_name}")
        
        try:
            records = []
            
            # NAV D files are fixed-width format
            with open(file_path, 'r', encoding='latin-1') as f:
                for line in f:
                    try:
                        # Parse fixed-width fields
                        nav_detail = NonAdValoremDetail(
                            parcel_id=line[3:28].strip(),  # Positions 4-28
                            county_code=line[1:3].strip(),  # Positions 2-3
                            county_name=county_name,
                            levy_id=line[28:38].strip(),  # Positions 29-38
                            levy_name=self._get_levy_name(line[28:38].strip()),  # Lookup levy name
                            local_gov_code=line[38:43].strip(),  # Positions 39-43
                            function_code=line[43:46].strip(),  # Positions 44-46
                            assessment_amount=self._parse_float(line[46:58]) / 100,  # Positions 47-58 (implied decimals)
                            tax_roll_sequence=self._parse_int(line[58:63]),  # Positions 59-63
                            tax_year=2024,
                            created_at=datetime.now().isoformat()
                        )
                        
                        records.append(asdict(nav_detail))
                        
                        if len(records) >= self.batch_size:
                            await self._upload_batch('nav_details', records)
                            self.stats['nav_d_processed'] += len(records)
                            records = []
                            
                    except Exception as e:
                        logger.debug(f"Error processing NAV D line: {e}")
                        self.stats['errors'] += 1
                        continue
            
            if records:
                await self._upload_batch('nav_details', records)
                self.stats['nav_d_processed'] += len(records)
            
            logger.info(f"✅ Loaded {self.stats['nav_d_processed']} NAV D records for {county_name}")
            
        except Exception as e:
            logger.error(f"Failed to load NAV D file {file_path}: {e}")
            self.stats['errors'] += 1
    
    async def _upload_batch(self, table_name: str, records: List[Dict]):
        """Upload batch of records to Supabase with retry logic"""
        for attempt in range(self.max_retries):
            try:
                # Use upsert to handle duplicates
                response = self.supabase.table(table_name).upsert(records).execute()
                self.stats['total_records'] += len(records)
                logger.debug(f"Uploaded {len(records)} records to {table_name}")
                return True
                
            except Exception as e:
                logger.warning(f"Upload attempt {attempt + 1} failed: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to upload batch to {table_name} after {self.max_retries} attempts")
                    self.stats['errors'] += 1
                    return False
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _detect_delimiter(self, file_path: Path) -> str:
        """Detect file delimiter"""
        with open(file_path, 'r', encoding='latin-1') as f:
            first_line = f.readline()
            if '\t' in first_line:
                return '\t'
            elif '|' in first_line:
                return '|'
            else:
                return ','
    
    def _parse_float(self, value: Any) -> float:
        """Safely parse float value"""
        if not value:
            return 0.0
        try:
            # Remove commas and dollar signs
            if isinstance(value, str):
                value = value.replace(',', '').replace('$', '')
            return float(value)
        except:
            return 0.0
    
    def _parse_int(self, value: Any) -> int:
        """Safely parse integer value"""
        if not value:
            return 0
        try:
            if isinstance(value, str):
                value = value.replace(',', '')
            return int(float(value))
        except:
            return 0
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to ISO format"""
        if not date_str:
            return None
        
        # Try common date formats
        formats = [
            '%Y%m%d',
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d'
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue
        
        return None
    
    def _determine_owner_type(self, owner_name: str) -> str:
        """Determine owner type from name"""
        owner_name = owner_name.upper()
        
        if any(word in owner_name for word in ['LLC', 'L.L.C.', 'LIMITED LIABILITY']):
            return 'LLC'
        elif any(word in owner_name for word in ['INC', 'CORP', 'CORPORATION', 'INCORPORATED']):
            return 'Corporation'
        elif any(word in owner_name for word in ['TRUST', 'TRUSTEE']):
            return 'Trust'
        elif any(word in owner_name for word in ['LP', 'L.P.', 'LIMITED PARTNERSHIP']):
            return 'Limited Partnership'
        elif any(word in owner_name for word in ['ESTATE OF']):
            return 'Estate'
        elif '&' in owner_name or ' AND ' in owner_name:
            return 'Joint'
        else:
            return 'Individual'
    
    def _get_levy_name(self, levy_id: str) -> str:
        """Get levy name from ID (would need a lookup table)"""
        # Common levy types
        levy_names = {
            'FIRE': 'Fire District',
            'LIGHT': 'Street Lighting',
            'GARB': 'Garbage Collection',
            'WATER': 'Water Management',
            'CDD': 'Community Development District',
            'STORM': 'Stormwater Management',
            'MOSQUITO': 'Mosquito Control',
            'LIBRARY': 'Library District'
        }
        
        for key, name in levy_names.items():
            if key in levy_id.upper():
                return name
        
        return levy_id  # Return ID if no match
    
    def get_county_code_from_filename(self, filename: str) -> Optional[str]:
        """Extract county code from filename"""
        # Pattern: NAVN162401.TXT -> code is 16
        import re
        match = re.search(r'NAV[ND](\d{2})', filename.upper())
        if match:
            return match.group(1)
        return None
    
    async def process_all_counties(self):
        """Process all county data files"""
        logger.info("="*70)
        logger.info("PROPERTY APPRAISER DATA LOADER FOR SUPABASE")
        logger.info("="*70)
        
        # Create tables if needed
        await self.create_tables()
        
        # Process each county directory
        for county_dir in self.data_path.iterdir():
            if not county_dir.is_dir():
                continue
            
            county_name = county_dir.name
            
            # Skip if not a valid county
            if county_name not in self.COUNTY_CODES.values():
                continue
            
            # Get county code
            county_code = next(
                (code for code, name in self.COUNTY_CODES.items() if name == county_name),
                None
            )
            
            if not county_code:
                continue
            
            logger.info(f"\nProcessing {county_name} (Code: {county_code})")
            self.stats['counties_processed'].add(county_name)
            
            # Process NAL files
            nal_dir = county_dir / "NAL"
            if nal_dir.exists():
                for nal_file in nal_dir.glob("*.csv"):
                    await self.load_nal_file(nal_file, county_name, county_code)
                for nal_file in nal_dir.glob("*.txt"):
                    await self.load_nal_file(nal_file, county_name, county_code)
            
            # Process NAP files
            nap_dir = county_dir / "NAP"
            if nap_dir.exists():
                for nap_file in nap_dir.glob("*.csv"):
                    await self.load_nap_file(nap_file, county_name, county_code)
                for nap_file in nap_dir.glob("*.txt"):
                    await self.load_nap_file(nap_file, county_name, county_code)
            
            # Process SDF files
            sdf_dir = county_dir / "SDF"
            if sdf_dir.exists():
                for sdf_file in sdf_dir.glob("*.csv"):
                    await self.load_sdf_file(sdf_file, county_name, county_code)
                for sdf_file in sdf_dir.glob("*.txt"):
                    await self.load_sdf_file(sdf_file, county_name, county_code)
            
            # Process NAV files
            nav_dir = county_dir / "NAV"
            if nav_dir.exists():
                # NAV N files
                nav_n_dir = nav_dir / "NAV_N"
                if nav_n_dir.exists():
                    for nav_file in nav_n_dir.glob("*.txt"):
                        await self.load_nav_n_file(nav_file, county_name, county_code)
                    for nav_file in nav_n_dir.glob("*.TXT"):
                        await self.load_nav_n_file(nav_file, county_name, county_code)
                
                # NAV D files
                nav_d_dir = nav_dir / "NAV_D"
                if nav_d_dir.exists():
                    for nav_file in nav_d_dir.glob("*.txt"):
                        await self.load_nav_d_file(nav_file, county_name, county_code)
                    for nav_file in nav_d_dir.glob("*.TXT"):
                        await self.load_nav_d_file(nav_file, county_name, county_code)
        
        # Print final statistics
        self.print_statistics()
    
    def print_statistics(self):
        """Print final loading statistics"""
        logger.info("\n" + "="*70)
        logger.info("LOADING COMPLETE - STATISTICS")
        logger.info("="*70)
        logger.info(f"Counties Processed: {len(self.stats['counties_processed'])}")
        logger.info(f"NAL Records: {self.stats['nal_processed']:,}")
        logger.info(f"NAP Records: {self.stats['nap_processed']:,}")
        logger.info(f"SDF Records: {self.stats['sdf_processed']:,}")
        logger.info(f"NAV N Records: {self.stats['nav_n_processed']:,}")
        logger.info(f"NAV D Records: {self.stats['nav_d_processed']:,}")
        logger.info(f"Total Records Loaded: {self.stats['total_records']:,}")
        logger.info(f"Errors: {self.stats['errors']:,}")
        logger.info("="*70)
        
        # Save statistics to file
        stats_file = Path('property_appraiser_load_stats.json')
        with open(stats_file, 'w') as f:
            # Convert set to list for JSON serialization
            stats_copy = self.stats.copy()
            stats_copy['counties_processed'] = list(stats_copy['counties_processed'])
            json.dump(stats_copy, f, indent=2)
        
        logger.info(f"Statistics saved to {stats_file}")


async def main():
    """Main execution function"""
    loader = PropertyAppraiserLoader()
    await loader.process_all_counties()


if __name__ == "__main__":
    asyncio.run(main())