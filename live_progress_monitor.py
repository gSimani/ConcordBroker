"""
Live progress monitor for quarterly download with percentage and ETA
"""

import sys
import io
import os
import time
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def monitor_download():
    """Live monitor of quarterly download progress"""
    
    file_path = r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\cordata_quarterly.zip"
    expected_size = 1639.0 * 1024 * 1024  # 1639 MB in bytes
    
    print("=" * 75)
    print("LIVE QUARTERLY DOWNLOAD MONITOR")
    print("=" * 75)
    print("Real-time progress tracking | Press Ctrl+C to stop\\n")
    
    last_size = 0
    last_time = time.time()
    start_time = time.time()
    speeds = []
    
    try:
        while True:
            if os.path.exists(file_path):
                current_size = os.path.getsize(file_path)
                current_mb = current_size / (1024 * 1024)
                expected_mb = expected_size / (1024 * 1024)
                progress = (current_size / expected_size) * 100
                
                # Calculate speed
                current_time = time.time()
                time_diff = current_time - last_time
                size_diff = current_size - last_size
                
                if time_diff > 0 and size_diff > 0:
                    speed_bps = size_diff / time_diff
                    speed_mbps = speed_bps / (1024 * 1024)
                    speeds.append(speed_mbps)
                    
                    # Keep last 10 measurements
                    if len(speeds) > 10:
                        speeds.pop(0)
                
                # Average speed
                avg_speed = sum(speeds) / len(speeds) if speeds else 0
                
                # ETA calculation
                remaining_mb = expected_mb - current_mb
                eta_minutes = remaining_mb / avg_speed / 60 if avg_speed > 0 else 0
                
                # Progress bar
                bar_width = 50
                filled = int(bar_width * progress / 100)
                bar = '█' * filled + '░' * (bar_width - filled)
                
                # Display
                timestamp = datetime.now().strftime('%H:%M:%S')
                print(f"\\r⏰ {timestamp} | Progress: [{bar}] {progress:.1f}%", end="")
                print(f" | {current_mb:.0f}/{expected_mb:.0f} MB", end="")
                if avg_speed > 0:
                    print(f" | {avg_speed:.1f} MB/s | ETA: {eta_minutes:.0f}m", end="")
                else:
                    print(" | Calculating speed...", end="")
                
                # Update tracking
                last_size = current_size
                last_time = current_time
                
                # Check completion
                if progress >= 100:
                    total_time = time.time() - start_time
                    print(f"\\n\\n🎉 DOWNLOAD COMPLETE!")
                    print(f"⏱️ Total time: {total_time/60:.1f} minutes")
                    print(f"🎯 Ready for email extraction!")
                    break
                    
            else:
                print(f"\\r❌ File not found: {file_path}", end="")
            
            time.sleep(2)  # Update every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\\n\\n⏹️ Monitoring stopped")
        if os.path.exists(file_path):
            current_mb = os.path.getsize(file_path) / (1024 * 1024)
            progress = (current_mb / expected_mb) * 100
            print(f"📊 Current progress: {current_mb:.1f} MB ({progress:.1f}%)")

if __name__ == "__main__":
    monitor_download()