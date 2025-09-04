"""
Property Management API Routes
Handles all property-related operations with address-based organization
"""

from fastapi import APIRouter, HTTPException, Query, Depends, Body
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
import asyncpg
from supabase import create_client, Client
import os

router = APIRouter(prefix="/api/properties", tags=["properties"])

# Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)


# Pydantic Models
class PropertyBase(BaseModel):
    parcel_id: str
    phy_addr1: Optional[str]
    phy_city: Optional[str]
    phy_zipcd: Optional[str]
    own_name: Optional[str]
    property_type: Optional[str]
    jv: Optional[float]
    tv_sd: Optional[float]
    lnd_val: Optional[float]
    tot_lvg_area: Optional[int]
    lnd_sqfoot: Optional[int]
    act_yr_blt: Optional[int]


class PropertyDetail(BaseModel):
    # Residential
    bedrooms: Optional[int]
    bathrooms: Optional[float]
    garage_spaces: Optional[int]
    pool: Optional[str]
    
    # Commercial
    rentable_area: Optional[int]
    tenant_count: Optional[int]
    occupancy_rate: Optional[float]
    
    # Custom fields
    custom_fields: Optional[Dict[str, Any]]


class PropertyNote(BaseModel):
    note_text: str
    priority: str = "low"  # low, medium, high
    status: str = "open"
    due_date: Optional[date] = None


class PropertyContact(BaseModel):
    contact_type: str = "owner"
    name: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    notes: Optional[str]


class PropertySearchParams(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    owner_name: Optional[str] = None
    property_type: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_sqft: Optional[int] = None
    max_sqft: Optional[int] = None


# CRUD Operations

@router.get("/search")
async def search_properties(
    address: Optional[str] = Query(None, description="Street address"),
    city: Optional[str] = Query(None, description="City name"),
    zip_code: Optional[str] = Query(None, description="ZIP code"),
    owner: Optional[str] = Query(None, description="Owner name"),
    property_type: Optional[str] = Query(None, description="Property type"),
    min_value: Optional[float] = Query(None, description="Minimum value"),
    max_value: Optional[float] = Query(None, description="Maximum value"),
    limit: int = Query(20, le=100),
    offset: int = Query(0)
) -> Dict:
    """
    Search properties by address and other criteria
    Primary search is address-based
    """
    try:
        # Build query
        query = supabase.table('properties').select(
            """
            id, parcel_id, phy_addr1, phy_city, phy_zipcd,
            own_name, property_type, property_subtype,
            jv, tv_sd, lnd_val, tot_lvg_area, lnd_sqfoot, act_yr_blt,
            property_sales!inner(sale_date, sale_price),
            property_notes(id)
            """
        )
        
        # Apply filters - Address is primary
        if address:
            query = query.ilike('phy_addr1', f'%{address}%')
        if city:
            query = query.ilike('phy_city', f'%{city}%')
        if zip_code:
            query = query.eq('phy_zipcd', zip_code)
        if owner:
            query = query.ilike('own_name', f'%{owner}%')
        if property_type:
            query = query.eq('property_type', property_type)
        if min_value:
            query = query.gte('jv', min_value)
        if max_value:
            query = query.lte('jv', max_value)
            
        # Order by address for consistency
        query = query.order('phy_addr1').order('phy_city')
        
        # Pagination
        query = query.range(offset, offset + limit - 1)
        
        response = query.execute()
        
        # Get total count
        count_response = supabase.table('properties').select('*', count='exact', head=True).execute()
        
        return {
            "properties": response.data,
            "total": count_response.count,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/address/{address}")
async def get_property_by_address(
    address: str,
    city: Optional[str] = None
) -> Dict:
    """
    Get property by street address
    This is the primary way to access properties
    """
    try:
        query = supabase.table('properties').select(
            """
            *,
            property_sales(*),
            property_details(*),
            property_notes(*),
            property_contacts(*),
            property_exemptions(*)
            """
        ).ilike('phy_addr1', f'%{address}%')
        
        if city:
            query = query.eq('phy_city', city)
            
        response = query.limit(1).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{property_id}")
async def get_property(property_id: int) -> Dict:
    """Get property by ID with all related data"""
    try:
        response = supabase.table('properties').select(
            """
            *,
            property_sales(*),
            property_details(*),
            property_notes(*),
            property_contacts(*),
            property_exemptions(*)
            """
        ).eq('id', property_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/parcel/{parcel_id}")
async def get_property_by_parcel(parcel_id: str) -> Dict:
    """Get property by parcel ID"""
    try:
        response = supabase.table('properties').select(
            """
            *,
            property_sales(*),
            property_details(*),
            property_notes(*),
            property_contacts(*)
            """
        ).eq('parcel_id', parcel_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Property not found")
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{property_id}/details")
async def update_property_details(
    property_id: int,
    details: PropertyDetail
) -> Dict:
    """Update property type-specific details"""
    try:
        # Check if details exist
        existing = supabase.table('property_details')\
            .select('id')\
            .eq('property_id', property_id)\
            .execute()
        
        details_dict = details.dict(exclude_none=True)
        details_dict['property_id'] = property_id
        details_dict['updated_at'] = datetime.now().isoformat()
        
        if existing.data:
            # Update existing
            response = supabase.table('property_details')\
                .update(details_dict)\
                .eq('property_id', property_id)\
                .execute()
        else:
            # Insert new
            response = supabase.table('property_details')\
                .insert(details_dict)\
                .execute()
                
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{property_id}/notes")
async def add_property_note(
    property_id: int,
    note: PropertyNote,
    author_name: str = "System"
) -> Dict:
    """Add a note to property timeline"""
    try:
        note_dict = note.dict()
        note_dict['property_id'] = property_id
        note_dict['author_name'] = author_name
        
        response = supabase.table('property_notes')\
            .insert(note_dict)\
            .execute()
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notes/{note_id}")
async def update_note(
    note_id: int,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    note_text: Optional[str] = None
) -> Dict:
    """Update a property note"""
    try:
        update_data = {}
        if status:
            update_data['status'] = status
            if status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
        if priority:
            update_data['priority'] = priority
        if note_text:
            update_data['note_text'] = note_text
            
        update_data['updated_at'] = datetime.now().isoformat()
        
        response = supabase.table('property_notes')\
            .update(update_data)\
            .eq('id', note_id)\
            .execute()
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{property_id}/contacts")
async def add_property_contact(
    property_id: int,
    contact: PropertyContact
) -> Dict:
    """Add contact information for a property"""
    try:
        contact_dict = contact.dict(exclude_none=True)
        contact_dict['property_id'] = property_id
        
        # Check if this should be primary
        existing = supabase.table('property_contacts')\
            .select('id')\
            .eq('property_id', property_id)\
            .execute()
            
        if not existing.data:
            contact_dict['is_primary'] = True
            
        response = supabase.table('property_contacts')\
            .insert(contact_dict)\
            .execute()
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{property_id}/watch")
async def add_to_watchlist(
    property_id: int,
    user_id: str,
    reason: Optional[str] = None,
    priority: str = "medium",
    alert_threshold: Optional[float] = 10.0
) -> Dict:
    """Add property to user's watchlist"""
    try:
        watchlist_data = {
            'property_id': property_id,
            'user_id': user_id,
            'reason': reason,
            'priority': priority,
            'alert_threshold_percent': alert_threshold
        }
        
        response = supabase.table('property_watchlist')\
            .insert(watchlist_data)\
            .execute()
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{property_id}/watch")
async def remove_from_watchlist(
    property_id: int,
    user_id: str
) -> Dict:
    """Remove property from watchlist"""
    try:
        response = supabase.table('property_watchlist')\
            .delete()\
            .eq('property_id', property_id)\
            .eq('user_id', user_id)\
            .execute()
            
        return {"message": "Property removed from watchlist"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_overview_statistics() -> Dict:
    """Get dashboard overview statistics"""
    try:
        # Get basic property counts and values
        properties_response = supabase.table('properties').select('id,jv', count='exact').execute()
        
        total_properties = properties_response.count or 0
        total_value = sum(prop.get('jv', 0) or 0 for prop in properties_response.data)
        average_value = total_value / total_properties if total_properties > 0 else 0
        
        # Get recent sales count (last 30 days)
        from datetime import timedelta
        date_threshold = (datetime.now() - timedelta(days=30)).date()
        
        sales_response = supabase.table('property_sales')\
            .select('id', count='exact')\
            .gte('sale_date', date_threshold.isoformat())\
            .execute()
        
        recent_sales = sales_response.count or 0
        
        # Get high value properties count (>$1M)
        high_value_response = supabase.table('properties')\
            .select('id', count='exact')\
            .gte('jv', 1000000)\
            .execute()
        
        high_value_count = high_value_response.count or 0
        
        # Get watched properties count
        watched_response = supabase.table('property_watchlist')\
            .select('id', count='exact')\
            .execute()
        
        watched_count = watched_response.count or 0
        
        return {
            'totalProperties': total_properties,
            'totalValue': total_value,
            'averageValue': average_value,
            'recentSales': recent_sales,
            'highValueCount': high_value_count,
            'watchedCount': watched_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-city")
async def get_city_statistics() -> List[Dict]:
    """Get property statistics grouped by city"""
    try:
        # Get city statistics with aggregation
        response = supabase.rpc('get_city_stats').execute()
        
        if response.data:
            return response.data
        
        # Fallback: manual aggregation
        properties = supabase.table('properties')\
            .select('phy_city,jv')\
            .not_.is_('phy_city', 'null')\
            .execute()
        
        city_stats = {}
        for prop in properties.data:
            city = prop.get('phy_city', 'Unknown')
            value = prop.get('jv', 0) or 0
            
            if city not in city_stats:
                city_stats[city] = {
                    'city': city,
                    'propertyCount': 0,
                    'totalValue': 0,
                    'averageValue': 0,
                    'percentChange': 0
                }
            
            city_stats[city]['propertyCount'] += 1
            city_stats[city]['totalValue'] += value
        
        # Calculate averages
        for city_data in city_stats.values():
            if city_data['propertyCount'] > 0:
                city_data['averageValue'] = city_data['totalValue'] / city_data['propertyCount']
        
        return list(city_stats.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/by-type")
async def get_type_statistics() -> List[Dict]:
    """Get property statistics grouped by type"""
    try:
        # Get type statistics
        response = supabase.rpc('get_type_stats').execute()
        
        if response.data:
            return response.data
        
        # Fallback: manual aggregation
        properties = supabase.table('properties')\
            .select('property_type,jv')\
            .not_.is_('property_type', 'null')\
            .execute()
        
        total_count = len(properties.data)
        type_stats = {}
        
        for prop in properties.data:
            prop_type = prop.get('property_type', 'Other')
            value = prop.get('jv', 0) or 0
            
            if prop_type not in type_stats:
                type_stats[prop_type] = {
                    'type': prop_type,
                    'count': 0,
                    'totalValue': 0,
                    'averageValue': 0,
                    'percentage': 0
                }
            
            type_stats[prop_type]['count'] += 1
            type_stats[prop_type]['totalValue'] += value
        
        # Calculate percentages and averages
        for type_data in type_stats.values():
            if total_count > 0:
                type_data['percentage'] = (type_data['count'] / total_count) * 100
            if type_data['count'] > 0:
                type_data['averageValue'] = type_data['totalValue'] / type_data['count']
        
        return list(type_stats.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent-sales")
async def get_recent_sales(
    days: int = Query(30, description="Number of days back"),
    min_price: Optional[float] = None,
    city: Optional[str] = None,
    limit: int = Query(20, le=100)
) -> List[Dict]:
    """Get recent property sales formatted for dashboard"""
    try:
        # Calculate date threshold
        from datetime import timedelta
        date_threshold = (datetime.now() - timedelta(days=days)).date()
        
        query = supabase.table('property_sales').select(
            """
            *,
            properties!inner(
                id, parcel_id, phy_addr1, phy_city, phy_zipcd,
                own_name, property_type, jv
            )
            """
        ).gte('sale_date', date_threshold.isoformat())
        
        if min_price:
            query = query.gte('sale_price', min_price)
        if city:
            query = query.eq('properties.phy_city', city)
            
        query = query.order('sale_date', desc=True).limit(limit)
        
        response = query.execute()
        
        # Transform data for dashboard format
        sales_data = []
        for sale in response.data:
            property_data = sale.get('properties', {})
            sales_data.append({
                'id': property_data.get('id'),
                'address': property_data.get('phy_addr1', 'Unknown Address'),
                'city': property_data.get('phy_city', 'Unknown City'),
                'saleDate': sale.get('sale_date'),
                'salePrice': sale.get('sale_price', 0),
                'propertyType': property_data.get('property_type', 'Unknown')
            })
        
        return sales_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/high-value")
async def get_high_value_properties(
    min_value: float = Query(1000000, description="Minimum value"),
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = Query(20, le=100)
) -> List[Dict]:
    """Get high-value properties"""
    try:
        query = supabase.table('properties').select(
            """
            id, parcel_id, phy_addr1, phy_city, phy_zipcd,
            own_name, property_type, jv, tv_sd, 
            tot_lvg_area, lnd_sqfoot, act_yr_blt
            """
        ).gte('jv', min_value)
        
        if city:
            query = query.eq('phy_city', city)
        if property_type:
            query = query.eq('property_type', property_type)
            
        query = query.order('jv', desc=True).limit(limit)
        
        response = query.execute()
        return response.data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk operations for data import
@router.post("/bulk/import")
async def bulk_import_properties(
    properties: List[Dict] = Body(...),
    update_existing: bool = Query(False)
) -> Dict:
    """Bulk import properties from NAL data"""
    try:
        imported = 0
        updated = 0
        errors = []
        
        for prop_data in properties:
            try:
                # Check if exists
                existing = supabase.table('properties')\
                    .select('id')\
                    .eq('parcel_id', prop_data['parcel_id'])\
                    .execute()
                
                if existing.data and update_existing:
                    # Update
                    supabase.table('properties')\
                        .update(prop_data)\
                        .eq('parcel_id', prop_data['parcel_id'])\
                        .execute()
                    updated += 1
                elif not existing.data:
                    # Insert
                    supabase.table('properties')\
                        .insert(prop_data)\
                        .execute()
                    imported += 1
                    
            except Exception as e:
                errors.append({
                    'parcel_id': prop_data.get('parcel_id'),
                    'error': str(e)
                })
                
        return {
            'imported': imported,
            'updated': updated,
            'errors': len(errors),
            'error_details': errors[:10]  # Return first 10 errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))