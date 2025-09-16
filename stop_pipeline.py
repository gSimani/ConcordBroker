"""
Stop the pipeline orchestrator
"""

import psutil
import os
import signal
import time

def stop_pipeline():
    """Stop the pipeline orchestrator process"""
    
    found = False
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if cmdline and 'start_pipeline.py' in str(cmdline):
                pid = proc.info['pid']
                print(f"[INFO] Found pipeline orchestrator (PID: {pid})")
                
                # Terminate the process
                if os.name == 'nt':  # Windows
                    os.kill(pid, signal.SIGTERM)
                else:  # Unix/Linux
                    os.kill(pid, signal.SIGTERM)
                
                print(f"[INFO] Sent termination signal to PID {pid}")
                
                # Wait for process to terminate
                time.sleep(2)
                
                # Check if still running
                if proc.is_running():
                    print(f"[WARNING] Process still running, forcing kill...")
                    proc.kill()
                    time.sleep(1)
                
                if not proc.is_running():
                    print(f"[SUCCESS] Pipeline orchestrator stopped")
                else:
                    print(f"[ERROR] Failed to stop pipeline orchestrator")
                    
                found = True
                break
                
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        except Exception as e:
            print(f"[ERROR] Error checking process: {e}")
    
    if not found:
        print("[INFO] Pipeline orchestrator is not running")
    
    return not found

if __name__ == "__main__":
    stop_pipeline()