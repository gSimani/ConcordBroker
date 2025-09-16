"""
Download the comprehensive quarterly data files that contain much more data
Focus on cordata.zip (1.6GB) and corevent.zip (170MB) for maximum email extraction
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
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class QuarterlyDataDownloader:
    """Download and process comprehensive quarterly corporate data"""
    
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
    
    def download_with_resume(self, sftp, remote_path: str, local_path: Path) -> bool:
        """Download file with resume capability"""
        print(f"\n📦 Downloading: {remote_path}")
        
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
            
            # Download with progress
            with sftp.open(remote_path, 'rb') as remote_file:
                if start_pos > 0:
                    remote_file.seek(start_pos)
                
                mode = 'ab' if start_pos > 0 else 'wb'
                with open(local_path, mode) as local_file:
                    chunk_size = 5 * 1024 * 1024  # 5MB chunks
                    bytes_downloaded = start_pos
                    last_update = time.time()
                    download_start = time.time()
                    
                    while bytes_downloaded < total_size:
                        chunk = remote_file.read(chunk_size)
                        if not chunk:
                            break
                        
                        local_file.write(chunk)
                        local_file.flush()
                        bytes_downloaded += len(chunk)
                        
                        # Progress update every 10 seconds
                        if time.time() - last_update > 10:
                            progress = (bytes_downloaded / total_size) * 100
                            mb_done = bytes_downloaded / (1024 * 1024)
                            elapsed = time.time() - download_start
                            
                            if elapsed > 0:
                                speed = (bytes_downloaded - start_pos) / elapsed / (1024 * 1024)
                                eta = (total_size - bytes_downloaded) / (speed * 1024 * 1024) if speed > 0 else 0
                                
                                print(f"Progress: {progress:.1f}% ({mb_done:.1f}/{total_mb:.1f} MB) - "
                                      f"Speed: {speed:.1f} MB/s - ETA: {eta/60:.1f} min")
                            
                            last_update = time.time()
            
            elapsed = time.time() - download_start
            print(f"✅ Download complete in {elapsed/60:.1f} minutes!")
            self.stats['files_downloaded'] += 1
            return True
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def extract_emails_from_text(self, text: str) -> list:
        """Extract email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text, re.IGNORECASE)
    
    def process_zip_file(self, zip_path: Path) -> int:
        """Process ZIP file and extract emails"""
        print(f"\n📂 Processing: {zip_path.name}")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                print(f"Found {len(files)} files in ZIP")
                
                file_emails_found = 0
                
                for i, filename in enumerate(files):
                    print(f"\n📄 Processing {filename} ({i+1}/{len(files)})")
                    
                    try:
                        with zf.open(filename) as f:
                            # Process in chunks to avoid memory issues
                            chunk_size = 10 * 1024 * 1024  # 10MB chunks
                            chunk_num = 0
                            
                            while True:
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                
                                chunk_num += 1
                                
                                # Decode and extract emails
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
                                    print(f"  Chunk {chunk_num}: Found {len(chunk_emails)} emails")
                        
                        if file_emails_found > 0:
                            print(f"  ✅ Total emails in {filename}: {file_emails_found}")
                        
                    except Exception as e:
                        print(f"  ❌ Error processing {filename}: {e}")
                
                print(f"\n✅ ZIP processing complete!")
                print(f"📧 Emails found in this ZIP: {file_emails_found}")
                return file_emails_found
                
        except Exception as e:
            print(f"❌ Error opening ZIP: {e}")
            return 0
    
    def run(self):
        """Download and process all quarterly data"""
        print("=" * 70)
        print("COMPREHENSIVE QUARTERLY DATA DOWNLOADER")
        print("=" * 70)
        print("Downloading massive datasets for complete email extraction")
        
        # Priority files to download
        priority_files = [
            {
                'remote_path': '/Public/doc/Quarterly/Cor/cordata.zip',
                'filename': 'cordata_quarterly.zip',
                'description': 'Complete quarterly corporate data (1.6GB)',
                'priority': 1
            },
            {
                'remote_path': '/Public/doc/Quarterly/Cor/corevent.zip', 
                'filename': 'corevent_quarterly.zip',
                'description': 'Corporate events quarterly data (170MB)',
                'priority': 2
            }
        ]
        
        try:
            # Connect to SFTP
            print("\n🔌 Connecting to SFTP...")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                hostname=self.sftp_host,
                port=22,
                username=self.sftp_username,
                password=self.sftp_password,
                timeout=30
            )
            
            sftp = ssh.open_sftp()
            print("✅ Connected!")
            
            # Download files
            downloaded_files = []
            
            for file_info in priority_files:
                print(f"\n" + "=" * 50)
                print(f"PRIORITY {file_info['priority']}: {file_info['description']}")
                print("=" * 50)
                
                local_path = self.base_path / file_info['filename']
                
                if self.download_with_resume(sftp, file_info['remote_path'], local_path):
                    downloaded_files.append(local_path)
            
            sftp.close()
            ssh.close()
            
            # Process downloaded files
            print(f"\n" + "=" * 70)
            print("PROCESSING DOWNLOADED FILES FOR EMAILS")
            print("=" * 70)
            
            total_emails = 0
            for file_path in downloaded_files:
                emails_in_file = self.process_zip_file(file_path)
                total_emails += emails_in_file
            
            # Final results
            elapsed = time.time() - self.stats['start_time']
            
            print(f"\n" + "=" * 70)
            print("COMPREHENSIVE EMAIL EXTRACTION COMPLETE")
            print("=" * 70)
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
                output_file = self.base_path / "comprehensive_emails.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    for email in sorted(self.stats['unique_emails']):
                        f.write(f"{email}\n")
                
                print(f"\n💾 ALL UNIQUE EMAILS SAVED TO:")
                print(f"📄 {output_file}")
                print(f"📊 Contains {len(self.stats['unique_emails']):,} unique email addresses")
                
                # Show sample
                print(f"\n📧 SAMPLE EMAILS EXTRACTED:")
                print("-" * 50)
                unique_list = list(self.stats['unique_emails'])
                for i, email in enumerate(unique_list[:25]):
                    print(f"{i+1:2d}. {email}")
                
                if len(unique_list) > 25:
                    print(f"\n... and {len(unique_list) - 25:,} more unique emails!")
                
                print(f"\n🎉 SUCCESS!")
                print(f"Extracted {len(self.stats['unique_emails']):,} unique Florida business emails")
                print("💼 Complete corporate database with officer contact information")
            
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    downloader = QuarterlyDataDownloader()
    downloader.run()