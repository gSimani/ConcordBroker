"""
Start pipeline orchestrator in background mode
"""

import subprocess
import sys
import os
import time
import psutil

def start_pipeline_background():
    """Start the pipeline orchestrator as a background process"""
    
    # Check if already running
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and 'start_pipeline.py' in str(cmdline):
                print(f"[INFO] Pipeline orchestrator already running (PID: {proc.info['pid']})")
                return proc.info['pid']
        except:
            pass
    
    print("[INFO] Starting pipeline orchestrator in background...")
    
    # Start the orchestrator in background
    if os.name == 'nt':  # Windows
        process = subprocess.Popen(
            [sys.executable, 'start_pipeline.py'],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
            stdout=open('pipeline.log', 'w'),
            stderr=subprocess.STDOUT
        )
    else:  # Unix/Linux
        process = subprocess.Popen(
            [sys.executable, 'start_pipeline.py'],
            stdout=open('pipeline.log', 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    
    print(f"[SUCCESS] Pipeline orchestrator started (PID: {process.pid})")
    print("[INFO] Logs are being written to pipeline.log")
    
    # Wait a moment for it to start
    time.sleep(3)
    
    # Check if it's still running
    if process.poll() is None:
        print("[SUCCESS] Pipeline orchestrator is running")
        return process.pid
    else:
        print("[ERROR] Pipeline orchestrator failed to start")
        return None

if __name__ == "__main__":
    pid = start_pipeline_background()
    if pid:
        print(f"\nPipeline orchestrator is running with PID: {pid}")
        print("To check status: python check_pipeline_status.py")
        print("To stop: python stop_pipeline.py")
        print("To view logs: tail -f pipeline.log")