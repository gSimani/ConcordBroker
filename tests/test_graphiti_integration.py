"""
Test Suite for Graphiti Integration
Comprehensive tests for graph operations, agents, and monitoring
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import os
from unittest.mock import Mock, AsyncMock, patch

# Set test environment
os.environ["TESTING"] = "true"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "test_password"

from apps.api.graph.property_graph_service import (
    PropertyGraphService, 
    PropertyNode, 
    OwnerNode, 
    TransactionEdge
)
from apps.api.graph.enhanced_rag_service import (
    EnhancedRAGService,
    RetrievalResult,
    GraphEnhancedAgent
)
from apps.api.graph.monitoring import (
    GraphMonitor,
    GraphMetricsDashboard,
    QueryMetric,
    HealthStatus
)
from apps.api.agents.graph_enhanced_agents import (
    GraphEnhancedPropertyAgent,
    GraphEnhancedEntityExtractor,
    GraphAgentOrchestrator
)


# ========================
# Fixtures
# ========================

@pytest.fixture
async def graph_service():
    """Create a test graph service instance"""
    service = PropertyGraphService(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test_password"
    )
    
    # Mock the graphiti client if not available
    if not hasattr(service, 'graphiti'):
        service.graphiti = AsyncMock()
        service.graphiti.add_episode = AsyncMock(return_value=Mock(id="test_episode_id"))
        service.graphiti.search = AsyncMock(return_value=[])
        service.graphiti.build_indices = AsyncMock()
    
    yield service
    
    # Cleanup would go here
    

@pytest.fixture
async def rag_service(graph_service):
    """Create a test RAG service instance"""
    service = EnhancedRAGService(graph_service)
    return service


@pytest.fixture
async def graph_monitor():
    """Create a test graph monitor instance"""
    monitor = GraphMonitor(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="test_password",
        check_interval=1  # Fast checks for testing
    )
    
    # Mock the driver if not available
    monitor.driver = AsyncMock()
    
    yield monitor
    
    if monitor.is_monitoring:
        await monitor.stop()


@pytest.fixture
def sample_property():
    """Create a sample property node"""
    return PropertyNode(
        parcel_id="TEST_001",
        address="123 Test Street",
        city="Test City",
        county="Test County",
        state="FL",
        property_type="Residential",
        current_value=500000,
        year_built=2020,
        square_feet=2000,
        bedrooms=3,
        bathrooms=2
    )


@pytest.fixture
def sample_owner():
    """Create a sample owner node"""
    return OwnerNode(
        name="Test Owner",
        entity_type="person",
        email="test@example.com",
        phone="555-0123"
    )


# ========================
# Property Graph Service Tests
# ========================

class TestPropertyGraphService:
    """Test property graph service operations"""
    
    @pytest.mark.asyncio
    async def test_add_property(self, graph_service, sample_property):
        """Test adding a property to the graph"""
        
        # Add property
        node_id = await graph_service.add_property(sample_property)
        
        # Verify
        assert node_id is not None
        graph_service.graphiti.add_episode.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_owner(self, graph_service, sample_owner):
        """Test adding an owner to the graph"""
        
        # Add owner
        node_id = await graph_service.add_owner(sample_owner)
        
        # Verify
        assert node_id is not None
        graph_service.graphiti.add_episode.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_ownership(self, graph_service):
        """Test creating ownership relationship"""
        
        # Add ownership
        relationship_id = await graph_service.add_ownership(
            parcel_id="TEST_001",
            owner_name="Test Owner",
            ownership_type="current",
            start_date=datetime(2020, 1, 1),
            percentage=100.0
        )
        
        # Verify
        assert relationship_id is not None
        graph_service.graphiti.add_episode.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_add_transaction(self, graph_service):
        """Test adding a transaction"""
        
        transaction = TransactionEdge(
            transaction_type="sale",
            date=datetime(2020, 6, 1),
            amount=500000,
            document_number="DOC123"
        )
        
        # Add transaction
        transaction_id = await graph_service.add_transaction(
            from_owner="Seller",
            to_owner="Buyer",
            parcel_id="TEST_001",
            transaction=transaction
        )
        
        # Verify
        assert transaction_id is not None
        graph_service.graphiti.add_episode.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_search_properties(self, graph_service):
        """Test property search"""
        
        # Mock search results
        mock_results = [
            Mock(
                entity_name="Property_TEST_001",
                score=0.95,
                fact="Property in Test City",
                valid_from="2020-01-01",
                valid_to=None
            )
        ]
        graph_service.graphiti.search = AsyncMock(return_value=mock_results)
        
        # Search
        results = await graph_service.search_properties(
            query="properties in Test City",
            num_results=10
        )
        
        # Verify
        assert len(results) > 0
        assert results[0]["relevance_score"] == 0.95
        
    @pytest.mark.asyncio
    async def test_get_property_history(self, graph_service):
        """Test getting property history"""
        
        # Mock history results
        mock_results = [
            Mock(
                entity_name="Property_TEST_001",
                score=0.9,
                fact="Property sold for $500,000",
                valid_from="2020-06-01",
                valid_to=None
            )
        ]
        graph_service.graphiti.search = AsyncMock(return_value=mock_results)
        
        # Get history
        history = await graph_service.get_property_history("TEST_001")
        
        # Verify
        assert history["parcel_id"] == "TEST_001"
        assert len(history["timeline"]) > 0
        
    @pytest.mark.asyncio
    async def test_find_related_properties(self, graph_service):
        """Test finding related properties"""
        
        # Mock related results
        mock_results = [
            Mock(
                entity_name="Property_TEST_002",
                score=0.8,
                fact="Property owned by same owner",
                valid_from="2021-01-01",
                valid_to=None
            )
        ]
        graph_service.graphiti.search = AsyncMock(return_value=mock_results)
        
        # Find related
        related = await graph_service.find_related_properties(
            parcel_id="TEST_001",
            max_hops=2
        )
        
        # Verify
        assert len(related) > 0
        
    @pytest.mark.asyncio
    async def test_detect_investment_patterns(self, graph_service):
        """Test investment pattern detection"""
        
        # Mock pattern results
        mock_results = [
            Mock(
                entity_name="Property_TEST_001",
                score=0.85,
                fact="John Doe bought property",
                valid_from="2020-01-01",
                valid_to=None
            ),
            Mock(
                entity_name="Property_TEST_002",
                score=0.85,
                fact="John Doe sold property",
                valid_from="2021-01-01",
                valid_to=None
            )
        ]
        graph_service.graphiti.search = AsyncMock(return_value=mock_results)
        
        # Detect patterns
        patterns = await graph_service.detect_investment_patterns(
            owner_name="John Doe",
            time_window=(datetime(2020, 1, 1), datetime(2021, 12, 31))
        )
        
        # Verify
        assert patterns["owner"] == "John Doe"
        assert "total_properties_owned" in patterns


# ========================
# Enhanced RAG Service Tests
# ========================

class TestEnhancedRAGService:
    """Test enhanced RAG service operations"""
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, rag_service):
        """Test hybrid search combining vector and graph"""
        
        # Perform search
        results = await rag_service.hybrid_search(
            query="residential properties in Hollywood",
            num_results=5,
            search_type="hybrid"
        )
        
        # Verify
        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, RetrievalResult)
            assert result.confidence >= 0 and result.confidence <= 1
            
    @pytest.mark.asyncio
    async def test_temporal_search(self, rag_service):
        """Test temporal search with date range"""
        
        # Perform temporal search
        results = await rag_service.temporal_search(
            query="properties sold",
            time_range=(datetime(2020, 1, 1), datetime(2021, 12, 31)),
            num_results=5
        )
        
        # Verify
        assert isinstance(results, list)
        for result in results:
            assert result.temporal_context is not None
            
    @pytest.mark.asyncio
    async def test_relationship_search(self, rag_service):
        """Test relationship-based search"""
        
        # Perform relationship search
        results = await rag_service.relationship_search(
            entity="TEST_001",
            max_hops=2,
            num_results=5
        )
        
        # Verify
        assert isinstance(results, list)
        for result in results:
            assert result.relationships is not None
            
    @pytest.mark.asyncio
    async def test_index_documents(self, rag_service):
        """Test document indexing"""
        
        documents = [
            {
                "id": "doc1",
                "type": "property",
                "content": "Test property description",
                "metadata": {
                    "parcel_id": "TEST_001",
                    "city": "Test City"
                }
            }
        ]
        
        # Index documents
        count = await rag_service.index_documents(documents)
        
        # Verify
        assert count == 1


# ========================
# Graph Enhanced Agents Tests
# ========================

class TestGraphEnhancedAgents:
    """Test graph-enhanced agents"""
    
    @pytest.mark.asyncio
    async def test_property_agent(self, graph_service):
        """Test graph-enhanced property agent"""
        
        agent = GraphEnhancedPropertyAgent(graph_service)
        
        # Process query
        result = await agent.process({
            "query": "Find properties in Test City",
            "action": "search"
        })
        
        # Verify
        assert "confidence" in result
        assert "graph_insights" in result
        assert result["confidence"] >= 0 and result["confidence"] <= 1
        
    @pytest.mark.asyncio
    async def test_entity_extractor(self, graph_service):
        """Test graph-enhanced entity extractor"""
        
        agent = GraphEnhancedEntityExtractor(graph_service)
        
        # Process text
        result = await agent.process({
            "text": "John Doe owns property at 123 Main St"
        })
        
        # Verify
        assert "entities" in result
        assert "summary" in result
        
    @pytest.mark.asyncio
    async def test_agent_orchestrator(self, graph_service):
        """Test agent orchestrator"""
        
        orchestrator = GraphAgentOrchestrator(graph_service)
        
        # Route request
        result = await orchestrator.route_request({
            "type": "search",
            "query": "commercial properties"
        })
        
        # Verify
        assert "orchestration" in result
        assert result["orchestration"]["graph_enabled"] == True
        
    @pytest.mark.asyncio
    async def test_multi_agent_analysis(self, graph_service):
        """Test multi-agent analysis"""
        
        orchestrator = GraphAgentOrchestrator(graph_service)
        
        # Perform analysis
        result = await orchestrator.multi_agent_analysis("TEST_001")
        
        # Verify
        assert result["property_id"] == "TEST_001"
        assert "analyses" in result
        assert "combined_insights" in result


# ========================
# Graph Monitoring Tests
# ========================

class TestGraphMonitoring:
    """Test graph monitoring and metrics"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, graph_monitor):
        """Test health check"""
        
        # Mock health check response
        mock_session = AsyncMock()
        mock_session.run = AsyncMock(side_effect=[
            AsyncMock(single=AsyncMock(return_value={"test": 1})),
            AsyncMock(__aiter__=AsyncMock(return_value=iter([
                {"count": 100, "type": "Property"}
            ]))),
            AsyncMock(__aiter__=AsyncMock(return_value=iter([
                {"count": 50, "type": "OWNS"}
            ])))
        ])
        
        graph_monitor.driver.session = AsyncMock(return_value=mock_session)
        
        # Check health
        health = await graph_monitor.check_health()
        
        # Verify
        assert isinstance(health, HealthStatus)
        assert health.node_count > 0
        assert health.edge_count > 0
        
    @pytest.mark.asyncio
    async def test_record_query(self, graph_monitor):
        """Test recording query metrics"""
        
        # Record queries
        await graph_monitor.record_query(
            query_type="property_search",
            duration=0.5,
            nodes_returned=10,
            success=True
        )
        
        await graph_monitor.record_query(
            query_type="complex_aggregation",
            duration=2.5,
            nodes_returned=0,
            success=False,
            error="Timeout"
        )
        
        # Verify
        assert len(graph_monitor.query_metrics) == 2
        assert graph_monitor.query_metrics[0].success == True
        assert graph_monitor.query_metrics[1].success == False
        
    @pytest.mark.asyncio
    async def test_get_statistics(self, graph_monitor):
        """Test getting statistics"""
        
        # Add some metrics
        await graph_monitor.record_query("test", 0.5, 10, True)
        
        # Mock current health
        graph_monitor.current_health = HealthStatus(
            is_healthy=True,
            neo4j_connected=True,
            graphiti_available=True,
            response_time=0.1,
            node_count=100,
            edge_count=50,
            last_check=datetime.now(),
            errors=[]
        )
        
        # Get statistics
        stats = await graph_monitor.get_statistics()
        
        # Verify
        assert "health" in stats
        assert "performance" in stats
        assert "usage" in stats
        assert "alerts" in stats
        
    @pytest.mark.asyncio
    async def test_monitoring_loop(self, graph_monitor):
        """Test monitoring loop"""
        
        # Mock health check
        graph_monitor.check_health = AsyncMock(return_value=HealthStatus(
            is_healthy=True,
            neo4j_connected=True,
            graphiti_available=True,
            response_time=0.1,
            node_count=100,
            edge_count=50,
            last_check=datetime.now(),
            errors=[]
        ))
        
        # Start monitoring
        await graph_monitor.start()
        
        # Wait for at least one check
        await asyncio.sleep(2)
        
        # Verify
        assert graph_monitor.is_monitoring == True
        assert graph_monitor.current_health is not None
        
        # Stop monitoring
        await graph_monitor.stop()
        assert graph_monitor.is_monitoring == False
        
    @pytest.mark.asyncio
    async def test_dashboard_data(self, graph_monitor):
        """Test dashboard data generation"""
        
        # Setup monitor with data
        graph_monitor.current_health = HealthStatus(
            is_healthy=True,
            neo4j_connected=True,
            graphiti_available=True,
            response_time=0.1,
            node_count=100,
            edge_count=50,
            last_check=datetime.now(),
            errors=[]
        )
        
        # Add query metrics
        for i in range(5):
            metric = QueryMetric(
                query_type="test_query",
                duration=0.1 * (i + 1),
                nodes_returned=10,
                success=True,
                timestamp=datetime.now()
            )
            graph_monitor.query_metrics.append(metric)
        
        # Create dashboard
        dashboard = GraphMetricsDashboard(graph_monitor)
        
        # Get dashboard data
        data = await dashboard.get_dashboard_data()
        
        # Verify
        assert data["status"]["health"] == "healthy"
        assert data["metrics"]["nodes"] == 100
        assert data["metrics"]["edges"] == 50
        assert len(data["charts"]["query_distribution"]) > 0


# ========================
# Integration Tests
# ========================

class TestGraphIntegration:
    """End-to-end integration tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_property_workflow(self, graph_service, rag_service):
        """Test complete property workflow"""
        
        # 1. Add property
        property_node = PropertyNode(
            parcel_id="INT_TEST_001",
            address="456 Integration Ave",
            city="Test City",
            county="Test County",
            current_value=750000,
            year_built=2022
        )
        prop_id = await graph_service.add_property(property_node)
        
        # 2. Add owner
        owner_node = OwnerNode(
            name="Integration Tester",
            entity_type="person",
            email="integration@test.com"
        )
        owner_id = await graph_service.add_owner(owner_node)
        
        # 3. Create ownership
        ownership_id = await graph_service.add_ownership(
            parcel_id="INT_TEST_001",
            owner_name="Integration Tester",
            ownership_type="current",
            start_date=datetime(2022, 1, 1)
        )
        
        # 4. Search for property
        search_results = await rag_service.hybrid_search(
            query="Integration Ave Test City",
            num_results=5
        )
        
        # 5. Get property history
        history = await graph_service.get_property_history("INT_TEST_001")
        
        # Verify workflow
        assert prop_id is not None
        assert owner_id is not None
        assert ownership_id is not None
        assert isinstance(search_results, list)
        assert history["parcel_id"] == "INT_TEST_001"
        
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_agent_with_monitoring(self, graph_service, graph_monitor):
        """Test agent operations with monitoring"""
        
        # Start monitoring
        await graph_monitor.start()
        
        # Create agent
        agent = GraphEnhancedPropertyAgent(graph_service)
        
        # Process multiple queries
        queries = [
            "Find properties in Test City",
            "Show commercial properties",
            "Properties owned by corporations"
        ]
        
        for query in queries:
            # Process query
            result = await agent.process({"query": query})
            
            # Record metric
            await graph_monitor.record_query(
                query_type="agent_query",
                duration=0.5,
                nodes_returned=5,
                success=True
            )
        
        # Get statistics
        stats = await graph_monitor.get_statistics()
        
        # Verify
        assert stats["performance"]["total_queries"] >= 3
        
        # Stop monitoring
        await graph_monitor.stop()


# ========================
# Performance Tests
# ========================

class TestPerformance:
    """Performance and load tests"""
    
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_bulk_property_insert(self, graph_service):
        """Test bulk property insertion performance"""
        
        import time
        
        # Create properties
        properties = []
        for i in range(100):
            properties.append(PropertyNode(
                parcel_id=f"PERF_TEST_{i:04d}",
                address=f"{i} Performance St",
                city="Test City",
                county="Test County",
                current_value=100000 * (i + 1)
            ))
        
        # Measure time
        start_time = time.time()
        
        # Insert properties
        for prop in properties:
            await graph_service.add_property(prop)
        
        elapsed = time.time() - start_time
        
        # Verify performance
        assert elapsed < 30  # Should complete within 30 seconds
        print(f"Inserted {len(properties)} properties in {elapsed:.2f} seconds")
        
    @pytest.mark.asyncio
    @pytest.mark.performance
    async def test_concurrent_searches(self, rag_service):
        """Test concurrent search performance"""
        
        import time
        
        # Create search tasks
        searches = [
            "residential properties",
            "commercial buildings",
            "properties in Hollywood",
            "recent sales",
            "foreclosed properties"
        ]
        
        # Measure time
        start_time = time.time()
        
        # Run searches concurrently
        tasks = [
            rag_service.hybrid_search(query, num_results=10)
            for query in searches
        ]
        
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Verify performance
        assert elapsed < 5  # Should complete within 5 seconds
        assert len(results) == len(searches)
        print(f"Completed {len(searches)} concurrent searches in {elapsed:.2f} seconds")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])