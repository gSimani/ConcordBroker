#!/usr/bin/env python3
"""
Property Filter Validation System
Comprehensive validation and normalization for property search filters
"""

import re
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for filter validation errors"""
    pass

class FilterValidationSystem:
    """Comprehensive validation system for property filters"""

    def __init__(self):
        self.valid_property_codes = self._get_valid_property_codes()
        self.valid_sub_usage_codes = self._get_valid_sub_usage_codes()
        self.valid_counties = self._get_florida_counties()

    def _get_valid_property_codes(self) -> List[str]:
        """Get list of valid property use codes"""
        return [
            '01', '02', '03', '04', '05', '06', '07', '08', '09',  # Residential
            '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',  # Commercial
            '20', '21', '22', '23', '24', '25', '26', '27',  # Industrial
            '30', '31', '32', '33', '34', '35', '36', '37', '38', '39'  # Special Use
        ]

    def _get_valid_sub_usage_codes(self) -> List[str]:
        """Get list of valid sub-usage codes"""
        # Sub-usage codes are typically 00-99
        return [f"{i:02d}" for i in range(100)]

    def _get_florida_counties(self) -> List[str]:
        """Get list of Florida counties"""
        return [
            'ALACHUA', 'BAKER', 'BAY', 'BRADFORD', 'BREVARD', 'BROWARD', 'CALHOUN',
            'CHARLOTTE', 'CITRUS', 'CLAY', 'COLLIER', 'COLUMBIA', 'DADE', 'DESOTO',
            'DIXIE', 'DUVAL', 'ESCAMBIA', 'FLAGLER', 'FRANKLIN', 'GADSDEN', 'GILCHRIST',
            'GLADES', 'GULF', 'HAMILTON', 'HARDEE', 'HENDRY', 'HERNANDO', 'HIGHLANDS',
            'HILLSBOROUGH', 'HOLMES', 'INDIAN RIVER', 'JACKSON', 'JEFFERSON', 'LAFAYETTE',
            'LAKE', 'LEE', 'LEON', 'LEVY', 'LIBERTY', 'MADISON', 'MANATEE', 'MARION',
            'MARTIN', 'MIAMI-DADE', 'MONROE', 'NASSAU', 'OKALOOSA', 'OKEECHOBEE',
            'ORANGE', 'OSCEOLA', 'PALM BEACH', 'PASCO', 'PINELLAS', 'POLK', 'PUTNAM',
            'SANTA ROSA', 'SARASOTA', 'SEMINOLE', 'ST. JOHNS', 'ST. LUCIE', 'SUMTER',
            'SUWANNEE', 'TAYLOR', 'UNION', 'VOLUSIA', 'WAKULLA', 'WALTON', 'WASHINGTON'
        ]

    def validate_value_range(self, min_value: Optional[int], max_value: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
        """Validate and normalize value range filters"""
        if min_value is not None:
            if min_value < 0:
                raise ValidationError("Minimum value cannot be negative")
            if min_value > 50000000:  # $50M reasonable upper limit
                raise ValidationError("Minimum value exceeds reasonable limit ($50M)")

        if max_value is not None:
            if max_value < 0:
                raise ValidationError("Maximum value cannot be negative")
            if max_value > 50000000:
                raise ValidationError("Maximum value exceeds reasonable limit ($50M)")

        # Auto-swap if min > max
        if min_value is not None and max_value is not None:
            if min_value > max_value:
                logger.warning(f"Swapping min_value ({min_value}) and max_value ({max_value})")
                min_value, max_value = max_value, min_value

        return min_value, max_value

    def validate_sqft_range(self, min_sqft: Optional[int], max_sqft: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
        """Validate and normalize square footage range filters"""
        if min_sqft is not None:
            if min_sqft < 0:
                raise ValidationError("Minimum square footage cannot be negative")
            if min_sqft > 100000:  # 100,000 sq ft reasonable upper limit
                raise ValidationError("Minimum square footage exceeds reasonable limit (100,000 sq ft)")

        if max_sqft is not None:
            if max_sqft < 0:
                raise ValidationError("Maximum square footage cannot be negative")
            if max_sqft > 100000:
                raise ValidationError("Maximum square footage exceeds reasonable limit (100,000 sq ft)")

        # Auto-swap if min > max
        if min_sqft is not None and max_sqft is not None:
            if min_sqft > max_sqft:
                logger.warning(f"Swapping min_sqft ({min_sqft}) and max_sqft ({max_sqft})")
                min_sqft, max_sqft = max_sqft, min_sqft

        return min_sqft, max_sqft

    def validate_year_range(self, min_year: Optional[int], max_year: Optional[int]) -> Tuple[Optional[int], Optional[int]]:
        """Validate and normalize year built range filters"""
        current_year = datetime.now().year

        if min_year is not None:
            if min_year < 1800:
                logger.warning(f"Adjusting min_year from {min_year} to 1800")
                min_year = 1800
            if min_year > current_year:
                raise ValidationError(f"Minimum year cannot be in the future (current year: {current_year})")

        if max_year is not None:
            if max_year < 1800:
                raise ValidationError("Maximum year cannot be before 1800")
            if max_year > current_year:
                logger.warning(f"Adjusting max_year from {max_year} to {current_year}")
                max_year = current_year

        # Auto-swap if min > max
        if min_year is not None and max_year is not None:
            if min_year > max_year:
                logger.warning(f"Swapping min_year ({min_year}) and max_year ({max_year})")
                min_year, max_year = max_year, min_year

        return min_year, max_year

    def validate_property_use_code(self, code: Optional[str]) -> Optional[str]:
        """Validate and normalize property use code"""
        if code is None:
            return None

        # Remove whitespace and convert to string
        code = str(code).strip()

        if not code:
            return None

        # Pad single digit codes with leading zero
        if len(code) == 1 and code.isdigit():
            code = f"0{code}"

        # Validate format (should be exactly 2 digits)
        if not re.match(r'^\d{2}$', code):
            raise ValidationError(f"Property use code must be 2 digits, got: '{code}'")

        # Validate against known codes
        if code not in self.valid_property_codes:
            raise ValidationError(f"Invalid property use code: '{code}'. Valid codes: {', '.join(self.valid_property_codes)}")

        return code

    def validate_sub_usage_code(self, code: Optional[str]) -> Optional[str]:
        """Validate and normalize sub-usage code"""
        if code is None:
            return None

        # Remove whitespace and convert to string
        code = str(code).strip()

        if not code:
            return None

        # Pad single digit codes with leading zero
        if len(code) == 1 and code.isdigit():
            code = f"0{code}"

        # Validate format (should be exactly 2 digits)
        if not re.match(r'^\d{2}$', code):
            raise ValidationError(f"Sub-usage code must be 2 digits, got: '{code}'")

        # Sub-usage codes can be 00-99
        if not (0 <= int(code) <= 99):
            raise ValidationError(f"Sub-usage code must be between 00-99, got: '{code}'")

        return code

    def validate_county(self, county: Optional[str]) -> Optional[str]:
        """Validate and normalize county name"""
        if county is None:
            return None

        county = county.strip().upper()

        if not county:
            return None

        # Handle common variations
        county_mappings = {
            'DADE': 'MIAMI-DADE',
            'MIAMI DADE': 'MIAMI-DADE',
            'ST JOHNS': 'ST. JOHNS',
            'ST LUCIE': 'ST. LUCIE',
            'SAINT JOHNS': 'ST. JOHNS',
            'SAINT LUCIE': 'ST. LUCIE'
        }

        if county in county_mappings:
            county = county_mappings[county]

        if county not in self.valid_counties:
            # Try fuzzy matching
            close_matches = [c for c in self.valid_counties if county in c or c in county]
            if close_matches:
                suggested = close_matches[0]
                logger.warning(f"County '{county}' not found. Did you mean '{suggested}'?")
                return suggested
            else:
                raise ValidationError(f"Invalid county: '{county}'. Valid counties: {', '.join(self.valid_counties[:10])}...")

        return county

    def validate_city(self, city: Optional[str]) -> Optional[str]:
        """Validate and normalize city name"""
        if city is None:
            return None

        city = city.strip()

        if not city:
            return None

        # Basic validation - no special characters except spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", city):
            raise ValidationError(f"Invalid city name format: '{city}'")

        # Capitalize properly
        city = ' '.join(word.capitalize() for word in city.split())

        return city

    def validate_zip_code(self, zip_code: Optional[str]) -> Optional[str]:
        """Validate and normalize ZIP code"""
        if zip_code is None:
            return None

        zip_code = str(zip_code).strip()

        if not zip_code:
            return None

        # Remove any non-digits
        zip_code = re.sub(r'\D', '', zip_code)

        # Validate length (5 or 9 digits for ZIP+4)
        if len(zip_code) not in [5, 9]:
            raise ValidationError(f"ZIP code must be 5 or 9 digits, got: '{zip_code}'")

        # For 9-digit codes, format as ZIP+4
        if len(zip_code) == 9:
            zip_code = f"{zip_code[:5]}-{zip_code[5:]}"

        # Basic range check for Florida ZIP codes (32xxx-34xxx)
        if not (32000 <= int(zip_code[:5]) <= 34999):
            logger.warning(f"ZIP code {zip_code[:5]} may not be in Florida")

        return zip_code

    def validate_pagination(self, limit: Optional[int], offset: Optional[int]) -> Tuple[int, int]:
        """Validate and normalize pagination parameters"""
        if limit is None:
            limit = 100
        elif limit < 1:
            raise ValidationError("Limit must be at least 1")
        elif limit > 1000:
            logger.warning(f"Limiting result set from {limit} to 1000 for performance")
            limit = 1000

        if offset is None:
            offset = 0
        elif offset < 0:
            raise ValidationError("Offset cannot be negative")

        return limit, offset

    def validate_sort_parameters(self, sort_by: Optional[str], sort_order: Optional[str]) -> Tuple[str, str]:
        """Validate and normalize sorting parameters"""
        valid_sort_fields = [
            'just_value', 'assessed_value', 'building_sqft', 'land_sqft',
            'year_built', 'sale_date', 'sale_price', 'county', 'city',
            'property_use_code', 'owner_name'
        ]

        if sort_by is None:
            sort_by = 'just_value'
        elif sort_by not in valid_sort_fields:
            raise ValidationError(f"Invalid sort field: '{sort_by}'. Valid fields: {', '.join(valid_sort_fields)}")

        if sort_order is None:
            sort_order = 'desc'
        elif sort_order.lower() not in ['asc', 'desc']:
            raise ValidationError(f"Invalid sort order: '{sort_order}'. Must be 'asc' or 'desc'")
        else:
            sort_order = sort_order.lower()

        return sort_by, sort_order

    def normalize_filters(self, filters) -> 'PropertyFilter':
        """Normalize all filters in a PropertyFilter object"""
        from advanced_property_filters import PropertyFilter

        # Validate and normalize value ranges
        min_value, max_value = self.validate_value_range(filters.min_value, filters.max_value)
        min_assessed, max_assessed = self.validate_value_range(filters.min_assessed_value, filters.max_assessed_value)

        # Validate and normalize size ranges
        min_sqft, max_sqft = self.validate_sqft_range(filters.min_sqft, filters.max_sqft)
        min_land_sqft, max_land_sqft = self.validate_sqft_range(filters.min_land_sqft, filters.max_land_sqft)

        # Validate and normalize year range
        min_year, max_year = self.validate_year_range(filters.min_year_built, filters.max_year_built)

        # Validate and normalize codes
        property_use_code = self.validate_property_use_code(filters.property_use_code)
        sub_usage_code = self.validate_sub_usage_code(filters.sub_usage_code)

        # Validate and normalize location
        county = self.validate_county(filters.county)
        city = self.validate_city(filters.city)
        zip_code = self.validate_zip_code(filters.zip_code)

        # Validate pagination and sorting
        limit, offset = self.validate_pagination(filters.limit, filters.offset)
        sort_by, sort_order = self.validate_sort_parameters(filters.sort_by, filters.sort_order)

        # Create normalized filter object
        return PropertyFilter(
            # Value filters
            min_value=min_value,
            max_value=max_value,
            min_assessed_value=min_assessed,
            max_assessed_value=max_assessed,

            # Size filters
            min_sqft=min_sqft,
            max_sqft=max_sqft,
            min_land_sqft=min_land_sqft,
            max_land_sqft=max_land_sqft,

            # Year filters
            min_year_built=min_year,
            max_year_built=max_year,

            # Property type filters
            property_use_code=property_use_code,
            sub_usage_code=sub_usage_code,
            property_type=filters.property_type,

            # Location filters
            county=county,
            city=city,
            zip_code=zip_code,

            # Other filters (pass through)
            tax_exempt=filters.tax_exempt,
            recently_sold=filters.recently_sold,
            sale_date_from=filters.sale_date_from,
            sale_date_to=filters.sale_date_to,
            has_pool=filters.has_pool,
            waterfront=filters.waterfront,
            gated_community=filters.gated_community,

            # Pagination and sorting
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )

    def get_validation_summary(self, original_filters, normalized_filters) -> Dict[str, Any]:
        """Generate a summary of validation changes"""
        changes = []

        # Compare all fields
        for field in original_filters.__dict__:
            original_val = getattr(original_filters, field)
            normalized_val = getattr(normalized_filters, field)

            if original_val != normalized_val:
                changes.append({
                    'field': field,
                    'original': original_val,
                    'normalized': normalized_val,
                    'reason': self._get_change_reason(field, original_val, normalized_val)
                })

        return {
            'changes_made': len(changes),
            'changes': changes,
            'validation_passed': True
        }

    def _get_change_reason(self, field: str, original: Any, normalized: Any) -> str:
        """Get human-readable reason for validation change"""
        if field.endswith('_code') and isinstance(original, str) and len(original) == 1:
            return "Padded single digit code with leading zero"
        elif field in ['min_value', 'max_value', 'min_sqft', 'max_sqft', 'min_year_built', 'max_year_built']:
            if 'min' in field and 'max' in field:
                return "Swapped min/max values to correct order"
        elif field == 'county':
            return "Normalized county name to standard format"
        elif field == 'city':
            return "Normalized city name capitalization"
        elif field == 'zip_code':
            return "Formatted ZIP code"
        elif field in ['limit', 'offset']:
            return "Applied performance or validation limits"
        elif field in ['sort_by', 'sort_order']:
            return "Applied default sorting parameters"

        return "Normalized value"


def test_validation_system():
    """Test the filter validation system"""
    from advanced_property_filters import PropertyFilter

    validator = FilterValidationSystem()

    print("Testing Filter Validation System")
    print("=" * 50)

    # Test cases with expected corrections
    test_cases = [
        {
            'name': 'Range swapping',
            'filters': PropertyFilter(min_value=500000, max_value=200000, min_sqft=3000, max_sqft=1500),
            'expect_swap': True
        },
        {
            'name': 'Code padding',
            'filters': PropertyFilter(property_use_code='1', sub_usage_code='5'),
            'expect_padding': True
        },
        {
            'name': 'County normalization',
            'filters': PropertyFilter(county='dade', city='miami beach'),
            'expect_county_fix': True
        },
        {
            'name': 'Year validation',
            'filters': PropertyFilter(min_year_built=1750, max_year_built=2030),
            'expect_year_fix': True
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)

        try:
            original = test_case['filters']
            normalized = validator.normalize_filters(original)
            summary = validator.get_validation_summary(original, normalized)

            print(f"[OK] Validation completed")
            print(f"Changes made: {summary['changes_made']}")

            for change in summary['changes']:
                print(f"  {change['field']}: '{change['original']}' -> '{change['normalized']}'")
                print(f"    Reason: {change['reason']}")

        except ValidationError as e:
            print(f"[ERROR] Validation error: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

    print(f"\n[OK] Validation system testing completed")


if __name__ == "__main__":
    test_validation_system()