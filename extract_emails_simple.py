"""
Simple email extraction from corprindata.zip
Just extracts and shows all email addresses found
"""

import sys
import io
import os
import zipfile
from pathlib import Path
import re
import time

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class SimpleEmailExtractor:
    """Extract emails from corprindata.zip"""
    
    def __init__(self):
        self.base_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
        self.corprin_file = self.base_path / "corprindata.zip"
        self.stats = {
            'files_processed': 0,
            'lines_processed': 0,
            'emails_found': 0,
            'unique_emails': set(),
            'start_time': time.time()
        }
    
    def extract_emails_from_text(self, text: str) -> list:
        """Extract email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text, re.IGNORECASE)
    
    def process_file_content(self, filename: str, content: bytes):
        """Process file content and extract emails"""
        try:
            # Try to decode
            text = content.decode('utf-8', errors='ignore')
            
            lines = text.split('\n')
            self.stats['lines_processed'] += len(lines)
            
            file_emails = []
            
            for line in lines:
                if '@' in line:  # Quick check before regex
                    emails = self.extract_emails_from_text(line)
                    for email in emails:
                        email_clean = email.lower().strip()
                        if email_clean:
                            file_emails.append(email_clean)
                            self.stats['unique_emails'].add(email_clean)
                            self.stats['emails_found'] += 1
            
            if file_emails:
                print(f"  📧 Found {len(file_emails)} emails in {filename}")
                
                # Show first few emails as sample
                if len(file_emails) <= 5:
                    for email in file_emails:
                        print(f"    • {email}")
                else:
                    for email in file_emails[:3]:
                        print(f"    • {email}")
                    print(f"    ... and {len(file_emails) - 3} more")
            
        except Exception as e:
            print(f"  ❌ Error processing {filename}: {e}")
    
    def run(self):
        """Extract all emails from corprindata.zip"""
        print("=" * 60)
        print("EXTRACTING EMAILS FROM CORPRINDATA.ZIP")
        print("=" * 60)
        
        # Check file exists
        if not self.corprin_file.exists():
            print(f"❌ File not found: {self.corprin_file}")
            return
        
        size_mb = self.corprin_file.stat().st_size / (1024 * 1024)
        print(f"📦 Processing: {self.corprin_file.name} ({size_mb:.1f} MB)")
        
        print("\n🔍 Extracting and scanning for email addresses...")
        
        try:
            with zipfile.ZipFile(self.corprin_file, 'r') as zf:
                files = zf.namelist()
                print(f"\n📁 Found {len(files)} files in ZIP")
                
                for i, filename in enumerate(files):
                    print(f"\n📄 Processing {filename} ({i+1}/{len(files)})")
                    
                    try:
                        # Read file content
                        with zf.open(filename) as f:
                            content = f.read()
                        
                        # Process for emails
                        self.process_file_content(filename, content)
                        self.stats['files_processed'] += 1
                        
                        # Progress update
                        if (i + 1) % 5 == 0:
                            elapsed = time.time() - self.stats['start_time']
                            rate = self.stats['lines_processed'] / elapsed if elapsed > 0 else 0
                            print(f"  📊 Progress: {i+1}/{len(files)} files | "
                                  f"{self.stats['emails_found']:,} emails | "
                                  f"{rate:.0f} lines/sec")
                        
                    except Exception as e:
                        print(f"  ❌ Error with {filename}: {e}")
                        
        except Exception as e:
            print(f"❌ Error opening ZIP: {e}")
            return
        
        # Final results
        elapsed = time.time() - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("EMAIL EXTRACTION COMPLETE")
        print("=" * 60)
        print(f"✅ Files processed: {self.stats['files_processed']}")
        print(f"✅ Lines processed: {self.stats['lines_processed']:,}")
        print(f"📧 Total emails found: {self.stats['emails_found']:,}")
        print(f"🎯 Unique emails: {len(self.stats['unique_emails']):,}")
        print(f"⏱️ Processing time: {elapsed:.1f} seconds")
        
        if self.stats['lines_processed'] > 0:
            rate = self.stats['lines_processed'] / elapsed
            print(f"🚀 Processing rate: {rate:.0f} lines/second")
        
        # Show sample unique emails
        if self.stats['unique_emails']:
            print("\n📧 SAMPLE EXTRACTED EMAILS:")
            print("-" * 40)
            unique_list = list(self.stats['unique_emails'])
            
            # Show first 20 unique emails
            for i, email in enumerate(unique_list[:20]):
                print(f"{i+1:2d}. {email}")
            
            if len(unique_list) > 20:
                print(f"... and {len(unique_list) - 20:,} more unique emails!")
        
        # Save results
        output_file = self.base_path / "extracted_emails.txt"
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                for email in sorted(self.stats['unique_emails']):
                    f.write(f"{email}\n")
            
            print(f"\n💾 All unique emails saved to: {output_file}")
            print(f"📊 File contains {len(self.stats['unique_emails']):,} unique email addresses")
            
        except Exception as e:
            print(f"❌ Error saving emails: {e}")
        
        # Success summary
        if len(self.stats['unique_emails']) > 0:
            print(f"\n🎉 SUCCESS! Extracted {len(self.stats['unique_emails']):,} unique email addresses")
            print("💼 These are Florida business officer/principal emails")
            print("📋 Perfect for business development and marketing!")
        else:
            print("\n⚠️ No emails found - may need to check file format")

if __name__ == "__main__":
    extractor = SimpleEmailExtractor()
    extractor.run()