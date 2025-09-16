"""
Check tax_deed_bidding_items table data
"""
from supabase import create_client, Client

# Use the frontend Supabase instance
SUPABASE_URL = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Get data from tax_deed_bidding_items
    response = supabase.table('tax_deed_bidding_items').select('*').limit(10).execute()
    
    if response.data:
        print(f"Found {len(response.data)} items in tax_deed_bidding_items table")
        
        # Count total
        count_response = supabase.table('tax_deed_bidding_items').select('*', count='exact').execute()
        total = len(count_response.data) if count_response.data else 0
        print(f"Total items in table: {total}")
        
        # Show first item structure
        if response.data:
            print("\nFirst item structure:")
            first_item = response.data[0]
            for key in first_item.keys():
                value = first_item[key]
                if value:
                    print(f"  {key}: {str(value)[:50]}...")
                    
            # Show statuses
            print("\nItem statuses:")
            status_counts = {}
            for item in response.data:
                status = item.get('item_status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            for status, count in status_counts.items():
                print(f"  {status}: {count}")
    else:
        print("No data found in tax_deed_bidding_items table")
        
except Exception as e:
    print(f"Error: {e}")