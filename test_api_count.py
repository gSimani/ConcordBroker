import requests
import json

# Test the API to see total count
response = requests.get("http://localhost:8000/api/properties/search?limit=1")
data = response.json()

print("="*50)
print("API RESPONSE SUMMARY")
print("="*50)
print(f"Success: {data.get('success')}")
print(f"Total Properties: {data.get('pagination', {}).get('total', 0):,}")
print(f"Total Pages: {data.get('pagination', {}).get('pages', 0):,}")
print(f"Current Page: {data.get('pagination', {}).get('page', 0)}")
print(f"Limit per page: {data.get('pagination', {}).get('limit', 0)}")
print("="*50)