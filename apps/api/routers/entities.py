"""
Entities Router
Endpoints for corporate entity data
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import db

router = APIRouter()


class EntitySearchResponse(BaseModel):
    """Entity search result"""
    id: str
    name: str
    fei_ein: Optional[str]
    status: Optional[str]
    principal_addr: Optional[str]
    created_date: Optional[str]
    property_count: int = 0
    total_value: float = 0


@router.get("/search")
async def search_entities(
    name: Optional[str] = Query(None, description="Entity name search"),
    status: Optional[str] = Query(None, description="Entity status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Search for corporate entities"""
    
    conditions = []
    params = []
    param_count = 0
    
    if name:
        param_count += 1
        conditions.append(f"name_tsv @@ plainto_tsquery('english', ${param_count})")
        params.append(name)
    
    if status:
        param_count += 1
        conditions.append(f"status = ${param_count}")
        params.append(status)
    
    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    
    param_count += 1
    params.append(limit)
    param_count += 1
    params.append(offset)
    
    query = f"""
        SELECT 
            e.*,
            COUNT(DISTINCT pel.folio) as property_count,
            COALESCE(SUM(p.just_value), 0) as total_value
        FROM entities e
        LEFT JOIN parcel_entity_links pel ON e.id = pel.entity_id
        LEFT JOIN parcels p ON pel.folio = p.folio
        {where_clause}
        GROUP BY e.id
        ORDER BY total_value DESC
        LIMIT ${param_count - 1} OFFSET ${param_count}
    """
    
    results = await db.fetch_many(query, *params)
    return results


@router.get("/{entity_id}")
async def get_entity(entity_id: str):
    """Get entity details with portfolio"""
    
    portfolio = await db.get_entity_portfolio(entity_id)
    
    if not portfolio:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    return portfolio


@router.get("/{entity_id}/network")
async def get_entity_network(entity_id: str):
    """Get entity relationship network"""
    
    # Get base entity
    entity = await db.fetch_one(
        "SELECT * FROM entities WHERE id = $1",
        entity_id
    )
    
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    
    # Get officers
    officers = await db.fetch_many(
        "SELECT * FROM officers WHERE entity_id = $1",
        entity_id
    )
    
    # Get related entities through shared officers
    related = await db.fetch_many(
        """
        SELECT DISTINCT e2.*, o2.name as shared_officer
        FROM officers o1
        JOIN officers o2 ON o1.name = o2.name
        JOIN entities e2 ON o2.entity_id = e2.id
        WHERE o1.entity_id = $1 AND e2.id != $1
        """,
        entity_id
    )
    
    return {
        "entity": entity,
        "officers": officers,
        "related_entities": related
    }