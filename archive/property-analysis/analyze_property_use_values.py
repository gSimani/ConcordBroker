#!/usr/bin/env python3
"""
Analyze property_use values in the florida_parcels table to understand
what values exist and fix the property filter mappings.
"""

import os
import json
from supabase import create_client, Client

# Set up Supabase connection
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1Njk1Njk1OCwiZXhwIjoyMDcyNTMyOTU4fQ.fbCYcTFxLaMC_g4P8IrQoHWbQbPr_t9eaxYD_9yS3u0"

def main():
    try:
        # Create Supabase client
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("Connected to Supabase")

        # Query to get all distinct property_use values with counts and descriptions
        print("\nAnalyzing property_use values in florida_parcels table...")

        # Get a sample of property_use values to understand the data structure
        print("Getting sample of property_use values...")

        # First, let's get a sample of all property fields to understand the structure
        result = supabase.table('florida_parcels').select('*').limit(100).execute()

        if result.data:
            print("Sample record structure:")
            sample_record = result.data[0]
            for key, value in sample_record.items():
                if 'use' in key.lower() or 'type' in key.lower() or 'class' in key.lower():
                    print(f"  {key}: {value}")
            print()

        # Get distinct property_use values with a larger limit
        result = supabase.table('florida_parcels').select('property_use, property_use_desc, land_use_code').limit(50000).execute()

        if not result.data:
            print("No data found in florida_parcels table")
            return

        # Process the data to get counts and descriptions
        property_use_counts = {}
        property_use_descriptions = {}

        for row in result.data:
            prop_use = row.get('property_use')

            # Try multiple description fields
            prop_use_desc = (
                row.get('property_use_desc') or
                row.get('land_use_code') or
                f"Property Use Code {prop_use}"
            )

            if prop_use is not None:
                if prop_use not in property_use_counts:
                    property_use_counts[prop_use] = 0
                property_use_counts[prop_use] += 1

                if prop_use_desc and prop_use not in property_use_descriptions:
                    property_use_descriptions[prop_use] = prop_use_desc

        # Sort property use codes
        sorted_codes = sorted(property_use_counts.keys(), key=lambda x: int(x) if str(x).isdigit() else 999)

        # Create result data structure similar to SQL query
        result_data = []
        for code in sorted_codes:
            result_data.append({
                'property_use': str(code),
                'count': property_use_counts[code],
                'sample_desc': property_use_descriptions.get(code, 'No description')
            })

        if result_data:
            print(f"\nFound {len(result_data)} distinct property_use values:")
            print("=" * 80)
            print(f"{'Code':<6} {'Count':<10} {'Description':<60}")
            print("=" * 80)

            # Store data for analysis
            property_use_data = {}

            for row in result_data:
                code = row['property_use']
                count = row['count']
                desc = row['sample_desc'] or 'No description'

                print(f"{code:<6} {count:<10} {desc:<60}")
                property_use_data[code] = {
                    'count': count,
                    'description': desc
                }

            # Analyze and categorize the codes
            print("\nPROPERTY TYPE CATEGORIZATION:")
            print("=" * 50)

            # Common Florida property use code patterns
            residential_codes = []
            commercial_codes = []
            industrial_codes = []
            agricultural_codes = []
            vacant_codes = []
            other_codes = []

            for code, data in property_use_data.items():
                desc = data['description'].lower()
                code_int = int(code) if code.isdigit() else 0

                # Categorize based on common Florida DOR patterns
                if any(word in desc for word in ['single family', 'residential', 'condo', 'townhouse', 'mobile home', 'apartment']):
                    residential_codes.append(code)
                elif any(word in desc for word in ['commercial', 'office', 'retail', 'store', 'restaurant', 'hotel', 'warehouse']):
                    commercial_codes.append(code)
                elif any(word in desc for word in ['industrial', 'manufacturing', 'factory']):
                    industrial_codes.append(code)
                elif any(word in desc for word in ['agricultural', 'farm', 'grove', 'pasture', 'timber']):
                    agricultural_codes.append(code)
                elif any(word in desc for word in ['vacant', 'undeveloped', 'acreage']):
                    vacant_codes.append(code)
                else:
                    other_codes.append(code)

            # Print categorization
            categories = {
                'Residential': residential_codes,
                'Commercial': commercial_codes,
                'Industrial': industrial_codes,
                'Agricultural': agricultural_codes,
                'Vacant Land': vacant_codes,
                'Other': other_codes
            }

            for category, codes in categories.items():
                if codes:
                    print(f"\n{category}:")
                    for code in codes[:10]:  # Show first 10 codes
                        desc = property_use_data[code]['description']
                        count = property_use_data[code]['count']
                        print(f"  {code}: {desc} ({count:,} properties)")
                    if len(codes) > 10:
                        print(f"  ... and {len(codes) - 10} more codes")

            # Generate correct mappings for frontend
            print("\nRECOMMENDED FRONTEND MAPPINGS:")
            print("=" * 50)
            print("Based on the analysis, here are the recommended property_use_values for each category:")
            print()

            for category, codes in categories.items():
                if codes:
                    codes_str = ', '.join(sorted(codes, key=lambda x: int(x) if x.isdigit() else 999))
                    print(f"{category.upper().replace(' ', '_')}: [{codes_str}]")

            # Save detailed results to file
            output_file = "property_use_analysis_results.json"
            with open(output_file, 'w') as f:
                json.dump({
                    'total_distinct_values': len(property_use_data),
                    'property_use_data': property_use_data,
                    'categorization': categories,
                    'recommended_mappings': {
                        category.upper().replace(' ', '_'): codes
                        for category, codes in categories.items() if codes
                    }
                }, f, indent=2)

            print(f"\nDetailed results saved to: {output_file}")

        else:
            print("No data returned from query")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()