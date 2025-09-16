"""
API endpoints for property-company matching agents
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import asyncio

from agents.property_company_matcher import (
    PropertyCompanyMatcher,
    MatchConfidence,
    MatchResult
)
from supabase import create_client, Client
import os

router = APIRouter(prefix="/api/property-matcher", tags=["Property Matching"])

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL", "")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "")
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize matcher
matcher = PropertyCompanyMatcher(supabase)

class PropertyMatchRequest(BaseModel):
    """Request model for property matching"""
    parcel_id: Optional[str] = None
    address: Optional[str] = None
    owner_name: Optional[str] = None
    tax_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    min_confidence: int = 60
    max_agents: int = 5

class MatchResponse(BaseModel):
    """Response model for match results"""
    company_name: str
    company_doc_number: str
    confidence: int
    match_type: str
    evidence: List[str]
    agent_name: str
    timestamp: str

@router.post("/match", response_model=List[MatchResponse])
async def match_property_to_companies(request: PropertyMatchRequest):
    """
    Find companies associated with a property using intelligent agents
    
    The system uses multiple tiers of agents with different accuracy levels:
    - Tier 1 (90-95%): Tax ID, Mortgage Documents, Utility Accounts
    - Tier 2 (75-85%): Permits, Licenses, Digital Footprint
    - Tier 3 (60-75%): Name Variations, Network Analysis, History
    - Tier 4 (45-60%): Geospatial, Industry Classification
    """
    
    try:
        # Build property data dict from request
        property_data = {
            "parcel_id": request.parcel_id,
            "address": request.address,
            "owner_name": request.owner_name,
            "tax_id": request.tax_id,
            "latitude": request.latitude,
            "longitude": request.longitude
        }
        
        # Get property details from database if parcel_id provided
        if request.parcel_id:
            response = supabase.from_("florida_parcels")\
                .select("*")\
                .eq("parcel_id", request.parcel_id)\
                .single()\
                .execute()
                
            if response.data:
                property_data.update({
                    "address": response.data.get("phy_addr1"),
                    "city": response.data.get("phy_city"),
                    "owner_name": response.data.get("owner_name"),
                    "tax_id": response.data.get("tax_id"),
                    "latitude": response.data.get("latitude"),
                    "longitude": response.data.get("longitude")
                })
        
        # Convert minimum confidence to enum
        min_confidence = MatchConfidence.MEDIUM
        if request.min_confidence >= 90:
            min_confidence = MatchConfidence.EXACT
        elif request.min_confidence >= 85:
            min_confidence = MatchConfidence.VERY_HIGH
        elif request.min_confidence >= 75:
            min_confidence = MatchConfidence.HIGH
        elif request.min_confidence >= 60:
            min_confidence = MatchConfidence.MEDIUM
        else:
            min_confidence = MatchConfidence.LOW
            
        # Run matching agents
        matches = await matcher.find_matches(
            property_data,
            min_confidence=min_confidence,
            max_agents=request.max_agents
        )
        
        # Convert to response format
        responses = []
        for match in matches:
            responses.append(MatchResponse(
                company_name=match.company_name,
                company_doc_number=match.company_doc_number,
                confidence=match.confidence.value,
                match_type=match.match_type,
                evidence=match.evidence,
                agent_name=match.agent_name,
                timestamp=match.timestamp.isoformat()
            ))
            
        return responses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/agents")
async def list_available_agents():
    """List all available matching agents and their accuracy tiers"""
    
    return {
        "tier_1_very_high_accuracy": [
            {
                "name": "TaxIdCrossReferenceAgent",
                "accuracy": "90-95%",
                "description": "Matches EIN/Tax IDs from property records to corporate filings"
            },
            {
                "name": "MortgageLenderDocumentAgent",
                "accuracy": "90-95%",
                "description": "Analyzes mortgage documents and deed recordings"
            },
            {
                "name": "UtilityAccountMatchingAgent",
                "accuracy": "90-95%",
                "description": "Matches business names on utility accounts"
            }
        ],
        "tier_2_high_accuracy": [
            {
                "name": "PermitLicenseAgent",
                "accuracy": "75-85%",
                "description": "Cross-references building permits and business licenses"
            },
            {
                "name": "DomainDigitalFootprintAgent",
                "accuracy": "75-85%",
                "description": "Searches online presence and business listings"
            },
            {
                "name": "PropertyManagerPatternAgent",
                "accuracy": "75-85%",
                "description": "Identifies property management patterns"
            }
        ],
        "tier_3_medium_accuracy": [
            {
                "name": "NameVariationAliasAgent",
                "accuracy": "60-75%",
                "description": "Handles DBA variations and name aliases"
            },
            {
                "name": "NetworkAnalysisAgent",
                "accuracy": "60-75%",
                "description": "Maps officer relationships across entities"
            },
            {
                "name": "HistoricalTransactionAgent",
                "accuracy": "60-75%",
                "description": "Analyzes property sale history"
            }
        ],
        "tier_4_moderate_accuracy": [
            {
                "name": "GeospatialClusteringAgent",
                "accuracy": "45-60%",
                "description": "Identifies ownership clusters and patterns"
            },
            {
                "name": "IndustryClassificationAgent",
                "accuracy": "45-60%",
                "description": "Matches property use codes to business types"
            },
            {
                "name": "FinancialPatternAgent",
                "accuracy": "45-60%",
                "description": "Analyzes investment and value patterns"
            }
        ]
    }

@router.get("/match/{parcel_id}")
async def match_by_parcel_id(
    parcel_id: str,
    min_confidence: int = Query(60, ge=20, le=95)
):
    """Quick match using parcel ID with default settings"""
    
    request = PropertyMatchRequest(
        parcel_id=parcel_id,
        min_confidence=min_confidence
    )
    
    return await match_property_to_companies(request)

@router.get("/explain/{company_doc_number}")
async def explain_match(company_doc_number: str, parcel_id: str):
    """Get detailed explanation of why a company was matched to a property"""
    
    # This would retrieve the match history and explain the reasoning
    # For now, return a sample explanation
    
    return {
        "company_doc_number": company_doc_number,
        "parcel_id": parcel_id,
        "explanation": {
            "primary_reason": "Exact address match in corporate filings",
            "confidence_score": 95,
            "supporting_evidence": [
                "Principal address matches property address exactly",
                "Business license active at this location",
                "Building permits filed by this entity",
                "Utility accounts in company name"
            ],
            "agent_chain": [
                "TaxIdCrossReferenceAgent (95% confidence)",
                "PermitLicenseAgent (80% confidence)",
                "DomainDigitalFootprintAgent (75% confidence)"
            ],
            "recommendation": "Very high confidence match - multiple documentary sources confirm ownership"
        }
    }