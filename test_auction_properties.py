"""
Test fetching properties from auction page
"""
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import json

async def test_properties():
    """Test fetching properties for auction 110"""
    BASE_URL = "https://broward.deedauction.net"
    auction_id = "110"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # First, get the auction page to find the data table configuration
        url = f"{BASE_URL}/auction/{auction_id}"
        async with session.get(url) as response:
            html = await response.text()
            
            # Look for the DataTable configuration in JavaScript
            # Find the script that contains the table configuration
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'DataTable' in script.string and 'ajax' in script.string:
                    # Extract the AJAX URL
                    ajax_match = re.search(r'"ajax":\s*{[^}]*"url":\s*"([^"]+)"', script.string)
                    if ajax_match:
                        ajax_url = ajax_match.group(1)
                        print(f"Found AJAX URL: {ajax_url}")
                        
                        # Make the AJAX request
                        full_url = f"{BASE_URL}{ajax_url}" if ajax_url.startswith('/') else ajax_url
                        
                        # DataTables parameters
                        data = {
                            'draw': '1',
                            'start': '0',
                            'length': '100',
                            'search[value]': '',
                            'search[regex]': 'false',
                            'order[0][column]': '0',
                            'order[0][dir]': 'asc'
                        }
                        
                        # Update headers for AJAX request
                        ajax_headers = headers.copy()
                        ajax_headers.update({
                            'Accept': 'application/json, text/javascript, */*; q=0.01',
                            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                            'X-Requested-With': 'XMLHttpRequest',
                            'Referer': url
                        })
                        
                        async with session.post(full_url, data=data, headers=ajax_headers) as ajax_response:
                            print(f"AJAX Status: {ajax_response.status}")
                            
                            if ajax_response.status == 200:
                                try:
                                    json_data = await ajax_response.json()
                                    
                                    if 'data' in json_data:
                                        print(f"\nFound {len(json_data['data'])} properties")
                                        
                                        # Show first few properties
                                        for i, prop in enumerate(json_data['data'][:3]):
                                            print(f"\nProperty {i+1}:")
                                            for key, value in prop.items():
                                                if not isinstance(value, dict):
                                                    print(f"  {key}: {value}")
                                                else:
                                                    print(f"  {key}: {json.dumps(value)}")
                                                    
                                except Exception as e:
                                    print(f"Error parsing JSON: {e}")
                                    text = await ajax_response.text()
                                    print(f"Response: {text[:500]}")

asyncio.run(test_properties())