#!/usr/bin/env python3
"""
Comprehensive analysis of property_use values in the florida_parcels table.
Uses Florida DOR standard property use codes to categorize properties.
"""

import os
import json
from supabase import create_client, Client

# Set up Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

# Standard Florida Department of Revenue Property Use Codes
# Reference: https://floridarevenue.com/property/dataportal/Pages/default.aspx
FLORIDA_PROPERTY_USE_CODES = {
    # RESIDENTIAL (00-99)
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

    # COMMERCIAL (10-39)
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

    # INDUSTRIAL (40-69)
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
    51: "Special Machinery",
    52: "Oil, Gas, Mineral Rights",
    53: "Quarries, Land & Improvements",
    54: "Extractive Industries",
    55: "Mineral Processing",
    56: "Fisheries",
    57: "Marine Service Commercial",
    58: "Marinas",
    59: "Miscellaneous Industrial",

    # AGRICULTURAL (70-89)
    70: "Vacant Institutional",
    71: "Churches",
    72: "Private Schools & Colleges",
    73: "Privately Owned Hospitals",
    74: "Homes for the Aged",
    75: "Orphanages",
    76: "Mortuaries",
    77: "Clubs, Lodges, Union Halls",
    78: "Sanitariums",
    79: "Miscellaneous Institutional",
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

    # GOVERNMENT/EXEMPT (90-99)
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

def categorize_property_use(code):
    """Categorize property use code based on Florida DOR standards."""
    code_int = int(code) if str(code).isdigit() else 0

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

        print("\nAnalyzing property_use values in florida_parcels table...")
        print("Getting comprehensive sample of property_use values...")

        # Get ALL distinct property_use values by processing data in chunks
        all_property_use_counts = {}
        offset = 0
        chunk_size = 50000
        total_processed = 0

        while True:
            print(f"Processing chunk {offset//chunk_size + 1}...")

            result = supabase.table('florida_parcels').select('property_use').range(offset, offset + chunk_size - 1).execute()

            if not result.data:
                break

            chunk_counts = {}
            for row in result.data:
                prop_use = row.get('property_use')
                if prop_use is not None:
                    if prop_use not in chunk_counts:
                        chunk_counts[prop_use] = 0
                    chunk_counts[prop_use] += 1
                    total_processed += 1

            # Merge chunk counts with overall counts
            for code, count in chunk_counts.items():
                if code not in all_property_use_counts:
                    all_property_use_counts[code] = 0
                all_property_use_counts[code] += count

            print(f"  Found {len(chunk_counts)} distinct codes in this chunk")
            print(f"  Total processed: {total_processed:,} properties")
            print(f"  Running total of distinct codes: {len(all_property_use_counts)}")

            # If we got less than the chunk size, we're done
            if len(result.data) < chunk_size:
                break

            offset += chunk_size

            # Safety break after processing reasonable amount
            if offset > 500000:  # Process up to 500k records
                print("Reached processing limit, stopping...")
                break

        if all_property_use_counts:
            print(f"\nCOMPREHENSIVE ANALYSIS RESULTS:")
            print(f"Total properties analyzed: {total_processed:,}")
            print(f"Distinct property_use values found: {len(all_property_use_counts)}")
            print("=" * 120)
            print(f"{'Code':<6} {'Count':<10} {'%':<8} {'Standard Description':<60} {'Category':<15}")
            print("=" * 120)

            # Sort codes numerically
            sorted_codes = sorted(all_property_use_counts.keys(), key=lambda x: int(x) if str(x).isdigit() else 999)

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

            for code in sorted_codes:
                count = all_property_use_counts[code]
                percentage = (count / total_processed) * 100

                # Get standard description
                description = FLORIDA_PROPERTY_USE_CODES.get(int(code) if str(code).isdigit() else -1, f"Unknown Code {code}")

                # Categorize
                category = categorize_property_use(code)
                categories[category].append(str(code))

                print(f"{code:<6} {count:<10} {percentage:<8.2f} {description:<60} {category:<15}")

                property_use_data[str(code)] = {
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
                    total_count = sum(all_property_use_counts.get(int(code), 0) for code in codes if str(code).isdigit())
                    percentage = (total_count / total_processed) * 100
                    print(f"{category:<20}: {len(codes):>3} codes, {total_count:>8,} properties ({percentage:>6.2f}%)")

                    # Show most common codes in category
                    if codes:
                        sorted_category_codes = sorted(codes, key=lambda x: all_property_use_counts.get(int(x), 0) if str(x).isdigit() else 0, reverse=True)
                        top_codes = sorted_category_codes[:5]
                        print(f"  Top codes: {', '.join(top_codes)}")
                    print()

            # Generate frontend mappings
            print("\nRECOMMENDED FRONTEND MAPPINGS:")
            print("=" * 60)

            frontend_mappings = {}
            for category, codes in categories.items():
                if codes:
                    # Convert string codes back to integers for frontend
                    int_codes = [int(code) for code in codes if code.isdigit()]
                    int_codes.sort()
                    frontend_mappings[category.upper().replace('/', '_')] = int_codes
                    print(f"{category.upper().replace('/', '_')}: {int_codes}")

            # Save comprehensive results
            output_file = "comprehensive_property_use_analysis.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'total_properties_analyzed': total_processed,
                    'total_distinct_codes': len(all_property_use_counts),
                    'property_use_data': property_use_data,
                    'category_summaries': {
                        category: {
                            'codes': codes,
                            'total_properties': sum(all_property_use_counts.get(int(code), 0) for code in codes if str(code).isdigit()),
                            'percentage': (sum(all_property_use_counts.get(int(code), 0) for code in codes if str(code).isdigit()) / total_processed) * 100 if codes else 0
                        }
                        for category, codes in categories.items() if codes
                    },
                    'frontend_mappings': frontend_mappings,
                    'code_standards_reference': FLORIDA_PROPERTY_USE_CODES
                }, f, indent=2)

            print(f"\nDetailed results saved to: {output_file}")

            # Show key insights
            print("\nKEY INSIGHTS:")
            print("=" * 40)
            print(f"• Most common property type: Code {max(all_property_use_counts, key=all_property_use_counts.get)} ({FLORIDA_PROPERTY_USE_CODES.get(int(max(all_property_use_counts, key=all_property_use_counts.get)), 'Unknown')})")
            print(f"• Total residential properties: {sum(all_property_use_counts.get(int(code), 0) for code in categories['Residential'] if str(code).isdigit()):,}")
            print(f"• Total commercial properties: {sum(all_property_use_counts.get(int(code), 0) for code in categories['Commercial'] if str(code).isdigit()):,}")
            print(f"• Data coverage: {total_processed:,} properties analyzed")

        else:
            print("No property_use data found in database")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()