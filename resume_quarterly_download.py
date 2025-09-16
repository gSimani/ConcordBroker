"""
Simple aggressive downloader to resume and complete the quarterly file
Focus on speed and reliability
"""

import sys
import io
import paramiko
from pathlib import Path
import time
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def resume_quarterly_download():
    """Resume and complete the quarterly download with aggressive settings"""
    
    print("=" * 70)
    print("AGGRESSIVE QUARTERLY DOWNLOAD RESUMPTION")
    print("=" * 70)
    
    # Connection settings
    sftp_host = "sftp.floridados.gov"
    sftp_username = "Public"
    sftp_password = "PubAccess1845!"
    
    # File paths
    base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
    local_file = base_path / "cordata_quarterly.zip"
    remote_path = "/Public/doc/Quarterly/Cor/cordata.zip"
    expected_size = 1639.0 * 1024 * 1024  # 1639 MB
    
    try:
        # Check current status
        current_size = 0
        if local_file.exists():
            current_size = local_file.stat().st_size
            current_mb = current_size / (1024 * 1024)
            progress = (current_size / expected_size) * 100
            print(f"Current file: {current_mb:.1f} MB ({progress:.1f}%)")
        else:
            print("Starting fresh download")
        
        if current_size >= expected_size:
            print("Download already complete!")
            return True
        
        # Connect with aggressive settings
        print("\\nConnecting with optimized settings...")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh.connect(
            hostname=sftp_host,
            port=22,
            username=sftp_username,
            password=sftp_password,
            timeout=30,
            compress=True,
            look_for_keys=False,
            allow_agent=False
        )
        
        sftp = ssh.open_sftp()
        print("Connected successfully!")
        
        # Aggressive download
        print(f"\\nStarting aggressive download from {current_size} bytes...")
        
        with sftp.open(remote_path, 'rb') as remote_file:
            # Seek to current position
            if current_size > 0:
                remote_file.seek(current_size)
                print(f"Resumed from {current_size / (1024*1024):.1f} MB")
            
            # Open local file for appending
            mode = 'ab' if current_size > 0 else 'wb'
            with open(local_file, mode) as local_f:
                
                # Aggressive settings
                chunk_size = 10 * 1024 * 1024  # 10MB chunks
                bytes_written = current_size
                last_update = time.time()
                start_time = time.time()
                
                print(f"Using {chunk_size // (1024*1024)}MB chunks for maximum speed")
                
                while bytes_written < expected_size:
                    try:
                        # Read chunk
                        chunk = remote_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        # Write immediately
                        local_f.write(chunk)
                        local_f.flush()  # Force write to disk
                        bytes_written += len(chunk)
                        
                        # Progress update every 5MB or 10 seconds
                        if (bytes_written - current_size) % (5 * 1024 * 1024) == 0 or time.time() - last_update > 10:
                            mb_done = bytes_written / (1024 * 1024)
                            total_mb = expected_size / (1024 * 1024)
                            progress = (bytes_written / expected_size) * 100
                            elapsed = time.time() - start_time
                            
                            if elapsed > 0:
                                speed = (bytes_written - current_size) / elapsed / (1024 * 1024)
                                remaining = (expected_size - bytes_written) / (1024 * 1024)
                                eta = remaining / speed if speed > 0 else 0
                                
                                print(f"Progress: {progress:.1f}% ({mb_done:.0f}/{total_mb:.0f} MB) | "
                                      f"Speed: {speed:.1f} MB/s | ETA: {eta:.1f} min")
                            
                            last_update = time.time()
                        
                    except Exception as e:
                        print(f"Chunk error: {e}")
                        time.sleep(1)  # Brief pause and continue
                        continue
        
        sftp.close()
        ssh.close()
        
        # Verify completion
        final_size = local_file.stat().st_size
        final_mb = final_size / (1024 * 1024)
        total_time = time.time() - start_time
        
        print(f"\\nDOWNLOAD COMPLETE!")
        print(f"Final size: {final_mb:.1f} MB")
        print(f"Total time: {total_time/60:.1f} minutes")
        print(f"Average speed: {(final_size - current_size) / total_time / (1024*1024):.1f} MB/s")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    success = resume_quarterly_download()
    if success:
        print("\\n" + "="*50)
        print("READY FOR EMAIL EXTRACTION!")
        print("Run: python process_quarterly_emails.py")
        print("="*50)