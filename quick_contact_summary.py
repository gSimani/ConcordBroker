"""
Quick Contact Summary - Get high-level statistics from downloaded SFTP database
"""

import re
import os
from pathlib import Path
from collections import defaultdict

def extract_phone_numbers(text):
    """Extract phone numbers from text"""
    patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890, 123.456.7890, 1234567890
        r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',    # (123) 456-7890
        r'\b\d{3}\s+\d{3}\s+\d{4}\b',     # 123 456 7890
    ]
    
    phones = set()
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            clean_phone = re.sub(r'[^\d]', '', match)
            if len(clean_phone) == 10 or (len(clean_phone) == 11 and clean_phone.startswith('1')):
                phones.add(match)
    return list(phones)

def extract_emails(text):
    """Extract email addresses from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(pattern, text)
    return list(set(emails))

def quick_analysis():
    """Get quick statistics"""
    database_path = Path(r"C:\Users\gsima\Documents\MyProject\ConcordBroker\TEMP\DATABASE")
    
    if not database_path.exists():
        print(f"ERROR: Database path not found: {database_path}")
        return
    
    print("QUICK CONTACT ANALYSIS")
    print("=" * 60)
    
    # Find all text files
    txt_files = list(database_path.rglob("*.txt"))
    print(f"Total text files found: {len(txt_files):,}")
    
    # Process sample of files to get estimates
    sample_size = min(100, len(txt_files))
    sample_files = txt_files[:sample_size]
    
    print(f"Analyzing sample of {sample_size} files...")
    print("-" * 40)
    
    total_phones = 0
    total_emails = 0
    company_contacts = defaultdict(lambda: {'phones': set(), 'emails': set()})
    
    for i, file_path in enumerate(sample_files):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            phones = extract_phone_numbers(content)
            emails = extract_emails(content)
            
            total_phones += len(phones)
            total_emails += len(emails)
            
            # Use filename as company identifier for quick analysis
            filename_company = file_path.stem
            company_contacts[filename_company]['phones'].update(phones)
            company_contacts[filename_company]['emails'].update(emails)
            
            if (i + 1) % 20 == 0:
                print(f"  Processed {i+1}/{sample_size} files...")
                
        except Exception as e:
            continue
    
    print(f"\nSAMPLE RESULTS ({sample_size} files):")
    print("-" * 40)
    print(f"Phone numbers found: {total_phones:,}")
    print(f"Email addresses found: {total_emails:,}")
    print(f"Companies with contacts: {len(company_contacts):,}")
    
    # Estimate for all files
    if sample_size > 0:
        total_files = len(txt_files)
        multiplier = total_files / sample_size
        
        estimated_phones = int(total_phones * multiplier)
        estimated_emails = int(total_emails * multiplier)
        estimated_companies = int(len(company_contacts) * multiplier)
        
        print(f"\nESTIMATED TOTALS (all {total_files:,} files):")
        print("-" * 40)
        print(f"Estimated phone numbers: {estimated_phones:,}")
        print(f"Estimated email addresses: {estimated_emails:,}")
        print(f"Estimated companies: {estimated_companies:,}")
    
    # Show top companies from sample
    print(f"\nTOP 10 COMPANIES (from sample):")
    print("-" * 40)
    
    sorted_companies = sorted(
        company_contacts.items(),
        key=lambda x: len(x[1]['phones']) + len(x[1]['emails']),
        reverse=True
    )
    
    for i, (company, contacts) in enumerate(sorted_companies[:10], 1):
        phone_count = len(contacts['phones'])
        email_count = len(contacts['emails'])
        total_contacts = phone_count + email_count
        
        if total_contacts > 0:
            print(f"{i:2d}. {company[:50]:<50} | Phones: {phone_count:2d} | Emails: {email_count:2d} | Total: {total_contacts:2d}")
    
    # Show breakdown by folder/category
    print(f"\nFILE BREAKDOWN:")
    print("-" * 40)
    
    folder_stats = defaultdict(int)
    for file_path in txt_files:
        folder = str(file_path.parent.relative_to(database_path))
        folder_stats[folder] += 1
    
    for folder, count in sorted(folder_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{folder:<30} : {count:,} files")
    
    return {
        'total_files': len(txt_files),
        'sample_phones': total_phones,
        'sample_emails': total_emails,
        'sample_companies': len(company_contacts)
    }

if __name__ == "__main__":
    results = quick_analysis()