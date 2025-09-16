"""
Enhanced Sunbiz Contact Loader 
Uses existing sunbiz_officers table and adds contact enrichment
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

class SunbizEnhancedContactLoader:
    """Enhanced contact loader using existing infrastructure"""
    
    def __init__(self):
        # FTP credentials
        self.ftp_host = "sftp.floridados.gov"
        self.ftp_user = "Public"
        self.ftp_pass = "PubAccess1845!"
        
        # Local storage
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\SUNBIZ_ENHANCED")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Supabase connection
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Contact patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\(]?[0-9]{3}[\)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}')
        
        # Progress tracking
        self.processed_count = 0
        self.enhanced_count = 0
        self.new_contacts = 0
        
    def analyze_existing_data(self) -> Dict:
        """Analyze existing officer data"""
        print("🔍 Analyzing existing Sunbiz officer data...")
        
        try:
            # Get sample of existing data
            result = self.supabase.table('sunbiz_officers').select('*').limit(10).execute()
            
            analysis = {
                'total_records': 0,
                'has_emails': 0,
                'has_phones': 0,
                'sample_data': result.data if result.data else []
            }
            
            # Get total count
            count_result = self.supabase.table('sunbiz_officers').select('*', count='exact').limit(0).execute()
            analysis['total_records'] = count_result.count
            
            # Analyze sample for contact patterns
            for record in result.data:
                record_str = str(record).lower()
                if '@' in record_str:
                    analysis['has_emails'] += 1
                if len([c for c in record_str if c.isdigit()]) >= 10:
                    analysis['has_phones'] += 1
            
            print(f"📊 Analysis Results:")
            print(f"  Total records: {analysis['total_records']:,}")
            print(f"  Sample with emails: {analysis['has_emails']}/10")
            print(f"  Sample with phones: {analysis['has_phones']}/10")
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error analyzing data: {e}")
            return {}
    
    def try_ftp_connection(self) -> Optional[ftplib.FTP]:
        """Try different methods to connect to FTP"""
        print(f"🌐 Attempting FTP connection to {self.ftp_host}...")
        
        connection_methods = [
            ("Standard FTP", lambda: ftplib.FTP()),
            ("FTP with TLS", lambda: ftplib.FTP_TLS()),
        ]
        
        for method_name, ftp_creator in connection_methods:
            try:
                print(f"  Trying {method_name}...")
                ftp = ftp_creator()
                ftp.connect(self.ftp_host, 21)
                ftp.login(self.ftp_user, self.ftp_pass)
                
                if hasattr(ftp, 'prot_p'):
                    ftp.prot_p()  # Enable protection for FTP_TLS
                
                print(f"  ✅ {method_name} connection successful!")
                return ftp
                
            except Exception as e:
                print(f"  ❌ {method_name} failed: {e}")
                
        return None
    
    def explore_ftp_structure(self, ftp: ftplib.FTP) -> Dict:
        """Explore FTP directory structure for contact data"""
        print("🗂️  Exploring FTP directory structure...")
        
        structure = {}
        
        try:
            # Start from root and look for public directory
            ftp.cwd('/')
            root_items = []
            ftp.retrlines('LIST', root_items.append)
            
            print("Root directory contents:")
            for item in root_items[:5]:
                print(f"  {item}")
            
            # Navigate to public directory
            try:
                ftp.cwd('/public')
                public_items = []
                ftp.retrlines('LIST', public_items.append)
                structure['public'] = public_items
                print(f"\\nPublic directory has {len(public_items)} items")
                
                # Navigate to doc directory
                try:
                    ftp.cwd('/public/doc')
                    doc_items = []
                    ftp.retrlines('LIST', doc_items.append)
                    structure['public/doc'] = doc_items
                    
                    print(f"\\nDoc directory contents:")
                    for item in doc_items[:10]:
                        print(f"  {item}")
                    
                    # Look for officer/contact directories
                    contact_dirs = ['off', 'AG', 'annual', 'officers', 'contacts']
                    for contact_dir in contact_dirs:
                        try:
                            ftp.cwd(f'/public/doc/{contact_dir}')
                            contact_items = []
                            ftp.retrlines('LIST', contact_items.append)
                            structure[f'public/doc/{contact_dir}'] = contact_items
                            print(f"\\n✅ Found {contact_dir} directory with {len(contact_items)} items")
                            
                            # Show first few files
                            for item in contact_items[:3]:
                                print(f"    {item}")
                                
                        except Exception as e:
                            print(f"❌ {contact_dir} directory not accessible")
                
                except Exception as e:
                    print(f"❌ Cannot access /public/doc: {e}")
                    
            except Exception as e:
                print(f"❌ Cannot access /public: {e}")
                
        except Exception as e:
            print(f"❌ Error exploring structure: {e}")
        
        return structure
    
    def download_sample_contact_files(self, ftp: ftplib.FTP, structure: Dict) -> List[Path]:
        """Download sample files that likely contain contact information"""
        print("📥 Downloading sample contact files...")
        
        downloaded_files = []
        
        # Priority directories for contact information
        priority_dirs = [
            'public/doc/off',      # Officers/Directors
            'public/doc/AG',       # Registered Agents  
            'public/doc/annual'    # Annual reports (may have contact updates)
        ]
        
        for dir_path in priority_dirs:
            if dir_path not in structure:
                print(f"⏭️  Skipping {dir_path} (not found)")
                continue
                
            try:
                print(f"\\n📁 Processing {dir_path}...")
                ftp.cwd(f'/{dir_path}')
                
                # Get list of files
                file_items = structure[dir_path]
                
                # Filter for recent text files
                text_files = [item for item in file_items if '.txt' in item.lower()]
                
                print(f"  Found {len(text_files)} text files")
                
                # Download first 2 files for analysis
                for i, file_item in enumerate(text_files[:2]):
                    try:
                        # Extract filename from LIST output
                        file_name = file_item.split()[-1]
                        
                        if file_name.endswith('.txt'):
                            local_path = self.base_path / f"{dir_path.replace('/', '_')}_{file_name}"
                            
                            print(f"  📥 Downloading {file_name}...")
                            
                            with open(local_path, 'wb') as f:
                                ftp.retrbinary(f'RETR {file_name}', f.write)
                            
                            file_size = local_path.stat().st_size
                            print(f"  ✅ Downloaded {file_name} ({file_size:,} bytes)")
                            
                            downloaded_files.append(local_path)
                            
                    except Exception as e:
                        print(f"  ❌ Error downloading file: {e}")
                        
            except Exception as e:
                print(f"❌ Error processing {dir_path}: {e}")
        
        return downloaded_files
    
    def extract_enhanced_contacts(self, file_path: Path) -> List[Dict]:
        """Extract enhanced contact information from downloaded files"""
        print(f"🔍 Extracting contacts from {file_path.name}...")
        
        contacts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Look for email and phone patterns
                emails = self.email_pattern.findall(line)
                phones = self.phone_pattern.findall(line)
                
                if emails or phones:
                    # Extract context (surrounding lines)
                    context_start = max(0, i-2)
                    context_end = min(len(lines), i+3)
                    context_lines = lines[context_start:context_end]
                    
                    # Try to identify entity and officer names from context
                    entity_name = ""
                    officer_name = ""
                    officer_title = ""
                    
                    for ctx_line in context_lines:
                        ctx_upper = ctx_line.upper()
                        
                        # Look for officer titles
                        if any(title in ctx_upper for title in ['PRESIDENT', 'CEO', 'DIRECTOR', 'OFFICER', 'MANAGER', 'SECRETARY']):
                            officer_title = ctx_line.strip()
                            
                        # Look for entity identifiers
                        if any(entity_type in ctx_upper for entity_type in ['LLC', 'INC', 'CORP', 'COMPANY', 'PARTNERSHIP']):
                            entity_name = ctx_line.strip()
                    
                    # Create enhanced contact record
                    contact = {
                        'entity_name': entity_name[:100] if entity_name else None,
                        'officer_name': officer_name[:100] if officer_name else None,
                        'officer_title': officer_title[:50] if officer_title else None,
                        'officer_email': emails[0] if emails else None,
                        'officer_phone': phones[0] if phones else None,
                        'source_file': file_path.name,
                        'import_date': datetime.now().isoformat(),
                        'additional_data': {
                            'all_emails': emails,
                            'all_phones': phones,
                            'context': ' '.join(context_lines).strip()[:500],
                            'line_number': i + 1
                        }
                    }
                    
                    contacts.append(contact)
            
            print(f"  ✅ Extracted {len(contacts)} enhanced contacts")
            
        except Exception as e:
            print(f"  ❌ Error extracting from {file_path.name}: {e}")
        
        return contacts
    
    def enhance_existing_officers(self, new_contacts: List[Dict]) -> int:
        """Add new contact records to existing sunbiz_officers table"""
        print(f"💾 Adding {len(new_contacts)} enhanced contacts to database...")
        
        added_count = 0
        
        for contact in new_contacts:
            try:
                # Create record for sunbiz_officers table
                officer_record = {
                    'doc_number': f"ENHANCED_{datetime.now().strftime('%Y%m%d%H%M%S')}_{added_count}",
                    'officer_name': contact['officer_name'] or 'ENHANCED CONTACT',
                    'officer_title': contact['officer_title'] or 'CONTACT',
                    'officer_address': 'FTP ENHANCED',
                    'officer_city': 'ENHANCED',
                    'officer_state': 'FL',
                    'officer_zip': '00000',
                    'officer_email': contact['officer_email'],
                    'officer_phone': contact['officer_phone'],
                    'source_file': contact['source_file'],
                    'import_date': contact['import_date']
                }
                
                # Insert into database
                result = self.supabase.table('sunbiz_officers').insert(officer_record).execute()
                
                if result.data:
                    added_count += 1
                    if added_count % 10 == 0:
                        print(f"  📊 Added {added_count} contacts...")
                
            except Exception as e:
                print(f"  ❌ Error adding contact: {e}")
        
        print(f"✅ Successfully added {added_count} enhanced contacts")
        return added_count
    
    def create_summary_report(self, results: Dict):
        """Create detailed summary report"""
        report_path = self.base_path / f"enhanced_contact_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("SUNBIZ ENHANCED CONTACT EXTRACTION REPORT\\n")
            f.write("=" * 50 + "\\n\\n")
            
            f.write(f"Extraction Date: {results.get('start_time', 'N/A')}\\n")
            f.write(f"Files Downloaded: {results.get('files_downloaded', 0)}\\n")
            f.write(f"Contacts Found: {results.get('contacts_found', 0)}\\n")
            f.write(f"Contacts Added: {results.get('contacts_added', 0)}\\n")
            f.write(f"Total Officer Records: {results.get('total_officers', 0)}\\n\\n")
            
            if results.get('errors'):
                f.write("ERRORS:\\n")
                for error in results['errors']:
                    f.write(f"  - {error}\\n")
                f.write("\\n")
            
            f.write("FTP STRUCTURE EXPLORED:\\n")
            f.write("-" * 30 + "\\n")
            for dir_name, items in results.get('ftp_structure', {}).items():
                f.write(f"\\n{dir_name}:\\n")
                for item in items[:5]:  # First 5 items
                    f.write(f"  {item}\\n")
        
        print(f"📄 Report saved: {report_path}")
    
    def run_enhanced_extraction(self) -> Dict:
        """Main execution flow"""
        print("=" * 60)
        print("SUNBIZ ENHANCED CONTACT EXTRACTION")
        print("=" * 60)
        
        results = {
            'start_time': datetime.now().isoformat(),
            'files_downloaded': 0,
            'contacts_found': 0,
            'contacts_added': 0,
            'total_officers': 0,
            'errors': [],
            'ftp_structure': {}
        }
        
        try:
            # Analyze existing data
            analysis = self.analyze_existing_data()
            results['total_officers'] = analysis.get('total_records', 0)
            
            # Try FTP connection
            ftp = self.try_ftp_connection()
            if not ftp:
                raise Exception("All FTP connection methods failed")
            
            # Explore structure
            structure = self.explore_ftp_structure(ftp)
            results['ftp_structure'] = structure
            
            # Download sample files
            downloaded_files = self.download_sample_contact_files(ftp, structure)
            results['files_downloaded'] = len(downloaded_files)
            
            # Close FTP
            ftp.quit()
            print("\\n✅ FTP connection closed")
            
            # Extract contacts from downloaded files
            all_contacts = []
            for file_path in downloaded_files:
                contacts = self.extract_enhanced_contacts(file_path)
                all_contacts.extend(contacts)
            
            results['contacts_found'] = len(all_contacts)
            
            # Add to database
            if all_contacts:
                added_count = self.enhance_existing_officers(all_contacts)
                results['contacts_added'] = added_count
            
            # Create report
            self.create_summary_report(results)
            
        except Exception as e:
            error_msg = f"Critical error: {e}"
            print(f"❌ {error_msg}")
            results['errors'].append(error_msg)
        
        results['end_time'] = datetime.now().isoformat()
        return results


def main():
    """Main execution"""
    loader = SunbizEnhancedContactLoader()
    results = loader.run_enhanced_extraction()
    
    print("\\n" + "=" * 60)
    print("ENHANCED EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Files Downloaded: {results['files_downloaded']}")
    print(f"Contacts Found: {results['contacts_found']}")
    print(f"Contacts Added: {results['contacts_added']}")
    print(f"Total Officers Now: {results['total_officers'] + results['contacts_added']}")
    
    if results['errors']:
        print(f"\\nErrors: {len(results['errors'])}")


if __name__ == "__main__":
    main()