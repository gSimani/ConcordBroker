#!/usr/bin/env python3
"""
Florida Data Agent Deployment Script
Production-ready deployment script for the Florida property data agent system

Features:
- Environment setup and validation
- Dependency installation and verification  
- Configuration validation and setup
- Database schema deployment
- Service installation and configuration
- Health checks and smoke tests
- Rollback capabilities
- Automated monitoring setup
"""

import os
import sys
import json
import logging
import subprocess
import argparse
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
import tempfile
import platform

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FloridaAgentDeployment:
    """Deployment manager for Florida Data Agents"""
    
    def __init__(self, target_env: str = "production"):
        self.target_env = target_env
        self.project_root = Path(__file__).parent.parent.parent
        self.agent_dir = Path(__file__).parent
        self.deployment_dir = Path("/opt/florida-agents") if platform.system() != "Windows" else Path("C:/florida-agents")
        
        # Deployment configuration
        self.required_python_version = "3.8"
        self.required_packages = [
            "asyncio", "aiohttp", "aiofiles", "asyncpg", "pandas", "numpy",
            "beautifulsoup4", "rich", "psutil", "schedule", "cryptography",
            "jsonschema", "pyyaml", "supabase", "python-dotenv"
        ]
        
        self.services = [
            "florida-agent-orchestrator",
            "florida-agent-scheduler",
            "florida-agent-monitor"
        ]

    def deploy(self):
        """Execute complete deployment process"""
        logger.info(f"🚀 Starting deployment to {self.target_env} environment")
        
        try:
            # Pre-deployment validation
            self.validate_environment()
            self.validate_dependencies() 
            self.validate_configuration()
            
            # Core deployment steps
            self.setup_deployment_directory()
            self.install_application_files()
            self.setup_configuration()
            self.setup_database_schemas()
            self.install_system_services()
            self.setup_monitoring()
            
            # Post-deployment validation
            self.run_health_checks()
            self.run_smoke_tests()
            
            # Finalize deployment
            self.create_deployment_record()
            self.setup_log_rotation()
            
            logger.info("✅ Deployment completed successfully!")
            self.print_deployment_summary()
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            self.rollback_deployment()
            raise

    def validate_environment(self):
        """Validate deployment environment"""
        logger.info("🔍 Validating deployment environment...")
        
        # Check Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if python_version < self.required_python_version:
            raise ValueError(f"Python {self.required_python_version}+ required, found {python_version}")
        
        # Check system requirements
        system = platform.system()
        logger.info(f"Deploying on {system} {platform.release()}")
        
        # Check available disk space (minimum 5GB)
        if system != "Windows":
            stat = os.statvfs(self.deployment_dir.parent)
            available_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
            if available_gb < 5:
                raise ValueError(f"Insufficient disk space: {available_gb:.1f}GB available, 5GB required")
        
        # Check permissions
        if system != "Windows":
            if os.getuid() != 0:
                logger.warning("Not running as root - some operations may require sudo")
        
        logger.info("✅ Environment validation passed")

    def validate_dependencies(self):
        """Validate and install required dependencies"""
        logger.info("📦 Validating dependencies...")
        
        missing_packages = []
        
        for package in self.required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
            self.install_packages(missing_packages)
        
        logger.info("✅ Dependencies validated")

    def install_packages(self, packages: List[str]):
        """Install Python packages using pip"""
        try:
            cmd = [sys.executable, "-m", "pip", "install"] + packages
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Packages installed successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to install packages: {e.stderr}")

    def validate_configuration(self):
        """Validate configuration files and environment variables"""
        logger.info("⚙️ Validating configuration...")
        
        # Check required environment variables
        required_env_vars = [
            "SUPABASE_URL",
            "SUPABASE_ANON_KEY", 
            "SUPABASE_SERVICE_KEY",
            "SUPABASE_DB_URL"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
            logger.info("These can be set in the .env file or system environment")
        
        # Validate configuration file
        config_file = self.agent_dir / "florida_agent_config.json"
        if not config_file.exists():
            logger.info("Creating default configuration file...")
            self.create_default_config()
        
        logger.info("✅ Configuration validated")

    def create_default_config(self):
        """Create default configuration file"""
        from florida_config_manager import FloridaConfigManager
        
        config_manager = FloridaConfigManager()
        default_config = config_manager.get_config()
        
        config_file = self.agent_dir / "florida_agent_config.json"
        with open(config_file, 'w') as f:
            json.dump(default_config, f, indent=2, default=str)
        
        logger.info(f"Default configuration created: {config_file}")

    def setup_deployment_directory(self):
        """Setup deployment directory structure"""
        logger.info("📁 Setting up deployment directory...")
        
        # Create main deployment directory
        self.deployment_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        subdirs = [
            "agents",
            "config", 
            "data",
            "logs",
            "backups",
            "scripts",
            "monitoring"
        ]
        
        for subdir in subdirs:
            (self.deployment_dir / subdir).mkdir(exist_ok=True)
        
        # Set appropriate permissions
        if platform.system() != "Windows":
            os.chmod(self.deployment_dir, 0o755)
            for subdir in subdirs:
                os.chmod(self.deployment_dir / subdir, 0o755)
        
        logger.info(f"✅ Deployment directory setup: {self.deployment_dir}")

    def install_application_files(self):
        """Install application files to deployment directory"""
        logger.info("📋 Installing application files...")
        
        # Copy agent files
        agent_files = list(self.agent_dir.glob("*.py"))
        for file in agent_files:
            if file.name != "deploy_florida_agents.py":  # Skip deployment script
                shutil.copy2(file, self.deployment_dir / "agents")
        
        # Copy configuration files
        config_files = [
            "florida_agent_config.json",
            "requirements.txt"
        ]
        
        for config_file in config_files:
            source_file = self.agent_dir / config_file
            if source_file.exists():
                shutil.copy2(source_file, self.deployment_dir / "config")
            elif config_file == "requirements.txt":
                # Create requirements.txt if it doesn't exist
                self.create_requirements_file()
        
        # Make agent files executable
        if platform.system() != "Windows":
            for py_file in (self.deployment_dir / "agents").glob("*.py"):
                os.chmod(py_file, 0o755)
        
        logger.info("✅ Application files installed")

    def create_requirements_file(self):
        """Create requirements.txt file"""
        requirements_content = """
# Florida Data Agent Dependencies
asyncio>=3.4.3
aiohttp>=3.8.0
aiofiles>=0.8.0
asyncpg>=0.27.0
pandas>=1.3.0
numpy>=1.21.0
beautifulsoup4>=4.10.0
rich>=12.0.0
psutil>=5.8.0
schedule>=1.1.0
cryptography>=3.4.0
jsonschema>=4.0.0
pyyaml>=6.0
supabase>=1.0.0
python-dotenv>=0.19.0
lxml>=4.6.0
requests>=2.25.0
""".strip()
        
        requirements_file = self.deployment_dir / "config" / "requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write(requirements_content)
        
        logger.info("Created requirements.txt")

    def setup_configuration(self):
        """Setup configuration for target environment"""
        logger.info("⚙️ Setting up configuration...")
        
        # Copy environment-specific configuration
        env_config_file = self.deployment_dir / "config" / f"config_{self.target_env}.json"
        
        if not env_config_file.exists():
            # Create environment-specific config from default
            default_config_file = self.deployment_dir / "config" / "florida_agent_config.json"
            if default_config_file.exists():
                shutil.copy2(default_config_file, env_config_file)
        
        # Setup environment file
        env_file = self.deployment_dir / "config" / ".env"
        if not env_file.exists():
            self.create_env_file()
        
        logger.info("✅ Configuration setup complete")

    def create_env_file(self):
        """Create .env file template"""
        env_content = f"""
# Florida Data Agent Environment Configuration
# Environment: {self.target_env}

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key
SUPABASE_DB_URL=postgresql://postgres:password@db.your-project.supabase.co:5432/postgres

# Email Notifications (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=alerts@yourdomain.com
EMAIL_TO=admin@yourdomain.com
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Webhook Notifications (Optional)
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts

# Performance Tuning
LOG_LEVEL=INFO
DOWNLOAD_MAX_CONCURRENT=5
PROCESSING_BATCH_SIZE=10000
DATABASE_MAX_CONNECTIONS=10

# Environment
FLORIDA_AGENT_ENV={self.target_env}
""".strip()
        
        env_file = self.deployment_dir / "config" / ".env"
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        # Set restrictive permissions on .env file
        if platform.system() != "Windows":
            os.chmod(env_file, 0o600)
        
        logger.info(f"Environment file created: {env_file}")
        logger.warning("⚠️ Please update .env file with actual credentials before starting services")

    def setup_database_schemas(self):
        """Setup database schemas and tables"""
        logger.info("🗄️ Setting up database schemas...")
        
        try:
            # Import and run database agent to create schemas
            sys.path.insert(0, str(self.deployment_dir / "agents"))
            
            from florida_config_manager import FloridaConfigManager
            from florida_database_agent import FloridaDatabaseAgent
            
            # Load configuration
            config_manager = FloridaConfigManager(
                str(self.deployment_dir / "config" / f"config_{self.target_env}.json")
            )
            
            # Initialize database agent
            import asyncio
            
            async def setup_schemas():
                db_agent = FloridaDatabaseAgent(config_manager)
                await db_agent.initialize()
                await db_agent.cleanup()
            
            # Run schema setup
            asyncio.run(setup_schemas())
            
            logger.info("✅ Database schemas setup complete")
            
        except Exception as e:
            logger.warning(f"Database schema setup failed: {e}")
            logger.info("Database schemas can be setup manually after deployment")

    def install_system_services(self):
        """Install system services for automatic startup"""
        logger.info("🔧 Installing system services...")
        
        if platform.system() == "Linux":
            self.install_systemd_services()
        elif platform.system() == "Windows":
            self.install_windows_services()
        else:
            logger.warning(f"System services not supported on {platform.system()}")
            self.create_startup_scripts()

    def install_systemd_services(self):
        """Install systemd services on Linux"""
        service_template = """
[Unit]
Description=Florida Data Agent - {service_name}
After=network.target
Requires=network.target

[Service]
Type=simple
User=florida-agent
Group=florida-agent
WorkingDirectory={deployment_dir}
Environment=PYTHONPATH={deployment_dir}/agents
ExecStart={python_path} {script_path} {args}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=florida-agent-{service_name}

[Install]
WantedBy=multi-user.target
"""
        
        services = [
            {
                "name": "orchestrator",
                "script": "florida_agent_orchestrator.py",
                "args": "--mode daemon --config config/config_{}.json".format(self.target_env)
            },
            {
                "name": "monitor", 
                "script": "florida_agent_orchestrator.py",
                "args": "--mode dashboard --config config/config_{}.json".format(self.target_env)
            }
        ]
        
        # Create system user for services
        try:
            subprocess.run([
                "useradd", "-r", "-s", "/bin/false", "-d", str(self.deployment_dir), "florida-agent"
            ], check=True)
        except subprocess.CalledProcessError:
            pass  # User might already exist
        
        # Install services
        for service in services:
            service_content = service_template.format(
                service_name=service["name"],
                deployment_dir=self.deployment_dir,
                python_path=sys.executable,
                script_path=self.deployment_dir / "agents" / service["script"],
                args=service["args"]
            )
            
            service_file = Path(f"/etc/systemd/system/florida-agent-{service['name']}.service")
            
            try:
                with open(service_file, 'w') as f:
                    f.write(service_content)
                
                # Reload systemd and enable service
                subprocess.run(["systemctl", "daemon-reload"], check=True)
                subprocess.run(["systemctl", "enable", f"florida-agent-{service['name']}"], check=True)
                
                logger.info(f"Installed systemd service: florida-agent-{service['name']}")
                
            except Exception as e:
                logger.error(f"Failed to install service {service['name']}: {e}")
        
        # Set ownership of deployment directory
        try:
            shutil.chown(self.deployment_dir, user="florida-agent", group="florida-agent")
        except:
            pass

    def install_windows_services(self):
        """Install Windows services"""
        logger.warning("Windows service installation not yet implemented")
        self.create_startup_scripts()

    def create_startup_scripts(self):
        """Create startup scripts for manual service management"""
        logger.info("Creating startup scripts...")
        
        # Create start script
        start_script_content = f"""#!/bin/bash
# Florida Data Agent Startup Script

export PYTHONPATH="{self.deployment_dir}/agents"
export FLORIDA_AGENT_ENV="{self.target_env}"

cd "{self.deployment_dir}"

# Load environment variables
if [ -f "config/.env" ]; then
    source config/.env
fi

echo "Starting Florida Data Agent Orchestrator..."
{sys.executable} agents/florida_agent_orchestrator.py --mode daemon --config config/config_{self.target_env}.json > logs/orchestrator.log 2>&1 &
echo $! > logs/orchestrator.pid

echo "Starting Florida Data Agent Monitor..."
{sys.executable} agents/florida_agent_orchestrator.py --mode dashboard --config config/config_{self.target_env}.json > logs/monitor.log 2>&1 &
echo $! > logs/monitor.pid

echo "Florida Data Agent services started"
echo "Check logs in the logs/ directory"
"""
        
        start_script = self.deployment_dir / "scripts" / "start_agents.sh"
        with open(start_script, 'w') as f:
            f.write(start_script_content.strip())
        
        # Create stop script
        stop_script_content = f"""#!/bin/bash
# Florida Data Agent Stop Script

cd "{self.deployment_dir}"

echo "Stopping Florida Data Agent services..."

if [ -f "logs/orchestrator.pid" ]; then
    kill $(cat logs/orchestrator.pid) 2>/dev/null
    rm -f logs/orchestrator.pid
    echo "Orchestrator stopped"
fi

if [ -f "logs/monitor.pid" ]; then
    kill $(cat logs/monitor.pid) 2>/dev/null
    rm -f logs/monitor.pid
    echo "Monitor stopped"
fi

echo "All services stopped"
"""
        
        stop_script = self.deployment_dir / "scripts" / "stop_agents.sh"
        with open(stop_script, 'w') as f:
            f.write(stop_script_content.strip())
        
        # Make scripts executable
        if platform.system() != "Windows":
            os.chmod(start_script, 0o755)
            os.chmod(stop_script, 0o755)
        
        logger.info("Startup scripts created in scripts/ directory")

    def setup_monitoring(self):
        """Setup monitoring and alerting"""
        logger.info("📊 Setting up monitoring...")
        
        # Create monitoring configuration
        monitoring_config = {
            "dashboards": {
                "grafana_enabled": False,
                "prometheus_enabled": False
            },
            "health_checks": {
                "enabled": True,
                "interval_minutes": 5,
                "endpoints": [
                    "http://localhost:8080/health",
                    "database_connectivity"
                ]
            },
            "log_aggregation": {
                "enabled": True,
                "retention_days": 30
            }
        }
        
        monitoring_config_file = self.deployment_dir / "config" / "monitoring.json"
        with open(monitoring_config_file, 'w') as f:
            json.dump(monitoring_config, f, indent=2)
        
        # Create health check script
        health_check_script = f"""#!/bin/bash
# Florida Data Agent Health Check Script

cd "{self.deployment_dir}"

echo "=== Florida Data Agent Health Check ==="
echo "Timestamp: $(date)"
echo

# Check if processes are running
if pgrep -f "florida_agent_orchestrator.py.*daemon" > /dev/null; then
    echo "✅ Orchestrator: Running"
else
    echo "❌ Orchestrator: Not running"
fi

if pgrep -f "florida_agent_orchestrator.py.*dashboard" > /dev/null; then
    echo "✅ Monitor: Running"
else
    echo "❌ Monitor: Not running"  
fi

# Check log files
echo
echo "=== Recent Log Activity ==="
if [ -f "logs/orchestrator.log" ]; then
    echo "Last 5 lines of orchestrator log:"
    tail -5 logs/orchestrator.log
else
    echo "❌ No orchestrator log found"
fi

echo
echo "=== System Resources ==="
echo "Memory Usage: $(free -h | awk 'NR==2{{printf \"%.1f%%\", $3/$2*100}}')"
echo "Disk Usage: $(df -h {self.deployment_dir} | awk 'NR==2{{print $5}}')"

echo
echo "Health check complete"
"""
        
        health_check_file = self.deployment_dir / "scripts" / "health_check.sh"
        with open(health_check_file, 'w') as f:
            f.write(health_check_script.strip())
        
        if platform.system() != "Windows":
            os.chmod(health_check_file, 0o755)
        
        logger.info("✅ Monitoring setup complete")

    def setup_log_rotation(self):
        """Setup log rotation to prevent disk space issues"""
        logger.info("📝 Setting up log rotation...")
        
        if platform.system() == "Linux":
            logrotate_config = f"""
{self.deployment_dir}/logs/*.log {{
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 florida-agent florida-agent
    postrotate
        # Restart services to use new log files
        systemctl restart florida-agent-orchestrator || true
        systemctl restart florida-agent-monitor || true
    endscript
}}
"""
            
            logrotate_file = Path(f"/etc/logrotate.d/florida-agent")
            try:
                with open(logrotate_file, 'w') as f:
                    f.write(logrotate_config.strip())
                logger.info("Logrotate configuration installed")
            except Exception as e:
                logger.warning(f"Failed to setup logrotate: {e}")
        
        logger.info("✅ Log rotation setup complete")

    def run_health_checks(self):
        """Run health checks to validate deployment"""
        logger.info("🏥 Running health checks...")
        
        checks_passed = 0
        total_checks = 4
        
        # Check 1: Verify files are in place
        required_files = [
            "agents/florida_agent_orchestrator.py",
            "agents/florida_config_manager.py",
            "config/.env"
        ]
        
        for file_path in required_files:
            full_path = self.deployment_dir / file_path
            if full_path.exists():
                checks_passed += 1
                logger.info(f"✅ File check: {file_path}")
            else:
                logger.error(f"❌ File check: {file_path} missing")
        
        # Check 2: Verify Python dependencies
        try:
            sys.path.insert(0, str(self.deployment_dir / "agents"))
            from florida_config_manager import FloridaConfigManager
            checks_passed += 1
            logger.info("✅ Dependency check: Core modules importable")
        except ImportError as e:
            logger.error(f"❌ Dependency check: {e}")
        
        # Check 3: Validate configuration
        try:
            config_file = self.deployment_dir / "config" / f"config_{self.target_env}.json"
            if config_file.exists():
                with open(config_file) as f:
                    config = json.load(f)
                if config.get("orchestrator", {}).get("name"):
                    checks_passed += 1
                    logger.info("✅ Configuration check: Valid configuration file")
                else:
                    logger.error("❌ Configuration check: Invalid configuration structure")
            else:
                logger.error("❌ Configuration check: Configuration file missing")
        except Exception as e:
            logger.error(f"❌ Configuration check: {e}")
        
        # Check 4: Directory permissions
        try:
            test_file = self.deployment_dir / "test_write.tmp"
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            checks_passed += 1
            logger.info("✅ Permissions check: Directory writable")
        except Exception as e:
            logger.error(f"❌ Permissions check: {e}")
        
        success_rate = (checks_passed / total_checks) * 100
        logger.info(f"Health checks: {checks_passed}/{total_checks} passed ({success_rate:.0f}%)")
        
        if checks_passed < total_checks:
            raise ValueError("Health checks failed - deployment may not function correctly")

    def run_smoke_tests(self):
        """Run smoke tests to validate basic functionality"""
        logger.info("💨 Running smoke tests...")
        
        try:
            # Import and test configuration manager
            sys.path.insert(0, str(self.deployment_dir / "agents"))
            from florida_config_manager import FloridaConfigManager
            
            config_manager = FloridaConfigManager(
                str(self.deployment_dir / "config" / f"config_{self.target_env}.json")
            )
            
            config = config_manager.get_config()
            
            if config.get("orchestrator", {}).get("name"):
                logger.info("✅ Smoke test: Configuration manager functional")
            else:
                raise ValueError("Configuration manager returned invalid config")
            
            # Test configuration validation
            is_valid, errors = config_manager.validate_configuration()
            if is_valid:
                logger.info("✅ Smoke test: Configuration validation passed")
            else:
                logger.warning(f"⚠️ Smoke test: Configuration validation warnings: {errors}")
            
            logger.info("✅ Smoke tests completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Smoke test failed: {e}")
            raise ValueError("Smoke tests failed - deployment may not be functional")

    def create_deployment_record(self):
        """Create deployment record for tracking"""
        deployment_record = {
            "deployment_id": f"florida-agents-{self.target_env}-{os.getpid()}",
            "timestamp": str(datetime.now()),
            "environment": self.target_env,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": f"{platform.system()} {platform.release()}",
            "deployment_dir": str(self.deployment_dir),
            "services_installed": self.services,
            "configuration_file": f"config_{self.target_env}.json",
            "status": "completed"
        }
        
        record_file = self.deployment_dir / "deployment_record.json"
        with open(record_file, 'w') as f:
            json.dump(deployment_record, f, indent=2)
        
        logger.info(f"Deployment record created: {record_file}")

    def rollback_deployment(self):
        """Rollback deployment in case of failure"""
        logger.warning("🔄 Initiating deployment rollback...")
        
        try:
            # Stop services if running
            if platform.system() == "Linux":
                for service_name in ["orchestrator", "monitor"]:
                    try:
                        subprocess.run([
                            "systemctl", "stop", f"florida-agent-{service_name}"
                        ], check=False)
                        subprocess.run([
                            "systemctl", "disable", f"florida-agent-{service_name}"
                        ], check=False)
                    except:
                        pass
            
            # Remove deployment directory
            if self.deployment_dir.exists():
                shutil.rmtree(self.deployment_dir)
                logger.info(f"Removed deployment directory: {self.deployment_dir}")
            
            logger.info("✅ Rollback completed")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    def print_deployment_summary(self):
        """Print deployment summary and next steps"""
        summary = f"""
🎉 Florida Data Agent Deployment Summary
========================================

Deployment Environment: {self.target_env}
Deployment Directory: {self.deployment_dir}
Python Version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}

📁 Installed Components:
  • Agent Orchestrator
  • Download Agent  
  • Processing Agent
  • Database Agent
  • Monitoring Agent
  • Configuration Manager

🔧 Configuration Files:
  • Main Config: config/config_{self.target_env}.json
  • Environment: config/.env
  • Monitoring: config/monitoring.json

📜 Management Scripts:
  • Start Services: scripts/start_agents.sh
  • Stop Services: scripts/stop_agents.sh
  • Health Check: scripts/health_check.sh

📊 Log Files:
  • Application Logs: logs/
  • System Logs: /var/log/florida-agent/ (Linux)

🚀 Next Steps:
  1. Update config/.env with your actual Supabase credentials
  2. Review and customize config/config_{self.target_env}.json
  3. Start services: ./scripts/start_agents.sh
  4. Check health: ./scripts/health_check.sh
  5. Monitor logs: tail -f logs/orchestrator.log

📖 Documentation:
  • See README.md for detailed usage instructions
  • Configuration reference in config/ directory
  • Troubleshooting guide in docs/

⚡ Quick Start:
  cd {self.deployment_dir}
  ./scripts/start_agents.sh
  
Happy property data processing! 🏠📊
        """
        
        print(summary)

def main():
    """Main deployment entry point"""
    parser = argparse.ArgumentParser(description="Deploy Florida Data Agent System")
    parser.add_argument("--env", choices=["development", "staging", "production"], 
                       default="production", help="Target environment")
    parser.add_argument("--rollback", action="store_true", 
                       help="Rollback previous deployment")
    
    args = parser.parse_args()
    
    deployment = FloridaAgentDeployment(args.env)
    
    if args.rollback:
        deployment.rollback_deployment()
    else:
        deployment.deploy()

if __name__ == "__main__":
    main()