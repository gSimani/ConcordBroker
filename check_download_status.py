"""
Check the status of the corprindata.zip download
"""

import sys
import io
import json
from pathlib import Path
from datetime import datetime

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_status():
    """Check download status"""
    
    print("=" * 60)
    print("DOWNLOAD STATUS CHECK")
    print("=" * 60)
    
    # File paths
    local_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\corprindata.zip")
    progress_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\download_progress.json")
    
    # Check if file exists
    if local_file.exists():
        current_size = local_file.stat().st_size
        current_mb = current_size / (1024 * 1024)
        print(f"📦 File: {local_file.name}")
        print(f"📊 Current size: {current_mb:.1f} MB")
        
        # Expected size is ~665MB
        expected_mb = 665
        progress_pct = (current_mb / expected_mb) * 100
        
        print(f"📈 Progress: {progress_pct:.1f}% of expected {expected_mb} MB")
        
        if current_mb >= 600:
            print("✅ File appears to be complete or nearly complete!")
            print("You can now run: python process_corprindata.py")
        else:
            print(f"⏳ Still downloading... {expected_mb - current_mb:.1f} MB remaining")
            
    else:
        print("❌ File not found - download not started or failed")
    
    # Check progress file
    if progress_file.exists():
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            print(f"\n📊 DETAILED PROGRESS:")
            print("-" * 40)
            print(f"Status: {progress['status']}")
            print(f"Downloaded: {progress['bytes_downloaded'] / (1024*1024):.1f} MB")
            print(f"Total: {progress['total_size'] / (1024*1024):.1f} MB")
            print(f"Progress: {progress['progress_percent']:.1f}%")
            print(f"Last update: {progress['timestamp']}")
            
            # Calculate time since last update
            try:
                last_update = datetime.fromisoformat(progress['timestamp'])
                now = datetime.now()
                minutes_since = (now - last_update).total_seconds() / 60
                
                if minutes_since > 5:
                    print(f"\n⚠️ No updates for {minutes_since:.1f} minutes")
                    print("Download may have stalled")
                else:
                    print(f"\n✅ Last update: {minutes_since:.1f} minutes ago")
                    
            except:
                pass
                
        except Exception as e:
            print(f"\n❌ Error reading progress file: {e}")
    else:
        print("\n📝 No progress file found")
    
    print("\n💡 WHAT TO DO:")
    print("-" * 40)
    
    if local_file.exists() and local_file.stat().st_size / (1024*1024) >= 600:
        print("✅ File ready - process it:")
        print("   python process_corprindata.py")
    else:
        print("⏳ Download in progress:")
        print("   1. Wait for download to complete")
        print("   2. Run this script again to check status")
        print("   3. Or restart download: python download_corprindata_background.py")

if __name__ == "__main__":
    check_status()