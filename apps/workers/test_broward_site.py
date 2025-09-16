"""
Test Broward Tax Deed Site Structure
"""
import requests
from bs4 import BeautifulSoup

# Test the main auctions page
url = "https://broward.deedauction.net/auctions"
print(f"Testing: {url}")

response = requests.get(url)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Look for auction information
    print("\n=== Page Title ===")
    title = soup.find('title')
    if title:
        print(title.text)
    
    print("\n=== Forms on page ===")
    forms = soup.find_all('form')
    print(f"Found {len(forms)} forms")
    
    print("\n=== Links containing 'auction' ===")
    auction_links = soup.find_all('a', href=lambda x: x and 'auction' in x.lower())
    for link in auction_links[:5]:
        print(f"  {link.get('href')} - {link.text.strip()[:50]}")
    
    print("\n=== Tables on page ===")
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    for i, table in enumerate(tables[:2]):
        print(f"\nTable {i+1}:")
        rows = table.find_all('tr')[:3]
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if cells:
                print("  " + " | ".join([cell.text.strip()[:20] for cell in cells[:4]]))
    
    print("\n=== Divs with class containing 'property' or 'item' ===")
    property_divs = soup.find_all('div', class_=lambda x: x and ('property' in x.lower() or 'item' in x.lower()))
    print(f"Found {len(property_divs)} property/item divs")
    
    # Save page for analysis
    with open('broward_auction_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("\nPage saved to broward_auction_page.html for analysis")