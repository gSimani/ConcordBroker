#!/usr/bin/env python3
"""
Florida Data URL Resolver
Advanced URL resolution and pattern matching for Florida data sources
Handles dynamic folder structures and naming conventions
"""

import asyncio
import aiohttp
import re
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from urllib.parse import urljoin, quote, unquote
from bs4 import BeautifulSoup
import calendar

logger = logging.getLogger(__name__)

class FloridaURLResolver:
    """Resolves and discovers URLs for Florida data sources with dynamic patterns"""
    
    def __init__(self):
        self.session = None
        self.discovered_patterns = {}
        self.base_patterns = self._initialize_base_patterns()
        self.county_mappings = self._initialize_county_mappings()
        
    def _initialize_base_patterns(self) -> Dict[str, Dict]:
        """Initialize known base URL patterns for Florida data sources"""
        return {
            "florida_revenue": {
                "base_url": "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/",
                "path_patterns": [
                    "Tax%20Roll%20Data%20Files/{year}/{dataset}_{county}_{year}.{ext}",
                    "Tax%20Roll%20Data%20Files/{year}{period}/{dataset}{county}{period}{year_short}{month:02d}.{ext}",
                    "Tax%20Roll%20Data%20Files/NAL/{year}{period}/NAL{county}{period}{year_short}{month:02d}.txt",
                    "Tax%20Roll%20Data%20Files/NAP/{year}{period}/NAP{county}{period}{year_short}{month:02d}.txt",
                    "Tax%20Roll%20Data%20Files/NAV/{year}/NAV%20{nav_type}/NAV{nav_type}_{county}_{year}.txt",
                    "Tax%20Roll%20Data%20Files/SDF/{year}{period}/SDF{county}{period}{year_short}{month:02d}.txt",
                    "Tax%20Roll%20Data%20Files/TPP/{year}/TPP_{county}_{year}.txt",
                ],
                "datasets": ["NAL", "NAP", "NAV", "SDF", "TPP", "RER", "CDF", "JVS"],
                "periods": ["P", "F"],  # Preliminary, Final
                "nav_types": ["D", "N"],  # Detail, Summary
                "file_extensions": ["txt", "zip", "csv"]
            },
            
            "sunbiz_daily": {
                "base_url": "https://dos.fl.gov/sunbiz/other-services/data-downloads/daily-data/",
                "path_patterns": [
                    "{entity_type}_{date:%Y%m%d}.txt",
                    "{entity_type}_detail_{date:%Y%m%d}.zip",
                    "quarterly/{entity_type}_{year}_Q{quarter}.zip"
                ],
                "entity_types": ["corp", "llc", "lp", "fictitious", "officers", "agents"],
                "file_extensions": ["txt", "zip", "csv"]
            },
            
            "broward_daily": {
                "base_url": "https://www.broward.org/RecordsTaxesTreasury/Records/Documents/",
                "path_patterns": [
                    "DailyIndex/{date:%Y%m%d}.zip",
                    "ExportFiles/{date:%Y}/{date:%m}/{date:%d}_extract.zip",
                    "MonthlyExports/{date:%Y}_{date:%m}.zip"
                ],
                "file_extensions": ["zip"]
            },
            
            "map_data": {
                "base_url": "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/",
                "path_patterns": [
                    "{county_name}/parcels_{year}.shp",
                    "{county_name}/boundaries_{year}.zip",
                    "Statewide/florida_parcels_{year}.gdb.zip"
                ],
                "file_extensions": ["shp", "zip", "gdb", "kml"]
            }
        }
    
    def _initialize_county_mappings(self) -> Dict[str, Dict]:
        """Initialize county code to name mappings"""
        return {
            "06": {"name": "Broward", "full_name": "Broward County"},
            "13": {"name": "Dade", "full_name": "Miami-Dade County", "alt_name": "Miami-Dade"},
            "50": {"name": "Palm Beach", "full_name": "Palm Beach County"},
            "57": {"name": "Osceola", "full_name": "Osceola County"},
            "99": {"name": "Orange", "full_name": "Orange County"}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "FloridaDataResolver/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def resolve_year_folders(self, base_url: str) -> List[str]:
        """Discover available year folders dynamically"""
        logger.info(f"Discovering year folders in {base_url}")
        
        year_folders = []
        current_year = datetime.now().year
        
        # Generate possible year patterns
        year_patterns = [
            str(year) for year in range(current_year - 2, current_year + 2)
        ] + [
            f"{year}F" for year in range(current_year - 2, current_year + 1)
        ] + [
            f"{year}P" for year in range(current_year, current_year + 2)
        ] + [
            f"TAX_ROLL_{year}" for year in range(current_year - 2, current_year + 2)
        ]
        
        # Test each pattern
        for pattern in year_patterns:
            test_url = urljoin(base_url, f"{pattern}/")
            
            try:
                async with self.session.head(test_url) as response:
                    if response.status == 200:
                        year_folders.append(pattern)
                        logger.info(f"Found year folder: {pattern}")
            except Exception as e:
                logger.debug(f"Year folder {pattern} not accessible: {e}")
        
        return sorted(year_folders)
    
    async def resolve_dataset_urls(self, source_name: str, county_codes: List[str] = None, 
                                 years: List[str] = None) -> Dict[str, List[str]]:
        """Resolve all URLs for a given data source"""
        if source_name not in self.base_patterns:
            raise ValueError(f"Unknown source: {source_name}")
        
        pattern_config = self.base_patterns[source_name]
        base_url = pattern_config["base_url"]
        
        # Use provided parameters or defaults
        county_codes = county_codes or ["06", "13", "50"]
        years = years or [str(datetime.now().year), str(datetime.now().year - 1)]
        
        resolved_urls = {"discovered": [], "potential": [], "failed": []}
        
        # Discover year folders if dealing with Florida Revenue
        if source_name == "florida_revenue":
            available_years = await self.resolve_year_folders(base_url + "Tax%20Roll%20Data%20Files/")
            if available_years:
                years = available_years
        
        # Generate URLs from patterns
        for pattern in pattern_config["path_patterns"]:
            urls = await self._generate_urls_from_pattern(
                base_url, pattern, pattern_config, county_codes, years
            )
            
            # Test URLs
            for url in urls:
                try:
                    async with self.session.head(url) as response:
                        if response.status == 200:
                            resolved_urls["discovered"].append(url)
                            logger.info(f"Confirmed URL: {url}")
                        elif response.status in [404, 403]:
                            resolved_urls["potential"].append(url)
                        else:
                            resolved_urls["failed"].append(url)
                            
                except Exception as e:
                    resolved_urls["failed"].append(url)
                    logger.debug(f"URL test failed for {url}: {e}")
                
                # Rate limiting
                await asyncio.sleep(0.5)
        
        return resolved_urls
    
    async def _generate_urls_from_pattern(self, base_url: str, pattern: str, 
                                        config: Dict, county_codes: List[str], 
                                        years: List[str]) -> List[str]:
        """Generate URLs from a pattern template"""
        urls = []
        current_date = datetime.now()
        
        for year in years:
            for county_code in county_codes:
                county_name = self.county_mappings.get(county_code, {}).get("name", f"County{county_code}")
                year_short = year[-2:] if len(year) >= 2 else year
                
                # Generate variations for different contexts
                contexts = []
                
                # Basic context
                basic_context = {
                    "year": year,
                    "year_short": year_short,
                    "county": county_code,
                    "county_name": county_name,
                    "date": current_date,
                    "month": current_date.month
                }
                contexts.append(basic_context)
                
                # Add dataset-specific contexts
                if "datasets" in config:
                    for dataset in config["datasets"]:
                        dataset_context = basic_context.copy()
                        dataset_context["dataset"] = dataset
                        contexts.append(dataset_context)
                
                # Add period-specific contexts
                if "periods" in config:
                    for period in config["periods"]:
                        period_context = basic_context.copy()
                        period_context["period"] = period
                        contexts.append(period_context)
                
                # Add NAV type contexts
                if "nav_types" in config:
                    for nav_type in config["nav_types"]:
                        nav_context = basic_context.copy()
                        nav_context["nav_type"] = nav_type
                        contexts.append(nav_context)
                
                # Add entity type contexts (for Sunbiz)
                if "entity_types" in config:
                    for entity_type in config["entity_types"]:
                        entity_context = basic_context.copy()
                        entity_context["entity_type"] = entity_type
                        contexts.append(entity_context)
                
                # Add extension contexts
                if "file_extensions" in config:
                    for ext in config["file_extensions"]:
                        for context in contexts.copy():
                            ext_context = context.copy()
                            ext_context["ext"] = ext
                            contexts.append(ext_context)
                
                # Generate URLs from contexts
                for context in contexts:
                    try:
                        # Handle date formatting in patterns
                        formatted_pattern = pattern
                        if "{date:" in pattern:
                            # Extract date format and apply it
                            import re
                            date_matches = re.findall(r'\{date:([^}]+)\}', pattern)
                            for date_format in date_matches:
                                formatted_date = current_date.strftime(date_format)
                                formatted_pattern = formatted_pattern.replace(
                                    f"{{date:{date_format}}}", formatted_date
                                )
                        
                        # Format the pattern with context
                        try:
                            formatted_path = formatted_pattern.format(**context)
                            full_url = urljoin(base_url, formatted_path)
                            urls.append(full_url)
                        except KeyError:
                            # Pattern requires variables not in this context
                            continue
                            
                    except Exception as e:
                        logger.debug(f"Pattern formatting failed: {e}")
                        continue
        
        # Remove duplicates
        return list(set(urls))
    
    async def discover_directory_listing(self, directory_url: str) -> List[Dict[str, Any]]:
        """Discover files in a directory through HTML parsing"""
        logger.info(f"Discovering directory listing: {directory_url}")
        
        files = []
        
        try:
            async with self.session.get(directory_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for file links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        # Skip navigation links
                        if href in ['.', '..', '/'] or href.startswith('#'):
                            continue
                        
                        # Extract file info
                        file_info = {
                            "name": unquote(href),
                            "url": urljoin(directory_url, href),
                            "type": self._determine_file_type(href),
                            "size": None,
                            "modified": None
                        }
                        
                        # Try to extract size and date from table structure
                        parent_row = link.find_parent('tr')
                        if parent_row:
                            cells = parent_row.find_all('td')
                            if len(cells) >= 3:
                                # Common format: Name | Modified | Size
                                try:
                                    file_info["modified"] = cells[1].get_text().strip()
                                    file_info["size"] = cells[2].get_text().strip()
                                except Exception:
                                    pass
                        
                        files.append(file_info)
                        
        except Exception as e:
            logger.error(f"Directory listing discovery failed: {e}")
        
        return files
    
    def _determine_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        extension = Path(filename).suffix.lower()
        
        type_mapping = {
            '.txt': 'text',
            '.csv': 'csv',
            '.zip': 'compressed',
            '.gz': 'compressed',
            '.pdf': 'document',
            '.shp': 'geospatial',
            '.gdb': 'geospatial',
            '.kml': 'geospatial',
            '.json': 'json',
            '.xml': 'xml'
        }
        
        return type_mapping.get(extension, 'unknown')
    
    async def validate_url_patterns(self, urls: List[str]) -> Dict[str, List[str]]:
        """Validate a list of URLs and categorize them"""
        results = {
            "valid": [],
            "invalid": [],
            "redirected": [],
            "access_denied": [],
            "not_found": []
        }
        
        for url in urls:
            try:
                async with self.session.head(url, allow_redirects=False) as response:
                    if response.status == 200:
                        results["valid"].append(url)
                    elif response.status in [301, 302, 303, 307, 308]:
                        results["redirected"].append({
                            "original": url,
                            "location": response.headers.get("Location", "Unknown")
                        })
                    elif response.status == 403:
                        results["access_denied"].append(url)
                    elif response.status == 404:
                        results["not_found"].append(url)
                    else:
                        results["invalid"].append(url)
                        
            except Exception as e:
                results["invalid"].append(url)
                logger.debug(f"URL validation failed for {url}: {e}")
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        return results
    
    def extract_metadata_from_filename(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename using known patterns"""
        metadata = {
            "dataset": None,
            "county": None,
            "year": None,
            "period": None,
            "date": None,
            "type": None
        }
        
        # Florida Revenue patterns
        revenue_patterns = [
            r'(NAL|NAP|NAV|SDF|TPP|RER|CDF|JVS)(\d{2})(P|F)(\d{6})\.(\w+)',
            r'(broward|dade|palm_beach)_(\w+)_(\d{4})\.(\w+)',
            r'(\w+)_(\d{2})_(\d{4})\.(\w+)'
        ]
        
        for pattern in revenue_patterns:
            match = re.match(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 5:  # Full Florida Revenue pattern
                    metadata.update({
                        "dataset": groups[0].upper(),
                        "county": groups[1],
                        "period": groups[2],
                        "date": groups[3],
                        "type": groups[4]
                    })
                elif len(groups) >= 4:  # County-specific pattern
                    metadata.update({
                        "county": groups[0],
                        "dataset": groups[1].upper(),
                        "year": groups[2],
                        "type": groups[3]
                    })
                break
        
        # Date patterns
        date_patterns = [
            r'(\d{8})',  # YYYYMMDD
            r'(\d{4})_(\d{2})_(\d{2})',  # YYYY_MM_DD
            r'(\d{4})-(\d{2})-(\d{2})'   # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, filename)
            if matches:
                if len(matches[0]) == 1:  # Single group (YYYYMMDD)
                    date_str = matches[0]
                    if len(date_str) == 8:
                        try:
                            parsed_date = datetime.strptime(date_str, '%Y%m%d')
                            metadata["date"] = parsed_date.isoformat()
                            metadata["year"] = str(parsed_date.year)
                        except ValueError:
                            pass
                break
        
        return metadata
    
    async def generate_comprehensive_url_list(self, sources: List[str] = None) -> Dict[str, Any]:
        """Generate comprehensive URL list for all or specified sources"""
        sources = sources or list(self.base_patterns.keys())
        
        comprehensive_list = {
            "generated_at": datetime.now().isoformat(),
            "sources": {},
            "summary": {
                "total_sources": len(sources),
                "total_urls": 0,
                "valid_urls": 0,
                "potential_urls": 0
            }
        }
        
        for source_name in sources:
            logger.info(f"Generating URLs for source: {source_name}")
            
            try:
                resolved = await self.resolve_dataset_urls(source_name)
                
                comprehensive_list["sources"][source_name] = {
                    "base_config": self.base_patterns[source_name],
                    "resolved_urls": resolved,
                    "url_count": {
                        "discovered": len(resolved["discovered"]),
                        "potential": len(resolved["potential"]),
                        "failed": len(resolved["failed"])
                    }
                }
                
                # Update summary
                comprehensive_list["summary"]["total_urls"] += sum(len(urls) for urls in resolved.values())
                comprehensive_list["summary"]["valid_urls"] += len(resolved["discovered"])
                comprehensive_list["summary"]["potential_urls"] += len(resolved["potential"])
                
            except Exception as e:
                logger.error(f"URL generation failed for {source_name}: {e}")
                comprehensive_list["sources"][source_name] = {"error": str(e)}
        
        return comprehensive_list

async def main():
    """Test the URL resolver"""
    async with FloridaURLResolver() as resolver:
        print("Testing Florida URL Resolver...")
        
        # Test Florida Revenue URLs
        print("\n1. Resolving Florida Revenue URLs:")
        florida_urls = await resolver.resolve_dataset_urls("florida_revenue", ["06"], ["2025"])
        print(f"  - Discovered: {len(florida_urls['discovered'])}")
        print(f"  - Potential: {len(florida_urls['potential'])}")
        
        # Test Sunbiz URLs  
        print("\n2. Resolving Sunbiz URLs:")
        sunbiz_urls = await resolver.resolve_dataset_urls("sunbiz_daily")
        print(f"  - Discovered: {len(sunbiz_urls['discovered'])}")
        print(f"  - Potential: {len(sunbiz_urls['potential'])}")
        
        # Generate comprehensive list
        print("\n3. Generating comprehensive URL list:")
        comprehensive = await resolver.generate_comprehensive_url_list()
        
        # Save to file
        output_file = Path("florida_comprehensive_urls.json")
        output_file.write_text(json.dumps(comprehensive, indent=2))
        print(f"  - Saved to: {output_file}")
        print(f"  - Total URLs: {comprehensive['summary']['total_urls']}")
        print(f"  - Valid URLs: {comprehensive['summary']['valid_urls']}")

if __name__ == "__main__":
    asyncio.run(main())