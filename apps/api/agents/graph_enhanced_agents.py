"""
Graph-Enhanced Agents with Persistent Memory
Integrates existing agents with Graphiti knowledge graph
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .base_agent import BaseAgent, AgentStatus
from .confidence_agent import ConfidenceAgent, Decision
from .entity_extraction_agent import EntityExtractionAgent
from .semantic_search_agent import SemanticSearchAgent
from ..graph.enhanced_rag_service import EnhancedRAGService
from ..graph.property_graph_service import PropertyGraphService
from ..core.comprehensive_logging import get_logger, get_metrics_logger

logger = get_logger("graph_enhanced_agents")
metrics = get_metrics_logger("graph_enhanced_agents")


class GraphMemoryMixin:
    """
    Mixin to add graph-based memory to any agent
    """
    
    def __init__(self, graph_service: PropertyGraphService = None):
        self.graph_service = graph_service or PropertyGraphService()
        self.memory_context = []
        self.session_id = f"session_{datetime.now().timestamp()}"
        
    async def store_interaction(self, 
                               interaction_type: str,
                               input_data: Dict[str, Any],
                               output_data: Dict[str, Any],
                               confidence: float = 0.5):
        """Store agent interaction in graph for future reference"""
        
        try:
            episode_text = f"""
            Agent Interaction - {interaction_type}
            Session: {self.session_id}
            Agent: {getattr(self, 'agent_id', 'unknown')}
            
            Input: {input_data}
            Output: {output_data}
            Confidence: {confidence}
            Timestamp: {datetime.now().isoformat()}
            """
            
            episode = await self.graph_service.graphiti.add_episode(
                name=f"Agent_{interaction_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                episode_body=episode_text,
                source_description=f"Agent interaction - {interaction_type}",
                reference_time=datetime.now()
            )
            
            logger.debug(f"Stored interaction in graph: {episode.id}")
            metrics.record_count("interactions_stored")
            
            return episode.id
            
        except Exception as e:
            logger.warning(f"Failed to store interaction: {e}")
            return None
            
    async def retrieve_context(self, 
                              query: str, 
                              num_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context from graph memory"""
        
        try:
            # Search for relevant past interactions
            results = await self.graph_service.search_properties(
                query=query,
                num_results=num_results
            )
            
            # Extract context
            context = []
            for result in results:
                context.append({
                    "content": result.get("context", ""),
                    "relevance": result.get("relevance_score", 0),
                    "temporal": result.get("temporal_context", {}),
                    "connections": result.get("connections", [])
                })
            
            logger.debug(f"Retrieved {len(context)} context items from graph")
            metrics.record_count("context_retrievals")
            
            return context
            
        except Exception as e:
            logger.warning(f"Failed to retrieve context: {e}")
            return []
            
    async def find_similar_cases(self, 
                                case_description: str,
                                limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar cases from past interactions"""
        
        try:
            # Search for similar cases
            similar_query = f"similar cases to: {case_description}"
            
            results = await self.graph_service.search_properties(
                query=similar_query,
                num_results=limit
            )
            
            cases = []
            for result in results:
                cases.append({
                    "case": result.get("context", ""),
                    "similarity": result.get("relevance_score", 0),
                    "outcome": result.get("outcome", "unknown"),
                    "date": result.get("temporal_context", {}).get("valid_from", "")
                })
            
            return cases
            
        except Exception as e:
            logger.warning(f"Failed to find similar cases: {e}")
            return []


class GraphEnhancedPropertyAgent(ConfidenceAgent, GraphMemoryMixin):
    """
    Property agent enhanced with graph-based memory and context
    """
    
    def __init__(self, 
                 graph_service: PropertyGraphService = None,
                 rag_service: EnhancedRAGService = None):
        ConfidenceAgent.__init__(
            self,
            agent_id="graph_property_agent",
            name="Graph-Enhanced Property Agent",
            description="Property agent with knowledge graph memory"
        )
        GraphMemoryMixin.__init__(self, graph_service)
        
        self.rag_service = rag_service or EnhancedRAGService(graph_service)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process with graph-enhanced context"""
        
        with logger.operation_context("graph_enhanced_process",
                                     agent_id=self.agent_id):
            
            # 1. Retrieve relevant context from graph
            query = input_data.get("query", "")
            context = await self.retrieve_context(query)
            
            # 2. Find similar past cases
            similar_cases = await self.find_similar_cases(query)
            
            # 3. Enhance input with graph context
            input_data["graph_context"] = {
                "retrieved_context": context,
                "similar_cases": similar_cases,
                "session_id": self.session_id
            }
            
            # 4. Boost confidence based on context quality
            if context:
                avg_relevance = sum(c["relevance"] for c in context) / len(context)
                self.confidence_boost = min(0.25, avg_relevance * 0.3)
                logger.info(f"Confidence boost from graph: {self.confidence_boost:.2f}")
            
            # 5. Process with enhanced context
            result = await super().process(input_data)
            
            # 6. Store this interaction for future reference
            await self.store_interaction(
                interaction_type="property_query",
                input_data={"query": query},
                output_data=result,
                confidence=result.get("confidence", 0.5)
            )
            
            # 7. Add graph insights to result
            result["graph_insights"] = {
                "context_used": len(context),
                "similar_cases_found": len(similar_cases),
                "confidence_boost": self.confidence_boost
            }
            
            return result
            
    async def analyze_property_network(self, parcel_id: str) -> Dict[str, Any]:
        """Analyze the network of relationships around a property"""
        
        with logger.operation_context("analyze_property_network",
                                     parcel_id=parcel_id):
            
            # Get property history
            history = await self.graph_service.get_property_history(parcel_id)
            
            # Find related properties
            related = await self.graph_service.find_related_properties(
                parcel_id=parcel_id,
                max_hops=2
            )
            
            # Analyze patterns
            analysis = {
                "property": parcel_id,
                "history_events": len(history.get("timeline", [])),
                "ownership_changes": len(history.get("ownership_history", [])),
                "transactions": len(history.get("transaction_history", [])),
                "related_properties": len(related),
                "network_insights": []
            }
            
            # Generate insights
            if len(related) > 5:
                analysis["network_insights"].append(
                    "Property is part of a large network, possibly investment portfolio"
                )
            
            if len(history.get("ownership_history", [])) > 3:
                analysis["network_insights"].append(
                    "Frequent ownership changes detected"
                )
            
            # Store analysis
            await self.store_interaction(
                interaction_type="network_analysis",
                input_data={"parcel_id": parcel_id},
                output_data=analysis,
                confidence=0.85
            )
            
            return analysis


class GraphEnhancedEntityExtractor(EntityExtractionAgent, GraphMemoryMixin):
    """
    Entity extraction agent with graph storage
    """
    
    def __init__(self, graph_service: PropertyGraphService = None):
        EntityExtractionAgent.__init__(self)
        GraphMemoryMixin.__init__(self, graph_service)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract entities and store in graph"""
        
        # Extract entities using parent class
        result = await super().process(input_data)
        
        # Store extracted entities in graph
        entities = result.get("entities", {})
        
        # Store persons as owners
        for person in entities.get("persons", []):
            try:
                from ..graph.property_graph_service import OwnerNode
                
                owner = OwnerNode(
                    name=person["value"],
                    entity_type="person",
                    email=None,
                    phone=None
                )
                
                await self.graph_service.add_owner(owner)
                logger.debug(f"Added person to graph: {person['value']}")
                
            except Exception as e:
                logger.warning(f"Failed to add person to graph: {e}")
        
        # Store organizations
        for org in entities.get("organizations", []):
            try:
                from ..graph.property_graph_service import OwnerNode
                
                owner = OwnerNode(
                    name=org["value"],
                    entity_type="corporation"
                )
                
                await self.graph_service.add_owner(owner)
                logger.debug(f"Added organization to graph: {org['value']}")
                
            except Exception as e:
                logger.warning(f"Failed to add organization to graph: {e}")
        
        # Store the extraction event
        await self.store_interaction(
            interaction_type="entity_extraction",
            input_data={"text_length": len(input_data.get("text", ""))},
            output_data={
                "entities_found": result.get("summary", {}).get("total_entities", 0),
                "categories": result.get("summary", {}).get("categories_found", [])
            },
            confidence=0.8
        )
        
        return result


class GraphEnhancedSearchAgent(SemanticSearchAgent, GraphMemoryMixin):
    """
    Semantic search agent with graph-powered retrieval
    """
    
    def __init__(self, 
                 graph_service: PropertyGraphService = None,
                 rag_service: EnhancedRAGService = None):
        SemanticSearchAgent.__init__(self)
        GraphMemoryMixin.__init__(self, graph_service)
        
        self.rag_service = rag_service or EnhancedRAGService(graph_service)
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process search with hybrid retrieval"""
        
        query = input_data.get("query", "")
        filters = input_data.get("filters", {})
        
        # Perform hybrid search
        search_results = await self.rag_service.hybrid_search(
            query=query,
            filters=filters,
            num_results=input_data.get("limit", 10),
            search_type="hybrid"
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            formatted_results.append({
                "content": result.content,
                "source": result.source,
                "confidence": result.confidence,
                "graph_context": result.graph_context,
                "relationships": result.relationships
            })
        
        # Store search interaction
        await self.store_interaction(
            interaction_type="semantic_search",
            input_data={"query": query, "filters": filters},
            output_data={"results_count": len(formatted_results)},
            confidence=0.9
        )
        
        return {
            "query": query,
            "results": formatted_results,
            "total": len(formatted_results),
            "search_type": "hybrid_graph"
        }


class GraphAgentOrchestrator:
    """
    Orchestrator for graph-enhanced agents
    """
    
    def __init__(self, graph_service: PropertyGraphService = None):
        self.graph_service = graph_service or PropertyGraphService()
        self.rag_service = EnhancedRAGService(self.graph_service)
        
        # Initialize graph-enhanced agents
        self.agents = {
            "property": GraphEnhancedPropertyAgent(self.graph_service, self.rag_service),
            "entity_extraction": GraphEnhancedEntityExtractor(self.graph_service),
            "search": GraphEnhancedSearchAgent(self.graph_service, self.rag_service)
        }
        
        self.logger = get_logger("graph_orchestrator")
        
    async def route_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Route request to appropriate agent"""
        
        request_type = request.get("type", "search")
        
        if request_type == "property_analysis":
            agent = self.agents["property"]
        elif request_type == "extract_entities":
            agent = self.agents["entity_extraction"]
        else:
            agent = self.agents["search"]
        
        self.logger.info(f"Routing request to {agent.agent_id}")
        
        # Process with selected agent
        result = await agent.process(request)
        
        # Add orchestration metadata
        result["orchestration"] = {
            "agent_used": agent.agent_id,
            "graph_enabled": True,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    async def multi_agent_analysis(self, 
                                  property_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis using multiple agents
        """
        
        self.logger.info(f"Starting multi-agent analysis for {property_id}")
        
        results = {
            "property_id": property_id,
            "analyses": {},
            "combined_insights": []
        }
        
        # 1. Property network analysis
        property_agent = self.agents["property"]
        network_analysis = await property_agent.analyze_property_network(property_id)
        results["analyses"]["network"] = network_analysis
        
        # 2. Search for related information
        search_agent = self.agents["search"]
        search_results = await search_agent.process({
            "query": f"property {property_id} history transactions",
            "limit": 5
        })
        results["analyses"]["search"] = search_results
        
        # 3. Extract entities from search results
        if search_results.get("results"):
            combined_text = " ".join([r["content"] for r in search_results["results"][:3]])
            
            entity_agent = self.agents["entity_extraction"]
            entities = await entity_agent.process({
                "text": combined_text
            })
            results["analyses"]["entities"] = entities
        
        # Generate combined insights
        if network_analysis.get("network_insights"):
            results["combined_insights"].extend(network_analysis["network_insights"])
        
        if results["analyses"].get("entities", {}).get("summary", {}).get("key_findings"):
            results["combined_insights"].extend(
                results["analyses"]["entities"]["summary"]["key_findings"]
            )
        
        # Store multi-agent analysis
        await self.graph_service.graphiti.add_episode(
            name=f"MultiAgent_Analysis_{property_id}",
            episode_body=f"Multi-agent analysis performed for property {property_id}",
            source_description="Multi-agent orchestration",
            reference_time=datetime.now()
        )
        
        return results


# Example usage and integration
async def demo_graph_agents():
    """Demonstrate graph-enhanced agents"""
    
    # Initialize services
    graph_service = PropertyGraphService()
    orchestrator = GraphAgentOrchestrator(graph_service)
    
    # Test property agent
    print("Testing Graph-Enhanced Property Agent...")
    property_result = await orchestrator.route_request({
        "type": "property_analysis",
        "query": "Find properties in Hollywood with recent sales",
        "action": "search"
    })
    print(f"Property Agent Result: {property_result}")
    
    # Test entity extraction
    print("\nTesting Graph-Enhanced Entity Extraction...")
    entity_result = await orchestrator.route_request({
        "type": "extract_entities",
        "text": "John Smith sold property at 123 Main St to ABC Holdings LLC for $500,000"
    })
    print(f"Entity Extraction Result: {entity_result}")
    
    # Test search agent
    print("\nTesting Graph-Enhanced Search...")
    search_result = await orchestrator.route_request({
        "type": "search",
        "query": "commercial properties Fort Lauderdale"
    })
    print(f"Search Result: {search_result}")
    
    # Test multi-agent analysis
    print("\nTesting Multi-Agent Analysis...")
    analysis_result = await orchestrator.multi_agent_analysis("064210010010")
    print(f"Multi-Agent Analysis: {analysis_result}")


if __name__ == "__main__":
    asyncio.run(demo_graph_agents())