"""
Parse corporation files from the cor directory
These files contain both corporation and officer data with contact information
"""

import sys
import io
import os
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

class CorporationParser:
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc\cor")
        
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
        self.corporations = {}
        self.officers = []
        self.emails_found = set()
        self.phones_found = set()
        
    def parse_corporation_line(self, line):
        """Parse a line from corporation file
        Format appears to be fixed-width with embedded officer records
        """
        if not line or len(line) < 20:
            return None
            
        try:
            # Extract doc number (first 12 chars)
            doc_number = line[0:12].strip()
            if not doc_number:
                return None
                
            # Extract corporation name (next ~200 chars)
            corp_name = line[12:212].strip()
            
            # Look for email patterns anywhere in the line
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, line, re.IGNORECASE)
            
            # Look for phone patterns
            phone_pattern = r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'
            phones = re.findall(phone_pattern, line)
            
            # Look for officer names (pattern: P followed by last name, first name)
            # These appear after position ~800 in the line
            officers = []
            if len(line) > 800:
                # Look for pattern like "PMAHAJAN             MANOHAR       R"
                officer_pattern = r'P([A-Z][A-Z\s]{15,35})([A-Z][A-Za-z\s]{10,20})([A-Z\s]{0,5})'
                officer_matches = re.findall(officer_pattern, line[800:])
                
                for match in officer_matches:
                    last_name = match[0].strip()
                    first_name = match[1].strip()
                    middle = match[2].strip()
                    
                    officer = {
                        'doc_number': doc_number,
                        'name': f"{first_name} {middle} {last_name}".strip(),
                        'first_name': first_name,
                        'last_name': last_name,
                        'corp_name': corp_name
                    }
                    
                    # Assign email/phone if found
                    if emails:
                        officer['email'] = emails[0].lower()
                        self.emails_found.add(emails[0].lower())
                    if phones:
                        phone_formatted = f"({phones[0][0]}) {phones[0][1]}-{phones[0][2]}"
                        officer['phone'] = phone_formatted
                        self.phones_found.add(phone_formatted)
                        
                    officers.append(officer)
            
            # Store corporation
            if doc_number not in self.corporations:
                self.corporations[doc_number] = {
                    'doc_number': doc_number,
                    'name': corp_name,
                    'emails': list(set(emails)) if emails else [],
                    'phones': [f"({p[0]}) {p[1]}-{p[2]}" for p in phones] if phones else [],
                    'officers': []
                }
            
            # Add officers to corporation
            self.corporations[doc_number]['officers'].extend(officers)
            self.officers.extend(officers)
            
            return {'type': 'corporation', 'doc_number': doc_number, 'officers': len(officers)}
            
        except Exception as e:
            return None
    
    def process_file(self, filepath):
        """Process a single corporation file"""
        filename = filepath.name
        print(f"📄 Processing {filename}...")
        
        records_processed = 0
        officers_found = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    result = self.parse_corporation_line(line)
                    if result:
                        records_processed += 1
                        officers_found += result.get('officers', 0)
                        
                        if records_processed % 1000 == 0:
                            print(f"   {records_processed:,} records | "
                                  f"{len(self.officers):,} officers | "
                                  f"{len(self.emails_found):,} emails")
                            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        print(f"   ✅ Processed {records_processed:,} records, found {officers_found:,} officers")
        
    def process_all_files(self, limit=10):
        """Process corporation files"""
        print(f"\n📂 Processing corporation files from {self.base_path}")
        
        # Get all .txt files
        files = sorted(self.base_path.glob("*.txt"))[:limit]
        print(f"Found {len(files)} files to process")
        
        for filepath in files:
            self.process_file(filepath)
            
        print(f"\n✅ Processing complete!")
        print(f"   Corporations: {len(self.corporations):,}")
        print(f"   Officers: {len(self.officers):,}")
        print(f"   Email addresses: {len(self.emails_found):,}")
        print(f"   Phone numbers: {len(self.phones_found):,}")
        
    def save_to_database(self):
        """Save to database"""
        if not self.officers:
            print("No officers to save")
            return
            
        print(f"\n💾 Saving {len(self.officers):,} officers to database...")
        
        conn = psycopg2.connect(**self.conn_params)
        cur = conn.cursor()
        
        try:
            # Create table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS corporation_officers (
                    id SERIAL PRIMARY KEY,
                    doc_number VARCHAR(20),
                    officer_name VARCHAR(500),
                    first_name VARCHAR(200),
                    last_name VARCHAR(200),
                    officer_email VARCHAR(255),
                    officer_phone VARCHAR(50),
                    corp_name VARCHAR(500),
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(doc_number, officer_name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_corp_off_doc ON corporation_officers(doc_number);
                CREATE INDEX IF NOT EXISTS idx_corp_off_email ON corporation_officers(officer_email) WHERE officer_email IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_corp_off_phone ON corporation_officers(officer_phone) WHERE officer_phone IS NOT NULL;
                CREATE INDEX IF NOT EXISTS idx_corp_off_corp ON corporation_officers(corp_name);
            """)
            
            # Insert officers
            values = []
            for officer in self.officers:
                values.append((
                    officer['doc_number'],
                    officer['name'][:500],
                    officer.get('first_name', '')[:200],
                    officer.get('last_name', '')[:200],
                    officer.get('email', '')[:255] if officer.get('email') else None,
                    officer.get('phone', '')[:50] if officer.get('phone') else None,
                    officer.get('corp_name', '')[:500]
                ))
            
            execute_values(
                cur,
                """
                INSERT INTO corporation_officers 
                (doc_number, officer_name, first_name, last_name, 
                 officer_email, officer_phone, corp_name)
                VALUES %s
                ON CONFLICT (doc_number, officer_name) DO UPDATE SET
                    officer_email = COALESCE(EXCLUDED.officer_email, corporation_officers.officer_email),
                    officer_phone = COALESCE(EXCLUDED.officer_phone, corporation_officers.officer_phone)
                """,
                values,
                template="(%s, %s, %s, %s, %s, %s, %s)"
            )
            
            conn.commit()
            print(f"✅ Saved {len(values):,} officers")
            
            # Get counts
            cur.execute("SELECT COUNT(DISTINCT officer_email) FROM corporation_officers WHERE officer_email IS NOT NULL")
            email_count = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(DISTINCT officer_phone) FROM corporation_officers WHERE officer_phone IS NOT NULL")
            phone_count = cur.fetchone()[0]
            
            print(f"   Unique emails in database: {email_count:,}")
            print(f"   Unique phones in database: {phone_count:,}")
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            conn.rollback()
        finally:
            cur.close()
            conn.close()
            
    def create_report(self):
        """Create report"""
        # Sample data for report
        sample_with_contact = [
            officer for officer in self.officers[:100]
            if officer.get('email') or officer.get('phone')
        ]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'source': 'corporation files',
            'statistics': {
                'corporations_processed': len(self.corporations),
                'officers_found': len(self.officers),
                'unique_emails': len(self.emails_found),
                'unique_phones': len(self.phones_found),
                'officers_with_contact': len([o for o in self.officers if o.get('email') or o.get('phone')])
            },
            'sample_officers_with_contact': sample_with_contact[:20],
            'sample_emails': list(self.emails_found)[:50],
            'sample_phones': list(self.phones_found)[:50]
        }
        
        report_file = Path(f"corporation_officers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        print(f"\n📄 Report saved to: {report_file}")
        
        # Print sample
        if sample_with_contact:
            print("\n📧 Sample officers with contact info:")
            for officer in sample_with_contact[:5]:
                print(f"   {officer['name']} ({officer['corp_name'][:50]})")
                if officer.get('email'):
                    print(f"      Email: {officer['email']}")
                if officer.get('phone'):
                    print(f"      Phone: {officer['phone']}")
                    
    def run(self):
        """Main execution"""
        print("="*60)
        print("CORPORATION FILES PARSER")
        print("="*60)
        
        # Process files
        self.process_all_files(limit=50)  # Process first 50 files
        
        # Save to database if we have data
        if self.officers:
            self.save_to_database()
            
        # Create report
        self.create_report()
        
        print("\n✅ Complete!")
        
        if self.officers:
            print("\n📊 Query examples:")
            print("SELECT * FROM corporation_officers WHERE officer_email IS NOT NULL LIMIT 10;")
            print("SELECT corp_name, COUNT(*) as officer_count FROM corporation_officers GROUP BY corp_name ORDER BY officer_count DESC LIMIT 10;")

if __name__ == "__main__":
    parser = CorporationParser()
    parser.run()