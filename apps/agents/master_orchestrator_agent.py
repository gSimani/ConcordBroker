"""
Master Orchestrator Agent
Coordinates all data management agents to ensure proper data flow from Supabase to the website
"""

import os
import sys
import json
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import schedule
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import all sub-agents
from field_discovery_agent import FieldDiscoveryAgent
from data_mapping_agent import DataMappingAgent
from live_data_sync_agent import LiveDataSyncAgent
from data_validation_agent import DataValidationAgent

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"
    PAUSED = "paused"
    STOPPED = "stopped"

class WorkflowStage(Enum):
    """Workflow stage enumeration"""
    DISCOVERY = "discovery"
    MAPPING = "mapping"
    VALIDATION = "validation"
    SYNC = "sync"
    MONITORING = "monitoring"

class MasterOrchestratorAgent:
    """
    Master agent that orchestrates all data management agents
    """
    
    def __init__(self):
        self.agents = {}
        self.agent_status = {}
        self.workflow_status = {}
        self.orchestration_log = []
        self.error_recovery_attempts = {}
        self.performance_metrics = {}
        self.is_running = False
        self.workflow_thread = None
        self.monitoring_thread = None
        self.config = self._load_configuration()
        
    def _load_configuration(self) -> Dict:
        """
        Load orchestrator configuration
        """
        return {
            'discovery_interval': 3600,  # Run discovery every hour
            'mapping_interval': 1800,    # Update mappings every 30 minutes
            'validation_interval': 300,   # Validate data every 5 minutes
            'sync_interval': 10,          # Sync data every 10 seconds
            'health_check_interval': 60, # Check agent health every minute
            'max_error_retries': 3,
            'error_cooldown': 300,       # 5 minutes cooldown after max retries
            'batch_size': 100,
            'enable_auto_recovery': True,
            'enable_notifications': False,
            'log_level': 'INFO'
        }
    
    def initialize_agents(self) -> Dict[str, Any]:
        """
        Initialize all sub-agents
        """
        print("[Master Orchestrator] Initializing all agents...")
        
        try:
            # Initialize Field Discovery Agent
            self.agents['discovery'] = FieldDiscoveryAgent()
            self.agent_status['discovery'] = AgentStatus.IDLE
            print("  [OK] Field Discovery Agent initialized")
            
            # Initialize Data Mapping Agent
            self.agents['mapping'] = DataMappingAgent()
            self.agent_status['mapping'] = AgentStatus.IDLE
            print("  [OK] Data Mapping Agent initialized")
            
            # Initialize Data Validation Agent
            self.agents['validation'] = DataValidationAgent()
            self.agents['validation'].define_validation_rules()
            self.agent_status['validation'] = AgentStatus.IDLE
            print("  [OK] Data Validation Agent initialized")
            
            # Initialize Live Data Sync Agent
            self.agents['sync'] = LiveDataSyncAgent()
            self.agent_status['sync'] = AgentStatus.IDLE
            print("  [OK] Live Data Sync Agent initialized")
            
            self._log_event("agents_initialized", "All agents successfully initialized")
            
            return {
                'success': True,
                'agents': list(self.agents.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._log_error("initialization", str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def start_orchestration(self) -> None:
        """
        Start the orchestration workflow
        """
        if self.is_running:
            print("[Master Orchestrator] Already running")
            return
        
        self.is_running = True
        print("[Master Orchestrator] Starting orchestration workflow...")
        
        # Initialize agents if not already done
        if not self.agents:
            self.initialize_agents()
        
        # Start workflow thread
        self.workflow_thread = threading.Thread(target=self._run_workflow, daemon=True)
        self.workflow_thread.start()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._run_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        # Schedule periodic tasks
        self._schedule_tasks()
        
        self._log_event("orchestration_started", "Master orchestration started")
        print("[Master Orchestrator] Orchestration started successfully")
    
    def _run_workflow(self) -> None:
        """
        Main workflow execution loop
        """
        while self.is_running:
            try:
                # Execute workflow stages in sequence
                self._execute_discovery_stage()
                time.sleep(2)
                
                self._execute_mapping_stage()
                time.sleep(2)
                
                self._execute_validation_stage()
                time.sleep(2)
                
                self._execute_sync_stage()
                
                # Wait before next cycle
                time.sleep(self.config['sync_interval'])
                
            except Exception as e:
                self._handle_workflow_error(e)
                time.sleep(10)  # Wait before retry
    
    def _execute_discovery_stage(self) -> None:
        """
        Execute field discovery stage
        """
        if self.agent_status.get('discovery') == AgentStatus.RUNNING:
            return
        
        try:
            self.agent_status['discovery'] = AgentStatus.RUNNING
            self.workflow_status[WorkflowStage.DISCOVERY] = 'in_progress'
            
            # Run field discovery
            discovery_agent = self.agents['discovery']
            discovered_fields = discovery_agent.scan_all_components()
            
            # Validate discovered fields
            field_map = discovery_agent.generate_field_map()
            missing_ids = discovery_agent.find_missing_ids()
            
            # Store results
            self.workflow_status[WorkflowStage.DISCOVERY] = {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'fields_discovered': len(field_map.get('all_data_fields', [])),
                'components_scanned': field_map.get('total_components', 0),
                'missing_ids_count': len(missing_ids)
            }
            
            self.agent_status['discovery'] = AgentStatus.IDLE
            self._log_event("discovery_completed", f"Discovered {len(discovered_fields)} field locations")
            
        except Exception as e:
            self.agent_status['discovery'] = AgentStatus.ERROR
            self._handle_agent_error('discovery', e)
    
    def _execute_mapping_stage(self) -> None:
        """
        Execute data mapping stage
        """
        if self.agent_status.get('mapping') == AgentStatus.RUNNING:
            return
        
        try:
            self.agent_status['mapping'] = AgentStatus.RUNNING
            self.workflow_status[WorkflowStage.MAPPING] = 'in_progress'
            
            # Run data mapping
            mapping_agent = self.agents['mapping']
            
            # Discover Supabase schema
            schema = mapping_agent.discover_supabase_schema()
            
            # Create field mappings
            mappings = mapping_agent.create_field_mappings()
            
            # Generate mapping report
            mapping_report = mapping_agent.generate_mapping_report()
            
            self.workflow_status[WorkflowStage.MAPPING] = {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'total_mappings': mapping_report.get('total_mappings', 0),
                'supabase_tables': mapping_report.get('supabase_tables', 0)
            }
            
            self.agent_status['mapping'] = AgentStatus.IDLE
            self._log_event("mapping_completed", f"Created {len(mappings)} field mappings")
            
        except Exception as e:
            self.agent_status['mapping'] = AgentStatus.ERROR
            self._handle_agent_error('mapping', e)
    
    def _execute_validation_stage(self) -> None:
        """
        Execute data validation stage
        """
        if self.agent_status.get('validation') == AgentStatus.RUNNING:
            return
        
        try:
            self.agent_status['validation'] = AgentStatus.RUNNING
            self.workflow_status[WorkflowStage.VALIDATION] = 'in_progress'
            
            # Run data validation
            validation_agent = self.agents['validation']
            
            # Check data integrity
            integrity_report = validation_agent.check_data_integrity()
            
            # Validate sample records
            if 'sync' in self.agents:
                sync_agent = self.agents['sync']
                if hasattr(sync_agent, 'supabase') and sync_agent.supabase:
                    # Get sample records for validation
                    try:
                        result = sync_agent.supabase.table('florida_parcels').select('*').limit(10).execute()
                        if result.data:
                            batch_validation = validation_agent.validate_batch(result.data)
                            
                            self.workflow_status[WorkflowStage.VALIDATION] = {
                                'status': 'completed',
                                'timestamp': datetime.now().isoformat(),
                                'valid_records': batch_validation.get('valid_records', 0),
                                'invalid_records': batch_validation.get('invalid_records', 0),
                                'integrity_issues': len(integrity_report.get('issues', []))
                            }
                    except:
                        pass
            
            self.agent_status['validation'] = AgentStatus.IDLE
            self._log_event("validation_completed", "Data validation completed")
            
        except Exception as e:
            self.agent_status['validation'] = AgentStatus.ERROR
            self._handle_agent_error('validation', e)
    
    def _execute_sync_stage(self) -> None:
        """
        Execute data synchronization stage
        """
        if self.agent_status.get('sync') == AgentStatus.RUNNING:
            return
        
        try:
            self.agent_status['sync'] = AgentStatus.RUNNING
            self.workflow_status[WorkflowStage.SYNC] = 'in_progress'
            
            # Start live data sync if not already running
            sync_agent = self.agents['sync']
            
            if not sync_agent.is_running:
                sync_agent.start_monitoring(['florida_parcels', 'property_sales_history'])
            
            # Get sync status
            sync_status = sync_agent.get_sync_status()
            
            self.workflow_status[WorkflowStage.SYNC] = {
                'status': 'active',
                'timestamp': datetime.now().isoformat(),
                'monitored_tables': sync_status.get('monitored_tables', []),
                'queue_size': sync_status.get('queue_size', 0),
                'recent_syncs': len(sync_status.get('recent_syncs', {}))
            }
            
            self.agent_status['sync'] = AgentStatus.RUNNING
            self._log_event("sync_active", f"Monitoring {len(sync_status.get('monitored_tables', []))} tables")
            
        except Exception as e:
            self.agent_status['sync'] = AgentStatus.ERROR
            self._handle_agent_error('sync', e)
    
    def _run_monitoring(self) -> None:
        """
        Monitor agent health and performance
        """
        while self.is_running:
            try:
                # Check each agent's health
                for agent_name, agent in self.agents.items():
                    self._check_agent_health(agent_name, agent)
                
                # Calculate performance metrics
                self._calculate_performance_metrics()
                
                # Check for and recover from errors
                if self.config['enable_auto_recovery']:
                    self._attempt_error_recovery()
                
                # Wait before next check
                time.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                self._log_error("monitoring", str(e))
                time.sleep(60)
    
    def _check_agent_health(self, agent_name: str, agent: Any) -> None:
        """
        Check health of a specific agent
        """
        try:
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'status': self.agent_status.get(agent_name, AgentStatus.IDLE),
                'responsive': True
            }
            
            # Check if agent has specific health check method
            if hasattr(agent, 'get_status') or hasattr(agent, 'get_sync_status'):
                if agent_name == 'sync' and hasattr(agent, 'get_sync_status'):
                    status = agent.get_sync_status()
                    health_status['details'] = status
                    health_status['healthy'] = status.get('agent_status') == 'running'
                else:
                    health_status['healthy'] = True
            else:
                health_status['healthy'] = self.agent_status.get(agent_name) != AgentStatus.ERROR
            
            # Update performance metrics
            if agent_name not in self.performance_metrics:
                self.performance_metrics[agent_name] = []
            
            self.performance_metrics[agent_name].append(health_status)
            
            # Keep only last 100 health checks
            if len(self.performance_metrics[agent_name]) > 100:
                self.performance_metrics[agent_name] = self.performance_metrics[agent_name][-100:]
                
        except Exception as e:
            self._log_error(f"health_check_{agent_name}", str(e))
    
    def _calculate_performance_metrics(self) -> None:
        """
        Calculate overall system performance metrics
        """
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'agents': {},
            'overall_health': 'healthy'
        }
        
        for agent_name, status in self.agent_status.items():
            error_count = self.error_recovery_attempts.get(agent_name, 0)
            
            metrics['agents'][agent_name] = {
                'status': status.value,
                'error_count': error_count,
                'health': 'healthy' if status != AgentStatus.ERROR else 'unhealthy'
            }
            
            if status == AgentStatus.ERROR:
                metrics['overall_health'] = 'degraded'
        
        # Check workflow stages
        active_stages = sum(
            1 for stage_data in self.workflow_status.values()
            if isinstance(stage_data, dict) and stage_data.get('status') in ['active', 'completed']
        )
        
        metrics['workflow'] = {
            'active_stages': active_stages,
            'total_stages': len(WorkflowStage)
        }
        
        self.performance_metrics['system'] = metrics
    
    def _attempt_error_recovery(self) -> None:
        """
        Attempt to recover agents in error state
        """
        for agent_name, status in self.agent_status.items():
            if status == AgentStatus.ERROR:
                retry_count = self.error_recovery_attempts.get(agent_name, 0)
                
                if retry_count < self.config['max_error_retries']:
                    print(f"[Master Orchestrator] Attempting recovery for {agent_name} agent (attempt {retry_count + 1})")
                    
                    try:
                        # Re-initialize the agent
                        if agent_name == 'discovery':
                            self.agents[agent_name] = FieldDiscoveryAgent()
                        elif agent_name == 'mapping':
                            self.agents[agent_name] = DataMappingAgent()
                        elif agent_name == 'validation':
                            self.agents[agent_name] = DataValidationAgent()
                            self.agents[agent_name].define_validation_rules()
                        elif agent_name == 'sync':
                            self.agents[agent_name] = LiveDataSyncAgent()
                        
                        self.agent_status[agent_name] = AgentStatus.IDLE
                        self.error_recovery_attempts[agent_name] = 0
                        self._log_event(f"{agent_name}_recovered", f"Agent recovered successfully")
                        
                    except Exception as e:
                        self.error_recovery_attempts[agent_name] = retry_count + 1
                        self._log_error(f"recovery_{agent_name}", str(e))
                else:
                    # Max retries reached, pause agent
                    self.agent_status[agent_name] = AgentStatus.PAUSED
                    self._log_event(f"{agent_name}_paused", f"Agent paused after {retry_count} recovery attempts")
    
    def _schedule_tasks(self) -> None:
        """
        Schedule periodic tasks
        """
        # Schedule field discovery
        schedule.every(self.config['discovery_interval']).seconds.do(
            lambda: self._execute_discovery_stage()
        )
        
        # Schedule mapping updates
        schedule.every(self.config['mapping_interval']).seconds.do(
            lambda: self._execute_mapping_stage()
        )
        
        # Schedule validation checks
        schedule.every(self.config['validation_interval']).seconds.do(
            lambda: self._execute_validation_stage()
        )
        
        # Start scheduler thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
    
    def force_refresh(self, stages: List[str] = None) -> Dict:
        """
        Force refresh specific workflow stages
        """
        if not stages:
            stages = ['discovery', 'mapping', 'validation', 'sync']
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'stages': {}
        }
        
        for stage in stages:
            try:
                if stage == 'discovery':
                    self._execute_discovery_stage()
                elif stage == 'mapping':
                    self._execute_mapping_stage()
                elif stage == 'validation':
                    self._execute_validation_stage()
                elif stage == 'sync':
                    self._execute_sync_stage()
                
                results['stages'][stage] = 'success'
                
            except Exception as e:
                results['stages'][stage] = f'error: {str(e)}'
        
        return results
    
    def get_orchestration_status(self) -> Dict:
        """
        Get comprehensive orchestration status
        """
        # Convert workflow status keys to strings
        workflow_status_serializable = {}
        for key, value in self.workflow_status.items():
            if hasattr(key, 'value'):
                workflow_status_serializable[key.value] = value
            else:
                workflow_status_serializable[str(key)] = value
        
        return {
            'timestamp': datetime.now().isoformat(),
            'is_running': self.is_running,
            'agents': {
                name: {
                    'status': status.value,
                    'errors': self.error_recovery_attempts.get(name, 0)
                }
                for name, status in self.agent_status.items()
            },
            'workflow': workflow_status_serializable,
            'performance': self.performance_metrics.get('system', {}),
            'recent_events': self.orchestration_log[-20:]
        }
    
    def pause_agent(self, agent_name: str) -> bool:
        """
        Pause a specific agent
        """
        if agent_name in self.agents:
            self.agent_status[agent_name] = AgentStatus.PAUSED
            self._log_event(f"{agent_name}_paused", f"Agent paused by user")
            return True
        return False
    
    def resume_agent(self, agent_name: str) -> bool:
        """
        Resume a paused agent
        """
        if agent_name in self.agents and self.agent_status.get(agent_name) == AgentStatus.PAUSED:
            self.agent_status[agent_name] = AgentStatus.IDLE
            self._log_event(f"{agent_name}_resumed", f"Agent resumed by user")
            return True
        return False
    
    def stop_orchestration(self) -> None:
        """
        Stop all orchestration activities
        """
        print("[Master Orchestrator] Stopping orchestration...")
        self.is_running = False
        
        # Stop all agents
        for agent_name, agent in self.agents.items():
            if agent_name == 'sync' and hasattr(agent, 'stop_monitoring'):
                agent.stop_monitoring()
            
            self.agent_status[agent_name] = AgentStatus.STOPPED
        
        # Clear scheduled tasks
        schedule.clear()
        
        self._log_event("orchestration_stopped", "Master orchestration stopped")
        print("[Master Orchestrator] Orchestration stopped")
    
    def _handle_agent_error(self, agent_name: str, error: Exception) -> None:
        """
        Handle agent errors
        """
        error_msg = f"Error in {agent_name}: {str(error)}"
        self._log_error(agent_name, str(error))
        
        if agent_name not in self.error_recovery_attempts:
            self.error_recovery_attempts[agent_name] = 0
        
        self.error_recovery_attempts[agent_name] += 1
    
    def _handle_workflow_error(self, error: Exception) -> None:
        """
        Handle workflow errors
        """
        self._log_error("workflow", str(error))
    
    def _log_event(self, event_type: str, message: str) -> None:
        """
        Log orchestration events
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'message': message
        }
        
        self.orchestration_log.append(event)
        
        # Keep only last 1000 events
        if len(self.orchestration_log) > 1000:
            self.orchestration_log = self.orchestration_log[-1000:]
        
        if self.config['log_level'] in ['INFO', 'DEBUG']:
            print(f"[Master Orchestrator] {event_type}: {message}")
    
    def _log_error(self, context: str, error_msg: str) -> None:
        """
        Log errors
        """
        self._log_event(f"error_{context}", error_msg)
    
    def save_orchestration_report(self, output_path: str = "orchestration_report.json") -> None:
        """
        Save comprehensive orchestration report
        """
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': self.get_orchestration_status(),
            'configuration': self.config,
            'agent_reports': {},
            'orchestration_log': self.orchestration_log[-100:]
        }
        
        # Collect reports from each agent
        try:
            if 'discovery' in self.agents:
                report['agent_reports']['discovery'] = self.agents['discovery'].generate_field_map()
        except:
            pass
        
        try:
            if 'mapping' in self.agents:
                report['agent_reports']['mapping'] = self.agents['mapping'].generate_mapping_report()
        except:
            pass
        
        try:
            if 'validation' in self.agents:
                report['agent_reports']['validation'] = self.agents['validation'].generate_validation_report()
        except:
            pass
        
        try:
            if 'sync' in self.agents:
                report['agent_reports']['sync'] = self.agents['sync'].get_sync_status()
        except:
            pass
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"[Master Orchestrator] Report saved to {output_path}")


def main():
    """
    Run the Master Orchestrator Agent
    """
    orchestrator = MasterOrchestratorAgent()
    
    print("[Master Orchestrator] Initializing system...")
    print("=" * 60)
    
    # Initialize all agents
    init_result = orchestrator.initialize_agents()
    
    if not init_result['success']:
        print(f"[Master Orchestrator] Failed to initialize: {init_result.get('error')}")
        return
    
    # Start orchestration
    orchestrator.start_orchestration()
    
    # Run for demonstration period
    import time
    demo_duration = 30  # seconds
    
    print(f"\n[Master Orchestrator] Running for {demo_duration} seconds...")
    print("=" * 60)
    
    # Show status periodically
    for i in range(3):
        time.sleep(10)
        status = orchestrator.get_orchestration_status()
        
        print(f"\n[Master Orchestrator] Status Update {i+1}:")
        print(f"  - Running: {status['is_running']}")
        print(f"  - Agents:")
        for agent_name, agent_info in status['agents'].items():
            print(f"    * {agent_name}: {agent_info['status']}")
        
        if status.get('workflow'):
            print(f"  - Workflow Stages:")
            for stage, stage_data in status['workflow'].items():
                if isinstance(stage_data, dict):
                    print(f"    * {stage.value if hasattr(stage, 'value') else stage}: {stage_data.get('status', 'unknown')}")
    
    # Force refresh all stages
    print(f"\n[Master Orchestrator] Testing force refresh...")
    refresh_result = orchestrator.force_refresh(['discovery', 'mapping'])
    print(f"  Refresh results: {refresh_result['stages']}")
    
    # Save final report
    orchestrator.save_orchestration_report()
    
    # Stop orchestration
    orchestrator.stop_orchestration()
    
    print("\n[Master Orchestrator] Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()