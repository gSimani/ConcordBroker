"""
Unified Search Service for ConcordBroker
Single source of truth for both autocomplete and grid search results
Ensures consistent filtering and normalization across all property search endpoints
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from supabase import Client
import re
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

class UnifiedSearchService:
    """
    Canonical search service that provides consistent results for both
    autocomplete suggestions and property grid results.
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

        # Cache for performance optimization
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

        # County normalization mapping
        self.county_mapping = {
            'BROWARD': 'BROWARD',
            'MIAMI-DADE': 'MIAMI-DADE',
            'PALM BEACH': 'PALM BEACH',
            'HILLSBOROUGH': 'HILLSBOROUGH',
            'PINELLAS': 'PINELLAS',
            'ORANGE': 'ORANGE',
            'DUVAL': 'DUVAL',
            'LEE': 'LEE',
            'POLK': 'POLK',
            'BREVARD': 'BREVARD'
        }

        # Search scope definitions
        self.search_scopes = {
            'property_address': {
                'table': 'florida_parcels',
                'fields': ['phy_addr1', 'phy_city', 'phy_zipcd'],
                'display_fields': ['parcel_id', 'phy_addr1', 'phy_city', 'phy_zipcd', 'county', 'owner_name', 'property_use', 'just_value']
            },
            'property_owner': {
                'table': 'florida_parcels',
                'fields': ['owner_name'],
                'display_fields': ['parcel_id', 'phy_addr1', 'phy_city', 'county', 'owner_name', 'property_use', 'just_value']
            },
            'company': {
                'table': 'sunbiz_entities',
                'fields': ['entity_name', 'entity_address'],
                'display_fields': ['entity_id', 'entity_name', 'entity_address', 'entity_city', 'entity_state', 'entity_zip', 'status', 'filing_date'],
                'address_mapping_field': 'entity_address'
            },
            'officer': {
                'table': 'sunbiz_officers',
                'fields': ['officer_name', 'officer_address'],
                'display_fields': ['officer_id', 'entity_id', 'officer_name', 'officer_title', 'officer_address', 'officer_city', 'officer_state'],
                'address_mapping_field': 'officer_address'
            }
        }

        # Property use category mapping (using property_use codes from DOR)
        self.use_category_mapping = {
            'RESIDENTIAL': ['1', '2', '3', '4', '5', '6', '7', '8', '9'],
            'COMMERCIAL': ['10', '11', '12', '13', '14', '15', '16', '17', '18', '19'],
            'INDUSTRIAL': ['20', '21', '22', '23', '24', '25', '26', '27', '28', '29'],
            'AGRICULTURAL': ['30', '31', '32', '33', '34', '35', '36', '37', '38', '39'],
            'VACANT': ['80', '81', '82', '83', '84', '85', '86', '87', '88', '89']
        }

    def normalize_query(self, query: str) -> List[str]:
        """
        Normalize search query into tokens for consistent searching.
        """
        if not query:
            return []

        # Convert to uppercase and remove extra spaces
        normalized = query.strip().upper()

        # Split into tokens and filter out empty ones
        tokens = [token.strip() for token in normalized.split() if token.strip()]

        # Remove common noise words but keep meaningful ones
        noise_words = {'THE', 'AND', 'OR', 'OF', 'IN', 'AT', 'TO', 'FOR'}
        filtered_tokens = [token for token in tokens if token not in noise_words]

        return filtered_tokens if filtered_tokens else tokens

    def normalize_county(self, county: Optional[str]) -> Optional[str]:
        """
        Normalize county name for consistent filtering.
        """
        if not county:
            return None

        county_upper = county.strip().upper()
        return self.county_mapping.get(county_upper, county_upper)

    def normalize_use_category(self, use_category: Optional[str]) -> Optional[List[str]]:
        """
        Normalize use category into list of possible matches.
        """
        if not use_category:
            return None

        use_upper = use_category.strip().upper()

        # Check if it's a mapped category
        for category, variations in self.use_category_mapping.items():
            if use_upper in variations or use_upper == category:
                return variations

        # Return as single item list if not found in mapping
        return [use_upper]

    def build_search_query(
        self,
        query: str,
        county: Optional[str] = None,
        use_category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        for_autocomplete: bool = False,
        scope: str = 'property_address'
    ) -> Tuple[Any, int]:
        """
        Build consistent search query for both autocomplete and grid results.

        Args:
            query: Search text
            county: County filter
            use_category: Property use category filter
            limit: Maximum results
            offset: Pagination offset
            for_autocomplete: If True, optimize for autocomplete suggestions

        Returns:
            Tuple of (query_result, total_count)
        """
        start_time = time.time()

        # Validate scope
        if scope not in self.search_scopes:
            scope = 'property_address'

        # Generate cache key
        cache_key = f"{query}:{county}:{use_category}:{limit}:{offset}:{for_autocomplete}:{scope}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            # Normalize inputs
            tokens = self.normalize_query(query)
            normalized_county = self.normalize_county(county) if scope.startswith('property') else None
            normalized_use_categories = self.normalize_use_category(use_category) if scope.startswith('property') else None

            # Get scope configuration
            scope_config = self.search_scopes[scope]
            table_name = scope_config['table']
            search_fields = scope_config['fields']
            display_fields = scope_config['display_fields']

            # Select appropriate fields based on use case
            if for_autocomplete:
                # Use lighter field set for autocomplete
                if len(display_fields) > 8:
                    select_fields = ','.join(display_fields[:8])
                else:
                    select_fields = ','.join(display_fields)
            else:
                # Full fields for grid display
                select_fields = ','.join(display_fields)

            # Start building query
            base_query = self.supabase.table(table_name).select(select_fields)

            # Apply filters only for property searches
            if scope.startswith('property'):
                # Apply county filter first (most selective)
                if normalized_county:
                    base_query = base_query.eq('county', normalized_county)
                    logger.info(f"Applied county filter: {normalized_county}")

                # Apply use category filter
                if normalized_use_categories:
                    if len(normalized_use_categories) == 1:
                        base_query = base_query.eq('property_use', normalized_use_categories[0])
                    else:
                        base_query = base_query.in_('property_use', normalized_use_categories)
                    logger.info(f"Applied use category filter: {normalized_use_categories}")
            elif scope == 'company':
                # For company search, can filter by status if needed
                pass
            elif scope == 'officer':
                # For officer search, can filter by title if needed
                pass

            # Apply text search with AND logic across tokens
            if tokens:
                for token in tokens:
                    # Create OR conditions across searchable fields for each token
                    pattern = f'%{token}%'
                    or_conditions = []

                    # Build OR conditions based on scope's search fields
                    for field in search_fields:
                        or_conditions.append(f"{field}.ilike.{pattern}")

                    # Add parcel_id search for property scopes
                    if scope.startswith('property') and 'parcel_id' not in search_fields:
                        or_conditions.append(f"parcel_id.ilike.{pattern}")

                    if or_conditions:
                        base_query = base_query.or_(','.join(or_conditions))
                        logger.info(f"Applied token filter: {token} on fields: {search_fields}")

            # For autocomplete, prioritize exact matches and limit more aggressively
            if for_autocomplete:
                # Order by relevance based on scope
                if scope == 'property_address':
                    base_query = base_query.order('phy_addr1', desc=False)
                elif scope == 'property_owner':
                    base_query = base_query.order('owner_name', desc=False)
                elif scope == 'company':
                    base_query = base_query.order('entity_name', desc=False)
                elif scope == 'officer':
                    base_query = base_query.order('officer_name', desc=False)
                actual_limit = min(limit, 10)  # Cap autocomplete results
            else:
                # For grid, order by relevance or value
                if scope.startswith('property'):
                    base_query = base_query.order('just_value', desc=True)
                elif scope == 'company':
                    base_query = base_query.order('filing_date', desc=True)
                elif scope == 'officer':
                    base_query = base_query.order('officer_name', desc=False)
                actual_limit = limit

            # Apply pagination
            if offset > 0:
                base_query = base_query.range(offset, offset + actual_limit - 1)
            else:
                base_query = base_query.limit(actual_limit)

            # Execute query
            result = base_query.execute()
            data = result.data or []

            # Get total count for pagination (separate query for performance)
            # Use first column from display_fields for count
            count_column = display_fields[0] if display_fields else '*'
            count_query = self.supabase.table(table_name).select(count_column, count='exact')

            # Apply same filters as main query
            if scope.startswith('property'):
                if normalized_county:
                    count_query = count_query.eq('county', normalized_county)
                if normalized_use_categories:
                    if len(normalized_use_categories) == 1:
                        count_query = count_query.eq('property_use', normalized_use_categories[0])
                    else:
                        count_query = count_query.in_('property_use', normalized_use_categories)

            if tokens:
                for token in tokens:
                    pattern = f'%{token}%'
                    or_conditions = []
                    for field in search_fields:
                        or_conditions.append(f"{field}.ilike.{pattern}")
                    if scope.startswith('property') and 'parcel_id' not in search_fields:
                        or_conditions.append(f"parcel_id.ilike.{pattern}")
                    if or_conditions:
                        count_query = count_query.or_(','.join(or_conditions))

            count_result = count_query.execute()
            total_count = count_result.count or 0

            # Enhance results with metadata
            enhanced_data = self._enhance_results(data, tokens, normalized_county, for_autocomplete, scope)

            execution_time = time.time() - start_time
            logger.info(f"Search executed in {execution_time:.3f}s: {len(enhanced_data)} results, {total_count} total")

            # Cache the result
            result_tuple = (enhanced_data, total_count)
            self._cache_result(cache_key, result_tuple)

            return result_tuple

        except Exception as e:
            logger.error(f"Search query failed: {e}")
            raise Exception(f"Search failed: {str(e)}")

    def _enhance_results(
        self,
        data: List[Dict],
        tokens: List[str],
        county: Optional[str],
        for_autocomplete: bool,
        scope: str = 'property_address'
    ) -> List[Dict]:
        """
        Enhance search results with additional metadata and relevance scoring.
        """
        enhanced = []

        for item in data:
            enhanced_item = item.copy()

            # Add relevance score based on match quality
            relevance_score = self._calculate_relevance(item, tokens, scope)
            enhanced_item['relevance_score'] = relevance_score

            # Add display formatting for autocomplete
            if for_autocomplete:
                enhanced_item['display_text'] = self._format_autocomplete_display(item, scope)
                enhanced_item['search_context'] = {
                    'county': county,
                    'matched_tokens': tokens,
                    'scope': scope
                }

            # Field names are already normalized in the query

            enhanced.append(enhanced_item)

        # Sort by relevance score for autocomplete
        if for_autocomplete:
            enhanced.sort(key=lambda x: x['relevance_score'], reverse=True)

        return enhanced

    def _calculate_relevance(self, item: Dict, tokens: List[str], scope: str = 'property_address') -> float:
        """
        Calculate relevance score for search result.
        """
        score = 0.0

        # Get searchable fields based on scope
        scope_config = self.search_scopes.get(scope, self.search_scopes['property_address'])
        search_fields = scope_config['fields']

        # Map field names to actual values
        field_values = {}
        for field in search_fields:
            field_values[field] = str(item.get(field, '')).upper()

        for token in tokens:
            token_upper = token.upper()

            # Score based on field importance for each scope
            for i, field in enumerate(search_fields):
                field_value = field_values.get(field, '')
                if token_upper in field_value:
                    # Higher score for earlier fields (more important)
                    score += 10.0 / (i + 1)
                    # Bonus for exact match
                    if field_value == token_upper:
                        score += 5.0

        return score

    def _format_autocomplete_display(self, item: Dict, scope: str = 'property_address') -> str:
        """
        Format result for autocomplete display.
        """
        if scope == 'property_address':
            address = item.get('phy_addr1', '')
            city = item.get('phy_city', '')
            county = item.get('county', '')
            parts = [part for part in [address, city, county] if part]
        elif scope == 'property_owner':
            owner = item.get('owner_name', '')
            address = item.get('phy_addr1', '')
            county = item.get('county', '')
            parts = [part for part in [owner, address, county] if part]
        elif scope == 'company':
            name = item.get('entity_name', '')
            address = item.get('entity_address', '')
            city = item.get('entity_city', '')
            parts = [part for part in [name, address, city] if part]
        elif scope == 'officer':
            name = item.get('officer_name', '')
            title = item.get('officer_title', '')
            company = item.get('entity_name', '')
            parts = [part for part in [name, title, company] if part]
        else:
            # Fallback to first few fields
            parts = [str(v) for k, v in list(item.items())[:3] if v]

        return ', '.join(parts)

    def _get_cached_result(self, cache_key: str) -> Optional[Tuple[List[Dict], int]]:
        """
        Get cached search result if available and not expired.
        """
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if time.time() - cached_item['timestamp'] < self._cache_ttl:
                return cached_item['data']
            else:
                del self._cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: Tuple[List[Dict], int]):
        """
        Cache search result with timestamp.
        """
        self._cache[cache_key] = {
            'data': result,
            'timestamp': time.time()
        }

        # Simple cache cleanup - remove oldest entries if cache is too large
        if len(self._cache) > 1000:
            oldest_key = min(self._cache.keys(),
                           key=lambda k: self._cache[k]['timestamp'])
            del self._cache[oldest_key]

    def search_autocomplete(
        self,
        query: str,
        county: Optional[str] = None,
        use_category: Optional[str] = None,
        limit: int = 10,
        scope: str = 'property_address'
    ) -> List[Dict]:
        """
        Search for autocomplete suggestions.
        """
        data, _ = self.build_search_query(
            query=query,
            county=county,
            use_category=use_category,
            limit=limit,
            offset=0,
            for_autocomplete=True,
            scope=scope
        )
        return data

    def search_properties(
        self,
        query: str,
        county: Optional[str] = None,
        use_category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        scope: str = 'property_address'
    ) -> Dict[str, Any]:
        """
        Search for property grid results.
        """
        data, total_count = self.build_search_query(
            query=query,
            county=county,
            use_category=use_category,
            limit=limit,
            offset=offset,
            for_autocomplete=False,
            scope=scope
        )

        return {
            'data': data,
            'pagination': {
                'total': total_count,
                'page': (offset // limit) + 1 if limit > 0 else 1,
                'limit': limit,
                'offset': offset,
                'has_more': (offset + limit) < total_count
            },
            'filters_applied': {
                'query': query,
                'county': county,
                'use_category': use_category,
                'scope': scope
            }
        }

    def search_by_ids(self, parcel_ids: List[str]) -> List[Dict]:
        """
        Search for specific properties by parcel IDs.
        Useful when user selects exact autocomplete suggestion.
        """
        try:
            result = self.supabase.table('florida_parcels').select("""
                parcel_id,
                phy_addr1,
                phy_city,
                phy_zipcd,
                county,
                owner_name,
                property_use,
                just_value,
                land_value,
                building_value,
                taxable_value,
                year_built,
                land_sqft
            """).in_('parcel_id', parcel_ids).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Search by IDs failed: {e}")
            return []

    def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search service statistics.
        """
        return {
            'cache_size': len(self._cache),
            'cache_ttl_seconds': self._cache_ttl,
            'supported_counties': list(self.county_mapping.keys()),
            'supported_use_categories': list(self.use_category_mapping.keys()),
            'supported_scopes': list(self.search_scopes.keys())
        }