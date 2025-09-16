"""
Download the corprindata.zip file NOW with optimized settings
Uses chunked downloading and resume capability
"""

import sys
import io
import os
import paramiko
import time
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def download_corprindata():
    """Download the 665MB corprindata.zip file"""
    
    print("=" * 60)
    print("DOWNLOADING CORPRINDATA.ZIP (665MB)")
    print("=" * 60)
    
    # SFTP Credentials
    sftp_host = "sftp.floridados.gov"
    sftp_username = "Public"
    sftp_password = "PubAccess1845!"
    
    # File paths
    remote_path = "/Public/doc/AG/corprindata.zip"
    local_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\corprindata.zip")
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if partially downloaded
    start_pos = 0
    if local_path.exists():
        start_pos = local_path.stat().st_size
        print(f"📎 Resuming from {start_pos / (1024*1024):.1f} MB")
    
    try:
        # Connect to SFTP
        print("\n🔌 Connecting to SFTP...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Optimize transport settings
        ssh.connect(
            hostname=sftp_host,
            port=22,
            username=sftp_username,
            password=sftp_password,
            timeout=60,
            look_for_keys=False,
            allow_agent=False
        )
        
        # Get transport and optimize
        transport = ssh.get_transport()
        transport.set_keepalive(30)  # Keep connection alive
        transport.window_size = 2147483647  # Max window size
        transport.packetizer.REKEY_BYTES = pow(2, 40)  # Increase rekey limit
        
        sftp = ssh.open_sftp()
        print("✅ Connected to SFTP")
        
        # Get file info
        file_stat = sftp.stat(remote_path)
        total_size = file_stat.st_size
        total_mb = total_size / (1024 * 1024)
        print(f"\n📦 File size: {total_mb:.1f} MB")
        
        # Download with progress
        print("\n📥 Starting download...")
        print("This will take several minutes. Please wait...\n")
        
        start_time = time.time()
        last_update = time.time()
        bytes_downloaded = start_pos
        
        # Open remote file
        with sftp.open(remote_path, 'rb') as remote_file:
            # Seek to resume position if needed
            if start_pos > 0:
                remote_file.seek(start_pos)
            
            # Open local file for writing (append mode if resuming)
            mode = 'ab' if start_pos > 0 else 'wb'
            with open(local_path, mode) as local_file:
                # Download in chunks
                chunk_size = 1024 * 1024  # 1MB chunks
                
                while bytes_downloaded < total_size:
                    try:
                        # Read chunk
                        chunk = remote_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        # Write chunk
                        local_file.write(chunk)
                        local_file.flush()  # Force write to disk
                        
                        bytes_downloaded += len(chunk)
                        
                        # Update progress every 2 seconds
                        if time.time() - last_update > 2:
                            progress = (bytes_downloaded / total_size) * 100
                            mb_done = bytes_downloaded / (1024 * 1024)
                            elapsed = time.time() - start_time
                            
                            if elapsed > 0:
                                speed = (bytes_downloaded - start_pos) / elapsed / (1024 * 1024)
                                eta = (total_size - bytes_downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                                
                                print(f"Progress: {progress:.1f}% ({mb_done:.1f}/{total_mb:.1f} MB) - "
                                      f"Speed: {speed:.1f} MB/s - ETA: {eta:.0f}s", end='\r')
                            else:
                                print(f"Progress: {progress:.1f}% ({mb_done:.1f}/{total_mb:.1f} MB)", end='\r')
                            
                            last_update = time.time()
                            
                    except Exception as e:
                        print(f"\n⚠️ Connection issue: {e}")
                        print("Attempting to reconnect...")
                        
                        # Try to reconnect
                        try:
                            sftp.close()
                            ssh.close()
                            
                            # Reconnect
                            ssh.connect(
                                hostname=sftp_host,
                                port=22,
                                username=sftp_username,
                                password=sftp_password,
                                timeout=60
                            )
                            sftp = ssh.open_sftp()
                            
                            # Reopen remote file and seek
                            remote_file = sftp.open(remote_path, 'rb')
                            remote_file.seek(bytes_downloaded)
                            print("✅ Reconnected, resuming download...")
                            
                        except Exception as reconnect_error:
                            print(f"❌ Failed to reconnect: {reconnect_error}")
                            raise
        
        # Download complete
        elapsed_total = time.time() - start_time
        avg_speed = (bytes_downloaded - start_pos) / elapsed_total / (1024 * 1024)
        
        print(f"\n\n✅ DOWNLOAD COMPLETE!")
        print(f"📦 File: {local_path}")
        print(f"📊 Size: {total_mb:.1f} MB")
        print(f"⏱️ Time: {elapsed_total:.1f} seconds")
        print(f"🚀 Speed: {avg_speed:.1f} MB/s")
        
        sftp.close()
        ssh.close()
        
        return local_path
        
    except Exception as e:
        print(f"\n❌ Download error: {e}")
        
        # Check if we got partial download
        if local_path.exists():
            partial_mb = local_path.stat().st_size / (1024 * 1024)
            print(f"\n📎 Partial download saved: {partial_mb:.1f} MB")
            print("Run this script again to resume the download")
        
        return None

if __name__ == "__main__":
    result = download_corprindata()
    
    if result:
        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("1. File downloaded successfully!")
        print("2. Run: python process_corprindata.py")
        print("   to extract and process all officer emails")
    else:
        print("\n💡 TIP: If download keeps failing:")
        print("1. Use FileZilla with the same credentials")
        print("2. Or try from a different network")
        print("3. Or use a cloud server")