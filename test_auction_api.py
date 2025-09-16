"""
Test fetching data from the auction API endpoint
"""
import asyncio
import aiohttp
import json

async def test_api():
    """Test the auction API endpoint"""
    BASE_URL = "https://broward.deedauction.net"
    API_URL = f"{BASE_URL}/auctions/upcoming"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': 'https://broward.deedauction.net/auctions'
    }
    
    # DataTables request parameters
    data = {
        'draw': '1',
        'start': '0',
        'length': '10',
        'search[value]': '',
        'search[regex]': 'false',
        'order[0][column]': '0',
        'order[0][dir]': 'asc'
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.post(API_URL, data=data) as response:
            print(f"Status: {response.status}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            
            text = await response.text()
            print(f"\nResponse ({len(text)} chars):")
            
            try:
                json_data = json.loads(text)
                print(json.dumps(json_data, indent=2))
                
                # Extract auction data
                if 'data' in json_data:
                    print(f"\n=== Found {len(json_data['data'])} auctions ===")
                    for auction in json_data['data']:
                        print(f"\nAuction:")
                        for key, value in auction.items():
                            print(f"  {key}: {value}")
                            
            except json.JSONDecodeError:
                print("Could not parse as JSON:")
                print(text[:500])

asyncio.run(test_api())