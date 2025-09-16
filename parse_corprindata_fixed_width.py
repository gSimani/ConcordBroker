"""
Parse corprindata.zip using fixed-width format
Extracts officer information and matches to corporations
"""

import sys
import io
import zipfile
from pathlib import Path
import json
import re
from datetime import datetime
from collections import defaultdict
import psycopg2
from psycopg2.extras import execute_values
from urllib.parse import urlparse

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CorprinDataParser:
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.corprin_file = self.base_path / "corprindata.zip"
        
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
        
        # Data storage
        self.officers = []
        self.corporations = defaultdict(list)
        self.emails_found = set()
        self.phones_found = set()
        
    def parse_fixed_width_line(self, line):
        """Parse a fixed-width format line from corprindata"""
        if not line or len(line) < 20:
            return None
            
        try:
            # Fixed-width positions based on observed format
            # Doc number: 0-15 (includes suffix letter sometimes)
            # Type code: 15-16 (P=Principal, C=Corporation, etc)
            # Name fields vary based on type
            
            doc_number = line[0:12].strip()
            type_code = line[15:16] if len(line) > 15 else ''
            
            if not doc_number:
                return None
                
            record = {
                'doc_number': doc_number,
                'type': type_code,
                'raw_line': line
            }
            
            # Parse based on type
            if type_code == 'P':  # Principal/Officer
                # Extract name parts
                last_name = line[16:36].strip() if len(line) > 36 else ''
                first_name = line[36:50].strip() if len(line) > 50 else ''
                middle = line[50:52].strip() if len(line) > 52 else ''
                suffix = line[52:56].strip() if len(line) > 56 else ''
                
                # Extract address
                address1 = line[56:96].strip() if len(line) > 96 else ''
                city = line[96:124].strip() if len(line) > 124 else ''
                state = line[124:126].strip() if len(line) > 126 else ''
                zip_code = line[126:136].strip() if len(line) > 136 else ''
                
                record.update({
                    'name': f"{first_name} {middle} {last_name} {suffix}".strip(),
                    'first_name': first_name,
                    'last_name': last_name,
                    'address': address1,
                    'city': city,
                    'state': state,
                    'zip': zip_code
                })
                
            elif type_code == 'C':  # Corporation
                # Corporation name is in different position
                corp_name = line[16:96].strip() if len(line) > 96 else ''
                address = line[96:136].strip() if len(line) > 136 else ''
                city = line[136:164].strip() if len(line) > 164 else ''
                state = line[164:166].strip() if len(line) > 166 else ''
                zip_code = line[166:176].strip() if len(line) > 176 else ''
                
                record.update({
                    'name': corp_name,
                    'address': address,
                    'city': city,
                    'state': state,
                    'zip': zip_code
                })
            
            # Extract email if present anywhere in line
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, line, re.IGNORECASE)
            if emails:
                record['email'] = emails[0].lower()
                self.emails_found.add(emails[0].lower())
            
            # Extract phone if present
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            phones = re.findall(phone_pattern, line)
            if phones:
                record['phone'] = phones[0]
                self.phones_found.add(phones[0])
                
            return record
            
        except Exception as e:
            return None
    
    def process_zip_file(self):
        """Process the corprindata.zip file"""
        print(f"\n📂 Processing {self.corprin_file.name}...")
        
        total_lines = 0
        valid_records = 0
        
        with zipfile.ZipFile(self.corprin_file, 'r') as zf:
            files = zf.namelist()
            print(f"Found {len(files)} files in ZIP")
            
            for filename in files:
                print(f"\n📄 Processing {filename}...")
                
                with zf.open(filename) as f:
                    content = f.read().decode('utf-8', errors='ignore')
                    lines = content.split('\n')
                    
                    for line in lines:
                        total_lines += 1
                        record = self.parse_fixed_width_line(line)
                        
                        if record:
                            valid_records += 1
                            
                            # Store based on type
                            if record['type'] == 'P':
                                self.officers.append(record)
                            elif record['type'] == 'C':
                                # Group corporations by doc_number
                                self.corporations[record['doc_number']].append(record)
                            
                            # Progress update
                            if valid_records % 10000 == 0:
                                print(f"   Processed {valid_records:,} records | "
                                      f"Officers: {len(self.officers):,} | "
                                      f"Corps: {len(self.corporations):,} | "
                                      f"Emails: {len(self.emails_found):,}")
        
        print(f"\n✅ Processing complete!")
        print(f"   Total lines: {total_lines:,}")
        print(f"   Valid records: {valid_records:,}")
        print(f"   Officers found: {len(self.officers):,}")
        print(f"   Corporations found: {len(self.corporations):,}")
        print(f"   Email addresses: {len(self.emails_found):,}")
        print(f"   Phone numbers: {len(self.phones_found):,}")
    
    def match_officers_to_corporations(self):
        """Match officers to their corporations"""
        print("\n🔗 Matching officers to corporations...")
        
        matches = []
        
        for officer in self.officers:
            doc_num = officer['doc_number']
            
            # Find matching corporation
            if doc_num in self.corporations:
                corps = self.corporations[doc_num]
                for corp in corps:
                    match = {
                        'doc_number': doc_num,
                        'officer_name': officer.get('name', ''),
                        'officer_address': officer.get('address', ''),
                        'officer_city': officer.get('city', ''),
                        'officer_state': officer.get('state', ''),
                        'officer_zip': officer.get('zip', ''),
                        'officer_email': officer.get('email'),
                        'officer_phone': officer.get('phone'),
                        'corp_name': corp.get('name', ''),
                        'corp_address': corp.get('address', ''),
                        'corp_city': corp.get('city', ''),
                        'corp_state': corp.get('state', ''),
                        'corp_zip': corp.get('zip', '')
                    }
                    matches.append(match)
        
        print(f"✅ Created {len(matches):,} officer-corporation matches")
        
        # Save matches with contact info
        contacts_only = [m for m in matches if m.get('officer_email') or m.get('officer_phone')]
        print(f"   Matches with contact info: {len(contacts_only):,}")
        
        return matches
    
    def save_to_database(self, matches):
        """Save matches to database"""
        if not matches:
            print("No matches to save")
            return
            
        print(f"\n💾 Saving {len(matches):,} matches to database...")
        
        conn = psycopg2.connect(**self.conn_params)
        cur = conn.cursor()
        
        try:
            # Create table if not exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sunbiz_officer_corporation_matches (
                    id SERIAL PRIMARY KEY,
                    doc_number VARCHAR(20),
                    officer_name VARCHAR(500),
                    officer_address VARCHAR(500),
                    officer_city VARCHAR(100),
                    officer_state VARCHAR(10),
                    officer_zip VARCHAR(20),
                    officer_email VARCHAR(255),
                    officer_phone VARCHAR(50),
                    corp_name VARCHAR(500),
                    corp_address VARCHAR(500),
                    corp_city VARCHAR(100),
                    corp_state VARCHAR(10),
                    corp_zip VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(doc_number, officer_name, corp_name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_match_doc ON sunbiz_officer_corporation_matches(doc_number);
                CREATE INDEX IF NOT EXISTS idx_match_email ON sunbiz_officer_corporation_matches(officer_email) WHERE officer_email IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_match_phone ON sunbiz_officer_corporation_matches(officer_phone) WHERE officer_phone IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_match_corp ON sunbiz_officer_corporation_matches(corp_name);
            """)
            
            # Insert matches
            values = [
                (
                    m['doc_number'],
                    m['officer_name'][:500],
                    m['officer_address'][:500],
                    m['officer_city'][:100],
                    m['officer_state'][:10],
                    m['officer_zip'][:20],
                    m.get('officer_email', '')[:255] if m.get('officer_email') else None,
                    m.get('officer_phone', '')[:50] if m.get('officer_phone') else None,
                    m['corp_name'][:500],
                    m['corp_address'][:500],
                    m['corp_city'][:100],
                    m['corp_state'][:10],
                    m['corp_zip'][:20]
                )
                for m in matches
            ]
            
            execute_values(
                cur,
                """
                INSERT INTO sunbiz_officer_corporation_matches 
                (doc_number, officer_name, officer_address, officer_city, officer_state, officer_zip,
                 officer_email, officer_phone, corp_name, corp_address, corp_city, corp_state, corp_zip)
                VALUES %s
                ON CONFLICT (doc_number, officer_name, corp_name) DO UPDATE SET
                    officer_email = COALESCE(EXCLUDED.officer_email, sunbiz_officer_corporation_matches.officer_email),
                    officer_phone = COALESCE(EXCLUDED.officer_phone, sunbiz_officer_corporation_matches.officer_phone)
                """,
                values,
                template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            )
            
            conn.commit()
            print(f"✅ Saved {len(matches):,} matches to database")
            
            # Get counts
            cur.execute("SELECT COUNT(*) FROM sunbiz_officer_corporation_matches WHERE officer_email IS NOT NULL")
            email_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM sunbiz_officer_corporation_matches WHERE officer_phone IS NOT NULL")
            phone_count = cur.fetchone()[0]
            
            print(f"   Total records with emails: {email_count:,}")
            print(f"   Total records with phones: {phone_count:,}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    def create_report(self, matches):
        """Create a comprehensive report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': str(self.corprin_file),
            'statistics': {
                'total_officers': len(self.officers),
                'total_corporations': len(self.corporations),
                'total_matches': len(matches),
                'unique_emails': len(self.emails_found),
                'unique_phones': len(self.phones_found),
                'matches_with_contact': len([m for m in matches if m.get('officer_email') or m.get('officer_phone')])
            },
            'sample_matches': matches[:10] if matches else [],
            'sample_emails': list(self.emails_found)[:20],
            'sample_phones': list(self.phones_found)[:20]
        }
        
        report_file = self.base_path / f"officer_corporation_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Report saved to: {report_file}")
        
        return report
    
    def run(self):
        """Main execution"""
        print("="*60)
        print("CORPRINDATA FIXED-WIDTH PARSER")
        print("="*60)
        
        # Check file exists
        if not self.corprin_file.exists():
            print(f"❌ File not found: {self.corprin_file}")
            return
        
        # Process the file
        self.process_zip_file()
        
        # Match officers to corporations
        matches = self.match_officers_to_corporations()
        
        # Save to database if we have matches
        if matches:
            self.save_to_database(matches)
        
        # Create report
        self.create_report(matches)
        
        print("\n✅ Processing complete!")
        
        # Print SQL examples
        if matches:
            print("\n📊 Query examples:")
            print("-- Find all contacts for a specific corporation:")
            print("SELECT * FROM sunbiz_officer_corporation_matches WHERE corp_name ILIKE '%concord%';")
            print("\n-- Get all email addresses:")
            print("SELECT DISTINCT officer_email FROM sunbiz_officer_corporation_matches WHERE officer_email IS NOT NULL;")
            print("\n-- Count by corporation:")
            print("SELECT corp_name, COUNT(*) as officer_count FROM sunbiz_officer_corporation_matches GROUP BY corp_name ORDER BY officer_count DESC LIMIT 10;")

if __name__ == "__main__":
    parser = CorprinDataParser()
    parser.run()