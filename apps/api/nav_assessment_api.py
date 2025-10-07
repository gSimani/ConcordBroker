"""
NAV Assessment API
Serves Non Ad Valorem assessment data for properties
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="NAV Assessment API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NAVAssessment(BaseModel):
    levy_description_code: str
    function_code: str
    assessment_description: str
    assessment_amount: float
    county_code: int
    county_name: str

class NAVSummary(BaseModel):
    parcel_id: str
    county_code: int
    county_name: str
    assessment_count: int
    total_assessments: float
    tax_year: int
    assessments: List[NAVAssessment]

class NAVAssessmentService:
    def __init__(self, data_dir: str = "../../TEMP/NAV_MOCK_DATA"):
        self.data_dir = Path(data_dir)
        self.county_names = {
            11: "ALACHUA", 12: "BAKER", 13: "BAY", 14: "BRADFORD", 15: "BREVARD",
            16: "BROWARD", 17: "CALHOUN", 18: "CHARLOTTE", 19: "CITRUS", 20: "CLAY",
            21: "COLLIER", 22: "COLUMBIA", 23: "MIAMI-DADE", 24: "DESOTO", 25: "DIXIE",
            26: "DUVAL", 27: "ESCAMBIA", 28: "FLAGLER", 29: "FRANKLIN", 30: "GADSDEN",
            31: "GILCHRIST", 32: "GLADES", 33: "GULF", 34: "HAMILTON", 35: "HARDEE",
            36: "HENDRY", 37: "HERNANDO", 38: "HIGHLANDS", 39: "HILLSBOROUGH", 40: "HOLMES",
            41: "INDIAN RIVER", 42: "JACKSON", 43: "JEFFERSON", 44: "LAFAYETTE", 45: "LAKE",
            46: "LEE", 47: "LEON", 48: "LEVY", 49: "LIBERTY", 50: "MADISON",
            51: "MANATEE", 52: "MARION", 53: "MARTIN", 54: "MONROE", 55: "NASSAU",
            56: "OKALOOSA", 57: "OKEECHOBEE", 58: "ORANGE", 59: "OSCEOLA", 60: "PALM BEACH",
            61: "PASCO", 62: "PINELLAS", 63: "POLK", 64: "PUTNAM", 65: "ST. JOHNS",
            66: "ST. LUCIE", 67: "SANTA ROSA", 68: "SARASOTA", 69: "SEMINOLE", 70: "SUMTER",
            71: "SUWANNEE", 72: "TAYLOR", 73: "UNION", 74: "VOLUSIA", 75: "WAKULLA",
            76: "WALTON", 77: "WASHINGTON"
        }

        # Cache for loaded data
        self._nav_d_cache = {}
        self._nav_n_cache = {}
        self._load_nav_data()

    def _load_nav_data(self):
        """Load NAV data from files into memory cache"""
        try:
            # Load NAV D (detail) files
            nav_d_dir = self.data_dir / "NAV_D"
            if nav_d_dir.exists():
                for file_path in nav_d_dir.glob("NAVD*.TXT"):
                    county_code = int(file_path.name[4:6])
                    self._nav_d_cache[county_code] = self._load_nav_d_file(file_path)
                    logger.info(f"Loaded NAV D data for county {county_code}")

            # Load NAV N (summary) files
            nav_n_dir = self.data_dir / "NAV_N"
            if nav_n_dir.exists():
                for file_path in nav_n_dir.glob("NAVN*.TXT"):
                    county_code = int(file_path.name[4:6])
                    self._nav_n_cache[county_code] = self._load_nav_n_file(file_path)
                    logger.info(f"Loaded NAV N data for county {county_code}")

            logger.info(f"NAV data loaded for {len(self._nav_d_cache)} counties")

        except Exception as e:
            logger.error(f"Error loading NAV data: {e}")

    def _load_nav_d_file(self, file_path: Path) -> Dict[str, List[Dict]]:
        """Load NAV D file and group by parcel ID"""
        parcel_assessments = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 7 and row[0] == 'D':
                        parcel_id = row[2]
                        assessment = {
                            'levy_description_code': row[3],
                            'function_code': row[4],
                            'assessment_description': row[5],
                            'assessment_amount': float(row[6]) if row[6] else 0.0,
                            'county_code': int(row[1])
                        }

                        if parcel_id not in parcel_assessments:
                            parcel_assessments[parcel_id] = []
                        parcel_assessments[parcel_id].append(assessment)

        except Exception as e:
            logger.error(f"Error loading NAV D file {file_path}: {e}")

        return parcel_assessments

    def _load_nav_n_file(self, file_path: Path) -> Dict[str, Dict]:
        """Load NAV N file and index by parcel ID"""
        parcel_summaries = {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 7 and row[0] == 'N':
                        parcel_id = row[2]
                        summary = {
                            'parcel_id': parcel_id,
                            'county_code': int(row[1]),
                            'assessment_count': int(row[3]) if row[3] else 0,
                            'tax_year': int(row[4]) if row[4] else 2024,
                            'total_assessments': float(row[5]) if row[5] else 0.0
                        }
                        parcel_summaries[parcel_id] = summary

        except Exception as e:
            logger.error(f"Error loading NAV N file {file_path}: {e}")

        return parcel_summaries

    def get_nav_assessments(self, parcel_id: str) -> Optional[NAVSummary]:
        """Get NAV assessments for a specific parcel ID"""
        try:
            # Extract county from parcel ID (first 2 digits)
            county_code = int(parcel_id.split('-')[0]) if '-' in parcel_id else None

            if not county_code or county_code not in self._nav_d_cache:
                return None

            # Get assessments from NAV D data
            assessments_data = self._nav_d_cache[county_code].get(parcel_id, [])
            if not assessments_data:
                return None

            # Get summary from NAV N data
            summary_data = self._nav_n_cache.get(county_code, {}).get(parcel_id, {})

            # Build assessment objects
            assessments = []
            total_amount = 0

            for assessment_data in assessments_data:
                assessment = NAVAssessment(
                    levy_description_code=assessment_data['levy_description_code'],
                    function_code=assessment_data['function_code'],
                    assessment_description=assessment_data['assessment_description'],
                    assessment_amount=assessment_data['assessment_amount'],
                    county_code=county_code,
                    county_name=self.county_names.get(county_code, f"County {county_code}")
                )
                assessments.append(assessment)
                total_amount += assessment_data['assessment_amount']

            # Create summary
            nav_summary = NAVSummary(
                parcel_id=parcel_id,
                county_code=county_code,
                county_name=self.county_names.get(county_code, f"County {county_code}"),
                assessment_count=len(assessments),
                total_assessments=total_amount,
                tax_year=summary_data.get('tax_year', 2024),
                assessments=assessments
            )

            return nav_summary

        except Exception as e:
            logger.error(f"Error getting NAV assessments for {parcel_id}: {e}")
            return None

    def get_county_assessment_stats(self, county_code: int) -> Dict[str, Any]:
        """Get assessment statistics for a county"""
        try:
            if county_code not in self._nav_d_cache:
                return {}

            assessments = self._nav_d_cache[county_code]
            summaries = self._nav_n_cache.get(county_code, {})

            total_parcels = len(assessments)
            total_assessments = sum(len(parcel_assessments) for parcel_assessments in assessments.values())
            total_amount = sum(
                sum(assessment['assessment_amount'] for assessment in parcel_assessments)
                for parcel_assessments in assessments.values()
            )

            # Assessment type breakdown
            assessment_types = {}
            for parcel_assessments in assessments.values():
                for assessment in parcel_assessments:
                    desc = assessment['assessment_description']
                    if desc not in assessment_types:
                        assessment_types[desc] = {'count': 0, 'total_amount': 0}
                    assessment_types[desc]['count'] += 1
                    assessment_types[desc]['total_amount'] += assessment['assessment_amount']

            return {
                'county_code': county_code,
                'county_name': self.county_names.get(county_code, f"County {county_code}"),
                'total_parcels': total_parcels,
                'total_assessments': total_assessments,
                'total_amount': total_amount,
                'assessment_types': assessment_types
            }

        except Exception as e:
            logger.error(f"Error getting county stats for {county_code}: {e}")
            return {}

# Initialize service
nav_service = NAVAssessmentService()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "NAV Assessment API"}

@app.get("/api/nav-assessments/{parcel_id}", response_model=Optional[NAVSummary])
async def get_nav_assessments(parcel_id: str):
    """Get NAV assessments for a specific parcel"""
    logger.info(f"Getting NAV assessments for parcel: {parcel_id}")

    nav_data = nav_service.get_nav_assessments(parcel_id)
    if not nav_data:
        raise HTTPException(status_code=404, detail="No NAV assessments found for this parcel")

    return nav_data

@app.get("/api/nav-county-stats/{county_code}")
async def get_county_stats(county_code: int):
    """Get NAV assessment statistics for a county"""
    logger.info(f"Getting NAV stats for county: {county_code}")

    stats = nav_service.get_county_assessment_stats(county_code)
    if not stats:
        raise HTTPException(status_code=404, detail="No NAV data found for this county")

    return stats

@app.get("/api/nav-available-counties")
async def get_available_counties():
    """Get list of counties with NAV data available"""
    available_counties = []

    for county_code in nav_service._nav_d_cache.keys():
        county_name = nav_service.county_names.get(county_code, f"County {county_code}")
        parcel_count = len(nav_service._nav_d_cache[county_code])

        available_counties.append({
            'county_code': county_code,
            'county_name': county_name,
            'parcel_count': parcel_count
        })

    return sorted(available_counties, key=lambda x: x['county_name'])

@app.get("/api/nav-search")
async def search_nav_assessments(
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type"),
    min_amount: Optional[float] = Query(None, description="Minimum assessment amount"),
    max_amount: Optional[float] = Query(None, description="Maximum assessment amount"),
    county_code: Optional[int] = Query(None, description="Filter by county code"),
    limit: int = Query(100, description="Limit results")
):
    """Search NAV assessments with filters"""
    results = []
    count = 0

    # Search through cached data
    for county in nav_service._nav_d_cache.keys():
        if county_code and county != county_code:
            continue

        for parcel_id, assessments in nav_service._nav_d_cache[county].items():
            if count >= limit:
                break

            for assessment in assessments:
                if assessment_type and assessment_type.upper() not in assessment['assessment_description'].upper():
                    continue
                if min_amount and assessment['assessment_amount'] < min_amount:
                    continue
                if max_amount and assessment['assessment_amount'] > max_amount:
                    continue

                results.append({
                    'parcel_id': parcel_id,
                    'county_code': county,
                    'county_name': nav_service.county_names.get(county, f"County {county}"),
                    'assessment_description': assessment['assessment_description'],
                    'assessment_amount': assessment['assessment_amount'],
                    'function_code': assessment['function_code']
                })
                count += 1

                if count >= limit:
                    break

    return {
        'results': results,
        'total_found': len(results),
        'limit': limit
    }

if __name__ == "__main__":
    logger.info("Starting NAV Assessment API on port 8005")
    uvicorn.run(app, host="0.0.0.0", port=8005)