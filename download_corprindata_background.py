"""
Background downloader for corprindata.zip
Runs independently and saves progress
"""

import sys
import io
import os
import paramiko
import time
from pathlib import Path
import json
from datetime import datetime
import threading
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class BackgroundDownloader:
    def __init__(self):
        self.sftp_host = "sftp.floridados.gov"
        self.sftp_username = "Public"
        self.sftp_password = "PubAccess1845!"
        self.remote_path = "/Public/doc/AG/corprindata.zip"
        self.local_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\corprindata.zip")
        self.progress_file = self.local_path.parent / "download_progress.json"
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        
    def save_progress(self, bytes_downloaded, total_size, status):
        """Save download progress to file"""
        progress = {
            'timestamp': datetime.now().isoformat(),
            'bytes_downloaded': bytes_downloaded,
            'total_size': total_size,
            'progress_percent': (bytes_downloaded / total_size * 100) if total_size > 0 else 0,
            'status': status,
            'file': str(self.local_path)
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def download_chunk(self, sftp, start_byte, chunk_size=5*1024*1024):
        """Download a specific chunk of the file"""
        try:
            with sftp.open(self.remote_path, 'rb') as remote_file:
                remote_file.seek(start_byte)
                return remote_file.read(chunk_size)
        except Exception as e:
            print(f"Chunk error at byte {start_byte}: {e}")
            return None
    
    def run(self):
        """Run the download"""
        print("=" * 60)
        print("BACKGROUND DOWNLOADER FOR CORPRINDATA.ZIP")
        print("=" * 60)
        
        # Check existing progress
        start_pos = 0
        if self.local_path.exists():
            start_pos = self.local_path.stat().st_size
            print(f"📎 Found existing file: {start_pos / (1024*1024):.1f} MB downloaded")
        
        try:
            # Connect
            print("\n🔌 Connecting to SFTP...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=self.sftp_host,
                port=22,
                username=self.sftp_username,
                password=self.sftp_password,
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
            
            sftp = ssh.open_sftp()
            print("✅ Connected")
            
            # Get file size
            file_stat = sftp.stat(self.remote_path)
            total_size = file_stat.st_size
            total_mb = total_size / (1024 * 1024)
            
            print(f"\n📦 Total file size: {total_mb:.1f} MB")
            
            if start_pos >= total_size:
                print("✅ File already completely downloaded!")
                self.save_progress(total_size, total_size, "completed")
                return True
            
            print(f"📥 Need to download: {(total_size - start_pos) / (1024*1024):.1f} MB")
            
            # Download in smaller chunks with progress saves
            chunk_size = 5 * 1024 * 1024  # 5MB chunks
            mode = 'ab' if start_pos > 0 else 'wb'
            
            print("\n⏳ Starting chunked download...")
            print("Progress will be saved every 5MB")
            print("You can stop and resume anytime\n")
            
            with open(self.local_path, mode) as local_file:
                bytes_downloaded = start_pos
                start_time = time.time()
                last_save = time.time()
                
                while bytes_downloaded < total_size:
                    # Download chunk
                    chunk = self.download_chunk(sftp, bytes_downloaded, chunk_size)
                    
                    if chunk:
                        local_file.write(chunk)
                        local_file.flush()
                        bytes_downloaded += len(chunk)
                        
                        # Update progress
                        progress = (bytes_downloaded / total_size) * 100
                        mb_done = bytes_downloaded / (1024 * 1024)
                        
                        # Calculate speed
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            speed = (bytes_downloaded - start_pos) / elapsed / (1024 * 1024)
                            eta = (total_size - bytes_downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                            
                            print(f"Downloaded: {mb_done:.1f}/{total_mb:.1f} MB ({progress:.1f}%) - "
                                  f"Speed: {speed:.2f} MB/s - ETA: {eta/60:.1f} min", end='\r')
                        
                        # Save progress every 10 seconds
                        if time.time() - last_save > 10:
                            self.save_progress(bytes_downloaded, total_size, "downloading")
                            last_save = time.time()
                    else:
                        # Reconnect if chunk failed
                        print("\n⚠️ Connection lost, reconnecting...")
                        sftp.close()
                        ssh.close()
                        
                        ssh.connect(
                            hostname=self.sftp_host,
                            port=22,
                            username=self.sftp_username,
                            password=self.sftp_password,
                            timeout=30
                        )
                        sftp = ssh.open_sftp()
                        print("✅ Reconnected")
            
            # Complete
            elapsed = time.time() - start_time
            avg_speed = (bytes_downloaded - start_pos) / elapsed / (1024 * 1024) if elapsed > 0 else 0
            
            print(f"\n\n✅ DOWNLOAD COMPLETE!")
            print(f"📦 File saved to: {self.local_path}")
            print(f"⏱️ Time: {elapsed/60:.1f} minutes")
            print(f"🚀 Average speed: {avg_speed:.2f} MB/s")
            
            self.save_progress(total_size, total_size, "completed")
            
            sftp.close()
            ssh.close()
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            
            if self.local_path.exists():
                current_size = self.local_path.stat().st_size
                print(f"\n📎 Progress saved: {current_size / (1024*1024):.1f} MB")
                print("Run this script again to continue downloading")
                
                try:
                    self.save_progress(current_size, total_size, "interrupted")
                except:
                    pass
            
            return False

def check_progress():
    """Check current download progress"""
    progress_file = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\download_progress.json")
    
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        
        print("\n📊 CURRENT DOWNLOAD STATUS:")
        print("-" * 40)
        print(f"Progress: {progress['progress_percent']:.1f}%")
        print(f"Downloaded: {progress['bytes_downloaded'] / (1024*1024):.1f} MB")
        print(f"Total size: {progress['total_size'] / (1024*1024):.1f} MB")
        print(f"Status: {progress['status']}")
        print(f"Last update: {progress['timestamp']}")
        
        return progress['status'] == 'completed'
    else:
        print("No download in progress")
        return False

if __name__ == "__main__":
    # Check if already complete
    if check_progress():
        print("\n✅ File already downloaded!")
        print("Run: python process_corprindata.py")
    else:
        # Start download
        downloader = BackgroundDownloader()
        success = downloader.run()
        
        if success:
            print("\n" + "=" * 60)
            print("NEXT STEPS")
            print("=" * 60)
            print("1. The 665MB corprindata.zip is ready!")
            print("2. Run: python process_corprindata.py")
            print("   to extract all officer emails")