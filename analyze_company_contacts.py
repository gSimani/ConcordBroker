"""
Analyze downloaded SFTP database files for phone numbers and emails per company
"""

import re
import os
from pathlib import Path
from collections import defaultdict
import csv

def extract_phone_numbers(text):
    """Extract phone numbers from text"""
    # Various phone number patterns
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890, 123.456.7890, 1234567890
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (123) 456-7890
        r'\b\d{3}\s+\d{3}\s+\d{4}\b',     # 123 456 7890
        r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-123-456-7890
    ]
    
    phones = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Clean up the phone number
            clean_phone = re.sub(r'[^\d]', '', match)
            if len(clean_phone) == 10 or (len(clean_phone) == 11 and clean_phone.startswith('1')):
                phones.add(match)
    
    return list(phones)

def extract_emails(text):
    """Extract email addresses from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return list(set(emails))  # Remove duplicates

def analyze_database_files():
    """Analyze all downloaded database files"""
    
    database_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
    
    if not database_path.exists():
        print(f"❌ Database path not found: {database_path}")
        return
        
    print(f"📁 Analyzing database files in: {database_path}")
    print("="*80)
    
    # Find all text files in the database
    txt_files = list(database_path.rglob("*.txt"))
    print(f"📄 Found {len(txt_files)} text files")
    
    if len(txt_files) == 0:
        print("❌ No text files found to analyze")
        return
    
    # Company contact data
    company_contacts = defaultdict(lambda: {'phones': set(), 'emails': set()})
    
    total_phones = 0
    total_emails = 0
    files_processed = 0
    
    # Process each file
    for file_path in txt_files:
        try:
            print(f"\n📄 Processing: {file_path.name}")
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Extract all phone numbers and emails from this file
            phones = extract_phone_numbers(content)
            emails = extract_emails(content)
            
            file_phone_count = len(phones)
            file_email_count = len(emails)
            
            print(f"   📞 Found {file_phone_count} phone numbers")
            print(f"   📧 Found {file_email_count} email addresses")
            
            total_phones += file_phone_count
            total_emails += file_email_count
            
            # Try to extract company names from the file content
            # Look for common business entity patterns
            lines = content.split('\n')
            current_company = None
            
            for line in lines[:50]:  # Check first 50 lines for company info
                line = line.strip()
                
                # Look for company name patterns
                if any(keyword in line.upper() for keyword in ['CORP', 'LLC', 'INC', 'LTD', 'COMPANY', 'CORPORATION']):
                    # Extract potential company name
                    if '|' in line:  # Pipe-delimited format
                        parts = line.split('|')
                        for part in parts:
                            part = part.strip()
                            if any(keyword in part.upper() for keyword in ['CORP', 'LLC', 'INC', 'LTD']):
                                current_company = part[:100]  # Limit length
                                break
                    else:
                        current_company = line[:100]  # First 100 chars
                    break
            
            # If we found a company name, associate contacts with it
            if current_company:
                company_contacts[current_company]['phones'].update(phones)
                company_contacts[current_company]['emails'].update(emails)
            else:
                # Use filename as company identifier
                filename_company = file_path.stem
                company_contacts[filename_company]['phones'].update(phones)
                company_contacts[filename_company]['emails'].update(emails)
            
            files_processed += 1
            
            # Show progress every 10 files
            if files_processed % 10 == 0:
                print(f"\n📊 Progress: {files_processed}/{len(txt_files)} files processed")
                print(f"   Total phones so far: {total_phones}")
                print(f"   Total emails so far: {total_emails}")
                
        except Exception as e:
            print(f"   ❌ Error processing {file_path.name}: {str(e)[:100]}")
            continue
    
    print("\n" + "="*80)
    print("📊 ANALYSIS COMPLETE")
    print("="*80)
    
    print(f"📄 Files processed: {files_processed}")
    print(f"📞 Total phone numbers found: {total_phones}")
    print(f"📧 Total email addresses found: {total_emails}")
    print(f"🏢 Companies identified: {len(company_contacts)}")
    
    # Show top companies by contact count
    print(f"\n🏆 TOP 20 COMPANIES BY CONTACT COUNT:")
    print("-" * 80)
    
    # Sort companies by total contacts (phones + emails)
    sorted_companies = sorted(
        company_contacts.items(),
        key=lambda x: len(x[1]['phones']) + len(x[1]['emails']),
        reverse=True
    )
    
    for i, (company, contacts) in enumerate(sorted_companies[:20], 1):
        phone_count = len(contacts['phones'])
        email_count = len(contacts['emails'])
        total_contacts = phone_count + email_count
        
        print(f"{i:2d}. {company[:60]}...")
        print(f"    📞 Phones: {phone_count}, 📧 Emails: {email_count}, Total: {total_contacts}")
    
    # Export to CSV
    csv_path = database_path / "company_contacts_analysis.csv"
    print(f"\n💾 Exporting detailed results to: {csv_path}")
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Company', 'Phone_Count', 'Email_Count', 'Total_Contacts', 'Phone_Numbers', 'Email_Addresses'])
        
        for company, contacts in sorted_companies:
            phone_count = len(contacts['phones'])
            email_count = len(contacts['emails'])
            total_contacts = phone_count + email_count
            
            # Join phone numbers and emails with semicolons
            phones_str = '; '.join(contacts['phones'])
            emails_str = '; '.join(contacts['emails'])
            
            writer.writerow([company, phone_count, email_count, total_contacts, phones_str, emails_str])
    
    print("✅ Analysis complete! Check the CSV file for detailed company contact data.")
    
    # Show contact distribution
    print(f"\n📈 CONTACT DISTRIBUTION:")
    print("-" * 40)
    
    companies_with_phones = sum(1 for c in company_contacts.values() if len(c['phones']) > 0)
    companies_with_emails = sum(1 for c in company_contacts.values() if len(c['emails']) > 0)
    companies_with_both = sum(1 for c in company_contacts.values() if len(c['phones']) > 0 and len(c['emails']) > 0)
    
    print(f"📞 Companies with phone numbers: {companies_with_phones}")
    print(f"📧 Companies with email addresses: {companies_with_emails}")
    print(f"📱 Companies with both phones & emails: {companies_with_both}")
    
    return {
        'total_files': files_processed,
        'total_phones': total_phones,
        'total_emails': total_emails,
        'total_companies': len(company_contacts),
        'companies_with_phones': companies_with_phones,
        'companies_with_emails': companies_with_emails,
        'companies_with_both': companies_with_both
    }

if __name__ == "__main__":
    print("Starting Company Contact Analysis")
    print("=" * 80)
    
    results = analyze_database_files()
    
    if results:
        print(f"\n📋 SUMMARY:")
        print(f"   📄 Files analyzed: {results['total_files']}")
        print(f"   📞 Phone numbers: {results['total_phones']}")
        print(f"   📧 Email addresses: {results['total_emails']}")
        print(f"   🏢 Companies: {results['total_companies']}")
        print(f"   📱 Contact coverage: {results['companies_with_both']}/{results['total_companies']} companies have both phone & email")