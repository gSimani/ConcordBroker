"""
Configuration for Florida Revenue agent
"""

import os
from pathlib import Path
from typing import Optional

class Settings:
    """Configuration settings"""
    
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
    BROWARD_COUNTY_CODE: str = "16"
    
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
        base_path = Path(self.DATA_RAW_PATH) / 'florida_revenue'
        if subdir:
            base_path = base_path / subdir
        base_path.mkdir(parents=True, exist_ok=True)
        return base_path

settings = Settings()