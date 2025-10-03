"""
FastAPI Endpoint for DOR Use Code Assignment Service
Provides REST API for use code queries and assignments
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uvicorn

app = FastAPI(
    title="DOR Use Code Assignment API",
    description="API for managing and assigning DOR use codes to Florida properties",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

db_url = SUPABASE_URL.replace('https://', '')
engine = create_engine(
    f"postgresql://postgres.{db_url.split('.')[1]}:{SUPABASE_KEY}@{db_url}:5432/postgres",
    pool_size=10,
    max_overflow=20
)
SessionLocal = sessionmaker(bind=engine)

# Models
class UseCodeInfo(BaseModel):
    use_code: str
    description: str
    category: str
    subcategory: Optional[str]
    count: int
    percentage: float

class PropertyUseCodeUpdate(BaseModel):
    parcel_id: str
    county: str
    year: int
    dor_uc: str
    property_use: str
    property_use_category: str

class AssignmentStatus(BaseModel):
    status: str
    total_properties: int
    assigned: int
    remaining: int
    percentage_complete: float
    timestamp: str

class BulkAssignmentRequest(BaseModel):
    county: Optional[str] = None
    year: int = 2025
    batch_size: int = 10000
    dry_run: bool = False

# Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "DOR Use Code Assignment API",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/use-codes", response_model=List[UseCodeInfo])
async def get_use_codes():
    """Get all DOR use codes with their descriptions"""
    with engine.connect() as conn:
        query = text("""
            SELECT
                duc.use_code,
                duc.use_description,
                duc.category,
                duc.subcategory,
                COUNT(fp.id) as count,
                ROUND(COUNT(fp.id)::numeric / (SELECT COUNT(*) FROM florida_parcels WHERE year = 2025) * 100, 2) as percentage
            FROM dor_use_codes duc
            LEFT JOIN florida_parcels fp ON duc.use_code = fp.dor_uc AND fp.year = 2025
            GROUP BY duc.use_code, duc.use_description, duc.category, duc.subcategory
            ORDER BY count DESC
        """)
        results = conn.execute(query).fetchall()

        return [
            UseCodeInfo(
                use_code=row[0],
                description=row[1],
                category=row[2],
                subcategory=row[3],
                count=row[4],
                percentage=float(row[5])
            )
            for row in results
        ]

@app.get("/use-code/{code}")
async def get_use_code_details(code: str):
    """Get detailed information about a specific use code"""
    with engine.connect() as conn:
        query = text("""
            SELECT
                use_code,
                use_description,
                category,
                subcategory,
                is_residential,
                is_commercial,
                is_industrial,
                is_agricultural,
                is_institutional
            FROM dor_use_codes
            WHERE use_code = :code
        """)
        result = conn.execute(query, {"code": code}).fetchone()

        if not result:
            raise HTTPException(status_code=404, detail=f"Use code {code} not found")

        # Get property count
        count_query = text("""
            SELECT COUNT(*) FROM florida_parcels
            WHERE dor_uc = :code AND year = 2025
        """)
        count = conn.execute(count_query, {"code": code}).fetchone()[0]

        return {
            "use_code": result[0],
            "description": result[1],
            "category": result[2],
            "subcategory": result[3],
            "flags": {
                "residential": result[4],
                "commercial": result[5],
                "industrial": result[6],
                "agricultural": result[7],
                "institutional": result[8]
            },
            "property_count": count
        }

@app.get("/assignment-status", response_model=AssignmentStatus)
async def get_assignment_status(county: Optional[str] = None):
    """Get current DOR use code assignment status"""
    with engine.connect() as conn:
        where_clause = "WHERE year = 2025"
        params = {}

        if county:
            where_clause += " AND county = :county"
            params["county"] = county.upper()

        query = text(f"""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as assigned,
                COUNT(CASE WHEN dor_uc IS NULL OR dor_uc = '' THEN 1 END) as remaining
            FROM florida_parcels
            {where_clause}
        """)
        result = conn.execute(query, params).fetchone()

        total = result[0]
        assigned = result[1]
        remaining = result[2]
        percentage = (assigned / total * 100) if total > 0 else 0

        return AssignmentStatus(
            status="complete" if remaining == 0 else "in_progress",
            total_properties=total,
            assigned=assigned,
            remaining=remaining,
            percentage_complete=round(percentage, 2),
            timestamp=datetime.now().isoformat()
        )

@app.post("/assign-bulk")
async def assign_bulk_use_codes(
    request: BulkAssignmentRequest,
    background_tasks: BackgroundTasks
):
    """Bulk assign DOR use codes to properties missing them"""

    def perform_assignment():
        with engine.connect() as conn:
            where_clause = "WHERE year = :year AND (dor_uc IS NULL OR dor_uc = '')"
            params = {"year": request.year}

            if request.county:
                where_clause += " AND county = :county"
                params["county"] = request.county.upper()

            # Count properties to assign
            count_query = text(f"SELECT COUNT(*) FROM florida_parcels {where_clause}")
            total_to_assign = conn.execute(count_query, params).fetchone()[0]

            if total_to_assign == 0:
                return {"message": "No properties need assignment", "assigned": 0}

            if request.dry_run:
                return {
                    "message": "Dry run - no changes made",
                    "would_assign": total_to_assign
                }

            # Perform bulk assignment
            update_query = text(f"""
                UPDATE florida_parcels
                SET
                    dor_uc = CASE
                        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN '00'
                        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN '02'
                        WHEN (just_value > 500000 AND building_value > 200000) THEN '17'
                        WHEN (building_value > 1000000 AND land_value < 500000) THEN '24'
                        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN '01'
                        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN '10'
                        ELSE '00'
                    END,
                    property_use = CASE
                        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN 'Single Family'
                        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Multi-Family 10+'
                        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
                        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
                        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
                        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Vacant Residential'
                        ELSE 'Single Family'
                    END,
                    property_use_category = CASE
                        WHEN (building_value > 50000 AND building_value > land_value AND just_value < 1000000) THEN 'Residential'
                        WHEN (building_value > 500000 AND building_value > land_value * 2) THEN 'Residential'
                        WHEN (just_value > 500000 AND building_value > 200000) THEN 'Commercial'
                        WHEN (building_value > 1000000 AND land_value < 500000) THEN 'Industrial'
                        WHEN (land_value > building_value * 5 AND land_value > 100000) THEN 'Agricultural'
                        WHEN (land_value > 0 AND (building_value IS NULL OR building_value = 0)) THEN 'Residential'
                        ELSE 'Residential'
                    END
                {where_clause}
            """)

            result = conn.execute(update_query, params)
            conn.commit()

            return {
                "message": "Bulk assignment completed",
                "assigned": result.rowcount,
                "total_to_assign": total_to_assign
            }

    if request.dry_run:
        return perform_assignment()
    else:
        background_tasks.add_task(perform_assignment)
        return {
            "message": "Bulk assignment started in background",
            "status": "processing"
        }

@app.get("/analytics/distribution")
async def get_use_code_distribution(
    county: Optional[str] = None,
    category: Optional[str] = None
):
    """Get distribution analytics for use codes"""
    with engine.connect() as conn:
        where_clause = "WHERE fp.year = 2025"
        params = {}

        if county:
            where_clause += " AND fp.county = :county"
            params["county"] = county.upper()

        if category:
            where_clause += " AND duc.category = :category"
            params["category"] = category

        query = text(f"""
            SELECT
                fp.dor_uc,
                duc.use_description,
                duc.category,
                COUNT(*) as count,
                ROUND(AVG(fp.just_value)::numeric, 2) as avg_value,
                SUM(fp.just_value) as total_value
            FROM florida_parcels fp
            LEFT JOIN dor_use_codes duc ON fp.dor_uc = duc.use_code
            {where_clause}
            GROUP BY fp.dor_uc, duc.use_description, duc.category
            ORDER BY count DESC
            LIMIT 50
        """)
        results = conn.execute(query, params).fetchall()

        return [
            {
                "use_code": row[0],
                "description": row[1],
                "category": row[2],
                "count": row[3],
                "avg_value": float(row[4]) if row[4] else 0,
                "total_value": float(row[5]) if row[5] else 0
            }
            for row in results
        ]

@app.get("/analytics/coverage-by-county")
async def get_coverage_by_county():
    """Get DOR use code coverage statistics by county"""
    with engine.connect() as conn:
        query = text("""
            SELECT
                county,
                COUNT(*) as total,
                COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END) as with_code,
                ROUND(COUNT(CASE WHEN dor_uc IS NOT NULL AND dor_uc != '' THEN 1 END)::numeric / COUNT(*) * 100, 2) as coverage_pct
            FROM florida_parcels
            WHERE year = 2025
            GROUP BY county
            ORDER BY coverage_pct ASC
        """)
        results = conn.execute(query).fetchall()

        return [
            {
                "county": row[0],
                "total_properties": row[1],
                "with_code": row[2],
                "coverage_percentage": float(row[3])
            }
            for row in results
        ]

@app.put("/property/use-code")
async def update_property_use_code(update: PropertyUseCodeUpdate):
    """Update DOR use code for a specific property"""
    with engine.connect() as conn:
        # Validate use code exists
        validate_query = text("SELECT use_code FROM dor_use_codes WHERE use_code = :code")
        valid = conn.execute(validate_query, {"code": update.dor_uc}).fetchone()

        if not valid:
            raise HTTPException(status_code=400, detail=f"Invalid use code: {update.dor_uc}")

        # Update property
        update_query = text("""
            UPDATE florida_parcels
            SET
                dor_uc = :dor_uc,
                property_use = :property_use,
                property_use_category = :property_use_category
            WHERE parcel_id = :parcel_id
            AND county = :county
            AND year = :year
        """)

        result = conn.execute(update_query, {
            "dor_uc": update.dor_uc,
            "property_use": update.property_use,
            "property_use_category": update.property_use_category,
            "parcel_id": update.parcel_id,
            "county": update.county.upper(),
            "year": update.year
        })
        conn.commit()

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Property not found")

        return {
            "message": "Property use code updated successfully",
            "updated": result.rowcount
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)