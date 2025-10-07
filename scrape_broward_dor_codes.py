import re
import json
import requests
from bs4 import BeautifulSoup

# Fetch the page
url = "https://bcpa.net/UseType.asp"
response = requests.get(url)
response.raise_for_status()

# Parse HTML
soup = BeautifulSoup(response.content, 'html.parser')

# Find all table rows with the code pattern
# Pattern: <TR><TD><A Name="XXXX">XX-YY</TD><TD>Description</TD></TR>
rows = soup.find_all('tr')
matches = []

for row in rows:
    tds = row.find_all('td')
    if len(tds) >= 2:
        # First TD contains the code
        code_text = tds[0].get_text(strip=True)
        # Second TD contains the description
        desc_text = tds[1].get_text(strip=True)

        # Match pattern XX-YY
        code_match = re.match(r'(\d{2})-(\d{2})', code_text)
        if code_match and desc_text:
            main_code = code_match.group(1)
            sub_code = code_match.group(2)
            matches.append((main_code, sub_code, desc_text))

# Function to determine category based on main code
def get_category(main_code):
    code = int(main_code)
    if code == 0:
        return 'Vacant Land'
    elif code <= 9:
        return 'Residential'
    elif code <= 39:
        return 'Commercial'
    elif code <= 49:
        return 'Industrial'
    elif code <= 69:
        return 'Agricultural'
    elif code <= 79:
        return 'Institutional'
    elif code <= 89:
        return 'Government'
    else:
        return 'Vacant Land'

# Process matches
codes = []
for main_code, sub_code, description in matches:
    # Clean description - remove extra whitespace and newlines
    desc = ' '.join(description.strip().split())

    full_code = f"{main_code}-{sub_code}"
    category = get_category(main_code)

    codes.append({
        'main_code': main_code,
        'sub_code': sub_code,
        'full_code': full_code,
        'description': desc,
        'category': category
    })

print(f"Found {len(codes)} DOR use codes")

# Generate SQL file
sql_output = """-- Broward County DOR Use Type Codes
-- Scraped from https://bcpa.net/UseType.asp
-- Total codes: {count}

INSERT INTO dor_use_codes_std (main_code, sub_code, full_code, description, category) VALUES
""".format(count=len(codes))

sql_values = []
for code in codes:
    # Escape single quotes in descriptions
    desc_escaped = code['description'].replace("'", "''")
    sql_values.append(
        f"('{code['main_code']}', '{code['sub_code']}', '{code['full_code']}', '{desc_escaped}', '{code['category']}')"
    )

sql_output += ',\n'.join(sql_values)
sql_output += """
ON CONFLICT (full_code) DO UPDATE SET
  description = EXCLUDED.description,
  category = EXCLUDED.category;
"""

# Save SQL file
sql_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\supabase\migrations\insert_all_broward_dor_codes.sql"
with open(sql_path, 'w', encoding='utf-8') as f:
    f.write(sql_output)

print(f"SQL file created at: {sql_path}")

# Save JSON file
json_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\broward_dor_codes.json"
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(codes, f, indent=2)

print(f"JSON file created at: {json_path}")

# Show first 10 codes for verification
print("\nFirst 10 codes:")
for i, code in enumerate(codes[:10], 1):
    print(f"{i}. {code['full_code']}: {code['description']} ({code['category']})")
