#!/usr/bin/env python3
"""
Simple test API to verify the Supabase fixes work
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uvicorn
import os
from supabase import create_client, Client

app = FastAPI(title="Test API - Fixed Supabase")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
async def root():
    return {"status": "healthy", "message": "Test API with fixed Supabase"}

@app.get("/api/properties/search")
async def search_properties(
    limit: int = Query(10, le=50),
    sortBy: Optional[str] = Query("phy_addr1"),
    sortOrder: Optional[str] = Query("asc")
):
    try:
        query = supabase.table('florida_parcels').select('parcel_id, phy_addr1, phy_city')

        # Apply sorting with CORRECT syntax
        if sortBy and sortOrder:
            if sortOrder.lower() == 'asc':
                query = query.order(sortBy)
            else:
                query = query.order(sortBy, desc=True)

        query = query.limit(limit)
        response = query.execute()

        return {
            "success": True,
            "properties": response.data,
            "count": len(response.data),
            "message": "Fixed API working!"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "API failed"
        }

if __name__ == "__main__":
    uvicorn.run("test_api_fixed:app", host="0.0.0.0", port=8001, reload=False)