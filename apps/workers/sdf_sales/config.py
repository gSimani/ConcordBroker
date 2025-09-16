"""
Configuration for SDF Sales agent
"""

import os
from pathlib import Path
from typing import Optional, Dict

class Settings:
    """Configuration settings for SDF Sales data"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL', 
        'postgresql://user:password@localhost/concordbroker'
    )
    
    # Data storage
    DATA_RAW_PATH: str = os.getenv('DATA_RAW_PATH', './data/raw')
    DATA_PROCESSED_PATH: str = os.getenv('DATA_PROCESSED_PATH', './data/processed')
    
    # Florida Revenue specific
    FLORIDA_REVENUE_BASE_URL: str = "https://floridarevenue.com/property/dataportal/Documents/"
    SDF_BASE_PATH: str = "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF/"
    
    # County codes - same as NAV
    BROWARD_COUNTY_CODE: str = "16"
    MIAMI_DADE_COUNTY_CODE: str = "25"
    PALM_BEACH_COUNTY_CODE: str = "50"
    
    # Qualification codes mapping (from analysis)
    QUALIFICATION_CODES = {
        "01": {"type": "Qualified", "description": "Arms length transaction"},
        "02": {"type": "Qualified", "description": "Verified by questionnaire"},
        "03": {"type": "Qualified", "description": "Adjustment made by questionnaire"},
        "05": {"type": "Qualified", "description": "Forced sale/Foreclosure"},
        "06": {"type": "Qualified", "description": "Estate sale"},
        "11": {"type": "Qualified", "description": "Financial institution resale (REO)"},
        "12": {"type": "Qualified", "description": "Financial institution sale"},
        "16": {"type": "Disqualified", "description": "Related party transfer"},
        "17": {"type": "Disqualified", "description": "Non-market financing"},
        "18": {"type": "Disqualified", "description": "Property condition"},
        "19": {"type": "Disqualified", "description": "Multi-parcel sale"},
        "30": {"type": "Disqualified", "description": "Transfer between family"},
        "36": {"type": "Disqualified", "description": "Lease or rental"},
        "37": {"type": "Disqualified", "description": "Corrective/Tax deed"},
        "38": {"type": "Disqualified", "description": "Partial interest"},
        "39": {"type": "Disqualified", "description": "Love and affection"},
        "40": {"type": "Disqualified", "description": "Gift"},
        "43": {"type": "Disqualified", "description": "Charitable organization"},
        "99": {"type": "Other", "description": "Other/Unknown"}
    }
    
    # Sales analysis thresholds
    DISTRESSED_QUAL_CODES = ["05", "11", "12", "37"]  # Foreclosure, REO, Tax deed
    QUALIFIED_QUAL_CODES = ["01", "02", "03", "05", "06", "11", "12"]
    HIGH_VALUE_THRESHOLD = 1000000  # $1M+ sales
    LOW_VALUE_THRESHOLD = 1000  # Likely non-monetary transfers
    
    # DOR Use Codes (common ones)
    DOR_USE_CODES = {
        "000": "Vacant Residential",
        "001": "Single Family",
        "002": "Mobile Home",
        "003": "Multi-family (10+ units)",
        "004": "Condominium",
        "008": "Multi-family (2-9 units)",
        "010": "Vacant Commercial",
        "011": "Stores/Retail",
        "012": "Mixed use",
        "017": "Office Building",
        "021": "Restaurant",
        "039": "Hotel/Motel",
        "048": "Warehouse",
        "070": "Vacant Institutional",
        "080": "Vacant Governmental"
    }
    
    # Processing
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1000'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Retry configuration
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
    
    def get_data_path(self, subdir: str = '') -> Path:
        """Get data directory path"""
        base_path = Path(self.DATA_RAW_PATH) / 'sdf_sales'
        if subdir:
            base_path = base_path / subdir
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path
    
    def get_qualification_info(self, qual_code: str) -> Dict:
        """Get qualification code information"""
        return self.QUALIFICATION_CODES.get(
            qual_code, 
            {"type": "Unknown", "description": f"Unknown code: {qual_code}"}
        )
    
    def is_qualified_sale(self, qual_code: str) -> bool:
        """Check if sale is qualified for assessment purposes"""
        return qual_code in self.QUALIFIED_QUAL_CODES
    
    def is_distressed_sale(self, qual_code: str) -> bool:
        """Check if sale is distressed (foreclosure, REO, tax deed)"""
        return qual_code in self.DISTRESSED_QUAL_CODES
    
    def get_dor_use_description(self, dor_code: str) -> str:
        """Get DOR use code description"""
        # Handle padded codes (e.g., "001" and "1")
        try:
            code_int = int(dor_code)
            dor_code = f"{code_int:03d}"  # Format as 3-digit string
        except (ValueError, TypeError):
            pass
        
        return self.DOR_USE_CODES.get(dor_code, f"Code {dor_code}")

settings = Settings()