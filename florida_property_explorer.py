"""
Florida Revenue Property Data Explorer
Explores the actual structure of floridarevenue.com to find NAL files
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json

def explore_florida_revenue():
    """Explore the Florida Revenue website structure"""
    
    base_url = "https://floridarevenue.com/property/dataportal/"
    session = requests.Session()
    
    print("="*60)
    print("FLORIDA REVENUE DATA PORTAL EXPLORER")
    print("="*60)
    
    try:
        # First, get the main page
        print(f"\n[1] Accessing main data portal: {base_url}")
        response = session.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links on the page
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            full_url = urljoin(base_url, href)
            
            # Filter relevant links
            if 'NAL' in text or 'NAL' in href or '2025' in href or 'property' in href.lower():
                links.append({
                    'text': text,
                    'href': href,
                    'full_url': full_url
                })
        
        print(f"\n[2] Found {len(links)} relevant links:")
        for i, link in enumerate(links[:20], 1):  # Show first 20
            print(f"    {i}. {link['text'][:50]} -> {link['href'][:80]}")
        
        # Try to find FTP or download sections
        print("\n[3] Looking for FTP/Download sections...")
        
        # Common patterns for Florida Revenue data
        possible_paths = [
            "FTP%20Folders/",
            "FTP Folders/",
            "FTP/",
            "Downloads/",
            "Data/",
            "NAL/",
            "2025/"
        ]
        
        for path in possible_paths:
            test_url = urljoin(base_url, path)
            print(f"\n    Testing: {test_url}")
            
            try:
                resp = session.get(test_url, timeout=5)
                if resp.status_code == 200:
                    print(f"    [OK] Found: {test_url}")
                    
                    # Parse this page
                    sub_soup = BeautifulSoup(resp.text, 'html.parser')
                    sub_links = []
                    
                    for link in sub_soup.find_all('a', href=True):
                        href = link['href']
                        text = link.get_text(strip=True)
                        
                        if text and text != '..' and text != 'Parent Directory':
                            sub_links.append({
                                'text': text,
                                'href': href,
                                'full_url': urljoin(test_url, href)
                            })
                    
                    if sub_links:
                        print(f"    Found {len(sub_links)} items:")
                        for item in sub_links[:10]:
                            print(f"        - {item['text']}")
                            
                            # If we find NAL, explore it
                            if 'NAL' in item['text']:
                                nal_url = item['full_url']
                                print(f"\n[4] Found NAL directory! Exploring: {nal_url}")
                                
                                try:
                                    nal_resp = session.get(nal_url, timeout=5)
                                    if nal_resp.status_code == 200:
                                        nal_soup = BeautifulSoup(nal_resp.text, 'html.parser')
                                        
                                        print("\n    NAL subdirectories:")
                                        for nal_link in nal_soup.find_all('a', href=True):
                                            nal_text = nal_link.get_text(strip=True)
                                            if nal_text and nal_text != '..' and nal_text != 'Parent Directory':
                                                nal_href = nal_link['href']
                                                print(f"        - {nal_text}")
                                                
                                                # Check for 2025 or recent years
                                                if '2025' in nal_text or '2024' in nal_text:
                                                    year_url = urljoin(nal_url, nal_href)
                                                    print(f"\n[5] Found year directory: {year_url}")
                                                    
                                                    # Get files in year directory
                                                    year_resp = session.get(year_url, timeout=5)
                                                    if year_resp.status_code == 200:
                                                        year_soup = BeautifulSoup(year_resp.text, 'html.parser')
                                                        
                                                        zip_files = []
                                                        for file_link in year_soup.find_all('a', href=True):
                                                            file_href = file_link['href']
                                                            if file_href.endswith('.zip'):
                                                                zip_files.append({
                                                                    'name': file_link.get_text(strip=True),
                                                                    'url': urljoin(year_url, file_href)
                                                                })
                                                        
                                                        if zip_files:
                                                            print(f"\n[SUCCESS] Found {len(zip_files)} ZIP files!")
                                                            print("\nFirst 5 files:")
                                                            for zf in zip_files[:5]:
                                                                print(f"    - {zf['name']}")
                                                            
                                                            # Save the structure
                                                            with open('florida_revenue_structure.json', 'w') as f:
                                                                json.dump({
                                                                    'base_url': base_url,
                                                                    'nal_url': nal_url,
                                                                    'year_url': year_url,
                                                                    'zip_files': zip_files
                                                                }, f, indent=2)
                                                            
                                                            print(f"\n[SAVED] Structure saved to florida_revenue_structure.json")
                                                            print(f"\nCorrect NAL URL: {year_url}")
                                                            return year_url, zip_files
                                                
                                except Exception as e:
                                    print(f"    Error exploring NAL: {e}")
                else:
                    print(f"    [404] Not found: {test_url}")
                    
            except Exception as e:
                print(f"    [ERROR] {e}")
        
        print("\n[6] Alternative: Check if site requires authentication or special headers")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to access site: {e}")
        
    return None, []

if __name__ == "__main__":
    url, files = explore_florida_revenue()
    
    if url:
        print("\n" + "="*60)
        print("EXPLORATION COMPLETE")
        print("="*60)
        print(f"Use this URL in the downloader: {url}")
    else:
        print("\n[WARNING] Could not find NAL files automatically")
        print("The site may require manual navigation or authentication")