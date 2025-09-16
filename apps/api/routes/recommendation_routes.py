"""
FastAPI routes for graph-based property recommendations
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import asyncio

from ..graph.recommendation_engine import (
    GraphRecommendationEngine,
    PropertyRecommendation,
    RecommendationRequest,
    RecommendationType
)
from ..graph.property_graph_service import PropertyGraphService
from ..graph.enhanced_rag_service import EnhancedRAGService
from ..core.dependencies import get_current_user

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

# Pydantic models for API
class RecommendationTypeEnum(str, Enum):
    INVESTMENT = "investment"
    SIMILAR_PROPERTIES = "similar_properties"
    MARKET_OPPORTUNITIES = "market_opportunities"
    RISK_ANALYSIS = "risk_analysis"
    PORTFOLIO_EXPANSION = "portfolio_expansion"
    FLIP_OPPORTUNITIES = "flip_opportunities"

class RecommendationRequestModel(BaseModel):
    recommendation_types: List[RecommendationTypeEnum]
    filters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    max_results: int = Field(default=10, ge=1, le=50)
    include_reasoning: bool = True
    confidence_threshold: float = Field(default=0.6, ge=0.1, le=1.0)
    location_preferences: List[str] = Field(default_factory=list)
    budget_range: Optional[tuple[float, float]] = None
    investment_strategy: str = Field(default="balanced")  # conservative, balanced, aggressive

class PropertyRecommendationModel(BaseModel):
    parcel_id: str
    recommendation_type: str
    title: str
    description: str
    confidence_score: float
    potential_roi: Optional[float] = None
    risk_level: str
    reasoning: List[str]
    supporting_data: Dict[str, Any]
    urgency: str
    estimated_value: Optional[float] = None
    comparable_properties: List[str]
    action_items: List[str]

class RecommendationFeedbackModel(BaseModel):
    parcel_id: str
    feedback: str
    rating: int = Field(ge=1, le=5)
    additional_comments: Optional[str] = None

class RecommendationSummaryModel(BaseModel):
    total_recommendations: int
    by_type: Dict[str, int]
    by_risk_level: Dict[str, int]
    by_urgency: Dict[str, int]
    avg_confidence: float
    top_opportunity: Optional[PropertyRecommendationModel] = None

# Dependency injection
async def get_recommendation_engine() -> GraphRecommendationEngine:
    graph_service = PropertyGraphService()
    rag_service = EnhancedRAGService(graph_service)
    return GraphRecommendationEngine(graph_service, rag_service)

@router.post("/generate", response_model=List[PropertyRecommendationModel])
async def generate_recommendations(
    request: RecommendationRequestModel,
    current_user: dict = Depends(get_current_user),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """
    Generate personalized property recommendations based on user preferences and graph analysis
    """
    try:
        # Convert Pydantic model to internal request format
        rec_request = RecommendationRequest(
            user_id=current_user.get('user_id'),
            recommendation_types=[RecommendationType(rt.value) for rt in request.recommendation_types],
            filters=request.filters,
            max_results=request.max_results,
            include_reasoning=request.include_reasoning,
            confidence_threshold=request.confidence_threshold,
            location_preferences=request.location_preferences,
            budget_range=request.budget_range,
            investment_strategy=request.investment_strategy
        )
        
        recommendations = await engine.generate_recommendations(rec_request)
        
        # Convert to response models
        response = []
        for rec in recommendations:
            response.append(PropertyRecommendationModel(
                parcel_id=rec.parcel_id,
                recommendation_type=rec.recommendation_type.value,
                title=rec.title,
                description=rec.description,
                confidence_score=rec.confidence_score,
                potential_roi=rec.potential_roi,
                risk_level=rec.risk_level,
                reasoning=rec.reasoning,
                supporting_data=rec.supporting_data,
                urgency=rec.urgency,
                estimated_value=rec.estimated_value,
                comparable_properties=rec.comparable_properties,
                action_items=rec.action_items
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@router.get("/types", response_model=Dict[str, str])
async def get_recommendation_types():
    """Get available recommendation types with descriptions"""
    return {
        "investment": "Properties with strong investment potential based on historical performance",
        "similar_properties": "Properties similar to your existing portfolio or preferences",
        "market_opportunities": "Properties in emerging markets with growth potential",
        "risk_analysis": "Properties with potential risk factors requiring attention",
        "portfolio_expansion": "Properties to diversify your investment portfolio",
        "flip_opportunities": "Properties suitable for fix-and-flip investment strategy"
    }

@router.get("/summary", response_model=RecommendationSummaryModel)
async def get_recommendations_summary(
    recommendation_types: List[RecommendationTypeEnum] = Query(default=None),
    confidence_threshold: float = Query(default=0.6, ge=0.1, le=1.0),
    current_user: dict = Depends(get_current_user),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Get a summary of available recommendations for the user"""
    
    try:
        # Use all types if none specified
        if not recommendation_types:
            recommendation_types = list(RecommendationTypeEnum)
        
        rec_request = RecommendationRequest(
            user_id=current_user.get('user_id'),
            recommendation_types=[RecommendationType(rt.value) for rt in recommendation_types],
            max_results=50,  # Get more for summary
            confidence_threshold=confidence_threshold
        )
        
        recommendations = await engine.generate_recommendations(rec_request)
        
        # Calculate summary statistics
        by_type = {}
        by_risk_level = {}
        by_urgency = {}
        
        for rec in recommendations:
            # By type
            rec_type = rec.recommendation_type.value
            by_type[rec_type] = by_type.get(rec_type, 0) + 1
            
            # By risk level
            risk = rec.risk_level
            by_risk_level[risk] = by_risk_level.get(risk, 0) + 1
            
            # By urgency
            urgency = rec.urgency
            by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
        
        avg_confidence = sum(rec.confidence_score for rec in recommendations) / len(recommendations) if recommendations else 0
        
        # Find top opportunity (highest confidence + ROI)
        top_opportunity = None
        if recommendations:
            top_rec = max(recommendations, key=lambda x: (x.confidence_score, x.potential_roi or 0))
            top_opportunity = PropertyRecommendationModel(
                parcel_id=top_rec.parcel_id,
                recommendation_type=top_rec.recommendation_type.value,
                title=top_rec.title,
                description=top_rec.description,
                confidence_score=top_rec.confidence_score,
                potential_roi=top_rec.potential_roi,
                risk_level=top_rec.risk_level,
                reasoning=top_rec.reasoning,
                supporting_data=top_rec.supporting_data,
                urgency=top_rec.urgency,
                estimated_value=top_rec.estimated_value,
                comparable_properties=top_rec.comparable_properties,
                action_items=top_rec.action_items
            )
        
        return RecommendationSummaryModel(
            total_recommendations=len(recommendations),
            by_type=by_type,
            by_risk_level=by_risk_level,
            by_urgency=by_urgency,
            avg_confidence=round(avg_confidence, 3),
            top_opportunity=top_opportunity
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.get("/property/{parcel_id}/explanation")
async def get_recommendation_explanation(
    parcel_id: str,
    recommendation_type: RecommendationTypeEnum,
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Get detailed explanation for why a specific property was recommended"""
    
    try:
        explanation = await engine.get_recommendation_explanation(
            parcel_id=parcel_id,
            recommendation_type=RecommendationType(recommendation_type.value)
        )
        
        return explanation
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting explanation: {str(e)}")

@router.post("/feedback")
async def submit_recommendation_feedback(
    feedback: RecommendationFeedbackModel,
    current_user: dict = Depends(get_current_user),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Submit feedback on a recommendation to improve future suggestions"""
    
    try:
        success = await engine.update_recommendation_feedback(
            user_id=current_user.get('user_id'),
            parcel_id=feedback.parcel_id,
            feedback=feedback.feedback,
            rating=feedback.rating
        )
        
        return {
            "success": success,
            "message": "Feedback received and will be used to improve recommendations"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@router.get("/trending", response_model=List[PropertyRecommendationModel])
async def get_trending_recommendations(
    limit: int = Query(default=10, ge=1, le=20),
    time_period: str = Query(default="week", regex="^(day|week|month)$"),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Get trending property recommendations based on recent market activity"""
    
    try:
        # Focus on market opportunities for trending
        rec_request = RecommendationRequest(
            user_id="system",  # System-wide trending
            recommendation_types=[RecommendationType.MARKET_OPPORTUNITIES],
            max_results=limit,
            confidence_threshold=0.7  # Higher threshold for trending
        )
        
        recommendations = await engine.generate_recommendations(rec_request)
        
        # Convert to response models
        response = []
        for rec in recommendations:
            response.append(PropertyRecommendationModel(
                parcel_id=rec.parcel_id,
                recommendation_type=rec.recommendation_type.value,
                title=rec.title,
                description=rec.description,
                confidence_score=rec.confidence_score,
                potential_roi=rec.potential_roi,
                risk_level=rec.risk_level,
                reasoning=rec.reasoning,
                supporting_data=rec.supporting_data,
                urgency=rec.urgency,
                estimated_value=rec.estimated_value,
                comparable_properties=rec.comparable_properties,
                action_items=rec.action_items
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trending recommendations: {str(e)}")

@router.get("/similar/{parcel_id}", response_model=List[PropertyRecommendationModel])
async def get_similar_properties(
    parcel_id: str,
    limit: int = Query(default=5, ge=1, le=20),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Get properties similar to a specific property"""
    
    try:
        # Create a request focused on the specific property
        rec_request = RecommendationRequest(
            user_id="anonymous",  # Don't need user context for this
            recommendation_types=[RecommendationType.SIMILAR_PROPERTIES],
            max_results=limit,
            filters={"reference_parcel_id": parcel_id}
        )
        
        recommendations = await engine.generate_recommendations(rec_request)
        
        # Convert to response models
        response = []
        for rec in recommendations:
            response.append(PropertyRecommendationModel(
                parcel_id=rec.parcel_id,
                recommendation_type=rec.recommendation_type.value,
                title=rec.title,
                description=rec.description,
                confidence_score=rec.confidence_score,
                potential_roi=rec.potential_roi,
                risk_level=rec.risk_level,
                reasoning=rec.reasoning,
                supporting_data=rec.supporting_data,
                urgency=rec.urgency,
                estimated_value=rec.estimated_value,
                comparable_properties=rec.comparable_properties,
                action_items=rec.action_items
            ))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar properties: {str(e)}")

@router.post("/batch-analyze")
async def batch_analyze_properties(
    parcel_ids: List[str] = Body(..., min_items=1, max_items=20),
    analysis_type: RecommendationTypeEnum = Body(default=RecommendationTypeEnum.INVESTMENT),
    current_user: dict = Depends(get_current_user),
    engine: GraphRecommendationEngine = Depends(get_recommendation_engine)
):
    """Analyze multiple properties in batch for efficiency"""
    
    try:
        results = {}
        
        # Process properties in parallel for better performance
        tasks = []
        for parcel_id in parcel_ids:
            task = engine.get_recommendation_explanation(
                parcel_id=parcel_id,
                recommendation_type=RecommendationType(analysis_type.value)
            )
            tasks.append((parcel_id, task))
        
        # Execute all tasks concurrently
        for parcel_id, task in tasks:
            try:
                result = await task
                results[parcel_id] = result
            except Exception as e:
                results[parcel_id] = {"error": str(e)}
        
        return {
            "analysis_type": analysis_type.value,
            "results": results,
            "processed_count": len(results),
            "success_count": len([r for r in results.values() if "error" not in r])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in batch analysis: {str(e)}")