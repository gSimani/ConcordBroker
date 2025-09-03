"""
Configuration for Sunbiz Loader
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/concordbroker"
    )
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    # Data paths
    DATA_RAW_PATH: str = os.getenv("DATA_RAW_PATH", "/data/raw")
    DATA_PROCESSED_PATH: str = os.getenv("DATA_PROCESSED_PATH", "/data/processed")
    DATA_CACHE_PATH: str = os.getenv("DATA_CACHE_PATH", "/data/cache")
    
    # SFTP settings (hardcoded for security)
    SFTP_HOST: str = "sftp.floridados.gov"
    SFTP_USERNAME: str = "Public"
    SFTP_PASSWORD: str = "PubAccess1845!"
    SFTP_PORT: int = 22
    
    # Processing settings
    BATCH_SIZE: int = 1000
    MAX_WORKERS: int = 4
    CHUNK_SIZE: int = 10000
    
    # Entity resolution
    ENTITY_MATCH_THRESHOLD: float = 0.85
    USE_FUZZY_MATCHING: bool = True
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()