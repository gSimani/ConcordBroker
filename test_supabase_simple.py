import requests
import json

# Use the web app's credentials
url = "https://pmispwtdngkcmsrsjwbp.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

print(f"Testing Supabase connection...")
print(f"URL: {url}")

# Test the REST API directly
headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json"
}

# Try to query florida_parcels table
response = requests.get(
    f"{url}/rest/v1/florida_parcels?limit=5",
    headers=headers
)

print(f"\nStatus Code: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if data:
        print(f"[OK] Table exists with {len(data)} sample records")
        if len(data) > 0:
            print(f"\nFirst record sample:")
            for key, value in list(data[0].items())[:5]:
                print(f"  {key}: {value}")
    else:
        print("[OK] Table exists but has no data")
        print("\nYou need to populate the florida_parcels table with data.")
elif response.status_code == 404:
    print("[ERROR] Table 'florida_parcels' does not exist")
    print("\nThe table needs to be created first.")
else:
    print(f"Error: {response.text}")

# Check if table exists with a count query
count_response = requests.get(
    f"{url}/rest/v1/florida_parcels?select=*&limit=0",
    headers={**headers, "Prefer": "count=exact"}
)

if count_response.status_code == 200:
    content_range = count_response.headers.get('content-range')
    if content_range:
        total = content_range.split('/')[1]
        print(f"\nTotal records in florida_parcels: {total}")