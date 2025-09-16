"""
Configuration for NAV Assessments agent
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Configuration settings for NAV Assessments"""
    
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
    NAV_BASE_PATH: str = "PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAV/"
    
    # County codes
    BROWARD_COUNTY_CODE: str = "16"
    MIAMI_DADE_COUNTY_CODE: str = "25"
    PALM_BEACH_COUNTY_CODE: str = "50"
    
    # County name mapping
    COUNTY_NAMES = {
        "16": "Broward",
        "25": "Miami-Dade", 
        "50": "Palm Beach",
        "11": "Alachua",
        "12": "Baker",
        "13": "Bay",
        "14": "Bradford",
        "15": "Brevard",
        "17": "Calhoun",
        "18": "Charlotte",
        "19": "Citrus",
        "20": "Clay",
        "21": "Collier",
        "22": "Columbia",
        "23": "DeSoto",
        "24": "Dixie",
        "26": "Duval",
        "27": "Escambia",
        "28": "Flagler",
        "29": "Franklin",
        "30": "Gadsden",
        "31": "Gilchrist",
        "32": "Glades",
        "33": "Gulf",
        "34": "Hamilton",
        "35": "Hardee",
        "36": "Hendry",
        "37": "Hernando",
        "38": "Highlands",
        "39": "Hillsborough",
        "40": "Holmes",
        "41": "Indian River",
        "42": "Jackson",
        "43": "Jefferson",
        "44": "Lafayette",
        "45": "Lake",
        "46": "Lee",
        "47": "Leon",
        "48": "Levy",
        "49": "Liberty",
        "51": "Manatee",
        "52": "Marion",
        "53": "Martin",
        "54": "Monroe",
        "55": "Nassau",
        "56": "Okaloosa",
        "57": "Okeechobee",
        "58": "Orange",
        "59": "Osceola",
        "60": "Pasco",
        "61": "Pinellas",
        "62": "Polk",
        "63": "Putnam",
        "64": "St. Johns",
        "65": "St. Lucie",
        "66": "Santa Rosa",
        "67": "Sarasota",
        "68": "Seminole",
        "69": "Sumter",
        "70": "Suwannee",
        "71": "Taylor",
        "72": "Union",
        "73": "Volusia",
        "74": "Wakulla",
        "75": "Walton",
        "76": "Washington",
        "77": "Unknown"
    }
    
    # Function codes for assessments
    FUNCTION_CODES = {
        1: "General Government",
        2: "Public Safety",
        3: "Physical Environment", 
        4: "Transportation",
        5: "Economic Environment",
        6: "Human Services",
        7: "Culture/Recreation",
        8: "Court Related",
        9: "Debt Service",
        10: "Other"
    }
    
    # Processing
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '1000'))
    MAX_WORKERS: int = int(os.getenv('MAX_WORKERS', '4'))
    
    # Retry configuration
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('RETRY_DELAY', '5'))
    
    # Data validation
    ENABLE_DATA_VALIDATION: bool = os.getenv('ENABLE_DATA_VALIDATION', 'true').lower() == 'true'
    
    def get_data_path(self, subdir: str = '') -> Path:
        """Get data directory path"""
        base_path = Path(self.DATA_RAW_PATH) / 'nav_assessments'
        if subdir:
            base_path = base_path / subdir
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path
    
    def get_county_name(self, county_code: str) -> str:
        """Get county name from code"""
        return self.COUNTY_NAMES.get(county_code, f"County {county_code}")
    
    def get_function_description(self, function_code: int) -> str:
        """Get function description from code"""
        return self.FUNCTION_CODES.get(function_code, f"Function {function_code}")
    
    def generate_nav_filename(self, table_type: str, county_code: str, 
                            year: str, submission: str = "01") -> str:
        """Generate NAV filename based on specifications"""
        # Format: NAV[N|D][CountyCode][Year][Submission].TXT
        year_short = year[-2:] if len(year) == 4 else year
        return f"NAV{table_type.upper()}{county_code}{year_short}{submission}.TXT"

settings = Settings()