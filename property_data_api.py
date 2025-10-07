#!/usr/bin/env python3
"""
Property Data API
==================
FastAPI endpoints to expose Supabase database analysis and statistics

Usage:
    uvicorn property_data_api:app --reload --port 8001

Endpoints:
    - GET /health - Health check
    - GET /database/schema - Complete database schema
    - GET /database/tables - List all tables with basic stats
    - GET /database/sales-tables - Sales-related tables analysis
    - GET /florida-parcels/stats - Florida parcels statistics
    - GET /florida-parcels/counties - County distribution
    - GET /florida-parcels/completeness - Data completeness analysis
    - GET /property/{parcel_id} - Specific property data
    - GET /search/properties - Property search with filters
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sqlalchemy as sa
from sqlalchemy import create_engine, text, inspect
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Property Data API",
    description="FastAPI endpoints for Supabase property database analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
def get_db_url():
    """Get cleaned database URL"""
    url = os.getenv('DATABASE_URL')
    if url:
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql+psycopg2://', 1)
        if '&supa=' in url:
            url = url.split('&supa=')[0]
        if '&pgbouncer=' in url:
            url = url.split('&pgbouncer=')[0]
        return url
    raise ValueError("No DATABASE_URL found")

# Global database engine
try:
    engine = create_engine(get_db_url(), pool_size=5, max_overflow=10)
except Exception as e:
    print(f"Failed to create database engine: {e}")
    engine = None

def get_db_connection():
    """Get database connection dependency"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection not available")
    return engine.connect()

# Pydantic models
class TableInfo(BaseModel):
    name: str
    type: str
    row_count: int
    column_count: int
    columns: List[Dict[str, Any]]

class DatabaseSchema(BaseModel):
    total_tables: int
    total_views: int
    tables: Dict[str, TableInfo]

class PropertySearch(BaseModel):
    county: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    year: Optional[int] = None
    property_use_code: Optional[str] = None
    limit: int = 100

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@app.get("/database/schema")
async def get_database_schema():
    """Get complete database schema"""
    try:
        with get_db_connection() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            view_names = inspector.get_view_names()

            schema_data = {
                "analysis_timestamp": datetime.now().isoformat(),
                "summary": {
                    "total_tables": len(table_names),
                    "total_views": len(view_names),
                    "table_names": table_names,
                    "view_names": view_names
                },
                "tables": {}
            }

            # Get basic info for each table
            for table_name in table_names[:20]:  # Limit to first 20 for performance
                try:
                    columns = inspector.get_columns(table_name)
                    pk_constraint = inspector.get_pk_constraint(table_name)

                    # Quick row count
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.scalar()

                    schema_data["tables"][table_name] = {
                        "type": "table",
                        "row_count": row_count,
                        "column_count": len(columns),
                        "columns": [{"name": col["name"], "type": str(col["type"])} for col in columns],
                        "primary_keys": pk_constraint.get("constrained_columns", [])
                    }
                except Exception as e:
                    schema_data["tables"][table_name] = {"error": str(e)}

            return schema_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get schema: {e}")

@app.get("/database/tables")
async def get_tables_list():
    """Get list of all tables with basic statistics"""
    try:
        with get_db_connection() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            tables_data = []

            for table_name in table_names:
                try:
                    # Get row count
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    row_count = result.scalar()

                    # Get column count
                    columns = inspector.get_columns(table_name)
                    column_count = len(columns)

                    tables_data.append({
                        "name": table_name,
                        "row_count": row_count,
                        "column_count": column_count,
                        "has_data": row_count > 0
                    })

                except Exception as e:
                    tables_data.append({
                        "name": table_name,
                        "error": str(e)
                    })

            # Sort by row count descending
            tables_data.sort(key=lambda x: x.get("row_count", 0), reverse=True)

            return {
                "timestamp": datetime.now().isoformat(),
                "total_tables": len(tables_data),
                "tables": tables_data
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {e}")

@app.get("/database/sales-tables")
async def get_sales_tables():
    """Get information about sales-related tables"""
    try:
        with get_db_connection() as conn:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()

            # Look for sales-related tables
            sales_keywords = ['sale', 'sales', 'sdf', 'transaction', 'transfer', 'deed']
            sales_tables = []

            for table_name in table_names:
                table_name_lower = table_name.lower()
                if any(keyword in table_name_lower for keyword in sales_keywords):
                    try:
                        # Get basic info
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                        row_count = result.scalar()

                        columns = inspector.get_columns(table_name)
                        sales_columns = [
                            col["name"] for col in columns
                            if any(sales_word in col["name"].lower() for sales_word in ['sale', 'price', 'amount', 'value', 'date'])
                        ]

                        sales_tables.append({
                            "table_name": table_name,
                            "row_count": row_count,
                            "column_count": len(columns),
                            "sales_columns": sales_columns,
                            "keywords_matched": [kw for kw in sales_keywords if kw in table_name_lower]
                        })

                    except Exception as e:
                        sales_tables.append({
                            "table_name": table_name,
                            "error": str(e)
                        })

            return {
                "timestamp": datetime.now().isoformat(),
                "sales_tables_found": len(sales_tables),
                "tables": sales_tables
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sales tables: {e}")

@app.get("/florida-parcels/stats")
async def get_florida_parcels_stats():
    """Get basic statistics for florida_parcels table"""
    try:
        with get_db_connection() as conn:
            # Basic counts
            basic_stats = conn.execute(text("""
                SELECT
                    COUNT(*) as total_records,
                    COUNT(DISTINCT parcel_id) as unique_parcels,
                    COUNT(DISTINCT county) as unique_counties,
                    MIN(year) as earliest_year,
                    MAX(year) as latest_year
                FROM florida_parcels
            """)).fetchone()

            # Value statistics
            value_stats = conn.execute(text("""
                SELECT
                    COUNT(CASE WHEN just_value > 0 THEN 1 END) as properties_with_value,
                    AVG(CASE WHEN just_value > 0 THEN just_value END) as avg_just_value,
                    MAX(just_value) as max_just_value
                FROM florida_parcels
            """)).fetchone()

            return {
                "timestamp": datetime.now().isoformat(),
                "basic_statistics": {
                    "total_records": basic_stats[0],
                    "unique_parcels": basic_stats[1],
                    "unique_counties": basic_stats[2],
                    "earliest_year": basic_stats[3],
                    "latest_year": basic_stats[4]
                },
                "value_statistics": {
                    "properties_with_value": value_stats[0],
                    "avg_just_value": float(value_stats[1]) if value_stats[1] else 0,
                    "max_just_value": float(value_stats[2]) if value_stats[2] else 0
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get florida_parcels stats: {e}")

@app.get("/florida-parcels/counties")
async def get_counties_distribution():
    """Get county distribution for florida_parcels"""
    try:
        with get_db_connection() as conn:
            county_dist = conn.execute(text("""
                SELECT
                    county,
                    COUNT(*) as property_count,
                    COUNT(DISTINCT year) as year_coverage,
                    AVG(CASE WHEN just_value > 0 THEN just_value END) as avg_value
                FROM florida_parcels
                WHERE county IS NOT NULL
                GROUP BY county
                ORDER BY property_count DESC
                LIMIT 50
            """)).fetchall()

            counties = [
                {
                    "county": row[0],
                    "property_count": row[1],
                    "year_coverage": row[2],
                    "avg_value": float(row[3]) if row[3] else 0
                }
                for row in county_dist
            ]

            return {
                "timestamp": datetime.now().isoformat(),
                "total_counties": len(counties),
                "counties": counties
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get counties: {e}")

@app.get("/florida-parcels/completeness")
async def get_data_completeness():
    """Get data completeness analysis for key fields"""
    key_fields = [
        'parcel_id', 'county', 'year', 'phy_addr1', 'owner_name1',
        'just_value', 'land_value', 'building_value', 'land_sqft'
    ]

    try:
        with get_db_connection() as conn:
            completeness_data = {}

            for field in key_fields:
                try:
                    result = conn.execute(text(f"""
                        SELECT
                            COUNT(*) as total,
                            COUNT({field}) as non_null,
                            ROUND(COUNT({field}) * 100.0 / COUNT(*), 2) as completeness_percentage
                        FROM florida_parcels
                    """)).fetchone()

                    completeness_data[field] = {
                        "total_records": result[0],
                        "non_null_records": result[1],
                        "completeness_percentage": float(result[2])
                    }

                except Exception as e:
                    completeness_data[field] = {"error": str(e)}

            return {
                "timestamp": datetime.now().isoformat(),
                "analyzed_fields": key_fields,
                "completeness": completeness_data
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get completeness data: {e}")

@app.get("/property/{parcel_id}")
async def get_property_data(parcel_id: str):
    """Get data for a specific property across all relevant tables"""
    try:
        with get_db_connection() as conn:
            property_data = {}

            # Search in florida_parcels
            parcels_data = conn.execute(text("""
                SELECT * FROM florida_parcels
                WHERE parcel_id = :parcel_id
                ORDER BY year DESC
                LIMIT 10
            """), {"parcel_id": parcel_id}).fetchall()

            if parcels_data:
                columns = conn.execute(text("SELECT * FROM florida_parcels LIMIT 1")).keys()
                property_data["florida_parcels"] = {
                    "found": True,
                    "record_count": len(parcels_data),
                    "records": [
                        {col: (row[i].isoformat() if hasattr(row[i], 'isoformat') else row[i])
                         for i, col in enumerate(columns)}
                        for row in parcels_data
                    ]
                }

            # Search in property_sales_history
            sales_data = conn.execute(text("""
                SELECT * FROM property_sales_history
                WHERE parcel_id = :parcel_id
                ORDER BY sale_date DESC
                LIMIT 10
            """), {"parcel_id": parcel_id}).fetchall()

            if sales_data:
                columns = conn.execute(text("SELECT * FROM property_sales_history LIMIT 1")).keys()
                property_data["property_sales_history"] = {
                    "found": True,
                    "record_count": len(sales_data),
                    "records": [
                        {col: (row[i].isoformat() if hasattr(row[i], 'isoformat') else row[i])
                         for i, col in enumerate(columns)}
                        for row in sales_data
                    ]
                }

            # Search in tax_certificates
            tax_data = conn.execute(text("""
                SELECT * FROM tax_certificates
                WHERE parcel_id = :parcel_id
                LIMIT 10
            """), {"parcel_id": parcel_id}).fetchall()

            if tax_data:
                columns = conn.execute(text("SELECT * FROM tax_certificates LIMIT 1")).keys()
                property_data["tax_certificates"] = {
                    "found": True,
                    "record_count": len(tax_data),
                    "records": [
                        {col: (row[i].isoformat() if hasattr(row[i], 'isoformat') else row[i])
                         for i, col in enumerate(columns)}
                        for row in tax_data
                    ]
                }

            if not property_data:
                raise HTTPException(status_code=404, detail=f"Property {parcel_id} not found")

            return {
                "timestamp": datetime.now().isoformat(),
                "parcel_id": parcel_id,
                "data_sources": list(property_data.keys()),
                "property_data": property_data
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get property data: {e}")

@app.post("/search/properties")
async def search_properties(search: PropertySearch):
    """Search properties with filters"""
    try:
        with get_db_connection() as conn:
            # Build dynamic query
            conditions = ["1=1"]  # Base condition
            params = {}

            if search.county:
                conditions.append("county = :county")
                params["county"] = search.county

            if search.min_value:
                conditions.append("just_value >= :min_value")
                params["min_value"] = search.min_value

            if search.max_value:
                conditions.append("just_value <= :max_value")
                params["max_value"] = search.max_value

            if search.year:
                conditions.append("year = :year")
                params["year"] = search.year

            if search.property_use_code:
                conditions.append("property_use_code = :property_use_code")
                params["property_use_code"] = search.property_use_code

            where_clause = " AND ".join(conditions)
            query = f"""
                SELECT
                    parcel_id, county, year, phy_addr1, owner_name1,
                    just_value, land_value, building_value, property_use_code
                FROM florida_parcels
                WHERE {where_clause}
                ORDER BY just_value DESC
                LIMIT :limit
            """

            params["limit"] = min(search.limit, 1000)  # Cap at 1000 results

            results = conn.execute(text(query), params).fetchall()

            properties = [
                {
                    "parcel_id": row[0],
                    "county": row[1],
                    "year": row[2],
                    "address": row[3],
                    "owner": row[4],
                    "just_value": float(row[5]) if row[5] else 0,
                    "land_value": float(row[6]) if row[6] else 0,
                    "building_value": float(row[7]) if row[7] else 0,
                    "property_use_code": row[8]
                }
                for row in results
            ]

            return {
                "timestamp": datetime.now().isoformat(),
                "search_filters": search.dict(),
                "result_count": len(properties),
                "properties": properties
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Property Data API",
        "version": "1.0.0",
        "endpoints": [
            "/health",
            "/database/schema",
            "/database/tables",
            "/database/sales-tables",
            "/florida-parcels/stats",
            "/florida-parcels/counties",
            "/florida-parcels/completeness",
            "/property/{parcel_id}",
            "/search/properties"
        ],
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)