"""
Parse County Property Files
Parses NAL, NAP, NAV, and SDF files into structured data
Handles fixed-width and delimited formats
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict
from datetime import date


# NAL Format Specification (Florida Revenue - Name, Address, Legal)
# This is an example - actual format may vary
NAL_FORMAT = {
    'parcel_id': (0, 20),
    'county_code': (20, 25),
    'tax_year': (25, 29),
    'owner_name': (29, 79),
    'owner_addr1': (79, 129),
    'owner_addr2': (129, 179),
    'owner_city': (179, 229),
    'owner_state': (229, 231),
    'owner_zip': (231, 241),
    'phy_addr1': (241, 291),
    'phy_addr2': (291, 341),
    'city': (341, 391),
    'zip_code': (391, 401),
    'property_use_code': (401, 411),
    'just_value': (411, 426),
    'assessed_value': (426, 441),
    'taxable_value': (441, 456),
    'land_value': (456, 471),
    'building_value': (471, 486),
    'land_sqft': (486, 501),
}


def parse_fixed_width_line(line: str, format_spec: Dict) -> Dict:
    """Parse a fixed-width line according to format specification"""

    record = {}

    for field_name, (start, end) in format_spec.items():
        value = line[start:end].strip()

        # Convert numeric fields
        if field_name in ['tax_year', 'land_sqft']:
            try:
                record[field_name] = int(value) if value else None
            except ValueError:
                record[field_name] = None

        elif field_name.endswith('_value') or field_name == 'land_sqft':
            try:
                record[field_name] = float(value) if value else None
            except ValueError:
                record[field_name] = None

        else:
            record[field_name] = value if value else None

    return record


def parse_nal_file(file_path: Path) -> List[Dict]:
    """Parse NAL (Name, Address, Legal) file"""

    print(f"\n📄 Parsing NAL file: {file_path.name}")
    records = []

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        record = parse_fixed_width_line(line, NAL_FORMAT)
                        record['line_number'] = line_num
                        records.append(record)

                        if line_num % 10000 == 0:
                            print(f"   Processed {line_num:,} lines...")

                    except Exception as e:
                        print(f"   ⚠️  Error on line {line_num}: {e}")

        print(f"   ✅ Parsed {len(records):,} records")
        return records

    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return []


def parse_sdf_file(file_path: Path) -> List[Dict]:
    """Parse SDF (Sales Data File) file"""

    print(f"\n📄 Parsing SDF file: {file_path.name}")
    records = []

    # SDF format (example - may vary)
    sdf_format = {
        'parcel_id': (0, 20),
        'county_code': (20, 25),
        'sale_date': (25, 33),  # YYYYMMDD
        'sale_price': (33, 48),
        'buyer_name': (48, 98),
        'seller_name': (98, 148),
        'deed_book': (148, 158),
        'deed_page': (158, 168),
    }

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip():
                    try:
                        record = parse_fixed_width_line(line, sdf_format)

                        # Convert sale_date from YYYYMMDD to date
                        if record.get('sale_date'):
                            date_str = record['sale_date']
                            try:
                                record['sale_date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                            except:
                                record['sale_date'] = None

                        record['line_number'] = line_num
                        records.append(record)

                        if line_num % 10000 == 0:
                            print(f"   Processed {line_num:,} lines...")

                    except Exception as e:
                        print(f"   ⚠️  Error on line {line_num}: {e}")

        print(f"   ✅ Parsed {len(records):,} records")
        return records

    except Exception as e:
        print(f"   ❌ Error reading file: {e}")
        return []


def export_to_csv(records: List[Dict], output_file: Path):
    """Export parsed records to CSV"""

    if not records:
        print("   ⚠️  No records to export")
        return

    print(f"\n💾 Exporting to CSV: {output_file}")

    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=records[0].keys())
            writer.writeheader()
            writer.writerows(records)

        print(f"   ✅ Exported {len(records):,} records")
        print(f"   📊 File size: {output_file.stat().st_size:,} bytes")

    except Exception as e:
        print(f"   ❌ Export error: {e}")


def parse_county_files(county: str, download_date: str = None):
    """Parse all files for a county"""

    if download_date is None:
        download_date = str(date.today())

    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / download_date
    parsed_dir = Path(__file__).parent.parent / 'data' / 'parsed' / download_date
    parsed_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print(f"PARSING {county.upper()} COUNTY FILES")
    print("=" * 80)

    print(f"\n📂 Input directory: {data_dir}")
    print(f"📂 Output directory: {parsed_dir}")

    if not data_dir.exists():
        print(f"\n❌ Input directory not found: {data_dir}")
        print("   Run download_county.py first")
        return

    # Find files for this county
    county_upper = county.upper()
    files = {
        'NAL': list(data_dir.glob(f"{county_upper}_NAL*.txt")) + list(data_dir.glob(f"{county_upper}_NAL*.TXT")),
        'SDF': list(data_dir.glob(f"{county_upper}_SDF*.txt")) + list(data_dir.glob(f"{county_upper}_SDF*.TXT")),
        'NAP': list(data_dir.glob(f"{county_upper}_NAP*.txt")) + list(data_dir.glob(f"{county_upper}_NAP*.TXT")),
        'NAV': list(data_dir.glob(f"{county_upper}_NAV*.txt")) + list(data_dir.glob(f"{county_upper}_NAV*.TXT")),
    }

    # Parse NAL file
    if files['NAL']:
        nal_records = parse_nal_file(files['NAL'][0])
        if nal_records:
            csv_file = parsed_dir / f"{county_upper}_NAL_parsed.csv"
            export_to_csv(nal_records, csv_file)
    else:
        print(f"\n⚠️  No NAL file found for {county_upper}")

    # Parse SDF file
    if files['SDF']:
        sdf_records = parse_sdf_file(files['SDF'][0])
        if sdf_records:
            csv_file = parsed_dir / f"{county_upper}_SDF_parsed.csv"
            export_to_csv(sdf_records, csv_file)
    else:
        print(f"\n⚠️  No SDF file found for {county_upper}")

    # NAP and NAV would be similar - placeholder for now
    if files['NAP']:
        print(f"\n⚠️  NAP parsing not yet implemented")

    if files['NAV']:
        print(f"\n⚠️  NAV parsing not yet implemented")

    print("\n" + "=" * 80)
    print("✅ PARSING COMPLETE")
    print("=" * 80)

    print(f"\n📊 Parsed files saved to: {parsed_dir}")
    print("\n💡 Next step:")
    print(f"   python scripts/load_county_data.py --county {county}")


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(description='Parse Florida County Property Files')
    parser.add_argument('--county', required=True, help='County name (e.g., BROWARD)')
    parser.add_argument('--date', help='Download date (YYYY-MM-DD), default: today')

    args = parser.parse_args()

    parse_county_files(args.county, args.date)


if __name__ == '__main__':
    main()
