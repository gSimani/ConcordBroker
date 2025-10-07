"""
Database schema extraction and field mapping
"""
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
from rapidfuzz import fuzz, process
import re
from .config import config


class SchemaMapper:
    """Maps UI labels to database schema fields"""

    def __init__(self):
        self.supabase: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        self.schema_cache: Dict[str, List[Dict]] = {}
        self.field_mappings: Dict[str, str] = config.LABEL_MAPPINGS.copy()

    async def extract_schema(self) -> Dict[str, List[Dict]]:
        """Extract database schema from Supabase"""
        schema = {}

        for table_name in config.VALIDATION_TABLES:
            # Query information schema for column details
            result = self.supabase.rpc(
                'get_table_columns',
                {'table_name': table_name}
            ).execute()

            if result.data:
                schema[table_name] = result.data
            else:
                # Fallback: query the table directly to infer schema
                sample = self.supabase.table(table_name).select('*').limit(1).execute()
                if sample.data:
                    columns = [
                        {
                            'column_name': key,
                            'data_type': type(value).__name__,
                            'is_nullable': True
                        }
                        for key, value in sample.data[0].items()
                    ]
                    schema[table_name] = columns

        self.schema_cache = schema
        return schema

    def map_label_to_field(
        self,
        label: str,
        table_name: str = "florida_parcels",
        confidence_threshold: int = None
    ) -> Tuple[Optional[str], int, str]:
        """
        Map a UI label to a database field

        Returns:
            Tuple of (field_name, confidence_score, match_type)
        """
        threshold = confidence_threshold or config.FUZZY_MATCH_THRESHOLD

        # Normalize label
        normalized_label = self._normalize_label(label)

        # 1. Check exact mapping from config
        if normalized_label in self.field_mappings:
            return (self.field_mappings[normalized_label], 100, "exact_config")

        # 2. Check schema cache for the table
        if table_name not in self.schema_cache:
            return (None, 0, "no_schema")

        columns = [col['column_name'] for col in self.schema_cache[table_name]]

        # 3. Try exact match (case-insensitive)
        for col in columns:
            if normalized_label == col.lower():
                return (col, 100, "exact_match")

        # 4. Try fuzzy matching
        best_match = process.extractOne(
            normalized_label,
            columns,
            scorer=fuzz.ratio,
            score_cutoff=threshold
        )

        if best_match:
            field_name, score, _ = best_match
            return (field_name, score, "fuzzy_match")

        # 5. Try pattern-based matching
        pattern_match = self._pattern_match(normalized_label, columns)
        if pattern_match:
            return (pattern_match, 75, "pattern_match")

        return (None, 0, "no_match")

    def _normalize_label(self, label: str) -> str:
        """Normalize a label for matching"""
        # Remove special characters
        label = re.sub(r'[^a-zA-Z0-9\s]', '', label)
        # Convert to lowercase
        label = label.lower().strip()
        # Replace spaces with underscores
        label = re.sub(r'\s+', '_', label)
        return label

    def _pattern_match(self, label: str, columns: List[str]) -> Optional[str]:
        """Try pattern-based matching for common abbreviations"""
        patterns = {
            r'.*addr.*': ['phy_addr1', 'property_address_street', 'address'],
            r'.*own.*': ['owner_name', 'own_name', 'owner'],
            r'.*val.*': ['jv', 'market_value', 'just_value', 'lnd_val', 'av_sd'],
            r'.*tax.*': ['tax_amount', 'tv_sd', 'taxable_value'],
            r'.*bldg.*|.*building.*': ['bldg_val', 'building_value'],
            r'.*land.*': ['lnd_val', 'lnd_sqfoot', 'land_value'],
            r'.*year.*built.*': ['act_yr_blt', 'eff_yr_blt', 'year_built'],
            r'.*bed.*': ['bedroom_cnt', 'bedrooms'],
            r'.*bath.*': ['bathroom_cnt', 'bathrooms'],
            r'.*sqf.*|.*area.*': ['tot_lvg_area', 'lnd_sqfoot', 'living_area'],
            r'.*parcel.*|.*folio.*': ['parcel_id', 'folio'],
            r'.*sale.*price.*': ['sale_prc1', 'sale_price'],
            r'.*sale.*date.*': ['sale_date', 'sale_yr1', 'sale_mo1'],
        }

        for pattern, candidate_fields in patterns.items():
            if re.match(pattern, label):
                # Return first matching column from candidates
                for field in candidate_fields:
                    if field in columns:
                        return field

        return None

    def infer_label_from_field(self, field_name: str) -> str:
        """Generate a human-readable label from a database field name"""
        # Check reverse mapping
        for label, db_field in self.field_mappings.items():
            if db_field == field_name:
                return label.title()

        # Generate from field name
        # Convert snake_case to Title Case
        label = field_name.replace('_', ' ').title()

        # Handle common abbreviations
        abbreviations = {
            'Phy': 'Physical',
            'Addr': 'Address',
            'Own': 'Owner',
            'Jv': 'Just Value',
            'Av': 'Assessed Value',
            'Tv': 'Taxable Value',
            'Lnd': 'Land',
            'Bldg': 'Building',
            'Sqfoot': 'Square Feet',
            'Cnt': 'Count',
            'Yr': 'Year',
            'Blt': 'Built',
            'Dor': 'DOR',
            'Uc': 'Use Code',
            'Prc': 'Price',
            'No Res Unts': 'Number of Units',
            'Tot Lvg Area': 'Total Living Area',
            'Eff': 'Effective',
            'Act': 'Actual',
            'Zipcd': 'Zip Code',
            'Or': 'Official Records',
            'Cin': 'Clerk Instrument Number'
        }

        for abbr, full in abbreviations.items():
            label = label.replace(abbr, full)

        return label

    def get_field_type(self, field_name: str, table_name: str = "florida_parcels") -> Optional[str]:
        """Get the data type of a database field"""
        if table_name not in self.schema_cache:
            return None

        for col in self.schema_cache[table_name]:
            if col['column_name'] == field_name:
                return col.get('data_type', 'unknown')

        return None

    def add_custom_mapping(self, label: str, field_name: str):
        """Add a custom label-to-field mapping"""
        normalized_label = self._normalize_label(label)
        self.field_mappings[normalized_label] = field_name
