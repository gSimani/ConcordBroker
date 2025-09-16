"""
Test the actual API response format
"""
import requests
import json

# Test the upcoming auctions endpoint
url = "https://broward.deedauction.net/auctions/upcoming"

# Try as POST with DataTables format
data = {
    "draw": 1,
    "start": 0,
    "length": 100,
    "order": [{"column": 0, "dir": "asc"}]
}

print("Testing POST to:", url)
response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('content-type')}")

try:
    json_data = response.json()
    print("\nJSON Response received!")
    print(f"Keys: {json_data.keys()}")
    
    if 'data' in json_data:
        print(f"Found {len(json_data['data'])} items")
        if json_data['data']:
            print("\nFirst item:")
            print(json.dumps(json_data['data'][0], indent=2))
except:
    print("\nNot JSON, first 500 chars of response:")
    print(response.text[:500])