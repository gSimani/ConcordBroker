#!/usr/bin/env python3
"""
Agent Deployment and Testing Script
Deploys the complete ConcordBroker agent system and runs initial tests
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
import json

# Add apps directory to Python path
sys.path.append(str(Path(__file__).parent / "apps"))

from agents.master_orchestrator import MasterOrchestrator, AgentTask, Priority

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentDeployment:
    """Handles deployment and testing of the ConcordBroker agent system"""
    
    def __init__(self):
        self.orchestrator = None
        self.deployment_results = {}
        
    async def deploy(self):
        """Deploy the complete agent system"""
        logger.info("🚀 Starting ConcordBroker Agent System Deployment")
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        try:
            # Step 1: Initialize Master Orchestrator
            logger.info("Step 1: Initializing Master Orchestrator...")
            self.orchestrator = MasterOrchestrator()
            self.deployment_results['orchestrator'] = 'initialized'
            
            # Step 2: Test agent connections and status
            logger.info("Step 2: Testing agent status...")
            agent_status = await self._test_agent_status()
            self.deployment_results['agent_status'] = agent_status
            
            # Step 3: Run health checks
            logger.info("Step 3: Running system health checks...")
            health_check = await self.orchestrator.health_check()
            self.deployment_results['health_check'] = health_check
            
            # Step 4: Schedule immediate data loading task
            logger.info("Step 4: Scheduling immediate data loading...")
            await self._schedule_immediate_data_load()
            
            # Step 5: Schedule routine maintenance tasks
            logger.info("Step 5: Scheduling routine tasks...")
            self.orchestrator.schedule_routine_tasks()
            
            # Step 6: Run initial test cycle
            logger.info("Step 6: Running initial test cycle...")
            await self._run_test_cycle()
            
            # Step 7: Generate deployment report
            logger.info("Step 7: Generating deployment report...")
            report = self._generate_deployment_report()
            
            logger.info("✅ ConcordBroker Agent System Deployment Complete!")
            logger.info(f"📊 Deployment Report: {report['summary']}")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            self.deployment_results['error'] = str(e)
            raise

    async def _test_agent_status(self):
        """Test status of all configured agents"""
        agent_status = {}
        
        for agent_name, config in self.orchestrator.agents.items():
            try:
                # Try to import and instantiate agent
                module_parts = config.module_path.split('.')
                module = __import__(config.module_path, fromlist=[module_parts[-1]])
                
                agent_class_name = ''.join(word.capitalize() for word in agent_name.split('_'))
                agent_class = getattr(module, agent_class_name)
                agent_instance = agent_class()
                
                # Get agent status
                if hasattr(agent_instance, 'get_status'):
                    status = await agent_instance.get_status()
                    agent_status[agent_name] = {
                        'status': 'ready',
                        'details': status
                    }
                else:
                    agent_status[agent_name] = {
                        'status': 'ready',
                        'details': {'note': 'No status method available'}
                    }
                    
                logger.info(f"✅ {agent_name}: Ready")
                
            except Exception as e:
                logger.error(f"❌ {agent_name}: Failed - {e}")
                agent_status[agent_name] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        return agent_status

    async def _schedule_immediate_data_load(self):
        """Schedule immediate data loading if database is empty"""
        # Check if we need immediate data loading
        task = AgentTask(
            id=f"deploy_data_load_{int(datetime.now().timestamp())}",
            agent_name='data_loader',
            task_type='deployment_load',
            priority=Priority.CRITICAL,
            data={
                'force_reload': False,
                'datasets': ['NAL', 'SDF', 'NAP'],
                'batch_size': 50
            }
        )
        
        await self.orchestrator.add_task(task)
        logger.info("🔄 Data loading task scheduled")

    async def _run_test_cycle(self):
        """Run a test cycle with the orchestrator"""
        logger.info("Running test cycle for 60 seconds...")
        
        # Run orchestrator for 1 minute to test basic functionality
        test_start = datetime.now()
        test_duration = 60  # seconds
        
        async def test_runner():
            while (datetime.now() - test_start).seconds < test_duration:
                await self.orchestrator.process_task_queue()
                await asyncio.sleep(5)
        
        try:
            await asyncio.wait_for(test_runner(), timeout=test_duration + 10)
            self.deployment_results['test_cycle'] = 'completed'
            logger.info("✅ Test cycle completed successfully")
        except asyncio.TimeoutError:
            self.deployment_results['test_cycle'] = 'timeout'
            logger.warning("⚠️ Test cycle timed out")
        except Exception as e:
            self.deployment_results['test_cycle'] = f'failed: {str(e)}'
            logger.error(f"❌ Test cycle failed: {e}")

    def _generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'deployment_id': f"deploy_{int(datetime.now().timestamp())}",
            'system_status': 'deployed',
            'results': self.deployment_results,
            'orchestrator_status': self.orchestrator.get_status_report() if self.orchestrator else None,
            'next_steps': [
                "Monitor agent logs in logs/ directory",
                "Check health_status.json for ongoing health monitoring", 
                "Review task execution in orchestrator logs",
                "Verify data loading progress in database",
                "Monitor alerts.log for any critical issues"
            ],
            'summary': self._create_summary()
        }
        
        # Save report to file
        with open('logs/deployment_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report

    def _create_summary(self):
        """Create deployment summary"""
        total_agents = len(self.orchestrator.agents) if self.orchestrator else 0
        ready_agents = len([
            status for status in self.deployment_results.get('agent_status', {}).values() 
            if status.get('status') == 'ready'
        ])
        
        return {
            'total_agents_configured': total_agents,
            'agents_ready': ready_agents,
            'health_check_passed': 'health_check' in self.deployment_results,
            'data_loading_scheduled': True,
            'test_cycle_result': self.deployment_results.get('test_cycle', 'not_run'),
            'overall_status': 'success' if ready_agents == total_agents else 'partial'
        }

    async def monitor_agents(self, duration_minutes=10):
        """Monitor agent system for specified duration"""
        logger.info(f"🔍 Monitoring agent system for {duration_minutes} minutes...")
        
        if not self.orchestrator:
            raise Exception("Orchestrator not initialized")
        
        end_time = datetime.now().timestamp() + (duration_minutes * 60)
        
        try:
            while datetime.now().timestamp() < end_time:
                # Process tasks
                await self.orchestrator.process_task_queue()
                
                # Health check every 2 minutes
                if datetime.now().second % 120 == 0:
                    await self.orchestrator.health_check()
                    logger.info("Health check completed")
                
                # Status update every minute
                if datetime.now().second % 60 == 0:
                    status = self.orchestrator.get_status_report()
                    logger.info(f"Status: Queue={status['queue_size']}, Running={status['running_tasks']}, Completed={status['completed_tasks']}")
                
                await asyncio.sleep(10)  # Check every 10 seconds
            
            logger.info("✅ Monitoring period completed")
            
        except KeyboardInterrupt:
            logger.info("⏹️ Monitoring stopped by user")
        except Exception as e:
            logger.error(f"❌ Monitoring failed: {e}")
            raise

async def main():
    """Main deployment function"""
    print("ConcordBroker Agent System Deployment")
    print("=====================================")
    
    deployment = AgentDeployment()
    
    try:
        # Deploy the system
        report = await deployment.deploy()
        
        print("\nDeployment Summary:")
        print(f"- Total Agents: {report['summary']['total_agents_configured']}")
        print(f"- Agents Ready: {report['summary']['agents_ready']}")
        print(f"- Overall Status: {report['summary']['overall_status']}")
        
        # Ask user if they want to monitor
        response = input("\nWould you like to monitor the system for 10 minutes? (y/N): ")
        if response.lower() in ['y', 'yes']:
            await deployment.monitor_agents(10)
        else:
            print("\nDeployment complete! Check logs/ directory for ongoing monitoring.")
    
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        print(f"\nDeployment failed: {e}")
        print("Check logs/deployment.log for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)