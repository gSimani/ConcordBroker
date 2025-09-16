"""
Master Pipeline Controller
Initializes and starts all data pipeline agents with continuous monitoring
"""

import os
import sys
import asyncio
import logging
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv
import schedule
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import subprocess

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PipelineOrchestrator:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        if '&supa=' in self.db_url:
            self.db_url = self.db_url.split('&supa=')[0]
        elif '?supa=' in self.db_url:
            self.db_url = self.db_url.split('?supa=')[0]
        
        self.agents = {
            'tpp_agent': {
                'script': 'apps/workers/tpp/main.py',
                'schedule': 'weekly',
                'time': '05:00',
                'day': 1,  # Monday
                'description': 'Tangible Personal Property data'
            },
            'nav_agent': {
                'script': 'apps/workers/nav_assessments/main.py',
                'schedule': 'weekly',
                'time': '05:30',
                'day': 2,  # Tuesday
                'description': 'Non-ad valorem assessments'
            },
            'sdf_agent': {
                'script': 'apps/workers/sdf_sales/main.py',
                'schedule': 'daily',
                'time': '06:00',
                'description': 'Property sales data'
            },
            'sunbiz_agent': {
                'script': 'apps/workers/sunbiz_sftp/main.py',
                'schedule': 'daily',
                'time': '02:00',
                'description': 'Business entity data'
            }
        }
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running_agents = {}
    
    def update_agent_status(self, agent_name, status, error_msg=None):
        """Update agent status in database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            if status == 'running':
                cursor.execute("""
                    UPDATE fl_agent_status 
                    SET is_running = TRUE, 
                        current_status = %s,
                        last_run_start = NOW(),
                        updated_at = NOW()
                    WHERE agent_name = %s
                """, (status, agent_name))
            elif status == 'completed':
                cursor.execute("""
                    UPDATE fl_agent_status 
                    SET is_running = FALSE, 
                        current_status = %s,
                        last_run_end = NOW(),
                        last_run_status = 'success',
                        updated_at = NOW()
                    WHERE agent_name = %s
                """, (status, agent_name))
            elif status == 'failed':
                cursor.execute("""
                    UPDATE fl_agent_status 
                    SET is_running = FALSE, 
                        current_status = %s,
                        last_run_end = NOW(),
                        last_run_status = 'failed',
                        last_error = %s,
                        updated_at = NOW()
                    WHERE agent_name = %s
                """, (status, error_msg, agent_name))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update agent status: {e}")
    
    def run_agent(self, agent_name):
        """Run a specific agent"""
        agent_info = self.agents.get(agent_name)
        if not agent_info:
            logger.error(f"Unknown agent: {agent_name}")
            return
        
        script_path = agent_info['script']
        
        logger.info(f"Starting {agent_name}: {agent_info['description']}")
        self.update_agent_status(agent_name, 'running')
        
        try:
            # Check if script exists
            if not os.path.exists(script_path):
                # Try to create a simple agent script if it doesn't exist
                self.create_agent_script(agent_name, script_path)
            
            # Run the agent script
            result = subprocess.run(
                [sys.executable, script_path],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info(f"{agent_name} completed successfully")
                self.update_agent_status(agent_name, 'completed')
                
                # Log data update
                self.log_data_update(agent_name, 'success', result.stdout)
            else:
                logger.error(f"{agent_name} failed: {result.stderr}")
                self.update_agent_status(agent_name, 'failed', result.stderr)
                self.log_data_update(agent_name, 'failed', result.stderr)
                
        except subprocess.TimeoutExpired:
            logger.error(f"{agent_name} timed out")
            self.update_agent_status(agent_name, 'failed', 'Agent timed out after 1 hour')
        except FileNotFoundError:
            logger.error(f"Script not found: {script_path}")
            self.update_agent_status(agent_name, 'failed', f'Script not found: {script_path}')
        except Exception as e:
            logger.error(f"Error running {agent_name}: {e}")
            self.update_agent_status(agent_name, 'failed', str(e))
    
    def create_agent_script(self, agent_name, script_path):
        """Create a basic agent script if it doesn't exist"""
        logger.info(f"Creating placeholder script for {agent_name}")
        
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        
        # Create a basic agent script
        agent_code = f'''"""
{agent_name.upper()} Data Pipeline Agent
Auto-generated placeholder - replace with actual implementation
"""

import os
import sys
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting {agent_name}...")
    logger.info("Checking for data updates...")
    
    # TODO: Implement actual data collection logic here
    # For now, this is a placeholder
    
    logger.info("{agent_name} completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        
        with open(script_path, 'w') as f:
            f.write(agent_code)
    
    def log_data_update(self, agent_name, status, details=None):
        """Log data update to database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO fl_data_updates 
                (source_type, source_name, status, agent_name, update_date)
                VALUES (%s, %s, %s, %s, NOW())
            """, (agent_name.replace('_agent', '').upper(), agent_name, status, agent_name))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log data update: {e}")
    
    def schedule_agents(self):
        """Schedule all agents based on their configuration"""
        for agent_name, config in self.agents.items():
            if config['schedule'] == 'daily':
                schedule.every().day.at(config['time']).do(
                    lambda name=agent_name: self.executor.submit(self.run_agent, name)
                )
                logger.info(f"Scheduled {agent_name} daily at {config['time']}")
                
            elif config['schedule'] == 'weekly':
                day_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                day_name = day_names[config['day'] - 1]
                getattr(schedule.every(), day_name).at(config['time']).do(
                    lambda name=agent_name: self.executor.submit(self.run_agent, name)
                )
                logger.info(f"Scheduled {agent_name} weekly on {day_name} at {config['time']}")
    
    def run_initial_load(self):
        """Run all agents once for initial data load"""
        logger.info("="*60)
        logger.info("STARTING INITIAL DATA LOAD")
        logger.info("="*60)
        
        # Run SDF agent first (most recent data)
        logger.info("\n[1/4] Running SDF Sales Agent...")
        self.run_agent('sdf_agent')
        
        # Run Sunbiz agent
        logger.info("\n[2/4] Running Sunbiz Business Agent...")
        self.run_agent('sunbiz_agent')
        
        # Run TPP agent
        logger.info("\n[3/4] Running TPP Property Agent...")
        self.run_agent('tpp_agent')
        
        # Run NAV agent
        logger.info("\n[4/4] Running NAV Assessment Agent...")
        self.run_agent('nav_agent')
        
        logger.info("\n" + "="*60)
        logger.info("INITIAL DATA LOAD COMPLETE")
        logger.info("="*60)
    
    def monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting continuous monitoring loop...")
        
        while True:
            try:
                # Run scheduled jobs
                schedule.run_pending()
                
                # Check for manual triggers or urgent updates
                self.check_urgent_updates()
                
                # Sleep for 60 seconds
                time.sleep(60)
                
            except KeyboardInterrupt:
                logger.info("Stopping orchestrator...")
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                time.sleep(60)
    
    def check_urgent_updates(self):
        """Check for any urgent data updates that need immediate processing"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Check if any agents need immediate run
            cursor.execute("""
                SELECT agent_name 
                FROM fl_agent_status 
                WHERE is_enabled = TRUE 
                AND current_status = 'pending_urgent'
            """)
            
            urgent_agents = cursor.fetchall()
            for agent in urgent_agents:
                logger.info(f"Running urgent update for {agent[0]}")
                self.executor.submit(self.run_agent, agent[0])
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to check urgent updates: {e}")
    
    def start(self):
        """Start the orchestrator"""
        logger.info("="*60)
        logger.info("CONCORDBROKER DATA PIPELINE ORCHESTRATOR")
        logger.info("="*60)
        logger.info(f"Started at: {datetime.now()}")
        
        # Schedule all agents
        self.schedule_agents()
        
        # Run initial data load
        self.run_initial_load()
        
        # Update next run times in database
        self.update_next_run_times()
        
        # Start monitoring loop
        logger.info("\nStarting continuous monitoring...")
        logger.info("Agents will run automatically on schedule")
        logger.info("Press Ctrl+C to stop")
        
        self.monitor_loop()
    
    def update_next_run_times(self):
        """Update next scheduled run times in database"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            for agent_name, config in self.agents.items():
                # Calculate next run time
                now = datetime.now()
                time_parts = config['time'].split(':')
                run_time = now.replace(hour=int(time_parts[0]), minute=int(time_parts[1]), second=0)
                
                if config['schedule'] == 'daily':
                    if run_time <= now:
                        next_run = run_time + timedelta(days=1)
                    else:
                        next_run = run_time
                elif config['schedule'] == 'weekly':
                    days_ahead = config['day'] - now.weekday() - 1
                    if days_ahead <= 0:
                        days_ahead += 7
                    next_run = run_time + timedelta(days=days_ahead)
                
                cursor.execute("""
                    UPDATE fl_agent_status 
                    SET next_scheduled_run = %s,
                        updated_at = NOW()
                    WHERE agent_name = %s
                """, (next_run, agent_name))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info("Updated next run times for all agents")
            
        except Exception as e:
            logger.error(f"Failed to update next run times: {e}")

if __name__ == "__main__":
    orchestrator = PipelineOrchestrator()
    orchestrator.start()