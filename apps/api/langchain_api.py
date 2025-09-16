"""
LangChain API Server for ConcordBroker
Provides REST API endpoints for all LangChain agents and features
"""

import os
import sys
import asyncio
import logging
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

# LangSmith and tracing should be provided via environment.
os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
os.environ.setdefault("LANGCHAIN_PROJECT", os.getenv("LANGCHAIN_PROJECT", "concordbroker-property-analysis"))

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import LangChain system
from langchain_system.core import LangChainCore
from langchain_system.util_guardrails import redact_pii, parse_confidence
from langchain_system.agents import (
    PropertyAnalysisAgent,
    InvestmentAdvisorAgent,
    DataResearchAgent,
    MarketAnalysisAgent,
    LegalComplianceAgent
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ConcordBroker LangChain API",
    description="AI-powered property analysis and investment advisory API",
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

# Initialize LangChain Core
langchain_core = None

# Request/Response Models
class PropertyAnalysisRequest(BaseModel):
    parcel_id: str
    analysis_type: str = "comprehensive"
    include_recommendations: bool = True
    include_comparables: bool = True

class InvestmentAdviceRequest(BaseModel):
    property_data: Dict[str, Any]
    investor_profile: Dict[str, Any]
    market_conditions: Optional[Dict[str, Any]] = None

class ResearchRequest(BaseModel):
    query: str
    research_type: str = "general"
    include_sources: bool = True

class MarketAnalysisRequest(BaseModel):
    location: str
    timeframe: str = "current"
    include_projections: bool = True

class ComplianceCheckRequest(BaseModel):
    property_data: Dict[str, Any]
    check_type: str = "general"
    include_recommendations: bool = True

class ChatRequest(BaseModel):
    session_id: str
    message: str
    agent_type: str = "property_analysis"
    history: Optional[List[Dict[str, str]]] = []
    context: Optional[Dict[str, Any]] = {}
    explain: bool = False

class RAGPipelineRequest(BaseModel):
    document_path: str
    pipeline_name: str
    chunk_size: int = 1000
    chunk_overlap: int = 200

class KnowledgeQueryRequest(BaseModel):
    query: str
    knowledge_base: str = "properties"
    k: int = 5

class AgentInitRequest(BaseModel):
    agent_type: str

@app.on_event("startup")
async def startup_event():
    """Initialize LangChain Core on startup"""
    global langchain_core
    try:
        langchain_core = LangChainCore()
        logger.info("LangChain Core initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize LangChain Core: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global langchain_core
    if langchain_core:
        langchain_core.shutdown()
        logger.info("LangChain Core shutdown complete")

# Health Check Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "langchain_initialized": langchain_core is not None
    }

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    return langchain_core.get_agent_metrics()

# Agent Initialization Endpoints
@app.post("/agents/initialize")
async def initialize_agent(request: AgentInitRequest):
    """Initialize a specific agent"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        # Agent is already initialized in LangChain Core
        if request.agent_type in langchain_core.agents:
            return {
                "status": "initialized",
                "agent_id": request.agent_type,
                "message": f"Agent {request.agent_type} is ready"
            }
        else:
            raise ValueError(f"Unknown agent type: {request.agent_type}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Property Analysis Endpoints
@app.post("/analyze/property")
async def analyze_property(request: PropertyAnalysisRequest):
    """Analyze a property using LangChain agents"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        result = await langchain_core.analyze_property(
            request.parcel_id,
            request.analysis_type
        )
        return result
    except Exception as e:
        logger.error(f"Property analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Investment Advisory Endpoints
@app.post("/advice/investment")
async def get_investment_advice(request: InvestmentAdviceRequest):
    """Get investment advice for a property"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        agent = langchain_core.agents.get("investment_advisor")
        if not agent:
            raise ValueError("Investment advisor agent not initialized")
        
        portfolio_context = {
            **request.investor_profile,
            "property_data": request.property_data,
            "market_conditions": request.market_conditions or {}
        }
        
        result = await agent.advise(
            f"Analyze this property for investment: {request.property_data.get('address', 'Unknown')}",
            portfolio_context
        )
        
        return result
    except Exception as e:
        logger.error(f"Investment advice error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Research Endpoints
@app.post("/research/property")
async def research_property(request: ResearchRequest):
    """Research property data"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        agent = langchain_core.agents.get("data_research")
        if not agent:
            raise ValueError("Data research agent not initialized")
        
        result = await agent.research(
            request.query,
            request.research_type
        )
        
        return result
    except Exception as e:
        logger.error(f"Research error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Market Analysis Endpoints
@app.post("/analyze/market")
async def analyze_market(request: MarketAnalysisRequest):
    """Analyze market conditions"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        agent = langchain_core.agents.get("market_analysis")
        if not agent:
            raise ValueError("Market analysis agent not initialized")
        
        result = await agent.analyze_market(
            request.location,
            request.timeframe
        )
        
        return result
    except Exception as e:
        logger.error(f"Market analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Compliance Check Endpoints
@app.post("/compliance/check")
async def check_compliance(request: ComplianceCheckRequest):
    """Check legal compliance for a property"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        agent = langchain_core.agents.get("legal_compliance")
        if not agent:
            raise ValueError("Legal compliance agent not initialized")
        
        result = await agent.check_compliance(
            request.property_data,
            request.check_type
        )
        
        return result
    except Exception as e:
        logger.error(f"Compliance check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat Endpoints
@app.post("/chat")
async def chat(request: ChatRequest):
    """Chat with a LangChain agent"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        # Offline mode: return canned response to avoid external calls
        if os.getenv("OFFLINE_MODE", "false").lower() == "true":
            reply = "Acknowledged. Local offline response (no external LLM)."
            return {
                "response": reply,
                "metadata": {
                    "agent": request.agent_type,
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 0.95,
                    "escalated": False,
                    "rationale": "- Running in OFFLINE_MODE\n- Responded with canned confirmation"
                }
            }

        agent = langchain_core.agents.get(request.agent_type)
        if not agent:
            raise ValueError(f"Agent {request.agent_type} not initialized")
        
        # Build context from history
        context = {
            "session_id": request.session_id,
            "history": request.history,
            **request.context
        }
        
        # Process message through agent
        if hasattr(agent, 'analyze'):
            result = await agent.analyze({
                "query": request.message,
                **context
            })
        else:
            # For simpler agents, just run prediction
            result = await agent.agent.apredict(query=request.message)
        
        raw_response = result.get("recommendations") if isinstance(result, dict) else result
        safe_response = redact_pii(raw_response)
        # Confidence scoring (LLM-based heuristic)
        confidence = await compute_confidence(safe_response)
        threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
        escalated = bool(confidence < threshold)
        # Strict escalation mode: replace response if below threshold
        strict = os.getenv("STRICT_ESCALATION", "false").lower() == "true"
        if strict and escalated:
            safe_response = (
                "This response has been held for human review due to low confidence. "
                "A human reviewer will follow up or you may refine your request."
            )
        rationale = None
        if request.explain:
            rationale = await generate_rationale(
                query=request.message,
                response=safe_response
            )

        # Persist escalation event if needed
        if escalated:
            await persist_escalation_event(
                session_id=request.session_id,
                agent=request.agent_type,
                message=request.message,
                response=safe_response,
                confidence=confidence,
                strict=os.getenv("STRICT_ESCALATION", "false").lower() == "true"
            )

        return {
            "response": safe_response,
            "metadata": {
                "agent": request.agent_type,
                "timestamp": datetime.now().isoformat(),
                "confidence": confidence,
                "escalated": escalated,
                "rationale": rationale
            }
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def compute_confidence(text: str) -> float:
    """Estimate response confidence using secondary LLM. Returns [0,1].

    If LLM is unavailable, returns a conservative default of 0.75.
    """
    try:
        if os.getenv("OFFLINE_MODE", "false").lower() == "true":
            return 0.95
        if not text or not isinstance(text, str):
            return 0.0
        global langchain_core
        if not langchain_core or not getattr(langchain_core, 'secondary_llm', None):
            return 0.75
        prompt = (
            "You are a strict evaluator. Given the assistant's reply, output a single number between 0 and 1 "
            "representing your confidence that the reply is factually coherent, helpful, and safe for the user.\n\n"
            f"Reply: '''{text[:4000]}'''\n\nConfidence (0-1):"
        )
        score_text = await langchain_core.secondary_llm.apredict(prompt)
        val = parse_confidence(score_text)
        if val is not None:
            return val
        return 0.75
    except Exception:
        return 0.75


async def generate_rationale(query: str, response: str) -> Optional[str]:
    """Generate a brief, high-level rationale summary (no chain-of-thought).

    Returns 2-3 bullet points explaining why the response is appropriate,
    without exposing hidden reasoning traces.
    """
    try:
        global langchain_core
        if not langchain_core or not getattr(langchain_core, 'secondary_llm', None):
            return None
        prompt = (
            "Provide a concise, high-level rationale for the assistant's reply.\n"
            "Do NOT reveal chain-of-thought or hidden analysis.\n"
            "Use 2-3 bullet points focusing on the key factors considered.\n\n"
            f"User query:\n{(query or '')[:1000]}\n\n"
            f"Assistant reply:\n{(response or '')[:1500]}\n\n"
            "Rationale (bullets only, no chain-of-thought):"
        )
        text = await langchain_core.secondary_llm.apredict(prompt)
        return redact_pii(text)
    except Exception:
        return None


async def persist_escalation_event(session_id: str, agent: str, message: str, response: str,
                                   confidence: float, strict: bool):
    """Append escalation event to a JSONL file under logs/escalations.jsonl.

    This is a simple local sink intended for human triage or later ingestion.
    PII masking is applied to message/response.
    """
    try:
        os.makedirs('logs', exist_ok=True)
        event = {
            "ts": datetime.now().isoformat(),
            "session_id": session_id,
            "agent": agent,
            "confidence": confidence,
            "strict": strict,
            "message": redact_pii(message),
            "response": redact_pii(response)
        }
        with open('logs/escalations.jsonl', 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + "\n")
    except Exception as e:
        logger.warning(f"Failed to persist escalation event: {e}")

# RAG Pipeline Endpoints
@app.post("/rag/create")
async def create_rag_pipeline(request: RAGPipelineRequest):
    """Create a RAG pipeline for documents"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        # Update config for this pipeline
        langchain_core.config["chunk_size"] = request.chunk_size
        langchain_core.config["chunk_overlap"] = request.chunk_overlap
        
        chain = langchain_core.create_rag_pipeline(
            request.document_path,
            request.pipeline_name
        )
        
        return {
            "status": "created",
            "pipeline_name": request.pipeline_name,
            "config": {
                "chunk_size": request.chunk_size,
                "chunk_overlap": request.chunk_overlap
            }
        }
    except Exception as e:
        logger.error(f"RAG pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Knowledge Base Endpoints
@app.post("/knowledge/query")
async def query_knowledge_base(request: KnowledgeQueryRequest):
    """Query a knowledge base"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    try:
        # Update retrieval k for this query
        langchain_core.config["retrieval_k"] = request.k
        
        result = langchain_core.query_knowledge_base(
            request.query,
            request.knowledge_base
        )
        
        return result
    except Exception as e:
        logger.error(f"Knowledge query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket for real-time chat
@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    
    if not langchain_core:
        await websocket.send_json({
            "type": "error",
            "message": "LangChain Core not initialized"
        })
        await websocket.close()
        return
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Process based on message type
            if data.get("type") == "chat":
                agent_type = data.get("agent", "property_analysis")
                agent = langchain_core.agents.get(agent_type)
                
                if agent:
                    # Process message
                    context = {
                        "session_id": session_id,
                        "query": data.get("message")
                    }
                    
                    if hasattr(agent, 'analyze'):
                        result = await agent.analyze(context)
                        response = result.get("recommendations", "")
                    else:
                        response = "Agent response processing..."
                    
                    await websocket.send_json({
                        "type": "response",
                        "message": response,
                        "agent": agent_type,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Agent {agent_type} not found"
                    })
            
            elif data.get("type") == "analyze":
                parcel_id = data.get("parcel_id")
                if parcel_id:
                    result = await langchain_core.analyze_property(parcel_id)
                    await websocket.send_json({
                        "type": "analysis",
                        "data": result
                    })
            
            else:
                await websocket.send_json({
                    "type": "error",
                    "message": "Unknown message type"
                })
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()

# Test endpoints for development
@app.get("/test/agents")
async def test_agents():
    """Test all agents are working"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    results = {}
    for agent_name, agent in langchain_core.agents.items():
        try:
            results[agent_name] = {
                "status": "ready",
                "type": type(agent).__name__
            }
        except Exception as e:
            results[agent_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

@app.get("/test/vector-stores")
async def test_vector_stores():
    """Test vector stores are accessible"""
    if not langchain_core:
        raise HTTPException(status_code=503, detail="LangChain Core not initialized")
    
    results = {}
    for store_name, store in langchain_core.vector_stores.items():
        try:
            results[store_name] = {
                "status": "ready",
                "type": type(store).__name__
            }
        except Exception as e:
            results[store_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        log_level="info",
        reload=False
    )
@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    rid = request.headers.get('x-request-id') or f"{int(time.time()*1000)}-{uuid.uuid4().hex[:8]}"
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        duration = (time.time() - start) * 1000.0
        log = {
            "type": "http",
            "ts": datetime.now().isoformat(),
            "id": rid,
            "method": request.method,
            "path": request.url.path,
            "status": getattr(request, 'state', None) and getattr(getattr(request, 'state'), 'status_code', None),
            "duration_ms": round(duration, 2)
        }
        try:
            logger.info(json.dumps(log))
        except Exception:
            logger.info(str(log))
