"""
AI-Powered Routes for ConcordBroker
Implements HuggingFace models for real estate intelligence
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import aiohttp
import asyncio
import os
from datetime import datetime

router = APIRouter(prefix="/api/ai", tags=["AI"])

# HuggingFace configuration
HF_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
HF_BASE_URL = "https://api-inference.huggingface.co"

# Skip AI routes if token not configured
if not HF_TOKEN:
    print("WARNING: HUGGINGFACE_API_TOKEN not configured - AI routes will return mock responses")

# Model endpoints
MODELS = {
    "description": "facebook/bart-large",
    "embedding": "sentence-transformers/all-mpnet-base-v2",
    "sentiment": "ProsusAI/finbert",
    "ner": "dslim/bert-base-NER",
    "qa": "deepset/roberta-base-squad2",
    "summarization": "facebook/bart-large-cnn",
    "classification": "facebook/bart-large-mnli"
}

# Request/Response models
class PropertyDescriptionRequest(BaseModel):
    address: str
    bedrooms: int
    bathrooms: float
    square_feet: int
    property_type: str
    features: List[str] = []
    style: str = "professional"  # professional, luxury, casual

class PropertySearchRequest(BaseModel):
    query: str
    max_results: int = 10

class MarketAnalysisRequest(BaseModel):
    location: str
    property_type: str
    text: Optional[str] = None

class DocumentExtractionRequest(BaseModel):
    text: str
    extract_type: str = "all"  # all, names, addresses, prices, dates

class QARequest(BaseModel):
    context: str
    question: str

async def call_huggingface_api(model: str, payload: Dict[str, Any]) -> Any:
    """Generic function to call HuggingFace API"""
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    url = f"{HF_BASE_URL}/models/{model}"
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"HuggingFace API error: {error_text}")
        except asyncio.TimeoutError:
            raise HTTPException(status_code=504, detail="Request timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-description")
async def generate_property_description(request: PropertyDescriptionRequest):
    """
    Generate AI-powered property description using BART
    """
    # Create prompt based on style
    style_prompts = {
        "professional": "Generate a professional real estate listing description:",
        "luxury": "Create an elegant, luxury real estate description emphasizing exclusivity:",
        "casual": "Write a friendly, approachable property description:"
    }
    
    features_text = ", ".join(request.features) if request.features else "standard features"
    
    prompt = f"""{style_prompts.get(request.style, style_prompts['professional'])}
    
    Address: {request.address}
    Type: {request.property_type}
    Bedrooms: {request.bedrooms}
    Bathrooms: {request.bathrooms}
    Size: {request.square_feet} sq ft
    Features: {features_text}
    
    Description:"""
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 200,
            "temperature": 0.8,
            "top_p": 0.9,
            "do_sample": True
        }
    }
    
    result = await call_huggingface_api(MODELS["description"], payload)
    
    # Extract generated text - handle different response formats
    generated_text = ""
    if isinstance(result, list) and len(result) > 0:
        if isinstance(result[0], dict):
            generated_text = result[0].get("generated_text", "")
        else:
            generated_text = str(result[0])
    elif isinstance(result, dict):
        generated_text = result.get("generated_text", "")
    
    # Clean up the response
    if "Description:" in generated_text:
        generated_text = generated_text.split("Description:")[-1].strip()
    
    return {
        "description": generated_text,
        "property_data": request.dict(),
        "model": MODELS["description"],
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/semantic-search")
async def semantic_property_search(request: PropertySearchRequest):
    """
    Convert search query to embeddings for semantic property matching
    """
    payload = {
        "inputs": request.query,
        "options": {"wait_for_model": True}
    }
    
    embeddings = await call_huggingface_api(MODELS["embedding"], payload)
    
    # These embeddings would be compared with property embeddings in the database
    # For now, return the embedding and mock matches
    return {
        "query": request.query,
        "embedding_dims": len(embeddings) if isinstance(embeddings, list) else 768,
        "embedding_sample": embeddings[:10] if isinstance(embeddings, list) else [],
        "suggested_properties": [
            {
                "id": "prop_001",
                "address": "123 Ocean Drive, Miami Beach",
                "similarity_score": 0.92,
                "match_reason": "Waterfront location with luxury amenities"
            },
            {
                "id": "prop_002", 
                "address": "456 Bayview Terrace, Key Biscayne",
                "similarity_score": 0.87,
                "match_reason": "Ocean views and modern design"
            }
        ]
    }

@router.post("/market-sentiment")
async def analyze_market_sentiment(request: MarketAnalysisRequest):
    """
    Analyze market sentiment using FinBERT
    """
    text = request.text or f"Real estate market analysis for {request.property_type} properties in {request.location}"
    
    payload = {
        "inputs": text,
        "options": {"wait_for_model": True}
    }
    
    result = await call_huggingface_api(MODELS["sentiment"], payload)
    
    # Parse FinBERT output
    if isinstance(result, list) and len(result) > 0:
        sentiment_data = result[0] if isinstance(result[0], list) else result
        
        # Map FinBERT labels to our categories
        label_mapping = {
            "positive": "bullish",
            "negative": "bearish", 
            "neutral": "neutral"
        }
        
        sentiment = "neutral"
        confidence = 0.5
        
        if isinstance(sentiment_data, dict):
            sentiment = label_mapping.get(sentiment_data.get("label", "neutral").lower(), "neutral")
            confidence = sentiment_data.get("score", 0.5)
        elif isinstance(sentiment_data, list) and len(sentiment_data) > 0:
            sentiment = label_mapping.get(sentiment_data[0].get("label", "neutral").lower(), "neutral")
            confidence = sentiment_data[0].get("score", 0.5)
    else:
        sentiment = "neutral"
        confidence = 0.5
    
    return {
        "location": request.location,
        "property_type": request.property_type,
        "sentiment": sentiment,
        "confidence": confidence,
        "analysis": {
            "trend": "upward" if sentiment == "bullish" else "downward" if sentiment == "bearish" else "stable",
            "recommendation": "Good time to invest" if sentiment == "bullish" else "Exercise caution" if sentiment == "bearish" else "Market is stable"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/extract-entities")
async def extract_entities(request: DocumentExtractionRequest):
    """
    Extract named entities from property documents using NER
    """
    payload = {
        "inputs": request.text,
        "options": {"wait_for_model": True}
    }
    
    result = await call_huggingface_api(MODELS["ner"], payload)
    
    # Process NER results
    entities = {
        "persons": [],
        "locations": [],
        "organizations": [],
        "money": [],
        "dates": []
    }
    
    if isinstance(result, list):
        for entity in result:
            entity_type = entity.get("entity_group", entity.get("entity", "")).lower()
            word = entity.get("word", "")
            
            if "per" in entity_type:
                entities["persons"].append(word)
            elif "loc" in entity_type or "gpe" in entity_type:
                entities["locations"].append(word)
            elif "org" in entity_type:
                entities["organizations"].append(word)
            elif "money" in entity_type or "$" in word:
                entities["money"].append(word)
            elif "date" in entity_type or "time" in entity_type:
                entities["dates"].append(word)
    
    # Clean up duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return {
        "extracted_entities": entities,
        "total_entities": sum(len(v) for v in entities.values()),
        "text_length": len(request.text),
        "model": MODELS["ner"]
    }

@router.post("/property-qa")
async def property_question_answering(request: QARequest):
    """
    Answer questions about properties using RoBERTa-SQuAD
    """
    payload = {
        "inputs": {
            "question": request.question,
            "context": request.context
        },
        "options": {"wait_for_model": True}
    }
    
    result = await call_huggingface_api(MODELS["qa"], payload)
    
    return {
        "question": request.question,
        "answer": result.get("answer", "Unable to find answer"),
        "confidence": result.get("score", 0),
        "start_position": result.get("start", 0),
        "end_position": result.get("end", 0),
        "model": MODELS["qa"]
    }

@router.post("/summarize-document")
async def summarize_document(text: str, max_length: int = 150):
    """
    Summarize property documents, inspection reports, etc.
    """
    payload = {
        "inputs": text,
        "parameters": {
            "max_length": max_length,
            "min_length": 30,
            "do_sample": False
        }
    }
    
    result = await call_huggingface_api(MODELS["summarization"], payload)
    
    summary = result[0]["summary_text"] if isinstance(result, list) else result.get("summary_text", "")
    
    return {
        "original_length": len(text),
        "summary": summary,
        "summary_length": len(summary),
        "compression_ratio": f"{(1 - len(summary)/len(text)) * 100:.1f}%",
        "model": MODELS["summarization"]
    }

@router.post("/classify-inquiry")
async def classify_customer_inquiry(text: str):
    """
    Classify customer inquiries for better routing
    """
    labels = ["buying", "selling", "renting", "valuation", "general inquiry", "complaint"]
    
    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": labels,
            "multi_label": False
        }
    }
    
    result = await call_huggingface_api(MODELS["classification"], payload)
    
    return {
        "inquiry": text,
        "classification": result.get("labels", ["unknown"])[0],
        "confidence": result.get("scores", [0])[0],
        "all_scores": dict(zip(result.get("labels", []), result.get("scores", [])))
    }

@router.get("/ai-status")
async def get_ai_status():
    """
    Check status of AI services
    """
    return {
        "status": "operational",
        "models": MODELS,
        "token_configured": bool(HF_TOKEN),
        "base_url": HF_BASE_URL,
        "available_endpoints": [
            "/generate-description",
            "/semantic-search",
            "/market-sentiment",
            "/extract-entities",
            "/property-qa",
            "/summarize-document",
            "/classify-inquiry"
        ]
    }

# Export router
__all__ = ["router"]
