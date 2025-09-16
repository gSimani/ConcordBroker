"""
Check for auction details on Broward site
"""
import requests
from bs4 import BeautifulSoup
import re

# Try different potential URLs
urls = [
    "https://broward.deedauction.net/tabcontent/auctions",
    "https://broward.deedauction.net/api/auctions",
    "https://broward.deedauction.net/auction/current",
    "https://broward.deedauction.net/properties"
]

for url in urls:
    print(f"\n=== Testing: {url} ===")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if JSON response
            try:
                data = response.json()
                print("JSON Response:")
                print(data if isinstance(data, dict) else f"Array with {len(data)} items")
            except:
                # HTML response
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for parcel numbers
                parcel_pattern = re.compile(r'\d{4}-\d{2}-\d{2}-\d{4}')
                parcels = soup.find_all(string=parcel_pattern)
                if parcels:
                    print(f"Found {len(parcels)} parcel numbers")
                    for p in parcels[:3]:
                        print(f"  {p.strip()}")
                
                # Look for property related content
                property_elements = soup.find_all(['div', 'tr', 'li'], string=re.compile(r'(property|parcel|certificate|deed)', re.I))
                if property_elements:
                    print(f"Found {len(property_elements)} property-related elements")
                    
    except Exception as e:
        print(f"Error: {e}")

# Check the saved HTML file
print("\n=== Analyzing saved HTML ===")
with open('broward_auction_page.html', 'r', encoding='utf-8') as f:
    html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for JavaScript that might load data
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and ('auction' in script.string.lower() or 'property' in script.string.lower()):
            print("Found relevant JavaScript - site likely uses dynamic loading")
            break
    
    # Check for auction dates
    date_pattern = re.compile(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}')
    dates = soup.find_all(string=date_pattern)
    if dates:
        print(f"\nFound auction dates:")
        for date in dates:
            print(f"  {date.strip()}")