"""
Analyze Sunbiz data for contact information including emails
"""

import os
import sys
import io
from pathlib import Path
import re

# UTF-8 output fix
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_sunbiz_file(file_path, sample_size=1000):
    """Analyze a Sunbiz file for contact information"""
    
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    phone_pattern = re.compile(r'[\(]?[0-9]{3}[\)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4}')
    
    emails_found = []
    phones_found = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for i, line in enumerate(f):
            if i >= sample_size:
                break
            
            # Search for emails
            email_matches = email_pattern.findall(line)
            if email_matches:
                emails_found.extend(email_matches)
            
            # Search for phone numbers
            phone_matches = phone_pattern.findall(line)
            if phone_matches:
                phones_found.extend(phone_matches)
    
    return emails_found, phones_found

def main():
    # Path to Sunbiz data
    data_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE\doc")
    
    print("=" * 60)
    print("SUNBIZ CONTACT INFORMATION ANALYSIS")
    print("=" * 60)
    
    # Check corporation files
    cor_path = data_path / "cor"
    cor_files = list(cor_path.glob("*.txt"))[:5]  # Check first 5 files
    
    print(f"\nAnalyzing {len(cor_files)} corporation files...")
    print("-" * 40)
    
    total_emails = []
    total_phones = []
    
    for file_path in cor_files:
        print(f"\nFile: {file_path.name}")
        emails, phones = analyze_sunbiz_file(file_path, sample_size=500)
        
        if emails:
            print(f"  Emails found: {len(emails)}")
            for email in emails[:3]:
                print(f"    - {email}")
            total_emails.extend(emails)
        else:
            print(f"  No emails found")
        
        if phones:
            print(f"  Phone numbers found: {len(phones)}")
            for phone in phones[:3]:
                print(f"    - {phone}")
            total_phones.extend(phones)
        else:
            print(f"  No phone numbers found")
    
    # Check officers/directors data
    print("\n" + "=" * 60)
    print("CHECKING OFFICERS/DIRECTORS DATA")
    print("=" * 60)
    
    # Check for off (officers) directory
    off_path = data_path / "off"
    if off_path.exists():
        off_files = list(off_path.glob("*.txt"))[:3]
        print(f"Found {len(off_files)} officer files")
        
        for file_path in off_files:
            print(f"\nFile: {file_path.name}")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                sample = f.read(5000)
                if '@' in sample:
                    print("  ✅ Contains email addresses!")
                else:
                    print("  No emails in sample")
    else:
        print("No officers directory found")
    
    # Check registered agents
    ag_path = data_path / "AG"
    if ag_path.exists():
        print(f"\n✅ Registered Agents directory found: {ag_path}")
        ag_files = list(ag_path.glob("*.txt"))
        if ag_files:
            print(f"  Contains {len(ag_files)} agent files")
            # Sample first file
            with open(ag_files[0], 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(3)]
                for i, line in enumerate(lines, 1):
                    print(f"  Line {i}: {line[:100]}...")
    
    # Summary
    print("\n" + "=" * 60)
    print("CONTACT INFORMATION SUMMARY")
    print("=" * 60)
    print("\n📊 Available in current database:")
    print("  ✅ Registered Agent Names")
    print("  ✅ Principal Addresses") 
    print("  ✅ Mailing Addresses")
    print("  ✅ EIN Numbers")
    print("  ❌ Email Addresses")
    print("  ❌ Phone Numbers")
    
    print("\n📁 Additional data sources in TEMP/DATABASE/doc:")
    directories = [d for d in data_path.iterdir() if d.is_dir()]
    for dir_path in sorted(directories):
        file_count = len(list(dir_path.glob("*.txt")))
        if file_count > 0:
            print(f"  - {dir_path.name:15} ({file_count} files)")
    
    print("\n💡 Recommendations:")
    print("  1. The 'AG' folder (666MB) likely contains detailed agent info")
    print("  2. The 'off' folder may contain officer/director contact info")
    print("  3. Florida requires registered agents but not email disclosure")
    print("  4. Phone/email are typically not in public Sunbiz records")

if __name__ == "__main__":
    main()