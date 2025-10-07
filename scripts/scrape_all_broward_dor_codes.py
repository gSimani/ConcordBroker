"""
Scrape all DOR Use Type codes from Broward County Property Appraiser
Source: https://bcpa.net/UseType.asp
"""
import requests
from bs4 import BeautifulSoup
import re
import json
from pathlib import Path

def scrape_broward_dor_codes():
    """Scrape all DOR codes from Broward County website"""

    url = "https://bcpa.net/UseType.asp"

    print("Fetching Broward County DOR use codes...")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all code definitions
    codes = []

    # The page structure has codes in format: "XX-YY: Description"
    # Look for all text containing the pattern
    text_content = soup.get_text()

    # Pattern to match codes like "01-01: Single Family"
    pattern = r'(\d{2})-(\d{2}):\s*(.+?)(?=\d{2}-\d{2}:|$)'

    matches = re.findall(pattern, text_content, re.DOTALL)

    for match in matches:
        main_code = match[0]
        sub_code = match[1]
        full_code = f"{main_code}-{sub_code}"
        description = match[2].strip()

        # Clean description - remove extra whitespace and newlines
        description = ' '.join(description.split())

        # Determine category
        main_num = int(main_code)
        if main_num <= 9:
            category = 'Residential'
        elif 10 <= main_num <= 39:
            category = 'Commercial'
        elif 40 <= main_num <= 49:
            category = 'Industrial'
        elif 50 <= main_num <= 69:
            category = 'Agricultural'
        elif 70 <= main_num <= 79:
            category = 'Institutional'
        elif 80 <= main_num <= 89:
            category = 'Government'
        elif main_num == 0:
            category = 'Vacant Land'
        else:  # 90-99
            category = 'Vacant Land'

        codes.append({
            'main_code': main_code,
            'sub_code': sub_code,
            'full_code': full_code,
            'description': description,
            'category': category
        })

    # Sort by full_code
    codes.sort(key=lambda x: x['full_code'])

    # Remove duplicates
    seen = set()
    unique_codes = []
    for code in codes:
        if code['full_code'] not in seen:
            seen.add(code['full_code'])
            unique_codes.append(code)

    print(f"\nScraped {len(unique_codes)} unique DOR codes")

    # Show sample by category
    categories = {}
    for code in unique_codes:
        cat = code['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(code)

    print("\nCodes by category:")
    for cat, cat_codes in sorted(categories.items()):
        print(f"  {cat}: {len(cat_codes)} codes")
        # Show first 3 examples
        for code in cat_codes[:3]:
            print(f"    {code['full_code']}: {code['description'][:60]}...")

    return unique_codes

def save_codes_to_file(codes, filename='broward_dor_codes.json'):
    """Save codes to JSON file"""
    output_path = Path(__file__).parent.parent / filename

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(codes)} codes to {output_path}")
    return output_path

def generate_sql_insert(codes):
    """Generate SQL INSERT statement for all codes"""

    sql_lines = [
        "-- Complete Broward County DOR Use Codes",
        "-- Source: https://bcpa.net/UseType.asp",
        "-- Total codes: {}".format(len(codes)),
        "",
        "INSERT INTO dor_use_codes_std (main_code, sub_code, full_code, description, category) VALUES"
    ]

    value_lines = []
    for code in codes:
        # Escape single quotes in description
        desc = code['description'].replace("'", "''")
        value_lines.append(
            f"('{code['main_code']}', '{code['sub_code']}', '{code['full_code']}', '{desc}', '{code['category']}')"
        )

    sql_lines.append(',\n'.join(value_lines))
    sql_lines.append("ON CONFLICT (full_code) DO UPDATE SET")
    sql_lines.append("  description = EXCLUDED.description,")
    sql_lines.append("  category = EXCLUDED.category;")

    sql = '\n'.join(sql_lines)

    # Save to file
    sql_path = Path(__file__).parent.parent / 'supabase' / 'migrations' / 'insert_all_broward_dor_codes.sql'
    sql_path.parent.mkdir(parents=True, exist_ok=True)

    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write(sql)

    print(f"\nGenerated SQL file: {sql_path}")
    return sql_path

if __name__ == '__main__':
    try:
        # Scrape codes
        codes = scrape_broward_dor_codes()

        if not codes:
            print("ERROR: No codes found!")
            exit(1)

        # Save to JSON
        json_path = save_codes_to_file(codes)

        # Generate SQL
        sql_path = generate_sql_insert(codes)

        print("\n" + "="*80)
        print("SUCCESS - All Broward DOR codes scraped and processed")
        print("="*80)
        print(f"\nJSON file: {json_path}")
        print(f"SQL file: {sql_path}")
        print(f"\nNext step: Run the SQL file in Supabase SQL Editor")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
