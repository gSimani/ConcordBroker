#!/usr/bin/env python3
"""
Analyze Florida Property Data for Exemption Fields
This script examines what exemption fields are available in the florida_parcels table
"""

import os
from supabase import create_client, Client
from typing import Dict, Any, List

def analyze_exemption_fields():
    """Analyze exemption fields in florida_parcels table"""

    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co')
    supabase_anon_key = os.getenv('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A')

    supabase: Client = create_client(supabase_url, supabase_anon_key)

    print("Florida Property Exemption Field Analysis")
    print("=" * 60)

    # Get a sample of properties to analyze available fields
    try:
        # First, get schema information
        print("\nChecking table schema for exemption-related fields...")

        # Get a few sample records to see what fields are available
        response = supabase.table('florida_parcels').select('*').limit(1).execute()

        if response.data and len(response.data) > 0:
            sample_record = response.data[0]
            print(f"Found sample record with {len(sample_record.keys())} fields")

            # Look for exemption-related fields
            exemption_fields = []
            tax_fields = []
            homestead_fields = []

            for field_name in sample_record.keys():
                field_lower = field_name.lower()

                # Exemption fields
                if any(keyword in field_lower for keyword in ['exempt', 'xmpt', 'exmpt']):
                    exemption_fields.append(field_name)

                # Tax fields
                if any(keyword in field_lower for keyword in ['tax', 'homestead', 'hs_']):
                    tax_fields.append(field_name)

                # Homestead fields
                if any(keyword in field_lower for keyword in ['homestead', 'hs_', 'primary', 'residence']):
                    homestead_fields.append(field_name)

            print(f"\nPotential Homestead/Exemption Fields Found:")
            print(f"   Exemption Fields: {exemption_fields}")
            print(f"   Tax Fields: {tax_fields}")
            print(f"   Homestead Fields: {homestead_fields}")

            # Sample specific property to check actual values
            print(f"\nAnalyzing specific property: 3040190012860")

            property_response = supabase.table('florida_parcels').select('*').eq('parcel_id', '3040190012860').execute()

            if property_response.data and len(property_response.data) > 0:
                prop_data = property_response.data[0]
                print(f"Found target property")

                # Look for non-zero exemption values
                active_exemptions = []

                for field_name, value in prop_data.items():
                    field_lower = field_name.lower()

                    # Check for exemption-related fields with values > 0
                    if any(keyword in field_lower for keyword in ['exempt', 'xmpt', 'exmpt', 'homestead', 'hs_']):
                        if value and str(value) != '0' and str(value) != '0.0' and str(value).lower() not in ['', 'n/a', 'none', 'null']:
                            active_exemptions.append({
                                'field': field_name,
                                'value': value,
                                'type': 'exemption'
                            })

                # Common Florida exemption fields to specifically check
                common_exemption_fields = [
                    'homestead_exemption', 'hs_exemption', 'hs_xmpt',
                    'additional_homestead', 'add_hs_xmpt', 'add_homestead',
                    'widow_exemption', 'wd_xmpt', 'widow_xmpt',
                    'veteran_exemption', 'vet_xmpt', 'veteran_xmpt',
                    'disabled_veteran_exemption', 'dis_vet_xmpt',
                    'senior_exemption', 'sr_xmpt', 'senior_xmpt',
                    'blind_exemption', 'blind_xmpt',
                    'disability_exemption', 'dis_xmpt',
                    'exemption_amount', 'total_exemption', 'xmpt_amt'
                ]

                print(f"\nChecking Common Florida Exemption Fields:")
                found_exemptions = []

                for field in common_exemption_fields:
                    if field in prop_data:
                        value = prop_data[field]
                        if value and str(value) != '0' and str(value) != '0.0':
                            found_exemptions.append(f"   FOUND {field}: {value}")
                        else:
                            found_exemptions.append(f"   EMPTY {field}: {value or 'N/A'}")

                if found_exemptions:
                    for exemption in found_exemptions:
                        print(exemption)
                else:
                    print("   No common exemption fields found with values > 0")

                # Check tax-related fields
                print(f"\nTax-Related Fields:")
                tax_related_fields = ['tax_amount', 'annual_tax', 'total_tax', 'taxable_value', 'assessed_value', 'just_value']

                for field in tax_related_fields:
                    if field in prop_data:
                        value = prop_data[field]
                        print(f"   {field}: {value}")

                # Show all available fields for reference
                print(f"\nAll Available Fields ({len(prop_data.keys())}):")
                sorted_fields = sorted(prop_data.keys())
                for i, field in enumerate(sorted_fields, 1):
                    value = prop_data[field]
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 50:
                        display_value = f"{value[:50]}..."
                    else:
                        display_value = value
                    print(f"   {i:2d}. {field}: {display_value}")

            else:
                print("Target property not found")

        else:
            print("No data found in florida_parcels table")

    except Exception as e:
        print(f"Error analyzing exemption fields: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_exemption_fields()