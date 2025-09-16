#!/usr/bin/env python3
"""
Advanced Property Search Filters
Optimized database filtering system for property search with efficient queries
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from supabase import create_client, Client
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PropertyFilter:
    """Data class for property filter parameters"""
    # Value filters
    min_value: Optional[int] = None
    max_value: Optional[int] = None

    # Size filters
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None

    # Land filters
    min_land_sqft: Optional[int] = None
    max_land_sqft: Optional[int] = None

    # Year filters
    min_year_built: Optional[int] = None
    max_year_built: Optional[int] = None

    # Property type filters
    property_use_code: Optional[str] = None
    sub_usage_code: Optional[str] = None
    property_type: Optional[str] = None

    # Location filters
    county: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None

    # Tax and assessment filters
    min_assessed_value: Optional[int] = None
    max_assessed_value: Optional[int] = None
    tax_exempt: Optional[bool] = None

    # Sales history filters
    recently_sold: Optional[bool] = None
    sale_date_from: Optional[str] = None
    sale_date_to: Optional[str] = None

    # Additional filters
    has_pool: Optional[bool] = None
    waterfront: Optional[bool] = None
    gated_community: Optional[bool] = None

    # Pagination
    limit: int = 100
    offset: int = 0

    # Sorting
    sort_by: str = 'just_value'
    sort_order: str = 'desc'  # 'asc' or 'desc'

class AdvancedPropertySearchEngine:
    """High-performance property search engine with optimized filtering"""

    def __init__(self):
        self.supabase = self._initialize_supabase()
        self.property_use_codes = self._load_property_use_codes()
        self.filter_cache = {}

    def _initialize_supabase(self) -> Client:
        """Initialize Supabase client"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

            if not url or not key:
                raise ValueError("Missing Supabase credentials")

            return create_client(url, key)
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            raise

    def _load_property_use_codes(self) -> Dict[str, str]:
        """Load property use codes for validation and filtering"""
        return {
            # Residential
            '01': 'Single Family',
            '02': 'Mobile Home',
            '03': 'Multi-Family',
            '04': 'Condominium',
            '05': 'Cooperative',
            '06': 'Retirement Home',
            '07': 'Manufactured Home',
            '08': 'Miscellaneous Residential',
            '09': 'Multi-Family 10+ Units',

            # Commercial
            '10': 'Vacant Commercial',
            '11': 'Stores/Office, One Story',
            '12': 'Mixed Use Commercial',
            '13': 'Department Store',
            '14': 'Supermarket',
            '15': 'Regional Shopping Center',
            '16': 'Community Shopping Center',
            '17': 'Office Building, Multi-Story',
            '18': 'Office Building, One Story',
            '19': 'Professional Service Building',

            # Industrial
            '20': 'Vacant Industrial',
            '21': 'Light Manufacturing',
            '22': 'Heavy Industrial',
            '23': 'Mini Warehouse',
            '24': 'Warehouse, Distribution Terminal',
            '25': 'Open Storage',
            '26': 'Improved Agricultural',
            '27': 'Unimproved Agricultural',

            # Special Use
            '30': 'Institutional',
            '31': 'Hospitals, Nursing Homes',
            '32': 'Educational',
            '33': 'Religious',
            '34': 'Cultural, Entertainment, Recreational',
            '35': 'Governmental',
            '36': 'Forest, Parks and Recreational',
            '37': 'Clubs and Lodges',
            '38': 'Cemeteries and Crematories',
            '39': 'Utilities, Mining, etc.'
        }

    def build_query_filters(self, filters: PropertyFilter) -> Dict[str, Any]:
        """Build efficient database query filters"""
        query_filters = {}

        # Value range filters
        if filters.min_value is not None:
            query_filters['just_value__gte'] = filters.min_value
        if filters.max_value is not None:
            query_filters['just_value__lte'] = filters.max_value

        # Square footage filters
        if filters.min_sqft is not None:
            query_filters['building_sqft__gte'] = filters.min_sqft
        if filters.max_sqft is not None:
            query_filters['building_sqft__lte'] = filters.max_sqft

        # Land square footage filters
        if filters.min_land_sqft is not None:
            query_filters['land_sqft__gte'] = filters.min_land_sqft
        if filters.max_land_sqft is not None:
            query_filters['land_sqft__lte'] = filters.max_land_sqft

        # Year built filters
        if filters.min_year_built is not None:
            query_filters['year_built__gte'] = filters.min_year_built
        if filters.max_year_built is not None:
            query_filters['year_built__lte'] = filters.max_year_built

        # Property type filters
        if filters.property_use_code:
            query_filters['property_use_code__eq'] = filters.property_use_code
        if filters.sub_usage_code:
            query_filters['sub_usage_code__eq'] = filters.sub_usage_code

        # Location filters
        if filters.county:
            query_filters['county__ilike'] = f"%{filters.county}%"
        if filters.city:
            query_filters['city__ilike'] = f"%{filters.city}%"
        if filters.zip_code:
            query_filters['zip_code__eq'] = filters.zip_code

        # Assessment filters
        if filters.min_assessed_value is not None:
            query_filters['assessed_value__gte'] = filters.min_assessed_value
        if filters.max_assessed_value is not None:
            query_filters['assessed_value__lte'] = filters.max_assessed_value

        # Boolean filters
        if filters.tax_exempt is not None:
            query_filters['tax_exempt__eq'] = filters.tax_exempt
        if filters.has_pool is not None:
            query_filters['pool__eq'] = filters.has_pool
        if filters.waterfront is not None:
            query_filters['waterfront__eq'] = filters.waterfront

        return query_filters

    def normalize_filters(self, filters: PropertyFilter) -> PropertyFilter:
        """Normalize filters using validation system"""
        from filter_validation_system import FilterValidationSystem

        validator = FilterValidationSystem()
        return validator.normalize_filters(filters)

    def build_query(self, filters: PropertyFilter) -> Tuple[str, Dict]:
        """Build query with validation - exposed for testing"""
        return self.build_optimized_query(filters)

    def build_optimized_query(self, filters: PropertyFilter) -> Tuple[str, Dict]:
        """Build optimized SQL query with proper indexing"""
        base_query = """
        SELECT
            parcel_id,
            owner_name,
            phy_addr1,
            phy_addr2,
            city,
            state,
            zip_code,
            county,
            just_value,
            assessed_value,
            land_value,
            building_value,
            land_sqft,
            building_sqft,
            year_built,
            property_use_code,
            sub_usage_code,
            sale_date,
            sale_price,
            tax_exempt
        FROM florida_parcels
        WHERE 1=1
        """

        conditions = []
        params = {}

        # Value filters with optimized ranges
        if filters.min_value is not None:
            conditions.append("just_value >= %(min_value)s")
            params['min_value'] = filters.min_value
        if filters.max_value is not None:
            conditions.append("just_value <= %(max_value)s")
            params['max_value'] = filters.max_value

        # Size filters
        if filters.min_sqft is not None:
            conditions.append("building_sqft >= %(min_sqft)s")
            params['min_sqft'] = filters.min_sqft
        if filters.max_sqft is not None:
            conditions.append("building_sqft <= %(max_sqft)s")
            params['max_sqft'] = filters.max_sqft

        # Land size filters
        if filters.min_land_sqft is not None:
            conditions.append("land_sqft >= %(min_land_sqft)s")
            params['min_land_sqft'] = filters.min_land_sqft
        if filters.max_land_sqft is not None:
            conditions.append("land_sqft <= %(max_land_sqft)s")
            params['max_land_sqft'] = filters.max_land_sqft

        # Year built filters
        if filters.min_year_built is not None:
            conditions.append("year_built >= %(min_year_built)s")
            params['min_year_built'] = filters.min_year_built
        if filters.max_year_built is not None:
            conditions.append("year_built <= %(max_year_built)s")
            params['max_year_built'] = filters.max_year_built

        # Property type filters
        if filters.property_use_code:
            conditions.append("property_use_code = %(property_use_code)s")
            params['property_use_code'] = filters.property_use_code
        if filters.sub_usage_code:
            conditions.append("sub_usage_code = %(sub_usage_code)s")
            params['sub_usage_code'] = filters.sub_usage_code

        # Location filters
        if filters.county:
            conditions.append("UPPER(county) = UPPER(%(county)s)")
            params['county'] = filters.county
        if filters.city:
            conditions.append("UPPER(city) LIKE UPPER(%(city)s)")
            params['city'] = f"%{filters.city}%"
        if filters.zip_code:
            conditions.append("zip_code = %(zip_code)s")
            params['zip_code'] = filters.zip_code

        # Assessment filters
        if filters.min_assessed_value is not None:
            conditions.append("assessed_value >= %(min_assessed_value)s")
            params['min_assessed_value'] = filters.min_assessed_value
        if filters.max_assessed_value is not None:
            conditions.append("assessed_value <= %(max_assessed_value)s")
            params['max_assessed_value'] = filters.max_assessed_value

        # Boolean filters
        if filters.tax_exempt is not None:
            conditions.append("tax_exempt = %(tax_exempt)s")
            params['tax_exempt'] = filters.tax_exempt

        # Sales history filters
        if filters.recently_sold:
            conditions.append("sale_date >= %(recent_date)s")
            params['recent_date'] = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

        if filters.sale_date_from:
            conditions.append("sale_date >= %(sale_date_from)s")
            params['sale_date_from'] = filters.sale_date_from
        if filters.sale_date_to:
            conditions.append("sale_date <= %(sale_date_to)s")
            params['sale_date_to'] = filters.sale_date_to

        # Add conditions to query
        if conditions:
            base_query += " AND " + " AND ".join(conditions)

        # Add sorting
        order_direction = "DESC" if filters.sort_order.lower() == 'desc' else "ASC"
        base_query += f" ORDER BY {filters.sort_by} {order_direction}"

        # Add pagination
        base_query += f" LIMIT {filters.limit} OFFSET {filters.offset}"

        return base_query, params

    def search_properties(self, filters: PropertyFilter) -> Dict[str, Any]:
        """Execute optimized property search"""
        try:
            start_time = datetime.now()

            # Normalize and validate filters first
            normalized_filters = self.normalize_filters(filters)

            # Build optimized query
            query, params = self.build_optimized_query(normalized_filters)

            # Execute query (using direct SQL for performance)
            # Note: In production, use parameterized queries through Supabase RPC
            logger.info(f"Executing property search with {len(params)} filters")

            # For now, simulate the search with sample data structure
            # In production, this would execute the SQL query
            results = self._execute_search_query(query, params)

            execution_time = (datetime.now() - start_time).total_seconds()

            # Process and enhance results
            enhanced_results = self._enhance_results(results)

            return {
                'success': True,
                'data': enhanced_results,
                'metadata': {
                    'total_count': len(enhanced_results),
                    'execution_time_seconds': execution_time,
                    'filters_applied': self._get_applied_filters(filters),
                    'query_hash': hash(query)
                }
            }

        except Exception as e:
            logger.error(f"Property search failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'data': []
            }

    def _execute_search_query(self, query: str, params: Dict) -> List[Dict]:
        """Execute the search query (placeholder for actual DB execution)"""
        # In production, this would execute the actual SQL query
        # For now, return sample structure based on the filter requirements

        sample_properties = [
            {
                'parcel_id': '474131031040',
                'owner_name': 'SAMPLE OWNER LLC',
                'phy_addr1': '123 SAMPLE ST',
                'phy_addr2': '',
                'city': 'MIAMI',
                'state': 'FL',
                'zip_code': '33101',
                'county': 'BROWARD',
                'just_value': 450000,
                'assessed_value': 430000,
                'land_value': 200000,
                'building_value': 250000,
                'land_sqft': 7500,
                'building_sqft': 2200,
                'year_built': 1995,
                'property_use_code': '01',
                'sub_usage_code': '00',
                'sale_date': '2023-06-15',
                'sale_price': 425000,
                'tax_exempt': False
            }
        ]

        return sample_properties

    def _enhance_results(self, results: List[Dict]) -> List[Dict]:
        """Enhance search results with additional computed fields"""
        enhanced = []

        for prop in results:
            enhanced_prop = prop.copy()

            # Add computed fields
            enhanced_prop['property_use_description'] = self.property_use_codes.get(
                prop.get('property_use_code', ''), 'Unknown'
            )

            # Calculate price per square foot
            if prop.get('building_sqft') and prop.get('just_value'):
                enhanced_prop['price_per_sqft'] = round(
                    prop['just_value'] / prop['building_sqft'], 2
                )

            # Calculate land price per square foot
            if prop.get('land_sqft') and prop.get('land_value'):
                enhanced_prop['land_price_per_sqft'] = round(
                    prop['land_value'] / prop['land_sqft'], 2
                )

            # Add assessment ratio
            if prop.get('assessed_value') and prop.get('just_value'):
                enhanced_prop['assessment_ratio'] = round(
                    prop['assessed_value'] / prop['just_value'], 3
                )

            # Format addresses
            enhanced_prop['full_address'] = self._format_address(prop)

            enhanced.append(enhanced_prop)

        return enhanced

    def _format_address(self, prop: Dict) -> str:
        """Format property address"""
        parts = []

        if prop.get('phy_addr1'):
            parts.append(prop['phy_addr1'])
        if prop.get('phy_addr2'):
            parts.append(prop['phy_addr2'])
        if prop.get('city'):
            parts.append(prop['city'])
        if prop.get('state'):
            parts.append(prop['state'])
        if prop.get('zip_code'):
            parts.append(prop['zip_code'])

        return ', '.join(parts)

    def _get_applied_filters(self, filters: PropertyFilter) -> Dict[str, Any]:
        """Get summary of applied filters"""
        applied = {}

        for field, value in filters.__dict__.items():
            if value is not None and field not in ['limit', 'offset', 'sort_by', 'sort_order']:
                applied[field] = value

        return applied

    def get_filter_suggestions(self, partial_filters: PropertyFilter) -> Dict[str, List]:
        """Get suggestions for filter values based on existing data"""
        suggestions = {
            'property_use_codes': list(self.property_use_codes.keys()),
            'property_use_descriptions': list(self.property_use_codes.values()),
            'common_cities': ['Miami', 'Fort Lauderdale', 'Hollywood', 'Pembroke Pines', 'Coral Springs'],
            'value_ranges': [
                {'label': 'Under $200K', 'min': 0, 'max': 200000},
                {'label': '$200K - $500K', 'min': 200000, 'max': 500000},
                {'label': '$500K - $1M', 'min': 500000, 'max': 1000000},
                {'label': 'Over $1M', 'min': 1000000, 'max': None}
            ],
            'sqft_ranges': [
                {'label': 'Under 1,000 sq ft', 'min': 0, 'max': 1000},
                {'label': '1,000 - 2,000 sq ft', 'min': 1000, 'max': 2000},
                {'label': '2,000 - 3,000 sq ft', 'min': 2000, 'max': 3000},
                {'label': 'Over 3,000 sq ft', 'min': 3000, 'max': None}
            ]
        }

        return suggestions

    def optimize_filters_for_performance(self, filters: PropertyFilter) -> PropertyFilter:
        """Optimize filters for database performance"""
        # Add database indexes recommendations
        optimized = filters

        # Suggest limiting very broad searches
        if not any([
            filters.min_value, filters.max_value,
            filters.county, filters.city,
            filters.property_use_code
        ]):
            # Add a reasonable value range for performance
            optimized.max_value = 2000000  # $2M max for broad searches

        return optimized

def create_property_search_api():
    """Create FastAPI endpoints for property search"""
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Advanced Property Search API")
    search_engine = AdvancedPropertySearchEngine()

    @app.post("/search/properties")
    async def search_properties(filters: PropertyFilter):
        """Advanced property search with filters"""
        try:
            # Optimize filters for performance
            optimized_filters = search_engine.optimize_filters_for_performance(filters)

            # Execute search
            results = search_engine.search_properties(optimized_filters)

            return JSONResponse(content=results)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/search/suggestions")
    async def get_filter_suggestions():
        """Get filter suggestions and property use codes"""
        suggestions = search_engine.get_filter_suggestions(PropertyFilter())
        return JSONResponse(content=suggestions)

    return app

# Performance testing and validation
def test_filter_performance():
    """Test filter performance with various scenarios"""
    search_engine = AdvancedPropertySearchEngine()

    test_cases = [
        # Basic value range
        PropertyFilter(min_value=200000, max_value=500000),

        # Size and location
        PropertyFilter(
            min_sqft=1500,
            max_sqft=3000,
            county='BROWARD'
        ),

        # Property type specific
        PropertyFilter(
            property_use_code='01',  # Single Family
            min_year_built=2000
        ),

        # Complex multi-filter
        PropertyFilter(
            min_value=300000,
            max_value=800000,
            min_sqft=1800,
            property_use_code='01',
            county='BROWARD',
            recently_sold=True
        )
    ]

    results = []
    for i, filters in enumerate(test_cases, 1):
        print(f"Testing filter case {i}...")
        result = search_engine.search_properties(filters)
        results.append({
            'case': i,
            'execution_time': result['metadata']['execution_time_seconds'],
            'filters_count': len(result['metadata']['filters_applied']),
            'results_count': result['metadata']['total_count']
        })

    # Create performance report
    df = pd.DataFrame(results)
    print("\nPerformance Test Results:")
    print(df.to_string(index=False))

    return df

if __name__ == "__main__":
    # Run performance tests
    print("Advanced Property Search Engine")
    print("=" * 50)

    test_filter_performance()

    # Example usage
    search_engine = AdvancedPropertySearchEngine()

    # Sample search
    sample_filters = PropertyFilter(
        min_value=100000,
        max_value=750000,
        property_use_code='01',
        county='BROWARD'
    )

    results = search_engine.search_properties(sample_filters)
    print(f"\nSample search results: {results['metadata']['total_count']} properties found")
    print(f"Execution time: {results['metadata']['execution_time_seconds']:.3f} seconds")