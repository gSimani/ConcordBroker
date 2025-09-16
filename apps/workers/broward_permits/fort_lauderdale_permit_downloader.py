"""
Fort Lauderdale Building Permits Downloader
Downloads building permit data from Fort Lauderdale's ArcGIS Hub
"""

import os
import requests
import json
import csv
import time
from datetime import datetime
from pathlib import Path

class FortLauderdalePermitDownloader:
    """Downloads Fort Lauderdale building permits from ArcGIS Hub"""
    
    def __init__(self):
        self.base_urls = [
            # Try various possible ArcGIS REST endpoints
            "https://services.arcgis.com/82LxCEC4N4AxRpwc/arcgis/rest/services",
            "https://fortlauderdale.maps.arcgis.com/sharing/rest/content/items",
            "https://services1.arcgis.com/82LxCEC4N4AxRpwc/arcgis/rest/services"
        ]
        
        self.data_dir = Path("data/fort_lauderdale_permits")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def search_permit_services(self):
        """Search for building permit services"""
        print("Searching for Fort Lauderdale building permit services...")
        
        services = []
        
        # Try different service endpoints
        for base_url in self.base_urls:
            try:
                # Get list of services
                response = requests.get(f"{base_url}?f=json", timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Found services at {base_url}")
                    
                    # Look for building permit related services
                    if 'services' in data:
                        for service in data['services']:
                            name = service.get('name', '').lower()
                            service_type = service.get('type', '')
                            
                            if any(keyword in name for keyword in ['permit', 'building', 'construction']):
                                service_info = {
                                    'name': service.get('name'),
                                    'type': service_type,
                                    'url': f"{base_url}/{service.get('name')}/{service_type}"
                                }
                                services.append(service_info)
                                print(f"  Found: {service_info['name']} ({service_type})")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"Error checking {base_url}: {e}")
                continue
        
        return services
    
    def try_common_permit_urls(self):
        """Try common URL patterns for building permits"""
        print("Trying common building permit URL patterns...")
        
        common_urls = [
            "https://services.arcgis.com/82LxCEC4N4AxRpwc/arcgis/rest/services/Building_Permits/FeatureServer/0/query?where=1%3D1&outFields=*&f=json",
            "https://services1.arcgis.com/82LxCEC4N4AxRpwc/arcgis/rest/services/BuildingPermits/FeatureServer/0/query?where=1%3D1&outFields=*&f=json",
            "https://services.arcgis.com/82LxCEC4N4AxRpwc/arcgis/rest/services/Permits/FeatureServer/0/query?where=1%3D1&outFields=*&f=json&resultRecordCount=10",
        ]
        
        for url in common_urls:
            try:
                print(f"Trying: {url}")
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'features' in data and len(data['features']) > 0:
                        print(f"SUCCESS! Found {len(data['features'])} permits")
                        print("Sample field names:", list(data['features'][0].get('attributes', {}).keys()))
                        return url, data
                    else:
                        print("  No features found")
                else:
                    print(f"  HTTP {response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"  Error: {e}")
        
        return None, None
    
    def download_all_permits(self, service_url):
        """Download all permits from the service"""
        print(f"Downloading all permits from: {service_url}")
        
        all_permits = []
        offset = 0
        batch_size = 1000
        
        while True:
            try:
                # Construct query URL with pagination
                query_url = service_url.replace('resultRecordCount=10', f'resultRecordCount={batch_size}')
                if 'resultOffset=' not in query_url:
                    query_url += f'&resultOffset={offset}'
                else:
                    query_url = query_url.replace(f'resultOffset={offset-batch_size}', f'resultOffset={offset}')
                
                print(f"  Fetching batch {offset//batch_size + 1} (offset: {offset})")
                
                response = requests.get(query_url, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'features' in data and data['features']:
                        features = data['features']
                        all_permits.extend(features)
                        print(f"    Got {len(features)} permits")
                        
                        # Check if we got a full batch (more data likely available)
                        if len(features) < batch_size:
                            break
                            
                        offset += batch_size
                    else:
                        break
                else:
                    print(f"    HTTP {response.status_code}: {response.text[:200]}")
                    break
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"    Error: {e}")
                break
        
        print(f"Downloaded {len(all_permits)} total permits")
        return all_permits
    
    def save_permits(self, permits, filename_prefix="fort_lauderdale_permits"):
        """Save permits to JSON and CSV files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save raw JSON
        json_file = self.data_dir / f"{filename_prefix}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'source': 'Fort Lauderdale ArcGIS',
                'downloaded_at': datetime.now().isoformat(),
                'total_permits': len(permits),
                'permits': permits
            }, f, indent=2)
        
        # Convert to CSV
        if permits:
            csv_file = self.data_dir / f"{filename_prefix}_{timestamp}.csv"
            
            # Extract field names from first permit
            first_permit = permits[0]
            attributes = first_permit.get('attributes', {})
            fieldnames = list(attributes.keys())
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for permit in permits:
                    writer.writerow(permit.get('attributes', {}))
            
            print(f"Saved {len(permits)} permits:")
            print(f"  JSON: {json_file}")
            print(f"  CSV: {csv_file}")
            
            # Show sample fields
            if fieldnames:
                print(f"  Fields: {', '.join(fieldnames[:10])}{'...' if len(fieldnames) > 10 else ''}")
            
            return str(csv_file), str(json_file)
        
        return None, None
    
    def analyze_permit_coverage(self, permits):
        """Analyze what areas/cities the permits cover"""
        print("\nAnalyzing permit coverage...")
        
        if not permits:
            print("No permits to analyze")
            return
        
        # Look for city/jurisdiction fields
        first_permit = permits[0].get('attributes', {})
        
        city_fields = []
        for field in first_permit.keys():
            field_lower = field.lower()
            if any(keyword in field_lower for keyword in ['city', 'jurisdiction', 'municipality', 'location']):
                city_fields.append(field)
        
        print(f"Potential city/jurisdiction fields: {city_fields}")
        
        # Analyze values in these fields
        for field in city_fields[:3]:  # Check first 3 relevant fields
            values = {}
            for permit in permits[:1000]:  # Sample first 1000
                value = permit.get('attributes', {}).get(field, '')
                if value:
                    values[value] = values.get(value, 0) + 1
            
            print(f"\n{field} values:")
            for value, count in sorted(values.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {value}: {count}")
    
    def run_discovery(self):
        """Run complete discovery process"""
        print("FORT LAUDERDALE BUILDING PERMITS DISCOVERY")
        print("=" * 60)
        
        # 1. Search for services
        services = self.search_permit_services()
        
        if services:
            print(f"\nFound {len(services)} potential permit services")
            for service in services:
                print(f"  - {service['name']} ({service['type']})")
        
        # 2. Try common URL patterns
        service_url, sample_data = self.try_common_permit_urls()
        
        if service_url:
            print(f"\nFound working permit service: {service_url}")
            
            # 3. Download all permits
            all_permits = self.download_all_permits(service_url)
            
            if all_permits:
                # 4. Save permits
                csv_file, json_file = self.save_permits(all_permits)
                
                # 5. Analyze coverage
                self.analyze_permit_coverage(all_permits)
                
                return {
                    'success': True,
                    'service_url': service_url,
                    'total_permits': len(all_permits),
                    'csv_file': csv_file,
                    'json_file': json_file
                }
        
        print("\nNo working permit services found")
        print("You may need to:")
        print("1. Check the Fort Lauderdale GeoHub directly")
        print("2. Contact gis@fortlauderdale.gov for API access")
        print("3. Use manual download from the web interface")
        
        return {
            'success': False,
            'message': 'No accessible permit data found'
        }

if __name__ == "__main__":
    downloader = FortLauderdalePermitDownloader()
    result = downloader.run_discovery()
    
    if result['success']:
        print(f"\n✅ SUCCESS!")
        print(f"Downloaded {result['total_permits']} permits")
        print(f"CSV file: {result['csv_file']}")
    else:
        print(f"\n❌ FAILED: {result['message']}")