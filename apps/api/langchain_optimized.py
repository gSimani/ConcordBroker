"""
Optimized LangChain Configuration for ConcordBroker
Leverages latest LangChain features for maximum performance
"""

import os
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langsmith import Client
import asyncio
from functools import lru_cache

# Enable caching for LLM calls
set_llm_cache(InMemoryCache())

class OptimizedLangChainConfig:
    """Optimized configuration for LangChain with latest features"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.langsmith_key = os.getenv("LANGSMITH_API_KEY")
        self.setup_optimized_llm()
        
    @lru_cache(maxsize=1)
    def setup_optimized_llm(self):
        """Create optimized LLM with caching and streaming"""
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            streaming=True,  # Enable streaming for real-time responses
            max_tokens=4000,
            request_timeout=30,
            max_retries=3,
            model_kwargs={
                "top_p": 0.95,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0
            },
            # Add callback for streaming
            callbacks=[StreamingStdOutCallbackHandler()] if os.getenv("DEBUG") else []
        )
        
        # Create a faster version for simple queries
        self.fast_llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            max_tokens=1000,
            request_timeout=10
        )
        
        return self.llm
    
    def create_optimized_chain(self):
        """Create an optimized chain with parallel processing"""
        
        # Prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are a helpful real estate assistant."),
            MessagesPlaceholder(variable_name="history"),
            HumanMessage(content="{input}")
        ])
        
        # Create chain with parallel processing
        chain = (
            RunnablePassthrough.assign(
                context=lambda x: x.get("context", "")
            )
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain
    
    def create_parallel_chain(self, tasks: Dict[str, Any]):
        """Create chain that runs multiple tasks in parallel"""
        
        # Run multiple operations in parallel
        parallel_chain = RunnableParallel(
            **{name: task for name, task in tasks.items()}
        )
        
        return parallel_chain
    
    async def batch_process(self, inputs: list):
        """Process multiple inputs in batch for efficiency"""
        
        # Use batch processing for multiple inputs
        results = await self.llm.abatch(inputs)
        return results
    
    def create_agent_with_tools(self, tools: list):
        """Create an optimized agent with tool execution"""
        
        from langchain.agents import create_openai_functions_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant with access to tools."),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        
        # Create executor with optimizations
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=False,
            max_iterations=5,
            early_stopping_method="generate",
            handle_parsing_errors=True,
            return_intermediate_steps=False  # Reduce memory usage
        )
        
        return agent_executor

class OptimizedPropertySearchWorkflow:
    """Optimized property search using latest LangGraph features"""
    
    def __init__(self):
        self.config = OptimizedLangChainConfig()
        self.graph = self._build_optimized_graph()
        
    def _build_optimized_graph(self):
        """Build optimized LangGraph workflow"""
        
        workflow = StateGraph(dict)
        
        # Add nodes with async processing
        workflow.add_node("parse_query", self.parse_query)
        workflow.add_node("search_properties", self.search_properties) 
        workflow.add_node("enrich_results", self.enrich_results)
        workflow.add_node("format_response", self.format_response)
        
        # Add edges with conditional routing
        workflow.set_entry_point("parse_query")
        workflow.add_edge("parse_query", "search_properties")
        workflow.add_edge("search_properties", "enrich_results")
        workflow.add_edge("enrich_results", "format_response")
        workflow.add_edge("format_response", END)
        
        return workflow.compile()
    
    async def parse_query(self, state: dict):
        """Parse user query with optimized LLM"""
        query = state.get("query", "")
        
        # Use fast LLM for simple parsing
        prompt = f"Extract location, price range, and property type from: {query}"
        parsed = await self.config.fast_llm.ainvoke(prompt)
        
        state["parsed_query"] = parsed.content
        return state
    
    async def search_properties(self, state: dict):
        """Search properties with parallel processing"""
        # Simulate parallel property search
        await asyncio.sleep(0.1)  # Replace with actual search
        
        state["results"] = [
            {"id": 1, "address": "123 Main St", "price": 500000},
            {"id": 2, "address": "456 Oak Ave", "price": 750000}
        ]
        return state
    
    async def enrich_results(self, state: dict):
        """Enrich results with additional data in parallel"""
        results = state.get("results", [])
        
        # Process enrichment in parallel
        enrichment_tasks = []
        for result in results:
            enrichment_tasks.append(self._enrich_single_property(result))
        
        enriched = await asyncio.gather(*enrichment_tasks)
        state["enriched_results"] = enriched
        return state
    
    async def _enrich_single_property(self, property_data: dict):
        """Enrich single property with additional data"""
        # Simulate API call for enrichment
        await asyncio.sleep(0.05)
        
        property_data["school_rating"] = "A"
        property_data["neighborhood_score"] = 8.5
        return property_data
    
    async def format_response(self, state: dict):
        """Format final response"""
        enriched = state.get("enriched_results", [])
        
        # Use streaming for large responses
        response = {
            "total": len(enriched),
            "properties": enriched,
            "query": state.get("query"),
            "timestamp": "2025-01-09"
        }
        
        state["final_response"] = response
        return state
    
    async def run(self, query: str):
        """Run optimized workflow"""
        initial_state = {"query": query}
        result = await self.graph.ainvoke(initial_state)
        return result.get("final_response")

class PerformanceOptimizations:
    """Additional performance optimizations for LangChain"""
    
    @staticmethod
    def enable_streaming(llm: ChatOpenAI):
        """Enable streaming for real-time responses"""
        llm.streaming = True
        return llm
    
    @staticmethod
    def setup_caching():
        """Setup Redis caching for LangChain"""
        try:
            from langchain.cache import RedisCache
            import redis
            
            redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
            set_llm_cache(RedisCache(redis_client))
            print("[OK] Redis cache enabled for LangChain")
        except Exception as e:
            # Fallback to in-memory cache
            set_llm_cache(InMemoryCache())
            print("[OK] In-memory cache enabled for LangChain")
    
    @staticmethod
    async def parallel_llm_calls(llm: ChatOpenAI, prompts: list):
        """Execute multiple LLM calls in parallel"""
        tasks = [llm.ainvoke(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results
    
    @staticmethod
    def optimize_token_usage(text: str, max_tokens: int = 1000):
        """Optimize token usage by truncating intelligently"""
        from tiktoken import encoding_for_model
        
        try:
            encoder = encoding_for_model("gpt-4")
            tokens = encoder.encode(text)
            
            if len(tokens) > max_tokens:
                truncated = encoder.decode(tokens[:max_tokens])
                return truncated + "..."
            return text
        except:
            # Fallback to character-based truncation
            max_chars = max_tokens * 4
            if len(text) > max_chars:
                return text[:max_chars] + "..."
            return text

# Performance monitoring utilities
class LangChainMonitor:
    """Monitor LangChain performance"""
    
    def __init__(self):
        self.metrics = {
            "llm_calls": 0,
            "total_tokens": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time": 0
        }
    
    async def track_llm_call(self, func, *args, **kwargs):
        """Track LLM call metrics"""
        import time
        
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        
        self.metrics["llm_calls"] += 1
        self.metrics["avg_response_time"] = (
            (self.metrics["avg_response_time"] * (self.metrics["llm_calls"] - 1) + duration) 
            / self.metrics["llm_calls"]
        )
        
        return result
    
    def get_metrics(self):
        """Get performance metrics"""
        return self.metrics

# Usage example
async def main():
    """Example usage of optimized LangChain"""
    
    # Setup optimizations
    PerformanceOptimizations.setup_caching()
    
    # Create optimized workflow
    workflow = OptimizedPropertySearchWorkflow()
    
    # Run search
    result = await workflow.run("Find me luxury homes in Fort Lauderdale under $1M")
    print(f"Search results: {result}")
    
    # Parallel processing example
    config = OptimizedLangChainConfig()
    prompts = [
        "What is the weather today?",
        "Tell me about real estate",
        "How do I search properties?"
    ]
    
    # Process multiple prompts in parallel
    results = await PerformanceOptimizations.parallel_llm_calls(config.fast_llm, prompts)
    for r in results:
        print(f"Response: {r.content[:100]}...")

if __name__ == "__main__":
    asyncio.run(main())