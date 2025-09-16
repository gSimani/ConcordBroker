"""
Unified Orchestrator for ConcordBroker Agent System
Following OpenAI's Agent Design Principles
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentPriority(Enum):
    """Priority levels for agent task execution"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"

class UnifiedOrchestrator:
    """
    Single source of truth for all agent coordination in ConcordBroker.
    Implements Manager Pattern from OpenAI guide.
    """
    
    def __init__(self):
        self.agents = {}
        self.task_queue = asyncio.PriorityQueue()
        self.active_tasks = {}
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'escalated_tasks': 0,
            'avg_execution_time': 0
        }
        self.guardrails = self._setup_guardrails()
        self._register_agents()
        
    def _register_agents(self):
        """Register all active agents in the system"""
        logger.info("Registering agents...")
        
        # Core agents following single-agent pattern
        self.agents['data_pipeline'] = {
            'class': 'DataPipelineAgent',
            'priority': AgentPriority.HIGH,
            'tools': ['florida_collector', 'tax_deed_scraper', 'sunbiz_sync'],
            'max_concurrent': 3
        }
        
        self.agents['property_analysis'] = {
            'class': 'PropertyAnalysisAgent',
            'priority': AgentPriority.NORMAL,
            'tools': ['market_analyzer', 'roi_calculator', 'risk_assessor'],
            'max_concurrent': 5
        }
        
        self.agents['ai_assistant'] = {
            'class': 'AIAssistantAgent',
            'priority': AgentPriority.HIGH,
            'tools': ['nlp_parser', 'semantic_search', 'response_generator'],
            'max_concurrent': 10
        }
        
        self.agents['monitoring'] = {
            'class': 'MonitoringAgent',
            'priority': AgentPriority.CRITICAL,
            'tools': ['health_checker', 'alert_manager', 'metrics_collector'],
            'max_concurrent': 1
        }
        
        logger.info(f"Registered {len(self.agents)} agents")
    
    def _setup_guardrails(self) -> Dict:
        """Setup system-wide guardrails"""
        return {
            'max_concurrent_tasks': 20,
            'task_timeout': 300,  # 5 minutes
            'max_retries': 3,
            'confidence_threshold': 0.7,
            'escalation_threshold': 0.5,
            'rate_limits': {
                'api_calls_per_minute': 60,
                'db_queries_per_second': 10
            }
        }
    
    async def submit_task(self, 
                          agent_name: str, 
                          task: Dict[str, Any],
                          priority: Optional[AgentPriority] = None) -> str:
        """
        Submit a task to the orchestrator for execution
        
        Args:
            agent_name: Name of the agent to execute the task
            task: Task configuration and parameters
            priority: Optional priority override
            
        Returns:
            task_id: Unique identifier for tracking
        """
        # Validate agent exists
        if agent_name not in self.agents:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        # Generate task ID
        task_id = f"{agent_name}_{datetime.now().timestamp()}"
        
        # Set priority
        if priority is None:
            priority = self.agents[agent_name]['priority']
        
        # Create task wrapper
        task_wrapper = {
            'id': task_id,
            'agent': agent_name,
            'task': task,
            'status': TaskStatus.PENDING,
            'created_at': datetime.now(),
            'retries': 0
        }
        
        # Check guardrails
        if not await self._check_guardrails(task_wrapper):
            return await self._escalate_to_human(task_wrapper, "Guardrail violation")
        
        # Add to queue
        await self.task_queue.put((priority.value, task_wrapper))
        self.metrics['total_tasks'] += 1
        
        logger.info(f"Task {task_id} submitted for agent {agent_name}")
        return task_id
    
    async def _check_guardrails(self, task_wrapper: Dict) -> bool:
        """Check if task passes all guardrails"""
        # Check concurrent task limit
        if len(self.active_tasks) >= self.guardrails['max_concurrent_tasks']:
            logger.warning("Max concurrent tasks reached")
            return False
        
        # Check agent-specific limits
        agent_name = task_wrapper['agent']
        agent_tasks = [t for t in self.active_tasks.values() 
                      if t['agent'] == agent_name]
        
        if len(agent_tasks) >= self.agents[agent_name]['max_concurrent']:
            logger.warning(f"Max concurrent tasks for {agent_name} reached")
            return False
        
        return True
    
    async def execute(self):
        """Main execution loop"""
        logger.info("Starting orchestrator execution loop")
        
        while True:
            try:
                # Get next task from queue
                priority, task_wrapper = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # Execute task
                asyncio.create_task(self._execute_task(task_wrapper))
                
            except asyncio.TimeoutError:
                # No tasks in queue, perform maintenance
                await self._perform_maintenance()
                
            except Exception as e:
                logger.error(f"Orchestrator error: {e}")
                await asyncio.sleep(1)
    
    async def _execute_task(self, task_wrapper: Dict):
        """Execute a single task with error handling"""
        task_id = task_wrapper['id']
        agent_name = task_wrapper['agent']
        
        logger.info(f"Executing task {task_id}")
        
        # Mark as active
        task_wrapper['status'] = TaskStatus.RUNNING
        self.active_tasks[task_id] = task_wrapper
        
        try:
            # Get agent instance (lazy loading in real implementation)
            agent = await self._get_agent_instance(agent_name)
            
            # Execute with timeout
            result = await asyncio.wait_for(
                agent.execute(task_wrapper['task']),
                timeout=self.guardrails['task_timeout']
            )
            
            # Check confidence
            if result.get('confidence', 1.0) < self.guardrails['confidence_threshold']:
                await self._escalate_to_human(task_wrapper, "Low confidence")
            else:
                # Success
                task_wrapper['status'] = TaskStatus.COMPLETED
                task_wrapper['result'] = result
                self.metrics['completed_tasks'] += 1
                logger.info(f"Task {task_id} completed successfully")
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task_id} timed out")
            await self._handle_task_failure(task_wrapper, "Timeout")
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            await self._handle_task_failure(task_wrapper, str(e))
            
        finally:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _handle_task_failure(self, task_wrapper: Dict, error: str):
        """Handle task failure with retry logic"""
        task_wrapper['retries'] += 1
        
        if task_wrapper['retries'] < self.guardrails['max_retries']:
            # Retry with backoff
            await asyncio.sleep(2 ** task_wrapper['retries'])
            await self.task_queue.put((
                self.agents[task_wrapper['agent']]['priority'].value,
                task_wrapper
            ))
            logger.info(f"Retrying task {task_wrapper['id']} (attempt {task_wrapper['retries']})")
        else:
            # Max retries exceeded
            task_wrapper['status'] = TaskStatus.FAILED
            task_wrapper['error'] = error
            self.metrics['failed_tasks'] += 1
            await self._escalate_to_human(task_wrapper, f"Max retries exceeded: {error}")
    
    async def _escalate_to_human(self, task_wrapper: Dict, reason: str) -> str:
        """Escalate task to human intervention"""
        task_id = task_wrapper['id']
        
        escalation = {
            'task_id': task_id,
            'agent': task_wrapper['agent'],
            'reason': reason,
            'task': task_wrapper['task'],
            'timestamp': datetime.now().isoformat(),
            'status': TaskStatus.ESCALATED
        }
        
        # Log escalation
        logger.warning(f"Task {task_id} escalated: {reason}")
        
        # Store escalation (in real implementation, send to queue/notification)
        with open('escalations.json', 'a') as f:
            json.dump(escalation, f)
            f.write('\n')
        
        self.metrics['escalated_tasks'] += 1
        task_wrapper['status'] = TaskStatus.ESCALATED
        
        return task_id
    
    async def _get_agent_instance(self, agent_name: str):
        """Get or create agent instance (placeholder)"""
        # In real implementation, this would import and instantiate the agent
        # For now, return a mock agent
        class MockAgent:
            async def execute(self, task):
                await asyncio.sleep(0.5)  # Simulate work
                return {
                    'status': 'success',
                    'confidence': 0.85,
                    'result': f"Processed by {agent_name}"
                }
        
        return MockAgent()
    
    async def _perform_maintenance(self):
        """Perform periodic maintenance tasks"""
        # Update metrics
        if self.metrics['completed_tasks'] > 0:
            # Calculate average execution time (simplified)
            self.metrics['avg_execution_time'] = (
                self.metrics['total_tasks'] / self.metrics['completed_tasks']
            )
        
        # Check agent health
        for agent_name in self.agents:
            # In real implementation, perform health checks
            pass
        
        # Clean up old tasks
        # In real implementation, archive completed tasks
        pass
    
    def get_status(self) -> Dict:
        """Get current orchestrator status"""
        return {
            'active_agents': len(self.agents),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': self.task_queue.qsize(),
            'metrics': self.metrics,
            'guardrails': self.guardrails
        }
    
    async def shutdown(self):
        """Gracefully shutdown orchestrator"""
        logger.info("Shutting down orchestrator...")
        
        # Wait for active tasks to complete
        while self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} tasks to complete...")
            await asyncio.sleep(1)
        
        logger.info("Orchestrator shutdown complete")


# Example usage
async def main():
    """Example orchestrator usage"""
    orchestrator = UnifiedOrchestrator()
    
    # Submit some tasks
    task_id1 = await orchestrator.submit_task(
        'property_analysis',
        {'property_id': '123456', 'analysis_type': 'full'}
    )
    
    task_id2 = await orchestrator.submit_task(
        'ai_assistant',
        {'query': 'Find tax deed properties under $50,000'},
        priority=AgentPriority.HIGH
    )
    
    # Run orchestrator
    try:
        await orchestrator.execute()
    except KeyboardInterrupt:
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())