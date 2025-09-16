"""
Florida Business Search API - SQL + RAG Hybrid System
Combines structured SQL queries with semantic search capabilities
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import asyncio
from datetime import datetime, timedelta

import openai
from supabase import create_client, Client
from dotenv import load_dotenv
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

@dataclass
class SearchResult:
    entity_id: str
    business_name: str
    dba_name: Optional[str]
    business_city: str
    business_county: str
    entity_type: str
    formation_date: Optional[str]
    phone_numbers: Optional[str]
    email_addresses: Optional[str]
    relevance_score: float
    match_type: str  # 'exact', 'fuzzy', 'semantic'

class FloridaBusinessSearch:
    def __init__(self):
        """Initialize the hybrid search system"""
        # Supabase connection
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # OpenAI for embeddings
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Search configuration
        self.embedding_model = "text-embedding-3-small"
        self.max_sql_results = 100
        self.max_rag_results = 50
        
    async def search_businesses(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        search_type: str = "hybrid"  # 'sql', 'semantic', 'hybrid'
    ) -> List[SearchResult]:
        """
        Main search interface - combines SQL and semantic search
        """
        if search_type == "sql":
            return await self.sql_search(query, filters)
        elif search_type == "semantic":
            return await self.semantic_search(query, filters)
        else:  # hybrid
            return await self.hybrid_search(query, filters)

    async def sql_search(self, query: str, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """
        Structured SQL search for exact matches and filters
        """
        results = []
        
        try:
            # Build base query
            select_query = self.supabase.table('florida_active_entities_with_contacts').select('*')
            
            # Apply text search
            if query:
                # Search in business name and DBA name
                select_query = select_query.or_(
                    f'business_name.ilike.%{query}%,'
                    f'dba_name.ilike.%{query}%'
                )
            
            # Apply filters
            if filters:
                if filters.get('county'):
                    select_query = select_query.eq('business_county', filters['county'])
                
                if filters.get('entity_type'):
                    select_query = select_query.eq('entity_type', filters['entity_type'])
                
                if filters.get('city'):
                    select_query = select_query.ilike('business_city', f"%{filters['city']}%")
                
                if filters.get('formation_date_after'):
                    select_query = select_query.gte('formation_date', filters['formation_date_after'])
                
                if filters.get('has_phone'):
                    if filters['has_phone']:
                        select_query = select_query.not_.is_('phone_numbers', 'null')
                    else:
                        select_query = select_query.is_('phone_numbers', 'null')
                
                if filters.get('has_email'):
                    if filters['has_email']:
                        select_query = select_query.not_.is_('email_addresses', 'null')
                    else:
                        select_query = select_query.is_('email_addresses', 'null')
            
            # Execute query with limit
            response = select_query.limit(self.max_sql_results).execute()
            
            # Convert to SearchResult objects
            for item in response.data:
                results.append(SearchResult(
                    entity_id=item['entity_id'],
                    business_name=item['business_name'],
                    dba_name=item.get('dba_name'),
                    business_city=item['business_city'],
                    business_county=item['business_county'],
                    entity_type=item['entity_type'],
                    formation_date=item.get('formation_date'),
                    phone_numbers=item.get('phone_numbers'),
                    email_addresses=item.get('email_addresses'),
                    relevance_score=1.0,  # Exact match
                    match_type='exact'
                ))
                
        except Exception as e:
            print(f"SQL search error: {e}")
        
        return results

    async def semantic_search(self, query: str, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """
        Semantic search using embeddings for fuzzy/contextual matches
        """
        results = []
        
        try:
            # Generate embedding for the query
            query_embedding = await self._get_embedding(query)
            
            if not query_embedding:
                return results
            
            # Search similar embeddings in raw records
            # Note: This requires pgvector extension enabled in Supabase
            similarity_threshold = filters.get('similarity_threshold', 0.7) if filters else 0.7
            
            # Use vector similarity search
            response = self.supabase.rpc('match_documents', {
                'query_embedding': query_embedding,
                'match_threshold': similarity_threshold,
                'match_count': self.max_rag_results
            }).execute()
            
            # Process results and join with entity data
            for item in response.data:
                entity_response = self.supabase.table('florida_active_entities_with_contacts')\
                    .select('*').eq('entity_id', item['entity_id']).execute()
                
                if entity_response.data:
                    entity = entity_response.data[0]
                    results.append(SearchResult(
                        entity_id=entity['entity_id'],
                        business_name=entity['business_name'],
                        dba_name=entity.get('dba_name'),
                        business_city=entity['business_city'],
                        business_county=entity['business_county'],
                        entity_type=entity['entity_type'],
                        formation_date=entity.get('formation_date'),
                        phone_numbers=entity.get('phone_numbers'),
                        email_addresses=entity.get('email_addresses'),
                        relevance_score=item.get('similarity', 0.0),
                        match_type='semantic'
                    ))
                    
        except Exception as e:
            print(f"Semantic search error: {e}")
        
        return results

    async def hybrid_search(self, query: str, filters: Dict[str, Any] = None) -> List[SearchResult]:
        """
        Combine SQL and semantic search results with intelligent merging
        """
        # Run both searches in parallel
        sql_task = asyncio.create_task(self.sql_search(query, filters))
        semantic_task = asyncio.create_task(self.semantic_search(query, filters))
        
        sql_results, semantic_results = await asyncio.gather(sql_task, semantic_task)
        
        # Merge and deduplicate results
        merged_results = {}
        
        # Add SQL results (higher priority for exact matches)
        for result in sql_results:
            merged_results[result.entity_id] = result
        
        # Add semantic results, but don't override exact matches
        for result in semantic_results:
            if result.entity_id not in merged_results:
                merged_results[result.entity_id] = result
            else:
                # If we have both, boost the relevance score
                existing = merged_results[result.entity_id]
                existing.relevance_score = max(existing.relevance_score, result.relevance_score * 0.8)
                existing.match_type = 'hybrid'
        
        # Sort by relevance score and return
        final_results = list(merged_results.values())
        final_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return final_results

    async def _get_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI"""
        try:
            response = await openai.Embedding.acreate(
                model=self.embedding_model,
                input=[text]
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None

    # Specialized search methods
    async def search_by_industry(self, industry: str, location: str = None) -> List[SearchResult]:
        """Search businesses by industry/activity type"""
        query = f"businesses that provide {industry} services"
        filters = {}
        if location:
            filters['city'] = location
        
        return await self.hybrid_search(query, filters)

    async def search_contacts_by_area(self, county: str, has_phone: bool = True, has_email: bool = True) -> List[SearchResult]:
        """Find businesses with contact info in specific area"""
        filters = {
            'county': county,
            'has_phone': has_phone,
            'has_email': has_email
        }
        
        return await self.sql_search("", filters)

    async def search_new_businesses(self, days_back: int = 30, county: str = None) -> List[SearchResult]:
        """Find recently registered businesses"""
        cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        filters = {
            'formation_date_after': cutoff_date
        }
        
        if county:
            filters['county'] = county
        
        return await self.sql_search("", filters)

    async def advanced_search(
        self,
        business_name: str = None,
        industry_keywords: str = None,
        county: str = None,
        city: str = None,
        entity_type: str = None,
        has_contact_info: bool = None,
        formation_year: int = None
    ) -> List[SearchResult]:
        """Advanced search with multiple parameters"""
        
        # Build query string
        query_parts = []
        if business_name:
            query_parts.append(business_name)
        if industry_keywords:
            query_parts.append(industry_keywords)
        
        query = " ".join(query_parts)
        
        # Build filters
        filters = {}
        if county:
            filters['county'] = county
        if city:
            filters['city'] = city
        if entity_type:
            filters['entity_type'] = entity_type
        if has_contact_info is not None:
            filters['has_phone'] = has_contact_info
            filters['has_email'] = has_contact_info
        if formation_year:
            filters['formation_date_after'] = f"{formation_year}-01-01"
        
        # Use hybrid search for best results
        return await self.hybrid_search(query, filters)

    # Utility methods for ConcordBroker integration
    def to_dict(self, results: List[SearchResult]) -> List[Dict]:
        """Convert search results to dictionary format"""
        return [
            {
                'entity_id': r.entity_id,
                'business_name': r.business_name,
                'dba_name': r.dba_name,
                'location': f"{r.business_city}, {r.business_county} County",
                'entity_type': r.entity_type,
                'formation_date': r.formation_date,
                'phone_numbers': r.phone_numbers,
                'email_addresses': r.email_addresses,
                'relevance_score': r.relevance_score,
                'match_type': r.match_type
            }
            for r in results
        ]

    async def get_business_details(self, entity_id: str) -> Optional[Dict]:
        """Get full details for a specific business"""
        try:
            # Get entity details
            entity_response = self.supabase.table('florida_entities').select('*').eq('entity_id', entity_id).execute()
            
            if not entity_response.data:
                return None
            
            entity = entity_response.data[0]
            
            # Get contacts
            contacts_response = self.supabase.table('florida_contacts').select('*').eq('entity_id', entity_id).execute()
            
            # Get registered agents
            agents_response = self.supabase.table('florida_registered_agents').select('*').eq('entity_id', entity_id).execute()
            
            return {
                'entity': entity,
                'contacts': contacts_response.data,
                'registered_agents': agents_response.data
            }
            
        except Exception as e:
            print(f"Error getting business details: {e}")
            return None


# Example usage
async def example_usage():
    """Demonstrate the search capabilities"""
    search = FloridaBusinessSearch()
    
    # Example 1: Hybrid search for construction companies
    print("=== Construction Companies ===")
    results = await search.search_businesses("construction contractors", {"county": "MIAMI-DADE"})
    for result in results[:5]:
        print(f"{result.business_name} - {result.business_city} - Score: {result.relevance_score:.2f}")
    
    # Example 2: Search for new businesses
    print("\n=== New Businesses (last 30 days) ===")
    results = await search.search_new_businesses(30, "BROWARD")
    for result in results[:5]:
        print(f"{result.business_name} - Formed: {result.formation_date}")
    
    # Example 3: Businesses with contact information
    print("\n=== Businesses with Contact Info ===")
    results = await search.search_contacts_by_area("ORANGE", has_phone=True, has_email=True)
    for result in results[:5]:
        print(f"{result.business_name} - Phones: {result.phone_numbers}")


if __name__ == "__main__":
    asyncio.run(example_usage())