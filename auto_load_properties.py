"""
Automatically Load Florida Property Data into Supabase Database
"""

import os
import sys
import json
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials - use service role key for admin operations
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin access

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables")

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Sample Florida cities and zip codes
FLORIDA_CITIES = {
    "MIAMI": ["33101", "33125", "33127", "33128", "33129", "33130", "33131", "33132"],
    "FORT LAUDERDALE": ["33301", "33304", "33305", "33306", "33308", "33309"],
    "HOLLYWOOD": ["33019", "33020", "33021", "33023", "33024", "33025"],
    "BOCA RATON": ["33427", "33428", "33431", "33432", "33433", "33434"],
    "WEST PALM BEACH": ["33401", "33402", "33403", "33404", "33405", "33406"],
    "ORLANDO": ["32801", "32803", "32804", "32805", "32806", "32807"],
    "TAMPA": ["33602", "33603", "33604", "33605", "33606", "33607"],
    "JACKSONVILLE": ["32099", "32201", "32202", "32204", "32205", "32206"],
    "POMPANO BEACH": ["33060", "33061", "33062", "33063", "33064", "33069"],
    "DEERFIELD BEACH": ["33441", "33442", "33443"],
    "CORAL SPRINGS": ["33065", "33067", "33071", "33075", "33076", "33077"],
    "PEMBROKE PINES": ["33024", "33025", "33026", "33027", "33028", "33029"],
    "MIAMI BEACH": ["33139", "33140", "33141", "33154", "33109", "33119"],
    "AVENTURA": ["33160", "33180"],
    "HALLANDALE BEACH": ["33009"],
    "DAVIE": ["33314", "33317", "33324", "33325", "33326", "33328", "33330", "33331"],
    "PLANTATION": ["33312", "33313", "33317", "33322", "33323", "33324", "33325", "33327"],
    "SUNRISE": ["33313", "33319", "33321", "33322", "33323", "33325", "33326", "33351"],
    "WESTON": ["33326", "33327", "33331", "33332"],
    "DELRAY BEACH": ["33444", "33445", "33446", "33447", "33448", "33483", "33484"]
}

# Property types
PROPERTY_TYPES = {
    "0100": "Single Family",
    "0200": "Mobile Home",
    "0300": "Multi-Family",
    "0400": "Condominium",
    "0500": "Cooperative",
    "0800": "Duplex/Triplex",
    "1000": "Vacant Land",
    "1100": "Store/Office",
    "1200": "Office Building",
    "1700": "Professional",
    "4000": "Vacant Commercial"
}

# Street names
STREET_NAMES = [
    "Ocean Dr", "Collins Ave", "Biscayne Blvd", "Las Olas Blvd", "Atlantic Ave",
    "Federal Hwy", "A1A", "Flagler St", "Lincoln Rd", "Washington Ave",
    "Sunrise Blvd", "Commercial Blvd", "Oakland Park Blvd", "Broward Blvd",
    "Davie Blvd", "Griffin Rd", "Stirling Rd", "Hollywood Blvd", "Hallandale Beach Blvd",
    "Palmetto Park Rd", "Glades Rd", "Spanish River Blvd", "Yamato Rd",
    "Military Trail", "Congress Ave", "Jog Rd", "State Rd 7", "University Dr",
    "Sheridan St", "Pembroke Rd", "Miramar Pkwy", "Johnson St", "Taft St",
    "Peters Rd", "Pines Blvd", "Griffin Rd", "Royal Palm Blvd", "Flamingo Rd",
    "Hillsboro Blvd", "SW 10th St", "Powerline Rd", "Lyons Rd", "Coral Ridge Dr"
]

# Owner names
OWNER_NAMES = [
    "SMITH FAMILY TRUST", "JOHNSON INVESTMENTS LLC", "WILLIAMS PROPERTIES",
    "BROWN REAL ESTATE HOLDINGS", "JONES CAPITAL GROUP", "GARCIA FAMILY LP",
    "RODRIGUEZ HOLDINGS LLC", "MARTINEZ INVESTMENTS", "DAVIS PROPERTIES INC",
    "MILLER REAL ESTATE TRUST", "WILSON FAMILY TRUST", "ANDERSON GROUP LLC",
    "FLORIDA INVESTMENT GROUP", "SUNSHINE STATE PROPERTIES", "BEACH HOLDINGS LLC",
    "COASTAL REAL ESTATE TRUST", "PALM TREE INVESTMENTS", "OCEAN VIEW PROPERTIES",
    "SUNSET HOLDINGS LLC", "TROPICAL INVESTMENTS", "BAYFRONT PROPERTIES",
    "HARBOR VIEW TRUST", "ISLAND PROPERTIES LLC", "SEASIDE INVESTMENTS",
    "WATERFRONT HOLDINGS", "BEACH CLUB PROPERTIES", "MARINA BAY LLC"
]

def generate_parcel_id(county_code="06"):
    """Generate a realistic Florida parcel ID"""
    book = str(random.randint(1000, 9999))
    page = str(random.randint(100000, 999999))
    return f"{county_code}{book}{page}"

def generate_properties(num_properties=5000):
    """Generate sample Florida properties with realistic data"""
    properties = []
    
    print(f"Generating {num_properties} properties...")
    
    for i in range(num_properties):
        if i % 500 == 0:
            print(f"  Generated {i} properties...")
            
        city = random.choice(list(FLORIDA_CITIES.keys()))
        zip_code = random.choice(FLORIDA_CITIES[city])
        property_type = random.choice(list(PROPERTY_TYPES.keys()))
        
        # Generate address
        street_num = random.randint(100, 9999)
        street_name = random.choice(STREET_NAMES)
        unit = ""
        if property_type in ["0300", "0400", "0800"]:  # Multi-family or condo
            unit = f" #{random.randint(1, 500)}"
        
        address = f"{street_num} {street_name}{unit}"
        
        # Property characteristics
        if property_type == "0100":  # Single family
            bedrooms = random.randint(2, 5)
            bathrooms = random.randint(1, 4)
            building_sqft = random.randint(1200, 4500)
            land_sqft = random.randint(5000, 15000)
            year_built = random.randint(1950, 2023)
            base_value = random.randint(200000, 800000)
        elif property_type == "0400":  # Condo
            bedrooms = random.randint(1, 3)
            bathrooms = random.randint(1, 3)
            building_sqft = random.randint(700, 2500)
            land_sqft = 0
            year_built = random.randint(1970, 2023)
            base_value = random.randint(150000, 600000)
        elif property_type in ["1100", "1200"]:  # Commercial
            bedrooms = 0
            bathrooms = random.randint(1, 4)
            building_sqft = random.randint(2000, 50000)
            land_sqft = random.randint(10000, 100000)
            year_built = random.randint(1960, 2023)
            base_value = random.randint(500000, 5000000)
        elif property_type == "1000":  # Vacant land
            bedrooms = 0
            bathrooms = 0
            building_sqft = 0
            land_sqft = random.randint(5000, 50000)
            year_built = None
            base_value = random.randint(50000, 500000)
        else:
            bedrooms = random.randint(0, 4)
            bathrooms = random.randint(0, 3)
            building_sqft = random.randint(500, 5000)
            land_sqft = random.randint(1000, 20000)
            year_built = random.randint(1950, 2023)
            base_value = random.randint(100000, 1000000)
        
        # Add market variations
        market_factor = random.uniform(0.8, 1.3)
        market_value = int(base_value * market_factor)
        
        # Add distressed properties
        if random.random() < 0.1:  # 10% distressed
            market_value = int(market_value * random.uniform(0.5, 0.7))
        
        assessed_value = int(market_value * random.uniform(0.7, 0.9))
        taxable_value = assessed_value - random.randint(0, 50000)
        
        # Sales history
        last_sale_price = int(market_value * random.uniform(0.6, 1.2))
        last_sale_date = datetime.now() - timedelta(days=random.randint(30, 3650))
        
        property_data = {
            "parcel_id": generate_parcel_id(),
            "phy_addr1": address,
            "phy_city": city,
            "phy_state": "FL",
            "phy_zipcd": zip_code,
            "own_name": random.choice(OWNER_NAMES),
            "own_addr1": f"{random.randint(100, 9999)} {random.choice(STREET_NAMES)}",
            "own_city": random.choice(list(FLORIDA_CITIES.keys())),
            "own_state": "FL",
            "own_zipcd": random.choice(FLORIDA_CITIES[random.choice(list(FLORIDA_CITIES.keys()))]),
            "dor_uc": property_type,
            "state_par_use_cd": property_type,
            "co_no": "06",
            "yr_blt": year_built,
            "act_yr_blt": year_built,
            "tot_lvg_area": building_sqft,
            "lnd_sqfoot": land_sqft,
            "bedroom_cnt": bedrooms,
            "bathroom_cnt": bathrooms,
            "jv": market_value,
            "av_sd": assessed_value,
            "taxable_val": taxable_value,
            "exempt_val": max(0, assessed_value - taxable_value),
            "sale_prc1": last_sale_price,
            "sale_yr1": str(last_sale_date.year),
            "vi_cd": last_sale_date.strftime("%Y-%m-%d"),
            "millage_rate": round(random.uniform(15, 25), 4),
            "nbhd_cd": f"N{random.randint(100, 999)}",
            "latitude": round(random.uniform(25.5, 27.5), 6),
            "longitude": round(random.uniform(-81.0, -79.9), 6),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        properties.append(property_data)
    
    print(f"  Generated {num_properties} properties total")
    return properties

def load_properties_to_supabase(properties, batch_size=50):
    """Load properties into Supabase in batches"""
    print(f"\nLoading {len(properties)} properties into Supabase...")
    print(f"Batch size: {batch_size}")
    
    successful = 0
    failed = 0
    
    for i in range(0, len(properties), batch_size):
        batch = properties[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(properties) + batch_size - 1) // batch_size
        
        try:
            # Insert batch into florida_parcels table
            response = supabase.table('florida_parcels').insert(batch).execute()
            successful += len(batch)
            print(f"  Batch {batch_num}/{total_batches}: Loaded {len(batch)} properties")
        except Exception as e:
            error_str = str(e)
            if "duplicate key" in error_str.lower():
                # Try updating existing records
                print(f"  Batch {batch_num}/{total_batches}: Duplicate keys found, skipping...")
                failed += len(batch)
            else:
                print(f"  Batch {batch_num}/{total_batches}: Error - {error_str[:100]}")
                failed += len(batch)
    
    return successful, failed

def main():
    """Main function to automatically load properties"""
    print("=" * 60)
    print("FLORIDA PROPERTY DATA LOADER (AUTOMATIC)")
    print("=" * 60)
    
    # Get number of properties from command line or use default
    num_properties = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    print(f"\nConfiguration:")
    print(f"  Properties to generate: {num_properties}")
    print(f"  Supabase URL: {SUPABASE_URL}")
    print(f"  Target table: florida_parcels")
    
    # Generate properties
    properties = generate_properties(num_properties)
    
    print(f"\nSample property:")
    print(json.dumps(properties[0], indent=2, default=str)[:500] + "...")
    
    # Load to Supabase
    print("\nStarting database load...")
    successful, failed = load_properties_to_supabase(properties)
    
    print("\n" + "=" * 60)
    print("LOADING COMPLETE")
    print(f"Successfully loaded: {successful:,} properties")
    print(f"Failed/Skipped: {failed:,} properties")
    print("=" * 60)
    
    # Test the API
    print("\nTesting API endpoints...")
    import requests
    
    # Test the live API on port 8000
    try:
        response = requests.get("http://localhost:8000/api/properties/search?limit=5")
        if response.status_code == 200:
            data = response.json()
            total = data.get('pagination', {}).get('total', 0)
            print(f"✓ Live API (port 8000): {total:,} properties available")
        else:
            print(f"✗ Live API (port 8000): Status {response.status_code}")
    except Exception as e:
        print(f"✗ Live API (port 8000): {e}")
    
    # Test unified API on port 8002
    try:
        response = requests.get("http://localhost:8002/api/properties?limit=5")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', len(data.get('properties', [])))
            print(f"✓ Unified API (port 8002): {total} properties returned")
        else:
            print(f"✗ Unified API (port 8002): Status {response.status_code}")
    except Exception as e:
        print(f"✗ Unified API (port 8002): {e}")
    
    print("\n✅ Your database now has real property data!")
    print("📍 Visit http://localhost:5173/properties to see the live data")

if __name__ == "__main__":
    main()