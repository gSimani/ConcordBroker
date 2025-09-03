"""
Parcels Router
Endpoints for property parcel data
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel

from ..database import db
from ..services.score import ScoringService
from ..dependencies import get_current_user

router = APIRouter()
scoring_service = ScoringService()


class ParcelSearchResponse(BaseModel):
    """Parcel search result"""
    folio: str
    city: str
    main_use: str
    sub_use: Optional[str]
    situs_addr: Optional[str]
    owner_raw: Optional[str]
    just_value: Optional[float]
    assessed_soh: Optional[float]
    taxable: Optional[float]
    land_sf: Optional[int]
    score: Optional[float]
    last_sale_date: Optional[str]
    last_sale_price: Optional[float]


class ParcelDetailResponse(BaseModel):
    """Detailed parcel information"""
    folio: str
    city: str
    main_use: str
    sub_use: Optional[str]
    situs_addr: Optional[str]
    mailing_addr: Optional[str]
    owner_raw: Optional[str]
    just_value: Optional[float]
    assessed_soh: Optional[float]
    taxable: Optional[float]
    land_sf: Optional[int]
    bldg_sf: Optional[int]
    year_built: Optional[int]
    score: Optional[float]
    sales: List[dict]
    documents: List[dict]
    entity: Optional[dict]


@router.get("/search", response_model=List[ParcelSearchResponse])
async def search_parcels(
    city: Optional[str] = Query(None, description="City name"),
    main_use: Optional[str] = Query(None, description="Main use code (00-99)"),
    sub_use: Optional[str] = Query(None, description="Sub use code"),
    min_value: Optional[float] = Query(None, description="Minimum just value"),
    max_value: Optional[float] = Query(None, description="Maximum just value"),
    min_score: Optional[float] = Query(None, description="Minimum investment score"),
    limit: int = Query(100, le=1000, description="Maximum results"),
    offset: int = Query(0, description="Pagination offset")
):
    """Search for parcels with filters"""
    
    try:
        results = await db.search_parcels(
            city=city,
            main_use=main_use,
            sub_use=sub_use,
            min_value=min_value,
            max_value=max_value,
            min_score=min_score,
            limit=limit,
            offset=offset
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{folio}", response_model=ParcelDetailResponse)
async def get_parcel(folio: str):
    """Get detailed parcel information"""
    
    parcel = await db.get_parcel_details(folio)
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    return parcel


@router.post("/{folio}/score")
async def calculate_parcel_score(folio: str):
    """Calculate or recalculate investment score for a parcel"""
    
    # Get parcel data
    parcel = await db.get_parcel_details(folio)
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Get comparables
    comparables = await db.search_parcels(
        city=parcel['city'],
        main_use=parcel['main_use'],
        limit=20
    )
    
    # Calculate score
    score = scoring_service.calculate_score(parcel, comparables)
    
    # Update in database
    await db.execute(
        """
        UPDATE parcels 
        SET score = $1, score_updated_at = NOW()
        WHERE folio = $2
        """,
        score.total_score,
        folio
    )
    
    return {
        "folio": folio,
        "score": score.total_score,
        "breakdown": score.breakdown,
        "factors": score.factors,
        "confidence": score.confidence,
        "interpretation": scoring_service.get_score_interpretation(score.total_score)
    }


@router.get("/{folio}/comparables")
async def get_comparables(
    folio: str,
    radius: int = Query(5, description="Search radius in miles"),
    limit: int = Query(20, description="Maximum comparables")
):
    """Get comparable properties for a parcel"""
    
    # Get base parcel
    parcel = await db.get_parcel_details(folio)
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Find comparables (simplified - in production would use geographic query)
    comparables = await db.search_parcels(
        city=parcel['city'],
        main_use=parcel['main_use'],
        limit=limit
    )
    
    # Filter out the subject property
    comparables = [c for c in comparables if c['folio'] != folio]
    
    return {
        "subject": parcel,
        "comparables": comparables,
        "count": len(comparables)
    }


@router.post("/{folio}/watch")
async def add_to_watchlist(
    folio: str,
    user=Depends(get_current_user)
):
    """Add parcel to user's watchlist"""
    
    # Verify parcel exists
    parcel = await db.fetch_one(
        "SELECT folio FROM parcels WHERE folio = $1",
        folio
    )
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    
    # Add to watchlist
    await db.execute(
        """
        INSERT INTO watchlist (user_id, folio, alert_on_change)
        VALUES ($1, $2, true)
        ON CONFLICT (user_id, folio) DO NOTHING
        """,
        user['id'],
        folio
    )
    
    return {"message": "Added to watchlist", "folio": folio}


@router.delete("/{folio}/watch")
async def remove_from_watchlist(
    folio: str,
    user=Depends(get_current_user)
):
    """Remove parcel from user's watchlist"""
    
    result = await db.execute(
        """
        DELETE FROM watchlist
        WHERE user_id = $1 AND folio = $2
        """,
        user['id'],
        folio
    )
    
    return {"message": "Removed from watchlist", "folio": folio}