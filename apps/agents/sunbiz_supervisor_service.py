"""
SUNBIZ SUPERVISOR SERVICE - Windows/Linux Service Wrapper
=========================================================
Runs the Sunbiz Supervisor Agent as a permanent system service
"""

import os
import sys
import time
import logging
import signal
import subprocess
from pathlib import Path

# Platform-specific imports
if sys.platform == "win32":
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
else:
    import daemon
    from daemon import pidfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [SERVICE] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sunbiz_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SunbizSupervisorService:
    """Cross-platform service wrapper"""
    
    def __init__(self):
        self.running = False
        self.process = None
        self.agent_path = Path(__file__).parent / "sunbiz_supervisor_agent.py"
        
    def start(self):
        """Start the supervisor agent"""
        logger.info("Starting Sunbiz Supervisor Service")
        self.running = True
        
        # Start the supervisor agent as a subprocess
        self.process = subprocess.Popen(
            [sys.executable, str(self.agent_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        logger.info(f"Supervisor agent started with PID: {self.process.pid}")
        
        # Monitor the process
        while self.running:
            # Check if process is still running
            if self.process.poll() is not None:
                logger.error("Supervisor agent crashed, restarting...")
                time.sleep(5)
                self.process = subprocess.Popen(
                    [sys.executable, str(self.agent_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            time.sleep(10)
    
    def stop(self):
        """Stop the supervisor agent"""
        logger.info("Stopping Sunbiz Supervisor Service")
        self.running = False
        
        if self.process:
            # Send graceful shutdown signal
            self.process.terminate()
            
            # Wait for process to end
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                logger.warning("Force killing supervisor agent")
                self.process.kill()
        
        logger.info("Sunbiz Supervisor Service stopped")

# Windows Service Implementation
if sys.platform == "win32":
    class WindowsSunbizService(win32serviceutil.ServiceFramework):
        _svc_name_ = "SunbizSupervisor"
        _svc_display_name_ = "Sunbiz Database Supervisor Agent"
        _svc_description_ = "Manages daily updates of Florida Sunbiz database"
        
        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.service = SunbizSupervisorService()
        
        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            win32event.SetEvent(self.hWaitStop)
            self.service.stop()
        
        def SvcDoRun(self):
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            self.service.start()

# Linux Daemon Implementation
else:
    def run_as_daemon():
        """Run as Linux daemon"""
        service = SunbizSupervisorService()
        
        # Setup signal handlers
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}")
            service.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # Create daemon context
        context = daemon.DaemonContext(
            working_directory='/opt/sunbiz',
            pidfile=pidfile.TimeoutPIDLockFile('/var/run/sunbiz_supervisor.pid'),
            files_preserve=[
                logging.root.handlers[0].stream.fileno()
            ]
        )
        
        with context:
            service.start()

# Main entry point
def main():
    """Main entry point for service"""
    
    if sys.platform == "win32":
        # Windows service commands
        if len(sys.argv) == 1:
            servicemanager.Initialize()
            servicemanager.PrepareToHostSingle(WindowsSunbizService)
            servicemanager.StartServiceCtrlDispatcher()
        else:
            win32serviceutil.HandleCommandLine(WindowsSunbizService)
    
    else:
        # Linux daemon commands
        import argparse
        
        parser = argparse.ArgumentParser(description='Sunbiz Supervisor Service')
        parser.add_argument('command', choices=['start', 'stop', 'restart', 'status'])
        args = parser.parse_args()
        
        pid_file = '/var/run/sunbiz_supervisor.pid'
        
        if args.command == 'start':
            print("Starting Sunbiz Supervisor daemon...")
            run_as_daemon()
        
        elif args.command == 'stop':
            print("Stopping Sunbiz Supervisor daemon...")
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                os.kill(pid, signal.SIGTERM)
                os.remove(pid_file)
        
        elif args.command == 'restart':
            print("Restarting Sunbiz Supervisor daemon...")
            # Stop
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                os.kill(pid, signal.SIGTERM)
                os.remove(pid_file)
            time.sleep(2)
            # Start
            run_as_daemon()
        
        elif args.command == 'status':
            if os.path.exists(pid_file):
                with open(pid_file, 'r') as f:
                    pid = int(f.read())
                try:
                    os.kill(pid, 0)
                    print(f"Sunbiz Supervisor is running (PID: {pid})")
                except OSError:
                    print("Sunbiz Supervisor is not running (stale PID file)")
            else:
                print("Sunbiz Supervisor is not running")

if __name__ == "__main__":
    main()