"""
Property Search Workflow using LangGraph
Intelligent, stateful property search with refinement and enrichment
"""

import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, SystemMessage
import logging

from ..config import config
from ..state import PropertySearchState, PropertyFilter, WorkflowResult
from ..nodes.search_nodes import (
    parse_user_query,
    extract_search_entities,
    build_database_query,
    execute_search,
    enrich_results,
    format_final_results
)

logger = logging.getLogger(__name__)

class PropertySearchWorkflow:
    """
    Stateful property search workflow with intelligent query understanding,
    database search, result enrichment, and refinement capabilities
    """
    
    def __init__(self):
        self.config = config
        self.llm = config.get_llm()
        self.checkpointer = config.checkpointer or MemorySaver()
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
        
    def _build_graph(self) -> StateGraph:
        """Build the property search workflow graph"""
        
        # Create the graph with PropertySearchState
        workflow = StateGraph(PropertySearchState)
        
        # Add nodes
        workflow.add_node("parse_query", self.parse_query_node)
        workflow.add_node("extract_entities", self.extract_entities_node)
        workflow.add_node("check_cache", self.check_cache_node)
        workflow.add_node("build_query", self.build_query_node)
        workflow.add_node("execute_search", self.execute_search_node)
        workflow.add_node("enrich_results", self.enrich_results_node)
        workflow.add_node("format_results", self.format_results_node)
        workflow.add_node("suggest_refinements", self.suggest_refinements_node)
        
        # Add edges with conditions
        workflow.set_entry_point("parse_query")
        
        workflow.add_edge("parse_query", "extract_entities")
        workflow.add_edge("extract_entities", "check_cache")
        
        # Conditional edge: if cache hit, skip to formatting
        workflow.add_conditional_edges(
            "check_cache",
            self.should_use_cache,
            {
                "use_cache": "format_results",
                "no_cache": "build_query"
            }
        )
        
        workflow.add_edge("build_query", "execute_search")
        
        # Conditional edge: if no results, suggest refinements
        workflow.add_conditional_edges(
            "execute_search",
            self.check_results,
            {
                "has_results": "enrich_results",
                "no_results": "suggest_refinements"
            }
        )
        
        workflow.add_edge("enrich_results", "format_results")
        workflow.add_edge("suggest_refinements", "format_results")
        workflow.add_edge("format_results", END)
        
        return workflow
    
    async def parse_query_node(self, state: PropertySearchState) -> PropertySearchState:
        """Parse and understand the user's search query"""
        start_time = time.time()
        
        try:
            prompt = f"""
            Analyze this property search query and identify the user's intent:
            Query: {state['query']}
            
            Classify the intent as one of:
            - location_search: Looking for properties in a specific area
            - owner_search: Looking for properties by owner name
            - value_search: Looking for properties by value range
            - type_search: Looking for specific property types
            - complex_search: Multiple criteria
            
            Respond with just the intent classification.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a property search intent classifier."),
                HumanMessage(content=prompt)
            ])
            
            state['parsed_intent'] = response.content.strip().lower()
            state['execution_time'] = time.time() - start_time
            
            logger.info(f"Parsed intent: {state['parsed_intent']}")
            
        except Exception as e:
            logger.error(f"Error parsing query: {e}")
            state['error'] = str(e)
            state['parsed_intent'] = 'complex_search'  # Default fallback
            
        return state
    
    async def extract_entities_node(self, state: PropertySearchState) -> PropertySearchState:
        """Extract entities and filters from the query"""
        try:
            prompt = f"""
            Extract search parameters from this property query:
            Query: {state['query']}
            Intent: {state['parsed_intent']}
            
            Extract and return as JSON:
            - city: city name if mentioned
            - address: street address if mentioned
            - owner: owner name if mentioned
            - min_value: minimum property value
            - max_value: maximum property value
            - property_type: property type (residential, commercial, etc.)
            - year_built_min: minimum year built
            - year_built_max: maximum year built
            
            Only include fields that are explicitly mentioned or strongly implied.
            """
            
            response = await self.llm.ainvoke([
                SystemMessage(content="You are a property search entity extractor. Return valid JSON."),
                HumanMessage(content=prompt)
            ])
            
            # Parse the JSON response
            try:
                entities = json.loads(response.content)
                state['extracted_entities'] = entities
                
                # Merge with existing filters
                if state.get('filters'):
                    state['filters'].update(entities)
                else:
                    state['filters'] = entities
                    
                logger.info(f"Extracted entities: {entities}")
                
            except json.JSONDecodeError:
                logger.warning("Failed to parse entities JSON, using regex fallback")
                state['extracted_entities'] = self._extract_entities_fallback(state['query'])
                
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            state['error'] = str(e)
            state['extracted_entities'] = {}
            
        return state
    
    async def check_cache_node(self, state: PropertySearchState) -> PropertySearchState:
        """Check if we have cached results for this query"""
        # For now, simple implementation - no cache
        # TODO: Implement Redis caching
        state['cache_hit'] = False
        return state
    
    async def build_query_node(self, state: PropertySearchState) -> PropertySearchState:
        """Build the database query from extracted entities"""
        try:
            filters = state.get('filters', {})
            
            # Build WHERE clauses
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
                
            if filters.get('property_type'):
                where_clauses.append(f"property_type = '{filters['property_type']}'")
                
            # Build the query
            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            state['sql_query'] = f"""
                SELECT * FROM florida_parcels
                WHERE {where_clause}
                LIMIT {state.get('page_size', 20)}
                OFFSET {(state.get('page', 1) - 1) * state.get('page_size', 20)}
            """
            
            logger.info(f"Built query: {state['sql_query']}")
            
        except Exception as e:
            logger.error(f"Error building query: {e}")
            state['error'] = str(e)
            
        return state
    
    async def execute_search_node(self, state: PropertySearchState) -> PropertySearchState:
        """Execute the database search"""
        try:
            # Get Supabase client
            supabase = self.config.get_supabase_client()
            
            filters = state.get('filters', {})
            query = supabase.table('florida_parcels').select('*')
            
            # Apply filters
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
                
            # Execute with pagination
            page_size = state.get('page_size', 20)
            offset = (state.get('page', 1) - 1) * page_size
            
            response = query.range(offset, offset + page_size - 1).execute()
            
            state['raw_results'] = response.data if response.data else []
            state['total_count'] = len(response.data) if response.data else 0
            
            logger.info(f"Found {state['total_count']} properties")
            
        except Exception as e:
            logger.error(f"Error executing search: {e}")
            state['error'] = str(e)
            state['raw_results'] = []
            state['total_count'] = 0
            
        return state
    
    async def enrich_results_node(self, state: PropertySearchState) -> PropertySearchState:
        """Enrich search results with additional data"""
        try:
            # For now, just pass through
            # TODO: Add Sunbiz matching, sales history, etc.
            state['enriched_results'] = state.get('raw_results', [])
            
            # Add confidence scores
            for result in state['enriched_results']:
                # Simple confidence based on data completeness
                confidence = 0.5
                if result.get('own_name'):
                    confidence += 0.2
                if result.get('jv'):
                    confidence += 0.15
                if result.get('act_yr_blt'):
                    confidence += 0.15
                    
                result['confidence_score'] = confidence
                
        except Exception as e:
            logger.error(f"Error enriching results: {e}")
            state['enriched_results'] = state.get('raw_results', [])
            
        return state
    
    async def format_results_node(self, state: PropertySearchState) -> PropertySearchState:
        """Format the final results for output"""
        try:
            results = state.get('enriched_results', [])
            
            # Format for frontend consumption
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
                
            state['final_results'] = formatted
            
        except Exception as e:
            logger.error(f"Error formatting results: {e}")
            state['final_results'] = []
            
        return state
    
    async def suggest_refinements_node(self, state: PropertySearchState) -> PropertySearchState:
        """Suggest query refinements when no results found"""
        try:
            suggestions = []
            filters = state.get('filters', {})
            
            if filters.get('min_value') and filters.get('max_value'):
                suggestions.append("Try expanding your price range")
                
            if filters.get('city'):
                suggestions.append(f"Try searching nearby cities or remove city filter")
                
            if filters.get('owner'):
                suggestions.append("Try variations of the owner name or partial matches")
                
            if not suggestions:
                suggestions = [
                    "Try broadening your search criteria",
                    "Check spelling of location or owner names",
                    "Remove some filters to see more results"
                ]
                
            state['refinement_suggestions'] = suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting refinements: {e}")
            state['refinement_suggestions'] = ["Try adjusting your search criteria"]
            
        return state
    
    def should_use_cache(self, state: PropertySearchState) -> str:
        """Determine if cached results should be used"""
        return "use_cache" if state.get('cache_hit', False) else "no_cache"
    
    def check_results(self, state: PropertySearchState) -> str:
        """Check if search returned results"""
        has_results = state.get('total_count', 0) > 0
        return "has_results" if has_results else "no_results"
    
    def _extract_entities_fallback(self, query: str) -> Dict[str, Any]:
        """Fallback entity extraction using simple patterns"""
        entities = {}
        
        # Simple pattern matching
        query_lower = query.lower()
        
        # Cities
        cities = ['hollywood', 'fort lauderdale', 'pompano beach', 'davie', 'plantation']
        for city in cities:
            if city in query_lower:
                entities['city'] = city.upper()
                break
                
        return entities
    
    async def run(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        thread_id: Optional[str] = None
    ) -> WorkflowResult:
        """
        Run the property search workflow
        
        Args:
            query: User's search query
            filters: Additional filters
            page: Page number for pagination
            page_size: Number of results per page
            thread_id: Thread ID for conversation continuity
            
        Returns:
            WorkflowResult with search results
        """
        start_time = time.time()
        
        try:
            # Initialize state
            initial_state: PropertySearchState = {
                'query': query,
                'filters': filters or {},
                'user_id': None,
                'session_id': thread_id or f"search_{datetime.now().timestamp()}",
                'page': page,
                'page_size': page_size,
                'cache_hit': False,
                'retry_count': 0,
                'parsed_intent': None,
                'extracted_entities': None,
                'search_strategy': None,
                'sql_query': None,
                'raw_results': None,
                'enriched_results': None,
                'sunbiz_matches': None,
                'final_results': None,
                'total_count': None,
                'execution_time': None,
                'confidence_score': None,
                'refinement_suggestions': None,
                'error': None
            }
            
            # Run the workflow
            config = {"configurable": {"thread_id": thread_id}} if thread_id else None
            final_state = await self.compiled_graph.ainvoke(initial_state, config=config)
            
            # Prepare result
            execution_time = time.time() - start_time
            
            return WorkflowResult(
                success=final_state.get('error') is None,
                data={
                    'properties': final_state.get('final_results', []),
                    'total': final_state.get('total_count', 0),
                    'page': page,
                    'page_size': page_size,
                    'suggestions': final_state.get('refinement_suggestions', [])
                },
                error=final_state.get('error'),
                metadata={
                    'intent': final_state.get('parsed_intent'),
                    'entities': final_state.get('extracted_entities'),
                    'cache_hit': final_state.get('cache_hit', False),
                    'confidence': final_state.get('confidence_score', 0)
                },
                execution_time=execution_time,
                workflow_id=final_state.get('session_id', ''),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return WorkflowResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                workflow_id=thread_id or '',
                timestamp=datetime.now()
            )