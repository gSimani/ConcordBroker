"""
Download comprehensive corporate data from Florida DOS SFTP
Focus on the large corprindata.zip file that likely contains all corporate and officer data
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
import warnings
warnings.filterwarnings('ignore')

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CorporateDataDownloader:
    """Download and process comprehensive corporate data"""
    
    def __init__(self):
        # SFTP Credentials
        self.sftp_host = "sftp.floridados.gov"
        self.sftp_username = "Public"
        self.sftp_password = "PubAccess1845!"
        
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Database
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
        
        self.stats = {
            'files_downloaded': 0,
            'records_processed': 0,
            'emails_found': 0,
            'start_time': time.time()
        }
    
    def download_priority_files(self):
        """Download the most important files"""
        
        print("=" * 60)
        print("DOWNLOADING CORPORATE DATA FROM FLORIDA DOS")
        print("=" * 60)
        
        try:
            # Connect to SFTP
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
            print("✅ Connected to SFTP\n")
            
            # Priority files to download
            priority_files = [
                # The big comprehensive file
                ("/Public/doc/AG/corprindata.zip", "Complete corporate principal data (665MB)"),
                
                # Recent daily corporate files
                ("/Public/doc/cor/2024/20241209c.txt", "Most recent corporate filing"),
                ("/Public/doc/cor/2024/20241206c.txt", "Recent corporate filing"),
                
                # Try to find annual/officer files
                ("/Public/doc/annual/annual2024.txt", "Annual reports 2024"),
                ("/Public/doc/off/officers.txt", "Officer data"),
            ]
            
            downloaded = []
            
            for remote_path, description in priority_files:
                print(f"\n📦 {description}")
                print(f"   Path: {remote_path}")
                
                filename = Path(remote_path).name
                local_path = self.base_path / filename
                
                # Skip if exists
                if local_path.exists():
                    print(f"   ⏭️ Already downloaded")
                    downloaded.append(local_path)
                    continue
                
                try:
                    # Get file info
                    file_attr = sftp.stat(remote_path)
                    size_mb = file_attr.st_size / (1024 * 1024)
                    print(f"   Size: {size_mb:.1f} MB")
                    
                    # Download with progress
                    print(f"   📥 Downloading...")
                    start = time.time()
                    
                    # For large files, show progress
                    if size_mb > 10:
                        def progress_callback(transferred, total):
                            pct = (transferred / total) * 100
                            mb_done = transferred / (1024 * 1024)
                            if int(pct) % 10 == 0:
                                print(f"   ... {pct:.0f}% ({mb_done:.1f} MB)", end='\r')
                        
                        sftp.get(remote_path, str(local_path), callback=progress_callback)
                    else:
                        sftp.get(remote_path, str(local_path))
                    
                    elapsed = time.time() - start
                    speed = size_mb / elapsed if elapsed > 0 else 0
                    
                    print(f"   ✅ Downloaded in {elapsed:.1f}s ({speed:.1f} MB/s)")
                    self.stats['files_downloaded'] += 1
                    downloaded.append(local_path)
                    
                    # If it's a ZIP, check contents
                    if local_path.suffix.lower() == '.zip':
                        self.check_zip_contents(local_path)
                    
                except FileNotFoundError:
                    print(f"   ❌ File not found")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
            # List what's actually in the directories
            print("\n" + "=" * 60)
            print("EXPLORING AVAILABLE DATA")
            print("=" * 60)
            
            # Check /Public/doc for all subdirectories
            doc_path = "/Public/doc"
            try:
                subdirs = sftp.listdir(doc_path)
                print(f"\n📁 Available data types in {doc_path}:")
                for subdir in subdirs:
                    try:
                        subpath = f"{doc_path}/{subdir}"
                        items = sftp.listdir(subpath)
                        print(f"   - {subdir}/: {len(items)} items")
                        
                        # Check for interesting files
                        if subdir in ['off', 'annual', 'AG']:
                            print(f"     ⭐ May contain officer/contact data!")
                            
                            # Show first few files
                            for item in items[:3]:
                                print(f"       • {item}")
                                
                    except:
                        pass
                        
            except Exception as e:
                print(f"Error exploring: {e}")
            
            sftp.close()
            ssh.close()
            
            return downloaded
            
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return []
    
    def check_zip_contents(self, zip_path: Path):
        """Check ZIP file for emails and data structure"""
        print(f"\n   📂 Analyzing ZIP contents...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                files = zf.namelist()
                print(f"   Contains {len(files)} files")
                
                # Show first few files
                for f in files[:5]:
                    info = zf.getinfo(f)
                    size_mb = info.file_size / (1024 * 1024)
                    print(f"     - {f} ({size_mb:.1f} MB)")
                
                # Check a sample for emails
                if files:
                    first_file = files[0]
                    with zf.open(first_file) as f:
                        sample = f.read(1024 * 100)  # Read 100KB sample
                        
                        # Decode
                        try:
                            text = sample.decode('utf-8', errors='ignore')
                        except:
                            text = sample.decode('latin-1', errors='ignore')
                        
                        # Look for emails
                        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                        emails = re.findall(email_pattern, text)
                        
                        if emails:
                            print(f"   ✅ Found {len(emails)} emails in sample!")
                            print(f"   Sample emails: {', '.join(emails[:3])}")
                            self.stats['emails_found'] += len(emails)
                        else:
                            print(f"   ⚠️ No emails found in sample")
                            
                            # Check for phone numbers
                            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
                            phones = re.findall(phone_pattern, text)
                            if phones:
                                print(f"   📞 Found {len(phones)} phone numbers")
                        
        except Exception as e:
            print(f"   Error analyzing ZIP: {e}")
    
    def process_downloaded_files(self, files: list):
        """Process downloaded files for officer/email data"""
        print("\n" + "=" * 60)
        print("PROCESSING DOWNLOADED FILES")
        print("=" * 60)
        
        conn = psycopg2.connect(**self.conn_params)
        cur = conn.cursor()
        
        # Ensure tables exist
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sunbiz_principal_data (
                id SERIAL PRIMARY KEY,
                doc_number VARCHAR(20),
                entity_name VARCHAR(500),
                principal_name VARCHAR(500),
                principal_title VARCHAR(200),
                principal_address VARCHAR(500),
                principal_city VARCHAR(100),
                principal_state VARCHAR(10),
                principal_zip VARCHAR(20),
                principal_email VARCHAR(255),
                principal_phone VARCHAR(50),
                source_file VARCHAR(255),
                import_date TIMESTAMP DEFAULT NOW()
            );
            
            CREATE INDEX IF NOT EXISTS idx_principal_email 
                ON sunbiz_principal_data(principal_email) 
                WHERE principal_email IS NOT NULL;
        """)
        conn.commit()
        
        for file_path in files:
            print(f"\n📄 Processing: {file_path.name}")
            
            if file_path.suffix.lower() == '.zip':
                # Extract and process ZIP
                try:
                    with zipfile.ZipFile(file_path, 'r') as zf:
                        extract_dir = self.base_path / "extracted"
                        extract_dir.mkdir(exist_ok=True)
                        
                        for member in zf.namelist():
                            print(f"   Extracting: {member}")
                            zf.extract(member, extract_dir)
                            
                            extracted_file = extract_dir / member
                            if extracted_file.suffix.lower() in ['.txt', '.csv']:
                                self.process_text_file(extracted_file, cur, conn)
                                
                except Exception as e:
                    print(f"   Error processing ZIP: {e}")
                    
            elif file_path.suffix.lower() in ['.txt', '.csv']:
                self.process_text_file(file_path, cur, conn)
        
        conn.close()
        
    def process_text_file(self, file_path: Path, cur, conn):
        """Process a text file for corporate/officer data"""
        print(f"   📝 Reading: {file_path.name}")
        
        try:
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        lines = f.readlines()
                    break
                except UnicodeDecodeError:
                    continue
            
            batch = []
            emails_in_file = 0
            
            for line in lines[:10000]:  # Process first 10k lines
                # Look for email pattern
                if '@' in line:
                    email_match = re.search(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', line)
                    if email_match:
                        email = email_match.group(1).lower()
                        emails_in_file += 1
                        
                        # Parse line for other data
                        parts = line.split('|') if '|' in line else line.split('\t')
                        
                        record = {
                            'doc_number': parts[0][:20] if parts else '',
                            'entity_name': parts[1][:500] if len(parts) > 1 else '',
                            'principal_email': email[:255],
                            'source_file': file_path.name[:255]
                        }
                        
                        batch.append(record)
                        
                        if len(batch) >= 100:
                            self.insert_batch(cur, conn, batch)
                            batch = []
            
            if batch:
                self.insert_batch(cur, conn, batch)
            
            if emails_in_file > 0:
                print(f"   ✅ Found {emails_in_file} emails!")
                self.stats['emails_found'] += emails_in_file
            
            self.stats['records_processed'] += len(lines)
            
        except Exception as e:
            print(f"   Error processing file: {e}")
    
    def insert_batch(self, cur, conn, batch):
        """Insert batch of records"""
        try:
            values = [
                (
                    r.get('doc_number'),
                    r.get('entity_name'),
                    r.get('principal_name'),
                    r.get('principal_title'),
                    r.get('principal_address'),
                    r.get('principal_city'),
                    r.get('principal_state'),
                    r.get('principal_zip'),
                    r.get('principal_email'),
                    r.get('principal_phone'),
                    r.get('source_file')
                )
                for r in batch
            ]
            
            execute_values(
                cur,
                """
                INSERT INTO sunbiz_principal_data 
                (doc_number, entity_name, principal_name, principal_title,
                 principal_address, principal_city, principal_state, principal_zip,
                 principal_email, principal_phone, source_file)
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                values
            )
            
            conn.commit()
            
        except Exception as e:
            print(f"   DB error: {e}")
            conn.rollback()
    
    def run(self):
        """Main execution"""
        # Download files
        downloaded = self.download_priority_files()
        
        if downloaded:
            # Process downloaded files
            self.process_downloaded_files(downloaded)
        
        # Summary
        elapsed = time.time() - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("DOWNLOAD AND PROCESSING COMPLETE")
        print("=" * 60)
        print(f"✅ Files downloaded: {self.stats['files_downloaded']}")
        print(f"📊 Records processed: {self.stats['records_processed']:,}")
        print(f"📧 Emails found: {self.stats['emails_found']:,}")
        print(f"⏱️ Total time: {elapsed:.1f} seconds")
        
        if self.stats['emails_found'] > 0:
            print(f"\n✅ SUCCESS! Found email addresses in the data")
            print("Query: SELECT * FROM sunbiz_principal_data WHERE principal_email IS NOT NULL LIMIT 10;")
        
        print("\n💡 NEXT STEPS:")
        print("1. The corprindata.zip file (665MB) likely contains ALL principal/officer data")
        print("2. Download and process it fully for comprehensive email extraction")
        print("3. Check /Public/doc/off/ directory for specific officer files")
        print("4. Check /Public/doc/annual/ for annual report data with contacts")

if __name__ == "__main__":
    downloader = CorporateDataDownloader()
    downloader.run()