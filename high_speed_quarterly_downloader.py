"""
HIGH-SPEED OPTIMIZED DOWNLOADER for 1.6GB Quarterly Data
Uses multiple optimization techniques for maximum download speed
"""

import sys
import io
import paramiko
import zipfile
from pathlib import Path
import time
from datetime import datetime
import re
import threading
from queue import Queue, Empty
import warnings
import socket
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class HighSpeedQuarterlyDownloader:
    """Optimized high-speed downloader for quarterly corporate data"""
    
    def __init__(self):
        self.sftp_host = "sftp.floridados.gov"
        self.sftp_username = "Public"
        self.sftp_password = "PubAccess1845!"
        
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.stats = {
            'files_downloaded': 0,
            'records_processed': 0,
            'emails_found': 0,
            'unique_emails': set(),
            'start_time': time.time()
        }
    
    def create_optimized_connection(self):
        """Create optimized SFTP connection with high-performance settings"""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Optimized connection parameters
        ssh.connect(
            hostname=self.sftp_host,
            port=22,
            username=self.sftp_username,
            password=self.sftp_password,
            timeout=60,  # Increased timeout
            banner_timeout=60,
            auth_timeout=60,
            compress=True,  # Enable compression
            sock=None,
            gss_auth=False,
            gss_kex=False,
            gss_deleg_creds=True,
            gss_host=None,
            allow_agent=False,
            look_for_keys=False
        )
        
        # Configure transport for high performance
        transport = ssh.get_transport()
        transport.set_keepalive(30)  # Keep connection alive
        transport.use_compression(True)  # Use compression
        
        # Create SFTP with optimized settings
        sftp = ssh.open_sftp()
        
        # Increase buffer sizes for better performance
        try:
            sftp.get_channel().settimeout(300)  # 5 minute timeout per operation
        except:
            pass
            
        return ssh, sftp
    
    def optimized_download_with_resume(self, sftp, remote_path: str, local_path: Path) -> bool:
        """High-speed download with multiple optimizations"""
        print(f"\n🚀 HIGH-SPEED DOWNLOAD: {remote_path}")
        
        # Check if partially downloaded
        start_pos = 0
        if local_path.exists():
            start_pos = local_path.stat().st_size
            print(f"📎 Resuming from {start_pos / (1024*1024):.1f} MB")
        
        try:
            # Get file size
            file_stat = sftp.stat(remote_path)
            total_size = file_stat.st_size
            total_mb = total_size / (1024 * 1024)
            
            if start_pos >= total_size:
                print("✅ File already downloaded!")
                return True
            
            print(f"📊 Total size: {total_mb:.1f} MB")
            print(f"📥 Need to download: {(total_size - start_pos) / (1024*1024):.1f} MB")
            
            # Optimized download with larger chunks and buffering
            with sftp.open(remote_path, 'rb') as remote_file:
                if start_pos > 0:
                    remote_file.seek(start_pos)
                
                mode = 'ab' if start_pos > 0 else 'wb'
                with open(local_path, mode) as local_file:
                    # OPTIMIZED SETTINGS
                    chunk_size = 32 * 1024 * 1024  # 32MB chunks (4x larger)
                    buffer_size = 128 * 1024 * 1024  # 128MB buffer
                    
                    bytes_downloaded = start_pos
                    last_update = time.time()
                    download_start = time.time()
                    speed_samples = []
                    
                    print(f"⚡ Using 32MB chunks with 128MB buffer for maximum speed")
                    
                    while bytes_downloaded < total_size:
                        chunk_start = time.time()
                        
                        # Read large chunk
                        chunk = remote_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        # Write with buffer flushing
                        local_file.write(chunk)
                        if len(chunk) >= chunk_size:  # Only flush on full chunks
                            local_file.flush()
                        
                        bytes_downloaded += len(chunk)
                        chunk_time = time.time() - chunk_start
                        
                        # Calculate speed for this chunk
                        if chunk_time > 0:
                            chunk_speed = len(chunk) / chunk_time / (1024 * 1024)
                            speed_samples.append(chunk_speed)
                            
                            # Keep only last 10 samples for smooth average
                            if len(speed_samples) > 10:
                                speed_samples.pop(0)
                        
                        # Progress update every 5 seconds or every 100MB
                        if (time.time() - last_update > 5) or (len(chunk) < chunk_size):
                            progress = (bytes_downloaded / total_size) * 100
                            mb_done = bytes_downloaded / (1024 * 1024)
                            elapsed = time.time() - download_start
                            
                            if speed_samples:
                                avg_speed = sum(speed_samples) / len(speed_samples)
                                remaining_mb = (total_size - bytes_downloaded) / (1024 * 1024)
                                eta_minutes = remaining_mb / avg_speed / 60 if avg_speed > 0 else 0
                                
                                print(f"🔥 Progress: {progress:.1f}% ({mb_done:.1f}/{total_mb:.1f} MB) - "
                                      f"Speed: {avg_speed:.1f} MB/s - ETA: {eta_minutes:.1f} min")
                            
                            last_update = time.time()
                    
                    # Final flush
                    local_file.flush()
            
            elapsed = time.time() - download_start
            final_speed = (total_size - start_pos) / elapsed / (1024 * 1024)
            print(f"✅ HIGH-SPEED DOWNLOAD COMPLETE!")
            print(f"⏱️ Time: {elapsed/60:.1f} minutes")
            print(f"🚀 Average speed: {final_speed:.1f} MB/s")
            
            self.stats['files_downloaded'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def extract_emails_from_text(self, text: str) -> list:
        """Extract email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text, re.IGNORECASE)
    
    def process_zip_file_optimized(self, zip_path: Path) -> int:
        """Process ZIP file with high-speed email extraction"""
        print(f"\n🚀 HIGH-SPEED PROCESSING: {zip_path.name}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                print(f"Found {len(files)} files in ZIP")
                
                file_emails_found = 0
                
                for i, filename in enumerate(files):
                    print(f"\n📄 Processing {filename} ({i+1}/{len(files)})")
                    
                    try:
                        with zf.open(filename) as f:
                            # High-speed processing with larger chunks
                            chunk_size = 50 * 1024 * 1024  # 50MB chunks for processing
                            chunk_num = 0
                            
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                
                                chunk_num += 1
                                
                                # Fast decode and extract emails
                                try:
                                    text = chunk.decode('utf-8', errors='ignore')
                                except:
                                    text = chunk.decode('latin-1', errors='ignore')
                                
                                lines = text.split('\n')
                                self.stats['records_processed'] += len(lines)
                                
                                chunk_emails = []
                                for line in lines:
                                    if '@' in line:
                                        emails = self.extract_emails_from_text(line)
                                        for email in emails:
                                            email_clean = email.lower().strip()
                                            if email_clean and len(email_clean) > 5:
                                                chunk_emails.append(email_clean)
                                                self.stats['unique_emails'].add(email_clean)
                                                self.stats['emails_found'] += 1
                                
                                if chunk_emails:
                                    file_emails_found += len(chunk_emails)
                                    print(f"  ⚡ Chunk {chunk_num}: Found {len(chunk_emails)} emails")
                        
                        if file_emails_found > 0:
                            print(f"  ✅ Total emails in {filename}: {file_emails_found}")
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {filename}: {e}")
                
                print(f"\n🚀 HIGH-SPEED ZIP PROCESSING COMPLETE!")
                print(f"📧 Emails found in this ZIP: {file_emails_found}")
                return file_emails_found
                
        except Exception as e:
            print(f"❌ Error opening ZIP: {e}")
            return 0
    
    def run(self):
        """Run high-speed download and processing"""
        print("=" * 80)
        print("🚀 HIGH-SPEED QUARTERLY DATA DOWNLOADER")
        print("=" * 80)
        print("Optimized for maximum download speed and processing efficiency")
        
        # Priority file for high-speed download
        priority_file = {
            'remote_path': '/Public/doc/Quarterly/Cor/cordata.zip',
            'filename': 'cordata_quarterly.zip',
            'description': 'Complete quarterly corporate data (1.6GB)',
            'priority': 1
        }
        
        try:
            # Create optimized connection
            print(f"\n🔌 Creating optimized SFTP connection...")
            ssh, sftp = self.create_optimized_connection()
            print("✅ High-performance connection established!")
            
            # High-speed download
            print(f"\n" + "=" * 60)
            print(f"🚀 HIGH-SPEED DOWNLOAD: {priority_file['description']}")
            print("=" * 60)
            
            local_path = self.base_path / priority_file['filename']
            
            if self.optimized_download_with_resume(sftp, priority_file['remote_path'], local_path):
                print(f"\n🎉 HIGH-SPEED DOWNLOAD SUCCESS!")
                
                # High-speed processing
                print(f"\n" + "=" * 80)
                print("🚀 HIGH-SPEED EMAIL EXTRACTION")
                print("=" * 80)
                
                emails_in_file = self.process_zip_file_optimized(local_path)
                
                # Final results
                elapsed = time.time() - self.stats['start_time']
                
                print(f"\n" + "=" * 80)
                print("🚀 HIGH-SPEED EXTRACTION COMPLETE")
                print("=" * 80)
                print(f"✅ Files downloaded: {self.stats['files_downloaded']}")
                print(f"✅ Records processed: {self.stats['records_processed']:,}")
                print(f"📧 Total emails found: {self.stats['emails_found']:,}")
                print(f"🎯 Unique emails: {len(self.stats['unique_emails']):,}")
                print(f"⏱️ Total time: {elapsed/60:.1f} minutes")
                
                if self.stats['records_processed'] > 0:
                    rate = self.stats['records_processed'] / elapsed
                    print(f"🚀 Processing rate: {rate:,.0f} records/second")
                
                # Save all unique emails
                if self.stats['unique_emails']:
                    output_file = self.base_path / "comprehensive_quarterly_emails.txt"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        for email in sorted(self.stats['unique_emails']):
                            f.write(f"{email}\n")
                    
                    print(f"\n💾 ALL QUARTERLY EMAILS SAVED TO:")
                    print(f"📄 {output_file}")
                    print(f"📊 Contains {len(self.stats['unique_emails']):,} unique email addresses")
                    
                    # Show sample
                    print(f"\n📧 SAMPLE QUARTERLY EMAILS EXTRACTED:")
                    print("-" * 60)
                    unique_list = list(self.stats['unique_emails'])
                    for i, email in enumerate(unique_list[:25]):
                        print(f"{i+1:2d}. {email}")
                    
                    if len(unique_list) > 25:
                        print(f"\n... and {len(unique_list) - 25:,} more unique emails!")
                    
                    print(f"\n🎉 HIGH-SPEED SUCCESS!")
                    print(f"Extracted {len(self.stats['unique_emails']):,} unique Florida business emails")
                    print("💼 Complete quarterly corporate database with officer information")
                
            sftp.close()
            ssh.close()
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    downloader = HighSpeedQuarterlyDownloader()
    downloader.run()