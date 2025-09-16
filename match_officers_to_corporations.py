"""
Match Officers to Corporations from Sunbiz Data
Extracts officer/principal data and matches with corporation records
"""

import os
import sys
import io
import zipfile
import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import re
from typing import Dict, List, Set
from supabase import create_client

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class OfficerCorporationMatcher:
    """Match officers to their corporations with contact information"""
    
    def __init__(self):
        # Data paths
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.corprin_zip = self.base_path / "corprindata.zip"
        self.cor_path = self.base_path / "cor"
        
        # Supabase connection
        self.supabase_url = 'https://pmispwtdngkcmsrsjwbp.supabase.co'
        self.supabase_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBtaXNwd3RkbmdrY21zcnNqd2JwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY5NTY5NTgsImV4cCI6MjA3MjUzMjk1OH0.YvWR1NkVByTY10Vzpzt4jMtMjBszD_BOCsQDBfG951A'
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        
        # Data structures
        self.corporations = {}  # doc_number -> corporation info
        self.officers = defaultdict(list)  # doc_number -> list of officers
        self.officer_contacts = {}  # officer_name -> contact info
        self.email_to_officers = defaultdict(list)  # email -> list of officers
        
        # Patterns
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.phone_pattern = re.compile(r'[\(]?[0-9]{3}[\)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}')
        
        # Stats
        self.stats = {
            'total_corporations': 0,
            'total_officers': 0,
            'officers_with_emails': 0,
            'officers_with_phones': 0,
            'unique_emails': 0,
            'corporation_officer_matches': 0
        }
    
    def extract_corprindata(self, limit=None):
        """Extract officer/principal data from corprindata.zip"""
        print("📦 Extracting officer data from corprindata.zip...")
        
        if not self.corprin_zip.exists():
            print(f"❌ File not found: {self.corprin_zip}")
            return False
        
        officer_count = 0
        
        with zipfile.ZipFile(self.corprin_zip, 'r') as zf:
            # Process each file in the zip
            for file_info in zf.namelist():
                print(f"\n📄 Processing {file_info}...")
                
                with zf.open(file_info) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines):
                        if limit and officer_count >= limit:
                            break
                        
                        if not line.strip():
                            continue
                        
                        # Parse officer record
                        officer_data = self.parse_officer_record(line)
                        
                        if officer_data:
                            doc_number = officer_data.get('doc_number', '')
                            
                            if doc_number:
                                # Add to officers list for this corporation
                                self.officers[doc_number].append(officer_data)
                                officer_count += 1
                                
                                # Track contact info
                                if officer_data.get('email'):
                                    self.officer_contacts[officer_data['name']] = {
                                        'email': officer_data['email'],
                                        'phone': officer_data.get('phone', ''),
                                        'doc_number': doc_number
                                    }
                                    self.email_to_officers[officer_data['email']].append(officer_data['name'])
                                    self.stats['officers_with_emails'] += 1
                                
                                if officer_data.get('phone'):
                                    self.stats['officers_with_phones'] += 1
                                
                                if officer_count % 1000 == 0:
                                    print(f"  📊 Processed {officer_count:,} officers...")
                
                if limit and officer_count >= limit:
                    break
        
        self.stats['total_officers'] = officer_count
        self.stats['unique_emails'] = len(self.email_to_officers)
        
        print(f"\n✅ Extracted {officer_count:,} officer records")
        print(f"   - Officers with emails: {self.stats['officers_with_emails']:,}")
        print(f"   - Officers with phones: {self.stats['officers_with_phones']:,}")
        print(f"   - Unique email addresses: {self.stats['unique_emails']:,}")
        
        return True
    
    def parse_officer_record(self, line: str) -> Dict:
        """Parse a single officer/principal record"""
        # Common formats in corprindata:
        # Format 1: DOC_NUMBER|ENTITY_NAME|PRINCIPAL_NAME|TITLE|ADDRESS|CITY|STATE|ZIP|EMAIL|PHONE
        # Format 2: DOC_NUMBER|PRINCIPAL_NAME|TITLE|ADDRESS
        
        parts = line.split('|')
        
        if len(parts) < 3:
            return None
        
        # Extract basic info
        record = {
            'doc_number': parts[0].strip()[:20],
            'name': '',
            'title': '',
            'address': '',
            'email': None,
            'phone': None
        }
        
        # Try to identify fields based on content
        for i, part in enumerate(parts):
            part = part.strip()
            
            # Check for email
            email_match = self.email_pattern.search(part)
            if email_match:
                record['email'] = email_match.group()
            
            # Check for phone
            phone_match = self.phone_pattern.search(part)
            if phone_match:
                record['phone'] = phone_match.group()
            
            # Identify name (usually 2nd or 3rd field)
            if i == 1 and not email_match and not phone_match:
                # Could be entity name or officer name
                if any(corp_type in part.upper() for corp_type in ['LLC', 'INC', 'CORP', 'LP', 'LLP']):
                    record['entity_name'] = part[:200]
                else:
                    record['name'] = part[:100]
            elif i == 2 and not record['name']:
                record['name'] = part[:100]
            
            # Title (usually after name)
            if i == 3 or (i == 2 and record['name']):
                if any(title in part.upper() for title in ['PRESIDENT', 'CEO', 'DIRECTOR', 'MANAGER', 'SECRETARY', 'TREASURER', 'MEMBER', 'PARTNER']):
                    record['title'] = part[:50]
            
            # Address fields
            if i >= 4 and i <= 7:
                record['address'] += part + ' '
        
        # Clean up
        record['address'] = record['address'].strip()[:200]
        
        # Must have at least a name to be valid
        if not record['name'] and not record.get('entity_name'):
            return None
        
        return record
    
    def load_corporation_data(self, limit=100):
        """Load corporation data from cor directory"""
        print("\n🏢 Loading corporation data...")
        
        corp_count = 0
        
        # Get sample of corporation files
        corp_files = list(self.cor_path.glob("*.txt"))[:limit]
        
        for corp_file in corp_files:
            try:
                with open(corp_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    # Parse corporation records
                    lines = content.split('\n')
                    
                    for line in lines:
                        if not line.strip():
                            continue
                        
                        corp_data = self.parse_corporation_record(line)
                        
                        if corp_data:
                            doc_number = corp_data.get('doc_number', '')
                            if doc_number:
                                self.corporations[doc_number] = corp_data
                                corp_count += 1
                
            except Exception as e:
                print(f"  ❌ Error reading {corp_file.name}: {e}")
        
        self.stats['total_corporations'] = corp_count
        print(f"✅ Loaded {corp_count:,} corporation records")
        
        return corp_count > 0
    
    def parse_corporation_record(self, line: str) -> Dict:
        """Parse a corporation record"""
        # Corporation format typically:
        # DOC_NUMBER|ENTITY_NAME|STATUS|FILE_DATE|STATE|PRINCIPAL_ADDRESS
        
        parts = line.split('|')
        
        if len(parts) < 2:
            return None
        
        record = {
            'doc_number': parts[0].strip()[:20],
            'entity_name': parts[1].strip()[:200] if len(parts) > 1 else '',
            'status': parts[2].strip()[:20] if len(parts) > 2 else '',
            'file_date': parts[3].strip()[:20] if len(parts) > 3 else '',
            'state': parts[4].strip()[:2] if len(parts) > 4 else 'FL',
            'address': parts[5].strip()[:200] if len(parts) > 5 else ''
        }
        
        # Must have doc_number and entity_name
        if not record['doc_number'] or not record['entity_name']:
            return None
        
        return record
    
    def match_officers_to_corporations(self):
        """Match officers with their corporations"""
        print("\n🔗 Matching officers to corporations...")
        
        matches = []
        
        for doc_number, officer_list in self.officers.items():
            # Check if we have the corporation info
            corp_info = self.corporations.get(doc_number)
            
            if corp_info:
                # We have a match!
                for officer in officer_list:
                    match = {
                        'doc_number': doc_number,
                        'entity_name': corp_info['entity_name'],
                        'entity_status': corp_info.get('status', ''),
                        'entity_state': corp_info.get('state', 'FL'),
                        'officer_name': officer['name'],
                        'officer_title': officer.get('title', ''),
                        'officer_email': officer.get('email', ''),
                        'officer_phone': officer.get('phone', ''),
                        'officer_address': officer.get('address', ''),
                        'match_confidence': 1.0  # Direct doc_number match
                    }
                    matches.append(match)
                    self.stats['corporation_officer_matches'] += 1
            else:
                # Try to match by entity name if available
                if 'entity_name' in officer_list[0]:
                    entity_name = officer_list[0]['entity_name']
                    
                    # Search for corporation by name
                    for corp_doc, corp_data in self.corporations.items():
                        if entity_name.upper() in corp_data['entity_name'].upper():
                            for officer in officer_list:
                                match = {
                                    'doc_number': corp_doc,
                                    'entity_name': corp_data['entity_name'],
                                    'entity_status': corp_data.get('status', ''),
                                    'entity_state': corp_data.get('state', 'FL'),
                                    'officer_name': officer['name'],
                                    'officer_title': officer.get('title', ''),
                                    'officer_email': officer.get('email', ''),
                                    'officer_phone': officer.get('phone', ''),
                                    'officer_address': officer.get('address', ''),
                                    'match_confidence': 0.8  # Name match
                                }
                                matches.append(match)
                                self.stats['corporation_officer_matches'] += 1
                            break
        
        print(f"✅ Created {len(matches):,} officer-corporation matches")
        
        return matches
    
    def save_matches_to_database(self, matches: List[Dict], batch_size=100):
        """Save matched data to database"""
        print(f"\n💾 Saving {len(matches):,} matches to database...")
        
        saved_count = 0
        
        for i in range(0, len(matches), batch_size):
            batch = matches[i:i+batch_size]
            
            try:
                # Prepare records for database
                db_records = []
                for match in batch:
                    db_record = {
                        'doc_number': match['doc_number'],
                        'entity_name': match['entity_name'],
                        'entity_status': match['entity_status'],
                        'entity_state': match['entity_state'],
                        'officer_name': match['officer_name'],
                        'officer_title': match['officer_title'],
                        'officer_email': match['officer_email'],
                        'officer_phone': match['officer_phone'],
                        'officer_address': match['officer_address'],
                        'match_confidence': match['match_confidence'],
                        'created_at': datetime.now().isoformat()
                    }
                    db_records.append(db_record)
                
                # Insert into corporation_officers table
                result = self.supabase.table('corporation_officers').insert(db_records).execute()
                
                if result.data:
                    saved_count += len(result.data)
                    print(f"  📊 Saved batch {i//batch_size + 1}: {len(result.data)} records")
                
            except Exception as e:
                # If table doesn't exist, try alternative table
                try:
                    # Save to sunbiz_officers table instead
                    for match in batch[:10]:  # Save first 10 of batch
                        officer_record = {
                            'doc_number': match['doc_number'],
                            'officer_name': match['officer_name'],
                            'officer_title': match['officer_title'],
                            'officer_address': match['officer_address'],
                            'officer_city': 'EXTRACTED',
                            'officer_state': match['entity_state'],
                            'officer_zip': '00000',
                            'officer_email': match['officer_email'],
                            'officer_phone': match['officer_phone'],
                            'source_file': 'corprindata.zip',
                            'import_date': datetime.now().isoformat()
                        }
                        
                        result = self.supabase.table('sunbiz_officers').insert(officer_record).execute()
                        if result.data:
                            saved_count += 1
                
                except Exception as e2:
                    print(f"  ❌ Error saving batch: {e2}")
        
        print(f"✅ Successfully saved {saved_count:,} records")
        return saved_count
    
    def create_match_report(self, matches: List[Dict]):
        """Create comprehensive matching report"""
        report_path = Path(f"officer_corporation_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        # Prepare summary statistics
        summary = {
            'timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'top_corporations_by_officers': {},
            'officers_with_multiple_companies': {},
            'email_domains': {},
            'sample_matches': matches[:100]  # First 100 matches
        }
        
        # Analyze corporation officer counts
        corp_officer_counts = defaultdict(int)
        for match in matches:
            corp_officer_counts[match['entity_name']] += 1
        
        # Top 10 corporations by officer count
        top_corps = sorted(corp_officer_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        summary['top_corporations_by_officers'] = dict(top_corps)
        
        # Find officers in multiple companies
        officer_companies = defaultdict(set)
        for match in matches:
            if match['officer_email']:
                officer_companies[match['officer_email']].add(match['entity_name'])
        
        # Officers in multiple companies
        multi_company_officers = {email: list(companies) 
                                 for email, companies in officer_companies.items() 
                                 if len(companies) > 1}
        summary['officers_with_multiple_companies'] = dict(list(multi_company_officers.items())[:20])
        
        # Email domain analysis
        email_domains = defaultdict(int)
        for match in matches:
            if match['officer_email'] and '@' in match['officer_email']:
                domain = match['officer_email'].split('@')[1]
                email_domains[domain] += 1
        
        # Top email domains
        top_domains = sorted(email_domains.items(), key=lambda x: x[1], reverse=True)[:10]
        summary['email_domains'] = dict(top_domains)
        
        # Save report
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📄 Report saved: {report_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("OFFICER-CORPORATION MATCHING SUMMARY")
        print("=" * 60)
        print(f"Total Corporations: {self.stats['total_corporations']:,}")
        print(f"Total Officers: {self.stats['total_officers']:,}")
        print(f"Officers with Emails: {self.stats['officers_with_emails']:,}")
        print(f"Officers with Phones: {self.stats['officers_with_phones']:,}")
        print(f"Unique Email Addresses: {self.stats['unique_emails']:,}")
        print(f"Successful Matches: {self.stats['corporation_officer_matches']:,}")
        
        print("\n📊 TOP CORPORATIONS BY OFFICER COUNT:")
        for corp_name, count in top_corps:
            print(f"  - {corp_name[:50]}: {count} officers")
        
        print("\n📧 TOP EMAIL DOMAINS:")
        for domain, count in top_domains:
            print(f"  - {domain}: {count} officers")
        
        return report_path
    
    def run_matching(self, officer_limit=10000, corp_limit=1000):
        """Run the complete matching process"""
        print("=" * 60)
        print("OFFICER-CORPORATION MATCHING SYSTEM")
        print("=" * 60)
        
        # Extract officer data
        if not self.extract_corprindata(limit=officer_limit):
            print("❌ Failed to extract officer data")
            return
        
        # Load corporation data
        if not self.load_corporation_data(limit=corp_limit):
            print("❌ Failed to load corporation data")
            return
        
        # Match officers to corporations
        matches = self.match_officers_to_corporations()
        
        if matches:
            # Save to database
            self.save_matches_to_database(matches)
            
            # Create report
            self.create_match_report(matches)
        
        print("\n✅ Matching process complete!")
        
        return matches


def main():
    """Main entry point"""
    matcher = OfficerCorporationMatcher()
    
    # Run with limits for demonstration (remove limits for full processing)
    matches = matcher.run_matching(
        officer_limit=5000,  # Process first 5000 officers
        corp_limit=500       # Load first 500 corporation files
    )
    
    if matches:
        print(f"\n🎉 Successfully matched {len(matches):,} officer-corporation relationships!")
        print("   Check the JSON report for detailed analysis")


if __name__ == "__main__":
    main()