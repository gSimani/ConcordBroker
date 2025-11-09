"""
Sunbiz FTP Downloader for Officer Contact Information
Downloads officer/director contact data from the Florida Department of State FTP server
"""

import ftplib
import os
import sys
import io
import re
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import tempfile
from supabase import create_client

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SunbizFTPContactDownloader:
    """Download and process Sunbiz officer contact information"""
    
    def __init__(self):
        # FTP credentials from the user
        self.ftp_host = "sftp.floridados.gov"
        self.ftp_user = "Public"
        self.ftp_pass = "PubAccess1845!"
        
        # Local storage
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\SUNBIZ_CONTACTS")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Supabase connection
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Contact patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\(]?[0-9]{3}[\)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}')
        
        # Progress tracking
        self.files_processed = 0
        self.contacts_found = 0
        self.contacts_loaded = 0
        
    def connect_ftp(self) -> ftplib.FTP:
        """Connect to the Sunbiz FTP server"""
        print(f"Connecting to {self.ftp_host}...")
        
        try:
            # Try regular FTP first
            ftp = ftplib.FTP()
            ftp.connect(self.ftp_host, 21)
            ftp.login(self.ftp_user, self.ftp_pass)
            print("✅ Connected via FTP")
            return ftp
            
        except Exception as e:
            print(f"FTP connection failed: {e}")
            try:
                # Try FTP_TLS
                ftp = ftplib.FTP_TLS()
                ftp.connect(self.ftp_host, 21)
                ftp.login(self.ftp_user, self.ftp_pass)
                ftp.prot_p()  # Enable protection
                print("✅ Connected via FTP_TLS")
                return ftp
                
            except Exception as e2:
                print(f"FTP_TLS connection failed: {e2}")
                raise Exception(f"All FTP connection methods failed: {e}, {e2}")
    
    def explore_directory_structure(self, ftp: ftplib.FTP) -> Dict:
        """Explore the FTP directory structure"""
        print("\nExploring directory structure...")
        
        structure = {}
        
        try:
            # Start from root
            ftp.cwd('/')
            items = []
            ftp.retrlines('LIST', items.append)
            
            print("Root directory contents:")
            for item in items[:10]:  # Show first 10 items
                print(f"  {item}")
            
            # Look for common directories
            common_dirs = ['public', 'doc', 'data', 'files']
            
            for directory in common_dirs:
                try:
                    ftp.cwd(f'/{directory}')
                    sub_items = []
                    ftp.retrlines('LIST', sub_items.append)
                    structure[directory] = sub_items[:5]  # First 5 items
                    print(f"\n{directory}/ directory contents:")
                    for item in sub_items[:5]:
                        print(f"  {item}")
                        
                except Exception as e:
                    print(f"Cannot access /{directory}: {e}")
            
            # Look specifically for officer/contact data
            target_dirs = ['off', 'officers', 'directors', 'contacts']
            
            for target in target_dirs:
                try:
                    ftp.cwd(f'/public/doc/{target}')
                    target_items = []
                    ftp.retrlines('LIST', target_items.append)
                    structure[f'public/doc/{target}'] = target_items
                    print(f"\nFound target directory: /public/doc/{target}")
                    for item in target_items[:3]:
                        print(f"  {item}")
                        
                except Exception as e:
                    print(f"Cannot access /public/doc/{target}: {e}")
                    
        except Exception as e:
            print(f"Error exploring directory: {e}")
        
        return structure
    
    def download_officer_files(self, ftp: ftplib.FTP) -> List[Path]:
        """Download officer/director files containing contact information"""
        print("\nDownloading officer contact files...")
        
        downloaded_files = []
        
        # Target directories that likely contain contact info
        target_paths = [
            '/public/doc/off',  # Officers
            '/public/doc/AG',   # Registered Agents
            '/public/doc/annual',  # Annual reports (may have contact updates)
        ]
        
        for target_path in target_paths:
            try:
                print(f"\nChecking {target_path}...")
                ftp.cwd(target_path)
                
                # List files
                files = []
                ftp.retrlines('LIST', files.append)
                
                # Filter for recent files (text files)
                text_files = [f for f in files if '.txt' in f.lower()]
                
                print(f"Found {len(text_files)} text files")
                
                # Download first few files for analysis
                for file_line in text_files[:3]:  # Download first 3 files
                    # Parse file name from LIST output
                    file_name = file_line.split()[-1]
                    
                    if file_name.endswith('.txt'):
                        local_path = self.base_path / f"{target_path.replace('/', '_')}_{file_name}"
                        
                        print(f"Downloading {file_name}...")
                        try:
                            with open(local_path, 'wb') as f:
                                ftp.retrbinary(f'RETR {file_name}', f.write)
                            
                            downloaded_files.append(local_path)
                            print(f"✅ Downloaded {file_name} ({local_path.stat().st_size} bytes)")
                            
                        except Exception as e:
                            print(f"❌ Error downloading {file_name}: {e}")
                
            except Exception as e:
                print(f"Cannot access {target_path}: {e}")
        
        return downloaded_files
    
    def parse_contact_information(self, file_path: Path) -> List[Dict]:
        """Parse contact information from downloaded files"""
        print(f"\nParsing contacts from {file_path.name}...")
        
        contacts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Split into lines for processing
                lines = content.split('\n')
                
                for i, line in enumerate(lines):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Look for lines with contact information
                    emails = self.email_pattern.findall(line)
                    phones = self.phone_pattern.findall(line)
                    
                    if emails or phones:
                        # Try to extract officer/entity information from nearby lines
                        context_lines = lines[max(0, i-2):i+3]
                        context = ' '.join(context_lines)
                        
                        # Extract entity/officer name (usually before contact info)
                        entity_name = ""
                        officer_name = ""
                        
                        # Simple heuristics to find names
                        for ctx_line in context_lines:
                            if any(title in ctx_line.upper() for title in ['PRESIDENT', 'CEO', 'DIRECTOR', 'OFFICER', 'MANAGER']):
                                officer_name = ctx_line.strip()
                            elif any(word in ctx_line.upper() for word in ['LLC', 'INC', 'CORP', 'COMPANY']):
                                entity_name = ctx_line.strip()
                        
                        # Create contact record
                        contact = {
                            'entity_name': entity_name,
                            'officer_name': officer_name,
                            'emails': emails,
                            'phones': phones,
                            'source_file': file_path.name,
                            'source_line': i + 1,
                            'context': context[:200],  # First 200 chars for reference
                            'extracted_date': datetime.now().isoformat()
                        }
                        
                        contacts.append(contact)
                        self.contacts_found += 1
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
        
        print(f"Found {len(contacts)} contacts with email/phone information")
        return contacts
    
    def save_contacts_to_database(self, contacts: List[Dict]) -> int:
        \"\"\"Save extracted contacts to Supabase database\"\"\"
        print(f\"\\nSaving {len(contacts)} contacts to database...\")
        
        saved_count = 0
        
        for contact in contacts:
            try:
                # Prepare record for database
                db_record = {
                    'entity_name': contact['entity_name'][:100] if contact['entity_name'] else None,
                    'officer_name': contact['officer_name'][:100] if contact['officer_name'] else None,
                    'officer_email': contact['emails'][0] if contact['emails'] else None,
                    'officer_phone': contact['phones'][0] if contact['phones'] else None,
                    'additional_emails': ', '.join(contact['emails'][1:]) if len(contact['emails']) > 1 else None,
                    'additional_phones': ', '.join(contact['phones'][1:]) if len(contact['phones']) > 1 else None,
                    'source_file': contact['source_file'],
                    'source_line': contact['source_line'],
                    'context': contact['context'],
                    'extracted_date': contact['extracted_date'],
                    'import_date': datetime.now().isoformat()
                }
                
                # Insert into database
                result = self.supabase.table('sunbiz_officer_contacts').insert(db_record).execute()
                
                if result.data:
                    saved_count += 1
                
            except Exception as e:
                print(f\"Error saving contact: {e}\")
        
        print(f\"✅ Saved {saved_count} contacts to database\")
        return saved_count
    
    def run_contact_extraction(self) -> Dict:
        \"\"\"Main execution flow for contact extraction\"\"\"
        print(\"=\" * 60)
        print(\"SUNBIZ FTP CONTACT EXTRACTION\")
        print(\"=\" * 60)
        print(f\"Target directory: {self.base_path}\")
        
        results = {
            'start_time': datetime.now().isoformat(),
            'files_downloaded': 0,
            'contacts_found': 0,
            'contacts_saved': 0,
            'errors': []
        }
        
        try:
            # Connect to FTP
            ftp = self.connect_ftp()
            
            # Explore directory structure
            structure = self.explore_directory_structure(ftp)
            
            # Download officer files
            downloaded_files = self.download_officer_files(ftp)
            results['files_downloaded'] = len(downloaded_files)
            
            # Close FTP connection
            ftp.quit()
            print(\"\\n✅ FTP connection closed\")
            
            # Process downloaded files
            all_contacts = []
            for file_path in downloaded_files:
                contacts = self.parse_contact_information(file_path)
                all_contacts.extend(contacts)
            
            results['contacts_found'] = len(all_contacts)
            
            # Save to database
            if all_contacts:
                saved_count = self.save_contacts_to_database(all_contacts)
                results['contacts_saved'] = saved_count
            
            # Create summary report
            self.create_summary_report(results, all_contacts[:10])  # First 10 contacts
            
        except Exception as e:
            error_msg = f\"Critical error: {e}\"
            print(f\"❌ {error_msg}\")
            results['errors'].append(error_msg)
        
        results['end_time'] = datetime.now().isoformat()
        return results
    
    def create_summary_report(self, results: Dict, sample_contacts: List[Dict]):
        \"\"\"Create a summary report of the extraction\"\"\"
        report_path = self.base_path / f\"contact_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt\"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(\"SUNBIZ CONTACT EXTRACTION REPORT\\n\")
            f.write(\"=\" * 50 + \"\\n\\n\")
            
            f.write(f\"Extraction Date: {results['start_time']}\\n\")
            f.write(f\"Files Downloaded: {results['files_downloaded']}\\n\")
            f.write(f\"Contacts Found: {results['contacts_found']}\\n\")
            f.write(f\"Contacts Saved: {results['contacts_saved']}\\n\\n\")
            
            if results['errors']:
                f.write(\"ERRORS:\\n\")
                for error in results['errors']:
                    f.write(f\"  - {error}\\n\")
                f.write(\"\\n\")
            
            f.write(\"SAMPLE CONTACTS:\\n\")
            f.write(\"-\" * 30 + \"\\n\")
            for i, contact in enumerate(sample_contacts, 1):
                f.write(f\"\\n{i}. Entity: {contact['entity_name']}\\n\")
                f.write(f\"   Officer: {contact['officer_name']}\\n\")
                f.write(f\"   Emails: {', '.join(contact['emails'])}\\n\")
                f.write(f\"   Phones: {', '.join(contact['phones'])}\\n\")
                f.write(f\"   Source: {contact['source_file']}\\n\")
        
        print(f\"\\n📄 Report saved: {report_path}\")


def main():
    \"\"\"Main entry point\"\"\"
    downloader = SunbizFTPContactDownloader()
    results = downloader.run_contact_extraction()
    
    print(\"\\n\" + \"=\" * 60)
    print(\"EXTRACTION COMPLETE\")
    print(\"=\" * 60)
    print(f\"Files Downloaded: {results['files_downloaded']}\")
    print(f\"Contacts Found: {results['contacts_found']}\")
    print(f\"Contacts Saved: {results['contacts_saved']}\")
    
    if results['errors']:
        print(f\"\\nErrors: {len(results['errors'])}\")
        for error in results['errors']:
            print(f\"  - {error}\")


if __name__ == \"__main__\":
    main()