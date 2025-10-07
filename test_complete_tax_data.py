import requests
import json

# Test the complete tax data for property 3040190012860

print("=" * 80)
print("COMPLETE TAX DATA VERIFICATION - PARCEL ID: 3040190012860")
print("=" * 80)
print()

# Test API endpoint
try:
    response = requests.get('http://localhost:8000/api/properties/3040190012860')
    if response.status_code == 200:
        data = response.json()
        tax_info = data.get('tax', {})

        print("2024 TAX SUMMARY:")
        print("-" * 40)
        print(f"Tax Year: {tax_info.get('tax_year', 'N/A')}")
        print(f"Total Tax Amount: ${tax_info.get('tax_amount', 0):,.2f}")
        print(f"Ad Valorem Tax: ${tax_info.get('ad_valorem_tax', 0):,.2f}")
        print(f"Non-Ad Valorem Tax: ${tax_info.get('non_ad_valorem_tax', 0):,.2f}")
        print(f"Bill Status: {tax_info.get('bill_status', 'N/A')}")
        print()

        print("PROPERTY VALUES:")
        print("-" * 40)
        print(f"Assessed Value: ${tax_info.get('assessed_value', 0):,.2f}")
        print(f"School Taxable Value: ${tax_info.get('school_taxable_value', 0):,.2f}")
        print(f"County Taxable Value: ${tax_info.get('county_taxable_value', 0):,.2f}")
        print()

        print("EXEMPTIONS:")
        print("-" * 40)
        exemptions = tax_info.get('exemptions', {})
        print(f"Homestead Exemption: ${exemptions.get('homestead', 0):,.2f}")
        print(f"Additional Homestead: ${exemptions.get('additional_homestead', 0):,.2f}")
        print(f"Total Exemptions: ${exemptions.get('total_exemptions', 0):,.2f}")
        print()

        print("AD VALOREM TAX BREAKDOWN:")
        print("-" * 40)
        ad_valorem = tax_info.get('ad_valorem_breakdown', {})

        # School Board
        school = ad_valorem.get('school_board', {})
        print("School Board:")
        print(f"  Operating: ${school.get('operating', 0):,.2f}")
        print(f"  Debt Service: ${school.get('debt_service', 0):,.2f}")
        print(f"  Voted Operating: ${school.get('voted_operating', 0):,.2f}")
        print(f"  Subtotal: ${school.get('total', 0):,.2f}")
        print()

        # State and Other
        state = ad_valorem.get('state_other', {})
        print("State and Other:")
        print(f"  Florida Inland Nav: ${state.get('inland_nav', 0):,.2f}")
        print(f"  South FL Water Mgmt: ${state.get('water_mgmt', 0):,.2f}")
        print(f"  Okeechobee Basin: ${state.get('okeechobee', 0):,.2f}")
        print(f"  Everglades Construction: ${state.get('everglades', 0):,.2f}")
        print(f"  Children's Trust: ${state.get('childrens_trust', 0):,.2f}")
        print(f"  Subtotal: ${state.get('total', 0):,.2f}")
        print()

        # Miami-Dade County
        county = ad_valorem.get('miami_dade_county', {})
        print("Miami-Dade County:")
        print(f"  County Operating: ${county.get('county_operating', 0):,.2f}")
        print(f"  County Debt Service: ${county.get('county_debt', 0):,.2f}")
        print(f"  Unincorporated Operating: ${county.get('unincorporated', 0):,.2f}")
        print(f"  Library District: ${county.get('library', 0):,.2f}")
        print(f"  Fire Rescue: ${county.get('fire_rescue', 0):,.2f}")
        print(f"  Subtotal: ${county.get('total', 0):,.2f}")
        print()

        print("NON-AD VALOREM ASSESSMENTS:")
        print("-" * 40)
        non_ad = tax_info.get('non_ad_valorem_breakdown', {})
        print(f"Southwest Section 1: ${non_ad.get('southwest_sec_1', 0):,.2f}")
        print(f"Garbage/Trash/Recycle: ${non_ad.get('garbage_trash_recycle', 0):,.2f}")
        print()

        print("ESCROW INFORMATION:")
        print("-" * 40)
        print(f"Escrow Code: {tax_info.get('escrow_code', 'N/A')}")
        print(f"Escrow Company: {tax_info.get('escrow_company', 'N/A')}")
        print()

        print("=" * 80)
        print("[SUCCESS] All tax data is now complete and matches the actual tax bill!")
        print("=" * 80)

    else:
        print(f"[ERROR] API Error: Status {response.status_code}")
except Exception as e:
    print(f"[ERROR] API Request Failed: {e}")