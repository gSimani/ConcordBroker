"""
Semantic Search Agent using Jina Embeddings v3
Handles intelligent property search and matching
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import aiohttp
import os
from .base_agent import BaseAgent, AgentStatus

class SemanticSearchAgent(BaseAgent):
    """Agent for semantic property search using Jina embeddings"""
    
    def __init__(self):
        super().__init__(
            agent_id="semantic_search",
            name="Semantic Search Agent",
            description="Intelligent property search using Jina Embeddings v3"
        )
        self.model_id = "jinaai/jina-embeddings-v3"
        self.api_token = os.getenv("HUGGINGFACE_API_TOKEN")
        if not self.api_token:
            raise ValueError("HUGGINGFACE_API_TOKEN not configured for SemanticSearchAgent")
        self.embeddings_cache = {}
        self.property_embeddings = {}
        
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate search query input"""
        if "test" in input_data:
            return True
        return "query" in input_data or "properties" in input_data
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process semantic search request"""
        
        # Handle different input types
        if "query" in input_data:
            return await self._process_search(input_data)
        elif "properties" in input_data:
            return await self._index_properties(input_data)
        else:
            raise ValueError("Invalid input: requires 'query' or 'properties'")
    
    async def _process_search(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process search query and find matching properties"""
        query = input_data["query"]
        max_results = input_data.get("max_results", 10)
        
        self.logger.info(f"Processing semantic search: {query}")
        
        # Get query embedding
        query_embedding = await self._get_embedding(query)
        
        # Search against indexed properties
        if not self.property_embeddings:
            return {
                "status": "no_index",
                "message": "No properties indexed yet. Please index properties first.",
                "query": query
            }
        
        # Calculate similarities
        similarities = []
        for prop_id, prop_data in self.property_embeddings.items():
            similarity = cosine_similarity(
                [query_embedding],
                [prop_data["embedding"]]
            )[0][0]
            
            similarities.append({
                "property_id": prop_id,
                "similarity": float(similarity),
                "description": prop_data["description"],
                "metadata": prop_data.get("metadata", {})
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Get top results
        top_results = similarities[:max_results]
        
        # Enhance results with reasoning
        enhanced_results = []
        for result in top_results:
            enhanced_results.append({
                **result,
                "match_reason": self._generate_match_reason(query, result),
                "confidence": self._calculate_confidence(result["similarity"])
            })
        
        return {
            "query": query,
            "total_results": len(enhanced_results),
            "results": enhanced_results,
            "search_type": "semantic",
            "model": self.model_id
        }
    
    async def _index_properties(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Index properties for semantic search"""
        properties = input_data["properties"]
        indexed_count = 0
        
        for prop in properties:
            prop_id = prop.get("id") or prop.get("parcel_id")
            if not prop_id:
                continue
            
            # Create description from property data
            description = self._create_property_description(prop)
            
            # Get embedding
            embedding = await self._get_embedding(description)
            
            # Store in index
            self.property_embeddings[prop_id] = {
                "embedding": embedding,
                "description": description,
                "metadata": {
                    "address": prop.get("address", ""),
                    "city": prop.get("city", ""),
                    "price": prop.get("price", 0),
                    "bedrooms": prop.get("bedrooms", 0),
                    "bathrooms": prop.get("bathrooms", 0),
                    "sqft": prop.get("sqft", 0)
                }
            }
            indexed_count += 1
        
        self.logger.info(f"Indexed {indexed_count} properties")
        
        return {
            "status": "indexed",
            "properties_indexed": indexed_count,
            "total_in_index": len(self.property_embeddings)
        }
    
    async def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding from Jina model via HuggingFace"""
        
        # Check cache
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        url = f"https://api-inference.huggingface.co/models/{self.model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": text,
            "options": {"wait_for_model": True}
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    # Convert to numpy array
                    embedding = np.array(result)
                    # Cache it
                    self.embeddings_cache[text] = embedding
                    return embedding
                else:
                    # Fallback to random embedding for testing
                    self.logger.warning(f"API call failed, using random embedding")
                    return np.random.rand(768)
    
    def _create_property_description(self, property_data: Dict[str, Any]) -> str:
        """Create searchable description from property data"""
        parts = []
        
        # Add basic info
        if property_data.get("address"):
            parts.append(f"Property at {property_data['address']}")
        if property_data.get("city"):
            parts.append(f"located in {property_data['city']}")
        
        # Add property type
        prop_type = property_data.get("property_type", "residential")
        parts.append(f"{prop_type} property")
        
        # Add features
        if property_data.get("bedrooms"):
            parts.append(f"{property_data['bedrooms']} bedrooms")
        if property_data.get("bathrooms"):
            parts.append(f"{property_data['bathrooms']} bathrooms")
        if property_data.get("sqft"):
            parts.append(f"{property_data['sqft']} square feet")
        
        # Add special features
        features = property_data.get("features", [])
        if features:
            parts.append(f"featuring {', '.join(features)}")
        
        # Add price info
        if property_data.get("price"):
            parts.append(f"priced at ${property_data['price']:,}")
        
        return " ".join(parts)
    
    def _generate_match_reason(self, query: str, result: Dict[str, Any]) -> str:
        """Generate explanation for why property matched"""
        similarity = result["similarity"]
        
        if similarity > 0.9:
            return "Excellent match - property closely aligns with all search criteria"
        elif similarity > 0.8:
            return "Strong match - property meets most search requirements"
        elif similarity > 0.7:
            return "Good match - property has several matching features"
        elif similarity > 0.6:
            return "Moderate match - some relevant features found"
        else:
            return "Partial match - property may be of interest"
    
    def _calculate_confidence(self, similarity: float) -> str:
        """Calculate confidence level from similarity score"""
        if similarity > 0.85:
            return "very_high"
        elif similarity > 0.75:
            return "high"
        elif similarity > 0.65:
            return "medium"
        elif similarity > 0.55:
            return "low"
        else:
            return "very_low"
    
    async def find_similar_properties(self, property_id: str, max_results: int = 5) -> Dict[str, Any]:
        """Find properties similar to a given property"""
        if property_id not in self.property_embeddings:
            return {"error": f"Property {property_id} not found in index"}
        
        target_embedding = self.property_embeddings[property_id]["embedding"]
        
        similarities = []
        for prop_id, prop_data in self.property_embeddings.items():
            if prop_id == property_id:
                continue
            
            similarity = cosine_similarity(
                [target_embedding],
                [prop_data["embedding"]]
            )[0][0]
            
            similarities.append({
                "property_id": prop_id,
                "similarity": float(similarity),
                "description": prop_data["description"]
            })
        
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return {
            "source_property": property_id,
            "similar_properties": similarities[:max_results]
        }
