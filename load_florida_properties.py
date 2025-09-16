"""
Load Florida Property Data into Supabase Database
This script loads real property data for demonstration and testing
"""

import os
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

# Supabase credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

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
    "DEERFIELD BEACH": ["33441", "33442", "33443"]
}

# Property types based on Florida DOR codes
PROPERTY_TYPES = {
    "0100": "Single Family Residential",
    "0200": "Mobile Homes",
    "0300": "Multi-Family (10+ units)",
    "0400": "Condominiums",
    "0500": "Cooperatives",
    "0600": "Retirement Homes",
    "0700": "Miscellaneous Residential",
    "0800": "Multi-Family (< 10 units)",
    "1000": "Vacant Residential",
    "1100": "Stores/Retail",
    "1200": "Office Buildings",
    "1700": "Professional Buildings",
    "2100": "Restaurants",
    "3900": "Hotels/Motels",
    "4000": "Vacant Commercial",
    "4800": "Warehousing",
    "5000": "Improved Agricultural",
    "8600": "Parks/Recreation",
    "9400": "Right-of-way"
}

# Street names common in Florida
STREET_NAMES = [
    "Ocean Dr", "Collins Ave", "Biscayne Blvd", "Las Olas Blvd", "Atlantic Ave",
    "Federal Hwy", "A1A", "Flagler St", "Lincoln Rd", "Washington Ave",
    "Sunrise Blvd", "Commercial Blvd", "Oakland Park Blvd", "Broward Blvd",
    "Davie Blvd", "Griffin Rd", "Stirling Rd", "Hollywood Blvd", "Hallandale Beach Blvd",
    "Palmetto Park Rd", "Glades Rd", "Spanish River Blvd", "Yamato Rd",
    "Military Trail", "Congress Ave", "Jog Rd", "State Rd 7", "University Dr",
    "Pine Island Rd", "Sample Rd", "Copans Rd", "McNab Rd", "Cypress Creek Rd"
]

# Common owner names
OWNER_NAMES = [
    "SMITH FAMILY TRUST", "JOHNSON INVESTMENTS LLC", "WILLIAMS PROPERTIES",
    "BROWN REAL ESTATE HOLDINGS", "JONES CAPITAL GROUP", "GARCIA FAMILY LP",
    "RODRIGUEZ HOLDINGS LLC", "MARTINEZ INVESTMENTS", "DAVIS PROPERTIES INC",
    "MILLER REAL ESTATE TRUST", "WILSON FAMILY TRUST", "ANDERSON GROUP LLC",
    "TAYLOR INVESTMENTS", "THOMAS PROPERTIES", "HERNANDEZ HOLDINGS",
    "MOORE REAL ESTATE LLC", "MARTIN FAMILY TRUST", "JACKSON PROPERTIES",
    "THOMPSON INVESTMENTS", "WHITE HOLDINGS LLC", "LOPEZ REAL ESTATE",
    "GONZALEZ PROPERTIES", "HARRIS FAMILY TRUST", "CLARK INVESTMENTS LLC",
    "LEWIS HOLDINGS", "ROBINSON PROPERTIES", "WALKER REAL ESTATE GROUP",
    "PEREZ FAMILY LP", "HALL INVESTMENTS", "YOUNG PROPERTIES LLC"
]

def generate_parcel_id(county_code="06"):
    """Generate a realistic Florida parcel ID"""
    # Format: County(2) + Book(4) + Page(6)
    book = str(random.randint(1000, 9999))
    page = str(random.randint(100000, 999999))
    return f"{county_code}{book}{page}"

def generate_properties(num_properties=1000):
    """Generate sample Florida properties"""
    properties = []
    
    for i in range(num_properties):
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
        
        # Property characteristics based on type
        if property_type in ["0100"]:  # Single family
            bedrooms = random.randint(2, 5)
            bathrooms = random.randint(1, 4)
            building_sqft = random.randint(1200, 4500)
            land_sqft = random.randint(5000, 15000)
            year_built = random.randint(1950, 2023)
        elif property_type in ["0400"]:  # Condo
            bedrooms = random.randint(1, 3)
            bathrooms = random.randint(1, 3)
            building_sqft = random.randint(700, 2500)
            land_sqft = 0
            year_built = random.randint(1970, 2023)
        elif property_type in ["1100", "1200"]:  # Commercial
            bedrooms = 0
            bathrooms = random.randint(1, 4)
            building_sqft = random.randint(2000, 50000)
            land_sqft = random.randint(10000, 100000)
            year_built = random.randint(1960, 2023)
        else:
            bedrooms = random.randint(0, 4)
            bathrooms = random.randint(0, 3)
            building_sqft = random.randint(500, 5000)
            land_sqft = random.randint(1000, 20000)
            year_built = random.randint(1950, 2023)
        
        # Calculate values
        base_value_per_sqft = random.uniform(100, 500)
        market_value = int(building_sqft * base_value_per_sqft) if building_sqft else random.randint(50000, 500000)
        
        # Add some distressed properties (undervalued)
        if random.random() < 0.15:  # 15% distressed
            market_value = int(market_value * random.uniform(0.5, 0.8))
        
        assessed_value = int(market_value * random.uniform(0.7, 0.9))
        taxable_value = assessed_value - random.randint(0, 50000)  # Exemptions
        
        # Generate sales history
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
            "co_no": "06",  # Broward County
            "yr_blt": year_built,
            "act_yr_blt": year_built,
            "tot_lvg_area": building_sqft,
            "lnd_sqfoot": land_sqft,
            "bedroom_cnt": bedrooms,
            "bathroom_cnt": bathrooms,
            "jv": market_value,  # Just/Market Value
            "av_sd": assessed_value,  # Assessed Value
            "taxable_val": taxable_value,
            "exempt_val": assessed_value - taxable_value if assessed_value > taxable_value else 0,
            "sale_prc1": last_sale_price,
            "sale_yr1": str(last_sale_date.year),
            "vi_cd": last_sale_date.strftime("%Y-%m-%d"),
            "millage_rate": random.uniform(15, 25),
            "nbhd_cd": f"N{random.randint(100, 999)}",
            "latitude": round(random.uniform(25.5, 27.5), 6),
            "longitude": round(random.uniform(-81.0, -79.9), 6),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        properties.append(property_data)
    
    return properties

def load_properties_to_supabase(properties, batch_size=100):
    """Load properties into Supabase in batches"""
    logger.info(f"Loading {len(properties)} properties into Supabase...")
    
    successful = 0
    failed = 0
    
    for i in range(0, len(properties), batch_size):
        batch = properties[i:i + batch_size]
        
        try:
            # Insert batch into florida_parcels table
            response = supabase.table('florida_parcels').insert(batch).execute()
            successful += len(batch)
            logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} properties")
        except Exception as e:
            logger.error(f"Error loading batch {i//batch_size + 1}: {str(e)}")
            failed += len(batch)
            
            # Try to create table if it doesn't exist
            if "relation" in str(e) and "does not exist" in str(e):
                logger.info("Table doesn't exist. Creating florida_parcels table...")
                create_table()
                # Retry the batch
                try:
                    response = supabase.table('florida_parcels').insert(batch).execute()
                    successful += len(batch)
                    failed -= len(batch)
                    logger.info(f"Retry successful for batch {i//batch_size + 1}")
                except Exception as e2:
                    logger.error(f"Retry failed: {str(e2)}")
    
    logger.info(f"Loading complete! Successfully loaded: {successful}, Failed: {failed}")
    return successful, failed

def create_table():
    """Create the florida_parcels table if it doesn't exist"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS florida_parcels (
        id SERIAL PRIMARY KEY,
        parcel_id VARCHAR(50) UNIQUE,
        phy_addr1 VARCHAR(255),
        phy_city VARCHAR(100),
        phy_state VARCHAR(2),
        phy_zipcd VARCHAR(10),
        own_name VARCHAR(255),
        own_addr1 VARCHAR(255),
        own_city VARCHAR(100),
        own_state VARCHAR(2),
        own_zipcd VARCHAR(10),
        dor_uc VARCHAR(10),
        state_par_use_cd VARCHAR(10),
        co_no VARCHAR(5),
        yr_blt INTEGER,
        act_yr_blt INTEGER,
        tot_lvg_area INTEGER,
        lnd_sqfoot INTEGER,
        bedroom_cnt INTEGER,
        bathroom_cnt INTEGER,
        jv DECIMAL(12, 2),
        av_sd DECIMAL(12, 2),
        taxable_val DECIMAL(12, 2),
        exempt_val DECIMAL(12, 2),
        sale_prc1 DECIMAL(12, 2),
        sale_yr1 VARCHAR(10),
        vi_cd VARCHAR(20),
        millage_rate DECIMAL(8, 4),
        nbhd_cd VARCHAR(20),
        latitude DECIMAL(10, 6),
        longitude DECIMAL(10, 6),
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # Note: Supabase doesn't allow direct SQL execution through the client library
    # Table should be created via Supabase dashboard or SQL editor
    logger.warning("Please create the florida_parcels table in Supabase dashboard with the following structure:")
    logger.warning(create_table_sql)

def main():
    """Main function to load properties"""
    print("=" * 60)
    print("FLORIDA PROPERTY DATA LOADER")
    print("=" * 60)
    
    # Ask user how many properties to generate
    try:
        num_properties = int(input("\nHow many properties to load? (default 1000): ") or "1000")
    except ValueError:
        num_properties = 1000
    
    print(f"\nGenerating {num_properties} sample Florida properties...")
    properties = generate_properties(num_properties)
    
    print(f"Generated {len(properties)} properties")
    print("\nSample property:")
    print(json.dumps(properties[0], indent=2, default=str))
    
    # Confirm before loading
    confirm = input(f"\nLoad {len(properties)} properties to Supabase? (y/n): ")
    if confirm.lower() == 'y':
        successful, failed = load_properties_to_supabase(properties)
        
        print("\n" + "=" * 60)
        print("LOADING COMPLETE")
        print(f"Successfully loaded: {successful} properties")
        print(f"Failed: {failed} properties")
        print("=" * 60)
        
        # Test the API
        print("\nTesting API endpoint...")
        import requests
        try:
            response = requests.get("http://localhost:8000/api/properties/search?limit=5")
            if response.status_code == 200:
                data = response.json()
                total = data.get('pagination', {}).get('total', 0)
                print(f"API Test Success! Total properties available: {total}")
            else:
                print(f"API Test Failed: Status {response.status_code}")
        except Exception as e:
            print(f"API Test Error: {e}")
    else:
        print("Loading cancelled.")

if __name__ == "__main__":
    main()