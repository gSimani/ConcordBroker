"""
Enhanced RAG Service with Graphiti Knowledge Graph
Combines vector search, graph traversal, and temporal context for superior retrieval
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
from dataclasses import dataclass
import logging

from .property_graph_service import PropertyGraphService, GRAPHITI_AVAILABLE
from ..core.comprehensive_logging import get_logger, get_metrics_logger
from ..agents.confidence_agent import ConfidenceAgent

# Existing imports
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = get_logger("enhanced_rag")
metrics = get_metrics_logger("enhanced_rag")


@dataclass
class RetrievalResult:
    """Enhanced retrieval result with graph context"""
    content: str
    source: str  # vector, graph, hybrid
    relevance_score: float
    graph_context: Optional[Dict[str, Any]] = None
    temporal_context: Optional[Dict[str, Any]] = None
    relationships: Optional[List[Dict[str, Any]]] = None
    confidence: float = 0.5


class EnhancedRAGService:
    """
    Advanced RAG service that combines:
    1. Traditional vector search (FAISS/Embeddings)
    2. Knowledge graph traversal (Graphiti)
    3. Temporal context awareness
    4. Relationship-based retrieval
    """
    
    def __init__(self,
                 graph_service: PropertyGraphService = None,
                 embedding_model: str = "text-embedding-3-small",
                 rerank_model: str = "gpt-4o-mini"):
        """
        Initialize Enhanced RAG Service
        
        Args:
            graph_service: Property graph service instance
            embedding_model: OpenAI embedding model to use
            rerank_model: Model for reranking results
        """
        # Initialize graph service
        if GRAPHITI_AVAILABLE:
            self.graph_service = graph_service or PropertyGraphService()
        else:
            self.graph_service = None
            logger.warning("Graphiti not available - using vector-only RAG")
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        
        # Initialize vector store (will be populated with documents)
        self.vector_store = None
        
        # Reranking model
        self.rerank_model = rerank_model
        
        # Cache for performance
        self.cache = {}
        
        logger.info("Enhanced RAG Service initialized")
        
    async def index_documents(self, documents: List[Dict[str, Any]]) -> int:
        """
        Index documents in both vector store and knowledge graph
        
        Args:
            documents: List of documents to index
            
        Returns:
            Number of documents indexed
        """
        with logger.operation_context("index_documents", count=len(documents)):
            indexed_count = 0
            
            # Prepare documents for vector store
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            
            all_chunks = []
            
            for doc in documents:
                # Extract text content
                text = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                # Split into chunks for vector store
                chunks = text_splitter.split_text(text)
                
                for i, chunk in enumerate(chunks):
                    all_chunks.append(Document(
                        page_content=chunk,
                        metadata={
                            **metadata,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "source_id": doc.get("id", "unknown")
                        }
                    ))
                
                # Index in knowledge graph if available
                if self.graph_service and doc.get("type") == "property":
                    await self._index_property_in_graph(doc)
                    
                indexed_count += 1
            
            # Create or update vector store
            if all_chunks:
                if self.vector_store is None:
                    self.vector_store = FAISS.from_documents(
                        all_chunks,
                        self.embeddings
                    )
                else:
                    self.vector_store.add_documents(all_chunks)
            
            metrics.record_count("documents_indexed", indexed_count)
            logger.info(f"Indexed {indexed_count} documents with {len(all_chunks)} chunks")
            
            return indexed_count
            
    async def hybrid_search(self,
                          query: str,
                          filters: Dict[str, Any] = None,
                          num_results: int = 10,
                          search_type: str = "hybrid") -> List[RetrievalResult]:
        """
        Perform hybrid search combining vector and graph retrieval
        
        Args:
            query: Search query
            filters: Optional filters (date range, property type, etc.)
            num_results: Number of results to return
            search_type: "vector", "graph", or "hybrid"
            
        Returns:
            List of retrieval results with context
        """
        with logger.operation_context("hybrid_search", 
                                    query=query[:50],
                                    search_type=search_type):
            
            results = []
            
            # 1. Vector Search
            if search_type in ["vector", "hybrid"] and self.vector_store:
                vector_results = await self._vector_search(query, filters, num_results)
                results.extend(vector_results)
                logger.debug(f"Vector search returned {len(vector_results)} results")
            
            # 2. Graph Search
            if search_type in ["graph", "hybrid"] and self.graph_service:
                graph_results = await self._graph_search(query, filters, num_results)
                results.extend(graph_results)
                logger.debug(f"Graph search returned {len(graph_results)} results")
            
            # 3. Merge and Rerank
            if search_type == "hybrid" and len(results) > num_results:
                results = await self._rerank_results(query, results, num_results)
            
            # 4. Enhance with relationships
            if self.graph_service:
                results = await self._enhance_with_relationships(results)
            
            # 5. Calculate final confidence scores
            results = self._calculate_confidence_scores(results, query)
            
            # Sort by confidence and limit
            results.sort(key=lambda x: x.confidence, reverse=True)
            results = results[:num_results]
            
            metrics.record_count("searches_performed")
            metrics.record_metric("avg_confidence", 
                                np.mean([r.confidence for r in results]))
            
            logger.info(f"Hybrid search completed: {len(results)} results")
            
            return results
            
    async def temporal_search(self,
                            query: str,
                            time_range: Tuple[datetime, datetime],
                            num_results: int = 10) -> List[RetrievalResult]:
        """
        Search with temporal context awareness
        
        Args:
            query: Search query
            time_range: Time range for temporal filtering
            num_results: Number of results
            
        Returns:
            Temporally relevant results
        """
        with logger.operation_context("temporal_search",
                                    query=query[:50],
                                    time_range=f"{time_range[0]} to {time_range[1]}"):
            
            if not self.graph_service:
                logger.warning("Temporal search requires Graphiti - falling back to regular search")
                return await self.hybrid_search(query, num_results=num_results)
            
            # Search with temporal filter in graph
            graph_results = await self.graph_service.search_properties(
                query=query,
                num_results=num_results * 2,  # Get more for filtering
                date_filter=time_range
            )
            
            # Convert to retrieval results
            results = []
            for gr in graph_results:
                result = RetrievalResult(
                    content=gr.get("context", ""),
                    source="graph_temporal",
                    relevance_score=gr.get("relevance_score", 0.5),
                    graph_context=gr,
                    temporal_context=gr.get("temporal_context"),
                    relationships=gr.get("connections", []),
                    confidence=gr.get("relevance_score", 0.5) * 0.9  # Boost for temporal match
                )
                results.append(result)
            
            # Limit results
            results = results[:num_results]
            
            logger.info(f"Temporal search completed: {len(results)} results")
            
            return results
            
    async def relationship_search(self,
                                 entity: str,
                                 relationship_types: List[str] = None,
                                 max_hops: int = 2,
                                 num_results: int = 10) -> List[RetrievalResult]:
        """
        Search based on entity relationships in the graph
        
        Args:
            entity: Starting entity (property ID, owner name, etc.)
            relationship_types: Types of relationships to follow
            max_hops: Maximum graph traversal depth
            num_results: Number of results
            
        Returns:
            Related entities and their contexts
        """
        with logger.operation_context("relationship_search",
                                    entity=entity,
                                    max_hops=max_hops):
            
            if not self.graph_service:
                logger.warning("Relationship search requires Graphiti")
                return []
            
            # Find related properties
            related = await self.graph_service.find_related_properties(
                parcel_id=entity,
                relationship_types=relationship_types,
                max_hops=max_hops
            )
            
            # Convert to retrieval results
            results = []
            for rel in related[:num_results]:
                result = RetrievalResult(
                    content=f"Property {rel['parcel_id']} related to {entity}",
                    source="graph_relationship",
                    relevance_score=rel.get("connection_strength", 0.5),
                    graph_context=rel,
                    relationships=rel.get("relationships", []),
                    confidence=min(1.0, rel.get("connection_strength", 0.5) / max_hops)
                )
                results.append(result)
            
            logger.info(f"Relationship search completed: {len(results)} results")
            
            return results
            
    async def _vector_search(self,
                           query: str,
                           filters: Dict[str, Any],
                           num_results: int) -> List[RetrievalResult]:
        """Perform vector similarity search"""
        
        if not self.vector_store:
            return []
        
        # Perform similarity search
        docs_and_scores = self.vector_store.similarity_search_with_score(
            query,
            k=num_results
        )
        
        # Convert to retrieval results
        results = []
        for doc, score in docs_and_scores:
            # Normalize score (FAISS distance to similarity)
            similarity = 1 / (1 + score)  # Convert distance to similarity
            
            result = RetrievalResult(
                content=doc.page_content,
                source="vector",
                relevance_score=similarity,
                confidence=similarity * 0.8  # Vector search baseline confidence
            )
            
            # Add metadata if available
            if doc.metadata:
                result.graph_context = {"metadata": doc.metadata}
            
            results.append(result)
        
        return results
        
    async def _graph_search(self,
                          query: str,
                          filters: Dict[str, Any],
                          num_results: int) -> List[RetrievalResult]:
        """Perform knowledge graph search"""
        
        # Convert filters to date range if applicable
        date_filter = None
        if filters and "date_from" in filters and "date_to" in filters:
            date_filter = (filters["date_from"], filters["date_to"])
        
        # Search in graph
        graph_results = await self.graph_service.search_properties(
            query=query,
            num_results=num_results,
            date_filter=date_filter
        )
        
        # Convert to retrieval results
        results = []
        for gr in graph_results:
            result = RetrievalResult(
                content=gr.get("context", ""),
                source="graph",
                relevance_score=gr.get("relevance_score", 0.5),
                graph_context=gr,
                temporal_context=gr.get("temporal_context"),
                relationships=gr.get("connections", []),
                confidence=gr.get("relevance_score", 0.5) * 0.85  # Graph search confidence
            )
            results.append(result)
        
        return results
        
    async def _rerank_results(self,
                            query: str,
                            results: List[RetrievalResult],
                            num_results: int) -> List[RetrievalResult]:
        """Rerank results using cross-encoder or LLM"""
        
        # Simple reranking based on source diversity and relevance
        # In production, use a cross-encoder model
        
        # Group by source
        vector_results = [r for r in results if r.source == "vector"]
        graph_results = [r for r in results if r.source == "graph"]
        
        # Interleave results for diversity
        reranked = []
        for i in range(max(len(vector_results), len(graph_results))):
            if i < len(graph_results):
                reranked.append(graph_results[i])
            if i < len(vector_results):
                reranked.append(vector_results[i])
        
        # Deduplicate based on content similarity
        seen_content = set()
        unique_results = []
        
        for result in reranked:
            content_key = result.content[:100]  # Use first 100 chars as key
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_results.append(result)
        
        return unique_results[:num_results]
        
    async def _enhance_with_relationships(self,
                                         results: List[RetrievalResult]) -> List[RetrievalResult]:
        """Enhance results with relationship information from graph"""
        
        for result in results:
            if result.source == "vector" and result.graph_context:
                # Try to find graph relationships for vector results
                metadata = result.graph_context.get("metadata", {})
                
                if "source_id" in metadata:
                    # Query graph for relationships
                    # This is a placeholder - implement actual graph query
                    result.relationships = []
        
        return results
        
    def _calculate_confidence_scores(self,
                                    results: List[RetrievalResult],
                                    query: str) -> List[RetrievalResult]:
        """Calculate final confidence scores for results"""
        
        for result in results:
            # Base confidence from relevance score
            confidence = result.relevance_score
            
            # Boost for source type
            if result.source == "graph":
                confidence *= 1.1  # Graph results have richer context
            elif result.source == "hybrid":
                confidence *= 1.15  # Hybrid results are most confident
            
            # Boost for temporal context
            if result.temporal_context:
                confidence *= 1.05
            
            # Boost for relationships
            if result.relationships:
                confidence *= (1 + 0.02 * len(result.relationships))
            
            # Normalize to [0, 1]
            result.confidence = min(1.0, confidence)
        
        return results
        
    async def _index_property_in_graph(self, doc: Dict[str, Any]):
        """Index a property document in the knowledge graph"""
        
        # Extract property information
        property_data = {
            "parcel_id": doc.get("parcel_id"),
            "address": doc.get("address"),
            "city": doc.get("city", "Unknown"),
            "county": doc.get("county", "Unknown"),
            "property_type": doc.get("property_type"),
            "current_value": doc.get("value"),
            "year_built": doc.get("year_built"),
            "square_feet": doc.get("square_feet")
        }
        
        # Create episode in graph
        episode_text = f"""
        Property Information:
        {doc.get('content', '')}
        
        Metadata:
        - Parcel ID: {property_data['parcel_id']}
        - Address: {property_data['address']}
        - Value: ${property_data['current_value']}
        """
        
        await self.graph_service.graphiti.add_episode(
            name=f"Property_{property_data['parcel_id']}",
            episode_body=episode_text,
            source_description="Document indexing",
            reference_time=datetime.now()
        )


class GraphEnhancedAgent(ConfidenceAgent):
    """
    Agent enhanced with graph-based memory and context
    """
    
    def __init__(self, rag_service: EnhancedRAGService):
        super().__init__(
            agent_id="graph_enhanced_agent",
            name="Graph-Enhanced Property Agent",
            description="Agent with knowledge graph memory"
        )
        self.rag_service = rag_service
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process with graph-enhanced context"""
        
        with logger.operation_context("graph_enhanced_process",
                                     query=input_data.get("query", "")[:50]):
            
            # 1. Retrieve context from graph and vectors
            context_results = await self.rag_service.hybrid_search(
                query=input_data.get("query", ""),
                filters=input_data.get("filters"),
                num_results=5
            )
            
            # 2. Build enhanced context
            enhanced_context = {
                "retrieved_content": [r.content for r in context_results],
                "graph_relationships": [],
                "temporal_context": [],
                "confidence_boost": 0
            }
            
            for result in context_results:
                if result.relationships:
                    enhanced_context["graph_relationships"].extend(result.relationships)
                if result.temporal_context:
                    enhanced_context["temporal_context"].append(result.temporal_context)
                enhanced_context["confidence_boost"] += result.confidence * 0.1
            
            # 3. Add context to input
            input_data["enhanced_context"] = enhanced_context
            
            # 4. Boost confidence based on context quality
            self.confidence_boost = min(0.3, enhanced_context["confidence_boost"])
            
            # 5. Process with enhanced context
            result = await super().process(input_data)
            
            # 6. Store interaction in graph for future reference
            if self.rag_service.graph_service:
                await self.rag_service.graph_service.graphiti.add_episode(
                    name=f"Agent_Interaction_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    episode_body=f"""
                    Query: {input_data.get('query', '')}
                    Context Used: {len(context_results)} sources
                    Confidence: {result.get('confidence', 0)}
                    Result: {result.get('result', 'No result')}
                    """,
                    source_description="Agent interaction",
                    reference_time=datetime.now()
                )
            
            logger.info(f"Processed with graph enhancement: confidence {result.get('confidence', 0):.2f}")
            
            return result


# Example usage
async def demo_enhanced_rag():
    """Demonstrate Enhanced RAG capabilities"""
    
    # Initialize services
    graph_service = PropertyGraphService()
    rag_service = EnhancedRAGService(graph_service)
    
    # Index some documents
    documents = [
        {
            "id": "doc1",
            "type": "property",
            "content": "Beautiful 3-bedroom home in Hollywood, FL. Built in 2005, 2500 sq ft.",
            "metadata": {
                "parcel_id": "064210010010",
                "address": "123 Main St",
                "city": "Hollywood",
                "value": 450000
            }
        },
        {
            "id": "doc2",
            "type": "property",
            "content": "Commercial property in Fort Lauderdale. Prime location for retail.",
            "metadata": {
                "parcel_id": "064210010011",
                "address": "456 Commerce Ave",
                "city": "Fort Lauderdale",
                "value": 1200000
            }
        }
    ]
    
    await rag_service.index_documents(documents)
    print("Documents indexed")
    
    # Perform hybrid search
    results = await rag_service.hybrid_search(
        query="residential properties in Hollywood with good value",
        num_results=5
    )
    
    print("\nHybrid Search Results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Confidence: {result.confidence:.2f}")
        print(f"   Source: {result.source}")
        print(f"   Content: {result.content[:100]}...")
        if result.relationships:
            print(f"   Relationships: {len(result.relationships)}")
    
    # Temporal search
    temporal_results = await rag_service.temporal_search(
        query="properties sold in 2023",
        time_range=(datetime(2023, 1, 1), datetime(2023, 12, 31)),
        num_results=5
    )
    
    print("\nTemporal Search Results:")
    for result in temporal_results[:3]:
        print(f"- {result.content[:100]}...")
        if result.temporal_context:
            print(f"  Time: {result.temporal_context}")
    
    # Test graph-enhanced agent
    agent = GraphEnhancedAgent(rag_service)
    
    agent_result = await agent.process({
        "query": "Find me investment properties in Hollywood",
        "action": "search"
    })
    
    print("\nAgent Result:")
    print(f"Confidence: {agent_result.get('confidence', 0):.2f}")
    print(f"Result: {agent_result.get('result', 'No result')}")


if __name__ == "__main__":
    asyncio.run(demo_enhanced_rag())