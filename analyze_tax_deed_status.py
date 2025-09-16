import os
from supabase import create_client, Client
import json
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

def analyze_tax_deed_status():
    print("Analyzing tax deed status distribution...")
    
    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    try:
        # Get all tax deed bidding items with status analysis
        response = supabase.table('tax_deed_bidding_items').select("*").execute()
        
        if not response.data:
            print("No data found in tax_deed_bidding_items table")
            return
        
        data = response.data
        print(f"Total records: {len(data)}")
        
        # Analyze status distribution
        status_counts = {}
        active_items = []
        cancelled_items = []
        upcoming_items = []
        
        for item in data:
            status = item.get('item_status', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Categorize items based on status and close_time
            close_time = item.get('close_time')
            now = datetime.now()
            
            if status in ['Active', 'Upcoming']:
                if close_time:
                    close_dt = datetime.fromisoformat(close_time.replace('Z', '+00:00'))
                    if close_dt > now:
                        upcoming_items.append(item)
                    else:
                        # Past due but still marked active
                        item['_analysis'] = 'Past due but marked active'
                        upcoming_items.append(item)
                else:
                    upcoming_items.append(item)
            elif status in ['Canceled', 'Cancelled', 'Removed']:
                cancelled_items.append(item)
            else:
                active_items.append(item)
        
        print("\n=== STATUS DISTRIBUTION ===")
        for status, count in sorted(status_counts.items()):
            print(f"{status}: {count} items")
        
        print(f"\n=== CATEGORIZED ANALYSIS ===")
        print(f"Active/Upcoming items: {len(upcoming_items)}")
        print(f"Cancelled items: {len(cancelled_items)}")
        print(f"Other status items: {len(active_items)}")
        
        # Look at parcel IDs and addresses
        unknown_parcels = [item for item in data if item.get('parcel_id', '').startswith('UNKNOWN')]
        real_parcels = [item for item in data if not item.get('parcel_id', '').startswith('UNKNOWN')]
        no_address = [item for item in data if item.get('legal_situs_address') == 'Address not available']
        
        print(f"\n=== DATA QUALITY ANALYSIS ===")
        print(f"Unknown parcel IDs: {len(unknown_parcels)}")
        print(f"Real parcel IDs: {len(real_parcels)}")
        print(f"Missing addresses: {len(no_address)}")
        
        # Sample upcoming items that should show
        print(f"\n=== SAMPLE UPCOMING ITEMS (should show on website) ===")
        valid_upcoming = [item for item in upcoming_items if not item.get('parcel_id', '').startswith('UNKNOWN')]
        
        for i, item in enumerate(valid_upcoming[:5]):
            print(f"\nItem {i+1}:")
            print(f"  Tax Deed #: {item.get('tax_deed_number')}")
            print(f"  Parcel ID: {item.get('parcel_id')}")
            print(f"  Status: {item.get('item_status')}")
            print(f"  Address: {item.get('legal_situs_address')}")
            print(f"  Opening Bid: ${item.get('opening_bid', 0)}")
            print(f"  Close Time: {item.get('close_time')}")
            
        # Check if there's an auction_date field missing
        print(f"\n=== FIELD ANALYSIS ===")
        sample_item = data[0] if data else {}
        print("Available fields:")
        for field in sample_item.keys():
            sample_value = sample_item[field]
            print(f"  {field}: {type(sample_value).__name__} = {sample_value}")
        
        # Create analysis report
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_records": len(data),
            "status_distribution": status_counts,
            "categorized_counts": {
                "upcoming_items": len(upcoming_items),
                "cancelled_items": len(cancelled_items),
                "other_items": len(active_items)
            },
            "data_quality": {
                "unknown_parcels": len(unknown_parcels),
                "real_parcels": len(real_parcels),
                "missing_addresses": len(no_address)
            },
            "sample_upcoming_items": valid_upcoming[:5],
            "issue_analysis": {
                "total_in_db": len(data),
                "should_show_upcoming": len(valid_upcoming),
                "difference_from_website": len(valid_upcoming) - 13,
                "possible_issues": [
                    "Frontend filtering by close_time might be too restrictive",
                    "Unknown parcel IDs are being filtered out",
                    "Missing auction_date field causing issues",
                    "Status mapping between DB and frontend inconsistent"
                ]
            }
        }
        
        # Save analysis
        with open('tax_deed_status_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        print(f"\n=== KEY FINDINGS ===")
        print(f"• Database has {len(data)} total items")
        print(f"• {len(valid_upcoming)} items should be visible as 'upcoming'")
        print(f"• Website only shows 13 items")
        print(f"• Potential issue: {len(valid_upcoming) - 13} items not showing")
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing tax deed status: {e}")
        return None

if __name__ == "__main__":
    analysis = analyze_tax_deed_status()
    print("\nStatus analysis complete. Results saved to 'tax_deed_status_analysis.json'")