"""
Search-related nodes for LangGraph workflows
Reusable nodes for property search operations
"""

import json
import re
from typing import Dict, List, Any, Optional
from langchain_core.messages import HumanMessage, SystemMessage
import logging

logger = logging.getLogger(__name__)

async def parse_user_query(query: str, llm) -> str:
    """Parse user query to understand intent"""
    prompt = f"""
    Analyze this property search query and identify the primary intent:
    Query: {query}
    
    Classify as one of:
    - location_search
    - owner_search
    - value_search
    - type_search
    - complex_search
    
    Return only the classification.
    """
    
    response = await llm.ainvoke([
        SystemMessage(content="You are a query intent classifier."),
        HumanMessage(content=prompt)
    ])
    
    return response.content.strip().lower()

async def extract_search_entities(query: str, llm) -> Dict[str, Any]:
    """Extract entities from search query"""
    prompt = f"""
    Extract search parameters from: {query}
    
    Return as JSON with only these fields if found:
    - city
    - address
    - owner
    - min_value (number)
    - max_value (number)
    - property_type
    - year_built_min (number)
    - year_built_max (number)
    """
    
    response = await llm.ainvoke([
        SystemMessage(content="Extract entities as JSON."),
        HumanMessage(content=prompt)
    ])
    
    try:
        return json.loads(response.content)
    except:
        return {}

def build_database_query(filters: Dict[str, Any], page: int = 1, page_size: int = 20) -> str:
    """Build SQL query from filters"""
    where_clauses = []
    
    if filters.get('city'):
        where_clauses.append(f"phy_city ILIKE '%{filters['city']}%'")
    
    if filters.get('address'):
        where_clauses.append(f"phy_addr1 ILIKE '%{filters['address']}%'")
        
    if filters.get('owner'):
        where_clauses.append(f"own_name ILIKE '%{filters['owner']}%'")
        
    if filters.get('min_value'):
        where_clauses.append(f"jv >= {filters['min_value']}")
        
    if filters.get('max_value'):
        where_clauses.append(f"jv <= {filters['max_value']}")
        
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    offset = (page - 1) * page_size
    
    return f"""
        SELECT * FROM florida_parcels
        WHERE {where_clause}
        LIMIT {page_size}
        OFFSET {offset}
    """

async def execute_search(supabase_client, filters: Dict[str, Any], page: int = 1, page_size: int = 20) -> Dict:
    """Execute property search against database"""
    try:
        query = supabase_client.table('florida_parcels').select('*')
        
        if filters.get('city'):
            query = query.ilike('phy_city', f"%{filters['city']}%")
        
        if filters.get('address'):
            query = query.ilike('phy_addr1', f"%{filters['address']}%")
            
        if filters.get('owner'):
            query = query.ilike('own_name', f"%{filters['owner']}%")
            
        if filters.get('min_value'):
            query = query.gte('jv', filters['min_value'])
            
        if filters.get('max_value'):
            query = query.lte('jv', filters['max_value'])
            
        offset = (page - 1) * page_size
        response = query.range(offset, offset + page_size - 1).execute()
        
        return {
            'results': response.data if response.data else [],
            'count': len(response.data) if response.data else 0
        }
    except Exception as e:
        logger.error(f"Search execution error: {e}")
        return {'results': [], 'count': 0}

def enrich_results(results: List[Dict], enrichment_data: Optional[Dict] = None) -> List[Dict]:
    """Enrich search results with additional data"""
    enriched = []
    
    for result in results:
        # Calculate confidence score
        confidence = 0.5
        if result.get('own_name'):
            confidence += 0.2
        if result.get('jv'):
            confidence += 0.15
        if result.get('act_yr_blt'):
            confidence += 0.15
            
        result['confidence_score'] = confidence
        
        # Add enrichment data if available
        if enrichment_data:
            parcel_id = result.get('parcel_id')
            if parcel_id in enrichment_data:
                result.update(enrichment_data[parcel_id])
                
        enriched.append(result)
        
    return enriched

def format_final_results(results: List[Dict]) -> List[Dict]:
    """Format results for frontend consumption"""
    formatted = []
    
    for r in results:
        formatted.append({
            'id': r.get('id'),
            'parcel_id': r.get('parcel_id'),
            'address': r.get('phy_addr1'),
            'city': r.get('phy_city'),
            'zip': r.get('phy_zipcd'),
            'owner': r.get('own_name'),
            'value': r.get('jv'),
            'taxable_value': r.get('tv_sd'),
            'land_value': r.get('lnd_val'),
            'building_sqft': r.get('tot_lvg_area'),
            'land_sqft': r.get('lnd_sqfoot'),
            'year_built': r.get('act_yr_blt'),
            'property_use': r.get('dor_uc'),
            'confidence': r.get('confidence_score', 0.5)
        })
        
    return formatted

def generate_refinement_suggestions(filters: Dict[str, Any], result_count: int) -> List[str]:
    """Generate suggestions for refining search"""
    suggestions = []
    
    if result_count == 0:
        if filters.get('min_value') and filters.get('max_value'):
            suggestions.append("Try expanding your price range")
            
        if filters.get('city'):
            suggestions.append("Try searching nearby cities or remove city filter")
            
        if filters.get('owner'):
            suggestions.append("Try variations of the owner name")
            
        if not suggestions:
            suggestions = [
                "Broaden your search criteria",
                "Check spelling of names and locations",
                "Remove some filters"
            ]
    elif result_count > 100:
        suggestions.append("Add more filters to narrow results")
        
    return suggestions