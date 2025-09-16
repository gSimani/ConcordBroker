"""
Live progress monitor for the 1.6GB quarterly data download
Shows real-time progress bar with percentage completion
"""

import sys
import io
import time
from pathlib import Path
from datetime import datetime
import os

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def draw_progress_bar(percentage, width=60):
    """Draw a detailed progress bar"""
    filled = int(width * percentage / 100)
    bar = '█' * filled + '░' * (width - filled)
    return f'[{bar}] {percentage:.2f}%'

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
        return "Calculating..."
    
    remaining_bytes = total - downloaded
    eta_seconds = remaining_bytes / speed_bps
    
    if eta_seconds < 60:
        return f"{eta_seconds:.0f} seconds"
    elif eta_seconds < 3600:
        minutes = eta_seconds // 60
        seconds = eta_seconds % 60
        return f"{minutes:.0f}m {seconds:.0f}s"
    else:
        hours = eta_seconds // 3600
        minutes = (eta_seconds % 3600) // 60
        return f"{hours:.0f}h {minutes:.0f}m"

def live_quarterly_monitor():
    """Live monitoring of 1.6GB quarterly download"""
    
    print("=" * 85)
    print("📥 LIVE MONITOR: 1.6GB QUARTERLY DATA DOWNLOAD")
    print("=" * 85)
    print("Real-time progress tracking | Press Ctrl+C to stop monitoring\n")
    
    # File to monitor
    quarterly_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\cordata_quarterly.zip")
    expected_size = 1639.0 * 1024 * 1024  # 1639 MB in bytes
    
    # Tracking variables
    last_size = 0
    last_time = time.time()
    speed_history = []
    start_time = time.time()
    
    try:
        update_count = 0
        while True:
            # Clear screen for live updates
            if update_count > 0:
                # Move cursor up and clear lines
                print('\033[8A', end='')  # Move up 8 lines
                print('\033[J', end='')   # Clear from cursor down
            
            # Header
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"⏰ {current_time} | 📦 DOWNLOADING: cordata_quarterly.zip")
            print("=" * 85)
            
            # Check current file size
            current_size = 0
            if quarterly_file.exists():
                current_size = quarterly_file.stat().st_size
            
            # Calculate progress
            percentage = (current_size / expected_size) * 100 if expected_size > 0 else 0
            
            # Calculate download speed
            current_time_stamp = time.time()
            time_diff = current_time_stamp - last_time
            size_diff = current_size - last_size
            
            if time_diff > 0 and size_diff >= 0:
                speed_bps = size_diff / time_diff
                speed_history.append(speed_bps)
                
                # Keep last 20 measurements for smoother average
                if len(speed_history) > 20:
                    speed_history.pop(0)
                
                avg_speed = sum(speed_history) / len(speed_history) if speed_history else 0
            else:
                avg_speed = 0
            
            # Update tracking
            last_size = current_size
            last_time = current_time_stamp
            
            # Progress bar
            progress_bar = draw_progress_bar(percentage, 60)
            print(f"📊 Progress: {progress_bar}")
            
            # Size information
            current_mb = current_size / (1024 * 1024)
            expected_mb = expected_size / (1024 * 1024)
            remaining_mb = expected_mb - current_mb
            
            print(f"💾 Downloaded: {format_size(current_size)} / {format_size(expected_size)}")
            print(f"📈 Remaining: {format_size(expected_size - current_size)} ({remaining_mb:.0f} MB)")
            
            # Speed and ETA
            if avg_speed > 0:
                speed_text = format_size(avg_speed) + "/s"
                eta_text = calculate_eta(current_size, expected_size, avg_speed)
                print(f"🚀 Speed: {speed_text} | ⏱️ ETA: {eta_text}")
            else:
                print("🚀 Speed: Measuring... | ⏱️ ETA: Calculating...")
            
            # Completion status
            if percentage >= 100:
                elapsed_total = time.time() - start_time
                print(f"\n🎉 DOWNLOAD COMPLETE! 🎉")
                print(f"⏱️ Total time: {elapsed_total/60:.1f} minutes")
                print(f"🎯 Ready for email extraction!")
                print(f"📧 Expected: 1,000+ additional business emails")
                break
            elif percentage >= 95:
                print("🔥 Almost finished! Final megabytes downloading...")
            elif percentage >= 75:
                print("⚡ Three quarters complete! Entering final stretch...")
            elif percentage >= 50:
                print("🎯 Halfway there! Download progressing well...")
            elif percentage >= 25:
                print("📈 Quarter complete! Keep the momentum...")
            elif percentage >= 10:
                print("🚀 Download is active and progressing...")
            else:
                print("🌟 Starting up... Building download speed...")
            
            # Instructions
            elapsed = time.time() - start_time
            if elapsed > 60:  # After 1 minute, show helpful info
                print(f"💡 This comprehensive dataset will yield significantly more emails!")
            
            # Wait before next update
            if percentage < 100:
                time.sleep(3)  # Update every 3 seconds for smooth progress
                update_count += 1
            else:
                break
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped by user")
        current_mb = quarterly_file.stat().st_size / (1024 * 1024) if quarterly_file.exists() else 0
        print(f"📊 Current download: {current_mb:.1f} MB / 1639 MB")
        print("⏳ Download continues in background")
        print("🔄 Run this script again to resume monitoring")
        
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")
        print("🔄 Download may still be active - check file size manually")

def main():
    # Quick status check first
    quarterly_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\cordata_quarterly.zip")
    
    if not quarterly_file.exists():
        print("❌ Quarterly file not found!")
        print("Make sure the download is started")
        return
    
    current_mb = quarterly_file.stat().st_size / (1024 * 1024)
    if current_mb >= 1600:
        print("✅ Download already complete!")
        print("🚀 Run email extraction: python download_quarterly_data.py")
        return
    
    # Start live monitoring
    live_quarterly_monitor()

if __name__ == "__main__":
    main()