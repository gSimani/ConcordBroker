"""
Florida NAV Mock Data Generator
Creates sample NAV D and NAV N files based on navlayout.pdf specifications
"""

import csv
import random
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NAVMockDataGenerator:
    def __init__(self, output_dir: str = "TEMP/NAV_MOCK_DATA"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Florida counties (11-77)
        self.florida_counties = {
            11: "ALACHUA", 12: "BAKER", 13: "BAY", 14: "BRADFORD", 15: "BREVARD",
            16: "BROWARD", 17: "CALHOUN", 18: "CHARLOTTE", 19: "CITRUS", 20: "CLAY",
            21: "COLLIER", 22: "COLUMBIA", 23: "MIAMI-DADE", 24: "DESOTO", 25: "DIXIE",
            26: "DUVAL", 27: "ESCAMBIA", 28: "FLAGLER", 29: "FRANKLIN", 30: "GADSDEN",
            31: "GILCHRIST", 32: "GLADES", 33: "GULF", 34: "HAMILTON", 35: "HARDEE",
            36: "HENDRY", 37: "HERNANDO", 38: "HIGHLANDS", 39: "HILLSBOROUGH", 40: "HOLMES",
            41: "INDIAN RIVER", 42: "JACKSON", 43: "JEFFERSON", 44: "LAFAYETTE", 45: "LAKE",
            46: "LEE", 47: "LEON", 48: "LEVY", 49: "LIBERTY", 50: "MADISON",
            51: "MANATEE", 52: "MARION", 53: "MARTIN", 54: "MONROE", 55: "NASSAU",
            56: "OKALOOSA", 57: "OKEECHOBEE", 58: "ORANGE", 59: "OSCEOLA", 60: "PALM BEACH",
            61: "PASCO", 62: "PINELLAS", 63: "POLK", 64: "PUTNAM", 65: "ST. JOHNS",
            66: "ST. LUCIE", 67: "SANTA ROSA", 68: "SARASOTA", 69: "SEMINOLE", 70: "SUMTER",
            71: "SUWANNEE", 72: "TAYLOR", 73: "UNION", 74: "VOLUSIA", 75: "WAKULLA",
            76: "WALTON", 77: "WASHINGTON"
        }

        # NAV function codes for different types of assessments
        self.function_codes = [
            "01",  # General government
            "02",  # Public safety
            "03",  # Physical environment
            "04",  # Transportation
            "05",  # Economic environment
            "06",  # Human services
            "07",  # Culture/recreation
            "08",  # Court related
            "09",  # Other
        ]

        # Assessment types
        self.assessment_types = [
            "STORMWATER",
            "FIRE PROTECTION",
            "WASTE COLLECTION",
            "STREETLIGHT",
            "DRAINAGE",
            "ROAD MAINTENANCE",
            "LIBRARY",
            "PARKS",
            "SECURITY"
        ]

    def generate_parcel_id(self, county_code: int) -> str:
        """Generate a realistic Florida parcel ID"""
        # Format: CC-SS-TT-RRRR-PPPP-NNNN
        section = f"{random.randint(1, 36):02d}"
        township = f"{random.randint(10, 40):02d}"
        range_num = f"{random.randint(10, 40):04d}"
        parcel = f"{random.randint(1, 9999):04d}"
        suffix = f"{random.randint(1, 9999):04d}"

        return f"{county_code:02d}-{section}-{township}-{range_num}-{parcel}-{suffix}"

    def generate_nav_n_record(self, county_code: int) -> list:
        """Generate a NAV N (summary) record according to specifications"""
        parcel_id = self.generate_parcel_id(county_code)

        # Table N fields (8 total):
        # N1: Roll Type (always 'N')
        # N2: County Number (11-77)
        # N3: PA Parcel Number
        # N4: Assessment Count
        # N5: Tax Year
        # N6: Total Assessments
        # N7: Assessment Detail Count
        # N8: Filler

        assessment_count = random.randint(1, 5)
        total_assessments = round(random.uniform(100, 5000), 2)

        return [
            'N',                          # N1: Roll Type
            str(county_code),             # N2: County Number
            parcel_id,                    # N3: PA Parcel Number
            str(assessment_count),        # N4: Assessment Count
            '2024',                       # N5: Tax Year
            f"{total_assessments:.2f}",   # N6: Total Assessments
            str(assessment_count),        # N7: Assessment Detail Count
            ''                            # N8: Filler
        ]

    def generate_nav_d_record(self, county_code: int, parcel_id: str = None) -> list:
        """Generate a NAV D (detail) record according to specifications"""
        if not parcel_id:
            parcel_id = self.generate_parcel_id(county_code)

        # Table D fields (8 total):
        # D1: Record Type (always 'D')
        # D2: County Number (11-77)
        # D3: PA Parcel Number
        # D4: Levy Description Code
        # D5: Function Code
        # D6: Assessment Description
        # D7: Assessment Amount
        # D8: Filler

        function_code = random.choice(self.function_codes)
        assessment_type = random.choice(self.assessment_types)
        assessment_amount = round(random.uniform(50, 2000), 2)
        levy_code = f"{random.randint(1, 999):03d}"

        return [
            'D',                          # D1: Record Type
            str(county_code),             # D2: County Number
            parcel_id,                    # D3: PA Parcel Number
            levy_code,                    # D4: Levy Description Code
            function_code,                # D5: Function Code
            assessment_type,              # D6: Assessment Description
            f"{assessment_amount:.2f}",   # D7: Assessment Amount
            ''                            # D8: Filler
        ]

    def generate_county_nav_files(self, county_code: int, num_parcels: int = 100):
        """Generate NAV D and NAV N files for a specific county"""
        county_name = self.florida_counties[county_code]

        # File naming: NAV[D|N][county][year][submission].TXT
        nav_d_filename = f"NAVD{county_code:02d}2401.TXT"
        nav_n_filename = f"NAVN{county_code:02d}2401.TXT"

        nav_d_path = self.output_dir / "NAV_D" / nav_d_filename
        nav_n_path = self.output_dir / "NAV_N" / nav_n_filename

        # Create subdirectories
        nav_d_path.parent.mkdir(exist_ok=True)
        nav_n_path.parent.mkdir(exist_ok=True)

        logger.info(f"Generating NAV files for {county_name} County ({county_code})")

        # Generate parcel data
        parcels_data = []

        for _ in range(num_parcels):
            parcel_id = self.generate_parcel_id(county_code)

            # Generate NAV N record (summary)
            nav_n_record = self.generate_nav_n_record(county_code)
            nav_n_record[2] = parcel_id  # Use consistent parcel ID

            # Generate 1-3 NAV D records (details) per parcel
            num_assessments = random.randint(1, 3)
            nav_d_records = []
            total_amount = 0

            for _ in range(num_assessments):
                nav_d_record = self.generate_nav_d_record(county_code, parcel_id)
                nav_d_records.append(nav_d_record)
                total_amount += float(nav_d_record[6])

            # Update NAV N total assessments to match details
            nav_n_record[5] = f"{total_amount:.2f}"
            nav_n_record[3] = str(num_assessments)
            nav_n_record[6] = str(num_assessments)

            parcels_data.append({
                'nav_n': nav_n_record,
                'nav_d': nav_d_records
            })

        # Write NAV N file
        with open(nav_n_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for parcel in parcels_data:
                writer.writerow(parcel['nav_n'])

        # Write NAV D file
        with open(nav_d_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for parcel in parcels_data:
                for nav_d_record in parcel['nav_d']:
                    writer.writerow(nav_d_record)

        logger.info(f"Generated {nav_d_filename} with {sum(len(p['nav_d']) for p in parcels_data)} detail records")
        logger.info(f"Generated {nav_n_filename} with {len(parcels_data)} summary records")

        return {
            'county_code': county_code,
            'county_name': county_name,
            'nav_d_file': nav_d_path,
            'nav_n_file': nav_n_path,
            'parcels': len(parcels_data),
            'assessments': sum(len(p['nav_d']) for p in parcels_data)
        }

    def generate_sample_dataset(self, sample_counties: list = None, parcels_per_county: int = 50):
        """Generate sample NAV dataset for testing"""
        if sample_counties is None:
            # Sample counties: Miami-Dade, Orange, Hillsborough, Broward, Palm Beach
            sample_counties = [23, 58, 39, 16, 60]

        results = []
        total_parcels = 0
        total_assessments = 0

        logger.info(f"Generating mock NAV dataset for {len(sample_counties)} counties")

        for county_code in sample_counties:
            county_result = self.generate_county_nav_files(county_code, parcels_per_county)
            results.append(county_result)
            total_parcels += county_result['parcels']
            total_assessments += county_result['assessments']

        # Generate summary report
        self.generate_mock_summary_report(results, total_parcels, total_assessments)

        return results

    def generate_mock_summary_report(self, results: list, total_parcels: int, total_assessments: int):
        """Generate a summary report of the mock data"""
        report_path = self.output_dir / "NAV_Mock_Data_Report.txt"

        with open(report_path, 'w') as f:
            f.write("Florida NAV Mock Dataset Report\n")
            f.write("=" * 40 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("PURPOSE\n")
            f.write("-" * 10 + "\n")
            f.write("This mock dataset demonstrates the NAV (Non Ad Valorem) data processing\n")
            f.write("infrastructure based on the Florida Department of Revenue specifications\n")
            f.write("from navlayout.pdf. Files follow the exact format requirements for\n")
            f.write("production NAV D (detail) and NAV N (summary) files.\n\n")

            f.write("MOCK DATA SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Counties Generated: {len(results)}\n")
            f.write(f"Total Parcels: {total_parcels:,}\n")
            f.write(f"Total Assessments: {total_assessments:,}\n\n")

            f.write("COUNTY BREAKDOWN\n")
            f.write("-" * 20 + "\n")
            for result in results:
                f.write(f"{result['county_name']} (Code {result['county_code']:02d}):\n")
                f.write(f"  Parcels: {result['parcels']:,}\n")
                f.write(f"  Assessments: {result['assessments']:,}\n")
                f.write(f"  NAV D File: {result['nav_d_file'].name}\n")
                f.write(f"  NAV N File: {result['nav_n_file'].name}\n\n")

            f.write("FILE SPECIFICATIONS\n")
            f.write("-" * 20 + "\n")
            f.write("NAV D Files (Assessment Details):\n")
            f.write("  - 8 fields per record (D1-D8)\n")
            f.write("  - Record Type 'D'\n")
            f.write("  - County codes 11-77\n")
            f.write("  - Function codes 01-09\n")
            f.write("  - Assessment amounts in decimal format\n\n")

            f.write("NAV N Files (Assessment Summaries):\n")
            f.write("  - 8 fields per record (N1-N8)\n")
            f.write("  - Record Type 'N'\n")
            f.write("  - County codes 11-77\n")
            f.write("  - Tax year 2024\n")
            f.write("  - Total assessment amounts matching detail records\n\n")

            f.write("INTEGRATION READY\n")
            f.write("-" * 15 + "\n")
            f.write("This mock dataset can be processed by the existing NAV processor\n")
            f.write("infrastructure to validate data processing, database integration,\n")
            f.write("and reporting capabilities before working with production data.\n")

        logger.info(f"Mock data summary report saved to: {report_path}")

def main():
    generator = NAVMockDataGenerator()

    logger.info("Starting NAV Mock Data Generation")

    # Generate sample dataset
    results = generator.generate_sample_dataset()

    logger.info("Mock NAV dataset generation complete")
    logger.info(f"Files saved to: {generator.output_dir}")

    return results

if __name__ == "__main__":
    main()