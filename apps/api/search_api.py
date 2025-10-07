"""
FastAPI Search API - Unified search interface
Integrates Meilisearch for instant search and Supabase for semantic search
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, List, Any
import meilisearch
from supabase import create_client, Client
import os
import logging
from datetime import datetime
from functools import lru_cache

from search_config import (
    MEILISEARCH_URL,
    MEILISEARCH_KEY,
    PROPERTIES_INDEX,
    FACETS_CONFIG,
    CACHE_TTL
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="ConcordBroker Search API",
    description="Unified property search with Meilisearch and Supabase",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5178", "https://www.concordbroker.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Clients
meili_client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
supabase: Client = create_client(
    os.getenv('SUPABASE_URL', 'https://pmispwtdngkcmsrsjwbp.supabase.co'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY', '')
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Meilisearch
        meili_health = meili_client.health()
        meili_index = meili_client.get_index(PROPERTIES_INDEX)
        meili_stats = meili_index.get_stats()

        # Check Supabase
        supabase_check = supabase.table('florida_parcels').select('parcel_id').limit(1).execute()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "meilisearch": {
                    "status": meili_health['status'],
                    "documents": meili_stats['numberOfDocuments']
                },
                "supabase": {
                    "status": "healthy" if supabase_check.data else "unhealthy"
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=str(e))

@app.get("/api/search/instant")
async def instant_search(
    q: Optional[str] = Query(None, description="Search query"),
    county: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    minValue: Optional[float] = Query(None),
    maxValue: Optional[float] = Query(None),
    minBuildingSqFt: Optional[float] = Query(None),
    maxBuildingSqFt: Optional[float] = Query(None),
    minLandSqFt: Optional[float] = Query(None),
    maxLandSqFt: Optional[float] = Query(None),
    minYear: Optional[int] = Query(None),
    maxYear: Optional[int] = Query(None),
    isTaxDelinquent: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    sortBy: Optional[str] = Query("marketValue"),
    sortOrder: Optional[str] = Query("desc")
):
    """
    Instant search using Meilisearch
    Returns filtered properties with accurate counts and fast facets
    """
    try:
        logger.info(f"Instant search - q={q}, filters={locals()}")

        index = meili_client.get_index(PROPERTIES_INDEX)

        # Build filter string
        filters = []

        if county:
            filters.append(f'county = "{county}"')

        if propertyType:
            filters.append(f'propertyType = "{propertyType}"')

        if minValue is not None:
            filters.append(f'marketValue >= {minValue}')

        if maxValue is not None:
            filters.append(f'marketValue <= {maxValue}')

        if minBuildingSqFt is not None:
            filters.append(f'buildingSqFt >= {minBuildingSqFt}')

        if maxBuildingSqFt is not None:
            filters.append(f'buildingSqFt <= {maxBuildingSqFt}')

        if minLandSqFt is not None:
            filters.append(f'landSqFt >= {minLandSqFt}')

        if maxLandSqFt is not None:
            filters.append(f'landSqFt <= {maxLandSqFt}')

        if minYear is not None:
            filters.append(f'yearBuilt >= {minYear}')

        if maxYear is not None:
            filters.append(f'yearBuilt <= {maxYear}')

        if isTaxDelinquent is not None:
            filters.append(f'isTaxDelinquent = {str(isTaxDelinquent).lower()}')

        filter_string = ' AND '.join(filters) if filters else None

        # Calculate offset
        offset = (page - 1) * limit

        # Build sort
        sort_string = None
        if sortBy:
            direction = "desc" if sortOrder == "desc" else "asc"
            sort_string = [f"{sortBy}:{direction}"]

        # Execute search
        search_params = {
            "limit": limit,
            "offset": offset,
            "attributesToSearchOn": ["parcel_id", "address", "city", "owner_name", "county"] if q else None
        }

        if filter_string:
            search_params["filter"] = filter_string

        if sort_string:
            search_params["sort"] = sort_string

        result = index.search(q or "", search_params)

        # Format response
        return {
            "success": True,
            "query": q,
            "filters": {k: v for k, v in locals().items() if k not in ['q', 'page', 'limit', 'sortBy', 'sortOrder'] and v is not None},
            "data": result['hits'],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": result.get('estimatedTotalHits', 0),
                "pages": (result.get('estimatedTotalHits', 0) + limit - 1) // limit
            },
            "processingTimeMs": result.get('processingTimeMs', 0),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Instant search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/facets")
async def get_facets(
    q: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    propertyType: Optional[str] = Query(None),
    minValue: Optional[float] = Query(None),
    maxValue: Optional[float] = Query(None)
):
    """
    Get facets for filtered search
    Returns available filter options with counts
    """
    try:
        index = meili_client.get_index(PROPERTIES_INDEX)

        # Build filter (same as instant search)
        filters = []
        if county:
            filters.append(f'county = "{county}"')
        if propertyType:
            filters.append(f'propertyType = "{propertyType}"')
        if minValue is not None:
            filters.append(f'marketValue >= {minValue}')
        if maxValue is not None:
            filters.append(f'marketValue <= {maxValue}')

        filter_string = ' AND '.join(filters) if filters else None

        # Get facets
        result = index.search(q or "", {
            "facets": ["county", "propertyType", "yearBuilt", "isTaxDelinquent"],
            "filter": filter_string,
            "limit": 0  # We only want facets, not results
        })

        return {
            "success": True,
            "facets": result.get('facetDistribution', {}),
            "total": result.get('estimatedTotalHits', 0)
        }

    except Exception as e:
        logger.error(f"Facets error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/suggest")
async def autocomplete(
    q: str = Query(..., min_length=1),
    type: str = Query("address", regex="^(address|city|owner)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Autocomplete suggestions
    Fast prefix matching for typeahead
    """
    try:
        index = meili_client.get_index(PROPERTIES_INDEX)

        # Set attributes to search based on type
        attributes = {
            "address": ["address", "phy_addr1"],
            "city": ["city", "phy_city"],
            "owner": ["owner_name", "owner"]
        }

        result = index.search(q, {
            "limit": limit,
            "attributesToSearchOn": attributes[type],
            "attributesToRetrieve": [type, "parcel_id", "county"],
            "attributesToHighlight": [type]
        })

        # Deduplicate suggestions
        seen = set()
        suggestions = []

        for hit in result['hits']:
            value = hit.get(type, '') or hit.get(f'phy_{type}', '') or hit.get(f'{type}_name', '')
            if value and value not in seen:
                seen.add(value)
                suggestions.append({
                    "value": value,
                    "parcel_id": hit.get('parcel_id'),
                    "county": hit.get('county'),
                    "highlight": hit.get('_formatted', {}).get(type, value)
                })

        return {
            "success": True,
            "query": q,
            "type": type,
            "suggestions": suggestions[:limit]
        }

    except Exception as e:
        logger.error(f"Autocomplete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/search/stats")
async def search_stats():
    """Get search index statistics"""
    try:
        index = meili_client.get_index(PROPERTIES_INDEX)
        stats = index.get_stats()

        return {
            "success": True,
            "index": PROPERTIES_INDEX,
            "stats": {
                "totalDocuments": stats['numberOfDocuments'],
                "isIndexing": stats['isIndexing'],
                "fieldDistribution": stats.get('fieldDistribution', {})
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
