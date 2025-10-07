"""
Florida Counties Manager
Comprehensive list of all 67 Florida counties with proper URL formatting
for the Florida Department of Revenue data portal.
"""

import re
from typing import List, Dict, Tuple


class FloridaCountiesManager:
    """Manager class for Florida counties with URL formatting and validation"""

    # Complete list of all 67 Florida counties
    FLORIDA_COUNTIES = [
        'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
        'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DESOTO', 'DIXIE',
        'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST', 'GLADES',
        'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS', 'HILLSBOROUGH',
        'HOLMES', 'INDIAN_RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE', 'LAKE', 'LEE',
        'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION', 'MARTIN', 'MIAMI_DADE',
        'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE', 'ORANGE', 'OSCEOLA', 'PALM_BEACH',
        'PASCO', 'PINELLAS', 'POLK', 'PUTNAM', 'SANTA_ROSA', 'SARASOTA', 'SEMINOLE',
        'ST_JOHNS', 'ST_LUCIE', 'SUMTER', 'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA',
        'WAKULLA', 'WALTON', 'WASHINGTON'
    ]

    # Special county name mappings for URLs
    COUNTY_URL_MAPPINGS = {
        'MIAMI_DADE': 'MIAMI-DADE',
        'INDIAN_RIVER': 'INDIAN%20RIVER',
        'PALM_BEACH': 'PALM%20BEACH',
        'SANTA_ROSA': 'SANTA%20ROSA',
        'ST_JOHNS': 'ST.%20JOHNS',
        'ST_LUCIE': 'ST.%20LUCIE'
    }

    # County codes for file naming
    COUNTY_CODES = {
        'ALACHUA': '01', 'BAKER': '02', 'BAY': '03', 'BRADFORD': '04', 'BREVARD': '05',
        'BROWARD': '06', 'CALHOUN': '07', 'CHARLOTTE': '08', 'CITRUS': '09', 'CLAY': '10',
        'COLLIER': '11', 'COLUMBIA': '12', 'DESOTO': '13', 'DIXIE': '14', 'DUVAL': '15',
        'ESCAMBIA': '16', 'FLAGLER': '17', 'FRANKLIN': '18', 'GADSDEN': '19', 'GILCHRIST': '20',
        'GLADES': '21', 'GULF': '22', 'HAMILTON': '23', 'HARDEE': '24', 'HENDRY': '25',
        'HERNANDO': '26', 'HIGHLANDS': '27', 'HILLSBOROUGH': '28', 'HOLMES': '29', 'INDIAN_RIVER': '30',
        'JACKSON': '31', 'JEFFERSON': '32', 'LAFAYETTE': '33', 'LAKE': '34', 'LEE': '35',
        'LEON': '36', 'LEVY': '37', 'LIBERTY': '38', 'MADISON': '39', 'MANATEE': '40',
        'MARION': '41', 'MARTIN': '42', 'MIAMI_DADE': '43', 'MONROE': '44', 'NASSAU': '45',
        'OKALOOSA': '46', 'OKEECHOBEE': '47', 'ORANGE': '48', 'OSCEOLA': '49', 'PALM_BEACH': '50',
        'PASCO': '51', 'PINELLAS': '52', 'POLK': '53', 'PUTNAM': '54', 'SANTA_ROSA': '55',
        'SARASOTA': '56', 'SEMINOLE': '57', 'ST_JOHNS': '58', 'ST_LUCIE': '59', 'SUMTER': '60',
        'SUWANNEE': '61', 'TAYLOR': '62', 'UNION': '63', 'VOLUSIA': '64', 'WAKULLA': '65',
        'WALTON': '66', 'WASHINGTON': '67'
    }

    @classmethod
    def get_all_counties(cls) -> List[str]:
        """Get list of all Florida counties"""
        return cls.FLORIDA_COUNTIES.copy()

    @classmethod
    def format_county_for_url(cls, county: str) -> str:
        """
        Format county name for URL usage in Florida DOR data portal

        Args:
            county: County name in standard format (e.g., 'MIAMI_DADE')

        Returns:
            URL-formatted county name (e.g., 'MIAMI-DADE')
        """
        county = county.upper().strip()

        # Apply special mappings
        if county in cls.COUNTY_URL_MAPPINGS:
            return cls.COUNTY_URL_MAPPINGS[county]

        # Replace underscores with hyphens for URL
        return county.replace('_', '-')

    @classmethod
    def format_county_for_filename(cls, county: str) -> str:
        """
        Format county name for file system usage

        Args:
            county: County name in standard format

        Returns:
            File-system safe county name
        """
        county = county.upper().strip()
        # Keep underscores for file names
        return county.replace(' ', '_').replace('-', '_')

    @classmethod
    def get_county_code(cls, county: str) -> str:
        """
        Get the numeric code for a county

        Args:
            county: County name in standard format

        Returns:
            Two-digit county code
        """
        county = county.upper().strip()
        return cls.COUNTY_CODES.get(county, '00')

    @classmethod
    def validate_county(cls, county: str) -> bool:
        """
        Validate if a county name is valid Florida county

        Args:
            county: County name to validate

        Returns:
            True if valid county, False otherwise
        """
        county = county.upper().strip()
        return county in cls.FLORIDA_COUNTIES

    @classmethod
    def build_sdf_download_url(cls, county: str, year: str = '2025') -> str:
        """
        Build the complete SDF download URL for a county

        Args:
            county: County name in standard format
            year: Tax year (default: 2025)

        Returns:
            Complete download URL for SDF zip file
        """
        if not cls.validate_county(county):
            raise ValueError(f"Invalid county: {county}")

        url_county = cls.format_county_for_url(county)
        base_url = "https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/SDF"

        return f"{base_url}/{year}P/{url_county}.zip"

    @classmethod
    def get_county_info(cls, county: str) -> Dict:
        """
        Get comprehensive information about a county

        Args:
            county: County name in standard format

        Returns:
            Dictionary with county information
        """
        if not cls.validate_county(county):
            raise ValueError(f"Invalid county: {county}")

        return {
            'name': county,
            'code': cls.get_county_code(county),
            'url_format': cls.format_county_for_url(county),
            'filename_format': cls.format_county_for_filename(county),
            'download_url': cls.build_sdf_download_url(county),
            'valid': True
        }

    @classmethod
    def get_all_county_info(cls, year: str = '2025') -> List[Dict]:
        """
        Get information for all Florida counties

        Args:
            year: Tax year for download URLs

        Returns:
            List of dictionaries with county information
        """
        return [cls.get_county_info(county) for county in cls.FLORIDA_COUNTIES]

    @classmethod
    def get_priority_counties(cls) -> List[str]:
        """
        Get list of high-priority counties (largest by population/property count)

        Returns:
            List of priority county names
        """
        # Large counties with most properties - prioritize for initial processing
        return [
            'MIAMI_DADE',    # Largest county
            'BROWARD',       # Second largest
            'PALM_BEACH',    # Third largest
            'HILLSBOROUGH',  # Tampa area
            'ORANGE',        # Orlando area
            'PINELLAS',      # St. Petersburg area
            'DUVAL',         # Jacksonville area
            'LEE',           # Fort Myers area
            'POLK',          # Lakeland area
            'VOLUSIA'        # Daytona Beach area
        ]

    @classmethod
    def get_test_counties(cls) -> List[str]:
        """
        Get list of smaller counties for testing

        Returns:
            List of test county names (smaller counties)
        """
        return [
            'LAFAYETTE',     # Very small county
            'LIBERTY',       # Small county
            'DIXIE',         # Small county
            'UNION',         # Small county
            'GLADES'         # Small county
        ]


if __name__ == "__main__":
    # Test the counties manager
    manager = FloridaCountiesManager()

    print("Florida Counties Manager Test")
    print("=" * 50)

    # Test a few counties
    test_counties = ['MIAMI_DADE', 'BROWARD', 'ST_JOHNS', 'PALM_BEACH']

    for county in test_counties:
        info = manager.get_county_info(county)
        print(f"\nCounty: {county}")
        print(f"  Code: {info['code']}")
        print(f"  URL Format: {info['url_format']}")
        print(f"  Download URL: {info['download_url']}")

    print(f"\nTotal Counties: {len(manager.get_all_counties())}")
    print(f"Priority Counties: {len(manager.get_priority_counties())}")
    print(f"Test Counties: {len(manager.get_test_counties())}")