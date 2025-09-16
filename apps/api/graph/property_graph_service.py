"""
Property Knowledge Graph Service using Graphiti
Manages temporal property data and relationships in a knowledge graph
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

# Graphiti imports
try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EntityNode, EpisodicNode
    from graphiti_core.edges import EntityEdge, EpisodicEdge
    from graphiti_core.llm_client import OpenAIClient, LLMConfig
    from graphiti_core.embedder import OpenAIEmbedder
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    print("WARNING: Graphiti not installed. Install with: pip install graphiti-core")

from ..core.comprehensive_logging import get_logger, get_metrics_logger

logger = get_logger("property_graph")
metrics = get_metrics_logger("property_graph")


@dataclass
class PropertyNode:
    """Property entity in the knowledge graph"""
    parcel_id: str
    address: str
    city: str
    county: str
    state: str = "FL"
    property_type: Optional[str] = None
    current_value: Optional[float] = None
    land_value: Optional[float] = None
    building_value: Optional[float] = None
    year_built: Optional[int] = None
    square_feet: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    
    def to_entity_node(self) -> Dict[str, Any]:
        """Convert to Graphiti EntityNode format"""
        return {
            "name": f"Property_{self.parcel_id}",
            "entity_type": "property",
            "attributes": {
                "parcel_id": self.parcel_id,
                "address": self.address,
                "city": self.city,
                "county": self.county,
                "state": self.state,
                "property_type": self.property_type,
                "current_value": self.current_value,
                "land_value": self.land_value,
                "building_value": self.building_value,
                "year_built": self.year_built,
                "square_feet": self.square_feet,
                "bedrooms": self.bedrooms,
                "bathrooms": self.bathrooms
            }
        }


@dataclass
class OwnerNode:
    """Owner entity in the knowledge graph"""
    name: str
    entity_type: str  # person, corporation, trust
    sunbiz_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    
    def to_entity_node(self) -> Dict[str, Any]:
        """Convert to Graphiti EntityNode format"""
        return {
            "name": self.name,
            "entity_type": "owner",
            "attributes": {
                "owner_type": self.entity_type,
                "sunbiz_id": self.sunbiz_id,
                "phone": self.phone,
                "email": self.email,
                "address": self.address
            }
        }


@dataclass
class TransactionEdge:
    """Transaction relationship in the knowledge graph"""
    transaction_type: str  # sale, tax_deed, foreclosure, transfer
    date: datetime
    amount: Optional[float] = None
    document_number: Optional[str] = None
    
    def to_edge(self, source_id: str, target_id: str) -> Dict[str, Any]:
        """Convert to Graphiti Edge format"""
        return {
            "source": source_id,
            "target": target_id,
            "relationship_type": f"TRANSACTION_{self.transaction_type.upper()}",
            "attributes": {
                "date": self.date.isoformat(),
                "amount": self.amount,
                "document_number": self.document_number
            }
        }


class PropertyGraphService:
    """
    Service for managing property knowledge graph using Graphiti
    Provides temporal tracking, relationship mapping, and intelligent search
    """
    
    def __init__(self, 
                 neo4j_uri: str = None,
                 neo4j_user: str = None,
                 neo4j_password: str = None):
        """
        Initialize Property Graph Service
        
        Args:
            neo4j_uri: Neo4j database URI (default: from env)
            neo4j_user: Neo4j username (default: from env)
            neo4j_password: Neo4j password (default: from env)
        """
        if not GRAPHITI_AVAILABLE:
            raise ImportError("Graphiti is not installed. Please install it first.")
        
        # Configure Neo4j connection
        self.neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD", "password")
        
        # Initialize Graphiti
        self.graphiti = Graphiti(
            uri=self.neo4j_uri,
            user=self.neo4j_user,
            password=self.neo4j_password,
            llm_client=OpenAIClient(
                config=LLMConfig(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    temperature=0.7
                )
            ),
            embedder=OpenAIEmbedder(
                model="text-embedding-3-small"
            )
        )
        
        logger.info("Property Graph Service initialized with Graphiti")
        
    async def add_property(self, property_data: PropertyNode) -> str:
        """
        Add a property to the knowledge graph
        
        Args:
            property_data: PropertyNode with property information
            
        Returns:
            Property node ID in the graph
        """
        with logger.operation_context("add_property", parcel_id=property_data.parcel_id):
            # Create property description for LLM processing
            description = f"""
            Property Information:
            - Parcel ID: {property_data.parcel_id}
            - Address: {property_data.address}, {property_data.city}, {property_data.state}
            - County: {property_data.county}
            - Type: {property_data.property_type or 'Unknown'}
            - Current Value: ${property_data.current_value:,.2f} if property_data.current_value else 'Unknown'
            - Year Built: {property_data.year_built or 'Unknown'}
            - Square Feet: {property_data.square_feet or 'Unknown'}
            """
            
            # Add as episode to extract entities and relationships
            episode = await self.graphiti.add_episode(
                name=f"Property_{property_data.parcel_id}",
                episode_body=description,
                source_description="Property database import",
                reference_time=datetime.now()
            )
            
            metrics.record_count("properties_added")
            logger.info(f"Added property {property_data.parcel_id} to graph")
            
            return episode.id
            
    async def add_owner(self, owner_data: OwnerNode) -> str:
        """
        Add an owner to the knowledge graph
        
        Args:
            owner_data: OwnerNode with owner information
            
        Returns:
            Owner node ID in the graph
        """
        with logger.operation_context("add_owner", owner_name=owner_data.name):
            description = f"""
            Owner Information:
            - Name: {owner_data.name}
            - Type: {owner_data.entity_type}
            - Sunbiz ID: {owner_data.sunbiz_id or 'N/A'}
            - Contact: {owner_data.phone or owner_data.email or 'No contact info'}
            - Address: {owner_data.address or 'No address'}
            """
            
            episode = await self.graphiti.add_episode(
                name=f"Owner_{owner_data.name}",
                episode_body=description,
                source_description="Owner database import",
                reference_time=datetime.now()
            )
            
            metrics.record_count("owners_added")
            logger.info(f"Added owner {owner_data.name} to graph")
            
            return episode.id
            
    async def add_ownership(self, 
                           parcel_id: str,
                           owner_name: str,
                           ownership_type: str = "current",
                           start_date: datetime = None,
                           end_date: datetime = None,
                           percentage: float = 100.0) -> str:
        """
        Create ownership relationship between property and owner
        
        Args:
            parcel_id: Property parcel ID
            owner_name: Owner name
            ownership_type: Type of ownership (current, previous, partial)
            start_date: When ownership started
            end_date: When ownership ended (None for current)
            percentage: Ownership percentage
            
        Returns:
            Relationship ID
        """
        with logger.operation_context("add_ownership", 
                                    parcel_id=parcel_id,
                                    owner=owner_name):
            
            relationship_text = f"""
            {owner_name} {'owns' if ownership_type == 'current' else 'owned'} 
            property {parcel_id} ({percentage}% ownership)
            {'since ' + start_date.strftime('%Y-%m-%d') if start_date else ''}
            {'until ' + end_date.strftime('%Y-%m-%d') if end_date else ''}
            """
            
            episode = await self.graphiti.add_episode(
                name=f"Ownership_{parcel_id}_{owner_name}",
                episode_body=relationship_text,
                source_description="Ownership record",
                reference_time=start_date or datetime.now()
            )
            
            metrics.record_count("ownerships_added")
            logger.info(f"Added ownership: {owner_name} -> {parcel_id}")
            
            return episode.id
            
    async def add_transaction(self,
                            from_owner: str,
                            to_owner: str,
                            parcel_id: str,
                            transaction: TransactionEdge) -> str:
        """
        Add a property transaction to the graph
        
        Args:
            from_owner: Seller name
            to_owner: Buyer name
            parcel_id: Property parcel ID
            transaction: Transaction details
            
        Returns:
            Transaction episode ID
        """
        with logger.operation_context("add_transaction",
                                    parcel_id=parcel_id,
                                    type=transaction.transaction_type):
            
            transaction_text = f"""
            Transaction Record:
            - Type: {transaction.transaction_type}
            - Date: {transaction.date.strftime('%Y-%m-%d')}
            - Property: {parcel_id}
            - Seller: {from_owner}
            - Buyer: {to_owner}
            - Amount: ${transaction.amount:,.2f} if transaction.amount else 'Not disclosed'
            - Document: {transaction.document_number or 'N/A'}
            
            {from_owner} sold property {parcel_id} to {to_owner} on {transaction.date.strftime('%Y-%m-%d')}
            """
            
            episode = await self.graphiti.add_episode(
                name=f"Transaction_{parcel_id}_{transaction.date.strftime('%Y%m%d')}",
                episode_body=transaction_text,
                source_description=f"{transaction.transaction_type} transaction",
                reference_time=transaction.date
            )
            
            metrics.record_count("transactions_added")
            metrics.record_metric("transaction_value", transaction.amount or 0)
            logger.info(f"Added transaction: {from_owner} -> {to_owner} for {parcel_id}")
            
            return episode.id
            
    async def search_properties(self, 
                              query: str,
                              num_results: int = 10,
                              date_filter: Tuple[datetime, datetime] = None) -> List[Dict[str, Any]]:
        """
        Search properties using hybrid semantic and graph search
        
        Args:
            query: Search query
            num_results: Number of results to return
            date_filter: Optional date range filter
            
        Returns:
            List of property search results with context
        """
        with logger.operation_context("search_properties", query=query):
            start_time = datetime.now()
            
            # Configure search filters
            filter_config = {}
            if date_filter:
                filter_config["fact_dates"] = {
                    "start": date_filter[0].isoformat(),
                    "end": date_filter[1].isoformat()
                }
            
            # Perform hybrid search
            search_results = await self.graphiti.search(
                query=query,
                num_results=num_results,
                filter_config=filter_config
            )
            
            # Process and enhance results
            enhanced_results = []
            for result in search_results:
                # Get connected entities (owners, transactions)
                connections = await self._get_property_connections(result)
                
                enhanced_results.append({
                    "property": result.entity_name,
                    "relevance_score": result.score,
                    "context": result.fact,
                    "connections": connections,
                    "temporal_context": {
                        "valid_from": result.valid_from,
                        "valid_to": result.valid_to
                    }
                })
            
            # Record metrics
            search_time = (datetime.now() - start_time).total_seconds()
            metrics.record_timing("property_search", search_time)
            metrics.record_count("searches_performed")
            
            logger.info(f"Search completed: {len(enhanced_results)} results in {search_time:.2f}s")
            
            return enhanced_results
            
    async def get_property_history(self, parcel_id: str) -> Dict[str, Any]:
        """
        Get complete temporal history of a property
        
        Args:
            parcel_id: Property parcel ID
            
        Returns:
            Property history with all transactions and ownership changes
        """
        with logger.operation_context("get_property_history", parcel_id=parcel_id):
            # Search for all episodes related to this property
            history_query = f"Property {parcel_id} history ownership transactions"
            
            search_results = await self.graphiti.search(
                query=history_query,
                num_results=50  # Get comprehensive history
            )
            
            # Organize results by time
            timeline = []
            owners = []
            transactions = []
            values = []
            
            for result in search_results:
                if "owner" in result.fact.lower():
                    owners.append({
                        "owner": result.entity_name,
                        "period": f"{result.valid_from} to {result.valid_to or 'present'}",
                        "fact": result.fact
                    })
                elif "transaction" in result.fact.lower() or "sold" in result.fact.lower():
                    transactions.append({
                        "date": result.valid_from,
                        "description": result.fact,
                        "entities": result.entity_name
                    })
                elif "value" in result.fact.lower():
                    values.append({
                        "date": result.valid_from,
                        "value": result.fact
                    })
                    
                timeline.append({
                    "date": result.valid_from,
                    "event": result.fact,
                    "confidence": result.score
                })
            
            # Sort timeline by date
            timeline.sort(key=lambda x: x["date"])
            
            history = {
                "parcel_id": parcel_id,
                "timeline": timeline,
                "ownership_history": owners,
                "transaction_history": transactions,
                "value_history": values,
                "total_events": len(timeline)
            }
            
            metrics.record_count("histories_retrieved")
            logger.info(f"Retrieved history for {parcel_id}: {len(timeline)} events")
            
            return history
            
    async def find_related_properties(self,
                                     parcel_id: str,
                                     relationship_types: List[str] = None,
                                     max_hops: int = 2) -> List[Dict[str, Any]]:
        """
        Find properties related through ownership, transactions, or other relationships
        
        Args:
            parcel_id: Starting property parcel ID
            relationship_types: Types of relationships to follow
            max_hops: Maximum graph traversal depth
            
        Returns:
            List of related properties with relationship details
        """
        with logger.operation_context("find_related_properties",
                                    parcel_id=parcel_id,
                                    max_hops=max_hops):
            
            # Build search query for related entities
            query = f"Properties related to {parcel_id} through ownership or transactions"
            
            # Search with graph traversal
            search_results = await self.graphiti.search(
                query=query,
                num_results=20,
                filter_config={"n_level": max_hops}
            )
            
            # Process relationships
            related_properties = {}
            
            for result in search_results:
                # Extract property references from the fact
                if "property" in result.fact.lower() and parcel_id not in result.entity_name:
                    prop_id = result.entity_name
                    
                    if prop_id not in related_properties:
                        related_properties[prop_id] = {
                            "parcel_id": prop_id,
                            "relationships": [],
                            "connection_strength": 0
                        }
                    
                    related_properties[prop_id]["relationships"].append({
                        "type": self._extract_relationship_type(result.fact),
                        "description": result.fact,
                        "confidence": result.score
                    })
                    
                    related_properties[prop_id]["connection_strength"] += result.score
            
            # Convert to list and sort by connection strength
            results = list(related_properties.values())
            results.sort(key=lambda x: x["connection_strength"], reverse=True)
            
            metrics.record_count("related_properties_found", len(results))
            logger.info(f"Found {len(results)} related properties for {parcel_id}")
            
            return results
            
    async def detect_investment_patterns(self,
                                        owner_name: str,
                                        time_window: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """
        Detect investment patterns for a specific owner
        
        Args:
            owner_name: Name of the owner/investor
            time_window: Optional time window for analysis
            
        Returns:
            Investment pattern analysis
        """
        with logger.operation_context("detect_investment_patterns", owner=owner_name):
            # Search for all properties and transactions related to owner
            query = f"{owner_name} property investments purchases sales transactions"
            
            filter_config = {}
            if time_window:
                filter_config["fact_dates"] = {
                    "start": time_window[0].isoformat(),
                    "end": time_window[1].isoformat()
                }
            
            search_results = await self.graphiti.search(
                query=query,
                num_results=100,
                filter_config=filter_config
            )
            
            # Analyze patterns
            properties_owned = set()
            properties_sold = set()
            total_invested = 0
            total_returns = 0
            transaction_dates = []
            
            for result in search_results:
                fact_lower = result.fact.lower()
                
                if "bought" in fact_lower or "purchased" in fact_lower:
                    # Extract property and amount
                    properties_owned.add(result.entity_name)
                    # TODO: Extract amount from fact using NLP
                    
                elif "sold" in fact_lower:
                    properties_sold.add(result.entity_name)
                    # TODO: Extract amount from fact
                    
                if result.valid_from:
                    transaction_dates.append(result.valid_from)
            
            # Calculate metrics
            patterns = {
                "owner": owner_name,
                "total_properties_owned": len(properties_owned),
                "total_properties_sold": len(properties_sold),
                "current_portfolio_size": len(properties_owned - properties_sold),
                "investment_frequency": self._calculate_frequency(transaction_dates),
                "preferred_property_types": [],  # TODO: Analyze property types
                "preferred_locations": [],  # TODO: Analyze locations
                "holding_period_avg": 0,  # TODO: Calculate average holding period
                "roi_estimate": 0  # TODO: Calculate ROI
            }
            
            metrics.record_count("patterns_analyzed")
            logger.info(f"Analyzed investment patterns for {owner_name}")
            
            return patterns
            
    async def _get_property_connections(self, search_result) -> List[Dict[str, Any]]:
        """Get connected entities for a property search result"""
        connections = []
        
        # Extract entity references from the fact
        # This is a simplified version - in production, use NLP
        fact_lower = search_result.fact.lower()
        
        if "owner" in fact_lower or "owns" in fact_lower:
            connections.append({
                "type": "ownership",
                "entity": search_result.entity_name,
                "description": search_result.fact
            })
            
        if "sold" in fact_lower or "bought" in fact_lower:
            connections.append({
                "type": "transaction",
                "entity": search_result.entity_name,
                "description": search_result.fact
            })
            
        return connections
        
    def _extract_relationship_type(self, fact: str) -> str:
        """Extract relationship type from fact text"""
        fact_lower = fact.lower()
        
        if "owns" in fact_lower or "owner" in fact_lower:
            return "ownership"
        elif "sold" in fact_lower or "bought" in fact_lower:
            return "transaction"
        elif "manages" in fact_lower:
            return "management"
        elif "rents" in fact_lower or "leases" in fact_lower:
            return "rental"
        else:
            return "related"
            
    def _calculate_frequency(self, dates: List[str]) -> str:
        """Calculate transaction frequency from dates"""
        if len(dates) < 2:
            return "insufficient_data"
            
        # Sort dates
        dates.sort()
        
        # Calculate average time between transactions
        # This is simplified - in production, use proper date parsing
        total_days = 0
        for i in range(1, len(dates)):
            # TODO: Calculate actual date differences
            total_days += 30  # Placeholder
            
        avg_days = total_days / (len(dates) - 1)
        
        if avg_days < 30:
            return "very_frequent"
        elif avg_days < 90:
            return "frequent"
        elif avg_days < 180:
            return "moderate"
        elif avg_days < 365:
            return "occasional"
        else:
            return "rare"


# Example usage
async def demo_property_graph():
    """Demonstrate Property Graph Service capabilities"""
    
    # Initialize service
    service = PropertyGraphService()
    
    # Add a property
    property1 = PropertyNode(
        parcel_id="064210010010",
        address="123 Main St",
        city="Hollywood",
        county="Broward",
        property_type="Residential",
        current_value=450000,
        year_built=2005,
        square_feet=2500
    )
    
    prop_id = await service.add_property(property1)
    print(f"Added property: {prop_id}")
    
    # Add an owner
    owner1 = OwnerNode(
        name="John Smith",
        entity_type="person",
        phone="555-1234",
        email="john@example.com"
    )
    
    owner_id = await service.add_owner(owner1)
    print(f"Added owner: {owner_id}")
    
    # Create ownership relationship
    ownership_id = await service.add_ownership(
        parcel_id=property1.parcel_id,
        owner_name=owner1.name,
        ownership_type="current",
        start_date=datetime(2020, 1, 1),
        percentage=100.0
    )
    print(f"Created ownership: {ownership_id}")
    
    # Search for properties
    results = await service.search_properties(
        query="residential properties in Hollywood owned by John",
        num_results=5
    )
    
    print(f"\nSearch Results:")
    for result in results:
        print(f"- {result['property']}: {result['relevance_score']:.2f}")
        print(f"  Context: {result['context']}")
        
    # Get property history
    history = await service.get_property_history(property1.parcel_id)
    print(f"\nProperty History: {history['total_events']} events")
    
    # Find related properties
    related = await service.find_related_properties(
        parcel_id=property1.parcel_id,
        max_hops=2
    )
    print(f"\nRelated Properties: {len(related)} found")


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_property_graph())