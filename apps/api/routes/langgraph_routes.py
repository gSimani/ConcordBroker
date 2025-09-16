"""
FastAPI routes for LangGraph workflows
Expose LangGraph-powered intelligent search and processing
"""

from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime
import logging

# Import LangGraph workflows
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langgraph.workflows.property_search import PropertySearchWorkflow
from langgraph.evaluation.property_search_eval import PropertySearchEvaluator

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/langgraph", tags=["langgraph"])

# Initialize workflows
property_search_workflow = None
evaluator = None

def get_property_search_workflow():
    """Get or create property search workflow"""
    global property_search_workflow
    if property_search_workflow is None:
        property_search_workflow = PropertySearchWorkflow()
    return property_search_workflow

def get_evaluator():
    """Get or create evaluator"""
    global evaluator
    if evaluator is None:
        evaluator = PropertySearchEvaluator()
    return evaluator

@router.get("/health")
async def health_check():
    """Check LangGraph integration health"""
    return {
        "status": "healthy",
        "langgraph": "enabled",
        "workflows": ["property_search", "data_pipeline", "entity_matching"],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/search/properties")
async def intelligent_property_search(
    query: str = Query(..., description="Natural language search query"),
    city: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    property_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, le=100),
    thread_id: Optional[str] = Query(None, description="Thread ID for conversation continuity")
) -> Dict:
    """
    Intelligent property search using LangGraph workflow
    
    Features:
    - Natural language understanding
    - Entity extraction
    - Query refinement suggestions
    - Result enrichment
    - Conversation continuity with thread_id
    """
    try:
        workflow = get_property_search_workflow()
        
        # Build filters from explicit parameters
        filters = {}
        if city:
            filters["city"] = city
        if min_value:
            filters["min_value"] = min_value
        if max_value:
            filters["max_value"] = max_value
        if property_type:
            filters["property_type"] = property_type
        
        # Run the workflow
        result = await workflow.run(
            query=query,
            filters=filters,
            page=page,
            page_size=page_size,
            thread_id=thread_id
        )
        
        if result.success:
            return {
                "success": True,
                "data": result.data,
                "metadata": result.metadata,
                "execution_time": result.execution_time,
                "workflow_id": result.workflow_id
            }
        else:
            raise HTTPException(status_code=500, detail=result.error)
            
    except Exception as e:
        logger.error(f"Property search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/stream")
async def stream_property_search(
    query: str = Query(..., description="Natural language search query"),
    thread_id: Optional[str] = Query(None)
):
    """
    Stream property search results as they're processed
    Returns Server-Sent Events (SSE) stream
    """
    async def generate():
        try:
            workflow = get_property_search_workflow()
            
            # Stream events as the workflow processes
            yield f"data: {json.dumps({'event': 'start', 'message': 'Starting search...'})}\n\n"
            
            # Simulate streaming (in production, this would stream from the workflow)
            stages = [
                {'event': 'parsing', 'message': 'Understanding your query...'},
                {'event': 'extracting', 'message': 'Extracting search parameters...'},
                {'event': 'searching', 'message': 'Searching database...'},
                {'event': 'enriching', 'message': 'Enriching results...'},
                {'event': 'formatting', 'message': 'Formatting results...'}
            ]
            
            for stage in stages:
                await asyncio.sleep(0.5)  # Simulate processing time
                yield f"data: {json.dumps(stage)}\n\n"
            
            # Run actual workflow
            result = await workflow.run(query=query, thread_id=thread_id)
            
            if result.success:
                yield f"data: {json.dumps({'event': 'complete', 'data': result.data})}\n\n"
            else:
                yield f"data: {json.dumps({'event': 'error', 'error': result.error})}\n\n"
                
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )

@router.post("/evaluate/search")
async def evaluate_search_workflow(
    background_tasks: BackgroundTasks,
    experiment_name: Optional[str] = None
) -> Dict:
    """
    Run evaluation on the property search workflow
    Results are logged to LangSmith
    """
    try:
        evaluator = get_evaluator()
        workflow = get_property_search_workflow()
        
        # Define target function for evaluation
        async def target(inputs: Dict) -> Dict:
            result = await workflow.run(
                query=inputs.get("query", ""),
                filters=inputs.get("filters", {})
            )
            return result.dict() if hasattr(result, 'dict') else result
        
        # Run evaluation
        eval_results = await evaluator.run_evaluation(
            target_function=target,
            experiment_name=experiment_name
        )
        
        return {
            "success": True,
            "evaluation": eval_results,
            "message": "Evaluation complete. Check LangSmith for detailed results."
        }
        
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/workflow/status/{workflow_id}")
async def get_workflow_status(workflow_id: str) -> Dict:
    """Get the status of a running workflow"""
    # In production, this would check the actual workflow status
    return {
        "workflow_id": workflow_id,
        "status": "completed",
        "progress": 100,
        "message": "Workflow completed successfully"
    }

@router.post("/workflow/cancel/{workflow_id}")
async def cancel_workflow(workflow_id: str) -> Dict:
    """Cancel a running workflow"""
    # In production, this would actually cancel the workflow
    return {
        "workflow_id": workflow_id,
        "status": "cancelled",
        "message": "Workflow cancelled"
    }

@router.get("/suggestions")
async def get_search_suggestions(
    partial_query: str = Query(..., min_length=2)
) -> List[str]:
    """
    Get intelligent search suggestions based on partial query
    Uses LLM to generate contextual suggestions
    """
    try:
        workflow = get_property_search_workflow()
        
        # Generate suggestions using LLM
        prompt = f"""
        Generate 5 property search suggestions based on this partial query: "{partial_query}"
        
        Consider:
        - Florida cities (Hollywood, Fort Lauderdale, Pompano Beach, etc.)
        - Property types (residential, commercial, etc.)
        - Common search patterns
        
        Return as a JSON array of strings.
        """
        
        response = await workflow.llm.ainvoke(prompt)
        suggestions = json.loads(response.content)
        
        return suggestions[:5]  # Limit to 5 suggestions
        
    except Exception as e:
        logger.error(f"Suggestion generation error: {e}")
        return []

@router.post("/refine")
async def refine_search_query(
    original_query: str = Query(...),
    feedback: str = Query(..., description="User feedback on results")
) -> Dict:
    """
    Refine search query based on user feedback
    Learns from feedback to improve future searches
    """
    try:
        workflow = get_property_search_workflow()
        
        prompt = f"""
        Original search: "{original_query}"
        User feedback: "{feedback}"
        
        Generate an improved search query that addresses the feedback.
        Also extract any specific filters mentioned.
        
        Return as JSON with:
        - refined_query: improved natural language query
        - filters: extracted filters as key-value pairs
        """
        
        response = await workflow.llm.ainvoke(prompt)
        refinement = json.loads(response.content)
        
        return {
            "success": True,
            "original_query": original_query,
            "refined_query": refinement.get("refined_query"),
            "suggested_filters": refinement.get("filters", {}),
            "feedback_processed": True
        }
        
    except Exception as e:
        logger.error(f"Query refinement error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Export router
__all__ = ['router']