"""
Validation engine for comparing UI displayed values with database values
"""
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
import re
from datetime import datetime
from .config import config
from .schema_mapper import SchemaMapper
from .firecrawl_scraper import FirecrawlScraper


class FieldValidator:
    """Validates that UI fields display correct database values"""

    def __init__(self):
        self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.schema_mapper = SchemaMapper()
        self.scraper = FirecrawlScraper()

    async def validate_page(
        self,
        page_url: str,
        html: str,
        property_id: Optional[str] = None
    ) -> Dict:
        """Validate all fields on a single page"""

        # Extract property ID from URL if not provided
        if not property_id:
            property_id = self.scraper.extract_property_id(page_url)

        if not property_id:
            return {
                'page_url': page_url,
                'error': 'Could not extract property ID from URL',
                'validations': []
            }

        # Extract label-field pairs from HTML
        pairs = self.scraper.extract_label_field_pairs(html, page_url)

        # Fetch property data from database
        db_data = await self._fetch_property_data(property_id)

        if not db_data:
            return {
                'page_url': page_url,
                'property_id': property_id,
                'error': 'Property not found in database',
                'validations': []
            }

        # Validate each pair
        validations = []
        for pair in pairs:
            validation = await self._validate_pair(pair, db_data)
            validations.append(validation)

        # Calculate summary statistics
        summary = self._calculate_summary(validations)

        return {
            'page_url': page_url,
            'property_id': property_id,
            'validations': validations,
            'summary': summary
        }

    async def _fetch_property_data(self, property_id: str) -> Optional[Dict]:
        """Fetch property data from database"""
        try:
            result = self.supabase.table('florida_parcels') \
                .select('*') \
                .eq('parcel_id', property_id) \
                .limit(1) \
                .execute()

            if result.data and len(result.data) > 0:
                return result.data[0]

        except Exception as e:
            print(f"Error fetching property {property_id}: {e}")

        return None

    async def _validate_pair(
        self,
        pair: Dict,
        db_data: Dict
    ) -> Dict:
        """Validate a single label-field pair"""

        label = pair['label']
        displayed_value = pair['value']
        page_url = pair['page_url']

        # Map label to database field
        db_field, confidence, match_type = self.schema_mapper.map_label_to_field(label)

        if not db_field:
            return {
                **pair,
                'status': 'unmapped',
                'db_field': None,
                'expected_value': None,
                'confidence': 0,
                'match_type': 'no_match',
                'issue': f"Could not map label '{label}' to database field"
            }

        # Get expected value from database
        expected_value = db_data.get(db_field)

        # Normalize and compare values
        match_result = self._compare_values(
            displayed_value,
            expected_value,
            pair['data_type']
        )

        return {
            **pair,
            'db_field': db_field,
            'expected_value': expected_value,
            'confidence': confidence,
            'match_type': match_type,
            **match_result
        }

    def _compare_values(
        self,
        displayed: str,
        expected: any,
        data_type: str
    ) -> Dict:
        """Compare displayed value with expected database value"""

        # Handle None/null cases
        if expected is None:
            if not displayed or displayed.lower() in ['n/a', 'none', '-', '']:
                return {'status': 'match', 'issue': None}
            else:
                return {
                    'status': 'mismatch',
                    'issue': f"Database has NULL but UI shows '{displayed}'"
                }

        # Normalize both values
        displayed_norm = self._normalize_value(displayed, data_type)
        expected_norm = self._normalize_value(str(expected), data_type)

        # Compare normalized values
        if displayed_norm == expected_norm:
            return {'status': 'match', 'issue': None}

        # Check for formatting differences
        if self._is_formatting_difference(displayed_norm, expected_norm, data_type):
            return {
                'status': 'match_with_formatting',
                'issue': f"Values match but formatting differs ('{displayed}' vs '{expected}')"
            }

        # Values don't match
        return {
            'status': 'mismatch',
            'issue': f"UI shows '{displayed}' but database has '{expected}'"
        }

    def _normalize_value(self, value: str, data_type: str) -> str:
        """Normalize a value for comparison"""
        if not value:
            return ''

        # Remove common formatting
        normalized = str(value).strip()

        if config.NORMALIZE_CASE:
            normalized = normalized.upper()

        if config.NORMALIZE_WHITESPACE:
            normalized = re.sub(r'\s+', ' ', normalized)

        # Type-specific normalization
        if data_type in ['currency', 'integer', 'decimal']:
            # Remove currency symbols and commas
            normalized = re.sub(r'[$,\s]', '', normalized)

        elif data_type in ['date', 'date_iso']:
            # Normalize date format
            normalized = self._normalize_date(normalized)

        return normalized

    def _normalize_date(self, date_str: str) -> str:
        """Normalize date to YYYY-MM-DD format"""
        # Try common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%m-%d-%Y',
            '%d-%m-%Y'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return date_str

    def _is_formatting_difference(
        self,
        val1: str,
        val2: str,
        data_type: str
    ) -> bool:
        """Check if difference is just formatting"""

        # For numbers, check if numeric values are equal
        if data_type in ['currency', 'integer', 'decimal']:
            try:
                num1 = float(val1)
                num2 = float(val2)
                return abs(num1 - num2) < 0.01  # Allow for rounding
            except ValueError:
                return False

        # For text, check case-insensitive equality
        if data_type == 'text':
            return val1.upper() == val2.upper()

        return False

    def _calculate_summary(self, validations: List[Dict]) -> Dict:
        """Calculate summary statistics for validations"""
        total = len(validations)
        if total == 0:
            return {
                'total_fields': 0,
                'matched': 0,
                'mismatched': 0,
                'unmapped': 0,
                'match_percentage': 0
            }

        matched = sum(1 for v in validations if v['status'] in ['match', 'match_with_formatting'])
        mismatched = sum(1 for v in validations if v['status'] == 'mismatch')
        unmapped = sum(1 for v in validations if v['status'] == 'unmapped')

        return {
            'total_fields': total,
            'matched': matched,
            'mismatched': mismatched,
            'unmapped': unmapped,
            'match_percentage': round((matched / total) * 100, 2) if total > 0 else 0
        }

    async def validate_all_properties(
        self,
        property_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """Validate specific properties or all properties"""

        if property_ids:
            # Validate specific properties
            results = []
            for prop_id in property_ids:
                # Would need to know the URL pattern for each property
                # This is a simplified version
                page_url = f"{config.TARGET_SITE_URL}/property/{prop_id}"
                # In real implementation, would fetch HTML for this URL
                result = await self.validate_page(page_url, "", prop_id)
                results.append(result)

            return results

        else:
            # Crawl and validate all pages
            pages = await self.scraper.crawl_website(config.TARGET_SITE_URL)

            results = []
            for page in pages:
                property_id = self.scraper.extract_property_id(page['url'])
                if property_id:
                    result = await self.validate_page(
                        page['url'],
                        page['html'],
                        property_id
                    )
                    results.append(result)

            return results
