#!/usr/bin/env python3
"""
Complete analysis of ALL property_use values in the florida_parcels table.
Samples across the full 7.3M record range to find all property types.
"""

import os
import json
from supabase import create_client, Client

# Set up Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Standard Florida Department of Revenue Property Use Codes
FLORIDA_PROPERTY_USE_CODES = {
    0: "Vacant Residential",
    1: "Single Family Residential",
    2: "Mobile Homes",
    3: "Multi-Family 2-9 Units",
    4: "Condominiums",
    5: "Cooperatives",
    6: "Retirement Homes",
    7: "Miscellaneous Residential",
    8: "Multi-Family 10+ Units",
    9: "Undefined Residential",
    10: "Vacant Commercial",
    11: "Stores, One Story",
    12: "Mixed Use/Store & Office",
    13: "Department Stores",
    14: "Supermarkets",
    15: "Regional Shopping Centers",
    16: "Community Shopping Centers",
    17: "Office Buildings, One Story",
    18: "Office Buildings, Multi-Story",
    19: "Professional Services Buildings",
    20: "Airports, Terminals, Hangars",
    21: "Restaurants, Cafeterias",
    22: "Drive-In Restaurants",
    23: "Financial Institutions",
    24: "Insurance Company Offices",
    25: "Repair Service Shops",
    26: "Service Stations",
    27: "Auto Sales, Rent, Wash",
    28: "Parking Lots",
    29: "Wholesale Outlets",
    30: "Florist, Greenhouses",
    31: "Drive-In Theaters",
    32: "Enclosed Theaters, Auditoriums",
    33: "Night Clubs, Bars",
    34: "Bowling Alleys, Billiards",
    35: "Tourist Attractions",
    36: "Camps",
    37: "Race Tracks",
    38: "Golf Courses, Driving Ranges",
    39: "Miscellaneous Commercial",
    40: "Vacant Industrial",
    41: "Light Manufacturing",
    42: "Heavy Industrial",
    43: "Railroad Property",
    44: "Telephone Company Property",
    45: "Telegraph Company Property",
    46: "Electric Company Property",
    47: "Gas Company Property",
    48: "Water Company Property",
    49: "Sanitary Landfills",
    50: "Improved Industrial",
    80: "Crop & Pasture Land",
    81: "Timberland",
    82: "Agricultural Improvements",
    83: "Poultry, Bees, Tropical Fish",
    84: "Dairies",
    85: "Livestock",
    86: "Orchards, Groves, Vineyards",
    87: "Ornamentals, Miscellaneous Agriculture",
    88: "Vacant Agricultural",
    89: "Undefined Agricultural",
    90: "Vacant Government Owned",
    91: "Military",
    92: "Forest, Parks, Recreational",
    93: "Public County Schools",
    94: "State Universities, Community Colleges",
    95: "Hospitals",
    96: "Counties",
    97: "State Government",
    98: "Federal Government",
    99: "Municipalities"
}

def categorize_property_use(code_str):
    """Categorize property use code based on Florida DOR standards."""
    try:
        code_int = int(code_str)
    except (ValueError, TypeError):
        return "Other"

    if 0 <= code_int <= 9:
        return "Residential"
    elif 10 <= code_int <= 39:
        return "Commercial"
    elif 40 <= code_int <= 69:
        return "Industrial"
    elif 70 <= code_int <= 79:
        return "Institutional"
    elif 80 <= code_int <= 89:
        return "Agricultural"
    elif 90 <= code_int <= 99:
        return "Government/Exempt"
    else:
        return "Other"

def main():
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase")

        print("\nCOMPLETE PROPERTY USE ANALYSIS")
        print("Analyzing all property_use values across 7.3M records")
        print("=" * 60)

        # Sample systematically across the full range (7.3M records)
        total_records = 7312641
        sample_points = 100  # Take samples from 100 different points
        sample_size = 1000   # Get 1000 records from each point

        # Calculate evenly spaced offsets
        offsets = [int(i * (total_records / sample_points)) for i in range(sample_points)]

        all_property_use_counts = {}
        total_sampled = 0

        print(f"Sampling {sample_size} records from {sample_points} evenly distributed points...")
        print("This will give us a comprehensive view of all property types.")

        for i, offset in enumerate(offsets):
            if i % 10 == 0:  # Progress update every 10 samples
                print(f"Progress: {i+1}/{sample_points} samples processed...")

            try:
                result = supabase.table('florida_parcels').select('property_use').range(offset, offset + sample_size - 1).execute()

                if result.data:
                    for row in result.data:
                        prop_use = row['property_use']
                        if prop_use is not None:
                            if prop_use not in all_property_use_counts:
                                all_property_use_counts[prop_use] = 0
                            all_property_use_counts[prop_use] += 1
                            total_sampled += 1

            except Exception as e:
                print(f"  Error at offset {offset:,}: {e}")
                continue

        if all_property_use_counts:
            print(f"\nCOMPLETE ANALYSIS RESULTS:")
            print(f"Total properties sampled: {total_sampled:,}")
            print(f"Distinct property_use values found: {len(all_property_use_counts)}")
            print("=" * 120)
            print(f"{'Code':<6} {'Count':<8} {'%':<8} {'Standard Description':<55} {'Category':<15}")
            print("=" * 120)

            # Sort codes numerically
            sorted_codes = sorted(all_property_use_counts.keys(), key=lambda x: int(x) if x.isdigit() else 999)

            # Categorize the codes
            categories = {
                'Residential': [],
                'Commercial': [],
                'Industrial': [],
                'Institutional': [],
                'Agricultural': [],
                'Government/Exempt': [],
                'Other': []
            }

            property_use_data = {}

            for code_str in sorted_codes:
                count = all_property_use_counts[code_str]
                percentage = (count / total_sampled) * 100

                # Get standard description
                try:
                    code_int = int(code_str)
                    description = FLORIDA_PROPERTY_USE_CODES.get(code_int, f"Unknown Code {code_str}")
                except ValueError:
                    description = f"Invalid Code {code_str}"

                # Categorize
                category = categorize_property_use(code_str)
                categories[category].append(code_str)

                print(f"{code_str:<6} {count:<8} {percentage:<8.2f} {description:<55} {category:<15}")

                property_use_data[code_str] = {
                    'count': count,
                    'percentage': percentage,
                    'description': description,
                    'category': category
                }

            # Print category summaries
            print("\nCATEGORY SUMMARIES:")
            print("=" * 80)

            for category, codes in categories.items():
                if codes:
                    total_count = sum(all_property_use_counts[code] for code in codes)
                    percentage = (total_count / total_sampled) * 100
                    print(f"{category:<20}: {len(codes):>3} codes, {total_count:>8,} properties ({percentage:>6.2f}%)")

                    # Show codes in category
                    if codes:
                        sorted_category_codes = sorted(codes, key=lambda x: all_property_use_counts[x], reverse=True)
                        print(f"  Codes: {', '.join(sorted_category_codes)}")
                    print()

            # Generate frontend mappings
            print("FRONTEND MAPPINGS FOR PROPERTY FILTERS:")
            print("=" * 60)
            print("Copy these exact arrays to fix the frontend filter functionality:")
            print()

            frontend_mappings = {}
            for category, codes in categories.items():
                if codes:
                    # Convert string codes to integers for frontend
                    int_codes = []
                    for code_str in codes:
                        try:
                            int_codes.append(int(code_str))
                        except ValueError:
                            pass  # Skip invalid codes
                    int_codes.sort()

                    if int_codes:  # Only include categories with valid integer codes
                        frontend_mappings[category.upper().replace('/', '_')] = int_codes
                        print(f"{category.upper().replace('/', '_')}: {int_codes}")

            # Save comprehensive results
            output_file = "complete_property_use_analysis.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'analysis_date': '2025-09-26',
                    'total_database_records': total_records,
                    'total_properties_sampled': total_sampled,
                    'sampling_points': sample_points,
                    'sample_size_per_point': sample_size,
                    'total_distinct_codes': len(all_property_use_counts),
                    'property_use_data': property_use_data,
                    'category_summaries': {
                        category: {
                            'codes': codes,
                            'total_properties': sum(all_property_use_counts[code] for code in codes),
                            'percentage': (sum(all_property_use_counts[code] for code in codes) / total_sampled) * 100 if codes else 0
                        }
                        for category, codes in categories.items() if codes
                    },
                    'frontend_mappings': frontend_mappings,
                    'florida_dor_standards': FLORIDA_PROPERTY_USE_CODES
                }, f, indent=2)

            print(f"\nDetailed results saved to: {output_file}")

            # Show critical insights for fixing filters
            print("\nCRITICAL INSIGHTS FOR FIXING FRONTEND FILTERS:")
            print("=" * 60)

            print("\nCURRENT ISSUE:")
            print("Frontend is sending property_use_values like [10,11,16,17,19] for Commercial")
            print("but the database contains different codes than expected.")

            print("\nACTUAL CODES IN DATABASE:")
            for category, codes in frontend_mappings.items():
                if codes:
                    print(f"{category}: {codes}")

            print("\nRECOMMENDATION:")
            print("Update the frontend filter mappings to use the ACTUAL codes found in the database.")
            print("The current filters are probably returning 0 results because they're looking")
            print("for property_use codes that don't exist in your specific dataset.")

        else:
            print("No property_use data found in database")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()