"""
Download Sunbiz data using NEW SFTP credentials from dos.fl.gov
This should work 100% - uses official public access credentials
"""

import sys
import io
import os
import paramiko
import zipfile
from pathlib import Path
import time
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import ThreadedConnectionPool
from urllib.parse import urlparse
import re
import json
from typing import List, Dict, Any, Optional
import threading
from queue import Queue, Empty
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SunbizSFTPDownloader:
    """Download Sunbiz data using official SFTP access"""
    
    def __init__(self):
        # NEW SFTP Credentials from dos.fl.gov
        self.sftp_host = "sftp.floridados.gov"
        self.sftp_port = 22
        self.sftp_username = "Public"
        self.sftp_password = "PubAccess1845!"
        
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Database connection
        db_url = "postgres://postgres.pmispwtdngkcmsrsjwbp:West%40Boca613!@aws-1-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        parsed = urlparse(db_url)
        self.conn_params = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password.replace('%40', '@') if parsed.password else None,
            'sslmode': 'require'
        }
        
        self.conn_pool = ThreadedConnectionPool(1, 10, **self.conn_params)
        
        self.stats = {
            'files_downloaded': 0,
            'records_processed': 0,
            'emails_found': 0,
            'start_time': time.time()
        }
    
    def connect_sftp(self):
        """Connect to SFTP server using official credentials"""
        print("\n" + "=" * 60)
        print("CONNECTING TO OFFICIAL FLORIDA DOS SFTP")
        print("=" * 60)
        print(f"Host: {self.sftp_host}")
        print(f"Username: {self.sftp_username}")
        print(f"Password: {self.sftp_password[:3]}***")
        
        try:
            # Create SSH client
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with official credentials
            print("\nConnecting...")
            ssh.connect(
                hostname=self.sftp_host,
                port=self.sftp_port,
                username=self.sftp_username,
                password=self.sftp_password,
                timeout=30,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Create SFTP client
            sftp = ssh.open_sftp()
            print("✅ Successfully connected to SFTP server!")
            
            return ssh, sftp
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return None, None
    
    def list_available_files(self, sftp):
        """List all available files on SFTP server"""
        print("\n" + "=" * 60)
        print("LISTING AVAILABLE FILES")
        print("=" * 60)
        
        available_files = {}
        
        try:
            # List root directory
            print("\nExploring SFTP directories...")
            
            # Check common paths based on documentation
            paths_to_check = [
                "/",
                "/doc",
                "/doc/cor",
                "/doc/cor/events",
                "/quarterly",
                "/daily",
                "/Public",
                "/public"
            ]
            
            for path in paths_to_check:
                try:
                    print(f"\nChecking {path}...")
                    files = sftp.listdir_attr(path)
                    
                    if files:
                        print(f"  ✅ Found {len(files)} items in {path}")
                        available_files[path] = []
                        
                        for file_attr in files[:10]:  # Show first 10
                            filename = file_attr.filename
                            size_mb = file_attr.st_size / (1024 * 1024)
                            
                            # Look for interesting files
                            if any(keyword in filename.lower() for keyword in 
                                   ['cor', 'off', 'dir', 'annual', 'event', 'data', 'zip', 'txt']):
                                print(f"    - {filename} ({size_mb:.1f} MB)")
                                available_files[path].append({
                                    'name': filename,
                                    'size': file_attr.st_size,
                                    'path': f"{path}/{filename}"
                                })
                                
                except Exception as e:
                    print(f"  ❌ Cannot access {path}: {e}")
            
            # Look specifically for quarterly corporate data
            print("\n📦 QUARTERLY DATA FILES (Most Comprehensive):")
            print("-" * 40)
            
            quarterly_files = [
                "cordata.zip",    # Corporate filings
                "corevent.zip",   # Corporate events
                "ficdata.zip",    # Fictitious names
                "TMData.zip"      # Trademarks
            ]
            
            for filename in quarterly_files:
                print(f"  - {filename}: Quarterly complete dataset")
            
            return available_files
            
        except Exception as e:
            print(f"❌ Error listing files: {e}")
            return {}
    
    def download_file(self, sftp, remote_path: str, local_path: Path) -> bool:
        """Download a file from SFTP"""
        try:
            print(f"\n📥 Downloading: {remote_path}")
            print(f"   To: {local_path}")
            
            # Get file size
            file_attr = sftp.stat(remote_path)
            size_mb = file_attr.st_size / (1024 * 1024)
            print(f"   Size: {size_mb:.1f} MB")
            
            # Download with progress
            sftp.get(remote_path, str(local_path))
            
            print(f"   ✅ Downloaded successfully!")
            self.stats['files_downloaded'] += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
            return False
    
    def extract_and_process(self, zip_path: Path) -> int:
        """Extract ZIP file and process contents for officer/email data"""
        print(f"\n📂 Extracting: {zip_path.name}")
        
        records_found = 0
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Extract to temp directory
                extract_dir = self.base_path / "extracted"
                extract_dir.mkdir(exist_ok=True)
                
                zf.extractall(extract_dir)
                print(f"  ✅ Extracted {len(zf.filelist)} files")
                
                # Process each extracted file
                for filename in zf.namelist():
                    file_path = extract_dir / filename
                    
                    if file_path.suffix.lower() in ['.txt', '.csv']:
                        print(f"  📄 Processing: {filename}")
                        
                        # Look for email patterns in the file
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read(1024 * 1024)  # Read first 1MB
                            
                            # Count emails
                            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                            emails = re.findall(email_pattern, content)
                            
                            if emails:
                                print(f"    ✅ Found {len(emails)} email addresses!")
                                self.stats['emails_found'] += len(emails)
                                
                                # Save emails for processing
                                self.process_emails(emails, filename)
                            
                            # Count records (lines)
                            lines = content.count('\n')
                            records_found += lines
                            print(f"    📊 {lines:,} records")
                
        except Exception as e:
            print(f"  ❌ Error processing: {e}")
        
        return records_found
    
    def process_emails(self, emails: List[str], source_file: str):
        """Process found emails into database"""
        conn = self.conn_pool.getconn()
        try:
            cur = conn.cursor()
            
            # Ensure table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_extracted_emails (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    source_file VARCHAR(255),
                    extracted_date TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Insert unique emails
            for email in set(emails):
                try:
                    cur.execute("""
                        INSERT INTO sunbiz_extracted_emails (email, source_file)
                        VALUES (%s, %s)
                        ON CONFLICT (email) DO NOTHING
                    """, (email.lower(), source_file))
                except:
                    pass
            
            conn.commit()
            
        finally:
            self.conn_pool.putconn(conn)
    
    def download_priority_files(self, sftp):
        """Download priority files that likely contain officer/email data"""
        print("\n" + "=" * 60)
        print("DOWNLOADING PRIORITY FILES")
        print("=" * 60)
        
        # Priority files to download
        priority_files = [
            # Quarterly comprehensive data
            ("cordata.zip", "Quarterly corporate filings - complete dataset"),
            ("corevent.zip", "Quarterly corporate events"),
            
            # Try different paths for the files
            ("/cordata.zip", "Root quarterly corporate"),
            ("/quarterly/cordata.zip", "Quarterly path corporate"),
            ("/doc/cor/cordata.zip", "Doc path corporate"),
            ("/Public/cordata.zip", "Public path corporate")
        ]
        
        downloaded = []
        
        for remote_file, description in priority_files:
            print(f"\n🎯 {description}")
            
            # Generate local filename
            filename = Path(remote_file).name
            local_path = self.base_path / filename
            
            # Skip if already downloaded
            if local_path.exists():
                print(f"  ⏭️ Already exists: {filename}")
                downloaded.append(local_path)
                continue
            
            # Try to download
            try:
                if self.download_file(sftp, remote_file, local_path):
                    downloaded.append(local_path)
                    
                    # If it's a ZIP, extract and process
                    if local_path.suffix.lower() == '.zip':
                        records = self.extract_and_process(local_path)
                        self.stats['records_processed'] += records
                        
            except Exception as e:
                print(f"  ⚠️ Cannot download {remote_file}: {e}")
        
        return downloaded
    
    def run(self):
        """Main execution"""
        print("=" * 60)
        print("SUNBIZ SFTP DOWNLOADER - OFFICIAL ACCESS")
        print("=" * 60)
        print("Using official public credentials from dos.fl.gov")
        print("This should work 100% - no firewall issues!")
        
        # Connect to SFTP
        ssh, sftp = self.connect_sftp()
        
        if not sftp:
            print("\n❌ Could not connect to SFTP server")
            print("\nPossible issues:")
            print("1. SFTP port 22 might be blocked")
            print("2. Credentials might have changed")
            print("3. Server might be temporarily down")
            
            print("\n💡 Alternative: Try manual download")
            print("1. Use FileZilla or WinSCP")
            print(f"2. Host: {self.sftp_host}")
            print(f"3. Username: {self.sftp_username}")
            print(f"4. Password: {self.sftp_password}")
            return
        
        try:
            # List available files
            available = self.list_available_files(sftp)
            
            # Download priority files
            downloaded = self.download_priority_files(sftp)
            
            # Summary
            elapsed = time.time() - self.stats['start_time']
            
            print("\n" + "=" * 60)
            print("DOWNLOAD SUMMARY")
            print("=" * 60)
            print(f"✅ Files downloaded: {self.stats['files_downloaded']}")
            print(f"📊 Records processed: {self.stats['records_processed']:,}")
            print(f"📧 Emails found: {self.stats['emails_found']:,}")
            print(f"⏱️ Time: {elapsed:.1f} seconds")
            
            if downloaded:
                print("\n📁 Downloaded files:")
                for file in downloaded:
                    size_mb = file.stat().st_size / (1024 * 1024)
                    print(f"  - {file.name} ({size_mb:.1f} MB)")
            
            if self.stats['emails_found'] > 0:
                print(f"\n✅ SUCCESS! Found {self.stats['emails_found']:,} email addresses")
                print("Run query: SELECT * FROM sunbiz_extracted_emails LIMIT 10;")
            
        finally:
            # Close connections
            sftp.close()
            ssh.close()
            print("\n✅ SFTP connection closed")

if __name__ == "__main__":
    downloader = SunbizSFTPDownloader()
    downloader.run()