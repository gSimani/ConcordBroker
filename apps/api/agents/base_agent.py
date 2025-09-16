"""
Base Agent Class for Autonomous Property Intelligence System
Provides foundation for all specialized agents
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"

class AgentPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class BaseAgent(ABC):
    """Abstract base class for all intelligent agents"""
    
    def __init__(self, agent_id: str, name: str, description: str):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.logger = logging.getLogger(f"Agent.{agent_id}")
        self.task_queue = asyncio.Queue()
        self.results_cache = {}
        self.dependencies = []
        self.metrics = {
            "tasks_processed": 0,
            "success_rate": 0.0,
            "avg_processing_time": 0.0,
            "last_active": None
        }
        
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input data and return results"""
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data before processing"""
        pass
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task with error handling and metrics"""
        start_time = datetime.now()
        self.status = AgentStatus.PROCESSING
        
        try:
            # Validate input
            if not await self.validate_input(task):
                raise ValueError(f"Invalid input for agent {self.agent_id}")
            
            # Process task
            result = await self.process(task)
            
            # Update metrics
            self.metrics["tasks_processed"] += 1
            processing_time = (datetime.now() - start_time).total_seconds()
            self.update_metrics(processing_time, success=True)
            
            # Cache result
            task_id = task.get("task_id", str(datetime.now().timestamp()))
            self.results_cache[task_id] = result
            
            self.status = AgentStatus.COMPLETED
            
            return {
                "agent_id": self.agent_id,
                "status": "success",
                "result": result,
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in agent {self.agent_id}: {str(e)}")
            self.status = AgentStatus.FAILED
            self.update_metrics(0, success=False)
            
            return {
                "agent_id": self.agent_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def update_metrics(self, processing_time: float, success: bool):
        """Update agent performance metrics"""
        total = self.metrics["tasks_processed"]
        if total > 0:
            current_success = self.metrics["success_rate"]
            if success:
                self.metrics["success_rate"] = ((current_success * (total - 1)) + 1) / total
            else:
                self.metrics["success_rate"] = (current_success * (total - 1)) / total
            
            if processing_time > 0:
                current_avg = self.metrics["avg_processing_time"]
                self.metrics["avg_processing_time"] = ((current_avg * (total - 1)) + processing_time) / total
        
        self.metrics["last_active"] = datetime.now().isoformat()
    
    async def add_task(self, task: Dict[str, Any], priority: AgentPriority = AgentPriority.MEDIUM):
        """Add task to queue with priority"""
        await self.task_queue.put((priority.value, task))
        self.logger.info(f"Task added to {self.agent_id} queue with priority {priority.name}")
    
    async def process_queue(self):
        """Process tasks from queue continuously"""
        while True:
            try:
                # Get highest priority task
                priority, task = await self.task_queue.get()
                self.logger.info(f"Processing task with priority {priority}")
                
                # Execute task
                result = await self.execute(task)
                
                # Notify completion
                if "callback" in task:
                    await task["callback"](result)
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(1)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status and metrics"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "queue_size": self.task_queue.qsize(),
            "metrics": self.metrics,
            "cache_size": len(self.results_cache)
        }
    
    def clear_cache(self):
        """Clear results cache"""
        self.results_cache.clear()
        self.logger.info(f"Cache cleared for agent {self.agent_id}")
    
    async def health_check(self) -> bool:
        """Check if agent is healthy and responsive"""
        try:
            test_input = {"test": True, "timestamp": datetime.now().isoformat()}
            if await self.validate_input(test_input):
                return True
        except:
            pass
        return False
    
    def set_dependencies(self, dependencies: List[str]):
        """Set agent dependencies for chain processing"""
        self.dependencies = dependencies
        
    async def wait_for_dependencies(self, orchestrator):
        """Wait for dependent agents to complete"""
        for dep_id in self.dependencies:
            dep_agent = orchestrator.get_agent(dep_id)
            if dep_agent:
                while dep_agent.status == AgentStatus.PROCESSING:
                    await asyncio.sleep(0.5)
                if dep_agent.status == AgentStatus.FAILED:
                    raise Exception(f"Dependency {dep_id} failed")