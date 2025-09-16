"""
Florida Master Data Agent System
Comprehensive monitoring and download system for all Florida property data sources
"""

import os
import sys
import time
import json
import logging
import schedule
import requests
import paramiko
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, quote
from bs4 import BeautifulSoup
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from supabase import create_client
import httpx

# Fix proxy issue
_original_client_init = httpx.Client.__init__
def patched_client_init(self, *args, **kwargs):
    kwargs.pop('proxy', None)
    return _original_client_init(self, *args, **kwargs)
httpx.Client.__init__ = patched_client_init

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_agent_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BaseFloridaAgent:
    """Base class for all Florida data agents"""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
        self.supabase = self._init_supabase()
        self.data_dir = Path(f"data/{source_name.lower().replace(' ', '_')}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.monitoring_data = {
            'last_check': None,
            'files_found': 0,
            'files_downloaded': 0,
            'files_processed': 0,
            'errors': []
        }
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        return create_client(url, key)
    
    def log_activity(self, activity_type: str, details: dict):
        """Log agent activity to database"""
        try:
            self.supabase.table('agent_monitoring').insert({
                'agent_name': self.source_name,
                'activity_type': activity_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }).execute()
        except Exception as e:
            self.logger.error(f"Failed to log activity: {e}")
    
    def should_download(self, file_info: dict) -> bool:
        """Check if file should be downloaded"""
        # Check if file already exists and is recent
        local_path = self.data_dir / file_info['filename']
        if local_path.exists():
            # Check file age
            file_age = datetime.now() - datetime.fromtimestamp(local_path.stat().st_mtime)
            if file_age < timedelta(days=1):  # Skip if downloaded within last day
                return False
        return True
    
    async def download_file_async(self, url: str, filename: str) -> bool:
        """Async file download with progress tracking"""
        local_path = self.data_dir / filename
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(local_path, 'wb') as f:
                            f.write(content)
                        self.logger.info(f"Downloaded: {filename}")
                        return True
                    else:
                        self.logger.error(f"Download failed: {url} - Status {response.status}")
                        return False
            except Exception as e:
                self.logger.error(f"Download error: {e}")
                return False
    
    def monitor(self):
        """Monitor for new/updated files - to be implemented by subclasses"""
        raise NotImplementedError
    
    def process(self, file_path: Path):
        """Process downloaded file - to be implemented by subclasses"""
        raise NotImplementedError
    
    def load_to_database(self, table_name: str, data: pd.DataFrame):
        """Load data to Supabase"""
        try:
            # Convert DataFrame to records
            records = data.to_dict('records')
            
            # Insert in batches
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                self.supabase.table(table_name).insert(batch).execute()
            
            self.logger.info(f"Loaded {len(records)} records to {table_name}")
            return True
        except Exception as e:
            self.logger.error(f"Database load failed: {e}")
            return False


class FloridaRevenueAgent(BaseFloridaAgent):
    """Agent for Florida Revenue Data Portal"""
    
    BASE_URL = "https://floridarevenue.com/property/dataportal/"
    DATA_PATH = "Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/"
    
    def __init__(self):
        super().__init__("Florida Revenue")
        self.data_types = ['NAL', 'NAP', 'NAV', 'SDF', 'TPP', 'RER', 'CDF']
        self.current_years = self._detect_current_years()
    
    def _detect_current_years(self) -> Dict[str, str]:
        """Detect current year/period folders for each data type"""
        current_year = datetime.now().year
        years = {}
        
        # Common patterns to check
        patterns = [
            f"{current_year}P",     # Preliminary
            f"{current_year}F",     # Final
            f"{current_year-1}F",   # Previous year final
            f"TAX_ROLL_{current_year}",
            str(current_year)
        ]
        
        for data_type in self.data_types:
            for pattern in patterns:
                if self._check_directory_exists(data_type, pattern):
                    years[data_type] = pattern
                    self.logger.info(f"Found {data_type} data in folder: {pattern}")
                    break
        
        return years
    
    def _check_directory_exists(self, data_type: str, year: str) -> bool:
        """Check if a directory exists on the server"""
        if data_type == 'NAV':
            # NAV has subdirectories
            urls = [
                f"{self.BASE_URL}{self.DATA_PATH}{data_type}/{year}/NAV%20D/",
                f"{self.BASE_URL}{self.DATA_PATH}{data_type}/{year}/NAV%20N/"
            ]
        else:
            urls = [f"{self.BASE_URL}{self.DATA_PATH}{data_type}/{year}/"]
        
        for url in urls:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    return True
            except:
                continue
        
        return False
    
    def _list_files(self, data_type: str, year: str) -> List[Dict]:
        """List files in a directory"""
        files = []
        
        if data_type == 'NAV':
            # NAV has subdirectories
            subdirs = ['NAV%20D', 'NAV%20N']
            for subdir in subdirs:
                url = f"{self.BASE_URL}{self.DATA_PATH}{data_type}/{year}/{subdir}/"
                files.extend(self._parse_directory_listing(url, f"{data_type}_{subdir}"))
        else:
            url = f"{self.BASE_URL}{self.DATA_PATH}{data_type}/{year}/"
            files = self._parse_directory_listing(url, data_type)
        
        return files
    
    def _parse_directory_listing(self, url: str, data_type: str) -> List[Dict]:
        """Parse HTML directory listing"""
        files = []
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for file links (adjust based on actual HTML structure)
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    
                    # Filter for data files
                    if any(href.endswith(ext) for ext in ['.csv', '.txt', '.zip', '.gz']):
                        # Extract county code if present (16 = Broward)
                        county_code = None
                        if '16' in href:
                            county_code = '16'
                        
                        files.append({
                            'filename': os.path.basename(href),
                            'url': urljoin(url, href),
                            'data_type': data_type,
                            'county_code': county_code,
                            'size': self._get_file_size(link),
                            'modified': self._get_file_date(link)
                        })
        except Exception as e:
            self.logger.error(f"Failed to list files from {url}: {e}")
        
        return files
    
    def _get_file_size(self, link_element) -> Optional[int]:
        """Extract file size from directory listing"""
        # Parse size from HTML (implementation depends on actual structure)
        return None
    
    def _get_file_date(self, link_element) -> Optional[datetime]:
        """Extract file date from directory listing"""
        # Parse date from HTML (implementation depends on actual structure)
        return None
    
    def monitor(self):
        """Monitor all Florida Revenue data types"""
        self.monitoring_data['last_check'] = datetime.now()
        all_files = []
        
        for data_type, year in self.current_years.items():
            self.logger.info(f"Monitoring {data_type} for year {year}")
            files = self._list_files(data_type, year)
            
            # Filter for Broward County (code 16) or statewide files
            broward_files = [f for f in files if f['county_code'] == '16' or f['county_code'] is None]
            
            for file_info in broward_files:
                if self.should_download(file_info):
                    all_files.append(file_info)
        
        self.monitoring_data['files_found'] = len(all_files)
        self.log_activity('monitor', {
            'files_found': len(all_files),
            'data_types': list(self.current_years.keys())
        })
        
        return all_files
    
    async def download_files(self, files: List[Dict]):
        """Download multiple files concurrently"""
        tasks = []
        for file_info in files:
            task = self.download_file_async(file_info['url'], file_info['filename'])
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        self.monitoring_data['files_downloaded'] = sum(results)
        
        return results
    
    def process(self, file_path: Path):
        """Process Florida Revenue data file"""
        data_type = self._identify_data_type(file_path.name)
        
        if data_type == 'NAL':
            return self._process_nal(file_path)
        elif data_type == 'SDF':
            return self._process_sdf(file_path)
        elif data_type == 'NAV':
            return self._process_nav(file_path)
        elif data_type == 'NAP':
            return self._process_nap(file_path)
        elif data_type == 'TPP':
            return self._process_tpp(file_path)
        else:
            self.logger.warning(f"Unknown data type for file: {file_path}")
            return None
    
    def _identify_data_type(self, filename: str) -> Optional[str]:
        """Identify data type from filename"""
        filename_upper = filename.upper()
        for data_type in self.data_types:
            if data_type in filename_upper:
                return data_type
        return None
    
    def _process_nal(self, file_path: Path) -> pd.DataFrame:
        """Process NAL (Name/Address/Legal) file"""
        # NAL file structure based on user guide
        columns = [
            'PARCEL_ID', 'COUNTY_CODE', 'YEAR', 'OWNER_NAME',
            'OWNER_ADDR1', 'OWNER_ADDR2', 'OWNER_CITY', 'OWNER_STATE', 'OWNER_ZIP',
            'PHY_ADDR1', 'PHY_ADDR2', 'PHY_CITY', 'PHY_STATE', 'PHY_ZIPCD',
            'LEGAL_DESC', 'SUBDIVISION', 'LOT', 'BLOCK',
            'PROPERTY_USE', 'PROPERTY_USE_DESC', 'LAND_USE_CODE',
            'JUST_VALUE', 'ASSESSED_VALUE', 'TAXABLE_VALUE',
            'LAND_VALUE', 'BUILDING_VALUE', 'YEAR_BUILT',
            'TOTAL_LIVING_AREA', 'BEDROOMS', 'BATHROOMS'
        ]
        
        try:
            df = pd.read_csv(file_path, names=columns, low_memory=False)
            df['import_date'] = datetime.now()
            df['data_source'] = 'Florida Revenue NAL'
            
            # Load to database
            self.load_to_database('florida_nal', df)
            self.monitoring_data['files_processed'] += 1
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to process NAL file: {e}")
            return None
    
    def _process_sdf(self, file_path: Path) -> pd.DataFrame:
        """Process SDF (Sales Data File)"""
        columns = [
            'PARCEL_ID', 'SALE_DATE', 'SALE_PRICE', 'VI_CODE',
            'QUALIFIED_SALE', 'VACANT_IND', 'GRANTOR', 'GRANTEE',
            'OR_BOOK', 'OR_PAGE', 'CLERK_NO', 'SALE_TYPE'
        ]
        
        try:
            df = pd.read_csv(file_path, names=columns, low_memory=False)
            df['import_date'] = datetime.now()
            df['data_source'] = 'Florida Revenue SDF'
            
            # Convert date
            df['SALE_DATE'] = pd.to_datetime(df['SALE_DATE'], format='%Y%m%d', errors='coerce')
            
            # Load to database
            self.load_to_database('florida_sdf', df)
            self.monitoring_data['files_processed'] += 1
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to process SDF file: {e}")
            return None
    
    def _process_nav(self, file_path: Path) -> pd.DataFrame:
        """Process NAV (Non-Ad Valorem) file"""
        # Implementation for NAV processing
        pass
    
    def _process_nap(self, file_path: Path) -> pd.DataFrame:
        """Process NAP file"""
        # Implementation for NAP processing
        pass
    
    def _process_tpp(self, file_path: Path) -> pd.DataFrame:
        """Process TPP (Tangible Personal Property) file"""
        # Implementation for TPP processing
        pass


class SunbizSFTPAgent(BaseFloridaAgent):
    """Agent for Sunbiz SFTP data"""
    
    def __init__(self):
        super().__init__("Sunbiz SFTP")
        self.sftp_config = {
            'host': 'sftp.floridados.gov',
            'username': 'Public',
            'password': 'PubAccess1845!',
            'port': 22
        }
        self.sftp = None
        self.transport = None
    
    def _connect_sftp(self):
        """Establish SFTP connection"""
        try:
            self.transport = paramiko.Transport((self.sftp_config['host'], self.sftp_config['port']))
            self.transport.connect(
                username=self.sftp_config['username'],
                password=self.sftp_config['password']
            )
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            self.logger.info("Connected to Sunbiz SFTP")
            return True
        except Exception as e:
            self.logger.error(f"SFTP connection failed: {e}")
            return False
    
    def _disconnect_sftp(self):
        """Close SFTP connection"""
        if self.sftp:
            self.sftp.close()
        if self.transport:
            self.transport.close()
    
    def monitor(self):
        """Monitor Sunbiz SFTP for new files"""
        if not self._connect_sftp():
            return []
        
        files_to_download = []
        
        try:
            # List main directory files
            main_files = [
                'corpfilecopy.txt',      # Corporations
                'llcfilecopy.txt',       # LLCs
                'lpfilecopy.txt',        # Limited Partnerships
                'ficfilecopy.txt',       # Fictitious names
                'officefilecopy.txt',    # Officers/Directors
                'agentfilecopy.txt',     # Registered agents
                'principalfilecopy.txt', # Principal addresses
                'annualfilecopy.txt'     # Annual reports
            ]
            
            for filename in main_files:
                try:
                    # Get file info
                    file_stat = self.sftp.stat(filename)
                    file_info = {
                        'filename': filename,
                        'size': file_stat.st_size,
                        'modified': datetime.fromtimestamp(file_stat.st_mtime),
                        'path': filename
                    }
                    
                    if self.should_download(file_info):
                        files_to_download.append(file_info)
                except:
                    self.logger.warning(f"File not found: {filename}")
            
            # Check daily updates directory
            try:
                daily_files = self.sftp.listdir('daily')
                for filename in daily_files:
                    if filename.endswith('.txt'):
                        file_info = {
                            'filename': filename,
                            'path': f'daily/{filename}'
                        }
                        files_to_download.append(file_info)
            except:
                self.logger.warning("Daily directory not accessible")
            
            self.monitoring_data['files_found'] = len(files_to_download)
            self.log_activity('monitor', {'files_found': len(files_to_download)})
            
        finally:
            self._disconnect_sftp()
        
        return files_to_download
    
    def download_files(self, files: List[Dict]):
        """Download files from SFTP"""
        if not self._connect_sftp():
            return []
        
        downloaded = []
        
        try:
            for file_info in files:
                local_path = self.data_dir / file_info['filename']
                
                try:
                    self.sftp.get(file_info['path'], str(local_path))
                    self.logger.info(f"Downloaded: {file_info['filename']}")
                    downloaded.append(local_path)
                    self.monitoring_data['files_downloaded'] += 1
                except Exception as e:
                    self.logger.error(f"Failed to download {file_info['filename']}: {e}")
        finally:
            self._disconnect_sftp()
        
        return downloaded
    
    def process(self, file_path: Path):
        """Process Sunbiz data file"""
        filename = file_path.name.lower()
        
        if 'corp' in filename:
            return self._process_corporations(file_path)
        elif 'llc' in filename:
            return self._process_llc(file_path)
        elif 'office' in filename:
            return self._process_officers(file_path)
        elif 'agent' in filename:
            return self._process_agents(file_path)
        else:
            self.logger.warning(f"Unknown Sunbiz file type: {filename}")
            return None
    
    def _process_corporations(self, file_path: Path):
        """Process corporation file"""
        # Fixed-width format based on Sunbiz documentation
        widths = [12, 150, 40, 1, 8, 150, 40, 30, 2, 10, 150]
        names = [
            'entity_id', 'corporate_name', 'entity_type', 'status',
            'filing_date', 'principal_address', 'principal_city',
            'principal_state', 'principal_zip', 'fei_number', 'registered_agent'
        ]
        
        try:
            df = pd.read_fwf(file_path, widths=widths, names=names)
            df['import_date'] = datetime.now()
            df['data_source'] = 'Sunbiz Corporations'
            
            # Load to database
            self.load_to_database('sunbiz_entities', df)
            self.monitoring_data['files_processed'] += 1
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to process corporations file: {e}")
            return None
    
    def _process_llc(self, file_path: Path):
        """Process LLC file"""
        # Similar structure to corporations
        pass
    
    def _process_officers(self, file_path: Path):
        """Process officers file"""
        # Process officer/director information
        pass
    
    def _process_agents(self, file_path: Path):
        """Process registered agents file"""
        # Process agent information
        pass


class BrowardDailyIndexAgent(BaseFloridaAgent):
    """Agent for Broward County Daily Index files"""
    
    def __init__(self):
        super().__init__("Broward Daily Index")
        self.base_url = "https://www.broward.org/RecordsTaxesTreasury/Records/"
        self.daily_url = "Pages/DailyIndexExtractFiles.aspx"
    
    def monitor(self):
        """Monitor for daily index files"""
        files_to_download = []
        
        try:
            # Get the daily index page
            response = requests.get(self.base_url + self.daily_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Look for download links
                for link in soup.find_all('a'):
                    href = link.get('href', '')
                    
                    # Check for daily index files
                    if 'DailyIndex' in href and any(href.endswith(ext) for ext in ['.csv', '.txt', '.zip']):
                        file_info = {
                            'filename': os.path.basename(href),
                            'url': urljoin(self.base_url, href),
                            'date': self._extract_date_from_filename(os.path.basename(href))
                        }
                        
                        if self.should_download(file_info):
                            files_to_download.append(file_info)
            
            self.monitoring_data['files_found'] = len(files_to_download)
            self.log_activity('monitor', {'files_found': len(files_to_download)})
            
        except Exception as e:
            self.logger.error(f"Failed to monitor Broward daily index: {e}")
        
        return files_to_download
    
    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract date from daily index filename"""
        # Parse date from filename like DailyIndex_20240108.csv
        import re
        match = re.search(r'(\d{8})', filename)
        if match:
            try:
                return datetime.strptime(match.group(1), '%Y%m%d')
            except:
                pass
        return None
    
    def process(self, file_path: Path):
        """Process Broward daily index file"""
        try:
            # Read according to ExportFilesLayout.pdf specification
            df = pd.read_csv(file_path, low_memory=False)
            
            # Process different record types
            property_transfers = df[df['DOCUMENT_TYPE'].isin(['DEED', 'WARRANTY DEED', 'QUIT CLAIM'])]
            mortgages = df[df['DOCUMENT_TYPE'].isin(['MORTGAGE', 'MODIFICATION'])]
            liens = df[df['DOCUMENT_TYPE'].isin(['LIEN', 'TAX LIEN', 'JUDGMENT'])]
            
            # Add metadata
            df['import_date'] = datetime.now()
            df['data_source'] = 'Broward Daily Index'
            
            # Load to database
            self.load_to_database('broward_daily_index', df)
            self.monitoring_data['files_processed'] += 1
            
            return df
        except Exception as e:
            self.logger.error(f"Failed to process daily index: {e}")
            return None


class FloridaMasterOrchestrator:
    """Master orchestrator for all Florida data agents"""
    
    def __init__(self):
        self.agents = {
            'florida_revenue': FloridaRevenueAgent(),
            'sunbiz': SunbizSFTPAgent(),
            'broward_daily': BrowardDailyIndexAgent()
        }
        
        self.logger = logging.getLogger(__name__)
        self.supabase = self._init_supabase()
        self._setup_schedule()
    
    def _init_supabase(self):
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        return create_client(url, key)
    
    def _setup_schedule(self):
        """Setup scheduled tasks for all agents"""
        # Florida Revenue - Different schedules for different data types
        schedule.every().monday.at("03:00").do(self.run_agent, 'florida_revenue')
        
        # Sunbiz - Weekly main data, daily updates
        schedule.every().sunday.at("02:00").do(self.run_agent, 'sunbiz')
        schedule.every().day.at("02:30").do(self.run_sunbiz_daily)
        
        # Broward Daily Index
        schedule.every().day.at("06:00").do(self.run_agent, 'broward_daily')
    
    def run_agent(self, agent_name: str):
        """Run a specific agent"""
        if agent_name not in self.agents:
            self.logger.error(f"Unknown agent: {agent_name}")
            return
        
        agent = self.agents[agent_name]
        self.logger.info(f"Running agent: {agent_name}")
        
        try:
            # Monitor for new files
            files = agent.monitor()
            
            if files:
                self.logger.info(f"Found {len(files)} files to download")
                
                # Download files
                if isinstance(agent, FloridaRevenueAgent):
                    # Use async download for Florida Revenue
                    asyncio.run(agent.download_files(files))
                else:
                    agent.download_files(files)
                
                # Process downloaded files
                for file_path in agent.data_dir.glob('*'):
                    if file_path.is_file():
                        agent.process(file_path)
            
            # Update monitoring status
            self._update_agent_status(agent_name, 'success', agent.monitoring_data)
            
        except Exception as e:
            self.logger.error(f"Agent {agent_name} failed: {e}")
            self._update_agent_status(agent_name, 'failed', {'error': str(e)})
    
    def run_sunbiz_daily(self):
        """Special handler for Sunbiz daily updates"""
        # Check for daily update files only
        pass
    
    def _update_agent_status(self, agent_name: str, status: str, details: dict):
        """Update agent status in database"""
        try:
            self.supabase.table('agent_monitoring').insert({
                'agent_name': agent_name,
                'status': status,
                'last_run': datetime.now().isoformat(),
                'details': details
            }).execute()
        except Exception as e:
            self.logger.error(f"Failed to update agent status: {e}")
    
    def run_once(self):
        """Run all agents once"""
        for agent_name in self.agents:
            self.run_agent(agent_name)
    
    def run_continuous(self):
        """Run agents on schedule continuously"""
        self.logger.info("Starting Florida Master Orchestrator")
        
        # Run once at startup
        self.run_once()
        
        # Then run on schedule
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def get_status(self) -> dict:
        """Get status of all agents"""
        status = {}
        
        for agent_name, agent in self.agents.items():
            status[agent_name] = {
                'last_check': agent.monitoring_data.get('last_check'),
                'files_found': agent.monitoring_data.get('files_found', 0),
                'files_downloaded': agent.monitoring_data.get('files_downloaded', 0),
                'files_processed': agent.monitoring_data.get('files_processed', 0),
                'errors': len(agent.monitoring_data.get('errors', []))
            }
        
        return status


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Master Data Agent System')
    parser.add_argument('--mode', choices=['once', 'continuous', 'status'], 
                      default='once', help='Run mode')
    parser.add_argument('--agent', help='Run specific agent only')
    
    args = parser.parse_args()
    
    orchestrator = FloridaMasterOrchestrator()
    
    if args.mode == 'once':
        if args.agent:
            orchestrator.run_agent(args.agent)
        else:
            orchestrator.run_once()
    elif args.mode == 'continuous':
        orchestrator.run_continuous()
    elif args.mode == 'status':
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    main()