#!/usr/bin/env python3
"""
Fast Property Search API using pandas and FastAPI
Optimized for high-performance property search with Supabase backend
"""

import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import requests
import asyncio
import uvicorn
from datetime import datetime, timedelta
import logging
from functools import lru_cache
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase configuration
SUPABASE_URL = "https://pmispwtdngkcmsrsjwbp.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A"

# FastAPI app
app = FastAPI(title="ConcordBroker Property Search API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "https://www.concordbroker.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache for property data
property_cache = {"data": None, "timestamp": None, "ttl": 300}  # 5 minute TTL

class PropertyDataLoader:
    def __init__(self):
        self.headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
        }

    @lru_cache(maxsize=10)
    def load_property_batch(self, offset: int = 0, limit: int = 1000) -> pd.DataFrame:
        """Load a batch of properties with caching"""
        try:
            # Try property_assessments first (most complete data)
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/property_assessments",
                headers=self.headers,
                params={"limit": limit, "offset": offset}
            )

            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    logger.info(f"Loaded {len(df)} properties from property_assessments")
                    return df

            # Fallback to properties table
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/properties",
                headers=self.headers,
                params={"limit": limit, "offset": offset}
            )

            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)
                    logger.info(f"Loaded {len(df)} properties from properties table")
                    return df

            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error loading properties: {e}")
            return pd.DataFrame()

    def get_cached_properties(self) -> pd.DataFrame:
        """Get cached property data or load fresh"""
        now = datetime.now()

        # Check if cache is valid
        if (property_cache["data"] is not None and
            property_cache["timestamp"] is not None and
            (now - property_cache["timestamp"]).seconds < property_cache["ttl"]):
            return property_cache["data"]

        # Load fresh data
        logger.info("Loading fresh property data...")

        # Load multiple batches for better coverage
        all_properties = []
        for i in range(5):  # Load 5 batches = 5000 properties
            batch = self.load_property_batch(offset=i*1000, limit=1000)
            if not batch.empty:
                all_properties.append(batch)
            else:
                break

        if all_properties:
            df = pd.concat(all_properties, ignore_index=True)
            # Clean and optimize the data
            df = self.clean_property_data(df)

            # Cache the result
            property_cache["data"] = df
            property_cache["timestamp"] = now

            logger.info(f"Cached {len(df)} properties")
            return df

        return pd.DataFrame()

    def clean_property_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and optimize property data for search"""
        if df.empty:
            return df

        # Ensure key columns exist
        required_columns = ['parcel_id', 'property_address', 'owner_name']
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''

        # Clean text fields
        text_columns = ['property_address', 'owner_name', 'property_city', 'county_name']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip().str.upper()

        # Clean numeric fields
        numeric_columns = ['just_value', 'assessed_value', 'land_value', 'building_value']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Create search index
        df['search_text'] = (
            df.get('property_address', '') + ' ' +
            df.get('owner_name', '') + ' ' +
            df.get('property_city', '') + ' ' +
            df.get('county_name', '')
        ).str.upper()

        return df

# Initialize data loader
data_loader = PropertyDataLoader()

@app.get("/")
async def root():
    return {"message": "ConcordBroker Fast Property Search API", "status": "running"}

@app.get("/api/properties/search")
async def search_properties(
    address: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0)
):
    """Search properties with optimized pandas filtering"""
    try:
        # Load property data
        df = data_loader.get_cached_properties()

        if df.empty:
            return {"properties": [], "total": 0, "message": "No property data available"}

        # Start with all properties
        filtered_df = df.copy()

        # Apply filters using pandas vectorized operations
        if address:
            address_upper = address.upper()
            mask = filtered_df['search_text'].str.contains(address_upper, na=False)
            filtered_df = filtered_df[mask]

        if city:
            city_upper = city.upper()
            if 'property_city' in filtered_df.columns:
                mask = filtered_df['property_city'].str.contains(city_upper, na=False)
                filtered_df = filtered_df[mask]

        if zip_code:
            if 'property_zip' in filtered_df.columns:
                mask = filtered_df['property_zip'].astype(str).str.contains(str(zip_code), na=False)
                filtered_df = filtered_df[mask]

        if owner:
            owner_upper = owner.upper()
            if 'owner_name' in filtered_df.columns:
                mask = filtered_df['owner_name'].str.contains(owner_upper, na=False)
                filtered_df = filtered_df[mask]

        if min_value is not None:
            if 'just_value' in filtered_df.columns:
                mask = filtered_df['just_value'] >= min_value
                filtered_df = filtered_df[mask]

        if max_value is not None:
            if 'just_value' in filtered_df.columns:
                mask = filtered_df['just_value'] <= max_value
                filtered_df = filtered_df[mask]

        # Get total count
        total = len(filtered_df)

        # Apply pagination
        paginated_df = filtered_df.iloc[offset:offset + limit]

        # Convert to list of dictionaries
        properties = paginated_df.to_dict('records')

        # Clean the results
        for prop in properties:
            # Convert numpy types to Python types
            for key, value in prop.items():
                if pd.isna(value):
                    prop[key] = None
                elif isinstance(value, (np.integer, np.floating)):
                    prop[key] = float(value)

        logger.info(f"Search returned {len(properties)} properties out of {total} matches")

        return {
            "properties": properties,
            "total": total,
            "limit": limit,
            "offset": offset,
            "cached": True
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/api/properties/stats")
async def get_property_stats():
    """Get property statistics"""
    try:
        df = data_loader.get_cached_properties()

        if df.empty:
            return {"total_properties": 0}

        stats = {
            "total_properties": len(df),
            "avg_value": float(df['just_value'].mean()) if 'just_value' in df.columns else 0,
            "total_value": float(df['just_value'].sum()) if 'just_value' in df.columns else 0,
            "counties": df['county_name'].nunique() if 'county_name' in df.columns else 0,
            "last_updated": property_cache["timestamp"].isoformat() if property_cache["timestamp"] else None
        }

        return stats

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.post("/api/properties/refresh")
async def refresh_cache():
    """Manually refresh the property cache"""
    try:
        # Clear the cache
        property_cache["data"] = None
        property_cache["timestamp"] = None

        # Load fresh data
        df = data_loader.get_cached_properties()

        return {
            "message": "Cache refreshed successfully",
            "properties_loaded": len(df),
            "timestamp": property_cache["timestamp"].isoformat() if property_cache["timestamp"] else None
        }

    except Exception as e:
        logger.error(f"Refresh error: {e}")
        raise HTTPException(status_code=500, detail=f"Refresh failed: {str(e)}")

if __name__ == "__main__":
    print("Starting Fast Property Search API...")
    print("Using pandas for optimized data processing")
    print("Endpoints:")
    print("   - GET /api/properties/search - Search properties")
    print("   - GET /api/properties/stats - Get statistics")
    print("   - POST /api/properties/refresh - Refresh cache")
    print("API running on http://localhost:8000")

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")