"""
Async Agent Orchestrator for ConcordBroker
High-performance async orchestration replacing ThreadPoolExecutor
"""

import asyncio
import os
import time
import logging
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AgentResult:
    """Result from agent execution"""
    agent_name: str
    status: AgentStatus
    data: Any
    start_time: datetime
    end_time: datetime
    duration: float
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

class AsyncAgent:
    """Base class for async agents"""
    
    def __init__(self, name: str, timeout: int = 300):
        self.name = name
        self.timeout = timeout
        self.status = AgentStatus.PENDING
        self.result = None
        
    async def execute(self, context: Dict = None) -> Any:
        """Execute agent logic - override in subclasses"""
        raise NotImplementedError
    
    async def run(self, context: Dict = None) -> AgentResult:
        """Run agent with error handling and metrics"""
        start_time = datetime.now()
        self.status = AgentStatus.RUNNING
        
        try:
            # Execute with timeout
            result_data = await asyncio.wait_for(
                self.execute(context),
                timeout=self.timeout
            )
            
            self.status = AgentStatus.COMPLETED
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.COMPLETED,
                data=result_data,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds()
            )
            
        except asyncio.TimeoutError:
            self.status = AgentStatus.FAILED
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=f"Timeout after {self.timeout} seconds"
            )
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            result = AgentResult(
                agent_name=self.name,
                status=AgentStatus.FAILED,
                data=None,
                start_time=start_time,
                end_time=datetime.now(),
                duration=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
            logger.error(f"Agent {self.name} failed: {e}")
        
        self.result = result
        return result

class OptimizedOrchestrator:
    """High-performance async orchestrator"""
    
    def __init__(self, max_concurrent: int = 10, enable_monitoring: bool = True):
        self.max_concurrent = max_concurrent
        self.enable_monitoring = enable_monitoring
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.running_agents: Set[str] = set()
        self.results: List[AgentResult] = []
        self.start_time = None
        self.end_time = None
        
    async def run_agent_with_semaphore(self, agent: AsyncAgent, context: Dict = None) -> AgentResult:
        """Run single agent with concurrency control"""
        async with self.semaphore:
            self.running_agents.add(agent.name)
            logger.info(f"[RUNNING] Agent '{agent.name}' started")
            
            try:
                result = await agent.run(context)
                
                if result.status == AgentStatus.COMPLETED:
                    logger.info(f"[OK] Agent '{agent.name}' completed in {result.duration:.2f}s")
                else:
                    logger.error(f"[ERROR] Agent '{agent.name}' failed: {result.error}")
                
                return result
                
            finally:
                self.running_agents.discard(agent.name)
    
    async def run_parallel(self, agents: List[AsyncAgent], context: Dict = None) -> List[AgentResult]:
        """Run multiple agents in parallel"""
        self.start_time = datetime.now()
        self.running_agents.clear()
        self.results.clear()
        
        logger.info(f"Starting {len(agents)} agents with max concurrency of {self.max_concurrent}")
        
        # Create tasks for all agents
        tasks = [
            self.run_agent_with_semaphore(agent, context)
            for agent in agents
        ]
        
        # Run all tasks and gather results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Unexpected error: {result}")
            else:
                self.results.append(result)
        
        self.end_time = datetime.now()
        total_duration = (self.end_time - self.start_time).total_seconds()
        
        # Generate summary
        completed = sum(1 for r in self.results if r.status == AgentStatus.COMPLETED)
        failed = sum(1 for r in self.results if r.status == AgentStatus.FAILED)
        
        logger.info(f"Orchestration completed in {total_duration:.2f}s")
        logger.info(f"Results: {completed} completed, {failed} failed")
        
        if self.enable_monitoring:
            await self.save_metrics()
        
        return self.results
    
    async def run_sequential(self, agents: List[AsyncAgent], context: Dict = None) -> List[AgentResult]:
        """Run agents sequentially (for dependent workflows)"""
        self.start_time = datetime.now()
        self.results.clear()
        
        for agent in agents:
            result = await agent.run(context)
            self.results.append(result)
            
            # Pass result to next agent in context
            if context is None:
                context = {}
            context[f"{agent.name}_result"] = result.data
            
            # Stop on failure if needed
            if result.status == AgentStatus.FAILED:
                logger.warning(f"Stopping sequential execution due to failure of {agent.name}")
                break
        
        self.end_time = datetime.now()
        return self.results
    
    async def run_pipeline(self, pipeline: List[List[AsyncAgent]], context: Dict = None) -> List[AgentResult]:
        """Run pipeline of agent stages (parallel within stage, sequential between stages)"""
        all_results = []
        
        for stage_num, stage_agents in enumerate(pipeline):
            logger.info(f"Running pipeline stage {stage_num + 1} with {len(stage_agents)} agents")
            
            # Run agents in this stage in parallel
            stage_results = await self.run_parallel(stage_agents, context)
            all_results.extend(stage_results)
            
            # Check if any failed
            if any(r.status == AgentStatus.FAILED for r in stage_results):
                logger.error(f"Pipeline stopped at stage {stage_num + 1} due to failures")
                break
            
            # Update context with results for next stage
            if context is None:
                context = {}
            for result in stage_results:
                context[f"{result.agent_name}_result"] = result.data
        
        return all_results
    
    async def save_metrics(self):
        """Save execution metrics for monitoring"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self.results),
            "completed": sum(1 for r in self.results if r.status == AgentStatus.COMPLETED),
            "failed": sum(1 for r in self.results if r.status == AgentStatus.FAILED),
            "total_duration": (self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            "avg_duration": sum(r.duration for r in self.results) / len(self.results) if self.results else 0,
            "max_duration": max((r.duration for r in self.results), default=0),
            "min_duration": min((r.duration for r in self.results), default=0),
            "agents": [
                {
                    "name": r.agent_name,
                    "status": r.status.value,
                    "duration": r.duration,
                    "error": r.error
                }
                for r in self.results
            ]
        }
        
        # Save to file
        metrics_dir = Path("metrics")
        metrics_dir.mkdir(exist_ok=True)
        
        metrics_file = metrics_dir / f"orchestration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Metrics saved to {metrics_file}")

# Example Agent Implementations
class DataLoaderAgent(AsyncAgent):
    """Example async data loader agent"""
    
    async def execute(self, context: Dict = None) -> Dict:
        """Load data asynchronously"""
        # Simulate async data loading
        await asyncio.sleep(1)
        
        return {
            "records_loaded": 1000,
            "source": "florida_parcels",
            "timestamp": datetime.now().isoformat()
        }

class ValidationAgent(AsyncAgent):
    """Example async validation agent"""
    
    async def execute(self, context: Dict = None) -> Dict:
        """Validate data asynchronously"""
        # Get data from previous agent if available
        data = context.get("DataLoader_result", {}) if context else {}
        
        # Simulate validation
        await asyncio.sleep(0.5)
        
        return {
            "valid_records": data.get("records_loaded", 0) * 0.95,
            "invalid_records": data.get("records_loaded", 0) * 0.05,
            "timestamp": datetime.now().isoformat()
        }

class EnrichmentAgent(AsyncAgent):
    """Example async enrichment agent"""
    
    async def execute(self, context: Dict = None) -> Dict:
        """Enrich data with additional information"""
        # Simulate API calls for enrichment
        await asyncio.sleep(2)
        
        return {
            "enriched_records": 950,
            "enrichment_source": "sunbiz_api",
            "timestamp": datetime.now().isoformat()
        }

class NotificationAgent(AsyncAgent):
    """Example async notification agent"""
    
    async def execute(self, context: Dict = None) -> Dict:
        """Send notifications about completed processing"""
        # Simulate sending notifications
        await asyncio.sleep(0.3)
        
        return {
            "notifications_sent": 5,
            "channels": ["email", "webhook"],
            "timestamp": datetime.now().isoformat()
        }

# Utility function to convert existing sync agents
def make_async(sync_function: Callable) -> Callable:
    """Convert synchronous function to async"""
    async def async_wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, sync_function, *args, **kwargs)
    return async_wrapper

# Main execution example
async def main():
    """Example usage of the optimized orchestrator"""
    
    # Create orchestrator
    orchestrator = OptimizedOrchestrator(max_concurrent=5)
    
    # Create agents
    agents = [
        DataLoaderAgent("DataLoader", timeout=60),
        ValidationAgent("Validator", timeout=30),
        EnrichmentAgent("Enricher", timeout=120),
        NotificationAgent("Notifier", timeout=30)
    ]
    
    # Example 1: Run all agents in parallel
    print("\n[1] Running agents in parallel...")
    results = await orchestrator.run_parallel(agents)
    for r in results:
        print(f"  {r.agent_name}: {r.status.value} ({r.duration:.2f}s)")
    
    # Example 2: Run agents sequentially
    print("\n[2] Running agents sequentially...")
    results = await orchestrator.run_sequential(agents)
    for r in results:
        print(f"  {r.agent_name}: {r.status.value} ({r.duration:.2f}s)")
    
    # Example 3: Run pipeline (stages)
    print("\n[3] Running pipeline...")
    pipeline = [
        [DataLoaderAgent("Loader1"), DataLoaderAgent("Loader2")],  # Stage 1: parallel loaders
        [ValidationAgent("Validator")],  # Stage 2: validation
        [EnrichmentAgent("Enricher")],  # Stage 3: enrichment
        [NotificationAgent("Notifier")]  # Stage 4: notification
    ]
    results = await orchestrator.run_pipeline(pipeline)
    for r in results:
        print(f"  {r.agent_name}: {r.status.value} ({r.duration:.2f}s)")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run example
    asyncio.run(main())