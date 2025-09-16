#!/usr/bin/env python3
"""
Florida Daily Updates Setup Script
Initializes the Florida property data update system with all necessary
directories, permissions, and initial configuration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import yaml
import json
import platform
import getpass
from typing import Dict, Any, List

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("Florida Property Data Daily Update System")
    print("Setup and Installation Script")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version compatibility"""
    print("Checking Python version...")
    
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]} (compatible)")

def check_system_requirements():
    """Check system requirements"""
    print("\\nChecking system requirements...")
    
    # Check operating system
    os_name = platform.system()
    print(f"Operating System: {os_name}")
    
    if os_name not in ['Windows', 'Linux', 'Darwin']:
        print("⚠️  Warning: Untested operating system")
    
    # Check available disk space
    try:
        statvfs = os.statvfs('.')
        free_space_gb = (statvfs.f_frsize * statvfs.f_bavail) / (1024**3)
        print(f"Available disk space: {free_space_gb:.1f} GB")
        
        if free_space_gb < 5:
            print("⚠️  Warning: Less than 5 GB free space available")
            print("   Recommended: At least 10 GB for data storage")
    except:
        print("Could not check disk space")
    
    print("✅ System requirements check completed")

def create_directories():
    """Create necessary directories"""
    print("\\nCreating directory structure...")
    
    directories = [
        "florida_daily_updates/data/downloads",
        "florida_daily_updates/data/temp", 
        "florida_daily_updates/data/processed",
        "florida_daily_updates/data/backups",
        "florida_daily_updates/logs",
        "florida_daily_updates/scripts",
        "florida_daily_updates/config",
        "florida_daily_updates/agents"
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {directory}")
    
    print("✅ Directory structure created")

def install_python_dependencies():
    """Install Python dependencies"""
    print("\\nInstalling Python dependencies...")
    
    requirements = [
        "pyyaml>=6.0",
        "aiohttp>=3.8.0",
        "aiofiles>=23.0.0",
        "asyncpg>=0.28.0",
        "pandas>=2.0.0",
        "sqlalchemy>=2.0.0",
        "rich>=13.0.0",
        "python-crontab>=3.0.0",
        "schedule>=1.2.0",
        "beautifulsoup4>=4.12.0",
        "requests>=2.31.0",
        "supabase>=2.0.0"
    ]
    
    for requirement in requirements:
        try:
            print(f"  Installing {requirement}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", requirement
            ], check=True, capture_output=True, text=True)
            print(f"  ✅ Installed {requirement}")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install {requirement}: {e}")
            print("  You may need to install this manually")
    
    print("✅ Python dependencies installation completed")

def create_config_files():
    """Create configuration files if they don't exist"""
    print("\\nCreating configuration files...")
    
    config_dir = Path("florida_daily_updates/config")
    
    # Check if main config exists
    main_config = config_dir / "config.yaml"
    if not main_config.exists():
        print("  ❌ Main configuration file not found")
        print(f"     Expected: {main_config}")
        print("     Please ensure all agent files are properly copied")
        return False
    
    # Create environment-specific configs
    environments = ['development', 'staging', 'production']
    
    for env in environments:
        env_config = config_dir / f"config.{env}.yaml"
        if not env_config.exists():
            env_overrides = {
                'system': {
                    'environment': env,
                    'log_level': 'DEBUG' if env == 'development' else 'INFO'
                },
                'development' if env == 'development' else 'production': {
                    'enabled': True
                }
            }
            
            with open(env_config, 'w') as f:
                yaml.dump(env_overrides, f, default_flow_style=False)
            
            print(f"  Created: config.{env}.yaml")
    
    print("✅ Configuration files created")
    return True

def setup_environment_variables():
    """Setup environment variables"""
    print("\\nSetting up environment variables...")
    
    env_file = Path(".env")
    env_vars = {}
    
    # Load existing .env if it exists
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Required environment variables
    required_vars = [
        ('SUPABASE_URL', 'Supabase project URL'),
        ('SUPABASE_ANON_KEY', 'Supabase anonymous key'),
        ('SUPABASE_SERVICE_KEY', 'Supabase service role key'),
        ('SUPABASE_DB_URL', 'Direct Supabase database URL (postgresql://...)')
    ]
    
    # Optional environment variables
    optional_vars = [
        ('EMAIL_USERNAME', 'Email username for notifications'),
        ('EMAIL_PASSWORD', 'Email password for notifications'),
        ('SLACK_WEBHOOK_URL', 'Slack webhook URL for notifications'),
        ('ENCRYPTION_KEY', 'Encryption key for sensitive data')
    ]
    
    # Prompt for required variables
    for var_name, description in required_vars:
        if var_name not in env_vars or not env_vars[var_name]:
            value = getpass.getpass(f"Enter {description} ({var_name}): ")
            if value:
                env_vars[var_name] = value
    
    # Prompt for optional variables
    print("\\nOptional configuration (press Enter to skip):")
    for var_name, description in optional_vars:
        if var_name not in env_vars or not env_vars[var_name]:
            value = input(f"Enter {description} ({var_name}): ").strip()
            if value:
                env_vars[var_name] = value
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# Florida Daily Updates Environment Variables\\n")
        f.write(f"# Generated on {os.popen('date').read().strip()}\\n")
        f.write("\\n")
        
        for var_name, value in env_vars.items():
            f.write(f"{var_name}={value}\\n")
    
    print(f"✅ Environment variables saved to {env_file}")
    print("   Make sure to add .env to your .gitignore file!")

def setup_scheduling():
    """Setup scheduling based on operating system"""
    print("\\nSetting up scheduling...")
    
    os_name = platform.system()
    
    if os_name == "Windows":
        setup_windows_scheduling()
    elif os_name in ["Linux", "Darwin"]:
        setup_unix_scheduling()
    else:
        print("⚠️  Manual scheduling setup required for this OS")
        print("   Please refer to the documentation for manual setup")

def setup_windows_scheduling():
    """Setup Windows Task Scheduler"""
    print("  Setting up Windows Task Scheduler...")
    
    # Create PowerShell script for task scheduling
    script_content = '''
# Florida Daily Updates - Windows Task Scheduler Setup
# Run this script as Administrator

$TaskName = "Florida-Daily-Updates"
$ScriptPath = "{script_path}"
$LogPath = "{log_path}"

# Delete existing task if it exists
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create new scheduled task
$Action = New-ScheduledTaskAction -Execute "python" -Argument "`"$ScriptPath`" --mode full" -WorkingDirectory (Split-Path $ScriptPath)
$Trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings

Write-Host "Task '$TaskName' created successfully"
Write-Host "The task will run daily at 2:00 AM"
Write-Host ""
Write-Host "To manage the task:"
Write-Host "  View: Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Run:  Start-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Stop: Stop-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Delete: Unregister-ScheduledTask -TaskName '$TaskName'"
'''.format(
        script_path=Path("florida_daily_updates/scripts/run_daily_update.py").absolute(),
        log_path=Path("florida_daily_updates/logs").absolute()
    )
    
    # Write PowerShell script
    ps_script = Path("florida_daily_updates/scripts/setup_windows_scheduler.ps1")
    with open(ps_script, 'w') as f:
        f.write(script_content)
    
    print(f"  Created: {ps_script}")
    print("  ⚠️  Run the PowerShell script as Administrator to create the scheduled task")
    
    # Create batch file for easy execution
    batch_content = f'''@echo off
cd /d "{Path.cwd()}"
python florida_daily_updates/scripts/run_daily_update.py --mode full
pause
'''
    
    batch_file = Path("florida_daily_updates/scripts/run_update.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"  Created: {batch_file}")

def setup_unix_scheduling():
    """Setup Unix/Linux cron scheduling"""
    print("  Setting up cron scheduling...")
    
    try:
        from crontab import CronTab
        
        # Get current user's crontab
        cron = CronTab(user=True)
        
        # Remove existing Florida update jobs
        cron.remove_all(comment='Florida Daily Updates')
        
        # Add daily update job
        job = cron.new(
            command=f'{sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode full',
            comment='Florida Daily Updates'
        )
        job.setall('0 2 * * *')  # Daily at 2 AM
        
        # Add monitoring job  
        monitor_job = cron.new(
            command=f'{sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode monitor',
            comment='Florida Daily Updates Monitor'
        )
        monitor_job.setall('0 */6 * * *')  # Every 6 hours
        
        # Add maintenance job
        maintenance_job = cron.new(
            command=f'{sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode maintenance',
            comment='Florida Daily Updates Maintenance'
        )
        maintenance_job.setall('0 3 * * 0')  # Weekly on Sunday at 3 AM
        
        # Write crontab
        cron.write()
        
        print("  ✅ Cron jobs created:")
        print("    - Daily update: 0 2 * * * (2 AM daily)")
        print("    - Monitoring: 0 */6 * * * (every 6 hours)")
        print("    - Maintenance: 0 3 * * 0 (Sunday 3 AM)")
        
    except ImportError:
        print("  python-crontab not available, creating manual cron setup")
        
        cron_content = f'''# Florida Daily Updates Cron Jobs
# Add these lines to your crontab with: crontab -e

# Daily update at 2 AM
0 2 * * * {sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode full

# Monitor every 6 hours
0 */6 * * * {sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode monitor

# Maintenance weekly on Sunday at 3 AM  
0 3 * * 0 {sys.executable} {Path("florida_daily_updates/scripts/run_daily_update.py").absolute()} --mode maintenance
'''
        
        cron_file = Path("florida_daily_updates/scripts/crontab.txt")
        with open(cron_file, 'w') as f:
            f.write(cron_content)
        
        print(f"  Created: {cron_file}")
        print("  Run 'crontab florida_daily_updates/scripts/crontab.txt' to install cron jobs")

def create_service_scripts():
    """Create service management scripts"""
    print("\\nCreating service management scripts...")
    
    os_name = platform.system()
    scripts_dir = Path("florida_daily_updates/scripts")
    
    if os_name == "Windows":
        # Windows service scripts
        start_script = scripts_dir / "start_service.bat"
        with open(start_script, 'w') as f:
            f.write(f'''@echo off
echo Starting Florida Daily Updates Service...
cd /d "{Path.cwd()}"
python florida_daily_updates/scripts/run_daily_update.py --mode full
''')
        
        stop_script = scripts_dir / "stop_service.bat" 
        with open(stop_script, 'w') as f:
            f.write('''@echo off
echo Stopping Florida Daily Updates Service...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Florida*"
echo Service stopped.
''')
        
        print(f"  Created: {start_script}")
        print(f"  Created: {stop_script}")
        
    else:
        # Unix service scripts
        start_script = scripts_dir / "start_service.sh"
        with open(start_script, 'w') as f:
            f.write(f'''#!/bin/bash
# Florida Daily Updates Service Start Script

cd "{Path.cwd()}"
echo "Starting Florida Daily Updates Service..."

# Run the daily update
python florida_daily_updates/scripts/run_daily_update.py --mode full

echo "Service execution completed."
''')
        
        stop_script = scripts_dir / "stop_service.sh"
        with open(stop_script, 'w') as f:
            f.write('''#!/bin/bash
# Florida Daily Updates Service Stop Script

echo "Stopping Florida Daily Updates Service..."

# Find and kill running processes
pkill -f "run_daily_update.py"

echo "Service stopped."
''')
        
        # Make scripts executable
        os.chmod(start_script, 0o755)
        os.chmod(stop_script, 0o755)
        
        print(f"  Created: {start_script}")
        print(f"  Created: {stop_script}")

def run_initial_test():
    """Run initial test to verify setup"""
    print("\\nRunning initial test...")
    
    try:
        # Test configuration loading
        config_file = Path("florida_daily_updates/config/config.yaml")
        if not config_file.exists():
            print("  ❌ Configuration file not found")
            return False
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        print("  ✅ Configuration file loaded successfully")
        
        # Test environment variables
        required_env_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY', 'SUPABASE_SERVICE_KEY']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"  ⚠️  Missing environment variables: {', '.join(missing_vars)}")
            print("     Set these in your .env file or system environment")
        else:
            print("  ✅ Required environment variables found")
        
        # Test imports
        try:
            sys.path.insert(0, str(Path("florida_daily_updates").absolute()))
            from agents.monitor import FloridaDataMonitor
            print("  ✅ Agent modules can be imported")
        except ImportError as e:
            print(f"  ❌ Import error: {e}")
            return False
        
        print("\\n✅ Initial test completed successfully")
        return True
        
    except Exception as e:
        print(f"  ❌ Test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for user"""
    print("\\n" + "=" * 60)
    print("Setup completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print()
    print("1. Configure environment variables:")
    print("   - Edit the .env file with your Supabase credentials")
    print("   - Or set environment variables in your system")
    print()
    print("2. Test the system:")
    print("   python florida_daily_updates/scripts/run_daily_update.py --mode test")
    print()
    print("3. Run a manual update:")
    print("   python florida_daily_updates/scripts/run_daily_update.py --mode full")
    print()
    print("4. Enable scheduling:")
    
    if platform.system() == "Windows":
        print("   - Run setup_windows_scheduler.ps1 as Administrator")
        print("   - Or use run_update.bat for manual execution")
    else:
        print("   - Cron jobs should be automatically configured")
        print("   - Check with: crontab -l")
    
    print()
    print("5. Monitor logs:")
    print("   - Check florida_daily_updates/logs/ for execution logs")
    print("   - Monitor database for successful data updates")
    print()
    print("For troubleshooting, check the logs and ensure:")
    print("- Internet connectivity to floridarevenue.com")
    print("- Supabase database access")
    print("- Sufficient disk space (10+ GB recommended)")
    print()
    print("Documentation and support:")
    print("- Configuration: florida_daily_updates/config/config.yaml")
    print("- Schedules: florida_daily_updates/config/schedules.json")
    print("- Counties: florida_daily_updates/config/counties.json")

def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Run setup steps
        check_python_version()
        check_system_requirements()
        create_directories()
        
        # Install dependencies
        install_deps = input("\\nInstall Python dependencies? (y/N): ").strip().lower()
        if install_deps in ['y', 'yes']:
            install_python_dependencies()
        
        # Setup configuration
        if not create_config_files():
            print("❌ Configuration setup failed")
            print("Please ensure all system files are properly copied")
            sys.exit(1)
        
        # Setup environment
        setup_env = input("\\nSetup environment variables? (y/N): ").strip().lower()
        if setup_env in ['y', 'yes']:
            setup_environment_variables()
        
        # Setup scheduling
        setup_sched = input("\\nSetup automated scheduling? (y/N): ").strip().lower()
        if setup_sched in ['y', 'yes']:
            setup_scheduling()
        
        create_service_scripts()
        
        # Run test
        run_test = input("\\nRun initial test? (y/N): ").strip().lower()
        if run_test in ['y', 'yes']:
            if not run_initial_test():
                print("⚠️  Initial test had issues - please review the configuration")
        
        print_next_steps()
        
    except KeyboardInterrupt:
        print("\\n\\nSetup cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()