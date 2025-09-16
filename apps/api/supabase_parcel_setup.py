"""
Supabase Setup for Florida Parcel Data
Configures Supabase database, downloads data, and sets up monitoring
"""

import os
import json
import hashlib
import requests
import zipfile
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import asyncio
import aiohttp
from supabase import create_client, Client
import pandas as pd
import geopandas as gpd
from shapely import wkt
from shapely.geometry import mapping
import schedule
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseParcelManager:
    """
    Manages Florida parcel data in Supabase with automatic updates
    """
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.data_path = Path("./data/florida_parcels")
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # Florida Revenue data portal URLs
        self.base_url = "https://floridarevenue.com/property/Documents/GISData"
        self.counties = [
            "BROWARD", "MIAMI-DADE", "PALM BEACH", "MONROE", "MARTIN",
            "ST. LUCIE", "INDIAN RIVER", "OKEECHOBEE", "HENDRY", "COLLIER",
            "LEE", "CHARLOTTE", "SARASOTA", "MANATEE", "DESOTO", "GLADES"
        ]
        self.special_condo_counties = ["MIAMI-DADE", "ST. JOHNS"]
        
    async def setup_database_schema(self):
        """
        Create Supabase tables for parcel data
        """
        logger.info("Setting up Supabase database schema")
        
        # SQL for creating tables
        sql_commands = [
            # Main parcels table
            """
            CREATE TABLE IF NOT EXISTS florida_parcels (
                id BIGSERIAL PRIMARY KEY,
                parcel_id VARCHAR(50) NOT NULL,
                county VARCHAR(50) NOT NULL,
                year INTEGER NOT NULL,
                geometry JSONB,
                centroid JSONB,
                area_sqft FLOAT,
                
                -- NAL attributes
                owner_name VARCHAR(255),
                owner_addr1 VARCHAR(255),
                owner_city VARCHAR(100),
                owner_state VARCHAR(2),
                owner_zip VARCHAR(10),
                
                phy_addr1 VARCHAR(255),
                phy_city VARCHAR(100),
                phy_zipcd VARCHAR(10),
                
                legal_desc TEXT,
                subdivision VARCHAR(255),
                
                -- Valuations
                just_value FLOAT,
                assessed_value FLOAT,
                taxable_value FLOAT,
                land_value FLOAT,
                building_value FLOAT,
                
                -- Property details
                year_built INTEGER,
                total_living_area FLOAT,
                bedrooms INTEGER,
                bathrooms FLOAT,
                
                -- Sales info
                sale_date TIMESTAMP,
                sale_price FLOAT,
                
                -- Data quality
                match_status VARCHAR(20),
                is_redacted BOOLEAN DEFAULT FALSE,
                data_source VARCHAR(20),
                
                -- Metadata
                import_date TIMESTAMP DEFAULT NOW(),
                update_date TIMESTAMP,
                data_hash VARCHAR(64),
                
                -- Indexes
                UNIQUE(parcel_id, county, year)
            );
            
            CREATE INDEX IF NOT EXISTS idx_parcel_county ON florida_parcels(county);
            CREATE INDEX IF NOT EXISTS idx_parcel_year ON florida_parcels(year);
            CREATE INDEX IF NOT EXISTS idx_owner_name ON florida_parcels(owner_name);
            CREATE INDEX IF NOT EXISTS idx_phy_addr ON florida_parcels(phy_addr1);
            CREATE INDEX IF NOT EXISTS idx_taxable_value ON florida_parcels(taxable_value);
            """,
            
            # Condo units table
            """
            CREATE TABLE IF NOT EXISTS florida_condo_units (
                id BIGSERIAL PRIMARY KEY,
                parcel_id VARCHAR(50),
                county VARCHAR(50),
                unit_number VARCHAR(50),
                floor INTEGER,
                building VARCHAR(50),
                unit_sqft FLOAT,
                unit_owner VARCHAR(255),
                unit_assessed_value FLOAT,
                import_date TIMESTAMP DEFAULT NOW()
            );
            """,
            
            # Data sources monitoring table
            """
            CREATE TABLE IF NOT EXISTS data_source_monitor (
                id BIGSERIAL PRIMARY KEY,
                source_url TEXT NOT NULL UNIQUE,
                source_type VARCHAR(20),
                county VARCHAR(50),
                year INTEGER,
                file_name VARCHAR(255),
                file_size BIGINT,
                file_hash VARCHAR(64),
                last_modified TIMESTAMP,
                last_checked TIMESTAMP DEFAULT NOW(),
                last_downloaded TIMESTAMP,
                status VARCHAR(20),
                change_detected BOOLEAN DEFAULT FALSE,
                notes TEXT
            );
            """,
            
            # Update history table
            """
            CREATE TABLE IF NOT EXISTS parcel_update_history (
                id BIGSERIAL PRIMARY KEY,
                county VARCHAR(50),
                update_type VARCHAR(50),
                records_added INTEGER,
                records_updated INTEGER,
                records_deleted INTEGER,
                processing_time_seconds FLOAT,
                success BOOLEAN,
                error_message TEXT,
                update_date TIMESTAMP DEFAULT NOW()
            );
            """,
            
            # Agent monitoring configuration
            """
            CREATE TABLE IF NOT EXISTS monitoring_agents (
                id BIGSERIAL PRIMARY KEY,
                agent_name VARCHAR(100) NOT NULL UNIQUE,
                agent_type VARCHAR(50),
                monitoring_urls JSONB,
                check_frequency_hours INTEGER DEFAULT 24,
                last_run TIMESTAMP,
                next_run TIMESTAMP,
                enabled BOOLEAN DEFAULT TRUE,
                notification_settings JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """,
            
            # Enable Row Level Security
            """
            ALTER TABLE florida_parcels ENABLE ROW LEVEL SECURITY;
            ALTER TABLE florida_condo_units ENABLE ROW LEVEL SECURITY;
            ALTER TABLE data_source_monitor ENABLE ROW LEVEL SECURITY;
            
            -- Create policies for authenticated users
            CREATE POLICY "Public read access" ON florida_parcels 
                FOR SELECT USING (is_redacted = FALSE);
            
            CREATE POLICY "Admin full access" ON florida_parcels 
                FOR ALL USING (auth.jwt() ->> 'role' = 'admin');
            """
        ]
        
        # Execute SQL commands
        for sql in sql_commands:
            try:
                # Note: Supabase doesn't directly execute raw SQL through the client
                # You'll need to run these in Supabase SQL editor or use migrations
                logger.info(f"SQL to execute in Supabase:\n{sql[:100]}...")
            except Exception as e:
                logger.error(f"Error setting up schema: {e}")
    
    def generate_data_urls(self, year: int = 2024) -> List[Dict]:
        """
        Generate URLs for all Florida parcel data files
        """
        urls = []
        
        for county in self.counties:
            # PIN shapefile (geometry only)
            urls.append({
                'url': f"{self.base_url}/{year}/PIN_{county}_{year}.zip",
                'type': 'PIN',
                'county': county,
                'year': year,
                'filename': f"PIN_{county}_{year}.zip"
            })
            
            # PAR shapefile (geometry + attributes)
            urls.append({
                'url': f"{self.base_url}/{year}/PAR_{county}_{year}.zip",
                'type': 'PAR',
                'county': county,
                'year': year,
                'filename': f"PAR_{county}_{year}.zip"
            })
            
            # NAL file (attributes in DBF format)
            urls.append({
                'url': f"{self.base_url}/{year}/NAL_{county}_{year}.dbf",
                'type': 'NAL',
                'county': county,
                'year': year,
                'filename': f"NAL_{county}_{year}.dbf"
            })
            
            # Condo files for special counties
            if county in self.special_condo_counties:
                urls.append({
                    'url': f"{self.base_url}/{year}/CONDO_{county}_{year}.zip",
                    'type': 'CONDO',
                    'county': county,
                    'year': year,
                    'filename': f"CONDO_{county}_{year}.zip"
                })
        
        return urls
    
    async def download_file(self, url: str, filepath: Path) -> Optional[str]:
        """
        Download a file and return its hash
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Save file
                        filepath.parent.mkdir(parents=True, exist_ok=True)
                        filepath.write_bytes(content)
                        
                        # Calculate hash
                        file_hash = hashlib.sha256(content).hexdigest()
                        
                        logger.info(f"Downloaded: {filepath.name} ({len(content)/1024/1024:.2f} MB)")
                        return file_hash
                    else:
                        logger.warning(f"Failed to download {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return None
    
    async def check_for_updates(self, url_info: Dict) -> bool:
        """
        Check if a data source has been updated
        """
        try:
            # Check current file info in database
            result = self.supabase.table('data_source_monitor').select('*').eq(
                'source_url', url_info['url']
            ).execute()
            
            if not result.data:
                # New file, needs download
                return True
            
            stored_info = result.data[0]
            
            # Check file headers for modifications
            async with aiohttp.ClientSession() as session:
                async with session.head(url_info['url']) as response:
                    if response.status == 200:
                        # Check last modified header
                        last_modified = response.headers.get('Last-Modified')
                        content_length = response.headers.get('Content-Length')
                        
                        if last_modified:
                            # Compare with stored last_modified
                            return last_modified != stored_info.get('last_modified')
                        elif content_length:
                            # Fall back to file size comparison
                            return int(content_length) != stored_info.get('file_size')
                    
            return False
        except Exception as e:
            logger.error(f"Error checking updates for {url_info['url']}: {e}")
            return False
    
    async def download_and_process_county(self, county: str, year: int = 2024):
        """
        Download and process all data for a specific county
        """
        logger.info(f"Processing {county} County, Year {year}")
        
        # Generate URLs for this county
        urls = [u for u in self.generate_data_urls(year) if u['county'] == county]
        
        for url_info in urls:
            try:
                # Check if update needed
                needs_update = await self.check_for_updates(url_info)
                
                if not needs_update:
                    logger.info(f"No update needed for {url_info['filename']}")
                    continue
                
                # Download file
                filepath = self.data_path / url_info['filename']
                file_hash = await self.download_file(url_info['url'], filepath)
                
                if file_hash:
                    # Update monitoring record
                    self.supabase.table('data_source_monitor').upsert({
                        'source_url': url_info['url'],
                        'source_type': url_info['type'],
                        'county': county,
                        'year': year,
                        'file_name': url_info['filename'],
                        'file_size': filepath.stat().st_size,
                        'file_hash': file_hash,
                        'last_checked': datetime.now().isoformat(),
                        'last_downloaded': datetime.now().isoformat(),
                        'status': 'downloaded',
                        'change_detected': needs_update
                    }).execute()
                    
                    # Process based on file type
                    if url_info['type'] == 'PAR':
                        await self.process_par_shapefile(filepath, county, year)
                    elif url_info['type'] == 'NAL':
                        await self.process_nal_file(filepath, county, year)
                    elif url_info['type'] == 'CONDO':
                        await self.process_condo_file(filepath, county, year)
                        
            except Exception as e:
                logger.error(f"Error processing {url_info['filename']}: {e}")
                
                # Log error to monitoring table
                self.supabase.table('data_source_monitor').upsert({
                    'source_url': url_info['url'],
                    'status': 'error',
                    'notes': str(e),
                    'last_checked': datetime.now().isoformat()
                }).execute()
    
    async def process_par_shapefile(self, filepath: Path, county: str, year: int):
        """
        Process PAR shapefile and upload to Supabase
        """
        logger.info(f"Processing PAR shapefile: {filepath}")
        
        try:
            # Extract if zipped
            if filepath.suffix == '.zip':
                extract_dir = self.data_path / "temp" / filepath.stem
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Find shapefile
                shp_file = list(extract_dir.glob("*.shp"))[0]
            else:
                shp_file = filepath
            
            # Read shapefile
            gdf = gpd.read_file(shp_file)
            
            # Convert geometry to GeoJSON for storage
            records = []
            for _, row in gdf.iterrows():
                record = {
                    'parcel_id': row.get('PARCELNO', ''),
                    'county': county,
                    'year': year,
                    'geometry': mapping(row.geometry) if row.geometry else None,
                    'centroid': mapping(row.geometry.centroid) if row.geometry else None,
                    'area_sqft': row.geometry.area if row.geometry else None,
                    'data_source': 'PAR',
                    'import_date': datetime.now().isoformat()
                }
                
                # Add NAL attributes if present in PAR file
                nal_fields = ['OWNER_NAME', 'PHY_ADDR1', 'PHY_CITY', 'PHY_ZIPCD',
                             'JUST_VALUE', 'ASSESSED_VALUE', 'TAXABLE_VALUE']
                for field in nal_fields:
                    if field in row:
                        record[field.lower()] = row[field]
                
                # Generate hash for change detection
                record['data_hash'] = hashlib.md5(
                    json.dumps(record, sort_keys=True).encode()
                ).hexdigest()
                
                records.append(record)
            
            # Batch upload to Supabase
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                self.supabase.table('florida_parcels').upsert(batch).execute()
            
            logger.info(f"Uploaded {len(records)} parcels for {county}")
            
            # Log success
            self.supabase.table('parcel_update_history').insert({
                'county': county,
                'update_type': 'PAR_import',
                'records_added': len(records),
                'success': True,
                'update_date': datetime.now().isoformat()
            }).execute()
            
        except Exception as e:
            logger.error(f"Error processing PAR shapefile: {e}")
            
            # Log error
            self.supabase.table('parcel_update_history').insert({
                'county': county,
                'update_type': 'PAR_import',
                'success': False,
                'error_message': str(e),
                'update_date': datetime.now().isoformat()
            }).execute()
    
    async def process_nal_file(self, filepath: Path, county: str, year: int):
        """
        Process NAL file and update existing parcels
        """
        logger.info(f"Processing NAL file: {filepath}")
        
        # Implementation would follow similar pattern to process_par_shapefile
        # Read DBF, match with existing parcels, update attributes
        pass
    
    async def process_condo_file(self, filepath: Path, county: str, year: int):
        """
        Process condo file for special counties
        """
        logger.info(f"Processing condo file: {filepath}")
        
        # Implementation for condo-specific processing
        pass
    
    async def download_all_counties(self):
        """
        Download data for all configured counties
        """
        logger.info(f"Starting download for {len(self.counties)} counties")
        
        tasks = []
        for county in self.counties:
            task = self.download_and_process_county(county)
            tasks.append(task)
        
        # Process counties in batches to avoid overwhelming the server
        batch_size = 3
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            await asyncio.gather(*batch)
        
        logger.info("All counties processed")
    
    def setup_monitoring_agents(self):
        """
        Configure automated monitoring agents
        """
        logger.info("Setting up monitoring agents")
        
        agents = [
            {
                'agent_name': 'Florida_PTO_Monitor',
                'agent_type': 'data_source',
                'monitoring_urls': self.generate_data_urls(),
                'check_frequency_hours': 24,
                'enabled': True,
                'notification_settings': {
                    'email': 'admin@westbocaexecutiveoffice.com',
                    'slack': '#data-updates',
                    'on_change': True,
                    'on_error': True
                }
            },
            {
                'agent_name': 'Data_Quality_Agent',
                'agent_type': 'quality_check',
                'check_frequency_hours': 6,
                'enabled': True,
                'notification_settings': {
                    'thresholds': {
                        'unmatched_ratio': 0.1,
                        'invalid_geometry_ratio': 0.05
                    }
                }
            },
            {
                'agent_name': 'Update_Scheduler',
                'agent_type': 'scheduler',
                'check_frequency_hours': 1,
                'enabled': True,
                'notification_settings': {
                    'scheduled_times': ['02:00', '14:00']
                }
            }
        ]
        
        for agent in agents:
            self.supabase.table('monitoring_agents').upsert(agent).execute()
        
        logger.info(f"Configured {len(agents)} monitoring agents")
    
    async def run_monitoring_cycle(self):
        """
        Run a monitoring cycle to check for updates
        """
        logger.info("Running monitoring cycle")
        
        # Get enabled agents
        agents = self.supabase.table('monitoring_agents').select('*').eq(
            'enabled', True
        ).execute()
        
        for agent in agents.data:
            try:
                # Check if it's time to run
                next_run = agent.get('next_run')
                if next_run and datetime.fromisoformat(next_run) > datetime.now():
                    continue
                
                logger.info(f"Running agent: {agent['agent_name']}")
                
                if agent['agent_type'] == 'data_source':
                    # Check for data updates
                    urls = agent.get('monitoring_urls', [])
                    changes_detected = []
                    
                    for url_info in urls:
                        has_update = await self.check_for_updates(url_info)
                        if has_update:
                            changes_detected.append(url_info)
                    
                    if changes_detected:
                        logger.info(f"Changes detected: {len(changes_detected)} files")
                        await self.notify_changes(agent, changes_detected)
                        
                        # Trigger download for changed files
                        for url_info in changes_detected:
                            await self.download_and_process_county(
                                url_info['county'], 
                                url_info['year']
                            )
                
                # Update agent last run time
                self.supabase.table('monitoring_agents').update({
                    'last_run': datetime.now().isoformat(),
                    'next_run': (
                        datetime.now() + 
                        timedelta(hours=agent['check_frequency_hours'])
                    ).isoformat()
                }).eq('id', agent['id']).execute()
                
            except Exception as e:
                logger.error(f"Error running agent {agent['agent_name']}: {e}")
    
    async def notify_changes(self, agent: Dict, changes: List[Dict]):
        """
        Send notifications about detected changes
        """
        settings = agent.get('notification_settings', {})
        
        if settings.get('on_change'):
            message = f"""
            Data Update Detected!
            
            Agent: {agent['agent_name']}
            Files Changed: {len(changes)}
            Counties: {', '.join(set(c['county'] for c in changes))}
            Time: {datetime.now()}
            
            Details:
            {json.dumps(changes, indent=2)}
            """
            
            # Send email notification (implement with your email service)
            if settings.get('email'):
                logger.info(f"Email notification to: {settings['email']}")
                # await send_email(settings['email'], "Parcel Data Update", message)
            
            # Send Slack notification (implement with your Slack webhook)
            if settings.get('slack'):
                logger.info(f"Slack notification to: {settings['slack']}")
                # await send_slack(settings['slack'], message)
    
    def start_scheduler(self):
        """
        Start the background scheduler for automated monitoring
        """
        logger.info("Starting automated scheduler")
        
        # Schedule monitoring cycles
        schedule.every(1).hours.do(lambda: asyncio.run(self.run_monitoring_cycle()))
        schedule.every(24).hours.do(lambda: asyncio.run(self.download_all_counties()))
        
        # Run scheduler in background
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


async def main():
    """
    Main entry point for setting up and running the system
    """
    # Initialize with your Supabase credentials
    SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-project.supabase.co")
    SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "your-anon-key")
    
    manager = SupabaseParcelManager(SUPABASE_URL, SUPABASE_KEY)
    
    # Initial setup
    logger.info("Setting up Supabase parcel data system")
    await manager.setup_database_schema()
    manager.setup_monitoring_agents()
    
    # Initial download
    logger.info("Starting initial data download")
    await manager.download_all_counties()
    
    # Start monitoring
    logger.info("Starting monitoring agents")
    await manager.run_monitoring_cycle()
    
    # Start scheduler (this runs indefinitely)
    # manager.start_scheduler()


if __name__ == "__main__":
    asyncio.run(main())