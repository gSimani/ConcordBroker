"""
LangGraph Configuration
Central configuration for all LangGraph workflows
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langsmith import Client as LangSmithClient
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LangGraphConfig:
    """Configuration for LangGraph workflows"""
    
    def __init__(self):
        # LangSmith Configuration
        self.langsmith_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "concordbroker")
        
        # LLM Configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.default_llm_model = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini")
        
        # Supabase Configuration
        self.supabase_url = os.getenv("VITE_SUPABASE_URL")
        self.supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
        
        # Workflow Configuration
        self.max_retries = int(os.getenv("WORKFLOW_MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("WORKFLOW_TIMEOUT", "300"))
        self.enable_streaming = os.getenv("ENABLE_STREAMING", "true").lower() == "true"
        self.enable_human_in_loop = os.getenv("ENABLE_HUMAN_IN_LOOP", "false").lower() == "true"
        
        # Cache Configuration
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.cache_ttl = int(os.getenv("CACHE_TTL", "3600"))
        
        # Initialize components
        self._init_langsmith()
        self._init_checkpointer()
        
    def _init_langsmith(self):
        """Initialize LangSmith client if enabled"""
        if self.langsmith_enabled and self.langsmith_api_key:
            try:
                self.langsmith_client = LangSmithClient(
                    api_key=self.langsmith_api_key,
                    api_url=os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
                )
                logger.info(f"LangSmith initialized for project: {self.langsmith_project}")
            except Exception as e:
                logger.error(f"Failed to initialize LangSmith: {e}")
                self.langsmith_client = None
        else:
            self.langsmith_client = None
            logger.info("LangSmith tracing disabled")
    
    def _init_checkpointer(self):
        """Initialize checkpointer for workflow persistence"""
        try:
            # For now, use in-memory checkpointer
            # TODO: Replace with Redis checkpointer for production
            self.checkpointer = MemorySaver()
            logger.info("Initialized in-memory checkpointer")
        except Exception as e:
            logger.error(f"Failed to initialize checkpointer: {e}")
            self.checkpointer = None
    
    def get_llm(self, model: Optional[str] = None):
        """Get configured LLM instance"""
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        
        model_name = model or self.default_llm_model
        
        if "gpt" in model_name.lower():
            return ChatOpenAI(
                model=model_name,
                api_key=self.openai_api_key,
                temperature=0.7,
                streaming=self.enable_streaming
            )
        elif "claude" in model_name.lower():
            return ChatAnthropic(
                model=model_name,
                api_key=self.anthropic_api_key,
                temperature=0.7,
                streaming=self.enable_streaming
            )
        else:
            # Default to OpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                api_key=self.openai_api_key,
                temperature=0.7,
                streaming=self.enable_streaming
            )
    
    def get_embeddings(self):
        """Get configured embeddings model"""
        from langchain_openai import OpenAIEmbeddings
        
        return OpenAIEmbeddings(
            api_key=self.openai_api_key,
            model="text-embedding-3-small"
        )
    
    def get_supabase_client(self):
        """Get Supabase client"""
        from supabase import create_client
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase credentials not configured")
        
        return create_client(self.supabase_url, self.supabase_key)
    
    def create_dataset(self, name: str, description: str) -> Optional[Any]:
        """Create a LangSmith dataset for evaluation"""
        if not self.langsmith_client:
            logger.warning("LangSmith not configured, skipping dataset creation")
            return None
        
        try:
            dataset = self.langsmith_client.create_dataset(
                dataset_name=name,
                description=description,
                data_type="kv"
            )
            logger.info(f"Created dataset: {name}")
            return dataset
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            return None
    
    def log_workflow_run(self, workflow_name: str, status: str, metadata: Dict[str, Any]):
        """Log workflow execution to LangSmith"""
        if not self.langsmith_client:
            return
        
        try:
            # Log to LangSmith
            # This would integrate with LangSmith's run tracking
            logger.info(f"Workflow {workflow_name} completed with status: {status}")
        except Exception as e:
            logger.error(f"Failed to log workflow run: {e}")

# Global configuration instance
config = LangGraphConfig()