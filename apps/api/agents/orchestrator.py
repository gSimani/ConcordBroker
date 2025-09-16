"""
Master Orchestrator for Autonomous Agent System
Manages and coordinates all AI agents for 100% autonomous operation
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

from .base_agent import BaseAgent, AgentStatus, AgentPriority
from .semantic_search_agent import SemanticSearchAgent
from .entity_extraction_agent import EntityExtractionAgent
from .content_generation_agent import ContentGenerationAgent
from .document_processing_agent import DocumentProcessingAgent

class WorkflowType(Enum):
    """Predefined workflow types"""
    PROPERTY_ONBOARDING = "property_onboarding"
    DOCUMENT_ANALYSIS = "document_analysis"
    CONTENT_CREATION = "content_creation"
    MARKET_INTELLIGENCE = "market_intelligence"
    LEAD_PROCESSING = "lead_processing"
    AUTOMATED_VALUATION = "automated_valuation"

class Orchestrator:
    """Master orchestrator for autonomous agent system"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflows: Dict[str, Dict] = {}
        self.task_queue = asyncio.Queue()
        self.logger = logging.getLogger("Orchestrator")
        self.is_running = False
        self.metrics = {
            "total_tasks_processed": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "average_workflow_time": 0.0,
            "start_time": datetime.now()
        }
        
        # Initialize all agents
        self._initialize_agents()
        
        # Define automated workflows
        self._define_workflows()
        
        # Schedule automated tasks
        self.scheduled_tasks = []
        
    def _initialize_agents(self):
        """Initialize all AI agents"""
        
        self.logger.info("Initializing autonomous agents...")
        
        # Create agent instances
        self.agents["semantic_search"] = SemanticSearchAgent()
        self.agents["entity_extraction"] = EntityExtractionAgent()
        self.agents["content_generation"] = ContentGenerationAgent()
        self.agents["document_processing"] = DocumentProcessingAgent()
        
        # Set up agent dependencies
        self.agents["content_generation"].set_dependencies(["entity_extraction"])
        
        self.logger.info(f"Initialized {len(self.agents)} agents")
    
    def _define_workflows(self):
        """Define automated workflows"""
        
        self.workflows = {
            WorkflowType.PROPERTY_ONBOARDING: {
                "name": "Property Onboarding",
                "description": "Automatically process new property listings",
                "steps": [
                    {
                        "agent": "document_processing",
                        "action": "process_documents",
                        "input_mapping": {"documents": "property_documents"}
                    },
                    {
                        "agent": "entity_extraction",
                        "action": "extract_entities",
                        "input_mapping": {"text": "extracted_text"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_listing",
                        "input_mapping": {"property_data": "extracted_entities"}
                    },
                    {
                        "agent": "semantic_search",
                        "action": "index_property",
                        "input_mapping": {"properties": "generated_listing"}
                    }
                ]
            },
            
            WorkflowType.DOCUMENT_ANALYSIS: {
                "name": "Document Analysis",
                "description": "Analyze property documents and extract insights",
                "steps": [
                    {
                        "agent": "document_processing",
                        "action": "process_document",
                        "input_mapping": {"document": "input_document"}
                    },
                    {
                        "agent": "entity_extraction",
                        "action": "extract_all",
                        "input_mapping": {"text": "extracted_text"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_summary",
                        "input_mapping": {"data": "entities"}
                    }
                ]
            },
            
            WorkflowType.CONTENT_CREATION: {
                "name": "Content Creation",
                "description": "Generate all marketing content for a property",
                "steps": [
                    {
                        "agent": "content_generation",
                        "action": "generate_listing",
                        "input_mapping": {"property_data": "property"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_social_media",
                        "input_mapping": {"property_data": "property", "platforms": "social_platforms"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_email",
                        "input_mapping": {"property_data": "property", "recipient": "target_audience"}
                    }
                ]
            },
            
            WorkflowType.MARKET_INTELLIGENCE: {
                "name": "Market Intelligence",
                "description": "Gather and analyze market intelligence",
                "steps": [
                    {
                        "agent": "semantic_search",
                        "action": "search_similar",
                        "input_mapping": {"property": "target_property"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_market_report",
                        "input_mapping": {"market_data": "similar_properties"}
                    }
                ]
            },
            
            WorkflowType.LEAD_PROCESSING: {
                "name": "Lead Processing",
                "description": "Process and qualify incoming leads",
                "steps": [
                    {
                        "agent": "entity_extraction",
                        "action": "extract_contact",
                        "input_mapping": {"text": "lead_message"}
                    },
                    {
                        "agent": "semantic_search",
                        "action": "match_properties",
                        "input_mapping": {"query": "lead_requirements"}
                    },
                    {
                        "agent": "content_generation",
                        "action": "generate_response",
                        "input_mapping": {"lead": "lead_data", "matches": "matched_properties"}
                    }
                ]
            }
        }
    
    async def start(self):
        """Start the orchestrator"""
        
        if self.is_running:
            self.logger.warning("Orchestrator already running")
            return
        
        self.is_running = True
        self.logger.info("Starting autonomous orchestrator...")
        
        # Start agent processing loops
        agent_tasks = []
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(agent.process_queue())
            agent_tasks.append(task)
            self.logger.info(f"Started processing loop for {agent_id}")
        
        # Start main orchestration loop
        orchestration_task = asyncio.create_task(self._orchestration_loop())
        
        # Start scheduled tasks
        schedule_task = asyncio.create_task(self._scheduled_tasks_loop())
        
        # Start monitoring
        monitor_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Orchestrator fully operational")
        
        # Keep running
        await asyncio.gather(
            orchestration_task,
            schedule_task,
            monitor_task,
            *agent_tasks
        )
    
    async def _orchestration_loop(self):
        """Main orchestration loop"""
        
        while self.is_running:
            try:
                # Get next task from queue
                task = await self.task_queue.get()
                
                self.logger.info(f"Processing task: {task.get('task_id', 'unknown')}")
                
                # Determine workflow
                workflow_type = task.get("workflow_type")
                if workflow_type:
                    await self._execute_workflow(workflow_type, task.get("input_data", {}))
                else:
                    # Route to appropriate agent
                    await self._route_task(task)
                
                self.metrics["total_tasks_processed"] += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Orchestration error: {str(e)}")
                await asyncio.sleep(1)
    
    async def _execute_workflow(self, workflow_type: WorkflowType, input_data: Dict[str, Any]):
        """Execute a predefined workflow"""
        
        workflow = self.workflows.get(workflow_type)
        if not workflow:
            self.logger.error(f"Unknown workflow: {workflow_type}")
            return
        
        self.logger.info(f"Executing workflow: {workflow['name']}")
        start_time = datetime.now()
        
        try:
            # Initialize workflow context
            context = {
                "workflow_id": f"{workflow_type.value}_{datetime.now().timestamp()}",
                "input": input_data,
                "results": {},
                "status": "running"
            }
            
            # Execute each step
            for i, step in enumerate(workflow["steps"]):
                self.logger.info(f"Executing step {i+1}: {step['agent']}.{step['action']}")
                
                # Prepare input for step
                step_input = self._prepare_step_input(step, context)
                
                # Execute agent action
                agent = self.agents.get(step["agent"])
                if not agent:
                    raise Exception(f"Agent {step['agent']} not found")
                
                result = await agent.execute(step_input)
                
                # Store result in context
                context["results"][f"step_{i+1}"] = result
                
                # Update context with output
                if result.get("status") == "success":
                    context[f"step_{i+1}_output"] = result.get("result", {})
                else:
                    raise Exception(f"Step {i+1} failed: {result.get('error')}")
            
            # Workflow completed successfully
            context["status"] = "completed"
            self.metrics["successful_workflows"] += 1
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_workflow_metrics(execution_time)
            
            self.logger.info(f"Workflow completed in {execution_time:.2f} seconds")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Workflow failed: {str(e)}")
            self.metrics["failed_workflows"] += 1
            context["status"] = "failed"
            context["error"] = str(e)
            return context
    
    def _prepare_step_input(self, step: Dict, context: Dict) -> Dict[str, Any]:
        """Prepare input for workflow step"""
        
        step_input = {"action": step["action"]}
        
        # Map inputs from context
        for target_key, source_key in step.get("input_mapping", {}).items():
            # Check if source is from previous step output
            if source_key.startswith("step_"):
                step_num = int(source_key.split("_")[1])
                if f"step_{step_num}_output" in context:
                    step_input[target_key] = context[f"step_{step_num}_output"]
            # Check if source is from input data
            elif source_key in context.get("input", {}):
                step_input[target_key] = context["input"][source_key]
            # Check if source is from context
            elif source_key in context:
                step_input[target_key] = context[source_key]
        
        return step_input
    
    async def _route_task(self, task: Dict[str, Any]):
        """Route task to appropriate agent"""
        
        # Determine best agent based on task type
        task_type = task.get("type", "")
        
        if "search" in task_type:
            agent = self.agents["semantic_search"]
        elif "extract" in task_type or "entity" in task_type:
            agent = self.agents["entity_extraction"]
        elif "generate" in task_type or "content" in task_type:
            agent = self.agents["content_generation"]
        elif "document" in task_type or "ocr" in task_type:
            agent = self.agents["document_processing"]
        else:
            # Default to content generation
            agent = self.agents["content_generation"]
        
        # Add task to agent's queue
        priority = task.get("priority", AgentPriority.MEDIUM)
        await agent.add_task(task, priority)
    
    async def _scheduled_tasks_loop(self):
        """Execute scheduled tasks"""
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Daily tasks
                if current_time.hour == 9 and current_time.minute == 0:
                    await self._run_daily_tasks()
                
                # Hourly tasks
                if current_time.minute == 0:
                    await self._run_hourly_tasks()
                
                # Wait a minute before checking again
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduled task error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _run_daily_tasks(self):
        """Run daily automated tasks"""
        
        self.logger.info("Running daily tasks...")
        
        # Generate market reports
        await self.add_task({
            "workflow_type": WorkflowType.MARKET_INTELLIGENCE,
            "input_data": {
                "location": "Broward County",
                "property_type": "residential"
            },
            "priority": AgentPriority.HIGH
        })
        
        # Process pending documents
        await self.add_task({
            "workflow_type": WorkflowType.DOCUMENT_ANALYSIS,
            "input_data": {
                "batch_process": True
            },
            "priority": AgentPriority.MEDIUM
        })
    
    async def _run_hourly_tasks(self):
        """Run hourly automated tasks"""
        
        self.logger.info("Running hourly tasks...")
        
        # Check for new properties to onboard
        # In production, this would check a database or API
        new_properties = await self._check_new_properties()
        
        for property_data in new_properties:
            await self.add_task({
                "workflow_type": WorkflowType.PROPERTY_ONBOARDING,
                "input_data": property_data,
                "priority": AgentPriority.HIGH
            })
    
    async def _check_new_properties(self) -> List[Dict]:
        """Check for new properties to process"""
        
        # In production, would query database
        # For now, return empty list
        return []
    
    async def _monitoring_loop(self):
        """Monitor system health and performance"""
        
        while self.is_running:
            try:
                # Check agent health
                for agent_id, agent in self.agents.items():
                    if not await agent.health_check():
                        self.logger.warning(f"Agent {agent_id} health check failed")
                        # Attempt to restart agent
                        await self._restart_agent(agent_id)
                
                # Log metrics
                self._log_metrics()
                
                # Clean up old cache
                for agent in self.agents.values():
                    if len(agent.results_cache) > 1000:
                        agent.clear_cache()
                
                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                await asyncio.sleep(300)
    
    async def _restart_agent(self, agent_id: str):
        """Restart a failed agent"""
        
        self.logger.info(f"Attempting to restart agent {agent_id}")
        
        # Re-initialize the agent
        if agent_id == "semantic_search":
            self.agents[agent_id] = SemanticSearchAgent()
        elif agent_id == "entity_extraction":
            self.agents[agent_id] = EntityExtractionAgent()
        elif agent_id == "content_generation":
            self.agents[agent_id] = ContentGenerationAgent()
        elif agent_id == "document_processing":
            self.agents[agent_id] = DocumentProcessingAgent()
        
        # Restart processing loop
        asyncio.create_task(self.agents[agent_id].process_queue())
        
        self.logger.info(f"Agent {agent_id} restarted")
    
    def _update_workflow_metrics(self, execution_time: float):
        """Update workflow metrics"""
        
        total = self.metrics["successful_workflows"]
        if total > 0:
            current_avg = self.metrics["average_workflow_time"]
            self.metrics["average_workflow_time"] = ((current_avg * (total - 1)) + execution_time) / total
    
    def _log_metrics(self):
        """Log system metrics"""
        
        uptime = (datetime.now() - self.metrics["start_time"]).total_seconds() / 3600
        
        self.logger.info(f"""
        === System Metrics ===
        Uptime: {uptime:.2f} hours
        Total Tasks: {self.metrics['total_tasks_processed']}
        Successful Workflows: {self.metrics['successful_workflows']}
        Failed Workflows: {self.metrics['failed_workflows']}
        Average Workflow Time: {self.metrics['average_workflow_time']:.2f}s
        Queue Size: {self.task_queue.qsize()}
        """)
        
        # Log agent metrics
        for agent_id, agent in self.agents.items():
            status = agent.get_status()
            self.logger.info(f"""
            Agent: {agent_id}
            Status: {status['status']}
            Tasks Processed: {status['metrics']['tasks_processed']}
            Success Rate: {status['metrics']['success_rate']:.2%}
            Queue Size: {status['queue_size']}
            """)
    
    async def add_task(self, task: Dict[str, Any]):
        """Add task to orchestrator queue"""
        
        # Add task ID if not present
        if "task_id" not in task:
            task["task_id"] = f"task_{datetime.now().timestamp()}"
        
        # Add timestamp
        task["created_at"] = datetime.now().isoformat()
        
        await self.task_queue.put(task)
        self.logger.info(f"Task {task['task_id']} added to queue")
    
    async def execute_workflow(self, workflow_type: WorkflowType, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow immediately"""
        
        return await self._execute_workflow(workflow_type, input_data)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID"""
        return self.agents.get(agent_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        
        return {
            "is_running": self.is_running,
            "agents": list(self.agents.keys()),
            "workflows": list(self.workflows.keys()),
            "queue_size": self.task_queue.qsize(),
            "metrics": self.metrics
        }
    
    async def stop(self):
        """Stop the orchestrator"""
        
        self.logger.info("Stopping orchestrator...")
        self.is_running = False
        
        # Cancel all agent tasks
        for agent in self.agents.values():
            agent.status = AgentStatus.IDLE
        
        self.logger.info("Orchestrator stopped")

# Create global orchestrator instance
orchestrator = Orchestrator()

async def start_autonomous_system():
    """Start the autonomous agent system"""
    await orchestrator.start()

async def process_property(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process a property through the autonomous system"""
    
    return await orchestrator.execute_workflow(
        WorkflowType.PROPERTY_ONBOARDING,
        property_data
    )

async def analyze_document(document: Any) -> Dict[str, Any]:
    """Analyze a document autonomously"""
    
    return await orchestrator.execute_workflow(
        WorkflowType.DOCUMENT_ANALYSIS,
        {"input_document": document}
    )

async def generate_marketing_content(property_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate all marketing content for a property"""
    
    return await orchestrator.execute_workflow(
        WorkflowType.CONTENT_CREATION,
        {
            "property": property_data,
            "social_platforms": ["instagram", "facebook", "linkedin"],
            "target_audience": "potential buyers"
        }
    )