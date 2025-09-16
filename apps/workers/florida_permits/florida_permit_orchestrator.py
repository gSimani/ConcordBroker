"""
Florida Statewide Permit Orchestrator
Manages permit collection across all 67 Florida counties and 400+ municipalities
"""

import os
import sys
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import schedule
import time

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

from base_supabase_db import BaseSupabaseDB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('florida_permit_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CountyConfig:
    """Configuration for a Florida county's permit system"""
    county_code: str
    county_name: str
    population: int
    municipalities: List[str]
    system_type: str  # 'advanced', 'basic', 'legacy'
    priority: int     # 1=highest, 5=lowest
    base_url: str
    scraper_class: str
    api_key: Optional[str] = None
    rate_limit: int = 10  # requests per minute
    enabled: bool = True

@dataclass
class MunicipalityConfig:
    """Configuration for a municipality's permit system"""
    name: str
    county_code: str
    population: int
    tier: int  # 1=large, 2=medium, 3=small
    system_type: str
    base_url: Optional[str]
    scraper_class: Optional[str]
    enabled: bool = True

class FloridaPermitOrchestrator(BaseSupabaseDB):
    """Orchestrates permit collection across all of Florida"""
    
    def __init__(self):
        """Initialize the orchestrator"""
        super().__init__()
        
        self.data_dir = Path("data/florida_permits")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load county and municipality configurations
        self.counties = self._load_county_configs()
        self.municipalities = self._load_municipality_configs()
        
        # Processing statistics
        self.stats = {
            'counties_processed': 0,
            'municipalities_processed': 0,
            'permits_collected': 0,
            'permits_failed': 0,
            'last_full_run': None,
            'errors': []
        }
        
        # Rate limiting and concurrent processing
        self.max_concurrent = 10
        self.session_timeout = 300  # 5 minutes
        
    def _load_county_configs(self) -> Dict[str, CountyConfig]:
        """Load configuration for all 67 Florida counties"""
        counties = {}
        
        # High Priority Counties (Major Population Centers)
        high_priority = [
            CountyConfig("06", "Broward", 1944375, ["Hollywood", "Fort Lauderdale", "Pompano Beach"], "advanced", 1,
                        "https://www.broward.org/Development/Building/", "BrowardPermitScraper"),
            CountyConfig("25", "Miami-Dade", 2701767, ["Miami", "Hialeah", "Homestead"], "advanced", 1,
                        "https://www.miamidade.gov/permits/", "MiamiDadePermitScraper"),
            CountyConfig("50", "Palm Beach", 1492191, ["West Palm Beach", "Boca Raton", "Delray Beach"], "advanced", 1,
                        "https://www.pbcgov.org/pzb/planning/building/", "PalmBeachPermitScraper"),
            CountyConfig("48", "Orange", 1393452, ["Orlando", "Winter Park", "Winter Garden"], "advanced", 1,
                        "https://www.orangecountyfl.net/tabid/2046/", "OrangeCountyPermitScraper"),
            CountyConfig("28", "Hillsborough", 1459762, ["Tampa", "Temple Terrace", "Plant City"], "advanced", 1,
                        "https://www.hillsboroughcounty.org/building/", "HillsboroughPermitScraper"),
            CountyConfig("15", "Duval", 995567, ["Jacksonville"], "advanced", 2,
                        "https://www.coj.net/departments/planning-and-development/", "DuvalPermitScraper"),
            CountyConfig("52", "Pinellas", 959107, ["St. Petersburg", "Clearwater", "Largo"], "advanced", 2,
                        "https://www.pinellascounty.org/building/", "PinellasPermitScraper"),
        ]
        
        # Medium Priority Counties (100K-500K population)
        medium_priority = [
            CountyConfig("33", "Lee", 760822, ["Fort Myers", "Cape Coral"], "basic", 2,
                        "https://www.leegov.com/dcd/building/", "LeeCountyPermitScraper"),
            CountyConfig("12", "Collier", 384902, ["Naples", "Marco Island"], "basic", 2,
                        "https://www.colliercountyfl.gov/", "CollierCountyPermitScraper"),
            CountyConfig("53", "Polk", 725046, ["Lakeland", "Winter Haven"], "basic", 2,
                        "https://www.polk-county.net/", "PolkCountyPermitScraper"),
            CountyConfig("64", "Volusia", 553543, ["Daytona Beach", "Deltona"], "basic", 3,
                        "https://www.volusia.org/", "VolusiaCountyPermitScraper"),
            CountyConfig("58", "Sarasota", 434263, ["Sarasota", "Venice"], "basic", 3,
                        "https://www.scgov.net/", "SarasotaCountyPermitScraper"),
        ]
        
        # Add all counties to the collection
        for county in high_priority + medium_priority:
            counties[county.county_code] = county
        
        # Add remaining 55+ counties with basic/legacy systems
        remaining_counties = self._get_remaining_counties()
        for county in remaining_counties:
            counties[county.county_code] = county
        
        return counties
    
    def _get_remaining_counties(self) -> List[CountyConfig]:
        """Get configuration for remaining Florida counties"""
        # This would include all remaining counties with basic or legacy systems
        remaining = []
        
        # Sample of remaining counties
        county_data = [
            ("01", "Alachua", 278468, ["Gainesville"], "basic"),
            ("05", "Brevard", 606612, ["Melbourne", "Palm Bay"], "basic"),
            ("31", "Indian River", 156849, ["Vero Beach"], "basic"),
            ("55", "St. Johns", 273425, ["St. Augustine"], "basic"),
            ("56", "St. Lucie", 329226, ["Port St. Lucie"], "basic"),
            # ... Continue for all remaining counties
        ]
        
        for code, name, pop, munis, system_type in county_data:
            priority = 3 if pop > 200000 else 4 if pop > 100000 else 5
            remaining.append(CountyConfig(
                code, name, pop, munis, system_type, priority,
                f"https://www.{name.lower().replace(' ', '').replace('-', '')}countyfl.gov/",
                "GenericCountyPermitScraper"
            ))
        
        return remaining
    
    def _load_municipality_configs(self) -> Dict[str, MunicipalityConfig]:
        """Load configuration for major Florida municipalities"""
        municipalities = {}
        
        # Tier 1 Cities (100K+ population)
        tier1_cities = [
            MunicipalityConfig("Jacksonville", "15", 949611, 1, "advanced", 
                             "https://www.coj.net/", "JacksonvillePermitScraper"),
            MunicipalityConfig("Miami", "25", 442241, 1, "advanced",
                             "https://www.miamigov.com/", "MiamiPermitScraper"),
            MunicipalityConfig("Tampa", "28", 384959, 1, "advanced",
                             "https://www.tampa.gov/", "TampaPermitScraper"),
            MunicipalityConfig("Orlando", "48", 307573, 1, "advanced",
                             "https://www.orlando.gov/", "OrlandoPermitScraper"),
            MunicipalityConfig("St. Petersburg", "52", 258308, 1, "advanced",
                             "https://www.stpete.org/", "StPetePermitScraper"),
        ]
        
        for city in tier1_cities:
            municipalities[city.name] = city
        
        return municipalities
    
    def create_florida_permit_tables(self):
        """Create statewide permit database tables"""
        logger.info("Creating Florida permit database tables")
        
        # Main Florida permits table
        permits_sql = """
        CREATE TABLE IF NOT EXISTS florida_permits (
            id BIGSERIAL PRIMARY KEY,
            permit_number VARCHAR(100) NOT NULL,
            county_code VARCHAR(2) NOT NULL,
            county_name VARCHAR(100) NOT NULL,
            municipality VARCHAR(100),
            jurisdiction_type VARCHAR(50) DEFAULT 'county',
            permit_type VARCHAR(100),
            description TEXT,
            status VARCHAR(50),
            applicant_name VARCHAR(255),
            contractor_name VARCHAR(255),
            contractor_license VARCHAR(50),
            property_address VARCHAR(500),
            parcel_id VARCHAR(100),
            folio_number VARCHAR(50),
            issue_date DATE,
            expiration_date DATE,
            final_date DATE,
            valuation DECIMAL(15,2),
            permit_fee DECIMAL(10,2),
            source_system VARCHAR(50) NOT NULL,
            source_url TEXT,
            coordinates POINT,
            raw_data JSONB,
            scraped_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(permit_number, county_code, source_system)
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_florida_permits_county ON florida_permits(county_code);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_municipality ON florida_permits(municipality);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_permit_number ON florida_permits(permit_number);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_issue_date ON florida_permits(issue_date);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_parcel_id ON florida_permits(parcel_id);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_contractor_license ON florida_permits(contractor_license);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_coordinates ON florida_permits USING GIST(coordinates);
        CREATE INDEX IF NOT EXISTS idx_florida_permits_jurisdiction ON florida_permits(jurisdiction_type, county_code);
        """
        
        # Processing log table
        log_sql = """
        CREATE TABLE IF NOT EXISTS florida_permit_processing_log (
            id BIGSERIAL PRIMARY KEY,
            county_code VARCHAR(2),
            municipality VARCHAR(100),
            source_system VARCHAR(50),
            processing_date DATE,
            permits_found INTEGER DEFAULT 0,
            permits_loaded INTEGER DEFAULT 0,
            permits_updated INTEGER DEFAULT 0,
            permits_failed INTEGER DEFAULT 0,
            processing_time_seconds INTEGER,
            error_details TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_florida_permit_log_county ON florida_permit_processing_log(county_code);
        CREATE INDEX IF NOT EXISTS idx_florida_permit_log_date ON florida_permit_processing_log(processing_date);
        """
        
        # County processing status table
        status_sql = """
        CREATE TABLE IF NOT EXISTS florida_county_processing_status (
            county_code VARCHAR(2) PRIMARY KEY,
            county_name VARCHAR(100),
            last_processed TIMESTAMP WITH TIME ZONE,
            last_successful TIMESTAMP WITH TIME ZONE,
            total_permits_collected INTEGER DEFAULT 0,
            system_status VARCHAR(50) DEFAULT 'active',
            error_count INTEGER DEFAULT 0,
            last_error TEXT,
            next_scheduled TIMESTAMP WITH TIME ZONE,
            priority INTEGER DEFAULT 3,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        """
        
        try:
            if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() != 'true':
                logger.warning('SQL execution disabled; skip Florida permit table creation. Provision via migrations.')
                return False
            self.execute_sql(permits_sql)
            self.execute_sql(log_sql)
            self.execute_sql(status_sql)
            logger.info("Florida permit tables created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Florida permit tables: {e}")
            return False
    
    async def collect_county_permits(self, county_code: str, days_back: int = 7) -> Dict:
        """Collect permits from a specific county"""
        if county_code not in self.counties:
            return {'error': f'County {county_code} not configured'}
        
        county = self.counties[county_code]
        logger.info(f"Collecting permits from {county.county_name} County ({county_code})")
        
        results = {
            'county_code': county_code,
            'county_name': county.county_name,
            'start_time': datetime.now().isoformat(),
            'permits_found': 0,
            'permits_loaded': 0,
            'permits_failed': 0,
            'municipalities_processed': [],
            'errors': []
        }
        
        try:
            # Create appropriate scraper for this county
            scraper = self._create_scraper(county)
            
            if scraper:
                # Collect permits from county system
                permits = await scraper.scrape_permits(days_back=days_back)
                results['permits_found'] = len(permits)
                
                # Load permits into database
                if permits:
                    load_result = await self._load_permits_to_db(permits, county_code)
                    results['permits_loaded'] = load_result['loaded']
                    results['permits_failed'] = load_result['failed']
                
                # Process major municipalities in this county
                for municipality in county.municipalities:
                    if municipality in self.municipalities:
                        muni_result = await self.collect_municipality_permits(municipality, days_back)
                        results['municipalities_processed'].append(muni_result)
            
            results['end_time'] = datetime.now().isoformat()
            
            # Update county processing status
            await self._update_county_status(county_code, results)
            
        except Exception as e:
            logger.error(f"Error collecting permits from {county.county_name}: {e}")
            results['errors'].append(str(e))
        
        return results
    
    async def collect_municipality_permits(self, municipality: str, days_back: int = 7) -> Dict:
        """Collect permits from a specific municipality"""
        if municipality not in self.municipalities:
            return {'error': f'Municipality {municipality} not configured'}
        
        muni = self.municipalities[municipality]
        logger.info(f"Collecting permits from {municipality}")
        
        results = {
            'municipality': municipality,
            'county_code': muni.county_code,
            'start_time': datetime.now().isoformat(),
            'permits_found': 0,
            'permits_loaded': 0,
            'errors': []
        }
        
        try:
            # Create appropriate scraper for this municipality
            scraper = self._create_municipal_scraper(muni)
            
            if scraper:
                permits = await scraper.scrape_permits(days_back=days_back)
                results['permits_found'] = len(permits)
                
                if permits:
                    load_result = await self._load_permits_to_db(permits, muni.county_code, municipality)
                    results['permits_loaded'] = load_result['loaded']
            
            results['end_time'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"Error collecting permits from {municipality}: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def _create_scraper(self, county: CountyConfig):
        """Create appropriate scraper for county"""
        # This would dynamically import and instantiate the correct scraper class
        # For now, return a placeholder
        logger.info(f"Creating {county.scraper_class} for {county.county_name}")
        return None  # Placeholder - would instantiate actual scraper
    
    def _create_municipal_scraper(self, municipality: MunicipalityConfig):
        """Create appropriate scraper for municipality"""
        logger.info(f"Creating {municipality.scraper_class} for {municipality.name}")
        return None  # Placeholder - would instantiate actual scraper
    
    async def _load_permits_to_db(self, permits: List[Dict], county_code: str, municipality: str = None) -> Dict:
        """Load permits into the Florida permits database"""
        loaded = 0
        failed = 0
        
        for permit in permits:
            try:
                # Standardize permit data
                permit_data = {
                    'permit_number': permit.get('permit_number'),
                    'county_code': county_code,
                    'county_name': self.counties[county_code].county_name,
                    'municipality': municipality,
                    'jurisdiction_type': 'municipality' if municipality else 'county',
                    'permit_type': permit.get('permit_type'),
                    'description': permit.get('description'),
                    'status': permit.get('status'),
                    'applicant_name': permit.get('applicant_name'),
                    'contractor_name': permit.get('contractor_name'),
                    'contractor_license': permit.get('contractor_license'),
                    'property_address': permit.get('property_address'),
                    'parcel_id': permit.get('parcel_id'),
                    'folio_number': permit.get('folio_number'),
                    'issue_date': permit.get('issue_date'),
                    'expiration_date': permit.get('expiration_date'),
                    'final_date': permit.get('final_date'),
                    'valuation': permit.get('valuation'),
                    'permit_fee': permit.get('permit_fee'),
                    'source_system': permit.get('source_system'),
                    'source_url': permit.get('source_url'),
                    'raw_data': permit.get('raw_data', {}),
                    'scraped_at': permit.get('scraped_at', datetime.now().isoformat())
                }
                
                # Remove None values
                permit_data = {k: v for k, v in permit_data.items() if v is not None}
                
                # Upsert permit (insert or update if exists)
                self.execute_sql("""
                    INSERT INTO florida_permits ({}) VALUES ({})
                    ON CONFLICT (permit_number, county_code, source_system) 
                    DO UPDATE SET 
                        status = EXCLUDED.status,
                        description = EXCLUDED.description,
                        raw_data = EXCLUDED.raw_data,
                        updated_at = NOW()
                """.format(
                    ', '.join(permit_data.keys()),
                    ', '.join(['%s'] * len(permit_data))
                ), list(permit_data.values()))
                
                loaded += 1
                
            except Exception as e:
                logger.error(f"Error loading permit {permit.get('permit_number', 'unknown')}: {e}")
                failed += 1
        
        return {'loaded': loaded, 'failed': failed}
    
    async def _update_county_status(self, county_code: str, results: Dict):
        """Update county processing status"""
        try:
            county = self.counties[county_code]
            
            status_data = {
                'county_code': county_code,
                'county_name': county.county_name,
                'last_processed': datetime.now(),
                'total_permits_collected': results['permits_loaded'],
                'system_status': 'active' if not results['errors'] else 'error',
                'error_count': len(results['errors']),
                'last_error': results['errors'][0] if results['errors'] else None,
                'priority': county.priority
            }
            
            # Upsert county status (guarded by SUPABASE_ENABLE_SQL)
            if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() == 'true':
                self.execute_sql("""
                INSERT INTO florida_county_processing_status 
                (county_code, county_name, last_processed, total_permits_collected, 
                 system_status, error_count, last_error, priority, updated_at)
                VALUES (%(county_code)s, %(county_name)s, %(last_processed)s, %(total_permits_collected)s,
                        %(system_status)s, %(error_count)s, %(last_error)s, %(priority)s, NOW())
                ON CONFLICT (county_code) 
                DO UPDATE SET
                    last_processed = EXCLUDED.last_processed,
                    total_permits_collected = florida_county_processing_status.total_permits_collected + EXCLUDED.total_permits_collected,
                    system_status = EXCLUDED.system_status,
                    error_count = EXCLUDED.error_count,
                    last_error = EXCLUDED.last_error,
                    updated_at = NOW()
            """, status_data)
            else:
                logger.warning('SQL execution disabled; skipping county status upsert. Use vetted RPC or dashboard.')
            
            if not results['errors']:
                if os.getenv('SUPABASE_ENABLE_SQL', 'false').lower() == 'true':
                    self.execute_sql("""
                        UPDATE florida_county_processing_status 
                        SET last_successful = NOW() 
                        WHERE county_code = %s
                    """, (county_code,))
                else:
                    logger.info('SQL disabled; not updating last_successful. Consider a vetted RPC for this update.')
            
        except Exception as e:
            logger.error(f"Error updating county status for {county_code}: {e}")
    
    async def run_priority_collection(self, priority_level: int = 1, days_back: int = 1) -> Dict:
        """Run permit collection for counties at specific priority level"""
        logger.info(f"Running priority {priority_level} permit collection")
        
        priority_counties = [
            county for county in self.counties.values() 
            if county.priority == priority_level and county.enabled
        ]
        
        results = {
            'priority_level': priority_level,
            'counties_processed': len(priority_counties),
            'total_permits': 0,
            'start_time': datetime.now().isoformat(),
            'county_results': []
        }
        
        # Process counties concurrently with rate limiting
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_county_with_limit(county):
            async with semaphore:
                return await self.collect_county_permits(county.county_code, days_back)
        
        # Execute concurrent processing
        tasks = [process_county_with_limit(county) for county in priority_counties]
        county_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for i, result in enumerate(county_results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {priority_counties[i].county_name}: {result}")
                continue
            
            results['county_results'].append(result)
            results['total_permits'] += result.get('permits_loaded', 0)
        
        results['end_time'] = datetime.now().isoformat()
        
        # Update global statistics
        self.stats['counties_processed'] += len(priority_counties)
        self.stats['permits_collected'] += results['total_permits']
        
        logger.info(f"Priority {priority_level} collection complete: {results['total_permits']} permits")
        
        return results
    
    async def run_full_florida_collection(self, days_back: int = 1) -> Dict:
        """Run full statewide permit collection"""
        logger.info("Starting full Florida permit collection")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'priority_results': [],
            'total_permits': 0,
            'total_counties': len(self.counties)
        }
        
        # Process by priority levels
        for priority in range(1, 6):  # Priority 1-5
            priority_result = await self.run_priority_collection(priority, days_back)
            results['priority_results'].append(priority_result)
            results['total_permits'] += priority_result['total_permits']
            
            # Add delay between priority levels to manage load
            await asyncio.sleep(30)
        
        results['end_time'] = datetime.now().isoformat()
        self.stats['last_full_run'] = results['end_time']
        
        logger.info(f"Full Florida collection complete: {results['total_permits']} permits from {results['total_counties']} counties")
        
        return results
    
    def get_processing_status(self) -> Dict:
        """Get current processing status across Florida"""
        try:
            # Get county status summary
            county_status = self.fetch_data("""
                SELECT 
                    system_status,
                    COUNT(*) as count,
                    SUM(total_permits_collected) as total_permits,
                    AVG(error_count) as avg_errors
                FROM florida_county_processing_status 
                GROUP BY system_status
            """)
            
            # Get recent activity
            recent_activity = self.fetch_data("""
                SELECT county_code, county_name, last_processed, total_permits_collected, system_status
                FROM florida_county_processing_status
                ORDER BY last_processed DESC
                LIMIT 20
            """)
            
            # Get permit statistics
            permit_stats = self.fetch_data("""
                SELECT 
                    county_code,
                    county_name,
                    COUNT(*) as permit_count,
                    MAX(issue_date) as latest_permit
                FROM florida_permits
                GROUP BY county_code, county_name
                ORDER BY permit_count DESC
                LIMIT 20
            """)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_counties': len(self.counties),
                'counties_enabled': sum(1 for c in self.counties.values() if c.enabled),
                'system_status': county_status,
                'recent_activity': recent_activity,
                'top_permit_counties': permit_stats,
                'processing_stats': self.stats
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Florida Permit Orchestrator')
    parser.add_argument('--mode', 
                       choices=['init', 'priority', 'full', 'county', 'status'],
                       default='status',
                       help='Operation mode')
    parser.add_argument('--priority', type=int, choices=range(1, 6),
                       help='Priority level for priority mode (1-5)')
    parser.add_argument('--county', 
                       help='County code for county-specific collection')
    parser.add_argument('--days-back', type=int, default=7,
                       help='Number of days to look back for permits')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = FloridaPermitOrchestrator()
    
    async def main():
        if args.mode == 'init':
            # Initialize database tables
            result = orchestrator.create_florida_permit_tables()
            print(f"Database initialization: {'Success' if result else 'Failed'}")
            
        elif args.mode == 'priority':
            # Run priority collection
            priority = args.priority or 1
            result = await orchestrator.run_priority_collection(priority, args.days_back)
            print(f"Priority {priority} collection: {result['total_permits']} permits")
            
        elif args.mode == 'full':
            # Run full statewide collection
            result = await orchestrator.run_full_florida_collection(args.days_back)
            print(f"Full Florida collection: {result['total_permits']} permits")
            
        elif args.mode == 'county':
            # Run specific county collection
            if args.county:
                result = await orchestrator.collect_county_permits(args.county, args.days_back)
                print(f"{result['county_name']} collection: {result['permits_loaded']} permits")
            else:
                print("County code required for county mode")
                
        elif args.mode == 'status':
            # Show processing status
            status = orchestrator.get_processing_status()
            print("\nFlorida Permit Processing Status:")
            print(json.dumps(status, indent=2, default=str))
    
    # Run async main
    asyncio.run(main())
