"""
LangChain Core System for ConcordBroker
Central orchestration of all LangChain components
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# LangChain imports
from langchain import hub
from langchain.agents import AgentExecutor, create_openai_tools_agent, create_react_agent
from langchain.callbacks import LangChainTracer
from langchain.memory import ConversationBufferWindowMemory
try:
    from langchain_community.chat_message_histories import PostgresChatMessageHistory
except ImportError:
    PostgresChatMessageHistory = None
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.llms import HuggingFaceHub
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.document_loaders import DirectoryLoader, TextLoader, JSONLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain, ConversationalRetrievalChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langsmith import Client

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainCore:
    """
    Core LangChain system for ConcordBroker
    Manages all AI agents, RAG, and memory systems
    """
    
    def __init__(self):
        """Initialize LangChain core components"""
        
        # Import and use permanent configuration
        from .config import LANGCHAIN_CONFIG, configure_langsmith
        
        # Configure LangSmith with permanent API key
        self.langsmith_api_key = configure_langsmith()
        self.config_dict = LANGCHAIN_CONFIG
        
        # Initialize LangSmith client
        self.langsmith_client = Client(api_key=self.langsmith_api_key)
        
        # Ensure storage directories exist
        self._ensure_storage_dirs()

        # Initialize LLMs
        self.primary_llm = self._initialize_primary_llm()
        self.secondary_llm = self._initialize_secondary_llm()
        self.local_llm = self._initialize_local_llm()
        
        # Initialize embeddings (with offline fallback)
        offline = os.getenv("OFFLINE_MODE", "false").lower() == "true"
        openai_key = os.getenv("OPENAI_API_KEY")

        class DummyEmbeddings:
            def embed_documents(self, texts):
                return [[0.0] * 8 for _ in texts]
            def embed_query(self, text):
                return [0.0] * 8

        if offline or not openai_key:
            self.embeddings = DummyEmbeddings()
        else:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=self.config_dict.get("embedding_model", "text-embedding-3-small"),
                    openai_api_key=openai_key
                )
            except TypeError:
                self.embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
        
        # Initialize vector stores
        self.vector_stores = {}
        self._initialize_vector_stores()
        
        # Initialize memory systems
        self.memory_systems = {}
        self._initialize_memory()
        
        # Initialize agents
        self.agents = {}
        self._initialize_agents()
        
        # System configuration
        self.config = {
            "max_iterations": 10,
            "temperature": 0.7,
            "retrieval_k": 5,
            "chunk_size": 1000,
            "chunk_overlap": 200
        }
        
        logger.info("LangChain Core initialized successfully")
    
    def _initialize_primary_llm(self) -> ChatOpenAI:
        """Initialize primary OpenAI LLM for complex reasoning"""
        return ChatOpenAI(
            temperature=float(self.config_dict.get("temperature", 0.7)),
            model_name=self.config_dict.get("primary_model", "gpt-4o"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            callbacks=[LangChainTracer()],
            streaming=True,
            max_tokens=int(self.config_dict.get("max_tokens", 4000))
        )
    
    def _initialize_secondary_llm(self) -> ChatOpenAI:
        """Initialize secondary LLM for routine tasks"""
        return ChatOpenAI(
            temperature=0.5,
            model_name=self.config_dict.get("secondary_model", "gpt-4o-mini"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            callbacks=[LangChainTracer()],
            streaming=True,
            max_tokens=2000
        )

    def _ensure_storage_dirs(self):
        """Ensure vector store and chroma directories exist."""
        try:
            vs = self.config_dict.get("vector_store_path", "./vector_stores")
            ch = self.config_dict.get("chroma_persist_dir", "./chroma_db")
            os.makedirs(vs, exist_ok=True)
            os.makedirs(ch, exist_ok=True)
        except Exception as e:
            logger.warning(f"Storage directory setup failed: {e}")
    
    def _initialize_local_llm(self) -> Optional[HuggingFaceHub]:
        """Initialize local HuggingFace model for private data processing"""
        try:
            token = os.getenv("HUGGINGFACE_API_TOKEN")
            if not token:
                logger.warning("HUGGINGFACE_API_TOKEN not set; local LLM disabled")
                return None
            return HuggingFaceHub(
                repo_id="google/gemma-2b",
                model_kwargs={"temperature": 0.5, "max_length": 512},
                huggingfacehub_api_token=token
            )
        except Exception as e:
            logger.warning(f"Could not initialize local LLM: {e}")
            return None
    
    def _initialize_vector_stores(self):
        """Initialize vector stores for different data types"""
        
        # Property data vector store
        self.vector_stores["properties"] = FAISS.from_texts(
            texts=["Initial property database"],
            embedding=self.embeddings,
            metadatas=[{"type": "property", "initialized": str(datetime.now())}]
        )
        
        # Tax certificate vector store
        self.vector_stores["tax_certificates"] = FAISS.from_texts(
            texts=["Initial tax certificate database"],
            embedding=self.embeddings,
            metadatas=[{"type": "tax_certificate", "initialized": str(datetime.now())}]
        )
        
        # Legal documents vector store
        self.vector_stores["legal_docs"] = Chroma(
            collection_name="legal_documents",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db/legal"
        )
        
        # Market analysis vector store
        self.vector_stores["market_analysis"] = Chroma(
            collection_name="market_analysis",
            embedding_function=self.embeddings,
            persist_directory="./chroma_db/market"
        )
        
        logger.info("Vector stores initialized")
    
    def _initialize_memory(self):
        """Initialize memory systems for conversation and context"""
        
        # Short-term conversation memory
        self.memory_systems["conversation"] = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=10,  # Keep last 10 exchanges
            return_messages=True
        )
        
        # Long-term memory with PostgreSQL
        if os.getenv("POSTGRES_HOST") and PostgresChatMessageHistory:
            try:
                self.memory_systems["long_term"] = PostgresChatMessageHistory(
                    connection_string=os.getenv("DATABASE_URL"),
                    session_id="concordbroker_main"
                )
                logger.info("PostgreSQL memory initialized")
            except Exception as e:
                logger.warning(f"Could not initialize PostgreSQL memory: {e}")
        
        # Property analysis memory
        self.memory_systems["property_analysis"] = {}
        
        # User preference memory
        self.memory_systems["user_preferences"] = {}
    
    def _initialize_agents(self):
        """Initialize specialized agents for different tasks"""
        from .agents import (
            PropertyAnalysisAgent,
            InvestmentAdvisorAgent,
            DataResearchAgent,
            MarketAnalysisAgent,
            LegalComplianceAgent
        )
        
        # Property Analysis Agent
        self.agents["property_analysis"] = PropertyAnalysisAgent(
            llm=self.primary_llm,
            memory=self.memory_systems["conversation"],
            vector_store=self.vector_stores["properties"]
        )
        
        # Investment Advisor Agent
        self.agents["investment_advisor"] = InvestmentAdvisorAgent(
            llm=self.primary_llm,
            memory=self.memory_systems["conversation"]
        )
        
        # Data Research Agent
        self.agents["data_research"] = DataResearchAgent(
            llm=self.secondary_llm,
            vector_stores=self.vector_stores
        )
        
        # Market Analysis Agent
        self.agents["market_analysis"] = MarketAnalysisAgent(
            llm=self.primary_llm,
            vector_store=self.vector_stores["market_analysis"]
        )
        
        # Legal Compliance Agent
        self.agents["legal_compliance"] = LegalComplianceAgent(
            llm=self.primary_llm,
            vector_store=self.vector_stores["legal_docs"]
        )
        
        logger.info(f"Initialized {len(self.agents)} specialized agents")
    
    async def analyze_property(self, parcel_id: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Analyze a property using LangChain agents
        
        Args:
            parcel_id: Property identifier
            analysis_type: Type of analysis (comprehensive, investment, legal, market)
        
        Returns:
            Analysis results with recommendations
        """
        
        # Fetch property data
        property_data = await self._fetch_property_data(parcel_id)
        
        # Select appropriate agent
        if analysis_type == "comprehensive":
            agent = self.agents["property_analysis"]
        elif analysis_type == "investment":
            agent = self.agents["investment_advisor"]
        elif analysis_type == "legal":
            agent = self.agents["legal_compliance"]
        elif analysis_type == "market":
            agent = self.agents["market_analysis"]
        else:
            agent = self.agents["property_analysis"]
        
        # Prepare context
        context = {
            "property_data": property_data,
            "market_conditions": await self._get_market_conditions(),
            "user_preferences": self.memory_systems["user_preferences"],
            "analysis_date": datetime.now().isoformat()
        }
        
        # Run analysis
        try:
            result = await agent.analyze(context)
            
            # Store in memory
            self.memory_systems["property_analysis"][parcel_id] = {
                "timestamp": datetime.now(),
                "analysis": result,
                "type": analysis_type
            }
            
            # Log to LangSmith
            self.langsmith_client.create_run(
                name=f"property_analysis_{parcel_id}",
                run_type="chain",
                inputs={"parcel_id": parcel_id, "type": analysis_type},
                outputs=result
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing property {parcel_id}: {e}")
            raise
    
    async def _fetch_property_data(self, parcel_id: str) -> Dict[str, Any]:
        """Fetch property data from database"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:8002/api/properties/{parcel_id}/complete") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise ValueError(f"Could not fetch property data for {parcel_id}")
    
    async def _get_market_conditions(self) -> Dict[str, Any]:
        """Get current market conditions"""
        return {
            "interest_rates": 7.5,
            "market_trend": "stable",
            "inventory_level": "low",
            "average_dom": 45,
            "price_trend": "+3.2%"
        }
    
    def create_rag_pipeline(self, document_path: str, pipeline_name: str) -> ConversationalRetrievalChain:
        """
        Create a RAG pipeline for document retrieval
        
        Args:
            document_path: Path to documents
            pipeline_name: Name for the pipeline
        
        Returns:
            RAG chain for querying documents
        """
        
        # Load documents
        loader = DirectoryLoader(document_path, glob="**/*.txt")
        documents = loader.load()
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunk_size"],
            chunk_overlap=self.config["chunk_overlap"]
        )
        texts = text_splitter.split_documents(documents)
        
        # Create vector store
        vector_store = FAISS.from_documents(texts, self.embeddings)
        self.vector_stores[pipeline_name] = vector_store
        
        # Create retrieval chain
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.primary_llm,
            retriever=vector_store.as_retriever(
                search_kwargs={"k": self.config["retrieval_k"]}
            ),
            memory=self.memory_systems["conversation"],
            return_source_documents=True,
            verbose=True
        )
        
        logger.info(f"Created RAG pipeline: {pipeline_name}")
        return chain
    
    def query_knowledge_base(self, query: str, knowledge_base: str = "properties") -> Dict[str, Any]:
        """
        Query a specific knowledge base
        
        Args:
            query: User query
            knowledge_base: Which vector store to query
        
        Returns:
            Query results with sources
        """
        
        if knowledge_base not in self.vector_stores:
            raise ValueError(f"Knowledge base '{knowledge_base}' not found")
        
        # Perform similarity search
        results = self.vector_stores[knowledge_base].similarity_search_with_score(
            query, 
            k=self.config["retrieval_k"]
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            })
        
        # Generate summary using LLM
        summary_prompt = f"""
        Based on the following search results, provide a comprehensive answer to the query: "{query}"
        
        Results:
        {formatted_results}
        
        Provide a detailed, actionable response.
        """
        
        summary = self.secondary_llm.predict(summary_prompt)
        
        return {
            "query": query,
            "summary": summary,
            "sources": formatted_results,
            "knowledge_base": knowledge_base,
            "timestamp": datetime.now().isoformat()
        }
    
    def create_custom_agent(self, name: str, description: str, tools: List[Any], 
                          system_prompt: str) -> AgentExecutor:
        """
        Create a custom agent for specific tasks
        
        Args:
            name: Agent name
            description: Agent description
            tools: List of tools the agent can use
            system_prompt: System instructions for the agent
        
        Returns:
            Configured agent executor
        """
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        agent = create_openai_tools_agent(
            llm=self.primary_llm,
            tools=tools,
            prompt=prompt
        )
        
        # Create executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory_systems["conversation"],
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=self.config["max_iterations"],
            early_stopping_method="generate"
        )
        
        # Store agent
        self.agents[name] = agent_executor
        
        logger.info(f"Created custom agent: {name}")
        return agent_executor
    
    def get_agent_metrics(self) -> Dict[str, Any]:
        """Get metrics for all agents"""
        metrics = {
            "agents": {},
            "vector_stores": {},
            "memory_usage": {},
            "performance": {}
        }
        
        # Agent metrics
        for name, agent in self.agents.items():
            metrics["agents"][name] = {
                "status": "active",
                "calls_today": 0,  # Would need to track this
                "avg_response_time": 0  # Would need to track this
            }
        
        # Vector store metrics
        for name, store in self.vector_stores.items():
            # This would vary by vector store type
            metrics["vector_stores"][name] = {
                "documents": "unknown",  # Would need specific methods
                "last_updated": datetime.now().isoformat()
            }
        
        # Memory metrics
        for name, memory in self.memory_systems.items():
            if hasattr(memory, 'buffer'):
                metrics["memory_usage"][name] = len(memory.buffer) if hasattr(memory, 'buffer') else 0
        
        return metrics
    
    def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down LangChain Core")
        
        # Persist vector stores
        for name, store in self.vector_stores.items():
            if hasattr(store, 'save'):
                try:
                    store.save(f"./vector_stores/{name}")
                    logger.info(f"Saved vector store: {name}")
                except Exception as e:
                    logger.error(f"Error saving vector store {name}: {e}")
        
        # Clear memory
        for memory in self.memory_systems.values():
            if hasattr(memory, 'clear'):
                memory.clear()
        
        logger.info("LangChain Core shutdown complete")

    def create_rag_pipeline(self, document_path: str, pipeline_name: str):
        """Create a simple FAISS-based RAG pipeline from a directory or file.

        Documents are loaded from the provided path, chunked, embedded, and stored
        under vector_stores/{pipeline_name}. Returns basic pipeline info.
        """
        try:
            path_obj = Path(document_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Document path not found: {document_path}")

            # Load documents
            docs = []
            if path_obj.is_dir():
                loader = DirectoryLoader(str(path_obj), glob="**/*", show_progress=True)
                docs = loader.load()
            else:
                if path_obj.suffix.lower() in [".json"]:
                    docs = JSONLoader(str(path_obj)).load()
                else:
                    docs = TextLoader(str(path_obj)).load()

            # Split
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.config.get("chunk_size", 1000),
                chunk_overlap=self.config.get("chunk_overlap", 200),
            )
            chunks = splitter.split_documents(docs)

            # Build FAISS index
            index = FAISS.from_documents(chunks, self.embeddings)
            self.vector_stores[pipeline_name] = index

            # Persist if possible
            out_dir = Path(self.config_dict.get("vector_store_path", "./vector_stores")) / pipeline_name
            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                if hasattr(index, "save_local"):
                    index.save_local(str(out_dir))
            except Exception as e:
                logger.warning(f"Could not persist vector store: {e}")

            return {
                "status": "created",
                "pipeline": pipeline_name,
                "documents": len(docs),
                "chunks": len(chunks)
            }
        except Exception as e:
            logger.error(f"create_rag_pipeline error: {e}")
            raise
