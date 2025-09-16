"""
Autonomous Agent System API Routes
Provides endpoints to interact with the autonomous AI system
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime

from agents.orchestrator import orchestrator, WorkflowType
from agents.orchestrator import process_property, analyze_document, generate_marketing_content

router = APIRouter(prefix="/api/autonomous", tags=["Autonomous System"])

# Request/Response models
class PropertyRequest(BaseModel):
    property_data: Dict[str, Any]
    include_marketing: bool = True
    include_valuation: bool = False

class DocumentAnalysisRequest(BaseModel):
    document_type: str = "general"
    text: Optional[str] = None
    extract_entities: bool = True

class WorkflowRequest(BaseModel):
    workflow_type: str
    input_data: Dict[str, Any]
    priority: str = "medium"

class TaskRequest(BaseModel):
    task_type: str
    input_data: Dict[str, Any]
    priority: str = "medium"

@router.get("/status")
async def get_system_status():
    """Get autonomous system status"""
    
    try:
        status = orchestrator.get_status()
        
        # Calculate uptime safely
        uptime_hours = 0.0
        try:
            start_time = status["metrics"]["start_time"]
            if isinstance(start_time, str):
                start_time = datetime.fromisoformat(start_time)
            uptime_hours = (datetime.now() - start_time).total_seconds() / 3600
        except (KeyError, TypeError, ValueError):
            uptime_hours = 0.0
        
        # Add additional system info
        system_info = {
            "system_status": "operational" if status["is_running"] else "stopped",
            "total_agents": len(status["agents"]),
            "active_workflows": len(status.get("workflows", {})),
            "queue_size": status.get("queue_size", 0),
            "uptime_hours": uptime_hours,
            "agents": []
        }
        
        # Get detailed agent status
        for agent_id in status.get("agents", []):
            try:
                agent = orchestrator.get_agent(agent_id)
                if agent:
                    agent_status = agent.get_status()
                    system_info["agents"].append({
                        "id": agent_id,
                        "name": agent_status.get("name", agent_id),
                        "status": agent_status.get("status", "unknown"),
                        "tasks_processed": agent_status.get("metrics", {}).get("tasks_processed", 0),
                        "success_rate": f"{agent_status.get('metrics', {}).get('success_rate', 0):.1%}",
                        "queue_size": agent_status.get("queue_size", 0)
                    })
            except Exception as e:
                print(f"Error getting agent {agent_id} status: {e}")
                continue
        
        return {
            **status,
            "system_info": system_info
        }
        
    except Exception as e:
        # Return basic status if orchestrator is not yet initialized
        return {
            "is_running": False,
            "agents": [],
            "workflows": {},
            "queue_size": 0,
            "metrics": {
                "start_time": datetime.now().isoformat(),
                "total_tasks_processed": 0,
                "successful_workflows": 0,
                "failed_workflows": 0,
                "average_workflow_time": 0.0
            },
            "system_info": {
                "system_status": "initializing",
                "total_agents": 0,
                "active_workflows": 0,
                "queue_size": 0,
                "uptime_hours": 0.0,
                "agents": []
            },
            "initialization_error": str(e)
        }

@router.post("/process-property")
async def process_property_autonomous(request: PropertyRequest):
    """
    Process a property through the autonomous system
    This will automatically generate listings, index for search, and create marketing materials
    """
    
    try:
        # Add the property to autonomous processing
        result = await process_property(request.property_data)
        
        # If marketing content is requested, generate it
        if request.include_marketing and result.get("status") == "completed":
            marketing_result = await generate_marketing_content(request.property_data)
            result["marketing_content"] = marketing_result
        
        return {
            "status": "success",
            "property_id": request.property_data.get("id", "unknown"),
            "workflow_result": result,
            "processing_complete": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.post("/analyze-document")
async def analyze_document_autonomous(request: DocumentAnalysisRequest):
    """
    Analyze a document using the autonomous system
    Extracts entities, processes content, and generates summaries
    """
    
    try:
        # Prepare input for document analysis
        input_data = {
            "input_document": request.text,
            "document_type": request.document_type,
            "extract_entities": request.extract_entities
        }
        
        result = await analyze_document(input_data)
        
        return {
            "status": "success",
            "document_type": request.document_type,
            "analysis_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document analysis failed: {str(e)}")

@router.post("/upload-document")
async def upload_document_for_analysis(
    file: UploadFile = File(...),
    document_type: str = "general"
):
    """
    Upload and analyze a document file
    """
    
    try:
        # Read file content
        content = await file.read()
        
        # For now, convert to text (in production would use OCR for images/PDFs)
        if file.content_type.startswith("text/"):
            text_content = content.decode("utf-8")
        else:
            # Simulate OCR for non-text files
            text_content = f"Document content extracted from {file.filename}"
        
        # Analyze the document
        input_data = {
            "input_document": text_content,
            "document_type": document_type
        }
        
        result = await analyze_document(input_data)
        
        return {
            "status": "success",
            "filename": file.filename,
            "file_type": file.content_type,
            "document_type": document_type,
            "analysis_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@router.post("/execute-workflow")
async def execute_workflow(request: WorkflowRequest):
    """
    Execute a specific workflow in the autonomous system
    """
    
    try:
        # Convert string workflow type to enum
        workflow_type = WorkflowType(request.workflow_type)
        
        result = await orchestrator.execute_workflow(workflow_type, request.input_data)
        
        return {
            "status": "success",
            "workflow_type": request.workflow_type,
            "workflow_result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid workflow type: {request.workflow_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/add-task")
async def add_task_to_queue(request: TaskRequest):
    """
    Add a task to the autonomous system queue
    """
    
    try:
        task = {
            "type": request.task_type,
            "input_data": request.input_data,
            "priority": request.priority
        }
        
        await orchestrator.add_task(task)
        
        return {
            "status": "success",
            "message": "Task added to queue",
            "task_type": request.task_type,
            "priority": request.priority,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add task: {str(e)}")

@router.get("/workflows")
async def list_available_workflows():
    """
    List all available autonomous workflows
    """
    
    return {
        "workflows": [
            {
                "type": workflow_type.value,
                "name": workflow_data["name"],
                "description": workflow_data["description"],
                "steps": len(workflow_data["steps"])
            }
            for workflow_type, workflow_data in orchestrator.workflows.items()
        ]
    }

@router.get("/agents")
async def list_agents():
    """
    List all available agents and their capabilities
    """
    
    agents_info = []
    
    for agent_id, agent in orchestrator.agents.items():
        status = agent.get_status()
        agents_info.append({
            "id": agent_id,
            "name": status["name"],
            "description": status["description"],
            "status": status["status"],
            "capabilities": agent.__class__.__doc__ or "AI processing agent",
            "metrics": status["metrics"]
        })
    
    return {
        "agents": agents_info,
        "total_agents": len(agents_info)
    }

@router.post("/batch-process")
async def batch_process_properties(properties: List[Dict[str, Any]]):
    """
    Process multiple properties in batch through autonomous system
    """
    
    try:
        # Add batch processing task
        task = {
            "workflow_type": WorkflowType.PROPERTY_ONBOARDING,
            "input_data": {
                "properties": properties,
                "batch_mode": True
            },
            "priority": "high"
        }
        
        await orchestrator.add_task(task)
        
        return {
            "status": "success",
            "message": f"Batch processing started for {len(properties)} properties",
            "total_properties": len(properties),
            "estimated_completion": "15-30 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.post("/generate-listing")
async def generate_property_listing(
    property_data: Dict[str, Any],
    style: str = "professional",
    include_seo: bool = True
):
    """
    Generate property listing using autonomous content generation
    """
    
    try:
        # Add content generation task
        task = {
            "type": "generate_listing",
            "input_data": {
                "property_data": property_data,
                "style": style,
                "include_seo": include_seo
            },
            "priority": "medium"
        }
        
        await orchestrator.add_task(task)
        
        return {
            "status": "success",
            "message": "Listing generation started",
            "property_address": property_data.get("address", "Unknown"),
            "style": style,
            "estimated_completion": "2-5 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Listing generation failed: {str(e)}")

@router.post("/market-intelligence")
async def generate_market_intelligence(
    location: str,
    property_type: str = "residential",
    include_predictions: bool = True
):
    """
    Generate market intelligence report autonomously
    """
    
    try:
        # Add market intelligence task
        task = {
            "workflow_type": WorkflowType.MARKET_INTELLIGENCE,
            "input_data": {
                "location": location,
                "property_type": property_type,
                "include_predictions": include_predictions
            },
            "priority": "medium"
        }
        
        await orchestrator.add_task(task)
        
        return {
            "status": "success",
            "message": "Market intelligence generation started",
            "location": location,
            "property_type": property_type,
            "estimated_completion": "5-10 minutes",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market intelligence failed: {str(e)}")

@router.get("/system-metrics")
async def get_system_metrics():
    """
    Get detailed system performance metrics
    """
    
    status = orchestrator.get_status()
    metrics = status["metrics"]
    
    # Calculate additional metrics
    start_time = (datetime.fromisoformat(metrics["start_time"])
                 if isinstance(metrics["start_time"], str)
                 else metrics["start_time"])
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    
    return {
        "system_metrics": {
            "uptime_hours": uptime_seconds / 3600,
            "total_tasks_processed": metrics["total_tasks_processed"],
            "successful_workflows": metrics["successful_workflows"],
            "failed_workflows": metrics["failed_workflows"],
            "success_rate": (metrics["successful_workflows"] / 
                           max(metrics["successful_workflows"] + metrics["failed_workflows"], 1)),
            "average_workflow_time": metrics["average_workflow_time"],
            "tasks_per_hour": metrics["total_tasks_processed"] / max(uptime_seconds / 3600, 1)
        },
        "agent_metrics": [
            {
                "agent_id": agent_id,
                "metrics": agent.get_status()["metrics"]
            }
            for agent_id, agent in orchestrator.agents.items()
        ],
        "queue_status": {
            "current_queue_size": status["queue_size"],
            "is_processing": status["is_running"]
        }
    }

@router.post("/start-system")
async def start_autonomous_system(background_tasks: BackgroundTasks):
    """
    Start the autonomous system (if not already running)
    """
    
    if orchestrator.is_running:
        return {
            "status": "already_running",
            "message": "Autonomous system is already operational"
        }
    
    # Start system in background
    background_tasks.add_task(orchestrator.start)
    
    return {
        "status": "starting",
        "message": "Autonomous system is starting up",
        "estimated_startup_time": "30 seconds",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/emergency-stop")
async def emergency_stop_system():
    """
    Emergency stop of the autonomous system
    """
    
    try:
        await orchestrator.stop()
        
        return {
            "status": "stopped",
            "message": "Autonomous system has been stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop system: {str(e)}")

# Startup event to initialize the autonomous system
@router.on_event("startup")
async def startup_event():
    """Initialize autonomous system on startup"""
    
    # Start the orchestrator in background
    asyncio.create_task(orchestrator.start())

# Export router
__all__ = ["router"]