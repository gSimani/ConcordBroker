"""
Live download monitor with progress bar and continuous updates
"""

import sys
import io
import json
import time
from pathlib import Path
from datetime import datetime
import os

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def draw_progress_bar(percentage, width=50):
    """Draw a progress bar"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f'[{bar}] {percentage:.1f}%'

def format_size(bytes_value):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024
    return f"{bytes_value:.1f} TB"

def calculate_eta(downloaded, total, speed_bps):
    """Calculate estimated time remaining"""
    if speed_bps <= 0:
        return "Unknown"
    
    remaining_bytes = total - downloaded
    eta_seconds = remaining_bytes / speed_bps
    
    if eta_seconds < 60:
        return f"{eta_seconds:.0f}s"
    elif eta_seconds < 3600:
        return f"{eta_seconds/60:.0f}m {eta_seconds%60:.0f}s"
    else:
        hours = eta_seconds // 3600
        minutes = (eta_seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"

def live_monitor():
    """Live monitoring with updates"""
    
    print("=" * 70)
    print("🔄 LIVE DOWNLOAD MONITOR - CORPRINDATA.ZIP")
    print("=" * 70)
    print("Press Ctrl+C to stop monitoring\n")
    
    # File paths
    local_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\corprindata.zip")
    progress_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\download_progress.json")
    
    expected_size = 665.8 * 1024 * 1024  # 665.8 MB in bytes
    last_size = 0
    last_time = time.time()
    speed_history = []
    
    try:
        while True:
            # Clear previous line
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 70)
            print("🔄 LIVE DOWNLOAD MONITOR - CORPRINDATA.ZIP")
            print("=" * 70)
            print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | Press Ctrl+C to stop\n")
            
            # Check file size
            current_size = 0
            file_exists = local_file.exists()
            
            if file_exists:
                current_size = local_file.stat().st_size
                
            # Calculate progress
            percentage = (current_size / expected_size) * 100 if expected_size > 0 else 0
            
            # Calculate speed
            current_time = time.time()
            time_diff = current_time - last_time
            size_diff = current_size - last_size
            
            if time_diff > 0 and size_diff >= 0:
                speed_bps = size_diff / time_diff
                speed_history.append(speed_bps)
                
                # Keep only last 10 measurements for average
                if len(speed_history) > 10:
                    speed_history.pop(0)
                
                avg_speed = sum(speed_history) / len(speed_history) if speed_history else 0
            else:
                avg_speed = 0
            
            # Update for next iteration
            last_size = current_size
            last_time = current_time
            
            # Display progress
            print("📦 FILE STATUS:")
            print("-" * 70)
            
            if file_exists:
                print(f"📄 File: corprindata.zip")
                print(f"📊 Size: {format_size(current_size)} / {format_size(expected_size)}")
                
                # Progress bar
                progress_bar = draw_progress_bar(percentage, 50)
                print(f"📈 Progress: {progress_bar}")
                
                # Speed and ETA
                if avg_speed > 0:
                    speed_text = format_size(avg_speed) + "/s"
                    eta_text = calculate_eta(current_size, expected_size, avg_speed)
                    print(f"🚀 Speed: {speed_text} | ⏱️ ETA: {eta_text}")
                else:
                    print("🚀 Speed: Calculating... | ⏱️ ETA: Calculating...")
                
                # Status
                if percentage >= 100:
                    print("\n🎉 DOWNLOAD COMPLETE! 🎉")
                    print("✅ Ready to process!")
                    print("Run: python process_corprindata.py")
                    break
                elif percentage >= 99:
                    print("\n🔥 Almost there! Final bytes downloading...")
                elif percentage >= 90:
                    print("\n⚡ In the final stretch!")
                elif percentage >= 75:
                    print("\n💪 Three quarters done!")
                elif percentage >= 50:
                    print("\n🎯 Halfway there!")
                elif percentage >= 25:
                    print("\n📈 Quarter way through!")
                else:
                    print("\n🚀 Download in progress...")
                    
            else:
                print("❌ File not found - download not started or failed")
                print("Run: python download_corprindata_background.py")
                break
            
            # Check progress file for additional info
            if progress_file.exists():
                try:
                    with open(progress_file, 'r') as f:
                        progress = json.load(f)
                    
                    print(f"\n📊 DETAILED INFO:")
                    print("-" * 70)
                    print(f"Status: {progress['status']}")
                    
                    # Check if stalled
                    try:
                        last_update = datetime.fromisoformat(progress['timestamp'])
                        minutes_since = (datetime.now() - last_update).total_seconds() / 60
                        
                        if minutes_since > 2:
                            print(f"⚠️ No updates for {minutes_since:.1f} minutes")
                        else:
                            print(f"✅ Active - last update {minutes_since:.1f}m ago")
                    except:
                        pass
                        
                except:
                    pass
            
            # Instructions
            print(f"\n💡 WHAT'S NEXT:")
            print("-" * 70)
            if percentage >= 100:
                print("1. Run: python process_corprindata.py")
                print("2. This will extract all officer emails")
                print("3. Creates searchable database with contact info")
            else:
                remaining_mb = (expected_size - current_size) / (1024 * 1024)
                print(f"⏳ Waiting for download to complete ({remaining_mb:.1f} MB remaining)")
                print("📧 This file contains ALL Florida business officer emails!")
                print("🎯 We'll extract thousands of email addresses!")
            
            # Wait before next update
            if percentage < 100:
                time.sleep(2)  # Update every 2 seconds
            else:
                break
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped by user")
        print("Download continues in background")
        print("Run this script again to resume monitoring")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")

if __name__ == "__main__":
    live_monitor()