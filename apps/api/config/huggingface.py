"""
HuggingFace API Configuration for ConcordBroker
Handles AI/ML model integration and inference
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseSettings, Field

class HuggingFaceConfig(BaseSettings):
    """HuggingFace API configuration"""
    
    # HuggingFace Credentials
    hf_api_token: str = Field(
        default="",
        env="HUGGINGFACE_API_TOKEN"
    )
    hf_organization: str = Field(
        default="Concord Broker",
        env="HUGGINGFACE_ORG"
    )
    hf_base_url: str = Field(
        default="https://api-inference.huggingface.co",
        env="HUGGINGFACE_BASE_URL"
    )
    
    # Model Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="HF_EMBEDDING_MODEL"
    )
    text_generation_model: str = Field(
        default="microsoft/phi-2",
        env="HF_TEXT_MODEL"
    )
    classification_model: str = Field(
        default="distilbert-base-uncased-finetuned-sst-2-english",
        env="HF_CLASSIFICATION_MODEL"
    )
    
    # Property Analysis Models
    property_description_model: str = Field(
        default="google/flan-t5-base",
        env="HF_PROPERTY_DESC_MODEL"
    )
    market_analysis_model: str = Field(
        default="facebook/bart-large-mnli",
        env="HF_MARKET_ANALYSIS_MODEL"
    )
    
    # API Settings
    max_retries: int = Field(default=3, env="HF_MAX_RETRIES")
    timeout: int = Field(default=30, env="HF_TIMEOUT")
    use_gpu: bool = Field(default=False, env="HF_USE_GPU")
    
    class Config:
        env_file = ".env.huggingface"
        env_file_encoding = "utf-8"
    
    def get_headers(self) -> Dict[str, str]:
        """Get authorization headers for HuggingFace API"""
        if not self.hf_api_token:
            raise ValueError("HuggingFace API token not configured")
        return {
            "Authorization": f"Bearer {self.hf_api_token}",
            "Content-Type": "application/json"
        }
    
    def get_model_endpoint(self, model: str) -> str:
        """Get the full endpoint URL for a model"""
        return f"{self.hf_base_url}/models/{model}"
    
    def validate_token(self) -> bool:
        """Validate the HuggingFace API token"""
        return bool(self.hf_api_token and self.hf_api_token.startswith("hf_"))

# Singleton instance
huggingface_config = HuggingFaceConfig()