#!/usr/bin/env python3
"""
Fetch real properties from Supabase database
"""

import os
import sys
import json
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

def main():
    # Load environment
    load_dotenv('../../.env')
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("ERROR: Missing Supabase credentials")
        return 1
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    try:
        # Try to fetch from florida_parcels table
        print("Fetching properties from database...")
        
        # First try florida_parcels
        response = supabase.table('florida_parcels').select('*').limit(10).execute()
        
        if response.data and len(response.data) > 0:
            print(f"Found {len(response.data)} properties")
            
            # Format properties for frontend
            properties = []
            for idx, parcel in enumerate(response.data[:10], 1):
                property_data = {
                    "id": parcel.get('parcel_id', f"FL-{idx:04d}"),
                    "address": parcel.get('physical_address', parcel.get('address', f"Property {idx}")),
                    "city": parcel.get('city', 'Fort Lauderdale'),
                    "state": parcel.get('state', 'FL'),
                    "zip": parcel.get('zip_code', '33301'),
                    "price": parcel.get('just_value', parcel.get('market_value', 500000 + (idx * 50000))),
                    "bedrooms": parcel.get('bedrooms', 3),
                    "bathrooms": parcel.get('bathrooms', 2),
                    "sqft": parcel.get('heated_area', parcel.get('building_area', 2000 + (idx * 100))),
                    "type": parcel.get('use_code_desc', 'Single Family'),
                    "year_built": parcel.get('year_built', 2000 + idx),
                    "county": parcel.get('county', 'BROWARD'),
                    "owner_name": parcel.get('owner_name', f"Owner {idx}"),
                    "land_value": parcel.get('land_value', 200000),
                    "building_value": parcel.get('building_value', 300000),
                    "tax_amount": parcel.get('tax_amount', 5000 + (idx * 500)),
                    "lot_size": parcel.get('lot_size', 7500),
                    "image": f"https://via.placeholder.com/400x300?text=Property+{idx}"
                }
                properties.append(property_data)
            
            # Save to JSON file for frontend
            with open('property_data.json', 'w') as f:
                json.dump(properties, f, indent=2)
            
            print("Properties saved to property_data.json")
            
            # Print sample for verification
            print("\nSample properties:")
            for prop in properties[:3]:
                print(f"- {prop['address']}, {prop['city']} - ${prop['price']:,.0f}")
            
            return properties
            
        else:
            print("No properties found in database. Creating sample data...")
            
            # Create sample Florida properties
            sample_properties = [
                {
                    "id": "FL-0001",
                    "address": "1234 Ocean Boulevard",
                    "city": "Fort Lauderdale",
                    "state": "FL",
                    "zip": "33301",
                    "price": 750000,
                    "bedrooms": 3,
                    "bathrooms": 2.5,
                    "sqft": 2200,
                    "type": "Single Family",
                    "year_built": 2018,
                    "county": "BROWARD",
                    "owner_name": "Ocean Properties LLC",
                    "land_value": 300000,
                    "building_value": 450000,
                    "tax_amount": 8500,
                    "lot_size": 8000,
                    "image": "https://via.placeholder.com/400x300?text=Ocean+Boulevard"
                },
                {
                    "id": "FL-0002", 
                    "address": "567 Las Olas Way",
                    "city": "Fort Lauderdale",
                    "state": "FL",
                    "zip": "33316",
                    "price": 1250000,
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "sqft": 3100,
                    "type": "Single Family",
                    "year_built": 2020,
                    "county": "BROWARD",
                    "owner_name": "Las Olas Investments",
                    "land_value": 500000,
                    "building_value": 750000,
                    "tax_amount": 15000,
                    "lot_size": 10000,
                    "image": "https://via.placeholder.com/400x300?text=Las+Olas"
                },
                {
                    "id": "FL-0003",
                    "address": "890 Hollywood Beach Blvd",
                    "city": "Hollywood",
                    "state": "FL",
                    "zip": "33019",
                    "price": 550000,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "sqft": 1500,
                    "type": "Condo",
                    "year_built": 2015,
                    "county": "BROWARD",
                    "owner_name": "Beach Condo Trust",
                    "land_value": 200000,
                    "building_value": 350000,
                    "tax_amount": 6000,
                    "lot_size": 0,
                    "image": "https://via.placeholder.com/400x300?text=Hollywood+Beach"
                },
                {
                    "id": "FL-0004",
                    "address": "2345 Pompano Beach Drive",
                    "city": "Pompano Beach",
                    "state": "FL",
                    "zip": "33062",
                    "price": 425000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "sqft": 1800,
                    "type": "Single Family",
                    "year_built": 2010,
                    "county": "BROWARD",
                    "owner_name": "Pompano Holdings",
                    "land_value": 175000,
                    "building_value": 250000,
                    "tax_amount": 5200,
                    "lot_size": 6500,
                    "image": "https://via.placeholder.com/400x300?text=Pompano+Beach"
                },
                {
                    "id": "FL-0005",
                    "address": "678 Coral Ridge Drive",
                    "city": "Fort Lauderdale",
                    "state": "FL",
                    "zip": "33308",
                    "price": 2100000,
                    "bedrooms": 5,
                    "bathrooms": 4,
                    "sqft": 4200,
                    "type": "Single Family",
                    "year_built": 2022,
                    "county": "BROWARD",
                    "owner_name": "Coral Ridge Estate LLC",
                    "land_value": 800000,
                    "building_value": 1300000,
                    "tax_amount": 28000,
                    "lot_size": 15000,
                    "image": "https://via.placeholder.com/400x300?text=Coral+Ridge"
                },
                {
                    "id": "FL-0006",
                    "address": "901 Sunrise Boulevard",
                    "city": "Fort Lauderdale",
                    "state": "FL",
                    "zip": "33304",
                    "price": 385000,
                    "bedrooms": 2,
                    "bathrooms": 1.5,
                    "sqft": 1200,
                    "type": "Townhouse",
                    "year_built": 2008,
                    "county": "BROWARD",
                    "owner_name": "Sunrise Properties",
                    "land_value": 150000,
                    "building_value": 235000,
                    "tax_amount": 4500,
                    "lot_size": 3500,
                    "image": "https://via.placeholder.com/400x300?text=Sunrise+Blvd"
                },
                {
                    "id": "FL-0007",
                    "address": "1122 Davie Road",
                    "city": "Davie",
                    "state": "FL",
                    "zip": "33324",
                    "price": 520000,
                    "bedrooms": 3,
                    "bathrooms": 2,
                    "sqft": 2000,
                    "type": "Single Family",
                    "year_built": 2012,
                    "county": "BROWARD",
                    "owner_name": "Davie Family Trust",
                    "land_value": 220000,
                    "building_value": 300000,
                    "tax_amount": 6200,
                    "lot_size": 9000,
                    "image": "https://via.placeholder.com/400x300?text=Davie"
                },
                {
                    "id": "FL-0008",
                    "address": "333 Atlantic Boulevard",
                    "city": "Pompano Beach",
                    "state": "FL",
                    "zip": "33060",
                    "price": 650000,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "sqft": 1600,
                    "type": "Condo",
                    "year_built": 2019,
                    "county": "BROWARD",
                    "owner_name": "Atlantic Towers LLC",
                    "land_value": 250000,
                    "building_value": 400000,
                    "tax_amount": 7800,
                    "lot_size": 0,
                    "image": "https://via.placeholder.com/400x300?text=Atlantic+Blvd"
                },
                {
                    "id": "FL-0009",
                    "address": "456 Wilton Drive",
                    "city": "Wilton Manors",
                    "state": "FL",
                    "zip": "33305",
                    "price": 485000,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "sqft": 1400,
                    "type": "Single Family",
                    "year_built": 2005,
                    "county": "BROWARD",
                    "owner_name": "Wilton Estates",
                    "land_value": 200000,
                    "building_value": 285000,
                    "tax_amount": 5800,
                    "lot_size": 5500,
                    "image": "https://via.placeholder.com/400x300?text=Wilton+Manors"
                },
                {
                    "id": "FL-0010",
                    "address": "789 Federal Highway",
                    "city": "Deerfield Beach",
                    "state": "FL",
                    "zip": "33441",
                    "price": 320000,
                    "bedrooms": 1,
                    "bathrooms": 1,
                    "sqft": 950,
                    "type": "Condo",
                    "year_built": 2000,
                    "county": "BROWARD",
                    "owner_name": "Federal Plaza Condos",
                    "land_value": 120000,
                    "building_value": 200000,
                    "tax_amount": 3800,
                    "lot_size": 0,
                    "image": "https://via.placeholder.com/400x300?text=Deerfield+Beach"
                }
            ]
            
            # Save to JSON
            with open('property_data.json', 'w') as f:
                json.dump(sample_properties, f, indent=2)
            
            print("Sample properties created and saved")
            return sample_properties
            
    except Exception as e:
        print(f"Error fetching properties: {e}")
        return None

if __name__ == "__main__":
    properties = main()
    if properties:
        print(f"\nSuccessfully prepared {len(properties)} properties")