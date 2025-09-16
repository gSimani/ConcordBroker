#!/usr/bin/env python3
"""
Simple Tax Deed Scraper using requests and BeautifulSoup first to understand the structure
"""

import requests
import re
from bs4 import BeautifulSoup
from supabase import create_client, Client
import json
from datetime import datetime

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

def analyze_page_structure():
    """First analyze the page structure with requests"""
    
    url = "https://broward.deedauction.net/auction/110"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("Fetching page with requests...")
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for tables
            tables = soup.find_all('table')
            print(f"Found {len(tables)} tables")
            
            # Check if we can see the tax deed numbers in the HTML
            if "51640" in response.text:
                print("Found tax deed number 51640 in page content")
            else:
                print("Tax deed number 51640 NOT found in page content")
            
            # Look for specific patterns
            tax_deed_pattern = re.compile(r'5164\d')
            matches = tax_deed_pattern.findall(response.text)
            print(f"Found tax deed numbers: {set(matches)}")
            
            # Look for table rows
            for i, table in enumerate(tables):
                rows = table.find_all('tr')
                print(f"\nTable {i+1} has {len(rows)} rows")
                
                for j, row in enumerate(rows[:10]):  # First 10 rows
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        cell_texts = [cell.get_text(strip=True) for cell in cells]
                        if any(cell for cell in cell_texts if cell and len(cell) > 0):
                            print(f"  Row {j+1}: {cell_texts}")
            
            # Check for JavaScript loading
            scripts = soup.find_all('script')
            print(f"\nFound {len(scripts)} script tags")
            
            # Look for AJAX or dynamic loading indicators
            ajax_indicators = ['ajax', 'load', 'dynamic', 'json']
            for script in scripts:
                if script.string:
                    script_text = script.string.lower()
                    for indicator in ajax_indicators:
                        if indicator in script_text:
                            print(f"Found potential dynamic loading indicator: {indicator}")
                            break
        
        return response.text
        
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None

def extract_properties_from_html(html_content):
    """Extract properties from HTML content"""
    
    properties = []
    
    # Look for tax deed numbers in various patterns
    patterns = [
        r'(\d{5})\s*</a>',  # Tax deed number in links
        r'href="[^"]*(\d{5})_[^"]*\.pdf"',  # PDF links with tax deed numbers
        r'Tax Deed #?\s*(\d{5})',  # Direct tax deed references
    ]
    
    for pattern in patterns:
        matches = re.finditer(pattern, html_content, re.IGNORECASE)
        for match in matches:
            tax_deed_number = match.group(1)
            print(f"Found potential tax deed: {tax_deed_number}")
            
            # Try to extract additional info around this match
            start = max(0, match.start() - 500)
            end = min(len(html_content), match.end() + 500)
            context = html_content[start:end]
            
            property_data = {
                'tax_deed_number': tax_deed_number,
                'context': context[:200] + "..." if len(context) > 200 else context
            }
            
            # Look for opening bid in context
            bid_match = re.search(r'\$?([\d,]+\.?\d*)', context)
            if bid_match:
                try:
                    property_data['opening_bid'] = float(bid_match.group(1).replace(',', ''))
                except:
                    pass
            
            properties.append(property_data)
    
    return properties

def main():
    """Main function"""
    
    print("Starting simple tax deed analysis...")
    
    # First analyze with requests
    html_content = analyze_page_structure()
    
    if html_content:
        # Try to extract properties
        properties = extract_properties_from_html(html_content)
        
        print(f"\n\nFound {len(properties)} potential properties:")
        for prop in properties:
            print(f"Tax Deed: {prop['tax_deed_number']}")
            if 'opening_bid' in prop:
                print(f"  Opening Bid: ${prop['opening_bid']}")
            print(f"  Context: {prop['context']}")
            print()
        
        # Save analysis to file
        with open('tax_deed_analysis.json', 'w') as f:
            json.dump({
                'properties': properties,
                'total_found': len(properties),
                'analysis_time': datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"Analysis saved to tax_deed_analysis.json")
    
    else:
        print("Failed to fetch page content")

if __name__ == "__main__":
    main()