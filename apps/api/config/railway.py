"""
Railway API Configuration for ConcordBroker
Handles Railway-specific settings and service discovery
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field

class RailwayConfig(BaseSettings):
    """Railway deployment configuration"""
    
    # Railway Project Settings
    railway_token: str = Field(
        default="",  # Set via environment variable only
        env="RAILWAY_TOKEN"
    )
    railway_project_id: str = Field(
        default="05f5fbf4-f31c-4bdb-9022-3e987dd80fdb",
        env="RAILWAY_PROJECT_ID"
    )
    railway_environment: str = Field(
        default="concordbrokerproduction",
        env="RAILWAY_ENVIRONMENT"
    )
    railway_service_id: str = Field(
        default="5eeefe12-0a29-43b7-8a7b-6fa4e99e53d7",
        env="RAILWAY_SERVICE_ID"
    )
    
    # Railway Network Settings
    railway_internal_domain: str = Field(
        default="concordbroker.railway.internal",
        env="RAILWAY_INTERNAL_DOMAIN"
    )
    railway_public_domain: str = Field(
        default="https://concordbroker-railway-production.up.railway.app",
        env="RAILWAY_PUBLIC_DOMAIN"
    )
    
    # Service Discovery
    api_internal_url: str = Field(
        default="http://concordbroker.railway.internal:8000",
        env="INTERNAL_API_URL"
    )
    sunbiz_worker_url: Optional[str] = Field(
        default="http://sunbiz-worker.railway.internal",
        env="SUNBIZ_WORKER_URL"
    )
    bcpa_worker_url: Optional[str] = Field(
        default="http://bcpa-worker.railway.internal",
        env="BCPA_WORKER_URL"
    )
    records_worker_url: Optional[str] = Field(
        default="http://records-worker.railway.internal",
        env="RECORDS_WORKER_URL"
    )
    
    # Environment Detection
    is_railway: bool = Field(
        default=False,
        env="RAILWAY_ENVIRONMENT"
    )
    
    # Port Configuration
    port: int = Field(
        default=8000,
        env="PORT"
    )
    
    class Config:
        env_file = ".env.railway"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Auto-detect Railway environment
        self.is_railway = bool(os.environ.get("RAILWAY_ENVIRONMENT"))
        
        # Use Railway-provided PORT if available
        if os.environ.get("PORT"):
            self.port = int(os.environ.get("PORT"))
    
    def get_service_url(self, service: str) -> str:
        """Get internal service URL for Railway network communication"""
        service_urls = {
            "api": self.api_internal_url,
            "sunbiz": self.sunbiz_worker_url,
            "bcpa": self.bcpa_worker_url,
            "records": self.records_worker_url,
        }
        return service_urls.get(service, self.api_internal_url)
    
    def get_public_url(self) -> str:
        """Get public-facing URL for the API"""
        if self.is_railway:
            return self.railway_public_domain
        return f"http://localhost:{self.port}"

# Singleton instance
railway_config = RailwayConfig()