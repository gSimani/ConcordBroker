"""
Quick check of Florida Property Appraiser Upload Status
"""

from datetime import datetime
from supabase import create_client, Client

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_status():
    """Check current upload status"""
    client = get_supabase_client()
    
    print("=" * 80)
    print("FLORIDA PROPERTY APPRAISER UPLOAD STATUS")
    print("=" * 80)
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    try:
        # Query the monitoring view
        result = client.table('florida_parcels_ingest_status').select('*').execute()
        
        if result.data:
            # Calculate totals
            total_counties = len(result.data)
            total_records = sum(row['total_rows'] for row in result.data)
            
            print(f"Total Counties in Database: {total_counties}")
            print(f"Total Property Records: {total_records:,}")
            print("-" * 80)
            print(f"{'County':<20} {'Records':<15} {'Has Values':<15} {'Has Owner':<15}")
            print("-" * 80)
            
            # Display all counties sorted by record count
            for row in sorted(result.data, key=lambda x: x['total_rows'], reverse=True):
                county = row.get('county', 'Unknown')
                total = row.get('total_rows', 0)
                has_values = row.get('has_values', 0)
                has_owner = row.get('has_owner', 0)
                
                print(f"{county:<20} {total:<15,} {has_values:<15,} {has_owner:<15,}")
            
            print("-" * 80)
            print(f"Summary: {total_counties} counties, {total_records:,} total records")
            
            # List of all Florida counties to check what's missing
            all_counties = [
                'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN', 
                'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DADE', 'DESOTO', 
                'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 
                'GILCHRIST', 'GLADES', 'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 
                'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER', 
                'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE', 'LEON', 'LEVY', 
                'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN', 'MONROE', 
                'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM BEACH', 
                'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA ROSA', 'SARASOTA', 
                'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 
                'UNION', 'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
            ]
            
            uploaded_counties = {row['county'] for row in result.data}
            missing_counties = [c for c in all_counties if c not in uploaded_counties]
            
            if missing_counties:
                print(f"\nMissing counties ({len(missing_counties)}):")
                print(", ".join(missing_counties))
            else:
                print("\nAll 67 Florida counties have been uploaded!")
            
        else:
            print("No data found in monitoring view yet...")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_status()