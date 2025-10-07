"""
Backup Management API
Web-based control for daily backup system
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import subprocess
import json
import os
from pathlib import Path
import logging
from typing import Optional
import asyncio
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Backup Management API",
    description="Control and monitor Supabase daily backups",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://concordbroker.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration paths
BACKUP_CONFIG_FILE = Path("C:/TEMP/SUPABASE_BACKUPS/backup_config.json")
BACKUP_BASE_DIR = Path("C:/TEMP/SUPABASE_BACKUPS")
BACKUP_SCRIPT = Path(__file__).parent.parent.parent / "daily_supabase_backup.py"
BACKUP_LOG = Path("backup.log")

# Simple API key authentication
API_KEY = "concordbroker-backup-key-2025"

class BackupStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    RUNNING = "running"
    ERROR = "error"

class BackupConfig(BaseModel):
    enabled: bool
    schedule_time: str = "02:00"  # 24-hour format
    retention_days: int = 30
    last_backup: Optional[str] = None
    next_backup: Optional[str] = None
    status: BackupStatus = BackupStatus.DISABLED

class BackupToggle(BaseModel):
    enabled: bool

class BackupStats(BaseModel):
    total_backups: int
    total_size_gb: float
    last_backup_date: Optional[str]
    last_backup_size_mb: Optional[float]
    next_scheduled: Optional[str]
    status: BackupStatus

def verify_api_key(x_api_key: str = Header(None)):
    """Verify API key for authentication"""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

def load_config() -> BackupConfig:
    """Load backup configuration from file"""
    if not BACKUP_CONFIG_FILE.exists():
        # Create default config
        default_config = BackupConfig(
            enabled=False,
            schedule_time="02:00",
            retention_days=30,
            status=BackupStatus.DISABLED
        )
        save_config(default_config)
        return default_config

    try:
        with open(BACKUP_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return BackupConfig(**data)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return BackupConfig(enabled=False, status=BackupStatus.ERROR)

def save_config(config: BackupConfig):
    """Save backup configuration to file"""
    BACKUP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKUP_CONFIG_FILE, 'w') as f:
        json.dump(config.dict(), f, indent=2, default=str)

def update_windows_task(config: BackupConfig):
    """Update Windows Task Scheduler based on config"""
    task_name = "Supabase Daily Backup"

    try:
        if config.enabled:
            # Create or update scheduled task
            cmd = [
                'schtasks', '/create',
                '/tn', task_name,
                '/tr', f'python "{BACKUP_SCRIPT}"',
                '/sc', 'daily',
                '/st', config.schedule_time,
                '/f',
                '/rl', 'highest'
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Task scheduler updated: enabled at {config.schedule_time}")
                return True
            else:
                logger.error(f"Failed to update task: {result.stderr}")
                return False
        else:
            # Disable scheduled task
            cmd = ['schtasks', '/change', '/tn', task_name, '/disable']
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info("Task scheduler disabled")
                return True
            else:
                # Try to delete if disable fails
                cmd_delete = ['schtasks', '/delete', '/tn', task_name, '/f']
                subprocess.run(cmd_delete, capture_output=True)
                logger.info("Task scheduler removed")
                return True

    except Exception as e:
        logger.error(f"Error updating Windows task: {e}")
        return False

async def run_backup_async():
    """Run backup script asynchronously"""
    try:
        process = await asyncio.create_subprocess_exec(
            'python', str(BACKUP_SCRIPT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info("Backup completed successfully")
            return True, stdout.decode()
        else:
            logger.error(f"Backup failed: {stderr.decode()}")
            return False, stderr.decode()

    except Exception as e:
        logger.error(f"Error running backup: {e}")
        return False, str(e)

def get_backup_stats() -> BackupStats:
    """Get backup statistics"""
    try:
        # Count backups and calculate total size
        backup_dirs = [d for d in BACKUP_BASE_DIR.iterdir()
                      if d.is_dir() and d.name.startswith('backup_')]

        total_size_bytes = 0
        last_backup_date = None
        last_backup_size = None

        if backup_dirs:
            # Sort by date
            backup_dirs.sort(key=lambda x: x.name, reverse=True)

            # Get latest backup info
            latest_dir = backup_dirs[0]
            last_backup_date = latest_dir.name.replace('backup_', '')

            # Calculate size of latest backup
            latest_size = sum(f.stat().st_size for f in latest_dir.glob('**/*') if f.is_file())
            last_backup_size = latest_size / (1024 * 1024)  # Convert to MB

            # Calculate total size
            for backup_dir in backup_dirs:
                for file in backup_dir.glob('**/*'):
                    if file.is_file():
                        total_size_bytes += file.stat().st_size

        total_size_gb = total_size_bytes / (1024 ** 3)

        # Get next scheduled time
        config = load_config()
        next_scheduled = None
        if config.enabled:
            now = datetime.now()
            scheduled_time = datetime.strptime(config.schedule_time, "%H:%M").time()
            next_run = datetime.combine(now.date(), scheduled_time)
            if next_run < now:
                next_run += timedelta(days=1)
            next_scheduled = next_run.isoformat()

        return BackupStats(
            total_backups=len(backup_dirs),
            total_size_gb=round(total_size_gb, 2),
            last_backup_date=last_backup_date,
            last_backup_size_mb=round(last_backup_size, 2) if last_backup_size else None,
            next_scheduled=next_scheduled,
            status=config.status
        )

    except Exception as e:
        logger.error(f"Error getting backup stats: {e}")
        return BackupStats(
            total_backups=0,
            total_size_gb=0,
            last_backup_date=None,
            last_backup_size_mb=None,
            next_scheduled=None,
            status=BackupStatus.ERROR
        )

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Backup Management API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/backup/config", response_model=BackupConfig)
async def get_backup_config(api_key: str = Depends(verify_api_key)):
    """Get current backup configuration"""
    return load_config()

@app.post("/api/backup/toggle")
async def toggle_backup(
    toggle: BackupToggle,
    api_key: str = Depends(verify_api_key)
):
    """Toggle daily backup on/off"""
    config = load_config()
    config.enabled = toggle.enabled

    # Update Windows Task Scheduler
    success = update_windows_task(config)

    if success:
        config.status = BackupStatus.ENABLED if toggle.enabled else BackupStatus.DISABLED
        if toggle.enabled:
            # Calculate next backup time
            now = datetime.now()
            scheduled_time = datetime.strptime(config.schedule_time, "%H:%M").time()
            next_run = datetime.combine(now.date(), scheduled_time)
            if next_run < now:
                next_run += timedelta(days=1)
            config.next_backup = next_run.isoformat()
    else:
        config.status = BackupStatus.ERROR

    save_config(config)

    return {
        "success": success,
        "enabled": config.enabled,
        "status": config.status,
        "message": f"Daily backup {'enabled' if toggle.enabled else 'disabled'} successfully"
    }

@app.put("/api/backup/config")
async def update_backup_config(
    new_config: BackupConfig,
    api_key: str = Depends(verify_api_key)
):
    """Update backup configuration"""
    # Update Windows Task if schedule changed
    if new_config.enabled:
        success = update_windows_task(new_config)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update task scheduler")

    save_config(new_config)

    return {
        "success": True,
        "message": "Configuration updated successfully",
        "config": new_config
    }

@app.post("/api/backup/run")
async def run_backup_now(
    background_tasks: BackgroundTasks,
    api_key: str = Depends(verify_api_key)
):
    """Trigger backup immediately"""
    config = load_config()

    # Check if backup is already running
    if config.status == BackupStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Backup is already running")

    # Update status
    config.status = BackupStatus.RUNNING
    save_config(config)

    # Run backup in background
    async def run_and_update():
        success, output = await run_backup_async()

        # Update config with results
        config = load_config()
        if success:
            config.status = BackupStatus.ENABLED if config.enabled else BackupStatus.DISABLED
            config.last_backup = datetime.now().isoformat()
        else:
            config.status = BackupStatus.ERROR

        save_config(config)

    background_tasks.add_task(run_and_update)

    return {
        "success": True,
        "message": "Backup started in background",
        "status": BackupStatus.RUNNING
    }

@app.get("/api/backup/stats", response_model=BackupStats)
async def get_backup_stats_endpoint(api_key: str = Depends(verify_api_key)):
    """Get backup statistics and status"""
    return get_backup_stats()

@app.get("/api/backup/logs")
async def get_backup_logs(
    lines: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """Get recent backup logs"""
    try:
        if not BACKUP_LOG.exists():
            return {"logs": [], "message": "No logs available"}

        with open(BACKUP_LOG, 'r') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

        return {
            "logs": recent_lines,
            "total_lines": len(all_lines),
            "returned_lines": len(recent_lines)
        }

    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to read logs")

@app.delete("/api/backup/cleanup")
async def cleanup_old_backups(
    days: int = 30,
    api_key: str = Depends(verify_api_key)
):
    """Manually cleanup backups older than specified days"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for backup_dir in BACKUP_BASE_DIR.iterdir():
            if backup_dir.is_dir() and backup_dir.name.startswith('backup_'):
                try:
                    date_str = backup_dir.name.replace('backup_', '')
                    backup_date = datetime.strptime(date_str, '%Y-%m-%d')

                    if backup_date < cutoff_date:
                        import shutil
                        shutil.rmtree(backup_dir)
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {backup_dir.name}")

                except ValueError:
                    logger.warning(f"Could not parse backup date from: {backup_dir.name}")

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Deleted {deleted_count} backups older than {days} days"
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Cleanup failed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)