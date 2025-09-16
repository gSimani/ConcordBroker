"""
Graph API Routes for Graphiti Integration
Provides endpoints for knowledge graph operations
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/graph", tags=["Knowledge Graph"])


# ========================
# Request/Response Models
# ========================

class PropertyInput(BaseModel):
    """Input model for adding a property"""
    parcel_id: str = Field(..., description="Property parcel ID")
    address: str = Field(..., description="Property address")
    city: str = Field(..., description="City")
    county: str = Field(..., description="County")
    state: str = Field(default="FL", description="State")
    property_type: Optional[str] = Field(None, description="Property type")
    current_value: Optional[float] = Field(None, description="Current value")
    year_built: Optional[int] = Field(None, description="Year built")
    square_feet: Optional[int] = Field(None, description="Square footage")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms")


class OwnerInput(BaseModel):
    """Input model for adding an owner"""
    name: str = Field(..., description="Owner name")
    entity_type: str = Field(..., description="Entity type (person, corporation, trust)")
    sunbiz_id: Optional[str] = Field(None, description="Sunbiz ID for corporations")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    address: Optional[str] = Field(None, description="Mailing address")


class OwnershipInput(BaseModel):
    """Input model for creating ownership relationship"""
    parcel_id: str = Field(..., description="Property parcel ID")
    owner_name: str = Field(..., description="Owner name")
    ownership_type: str = Field(default="current", description="Ownership type")
    start_date: Optional[datetime] = Field(None, description="Ownership start date")
    end_date: Optional[datetime] = Field(None, description="Ownership end date")
    percentage: float = Field(default=100.0, description="Ownership percentage")


class TransactionInput(BaseModel):
    """Input model for adding a transaction"""
    from_owner: str = Field(..., description="Seller name")
    to_owner: str = Field(..., description="Buyer name")
    parcel_id: str = Field(..., description="Property parcel ID")
    transaction_type: str = Field(..., description="Transaction type (sale, tax_deed, foreclosure)")
    date: datetime = Field(..., description="Transaction date")
    amount: Optional[float] = Field(None, description="Transaction amount")
    document_number: Optional[str] = Field(None, description="Document number")


class SearchQuery(BaseModel):
    """Search query model"""
    query: str = Field(..., description="Search query")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")
    num_results: int = Field(default=10, ge=1, le=100, description="Number of results")
    search_type: str = Field(default="hybrid", pattern="^(vector|graph|hybrid)$")
    date_from: Optional[datetime] = Field(None, description="Date range start")
    date_to: Optional[datetime] = Field(None, description="Date range end")


# ========================
# Dependency Functions
# ========================

async def get_graph_service():
    """Get graph service instance"""
    from fastapi import Request
    from ...graph.property_graph_service import PropertyGraphService
    
    # In production, this would get the service from app state
    # For now, create a new instance
    try:
        service = PropertyGraphService()
        return service
    except Exception as e:
        logger.error(f"Failed to get graph service: {e}")
        raise HTTPException(status_code=503, detail="Graph service unavailable")


async def get_rag_service():
    """Get enhanced RAG service instance"""
    from fastapi import Request
    from ...graph.enhanced_rag_service import EnhancedRAGService
    
    try:
        graph_service = await get_graph_service()
        rag_service = EnhancedRAGService(graph_service)
        return rag_service
    except Exception as e:
        logger.error(f"Failed to get RAG service: {e}")
        raise HTTPException(status_code=503, detail="RAG service unavailable")


# ========================
# Property Endpoints
# ========================

@router.post("/property", response_model=Dict[str, Any])
async def add_property(
    property_data: PropertyInput,
    graph_service = Depends(get_graph_service)
):
    """Add a property to the knowledge graph"""
    try:
        from ...graph.property_graph_service import PropertyNode
        
        # Create property node
        property_node = PropertyNode(
            parcel_id=property_data.parcel_id,
            address=property_data.address,
            city=property_data.city,
            county=property_data.county,
            state=property_data.state,
            property_type=property_data.property_type,
            current_value=property_data.current_value,
            year_built=property_data.year_built,
            square_feet=property_data.square_feet,
            bedrooms=property_data.bedrooms,
            bathrooms=property_data.bathrooms
        )
        
        # Add to graph
        node_id = await graph_service.add_property(property_node)
        
        return {
            "success": True,
            "node_id": node_id,
            "parcel_id": property_data.parcel_id,
            "message": "Property added successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to add property: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/property/{parcel_id}/history")
async def get_property_history(
    parcel_id: str,
    graph_service = Depends(get_graph_service)
):
    """Get temporal history of a property"""
    try:
        history = await graph_service.get_property_history(parcel_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Property not found")
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get property history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/property/{parcel_id}/related")
async def get_related_properties(
    parcel_id: str,
    max_hops: int = Query(2, ge=1, le=3, description="Maximum graph traversal depth"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results"),
    graph_service = Depends(get_graph_service)
):
    """Find properties related through ownership or transactions"""
    try:
        related = await graph_service.find_related_properties(
            parcel_id=parcel_id,
            max_hops=max_hops
        )
        
        # Limit results
        related = related[:limit]
        
        return {
            "parcel_id": parcel_id,
            "max_hops": max_hops,
            "related_properties": related,
            "count": len(related)
        }
        
    except Exception as e:
        logger.error(f"Failed to find related properties: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Owner Endpoints
# ========================

@router.post("/owner", response_model=Dict[str, Any])
async def add_owner(
    owner_data: OwnerInput,
    graph_service = Depends(get_graph_service)
):
    """Add an owner to the knowledge graph"""
    try:
        from ...graph.property_graph_service import OwnerNode
        
        # Create owner node
        owner_node = OwnerNode(
            name=owner_data.name,
            entity_type=owner_data.entity_type,
            sunbiz_id=owner_data.sunbiz_id,
            phone=owner_data.phone,
            email=owner_data.email,
            address=owner_data.address
        )
        
        # Add to graph
        node_id = await graph_service.add_owner(owner_node)
        
        return {
            "success": True,
            "node_id": node_id,
            "owner_name": owner_data.name,
            "message": "Owner added successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to add owner: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/owner/{owner_name}/patterns")
async def get_investment_patterns(
    owner_name: str,
    start_date: Optional[datetime] = Query(None, description="Analysis start date"),
    end_date: Optional[datetime] = Query(None, description="Analysis end date"),
    graph_service = Depends(get_graph_service)
):
    """Detect investment patterns for an owner"""
    try:
        time_window = None
        if start_date and end_date:
            time_window = (start_date, end_date)
        
        patterns = await graph_service.detect_investment_patterns(
            owner_name=owner_name,
            time_window=time_window
        )
        
        return patterns
        
    except Exception as e:
        logger.error(f"Failed to detect investment patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Relationship Endpoints
# ========================

@router.post("/ownership", response_model=Dict[str, Any])
async def create_ownership(
    ownership_data: OwnershipInput,
    graph_service = Depends(get_graph_service)
):
    """Create ownership relationship between property and owner"""
    try:
        relationship_id = await graph_service.add_ownership(
            parcel_id=ownership_data.parcel_id,
            owner_name=ownership_data.owner_name,
            ownership_type=ownership_data.ownership_type,
            start_date=ownership_data.start_date,
            end_date=ownership_data.end_date,
            percentage=ownership_data.percentage
        )
        
        return {
            "success": True,
            "relationship_id": relationship_id,
            "message": f"Ownership created: {ownership_data.owner_name} -> {ownership_data.parcel_id}"
        }
        
    except Exception as e:
        logger.error(f"Failed to create ownership: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transaction", response_model=Dict[str, Any])
async def add_transaction(
    transaction_data: TransactionInput,
    graph_service = Depends(get_graph_service)
):
    """Add a property transaction to the graph"""
    try:
        from ...graph.property_graph_service import TransactionEdge
        
        # Create transaction edge
        transaction = TransactionEdge(
            transaction_type=transaction_data.transaction_type,
            date=transaction_data.date,
            amount=transaction_data.amount,
            document_number=transaction_data.document_number
        )
        
        # Add to graph
        transaction_id = await graph_service.add_transaction(
            from_owner=transaction_data.from_owner,
            to_owner=transaction_data.to_owner,
            parcel_id=transaction_data.parcel_id,
            transaction=transaction
        )
        
        return {
            "success": True,
            "transaction_id": transaction_id,
            "message": f"Transaction added: {transaction_data.from_owner} -> {transaction_data.to_owner}"
        }
        
    except Exception as e:
        logger.error(f"Failed to add transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Search Endpoints
# ========================

@router.post("/search", response_model=Dict[str, Any])
async def search_graph(
    search_query: SearchQuery,
    rag_service = Depends(get_rag_service)
):
    """Perform hybrid search using Graphiti"""
    try:
        # Prepare date filter
        filters = search_query.filters or {}
        if search_query.date_from:
            filters["date_from"] = search_query.date_from
        if search_query.date_to:
            filters["date_to"] = search_query.date_to
        
        # Perform search
        results = await rag_service.hybrid_search(
            query=search_query.query,
            filters=filters,
            num_results=search_query.num_results,
            search_type=search_query.search_type
        )
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "content": r.content,
                "source": r.source,
                "relevance_score": r.relevance_score,
                "confidence": r.confidence,
                "graph_context": r.graph_context,
                "temporal_context": r.temporal_context,
                "relationships": r.relationships
            })
        
        return {
            "query": search_query.query,
            "search_type": search_query.search_type,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/properties")
async def search_properties(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    graph_service = Depends(get_graph_service)
):
    """Quick property search endpoint"""
    try:
        results = await graph_service.search_properties(
            query=q,
            num_results=limit
        )
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Property search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/temporal")
async def temporal_search(
    query: str = Query(..., description="Search query"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    limit: int = Query(10, ge=1, le=50),
    rag_service = Depends(get_rag_service)
):
    """Search with temporal context"""
    try:
        results = await rag_service.temporal_search(
            query=query,
            time_range=(start_date, end_date),
            num_results=limit
        )
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "content": r.content,
                "temporal_context": r.temporal_context,
                "confidence": r.confidence
            })
        
        return {
            "query": query,
            "time_range": f"{start_date} to {end_date}",
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Temporal search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/relationships/{entity}")
async def search_relationships(
    entity: str,
    max_hops: int = Query(2, ge=1, le=3),
    limit: int = Query(10, ge=1, le=50),
    rag_service = Depends(get_rag_service)
):
    """Search based on entity relationships"""
    try:
        results = await rag_service.relationship_search(
            entity=entity,
            max_hops=max_hops,
            num_results=limit
        )
        
        # Format results
        formatted_results = []
        for r in results:
            formatted_results.append({
                "content": r.content,
                "relationships": r.relationships,
                "confidence": r.confidence
            })
        
        return {
            "entity": entity,
            "max_hops": max_hops,
            "results": formatted_results,
            "count": len(formatted_results)
        }
        
    except Exception as e:
        logger.error(f"Relationship search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Analytics Endpoints
# ========================

@router.get("/stats")
async def get_graph_statistics(
    graph_service = Depends(get_graph_service)
):
    """Get graph database statistics"""
    try:
        # This would need to be implemented in the graph service
        # For now, return mock data
        stats = {
            "total_nodes": 0,
            "total_edges": 0,
            "node_types": {
                "properties": 0,
                "owners": 0,
                "entities": 0
            },
            "edge_types": {
                "ownership": 0,
                "transactions": 0,
                "relationships": 0
            },
            "database_size": "0 MB"
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index/rebuild")
async def rebuild_indices(
    background_tasks: BackgroundTasks,
    graph_service = Depends(get_graph_service)
):
    """Rebuild graph indices for better performance"""
    try:
        # Run in background
        background_tasks.add_task(
            graph_service.graphiti.build_indices
        )
        
        return {
            "success": True,
            "message": "Index rebuild started in background"
        }
        
    except Exception as e:
        logger.error(f"Failed to rebuild indices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========================
# Health Check
# ========================

@router.get("/health")
async def graph_health_check():
    """Check graph service health"""
    try:
        graph_service = await get_graph_service()
        
        # Try a simple query
        await graph_service.search_properties("test", num_results=1)
        
        return {
            "status": "healthy",
            "service": "graph",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "graph",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }