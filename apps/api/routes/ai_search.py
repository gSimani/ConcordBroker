"""
AI Search API Routes
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import asyncio
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_search_service import ai_search_service

router = APIRouter(prefix="/api/ai", tags=["AI Search"])

class SearchRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    max_results: Optional[int] = 20

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    success: bool
    query: str
    conversation_id: str
    extracted_features: Dict[str, Any]
    properties: List[Dict[str, Any]]
    total_found: int
    insights: str
    processing_history: List[Dict[str, Any]]

@router.post("/semantic-search", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search using chain of agents
    """
    try:
        result = await ai_search_service.search(
            query=request.query,
            conversation_id=request.conversation_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_ai(message: ChatMessage):
    """
    Chat endpoint for conversational property search
    """
    try:
        # Process the message through the AI chain
        result = await ai_search_service.search(
            query=message.message,
            conversation_id=message.conversation_id
        )
        
        # Format response for chat
        response = {
            "conversation_id": result['conversation_id'],
            "user_message": message.message,
            "ai_response": result['insights'],
            "properties_found": result['total_found'],
            "top_properties": result['properties'][:3] if result['properties'] else [],
            "extracted_intent": result['extracted_features'],
            "timestamp": datetime.now().isoformat()
        }
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    Get conversation history
    """
    history = ai_search_service.get_conversation_history(conversation_id)
    return {
        "conversation_id": conversation_id,
        "history": history
    }

@router.delete("/conversation/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """
    Clear conversation history
    """
    ai_search_service.clear_conversation(conversation_id)
    return {"message": "Conversation cleared"}

@router.post("/suggest")
async def get_suggestions(query: str):
    """
    Get AI-powered search suggestions
    """
    suggestions = [
        f"{query} with pool",
        f"{query} near schools",
        f"{query} recently renovated",
        f"luxury {query}",
        f"affordable {query}",
        f"{query} with ocean view",
        f"{query} in gated community",
        f"investment {query}"
    ]
    
    return {
        "query": query,
        "suggestions": suggestions[:5]
    }

# WebSocket for real-time chat
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat
    """
    await websocket.accept()
    conversation_id = str(datetime.now().timestamp())
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Send typing indicator
            await websocket.send_json({
                "type": "typing",
                "message": "AI is thinking..."
            })
            
            # Process through AI chain
            result = await ai_search_service.search(
                query=message_data.get('message', ''),
                conversation_id=conversation_id
            )
            
            # Send results back
            await websocket.send_json({
                "type": "response",
                "conversation_id": conversation_id,
                "ai_response": result['insights'],
                "properties": result['properties'][:5],
                "total_found": result['total_found'],
                "extracted_features": result['extracted_features']
            })
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
        await websocket.close()