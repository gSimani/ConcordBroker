"""
HuggingFace Service for AI-powered property intelligence
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import logging
from ..config.huggingface import huggingface_config

logger = logging.getLogger(__name__)

class HuggingFaceService:
    """Service for interacting with HuggingFace models"""
    
    def __init__(self):
        self.config = huggingface_config
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(headers=self.config.get_headers())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def generate_property_description(self, property_data: Dict[str, Any]) -> str:
        """
        Generate an AI-powered property description
        
        Args:
            property_data: Property information including address, size, features
            
        Returns:
            Generated property description
        """
        prompt = self._create_property_prompt(property_data)
        
        endpoint = self.config.get_model_endpoint(self.config.property_description_model)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7,
                "top_p": 0.9
            }
        }
        
        try:
            async with self.session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result[0]["generated_text"] if result else ""
                else:
                    logger.error(f"HuggingFace API error: {response.status}")
                    return ""
        except Exception as e:
            logger.error(f"Error generating property description: {e}")
            return ""
    
    async def analyze_market_sentiment(self, location: str, property_type: str) -> Dict[str, Any]:
        """
        Analyze market sentiment for a specific location and property type
        
        Args:
            location: Property location
            property_type: Type of property (residential, commercial, etc.)
            
        Returns:
            Market analysis results
        """
        text = f"Real estate market analysis for {property_type} properties in {location}"
        
        endpoint = self.config.get_model_endpoint(self.config.market_analysis_model)
        
        payload = {
            "inputs": text,
            "parameters": {
                "candidate_labels": ["bullish", "bearish", "neutral"],
                "multi_label": False
            }
        }
        
        try:
            async with self.session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "sentiment": result.get("labels", ["neutral"])[0],
                        "confidence": result.get("scores", [0])[0]
                    }
                else:
                    logger.error(f"HuggingFace API error: {response.status}")
                    return {"sentiment": "neutral", "confidence": 0.5}
        except Exception as e:
            logger.error(f"Error analyzing market sentiment: {e}")
            return {"sentiment": "neutral", "confidence": 0.5}
    
    async def embed_property_features(self, features: List[str]) -> List[float]:
        """
        Create embeddings for property features
        
        Args:
            features: List of property features
            
        Returns:
            Feature embeddings
        """
        endpoint = self.config.get_model_endpoint(self.config.embedding_model)
        
        payload = {
            "inputs": " ".join(features),
            "options": {"wait_for_model": True}
        }
        
        try:
            async with self.session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result if isinstance(result, list) else []
                else:
                    logger.error(f"HuggingFace API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return []
    
    async def classify_property_inquiry(self, inquiry: str) -> Dict[str, Any]:
        """
        Classify user inquiries about properties
        
        Args:
            inquiry: User's inquiry text
            
        Returns:
            Classification result with intent and confidence
        """
        endpoint = self.config.get_model_endpoint(self.config.classification_model)
        
        payload = {
            "inputs": inquiry,
            "options": {"wait_for_model": True}
        }
        
        try:
            async with self.session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if result and isinstance(result, list) and len(result) > 0:
                        top_result = result[0][0] if isinstance(result[0], list) else result[0]
                        return {
                            "intent": top_result.get("label", "unknown"),
                            "confidence": top_result.get("score", 0.0)
                        }
                    return {"intent": "unknown", "confidence": 0.0}
                else:
                    logger.error(f"HuggingFace API error: {response.status}")
                    return {"intent": "unknown", "confidence": 0.0}
        except Exception as e:
            logger.error(f"Error classifying inquiry: {e}")
            return {"intent": "unknown", "confidence": 0.0}
    
    def _create_property_prompt(self, property_data: Dict[str, Any]) -> str:
        """Create a prompt for property description generation"""
        address = property_data.get("address", "Unknown address")
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        square_feet = property_data.get("square_feet", 0)
        property_type = property_data.get("property_type", "property")
        
        prompt = f"""Generate a compelling real estate description for:
        Address: {address}
        Type: {property_type}
        Bedrooms: {bedrooms}
        Bathrooms: {bathrooms}
        Size: {square_feet} sq ft
        
        Description:"""
        
        return prompt

# Singleton instance
huggingface_service = HuggingFaceService()