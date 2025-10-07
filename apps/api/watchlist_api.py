"""
ConcordBroker Watchlist Management API
Complete FastAPI endpoints for user watchlist and notes functionality
Part of 100% Supabase Integration
"""

import os
import sys
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path as FilePath

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = FilePath(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

# Initialize FastAPI app
app = FastAPI(
    title="ConcordBroker Watchlist API",
    description="Complete watchlist and notes management system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing Supabase configuration")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Pydantic models for request/response validation
class WatchlistItemCreate(BaseModel):
    parcel_id: str = Field(..., description="Property parcel ID")
    county: Optional[str] = Field(None, description="County name")
    property_address: Optional[str] = Field(None, description="Property address")
    owner_name: Optional[str] = Field(None, description="Property owner name")
    market_value: Optional[float] = Field(None, description="Market value")
    notes: Optional[str] = Field("", description="User notes")
    is_favorite: bool = Field(False, description="Favorite status")
    alert_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Alert preferences")

class WatchlistItemUpdate(BaseModel):
    notes: Optional[str] = Field(None, description="Updated notes")
    is_favorite: Optional[bool] = Field(None, description="Updated favorite status")
    alert_preferences: Optional[Dict[str, Any]] = Field(None, description="Updated alert preferences")

class WatchlistItemResponse(BaseModel):
    id: str
    user_id: str
    parcel_id: str
    county: Optional[str]
    property_address: Optional[str]
    owner_name: Optional[str]
    market_value: Optional[float]
    notes: str
    is_favorite: bool
    alert_preferences: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class PropertyNoteCreate(BaseModel):
    parcel_id: str = Field(..., description="Property parcel ID")
    county: Optional[str] = Field(None, description="County name")
    title: Optional[str] = Field(None, description="Note title")
    notes: str = Field(..., description="Note content")
    tags: List[str] = Field(default_factory=list, description="Note tags")
    is_private: bool = Field(True, description="Privacy setting")
    note_type: str = Field("general", description="Note type", regex="^(general|investment|contact|reminder|analysis)$")

class PropertyNoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated title")
    notes: Optional[str] = Field(None, description="Updated content")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    is_private: Optional[bool] = Field(None, description="Updated privacy setting")
    note_type: Optional[str] = Field(None, description="Updated note type", regex="^(general|investment|contact|reminder|analysis)$")

class PropertyNoteResponse(BaseModel):
    id: str
    user_id: str
    parcel_id: str
    county: Optional[str]
    title: Optional[str]
    notes: str
    tags: List[str]
    is_private: bool
    note_type: str
    created_at: datetime
    updated_at: datetime

class BulkWatchlistAdd(BaseModel):
    parcel_ids: List[str] = Field(..., description="List of parcel IDs to add")
    notes: Optional[str] = Field("", description="Common notes for all properties")
    is_favorite: bool = Field(False, description="Favorite status for all properties")

# Dependency for user authentication
async def get_current_user_id(user_id: str = Query(..., description="User ID for authentication")):
    """
    In production, this would validate JWT tokens and extract user ID
    For now, we accept user_id as a query parameter
    """
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_id

# ============================================================================
# WATCHLIST ENDPOINTS
# ============================================================================

@app.get("/api/watchlist", response_model=List[WatchlistItemResponse])
async def get_user_watchlist(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip")
):
    """Get user's complete watchlist"""
    try:
        result = supabase.table('user_watchlists')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Error fetching watchlist for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch watchlist")

@app.post("/api/watchlist", response_model=WatchlistItemResponse)
async def add_to_watchlist(
    item: WatchlistItemCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Add property to user's watchlist"""
    try:
        # Check if item already exists
        existing = supabase.table('user_watchlists')\
            .select('id')\
            .eq('user_id', user_id)\
            .eq('parcel_id', item.parcel_id)\
            .execute()

        if existing.data:
            raise HTTPException(status_code=409, detail="Property already in watchlist")

        # Insert new watchlist item
        result = supabase.table('user_watchlists')\
            .insert({
                'user_id': user_id,
                'parcel_id': item.parcel_id,
                'county': item.county,
                'property_address': item.property_address,
                'owner_name': item.owner_name,
                'market_value': item.market_value,
                'notes': item.notes,
                'is_favorite': item.is_favorite,
                'alert_preferences': item.alert_preferences
            })\
            .execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to add to watchlist")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add to watchlist")

@app.put("/api/watchlist/{parcel_id}", response_model=WatchlistItemResponse)
async def update_watchlist_item(
    parcel_id: str = Path(..., description="Parcel ID of the property to update"),
    updates: WatchlistItemUpdate = ...,
    user_id: str = Depends(get_current_user_id)
):
    """Update watchlist item"""
    try:
        # Prepare update data (only include non-None values)
        update_data = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = supabase.table('user_watchlists')\
            .update(update_data)\
            .eq('user_id', user_id)\
            .eq('parcel_id', parcel_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating watchlist item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update watchlist item")

@app.delete("/api/watchlist/{parcel_id}")
async def remove_from_watchlist(
    parcel_id: str = Path(..., description="Parcel ID of the property to remove"),
    user_id: str = Depends(get_current_user_id)
):
    """Remove property from user's watchlist"""
    try:
        result = supabase.table('user_watchlists')\
            .delete()\
            .eq('user_id', user_id)\
            .eq('parcel_id', parcel_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Watchlist item not found")

        return {"message": "Property removed from watchlist", "parcel_id": parcel_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing from watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to remove from watchlist")

@app.post("/api/watchlist/bulk-add")
async def bulk_add_to_watchlist(
    bulk_data: BulkWatchlistAdd,
    user_id: str = Depends(get_current_user_id)
):
    """Add multiple properties to watchlist"""
    try:
        # Prepare bulk insert data
        insert_data = []
        for parcel_id in bulk_data.parcel_ids:
            insert_data.append({
                'user_id': user_id,
                'parcel_id': parcel_id,
                'notes': bulk_data.notes,
                'is_favorite': bulk_data.is_favorite,
                'alert_preferences': {}
            })

        result = supabase.table('user_watchlists')\
            .insert(insert_data)\
            .execute()

        added_count = len(result.data) if result.data else 0

        return {
            "message": f"Added {added_count} properties to watchlist",
            "added_count": added_count,
            "items": result.data
        }

    except Exception as e:
        logger.error(f"Error bulk adding to watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to bulk add to watchlist")

@app.delete("/api/watchlist/clear")
async def clear_watchlist(
    user_id: str = Depends(get_current_user_id)
):
    """Clear user's entire watchlist"""
    try:
        result = supabase.table('user_watchlists')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()

        return {
            "message": "Watchlist cleared",
            "removed_count": len(result.data) if result.data else 0
        }

    except Exception as e:
        logger.error(f"Error clearing watchlist: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to clear watchlist")

# ============================================================================
# PROPERTY NOTES ENDPOINTS
# ============================================================================

@app.get("/api/property/{parcel_id}/notes", response_model=List[PropertyNoteResponse])
async def get_property_notes(
    parcel_id: str = Path(..., description="Parcel ID of the property"),
    user_id: str = Depends(get_current_user_id)
):
    """Get all notes for a specific property"""
    try:
        result = supabase.table('property_notes')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('parcel_id', parcel_id)\
            .order('created_at', desc=True)\
            .execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Error fetching notes for property {parcel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch property notes")

@app.post("/api/property/{parcel_id}/notes", response_model=PropertyNoteResponse)
async def add_property_note(
    parcel_id: str = Path(..., description="Parcel ID of the property"),
    note: PropertyNoteCreate,
    user_id: str = Depends(get_current_user_id)
):
    """Add note to a property"""
    try:
        result = supabase.table('property_notes')\
            .insert({
                'user_id': user_id,
                'parcel_id': parcel_id,
                'county': note.county,
                'title': note.title,
                'notes': note.notes,
                'tags': note.tags,
                'is_private': note.is_private,
                'note_type': note.note_type
            })\
            .execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to add note")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding note to property {parcel_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add property note")

@app.put("/api/property/notes/{note_id}", response_model=PropertyNoteResponse)
async def update_property_note(
    note_id: str = Path(..., description="ID of the note to update"),
    updates: PropertyNoteUpdate = ...,
    user_id: str = Depends(get_current_user_id)
):
    """Update property note"""
    try:
        # Prepare update data (only include non-None values)
        update_data = {k: v for k, v in updates.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")

        result = supabase.table('property_notes')\
            .update(update_data)\
            .eq('id', note_id)\
            .eq('user_id', user_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Note not found")

        return result.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update note")

@app.delete("/api/property/notes/{note_id}")
async def delete_property_note(
    note_id: str = Path(..., description="ID of the note to delete"),
    user_id: str = Depends(get_current_user_id)
):
    """Delete property note"""
    try:
        result = supabase.table('property_notes')\
            .delete()\
            .eq('id', note_id)\
            .eq('user_id', user_id)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Note not found")

        return {"message": "Note deleted successfully", "note_id": note_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note {note_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete note")

@app.get("/api/notes", response_model=List[PropertyNoteResponse])
async def get_all_user_notes(
    user_id: str = Depends(get_current_user_id),
    note_type: Optional[str] = Query(None, description="Filter by note type"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of notes to return"),
    offset: int = Query(0, ge=0, description="Number of notes to skip")
):
    """Get all notes for a user with optional filtering"""
    try:
        query = supabase.table('property_notes')\
            .select('*')\
            .eq('user_id', user_id)

        if note_type:
            query = query.eq('note_type', note_type)

        if tag:
            query = query.contains('tags', [tag])

        result = query.order('created_at', desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return result.data or []

    except Exception as e:
        logger.error(f"Error fetching user notes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch user notes")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ConcordBroker Watchlist API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(
        "watchlist_api:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )