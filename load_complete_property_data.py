"""
Load complete property data into Supabase to populate all UI fields
"""
import os
import sys
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import random

# Load environment variables
load_dotenv('apps/web/.env')

# Import after loading env
from supabase import create_client

url = os.getenv("VITE_SUPABASE_URL")
key = os.getenv("VITE_SUPABASE_ANON_KEY")

print(f"Loading complete property data into Supabase...")
print("=" * 60)

# Create client
supabase = create_client(url, key)

# First, let's create the florida_parcels table with all required fields
create_table_sql = """
CREATE TABLE IF NOT EXISTS florida_parcels (
    id SERIAL PRIMARY KEY,
    parcel_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Address fields
    phy_addr1 VARCHAR(255),
    phy_city VARCHAR(100),
    phy_state VARCHAR(2) DEFAULT 'FL',
    phy_zipcd VARCHAR(10),
    
    -- Owner fields
    own_name VARCHAR(255),
    own_addr1 VARCHAR(255),
    own_city VARCHAR(100),
    own_state VARCHAR(2),
    own_zipcd VARCHAR(10),
    
    -- Property classification
    dor_uc VARCHAR(10),  -- DOR Use Code
    property_type VARCHAR(50),
    property_use_desc VARCHAR(100),
    
    -- Values
    jv DECIMAL(15,2),  -- Just (Market) Value
    av_sd DECIMAL(15,2),  -- Assessed Value School District
    tv_sd DECIMAL(15,2),  -- Taxable Value School District
    lnd_val DECIMAL(15,2),  -- Land Value
    bldg_val DECIMAL(15,2),  -- Building Value
    
    -- Physical characteristics
    tot_lvg_area INTEGER,  -- Total Living Area (sq ft)
    lnd_sqfoot INTEGER,  -- Land Square Feet
    act_yr_blt INTEGER,  -- Actual Year Built
    eff_yr_blt INTEGER,  -- Effective Year Built
    no_res_unts INTEGER,  -- Number of Residential Units
    bedrooms INTEGER,
    bathrooms DECIMAL(3,1),
    
    -- Sales data
    sale_prc1 DECIMAL(15,2),  -- Last Sale Price
    sale_yr1 VARCHAR(4),  -- Last Sale Year
    sale_mo1 INTEGER,  -- Last Sale Month
    sale_date1 DATE,  -- Last Sale Date
    
    -- Tax data
    tax_amount DECIMAL(15,2),
    homestead_exemption DECIMAL(15,2),
    
    -- Additional fields
    subdivision VARCHAR(100),
    legal_desc TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

# Comprehensive sample properties with all fields populated
sample_properties = [
    {
        "parcel_id": "494222110010",
        "phy_addr1": "1200 BRICKELL AVE",
        "phy_city": "MIAMI",
        "phy_state": "FL",
        "phy_zipcd": "33131",
        "own_name": "BRICKELL TOWER LLC",
        "own_addr1": "1200 BRICKELL AVE SUITE 100",
        "own_city": "MIAMI",
        "own_state": "FL",
        "own_zipcd": "33131",
        "dor_uc": "011",
        "property_type": "Commercial",
        "property_use_desc": "Office Building",
        "jv": 125000000,
        "av_sd": 118750000,
        "tv_sd": 112500000,
        "lnd_val": 45000000,
        "bldg_val": 80000000,
        "tot_lvg_area": 450000,
        "lnd_sqfoot": 85000,
        "act_yr_blt": 2018,
        "eff_yr_blt": 2018,
        "no_res_unts": 0,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_prc1": 130000000,
        "sale_yr1": "2019",
        "sale_mo1": 6,
        "sale_date1": "2019-06-15",
        "tax_amount": 2250000,
        "homestead_exemption": 0,
        "subdivision": "BRICKELL CENTER",
        "legal_desc": "BRICKELL CENTER PB 150-88 LOT 1 BLK 1"
    },
    {
        "parcel_id": "504232100050",
        "phy_addr1": "3930 N OCEAN DR",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33308",
        "own_name": "OCEAN TOWERS CONDO ASSOC",
        "own_addr1": "3930 N OCEAN DR",
        "own_city": "FORT LAUDERDALE",
        "own_state": "FL",
        "own_zipcd": "33308",
        "dor_uc": "004",
        "property_type": "Residential",
        "property_use_desc": "Condominium",
        "jv": 1850000,
        "av_sd": 1665000,
        "tv_sd": 1572500,
        "lnd_val": 650000,
        "bldg_val": 1200000,
        "tot_lvg_area": 2400,
        "lnd_sqfoot": 0,
        "act_yr_blt": 1985,
        "eff_yr_blt": 2010,
        "no_res_unts": 1,
        "bedrooms": 3,
        "bathrooms": 3,
        "sale_prc1": 1950000,
        "sale_yr1": "2022",
        "sale_mo1": 3,
        "sale_date1": "2022-03-20",
        "tax_amount": 31450,
        "homestead_exemption": 50000,
        "subdivision": "OCEAN TOWERS CONDO",
        "legal_desc": "OCEAN TOWERS CONDO UNIT 1501"
    },
    {
        "parcel_id": "514245330040",
        "phy_addr1": "789 SUNSET BLVD",
        "phy_city": "HOLLYWOOD",
        "phy_state": "FL",
        "phy_zipcd": "33019",
        "own_name": "JOHNSON FAMILY TRUST",
        "own_addr1": "789 SUNSET BLVD",
        "own_city": "HOLLYWOOD",
        "own_state": "FL",
        "own_zipcd": "33019",
        "dor_uc": "001",
        "property_type": "Residential",
        "property_use_desc": "Single Family",
        "jv": 785000,
        "av_sd": 706500,
        "tv_sd": 656500,
        "lnd_val": 385000,
        "bldg_val": 400000,
        "tot_lvg_area": 3200,
        "lnd_sqfoot": 12500,
        "act_yr_blt": 1998,
        "eff_yr_blt": 2015,
        "no_res_unts": 1,
        "bedrooms": 4,
        "bathrooms": 3.5,
        "sale_prc1": 810000,
        "sale_yr1": "2020",
        "sale_mo1": 8,
        "sale_date1": "2020-08-10",
        "tax_amount": 13130,
        "homestead_exemption": 50000,
        "subdivision": "HOLLYWOOD HILLS",
        "legal_desc": "HOLLYWOOD HILLS PB 42-89 LOT 15 BLK 7"
    },
    {
        "parcel_id": "524257250080",
        "phy_addr1": "2500 UNIVERSITY DR",
        "phy_city": "DAVIE",
        "phy_state": "FL",
        "phy_zipcd": "33324",
        "own_name": "UNIVERSITY PLAZA LLC",
        "own_addr1": "100 CORPORATE BLVD",
        "own_city": "MIAMI",
        "own_state": "FL",
        "own_zipcd": "33126",
        "dor_uc": "011",
        "property_type": "Commercial",
        "property_use_desc": "Shopping Center",
        "jv": 28500000,
        "av_sd": 25650000,
        "tv_sd": 24200000,
        "lnd_val": 8500000,
        "bldg_val": 20000000,
        "tot_lvg_area": 125000,
        "lnd_sqfoot": 435600,
        "act_yr_blt": 2005,
        "eff_yr_blt": 2005,
        "no_res_unts": 0,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_prc1": 29750000,
        "sale_yr1": "2021",
        "sale_mo1": 12,
        "sale_date1": "2021-12-01",
        "tax_amount": 484000,
        "homestead_exemption": 0,
        "subdivision": "UNIVERSITY COMMONS",
        "legal_desc": "UNIVERSITY COMMONS PB 168-45 LOTS 1-10"
    },
    {
        "parcel_id": "534268140120",
        "phy_addr1": "456 CORAL SPRINGS DR",
        "phy_city": "CORAL SPRINGS",
        "phy_state": "FL",
        "phy_zipcd": "33065",
        "own_name": "MARTINEZ ROBERTO & MARIA",
        "own_addr1": "456 CORAL SPRINGS DR",
        "own_city": "CORAL SPRINGS",
        "own_state": "FL",
        "own_zipcd": "33065",
        "dor_uc": "001",
        "property_type": "Residential",
        "property_use_desc": "Single Family",
        "jv": 565000,
        "av_sd": 508500,
        "tv_sd": 458500,
        "lnd_val": 265000,
        "bldg_val": 300000,
        "tot_lvg_area": 2850,
        "lnd_sqfoot": 9800,
        "act_yr_blt": 2003,
        "eff_yr_blt": 2003,
        "no_res_unts": 1,
        "bedrooms": 4,
        "bathrooms": 2.5,
        "sale_prc1": 575000,
        "sale_yr1": "2019",
        "sale_mo1": 4,
        "sale_date1": "2019-04-15",
        "tax_amount": 9170,
        "homestead_exemption": 50000,
        "subdivision": "CORAL RIDGE",
        "legal_desc": "CORAL RIDGE PB 55-12 LOT 8 BLK 3"
    },
    {
        "parcel_id": "544279350150",
        "phy_addr1": "100 LAS OLAS BLVD",
        "phy_city": "FORT LAUDERDALE",
        "phy_state": "FL",
        "phy_zipcd": "33301",
        "own_name": "LAS OLAS TOWER LP",
        "own_addr1": "100 LAS OLAS BLVD PH",
        "own_city": "FORT LAUDERDALE",
        "own_state": "FL",
        "own_zipcd": "33301",
        "dor_uc": "039",
        "property_type": "Commercial",
        "property_use_desc": "Hotel/Motel",
        "jv": 95000000,
        "av_sd": 85500000,
        "tv_sd": 80750000,
        "lnd_val": 35000000,
        "bldg_val": 60000000,
        "tot_lvg_area": 380000,
        "lnd_sqfoot": 65340,
        "act_yr_blt": 2016,
        "eff_yr_blt": 2016,
        "no_res_unts": 250,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_prc1": 98000000,
        "sale_yr1": "2018",
        "sale_mo1": 9,
        "sale_date1": "2018-09-30",
        "tax_amount": 1615000,
        "homestead_exemption": 0,
        "subdivision": "LAS OLAS CENTER",
        "legal_desc": "LAS OLAS CENTER PB 177-22 LOT 1"
    },
    {
        "parcel_id": "554280460180",
        "phy_addr1": "8500 GRIFFIN RD",
        "phy_city": "COOPER CITY",
        "phy_state": "FL",
        "phy_zipcd": "33328",
        "own_name": "SMITH JOHN & SUSAN",
        "own_addr1": "8500 GRIFFIN RD",
        "own_city": "COOPER CITY",
        "own_state": "FL",
        "own_zipcd": "33328",
        "dor_uc": "001",
        "property_type": "Residential",
        "property_use_desc": "Single Family",
        "jv": 925000,
        "av_sd": 832500,
        "tv_sd": 782500,
        "lnd_val": 425000,
        "bldg_val": 500000,
        "tot_lvg_area": 3450,
        "lnd_sqfoot": 14500,
        "act_yr_blt": 2008,
        "eff_yr_blt": 2008,
        "no_res_unts": 1,
        "bedrooms": 5,
        "bathrooms": 3,
        "sale_prc1": 950000,
        "sale_yr1": "2021",
        "sale_mo1": 7,
        "sale_date1": "2021-07-20",
        "tax_amount": 15650,
        "homestead_exemption": 50000,
        "subdivision": "GRIFFIN ESTATES",
        "legal_desc": "GRIFFIN ESTATES PB 142-78 LOT 22 BLK 5"
    },
    {
        "parcel_id": "564291570210",
        "phy_addr1": "1850 SAWGRASS MILLS CIR",
        "phy_city": "SUNRISE",
        "phy_state": "FL",
        "phy_zipcd": "33323",
        "own_name": "SAWGRASS RETAIL LLC",
        "own_addr1": "1850 SAWGRASS MILLS CIR",
        "own_city": "SUNRISE",
        "own_state": "FL",
        "own_zipcd": "33323",
        "dor_uc": "011",
        "property_type": "Commercial",
        "property_use_desc": "Regional Mall",
        "jv": 485000000,
        "av_sd": 436500000,
        "tv_sd": 412000000,
        "lnd_val": 185000000,
        "bldg_val": 300000000,
        "tot_lvg_area": 2350000,
        "lnd_sqfoot": 3920400,
        "act_yr_blt": 1990,
        "eff_yr_blt": 2015,
        "no_res_unts": 0,
        "bedrooms": 0,
        "bathrooms": 0,
        "sale_prc1": 490000000,
        "sale_yr1": "2017",
        "sale_mo1": 5,
        "sale_date1": "2017-05-10",
        "tax_amount": 8240000,
        "homestead_exemption": 0,
        "subdivision": "SAWGRASS MILLS",
        "legal_desc": "SAWGRASS MILLS PB 99-45 ALL"
    }
]

print(f"Loading {len(sample_properties)} properties with complete data...")

# Try to access the florida_parcels table directly
successful_inserts = 0
for prop in sample_properties:
    try:
        # Check if property exists
        existing = supabase.table('florida_parcels').select('id').eq('parcel_id', prop['parcel_id']).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table('florida_parcels').update(prop).eq('parcel_id', prop['parcel_id']).execute()
            print(f"✓ Updated: {prop['phy_addr1']}, {prop['phy_city']} - ${prop['jv']:,.0f}")
            successful_inserts += 1
        else:
            # Insert new
            result = supabase.table('florida_parcels').insert(prop).execute()
            print(f"✓ Inserted: {prop['phy_addr1']}, {prop['phy_city']} - ${prop['jv']:,.0f}")
            successful_inserts += 1
            
    except Exception as e:
        error_msg = str(e)
        if 'relation "public.florida_parcels" does not exist' in error_msg:
            print(f"\n⚠ Table 'florida_parcels' doesn't exist. Trying 'properties' table instead...")
            break
        elif 'row-level security' in error_msg.lower():
            print(f"\n⚠ RLS is blocking access. Please disable RLS for the florida_parcels table in Supabase dashboard.")
            print("  Go to: Table Editor > florida_parcels > Policies > Disable RLS")
            break
        else:
            print(f"✗ Error with {prop['parcel_id']}: {error_msg[:100]}")

# If florida_parcels doesn't work, try properties table with mapped fields
if successful_inserts == 0:
    print("\n" + "=" * 60)
    print("Attempting to use 'properties' table with field mapping...")
    
    for prop in sample_properties[:3]:  # Try first 3 properties
        mapped_prop = {
            "parcel_id": prop["parcel_id"],
            "owner_name": prop["own_name"],
            "property_address": prop["phy_addr1"],
            "city": prop["phy_city"],
            "state": prop["phy_state"],
            "zip_code": prop["phy_zipcd"],
            "property_type": prop["property_use_desc"],
            "year_built": prop["act_yr_blt"],
            "total_sqft": prop["tot_lvg_area"],
            "lot_size_sqft": prop["lnd_sqfoot"],
            "bedrooms": prop["bedrooms"],
            "bathrooms": prop["bathrooms"],
            "assessed_value": float(prop["av_sd"]) if prop["av_sd"] else 0,
            "market_value": float(prop["jv"]) if prop["jv"] else 0,
            "last_sale_date": prop["sale_date1"],
            "last_sale_price": float(prop["sale_prc1"]) if prop["sale_prc1"] else 0
        }
        
        try:
            # Check if property exists
            existing = supabase.table('properties').select('id').eq('parcel_id', mapped_prop['parcel_id']).execute()
            
            if existing.data:
                # Update existing
                result = supabase.table('properties').update(mapped_prop).eq('parcel_id', mapped_prop['parcel_id']).execute()
                print(f"✓ Updated in properties table: {mapped_prop['property_address']}, {mapped_prop['city']}")
            else:
                # Insert new
                result = supabase.table('properties').insert(mapped_prop).execute()
                print(f"✓ Inserted in properties table: {mapped_prop['property_address']}, {mapped_prop['city']}")
        except Exception as e:
            print(f"✗ Error: {str(e)[:100]}")

print("\n" + "=" * 60)
print("Data loading complete!")
print("\nTo view this data:")
print("1. Go to http://localhost:5173/properties")
print("2. Search for cities: FORT LAUDERDALE, HOLLYWOOD, MIAMI, DAVIE, CORAL SPRINGS")
print("3. Click on any property to see the full profile with all data fields populated")
print("\nIf you see RLS errors, please:")
print("1. Go to your Supabase dashboard")
print("2. Navigate to Table Editor > florida_parcels (or properties)")
print("3. Click on 'Policies' tab")
print("4. Disable RLS or add a policy allowing public read access")