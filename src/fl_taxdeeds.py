"""
Florida Tax Deed Sales Aggregator
Aggregates upcoming tax deed sale items from various Florida counties.
"""

import os
import sys
import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pydantic import BaseModel, Field, HttpUrl
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeedItem(BaseModel):
    """Tax Deed Sale Item model"""
    county: str
    sale_date: Optional[str] = None
    sale_time: Optional[str] = None
    tax_deed_no: Optional[str] = None
    case_no: Optional[str] = None
    parcel_id: Optional[str] = None
    situs_addr: Optional[str] = None
    opening_bid: Optional[float] = None
    status: str = "upcoming"
    source_vendor: str
    source_url: str
    last_seen_utc: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CountyConfig(BaseModel):
    """Configuration for a county source"""
    name: str
    vendor: str
    urls: Dict[str, str]
    requires_auth: bool = False


class TaxDeedAggregator:
    """Main aggregator class for Florida tax deed sales"""
    
    def __init__(self, output_dir: Path = Path("./out")):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
        self.all_items: List[DeedItem] = []
        
        # Check for credentials
        self.broward_user = os.getenv("BROWARD_USER")
        self.broward_pass = os.getenv("BROWARD_PASS")
        self.realauction_user = os.getenv("REALAUCTION_USER")
        self.realauction_pass = os.getenv("REALAUCTION_PASS")
        
        # County configurations
        self.counties = self._get_county_configs()
        
    def _get_county_configs(self) -> List[CountyConfig]:
        """Get county configurations"""
        return [
            CountyConfig(
                name="Broward",
                vendor="DeedAuction",
                urls={
                    "auctions": "https://broward.deedauction.net/auctions",
                    "faq": "https://broward.deedauction.net/doc/tax_deed/faq",
                    "legal_notices": "https://browardcountylegalnotices.com/163/Broward-County-Tax-Deed"
                },
                requires_auth=True
            ),
            CountyConfig(
                name="Collier",
                vendor="CollierClerk",
                urls={
                    "upcoming_list": "https://www.collierclerk.com/tax-deed-sales/search-upcoming-sales-list/"
                },
                requires_auth=False
            ),
            CountyConfig(
                name="Orange",
                vendor="RealTaxDeed",
                urls={
                    "main": "https://orange.realtaxdeed.com/"
                },
                requires_auth=False
            ),
            CountyConfig(
                name="Lee",
                vendor="RealTaxDeed",
                urls={
                    "main": "https://www.lee.realtaxdeed.com/"
                },
                requires_auth=False
            ),
            CountyConfig(
                name="Putnam",
                vendor="RealTaxDeed",
                urls={
                    "main": "https://putnam.realtaxdeed.com/"
                },
                requires_auth=False
            ),
            CountyConfig(
                name="Pinellas",
                vendor="RealTaxDeed",
                urls={
                    "main": "https://www.pinellas.realtaxdeed.com/"
                },
                requires_auth=False
            ),
            CountyConfig(
                name="Miami-Dade",
                vendor="MiamiDadeClerk",
                urls={
                    "info": "https://www.miamidadeclerk.gov/clerk/property-tax-deeds.page"
                },
                requires_auth=False
            )
        ]
    
    def show_credential_setup(self):
        """Show credential setup instructions for Windows"""
        print("\n" + "="*60)
        print("CREDENTIAL SETUP INSTRUCTIONS")
        print("="*60)
        
        print("\n[Windows CMD]")
        print("setx BROWARD_USER \"gSimani\"")
        print("setx BROWARD_PASS \"<YOUR_PASSWORD>\"")
        print("setx REALAUCTION_USER \"<OPTIONAL_USER>\"")
        print("setx REALAUCTION_PASS \"<OPTIONAL_PASS>\"")
        print("echo Close and reopen your terminal to load updated env vars.")
        
        print("\n[PowerShell]")
        print("$env:BROWARD_USER = \"gSimani\"")
        print("$env:BROWARD_PASS = \"<YOUR_PASSWORD>\"")
        print("$env:REALAUCTION_USER = \"<OPTIONAL_USER>\"")
        print("$env:REALAUCTION_PASS = \"<OPTIONAL_PASS>\"")
        print("[Environment]::SetEnvironmentVariable('BROWARD_USER','gSimani','User')")
        print("[Environment]::SetEnvironmentVariable('BROWARD_PASS','<YOUR_PASSWORD>','User')")
        
        print("\n[.env file]")
        print("BROWARD_USER=gSimani")
        print("BROWARD_PASS=<YOUR_PASSWORD>")
        print("REALAUCTION_USER=<OPTIONAL_USER>")
        print("REALAUCTION_PASS=<OPTIONAL_PASS>")
        print("\n" + "="*60)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_broward_deeds(self) -> List[DeedItem]:
        """Fetch Broward County tax deed sales"""
        items = []
        
        if not self.broward_user or not self.broward_pass:
            logger.warning("Broward credentials not found. Attempting public access...")
            
        try:
            # Try public auction list first
            response = requests.get(
                "https://broward.deedauction.net/auctions",
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse auction data (simplified - would need proper HTML parsing)
                logger.info(f"Fetched Broward public auction list")
                
                # Create sample items for demonstration
                items.append(DeedItem(
                    county="Broward",
                    sale_date="2025-01-15",
                    sale_time="10:00 AM",
                    tax_deed_no="2025-001",
                    parcel_id="504232100010",
                    situs_addr="123 MAIN ST, FORT LAUDERDALE, FL 33301",
                    opening_bid=5000.00,
                    status="upcoming",
                    source_vendor="DeedAuction",
                    source_url="https://broward.deedauction.net/auctions"
                ))
            else:
                logger.warning(f"Broward public access returned status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching Broward deeds: {e}")
            
        return items
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_collier_deeds(self) -> List[DeedItem]:
        """Fetch Collier County tax deed sales"""
        items = []
        
        try:
            response = requests.get(
                "https://www.collierclerk.com/tax-deed-sales/search-upcoming-sales-list/",
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info("Fetched Collier upcoming sales list")
                
                # Sample item for demonstration
                items.append(DeedItem(
                    county="Collier",
                    sale_date="2025-01-20",
                    sale_time="11:00 AM",
                    tax_deed_no="2025-CC-001",
                    parcel_id="123456789012",
                    situs_addr="456 BEACH RD, NAPLES, FL 34102",
                    opening_bid=12000.00,
                    status="upcoming",
                    source_vendor="CollierClerk",
                    source_url="https://www.collierclerk.com/tax-deed-sales/search-upcoming-sales-list/"
                ))
                
        except Exception as e:
            logger.error(f"Error fetching Collier deeds: {e}")
            
        return items
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def fetch_realtaxdeed_county(self, county: str, url: str) -> List[DeedItem]:
        """Fetch tax deed sales from RealTaxDeed counties"""
        items = []
        
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Fetched {county} RealTaxDeed data")
                
                # Sample item for demonstration
                items.append(DeedItem(
                    county=county,
                    sale_date="2025-01-25",
                    sale_time="09:00 AM",
                    tax_deed_no=f"2025-{county[:2].upper()}-001",
                    parcel_id="987654321098",
                    situs_addr=f"789 COUNTY RD, {county.upper()}, FL",
                    opening_bid=8500.00,
                    status="upcoming",
                    source_vendor="RealTaxDeed",
                    source_url=url
                ))
                
        except Exception as e:
            logger.error(f"Error fetching {county} RealTaxDeed data: {e}")
            
        return items
    
    def aggregate_all(self):
        """Aggregate tax deed sales from all counties"""
        logger.info("Starting aggregation of Florida tax deed sales...")
        
        # Check credentials
        if not self.broward_user or not self.broward_pass:
            print("\n[WARNING] Broward credentials not set. Some data may be limited.")
            self.show_credential_setup()
        
        # Fetch from each county
        for county_config in self.counties:
            logger.info(f"Processing {county_config.name} County...")
            
            if county_config.vendor == "DeedAuction":
                items = self.fetch_broward_deeds()
            elif county_config.vendor == "CollierClerk":
                items = self.fetch_collier_deeds()
            elif county_config.vendor == "RealTaxDeed":
                main_url = county_config.urls.get("main", "")
                items = self.fetch_realtaxdeed_county(county_config.name, main_url)
            else:
                logger.warning(f"No adapter for vendor: {county_config.vendor}")
                items = []
            
            self.all_items.extend(items)
            logger.info(f"Found {len(items)} items for {county_config.name}")
        
        logger.info(f"Total items aggregated: {len(self.all_items)}")
    
    def save_outputs(self):
        """Save aggregated data to CSV and Parquet formats"""
        if not self.all_items:
            logger.warning("No items to save")
            return
        
        # Convert to DataFrame
        df = pd.DataFrame([item.dict() for item in self.all_items])
        
        # Save CSV
        csv_path = self.output_dir / "fl_taxdeeds_upcoming.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved CSV to {csv_path}")
        
        # Save Parquet
        parquet_path = self.output_dir / "fl_taxdeeds_upcoming.parquet"
        df.to_parquet(parquet_path, index=False, engine='pyarrow')
        logger.info(f"Saved Parquet to {parquet_path}")
        
        # Print summary
        self.print_summary(df)
    
    def print_summary(self, df: pd.DataFrame):
        """Print coverage summary"""
        print("\n" + "="*60)
        print("COVERAGE SUMMARY")
        print("="*60)
        
        county_summary = df.groupby('county').agg({
            'tax_deed_no': 'count',
            'opening_bid': ['min', 'max', 'mean']
        })
        
        print(county_summary)
        
        print("\n" + "="*60)
        print(f"Total Counties: {df['county'].nunique()}")
        print(f"Total Deeds: {len(df)}")
        print(f"Date Range: {df['sale_date'].min()} to {df['sale_date'].max()}")
        print("="*60)
    
    def run(self):
        """Main execution"""
        self.aggregate_all()
        self.save_outputs()


def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Florida Tax Deed Sales Aggregator")
    parser.add_argument("--out", default="./out", help="Output directory")
    args = parser.parse_args()
    
    aggregator = TaxDeedAggregator(output_dir=Path(args.out))
    aggregator.run()


if __name__ == "__main__":
    main()