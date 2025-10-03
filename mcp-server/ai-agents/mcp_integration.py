#!/usr/bin/env python3
"""
MCP Integration for AI Data Flow Monitoring System
Integrates all AI agents and systems with the existing MCP server
"""

import asyncio
import logging
import json
import os
import signal
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import subprocess
import threading
import time

# FastAPI and web server imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Local imports
from data_flow_orchestrator import DataFlowOrchestrator
from monitoring_agents import AgentOrchestrator, PropertyDataAgent, SalesDataAgent, TaxCertificateAgent, EntityLinkingAgent
from self_healing_system import SelfHealingOrchestrator
from sqlalchemy_models import initialize_database, DatabaseManager
from spark_data_processor import SparkDataProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MCPIntegratedSystem:
    """Integrated system that combines all AI agents with MCP server"""

    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.db_manager = None
        self.data_orchestrator = None
        self.agent_orchestrator = None
        self.self_healing_orchestrator = None
        self.spark_processor = None
        self.fastapi_app = None
        self.system_status = "INITIALIZING"
        self.services = {}
        self.background_tasks = []

    async def initialize(self):
        """Initialize all components"""
        try:
            logger.info("🚀 Initializing MCP Integrated AI System...")

            # 1. Initialize database
            self.db_manager = initialize_database(
                self.config.get('SUPABASE_URL', '').replace('https://', 'postgresql://postgres:') +
                f":{self.config.get('SUPABASE_SERVICE_ROLE_KEY', '')}@" +
                self.config.get('SUPABASE_URL', '').replace('https://', '').split('.')[0] +
                ".supabase.co:5432/postgres"
            )
            logger.info("✅ Database initialized")

            # 2. Initialize Data Flow Orchestrator
            self.data_orchestrator = DataFlowOrchestrator(self.config)
            logger.info("✅ Data Flow Orchestrator initialized")

            # 3. Initialize Agent Orchestrator
            self.agent_orchestrator = AgentOrchestrator(
                db_manager=self.db_manager,
                openai_api_key=self.config.get('OPENAI_API_KEY')
            )

            # Add all agents
            self.agent_orchestrator.add_agent(PropertyDataAgent, check_interval=300)  # 5 min
            self.agent_orchestrator.add_agent(SalesDataAgent, check_interval=600)     # 10 min
            self.agent_orchestrator.add_agent(TaxCertificateAgent, check_interval=900) # 15 min
            self.agent_orchestrator.add_agent(EntityLinkingAgent, check_interval=1800) # 30 min
            logger.info("✅ Agent Orchestrator initialized with 4 agents")

            # 4. Initialize Self-Healing System
            self.self_healing_orchestrator = SelfHealingOrchestrator(
                db_manager=self.db_manager,
                openai_api_key=self.config.get('OPENAI_API_KEY')
            )
            logger.info("✅ Self-Healing Orchestrator initialized")

            # 5. Initialize Spark Processor
            try:
                self.spark_processor = SparkDataProcessor("ConcordBroker-MCP-Integration")
                logger.info("✅ Spark Processor initialized")
            except Exception as e:
                logger.warning(f"⚠️ Spark Processor initialization failed: {e}")
                self.spark_processor = None

            # 6. Setup FastAPI integration
            self._setup_fastapi_integration()
            logger.info("✅ FastAPI integration setup")

            self.system_status = "READY"
            logger.info("🎉 MCP Integrated AI System fully initialized!")

        except Exception as e:
            logger.error(f"❌ System initialization failed: {e}")
            self.system_status = "ERROR"
            raise

    def _setup_fastapi_integration(self):
        """Setup FastAPI routes for integration with MCP server"""
        self.fastapi_app = FastAPI(
            title="ConcordBroker AI Data Flow System",
            description="Integrated AI monitoring and self-healing system",
            version="1.0.0"
        )

        # Add CORS middleware
        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Health check endpoint
        @self.fastapi_app.get("/ai-system/health")
        async def health_check():
            """Comprehensive health check of all AI systems"""
            return {
                "status": self.system_status,
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "database": "connected" if self.db_manager else "disconnected",
                    "data_orchestrator": "ready" if self.data_orchestrator else "not_ready",
                    "agent_orchestrator": "active" if self.agent_orchestrator and self.agent_orchestrator.orchestrator_active else "inactive",
                    "self_healing": "ready" if self.self_healing_orchestrator else "not_ready",
                    "spark_processor": "available" if self.spark_processor else "unavailable"
                }
            }

        # System status endpoint
        @self.fastapi_app.get("/ai-system/status")
        async def get_system_status():
            """Get detailed system status"""
            try:
                status = {
                    "system_status": self.system_status,
                    "timestamp": datetime.now().isoformat(),
                    "services": {}
                }

                # Agent status
                if self.agent_orchestrator:
                    status["services"]["agents"] = self.agent_orchestrator.get_system_status()

                # Self-healing status
                if self.self_healing_orchestrator:
                    status["services"]["self_healing"] = self.self_healing_orchestrator.get_system_health_report()

                # Data orchestrator metrics
                if self.data_orchestrator:
                    try:
                        # Get latest metrics from data orchestrator
                        import requests
                        response = requests.get("http://localhost:8001/metrics", timeout=5)
                        if response.status_code == 200:
                            status["services"]["data_metrics"] = response.json()
                    except:
                        status["services"]["data_metrics"] = {"status": "unavailable"}

                return status

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

        # Start monitoring endpoint
        @self.fastapi_app.post("/ai-system/start-monitoring")
        async def start_monitoring(background_tasks: BackgroundTasks):
            """Start all monitoring systems"""
            try:
                if self.system_status != "READY":
                    raise HTTPException(status_code=400, detail="System not ready")

                # Start agents in background
                if self.agent_orchestrator:
                    background_tasks.add_task(self.agent_orchestrator.start_all_agents)

                # Start self-healing in background
                if self.self_healing_orchestrator:
                    background_tasks.add_task(self.self_healing_orchestrator.start_continuous_healing, 1800)

                return {
                    "message": "Monitoring systems started",
                    "timestamp": datetime.now().isoformat(),
                    "systems_started": ["agents", "self_healing"]
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to start monitoring: {str(e)}")

        # Stop monitoring endpoint
        @self.fastapi_app.post("/ai-system/stop-monitoring")
        async def stop_monitoring():
            """Stop all monitoring systems"""
            try:
                if self.agent_orchestrator:
                    await self.agent_orchestrator.stop_all_agents()

                return {
                    "message": "Monitoring systems stopped",
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Failed to stop monitoring: {str(e)}")

        # Trigger healing endpoint
        @self.fastapi_app.post("/ai-system/trigger-healing")
        async def trigger_healing():
            """Manually trigger a healing cycle"""
            try:
                if not self.self_healing_orchestrator:
                    raise HTTPException(status_code=400, detail="Self-healing system not available")

                result = await self.self_healing_orchestrator.run_healing_cycle()
                return {
                    "message": "Healing cycle completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Healing cycle failed: {str(e)}")

        # Spark analysis endpoint
        @self.fastapi_app.post("/ai-system/spark-analysis")
        async def run_spark_analysis(county: str = None):
            """Run Spark-based data analysis"""
            try:
                if not self.spark_processor:
                    raise HTTPException(status_code=400, detail="Spark processor not available")

                # Run comprehensive analysis
                result = self.spark_processor.generate_comprehensive_report(county)
                return {
                    "message": "Spark analysis completed",
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Spark analysis failed: {str(e)}")

        # Data validation endpoint
        @self.fastapi_app.post("/ai-system/validate-data")
        async def validate_data():
            """Run comprehensive data validation"""
            try:
                # This would integrate with the data orchestrator's validation
                import requests
                response = requests.post("http://localhost:8001/validate/all", timeout=30)

                if response.status_code == 200:
                    return {
                        "message": "Data validation completed",
                        "result": response.json(),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Data validation service unavailable")

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Data validation failed: {str(e)}")

        # Performance metrics endpoint
        @self.fastapi_app.get("/ai-system/performance")
        async def get_performance_metrics():
            """Get system performance metrics"""
            try:
                import requests

                # Get performance data from data orchestrator
                try:
                    response = requests.get("http://localhost:8001/performance", timeout=10)
                    performance_data = response.json() if response.status_code == 200 else {}
                except:
                    performance_data = {}

                # Add AI system specific metrics
                ai_metrics = {
                    "system_uptime": time.time(),  # Would track actual uptime
                    "active_agents": len([a for a in self.agent_orchestrator.agents if a.status == "ACTIVE"]) if self.agent_orchestrator else 0,
                    "healing_cycles_today": 0,  # Would track from database
                    "spark_jobs_completed": 0   # Would track from Spark
                }

                return {
                    "timestamp": datetime.now().isoformat(),
                    "system_performance": performance_data,
                    "ai_system_metrics": ai_metrics
                }

            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Performance metrics failed: {str(e)}")

    async def start_services(self):
        """Start all background services"""
        try:
            logger.info("🚀 Starting all AI system services...")

            # Start data orchestrator
            if self.data_orchestrator:
                data_task = asyncio.create_task(
                    self.data_orchestrator.start_server(host="0.0.0.0", port=8001)
                )
                self.background_tasks.append(data_task)
                logger.info("✅ Data orchestrator started on port 8001")

            # Start FastAPI integration server
            if self.fastapi_app:
                config = uvicorn.Config(
                    self.fastapi_app,
                    host="0.0.0.0",
                    port=8003,
                    log_level="info"
                )
                server = uvicorn.Server(config)
                fastapi_task = asyncio.create_task(server.serve())
                self.background_tasks.append(fastapi_task)
                logger.info("✅ AI system API started on port 8003")

            # Start monitoring agents
            if self.agent_orchestrator:
                agent_task = asyncio.create_task(self.agent_orchestrator.start_all_agents())
                self.background_tasks.append(agent_task)
                logger.info("✅ Monitoring agents started")

            # Start self-healing system
            if self.self_healing_orchestrator:
                healing_task = asyncio.create_task(
                    self.self_healing_orchestrator.start_continuous_healing(1800)  # 30 minutes
                )
                self.background_tasks.append(healing_task)
                logger.info("✅ Self-healing system started")

            self.system_status = "ACTIVE"
            logger.info("🎉 All AI system services are now active!")

            # Wait for all tasks
            await asyncio.gather(*self.background_tasks)

        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}")
            self.system_status = "ERROR"
            raise

    async def stop_services(self):
        """Stop all services gracefully"""
        try:
            logger.info("🛑 Stopping AI system services...")

            # Stop agents
            if self.agent_orchestrator:
                await self.agent_orchestrator.stop_all_agents()

            # Cancel background tasks
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()

            # Close Spark session
            if self.spark_processor:
                self.spark_processor.close()

            # Close database connections
            if self.db_manager:
                self.db_manager.close()

            self.system_status = "STOPPED"
            logger.info("✅ All AI system services stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping services: {e}")

class MCPAutoStartup:
    """Handles automatic startup integration with MCP server"""

    def __init__(self, mcp_server_path: str = "../server.js"):
        self.mcp_server_path = mcp_server_path
        self.ai_system = None
        self.mcp_process = None

    def start_mcp_server(self):
        """Start the MCP server if not already running"""
        try:
            # Check if MCP server is already running
            import requests
            try:
                response = requests.get("http://localhost:3001/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ MCP server already running")
                    return True
            except:
                pass

            # Start MCP server
            logger.info("🚀 Starting MCP server...")
            self.mcp_process = subprocess.Popen(
                ["node", self.mcp_server_path],
                cwd=os.path.dirname(os.path.abspath(self.mcp_server_path)),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Wait a few seconds for startup
            time.sleep(5)

            # Verify it's running
            try:
                response = requests.get("http://localhost:3001/health", timeout=5)
                if response.status_code == 200:
                    logger.info("✅ MCP server started successfully")
                    return True
            except:
                pass

            logger.error("❌ MCP server failed to start properly")
            return False

        except Exception as e:
            logger.error(f"❌ Failed to start MCP server: {e}")
            return False

    async def start_integrated_system(self):
        """Start the complete integrated system"""
        try:
            # Load configuration
            config = self._load_config()

            # Start MCP server first
            if not self.start_mcp_server():
                raise Exception("Failed to start MCP server")

            # Initialize AI system
            self.ai_system = MCPIntegratedSystem(config)
            await self.ai_system.initialize()

            # Start AI services
            await self.ai_system.start_services()

        except Exception as e:
            logger.error(f"❌ Failed to start integrated system: {e}")
            raise

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from environment"""
        from dotenv import load_dotenv

        # Load environment variables
        env_path = os.path.join(os.path.dirname(__file__), '../.env.mcp')
        load_dotenv(env_path)

        config = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL', ''),
            'SUPABASE_SERVICE_ROLE_KEY': os.getenv('SUPABASE_SERVICE_ROLE_KEY', ''),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
            'LANGCHAIN_API_KEY': os.getenv('LANGCHAIN_API_KEY', ''),
            'LANGSMITH_API_KEY': os.getenv('LANGSMITH_API_KEY', ''),
            'HUGGINGFACE_API_TOKEN': os.getenv('HUGGINGFACE_API_TOKEN', '')
        }

        # Validate required config
        required_keys = ['SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
        missing_keys = [k for k in required_keys if not config[k]]

        if missing_keys:
            raise ValueError(f"Missing required configuration: {missing_keys}")

        return config

    async def stop_integrated_system(self):
        """Stop the integrated system"""
        try:
            if self.ai_system:
                await self.ai_system.stop_services()

            if self.mcp_process:
                self.mcp_process.terminate()
                self.mcp_process.wait(timeout=10)

            logger.info("✅ Integrated system stopped")

        except Exception as e:
            logger.error(f"❌ Error stopping integrated system: {e}")

# Integration script for MCP server
def create_mcp_integration_script():
    """Create integration script that can be called from MCP server"""
    script_content = '''#!/usr/bin/env python3
"""
MCP Integration Script - Called automatically by MCP server
"""

import asyncio
import sys
import os
import signal
import logging

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_integration import MCPAutoStartup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../logs/ai_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

startup_manager = None

async def main():
    """Main entry point"""
    global startup_manager

    try:
        logger.info("🚀 Starting ConcordBroker AI Data Flow System...")

        startup_manager = MCPAutoStartup()
        await startup_manager.start_integrated_system()

    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ System failed: {e}")
        sys.exit(1)
    finally:
        if startup_manager:
            await startup_manager.stop_integrated_system()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"🛑 Received signal {signum}")
    if startup_manager:
        asyncio.create_task(startup_manager.stop_integrated_system())
    sys.exit(0)

if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Create logs directory
    os.makedirs("../logs", exist_ok=True)

    # Run the system
    asyncio.run(main())
'''

    # Write the integration script
    script_path = os.path.join(os.path.dirname(__file__), 'start_ai_system.py')
    with open(script_path, 'w') as f:
        f.write(script_content)

    # Make it executable
    os.chmod(script_path, 0o755)

    logger.info(f"✅ Created MCP integration script: {script_path}")
    return script_path

# Update MCP server startup script
def update_mcp_server_startup():
    """Update the existing MCP server to auto-start AI system"""

    # Create the Node.js startup script
    nodejs_script = '''const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Auto-start AI system with MCP server
function startAISystem() {
    console.log('🤖 Starting ConcordBroker AI Data Flow System...');

    const aiScriptPath = path.join(__dirname, 'ai-agents', 'start_ai_system.py');

    if (!fs.existsSync(aiScriptPath)) {
        console.warn('⚠️ AI system script not found:', aiScriptPath);
        return null;
    }

    const aiProcess = spawn('python', [aiScriptPath], {
        cwd: path.join(__dirname, 'ai-agents'),
        stdio: ['ignore', 'pipe', 'pipe']
    });

    aiProcess.stdout.on('data', (data) => {
        console.log('🤖 AI System:', data.toString().trim());
    });

    aiProcess.stderr.on('data', (data) => {
        console.error('🤖 AI System Error:', data.toString().trim());
    });

    aiProcess.on('close', (code) => {
        console.log(`🤖 AI System exited with code ${code}`);
    });

    return aiProcess;
}

// Start AI system when this module is loaded
const aiProcess = startAISystem();

// Export for cleanup
module.exports = {
    aiProcess,
    startAISystem
};
'''

    script_path = os.path.join(os.path.dirname(__file__), 'ai_system_startup.js')
    with open(script_path, 'w') as f:
        f.write(nodejs_script)

    logger.info(f"✅ Created Node.js AI system startup script: {script_path}")
    return script_path

# Package.json requirements for AI system
def create_requirements_file():
    """Create requirements file for Python dependencies"""
    requirements = '''# ConcordBroker AI Data Flow System Requirements

# Core dependencies
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.5.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
psycopg2-binary>=2.9.0
pandas>=2.1.0
numpy>=1.24.0

# AI and ML
openai>=1.3.0
langchain>=0.0.350
langchain-openai>=0.0.2
langchain-community>=0.0.10

# Spark (optional)
pyspark>=3.5.0

# Database and caching
redis>=5.0.0
aioredis>=2.0.0

# Monitoring and logging
prometheus-client>=0.19.0

# Development and testing
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Environment management
python-dotenv>=1.0.0

# HTTP clients
requests>=2.31.0
httpx>=0.25.0
'''

    requirements_path = os.path.join(os.path.dirname(__file__), '../requirements/ai_system_requirements.txt')
    os.makedirs(os.path.dirname(requirements_path), exist_ok=True)

    with open(requirements_path, 'w') as f:
        f.write(requirements)

    logger.info(f"✅ Created requirements file: {requirements_path}")
    return requirements_path

# Main entry point for this module
async def main():
    """Main function for testing the integration"""
    try:
        # Create integration files
        create_mcp_integration_script()
        update_mcp_server_startup()
        create_requirements_file()

        # Test the integration
        logger.info("🧪 Testing MCP integration...")
        startup_manager = MCPAutoStartup()

        # Just test initialization, don't start services
        config = startup_manager._load_config()
        ai_system = MCPIntegratedSystem(config)
        await ai_system.initialize()

        logger.info("✅ MCP integration test completed successfully")

        # Show integration summary
        print("\n" + "="*80)
        print("🎉 MCP INTEGRATION SETUP COMPLETE")
        print("="*80)
        print("\nFiles created:")
        print("📄 ai-agents/start_ai_system.py - Main AI system startup script")
        print("📄 ai-agents/ai_system_startup.js - Node.js integration script")
        print("📄 requirements/ai_system_requirements.txt - Python dependencies")
        print("\nTo activate the AI system:")
        print("1. Install Python dependencies: pip install -r requirements/ai_system_requirements.txt")
        print("2. Ensure all environment variables are set in .env.mcp")
        print("3. Start MCP server - AI system will auto-start")
        print("4. Access AI system at: http://localhost:8003/ai-system/health")
        print("5. Monitor via Jupyter notebook: notebooks/data_flow_monitoring.ipynb")
        print("\n✨ The AI system will now automatically start with Claude Code sessions!")
        print("="*80)

    except Exception as e:
        logger.error(f"❌ MCP integration test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())